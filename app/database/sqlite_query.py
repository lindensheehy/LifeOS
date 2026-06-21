"""Direct SQL query channel for the /api/query routing group.

Two distinct channels:

* ``common_query`` treats the client payload as a search index. The client sends
  only a FROM/WHERE clause; the server blindly prepends ``SELECT date``, runs it
  to find the matching dates, and then rebuilds the full, rich domain JSON for
  those days using the existing readers. Dates that don't match are omitted.

* ``custom_query`` is a sandbox for ad-hoc, cross-database relational analytics.
  All three databases are attached to a throwaway in-memory connection so the
  client can JOIN across them using ``telemetry.``/``imported.``/``owned.``
  prefixes. Results come back as a flat array of row dicts.
"""

import sqlite3

import json_handler
import sqlite_handler

# source -> (db file, db_type for get_connection)
_SOURCE_DB = {
    "owned":     (sqlite_handler.OWNED_DB,     "owned"),
    "telemetry": (sqlite_handler.TELEMETRY_DB, "telemetry"),
    "imported":  (sqlite_handler.IMPORTED_DB,  "imported"),
}

VALID_SOURCES = tuple(_SOURCE_DB.keys())

# alias the client uses in custom queries -> (db file, db_type)
_ATTACH_DBS = {
    "telemetry": (sqlite_handler.TELEMETRY_DB, "telemetry"),
    "imported":  (sqlite_handler.IMPORTED_DB,  "imported"),
    "owned":     (sqlite_handler.OWNED_DB,     "owned"),
}


def common_query(source: str, where_clause: str, params: list) -> dict:
    """Runs ``SELECT date <where_clause>`` against the source DB to find matching
    dates, then returns the full domain JSON for those dates (non-matching dates
    omitted). ``where_clause`` is the client-supplied FROM/WHERE fragment."""
    db_path, db_type = _SOURCE_DB[source]

    conn = None
    try:
        conn = sqlite_handler.get_connection(db_path, db_type)
        cursor = conn.execute("SELECT date " + where_clause, params)
        dates = {row[0] for row in cursor.fetchall() if row[0] is not None}
    finally:
        if conn:
            conn.close()

    if not dates:
        return {}

    return _build_domain(source, dates)


def _build_domain(source: str, dates: set) -> dict:
    """Rebuilds the rich domain JSON for the matching dates using the existing
    readers, keeping only dates that matched and actually carry data."""
    start, end = min(dates), max(dates)

    if source == "owned":
        full = json_handler.read_owned_range(start, end)
    elif source == "telemetry":
        full = sqlite_handler.read_telemetry_range(start, end)
    else:  # imported
        full = sqlite_handler.read_imported_range(start, end)

    # read_owned_range emits empty {} blocks for dates with no data; the imported
    # and telemetry readers only emit dates that have data. Either way, keep only
    # matched dates whose block is non-empty.
    return {date: block for date, block in full.items() if date in dates and block}


def custom_query(query: str, params: list) -> list:
    """Attaches all three databases to an in-memory connection and runs an
    arbitrary query, returning a flat list of row dicts."""
    # Ensure each underlying DB exists with its schema before attaching, so a
    # never-initialized DB surfaces as a clean "no such table" rather than an
    # attached empty file.
    for db_path, db_type in _ATTACH_DBS.values():
        sqlite_handler.get_connection(db_path, db_type).close()

    conn = None
    try:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        for alias, (db_path, _) in _ATTACH_DBS.items():
            conn.execute(f"ATTACH DATABASE ? AS {alias}", (db_path,))

        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        if conn:
            for alias in _ATTACH_DBS:
                try:
                    conn.execute(f"DETACH DATABASE {alias}")
                except sqlite3.Error:
                    pass
            conn.close()
