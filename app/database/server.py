import os
import re
import sqlite3
import threading
import time
import traceback
from datetime import date as date_cls
from flask import Flask, request, jsonify, abort

import json_handler
import sqlite_handler
import sqlite_query

app = Flask(__name__)
lock = threading.Lock()
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

SESSION_META_KEYS = ("date", "app_name")

def is_valid_date(date) -> bool:
    if not isinstance(date, str) or not DATE_RE.match(date):
        return False
    try:
        date_cls.fromisoformat(date)
        return True
    except ValueError:
        return False

def validate_dates(*dates):
    for date in dates:
        if not is_valid_date(date):
            abort(400, description="Invalid date. Expected a valid YYYY-MM-DD date.")

def validate_range(start_date, end_date):
    validate_dates(start_date, end_date)
    if start_date > end_date:
        abort(400, description="start_date must not be after end_date.")

# --- Endpoint 1: Owned Data (Monolithic State) ---

def _read_owned_range(start_date, end_date):
    validate_range(start_date, end_date)
    try:
        with lock:
            data = json_handler.read_owned_range(start_date, end_date)
        return jsonify(data)
    except ValueError as e:
        abort(400, description=str(e))
    except PermissionError as e:
        abort(403, description=str(e))

@app.route('/api/owned/<date>', methods=['GET'])
def get_owned_day(date):
    return _read_owned_range(date, date)

@app.route('/api/owned/<start_date>/<end_date>', methods=['GET'])
def get_owned_range(start_date, end_date):
    return _read_owned_range(start_date, end_date)

@app.route('/api/owned/<date>', methods=['POST'])
def post_owned_day(date):
    validate_dates(date)

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        abort(400, description="Request body must be a JSON object mapping categories to one day of data.")

    # Validate categories up front; imported categories are pipeline-managed
    # and read-only via the API, so they are dropped from the write.
    owned_payload = {}
    for category, day_data in payload.items():
        try:
            domain = json_handler.resolve_domain(category)
        except ValueError as e:
            abort(400, description=str(e))
        if domain == "owned":
            owned_payload[category] = day_data

    try:
        with lock:
            # 1. Ground Truth Write
            json_handler.write_owned_day(date, owned_payload)

            # 2. Shadow Write
            try:
                sqlite_handler.write_owned_day(date, owned_payload)
            except Exception:
                print(f"[Shadow Write Error] SQLite Owned Data failed for {date}:\n{traceback.format_exc()}")

        return jsonify({"status": "ok"})
    except ValueError as e:
        abort(400, description=str(e))
    except PermissionError as e:
        abort(403, description=str(e))

# --- Endpoint 2: Telemetry Ingestion & Aggregation ---

@app.route('/api/telemetry/events', methods=['POST'])
def post_telemetry_events():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("daily_sessions"), list):
        abort(400, description='Request body must be a JSON object with a "daily_sessions" list.')

    # Firehose: routing metadata lives in each session, not the URL.
    # Group by (date, app_name) so each day's sessions are merged and written once.
    groups = {}
    for session in payload["daily_sessions"]:
        if not isinstance(session, dict):
            abort(400, description="Each entry in daily_sessions must be a JSON object.")

        date = session.get("date")
        app_name = session.get("app_name")
        if not is_valid_date(date):
            abort(400, description='Each session must carry a valid "date" (YYYY-MM-DD).')
        if not app_name or not isinstance(app_name, str):
            abort(400, description='Each session must carry an "app_name".')

        session = {k: v for k, v in session.items() if k not in SESSION_META_KEYS}
        groups.setdefault((date, app_name), []).append(session)

    with lock:
        for (date, app_name), new_sessions in groups.items():
            # telemetry.db is the source of truth: merge the chunk into the
            # stored sessions for this (date, app) and rewrite them.
            sqlite_handler.merge_telemetry(date, app_name, new_sessions)

    return jsonify({"status": "ok"})

@app.route('/api/telemetry/<date>', methods=['GET'])
def get_telemetry_day(date):
    return get_telemetry_range(date, date)

@app.route('/api/telemetry/<start_date>/<end_date>', methods=['GET'])
def get_telemetry_range(start_date, end_date):
    validate_range(start_date, end_date)
    with lock:
        data = sqlite_handler.read_telemetry_range(start_date, end_date)
    return jsonify(data)

# --- Endpoint 3: Imported Data ---

_IMPORTED_CATEGORIES = {"transactions", "apple_health", "spotify_streaming", "discord_messages"}

def _read_imported_range(start_date, end_date):
    validate_range(start_date, end_date)
    with lock:
        data = sqlite_handler.read_imported_range(start_date, end_date)
    return jsonify(data)

@app.route('/api/imported/<date>', methods=['GET'])
def get_imported_day(date):
    return _read_imported_range(date, date)

@app.route('/api/imported/<start_date>/<end_date>', methods=['GET'])
def get_imported_range(start_date, end_date):
    return _read_imported_range(start_date, end_date)

@app.route('/api/imported', methods=['POST'])
def post_imported():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        abort(400, description='Request body must be a JSON object with "category" and "records".')

    category = payload.get("category")
    records = payload.get("records")

    if category not in _IMPORTED_CATEGORIES:
        abort(400, description=f'Unknown category "{category}". Must be one of: {", ".join(sorted(_IMPORTED_CATEGORIES))}.')
    if not isinstance(records, list):
        abort(400, description='"records" must be a JSON array.')

    try:
        with lock:
            sqlite_handler.write_imported(category, records)
        return jsonify({"status": "ok", "written": len(records)})
    except Exception:
        print(f"[Imported Write Error] {category}:\n{traceback.format_exc()}")
        abort(500, description="Failed to write imported records to database.")

# --- Endpoint 5: Direct SQL Query Channel ---

def _query_error(message):
    return jsonify({"status": "error", "error_message": message}), 400

def _parse_query_payload():
    """Validates the shared {query, params} body shape. Returns (query, params)
    or (None, error_response)."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("query"), str):
        return None, _query_error('Request body must be a JSON object with a "query" string.')
    params = payload.get("params", [])
    if not isinstance(params, list):
        return None, _query_error('"params" must be a JSON array.')
    return (payload["query"], params), None

@app.route('/api/query/common/<source>', methods=['POST'])
def post_query_common(source):
    if source not in sqlite_query.VALID_SOURCES:
        return _query_error(
            f"Invalid source '{source}'. Must be one of: {', '.join(sqlite_query.VALID_SOURCES)}."
        )

    parsed, error = _parse_query_payload()
    if error:
        return error
    where_clause, params = parsed

    try:
        with lock:
            data = sqlite_query.common_query(source, where_clause, params)
        return jsonify({"status": "success", "data": data})
    except (sqlite3.Error, ValueError) as e:
        return _query_error(str(e))

@app.route('/api/query/custom', methods=['POST'])
def post_query_custom():
    parsed, error = _parse_query_payload()
    if error:
        return error
    query, params = parsed

    try:
        with lock:
            rows = sqlite_query.custom_query(query, params)
        return jsonify({"status": "success", "row_count": len(rows), "data": rows})
    except sqlite3.Error as e:
        return _query_error(str(e))

# --- Endpoint 4: Global Utilities & Config ---

@app.route('/api/system/config', methods=['GET'])
def get_system_config():
    with lock:
        data = json_handler.read_all_util()
    return jsonify(data)

# --- Error Handlers & Setup ---

@app.errorhandler(400)
def bad_request(e): return jsonify({"error": str(e.description)}), 400

@app.errorhandler(403)
def forbidden(e): return jsonify({"error": str(e.description)}), 403

def check_stop_signal():
    while True:
        if os.path.exists("server.stop"):
            print("[!] Shutdown signal file detected. Stopping server...")
            os.remove("server.stop")
            os._exit(0)
        time.sleep(1)

threading.Thread(target=check_stop_signal, daemon=True).start()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=4999, debug=False)
