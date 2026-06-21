import os
import sys
import json
import time
import shutil
import requests
from datetime import datetime

DB_URL = "http://127.0.0.1:4999"

TELEMETRY_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(TELEMETRY_DIR))

RAW_DIR = os.path.join(TELEMETRY_DIR, "raw")
BACKUP_DIR = os.path.join(TELEMETRY_DIR, "raw_backup")
STOP_FILE = os.path.join(TELEMETRY_DIR, "processor.stop")

# 10 GB limit for the backup buffer
MAX_BACKUP_SIZE_BYTES = 10 * 1024 * 1024 * 1024
ROLLOVER_OFFSET = 4 * 3600  # 4 hours in seconds

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

CLICK_MAP = {
    "0x201": "left",
    "0x204": "right",
    "0x207": "middle"
}

# State is now keyed by session_id, not app_name
session_states = {}

def get_session_state(session_id):
    if session_id not in session_states:
        session_states[session_id] = {
            "focus_start": None,
            "focus_title": "Unknown",
            "text_buffer": [],
            "text_start": None,
            "text_last": None
        }
    return session_states[session_id]

def get_logical_date_path(timestamp):
    """Returns YYYY/MM/DD adjusted for the 4 AM rollover."""
    adjusted_ts = timestamp - ROLLOVER_OFFSET
    return datetime.fromtimestamp(adjusted_ts).strftime('%Y/%m/%d')

def process_chunk(filepath, filename):
    # App name is the first part of the filename (e.g., brave_MessageListener_...)
    base_name = filename.replace(".json", "")
    app_name = base_name.split("_")[0].replace(".exe", "")

    with open(filepath, "r") as f:
        data = json.load(f)

    if not data:
        os.remove(filepath)
        return

    # Use the first event's timestamp to determine the logical day folder for this chunk
    logical_date_path = get_logical_date_path(data[0]["timestamp"])

    # We will build up a dictionary of new session data to merge later
    chunk_sessions = {}

    def init_chunk_session(sid, pid):
        if sid not in chunk_sessions:
            chunk_sessions[sid] = {
                "session_id": sid,
                "pid": pid,
                "session_start": None,
                "session_end": None,
                "focus": [],
                "left_clicks": [],
                "right_clicks": [],
                "middle_clicks": [],
                "text": []
            }
        return chunk_sessions[sid]

    def flush_text(state, sid_data):
        if state["text_buffer"]:
            duration = state["text_last"] - state["text_start"]
            sid_data["text"].append({
                "start_time": state["text_start"],
                "end_time": state["text_last"],
                "duration": round(duration, 3),
                "string": "".join(state["text_buffer"])
            })
            state["text_buffer"].clear()
            state["text_start"] = None
            state["text_last"] = None

    for event in data:
        # Default to "0" and -1 for legacy data backwards compatibility
        session_id = event.get("session_id", "0")
        pid = event.get("pid", -1)
        window_title = event.get("window_title", "Unknown")

        hex_id = event.get("msg_id")
        wparam = event.get("wparam")
        lparam = event.get("lparam")
        ts = event.get("timestamp")

        state = get_session_state(session_id)
        sid_data = init_chunk_session(session_id, pid)

        # Expand session boundaries
        if sid_data["session_start"] is None or ts < sid_data["session_start"]:
            sid_data["session_start"] = ts
        if sid_data["session_end"] is None or ts > sid_data["session_end"]:
            sid_data["session_end"] = ts

        if hex_id == "0x102":
            if not state["text_buffer"]:
                state["text_start"] = ts

            if wparam == 8:
                if state["text_buffer"]:
                    state["text_buffer"].pop()
            elif wparam == 13:
                state["text_buffer"].append("\n")
            elif 32 <= wparam <= 126:
                state["text_buffer"].append(chr(wparam))

            state["text_last"] = ts

        elif hex_id == "0x100" and wparam in (27, 37, 38, 39, 40):
            flush_text(state, sid_data)

        elif hex_id == "0x7":
            flush_text(state, sid_data)
            state["focus_start"] = ts
            state["focus_title"] = window_title

        elif hex_id == "0x8":
            flush_text(state, sid_data)
            if state["focus_start"] is not None:
                duration = ts - state["focus_start"]
                sid_data["focus"].append({
                    "start_time": state["focus_start"],
                    "end_time": ts,
                    "duration": round(duration, 3),
                    "window_title": state["focus_title"]
                })
                state["focus_start"] = None

        elif hex_id in CLICK_MAP:
            flush_text(state, sid_data)
            click_type = CLICK_MAP[hex_id]
            target_list = f"{click_type}_clicks"
            sid_data[target_list].append({
                "timestamp": ts,
                "position_x": lparam & 0xFFFF,
                "position_y": (lparam >> 16) & 0xFFFF
            })

    # --- 1. Ship to the database via the firehose endpoint ---
    # Routing metadata (date, app_name) travels in the payload body; the
    # database server handles merging into the existing daily sessions.
    date_key = logical_date_path.replace("/", "-")  # YYYY/MM/DD -> YYYY-MM-DD

    daily_sessions = []
    for chunk_session in chunk_sessions.values():
        chunk_session["date"] = date_key
        chunk_session["app_name"] = app_name
        daily_sessions.append(chunk_session)

    try:
        r = requests.post(f"{DB_URL}/api/telemetry/events", json={"daily_sessions": daily_sessions})
        r.raise_for_status()
    except requests.exceptions.ConnectionError:
        print(f"[DB ERROR] Database unreachable. {filename} will be retried next cycle.")
        raise

    # --- 2. Write to BACKUP_DIR ---
    date_dir_backup = os.path.join(BACKUP_DIR, logical_date_path)
    os.makedirs(date_dir_backup, exist_ok=True)
    backup_filepath = os.path.join(date_dir_backup, f"{app_name}.json")

    backup_data = []
    if os.path.exists(backup_filepath):
        with open(backup_filepath, "r") as f:
            try:
                backup_data = json.load(f)
            except json.JSONDecodeError:
                pass

    backup_data.extend(data)

    with open(backup_filepath, "w") as f:
        json.dump(backup_data, f, indent=4)

    # --- 3. Clean up the raw file ---
    os.remove(filepath)

def enforce_backup_limit():
    """Maintains the 10GB rolling buffer by deleting the oldest directories."""
    def get_dir_size(path):
        total = 0
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total += os.path.getsize(fp)
        return total

    while get_dir_size(BACKUP_DIR) > MAX_BACKUP_SIZE_BYTES:
        years = sorted([d for d in os.listdir(BACKUP_DIR) if os.path.isdir(os.path.join(BACKUP_DIR, d))])
        if not years: break

        oldest_year = os.path.join(BACKUP_DIR, years[0])
        months = sorted([d for d in os.listdir(oldest_year) if os.path.isdir(os.path.join(oldest_year, d))])

        if not months:
            shutil.rmtree(oldest_year)
            continue

        oldest_month = os.path.join(oldest_year, months[0])
        days = sorted([d for d in os.listdir(oldest_month) if os.path.isdir(os.path.join(oldest_month, d))])

        if not days:
            shutil.rmtree(oldest_month)
            continue

        oldest_day = os.path.join(oldest_month, days[0])
        shutil.rmtree(oldest_day)
        print(f"[*] Backup limit reached. Pruned oldest directory: {years[0]}/{months[0]}/{days[0]}")

def main():
    print("[*] Phase 2 Processor Daemon Started.")

    try:
        requests.get(f"{DB_URL}/api/system/config", timeout=2)
    except requests.exceptions.ConnectionError:
        print("[FATAL] Database server is not running on port 4999. Start database/server.py first.")
        sys.exit(1)

    try:
        while True:
            # 1. Immediate check before processing
            if os.path.exists(STOP_FILE):
                print("[!] Shutdown signal file detected.")
                break

            raw_files = [f for f in os.listdir(RAW_DIR) if f.endswith(".json")]
            for filename in raw_files:
                filepath = os.path.join(RAW_DIR, filename)
                try:
                    process_chunk(filepath, filename)
                    print(f"[+] Processed & Backed up: {filename}")
                except requests.exceptions.ConnectionError:
                    pass  # already logged in process_chunk
                except Exception as e:
                    print(f"[-] Error processing {filename}: {e}")

            enforce_backup_limit()

            # 2. Responsive Sleep: Sleep for 10 seconds, but check for the stop file every 1 second
            stopped = False
            for _ in range(10):
                if os.path.exists(STOP_FILE):
                    stopped = True
                    break
                time.sleep(1)

            if stopped:
                print("[!] Shutdown signal file detected.")
                break

    except KeyboardInterrupt:
        print("\n[!] Keyboard interrupt caught.")
    finally:
        if os.path.exists(STOP_FILE):
            os.remove(STOP_FILE)
        print("[!] Daemon shutting down.")

if __name__ == "__main__":
    main()
