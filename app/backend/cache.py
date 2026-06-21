import calendar
import requests

DB_URL = "http://127.0.0.1:4999"


def ping() -> bool:
    """Returns True if the database server is reachable, False otherwise."""
    try:
        requests.get(f"{DB_URL}/api/system/config", timeout=2)
        return True
    except requests.exceptions.ConnectionError:
        return False


def _db_get(path: str) -> dict | list:
    try:
        r = requests.get(f"{DB_URL}{path}")
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        print(f"[DB ERROR] Database server unreachable. GET {path} failed. Returning empty data.")
        return {}


def _db_post(path: str, data: dict):
    try:
        r = requests.post(f"{DB_URL}{path}", json=data)
        r.raise_for_status()
    except requests.exceptions.ConnectionError:
        print(f"[DB ERROR] Database server unreachable. POST {path} failed. Write was not saved.")
        raise


class MemoryStore:
    def __init__(self, max_months=5):
        # Flattened RAM structure: {'2026-05': {'gym': {...}, 'transactions': {...}}}
        self.store = {}
        self.util_store = {}
        self.loaded_months = []
        self.max_months = max_months

    def preload_util(self):
        # The config endpoint bundles every util file ({'dropdowns': {...}, ...})
        config = _db_get('/api/system/config')
        if isinstance(config, dict):
            self.util_store = config

    def load_month(self, year_month):
        if year_month in self.store: return

        if len(self.loaded_months) >= self.max_months:
            oldest = self.loaded_months.pop(0)
            del self.store[oldest]
            print(f"Evicted {oldest} from RAM")

        year, month = map(int, year_month.split('-'))
        last_day = calendar.monthrange(year, month)[1]
        range_data = _db_get(f'/api/owned/{year_month}-01/{year_month}-{last_day:02d}')

        # Pivot {date: {category: data}} into the RAM shape {category: {day: data}}
        month_data = {}
        for date_str, categories in range_data.items():
            day = date_str[8:10]
            for category, payload in categories.items():
                month_data.setdefault(category, {})[day] = payload

        self.store[year_month] = month_data
        self.loaded_months.append(year_month)
        print(f"Loaded {year_month} into RAM")

    def get_day(self, date_str):
        year_month = date_str[:7]
        day = date_str[8:10]

        self.load_month(year_month)

        day_data = {}
        month_data = self.store[year_month]

        for category, days in month_data.items():
            if day in days:
                day_data[category] = days[day]

        return day_data

    def get_month_days(self, year_month):
        self.load_month(year_month)
        month_data = self.store[year_month]

        days_out = {}

        for category, days in month_data.items():
            for day, payload in days.items():
                if day not in days_out:
                    days_out[day] = {}
                days_out[day][category] = payload

        return days_out

    def save_section(self, date_str, category, payload):
        year_month = date_str[:7]
        day = date_str[8:10]

        self.load_month(year_month)
        month_data = self.store[year_month]

        # Compose the complete day state (API invariant: POST exactly one full day).
        # The server drops read-only imported categories from the write itself.
        day_data = {}
        for cat, days in month_data.items():
            if day in days:
                day_data[cat] = days[day]
        day_data[category] = payload

        _db_post(f'/api/owned/{date_str}', day_data)

        # Update RAM only after the write succeeds
        month_data.setdefault(category, {})[day] = payload

        return True


cache = MemoryStore()
