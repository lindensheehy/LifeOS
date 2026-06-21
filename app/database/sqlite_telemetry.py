# Map click strings to enum integers to save disk space
_CLICK_MAP = {"left_clicks": 0, "right_clicks": 1, "middle_clicks": 2}
_CLICK_ENUM_TO_KEY = {v: k for k, v in _CLICK_MAP.items()}

def merge_sessions(daily_sessions: list, new_sessions: list) -> list:
    """Merges incoming chunk sessions into the existing daily sessions by session_id."""
    for chunk_session in new_sessions:
        sid = chunk_session.get("session_id")
        existing = next((s for s in daily_sessions if s.get("session_id") == sid), None)

        if existing:
            existing["session_start"] = min(existing["session_start"], chunk_session["session_start"])
            existing["session_end"] = max(existing["session_end"], chunk_session["session_end"])
            for key in ("focus", "left_clicks", "right_clicks", "middle_clicks", "text"):
                existing.setdefault(key, []).extend(chunk_session.get(key, []))
        else:
            daily_sessions.append(chunk_session)

    return daily_sessions

def read_day(conn, date: str, app_name: str) -> list:
    """Returns the stored sessions for a single (date, app_name), in the same
    shape replace_day consumes."""
    return read_range(conn, date, date).get(date, {}).get(app_name, [])

def _get_process_id(cursor, app_name: str) -> int:
    cursor.execute('INSERT OR IGNORE INTO processes (executable_name) VALUES (?)', (app_name,))
    cursor.execute('SELECT process_id FROM processes WHERE executable_name = ?', (app_name,))
    return cursor.fetchone()[0]

def replace_day(conn, date: str, app_name: str, payload: list):
    """Replaces all sessions for (date, app) with the supplied merged daily sessions."""
    cursor = conn.cursor()
    process_id = _get_process_id(cursor, app_name)

    # Child rows (focus_spans, clicks, text_inputs) are removed via ON DELETE CASCADE
    cursor.execute('DELETE FROM sessions WHERE date = ? AND process_id = ?', (date, process_id))

    for session in payload:
        cursor.execute('''
            INSERT INTO sessions (session_uuid, process_id, pid, date, start_time, end_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            session.get("session_id"),
            process_id,
            session.get("pid"),
            date,
            session.get("session_start"),
            session.get("session_end")
        ))
        session_id = cursor.lastrowid

        for span in session.get("focus", []):
            cursor.execute('''
                INSERT INTO focus_spans (session_id, window_title, start_time, end_time, duration)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                session_id,
                span.get("window_title"),
                span.get("start_time"),
                span.get("end_time"),
                span.get("duration")
            ))

        for click_key, enum_val in _CLICK_MAP.items():
            for click in session.get(click_key, []):
                cursor.execute('''
                    INSERT INTO clicks (session_id, click_type_enum, position_x, position_y, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    session_id,
                    enum_val,
                    click.get("position_x"),
                    click.get("position_y"),
                    click.get("timestamp")
                ))

        for text_entry in session.get("text", []):
            cursor.execute('''
                INSERT INTO text_inputs (session_id, content, timestamp)
                VALUES (?, ?, ?)
            ''', (
                session_id,
                text_entry.get("string"),
                text_entry.get("start_time")
            ))

def read_range(conn, start_date: str, end_date: str) -> dict:
    """Reconstructs {date: {app_name: [sessions]}} for the inclusive date range,
    filtering on the sessions.date TEXT column."""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.session_id, s.session_uuid, s.pid, s.date, s.start_time, s.end_time, p.executable_name
        FROM sessions s
        JOIN processes p ON s.process_id = p.process_id
        WHERE s.date BETWEEN ? AND ?
        ORDER BY s.date, p.executable_name, s.start_time
    ''', (start_date, end_date))
    session_rows = cursor.fetchall()

    result = {}
    for row_id, session_uuid, pid, date, start_time, end_time, app_name in session_rows:
        session = {
            "session_id": session_uuid,
            "pid": pid,
            "session_start": start_time,
            "session_end": end_time,
            "focus": [],
            "left_clicks": [],
            "right_clicks": [],
            "middle_clicks": [],
            "text": []
        }

        cursor.execute(
            'SELECT window_title, start_time, end_time, duration FROM focus_spans WHERE session_id = ? ORDER BY start_time',
            (row_id,)
        )
        for window_title, span_start, span_end, duration in cursor.fetchall():
            session["focus"].append({
                "window_title": window_title,
                "start_time": span_start,
                "end_time": span_end,
                "duration": duration
            })

        cursor.execute(
            'SELECT click_type_enum, position_x, position_y, timestamp FROM clicks WHERE session_id = ? ORDER BY timestamp',
            (row_id,)
        )
        for enum_val, pos_x, pos_y, timestamp in cursor.fetchall():
            key = _CLICK_ENUM_TO_KEY.get(enum_val, "left_clicks")
            session[key].append({
                "position_x": pos_x,
                "position_y": pos_y,
                "timestamp": timestamp
            })

        cursor.execute(
            'SELECT content, timestamp FROM text_inputs WHERE session_id = ? ORDER BY timestamp',
            (row_id,)
        )
        for content, timestamp in cursor.fetchall():
            session["text"].append({
                "string": content,
                "start_time": timestamp
            })

        result.setdefault(date, {}).setdefault(app_name, []).append(session)

    return result
