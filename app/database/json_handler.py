import os
import json
from datetime import date as date_cls, timedelta

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'lake'))
READ_ONLY_DIR = os.path.join(DATA_DIR, "READ_ONLY_DATA_COPY")

CATEGORY_ROUTING = {
    "transactions": "imported",
    "apple_health": "imported",
    "coding": "owned",
    "evaluation": "owned",
    "events": "owned",
    "finances": "owned",
    "gym": "owned",
    "health": "owned",
    "major_events": "owned",
    "notes": "owned",
}

def sanitize(segment: str) -> str:
    if not segment:
        return ""
    return segment.replace("/", "").replace("\\", "").replace("..", "")

def resolve_domain(category: str) -> str:
    if category not in CATEGORY_ROUTING:
        raise ValueError(f"CRITICAL: Unknown category '{category}'. Must be registered.")
    return CATEGORY_ROUTING[category]

def build_safe_path(domain: str, month: str, category: str) -> str:
    safe_domain = sanitize(domain)
    safe_month = sanitize(month)
    safe_filename = f"{sanitize(category)}.json"
    target_path = os.path.abspath(os.path.join(DATA_DIR, safe_domain, safe_month, safe_filename))
    if not target_path.startswith(DATA_DIR):
        raise PermissionError(f"CRITICAL: Path traversal attempt detected: {target_path}")
    return target_path

# --- Owned / Imported Data ---

def read_data(month: str, category: str) -> dict:
    domain = resolve_domain(category)
    path = build_safe_path(domain, month, category)
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_data(month: str, category: str, data: dict):
    domain = resolve_domain(category)
    if domain == "imported":
        raise PermissionError(f"CRITICAL: Category '{category}' is read-only via API.")
    path = build_safe_path(domain, month, category)
    if path.startswith(READ_ONLY_DIR):
        raise PermissionError("CRITICAL: Attempted to write to the backup copy.")
    
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def read_owned_range(start_date: str, end_date: str) -> dict:
    """Reconstructs {date: {category: data}} for all dates in the inclusive range."""
    start = date_cls.fromisoformat(start_date)
    end = date_cls.fromisoformat(end_date)

    # Each month file is read at most once, regardless of range length
    month_cache = {}

    result = {}
    current = start
    while current <= end:
        date_str = current.isoformat()
        month = date_str[:7]
        day = date_str[8:10]

        if month not in month_cache:
            month_data = {}
            for category in CATEGORY_ROUTING:
                data = read_data(month, category)
                if data:
                    month_data[category] = data
            month_cache[month] = month_data

        day_block = {}
        for category, days in month_cache[month].items():
            if day in days:
                day_block[category] = days[day]

        result[date_str] = day_block
        current += timedelta(days=1)

    return result

def write_owned_day(date_str: str, day_payload: dict):
    """Merges one complete day of state ({category: data}) into the monthly ground-truth files."""
    month = date_str[:7]
    day = date_str[8:10]
    for category, day_data in day_payload.items():
        month_data = read_data(month, category)
        month_data[day] = day_data
        write_data(month, category, month_data)

# --- Utils ---

def read_all_util() -> dict:
    """Bundles every JSON file in data/lake/util/ into one {filename: contents} object."""
    util_dir = os.path.join(DATA_DIR, "util")
    config = {}
    if not os.path.isdir(util_dir):
        return config
    for filename in sorted(os.listdir(util_dir)):
        if not filename.endswith(".json"):
            continue
        with open(os.path.join(util_dir, filename), 'r', encoding='utf-8') as f:
            config[filename[:-len(".json")]] = json.load(f)
    return config