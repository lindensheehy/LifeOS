import os
import json

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
READ_ONLY_DIR = os.path.join(DATA_DIR, "READ_ONLY_DATA_COPY")

# The Source of Truth: access.py knows exactly where everything lives.
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
    "notes": "owned"
}

def _sanitize(segment: str) -> str:
    if not segment: return ""
    return segment.replace("/", "").replace("\\", "").replace("..", "")

def _resolve_domain(category: str) -> str:
    """Internal router to find where a category belongs."""
    if category not in CATEGORY_ROUTING:
        raise ValueError(f"CRITICAL: Unknown category '{category}'. Must be registered in access.py.")
    return CATEGORY_ROUTING[category]

def _build_safe_path(domain: str, month: str, category: str) -> str:
    safe_domain = _sanitize(domain)
    safe_month = _sanitize(month)
    safe_filename = f"{_sanitize(category)}.json"
    
    target_path = os.path.abspath(os.path.join(DATA_DIR, safe_domain, safe_month, safe_filename))

    if not target_path.startswith(DATA_DIR):
        raise PermissionError(f"CRITICAL: Path traversal attempt detected: {target_path}")
    
    return target_path

# --- PUBLIC API ---

def list_all_categories() -> list:
    """Returns a list of all registered categories, regardless of domain."""
    return list(CATEGORY_ROUTING.keys())

def read_data(month: str, category: str) -> dict:
    """Reads a JSON file safely. The caller doesn't need to know the domain."""
    domain = _resolve_domain(category)
    path = _build_safe_path(domain, month, category)
    
    if not os.path.exists(path):
        return {} 
        
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_data(month: str, category: str, data: dict):
    """Writes data safely, enforcing read-only rules for imported data."""
    domain = _resolve_domain(category)

    # Architectural lock: The frontend/cache can NEVER write to pipeline data.
    if domain == "imported":
        raise PermissionError(f"CRITICAL: Category '{category}' is read-only. Modifying imported data is blocked.")

    path = _build_safe_path(domain, month, category)

    if path.startswith(READ_ONLY_DIR):
        raise PermissionError("CRITICAL: Attempted to write to the backup copy.")
    
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def read_util(filename: str) -> dict:
    path = os.path.abspath(os.path.join(DATA_DIR, "util", f"{_sanitize(filename)}.json"))
    if not os.path.exists(path): return {}
    with open(path, 'r', encoding='utf-8') as f: return json.load(f)