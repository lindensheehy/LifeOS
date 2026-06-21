import os
import sqlite3
import sqlite_telemetry
import sqlite_owned
import sqlite_imported

DATA_DIR     = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'lake'))
TELEMETRY_DB = os.path.join(DATA_DIR, "telemetry", "telemetry.db")
OWNED_DB     = os.path.join(DATA_DIR, "owned", "owned_index.db")
IMPORTED_DB  = os.path.join(DATA_DIR, "imported", "imported.db")


def _ensure_schema(conn, db_type):
    current = conn.execute("PRAGMA user_version").fetchone()[0]

    # Fresh database: lay down the full baseline schema.
    if current == 0:
        if db_type == "telemetry":
            schema = _TELEMETRY_SCHEMA
        elif db_type == "imported":
            schema = _IMPORTED_SCHEMA
        else:
            schema = _OWNED_SCHEMA
        conn.executescript(schema)
        current = conn.execute("PRAGMA user_version").fetchone()[0]

    # Apply any pending forward migrations (imported.db only for now).
    if db_type == "imported" and current < _IMPORTED_TARGET_VERSION:
        for version in range(current + 1, _IMPORTED_TARGET_VERSION + 1):
            migration = _IMPORTED_MIGRATIONS.get(version)
            if migration:
                conn.executescript(migration)
            conn.execute(f"PRAGMA user_version = {version}")
        conn.commit()

def get_connection(db_path, db_type):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    _ensure_schema(conn, db_type)
    return conn

def merge_telemetry(date: str, app_name: str, new_sessions: list):
    """Merges an incoming chunk into the stored (date, app) sessions and rewrites
    them, all in one transaction. telemetry.db is the source of truth."""
    conn = None
    try:
        conn = get_connection(TELEMETRY_DB, "telemetry")
        existing = sqlite_telemetry.read_day(conn, date, app_name)
        merged = sqlite_telemetry.merge_sessions(existing, new_sessions)
        sqlite_telemetry.replace_day(conn, date, app_name, merged)
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def read_telemetry_range(start_date: str, end_date: str) -> dict:
    conn = None
    try:
        conn = get_connection(TELEMETRY_DB, "telemetry")
        return sqlite_telemetry.read_range(conn, start_date, end_date)
    finally:
        if conn:
            conn.close()

def read_imported_range(start_date: str, end_date: str) -> dict:
    conn = None
    try:
        conn = get_connection(IMPORTED_DB, "imported")
        return sqlite_imported.read_range(conn, start_date, end_date)
    finally:
        if conn:
            conn.close()

def write_imported(category: str, records: list):
    """INSERT OR IGNORE a flat list of normalized records into imported.db."""
    conn = None
    try:
        conn = get_connection(IMPORTED_DB, "imported")
        sqlite_imported.write_records(conn, category, records)
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def write_owned_day(date: str, day_payload: dict):
    """UPSERTs one complete day of state ({category: data}) into owned_index.db."""
    conn = None
    try:
        conn = get_connection(OWNED_DB, "owned")
        for category, day_data in day_payload.items():
            sqlite_owned.upsert_day(conn, date, category, day_data)
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
