def _or_none(value):
    return None if (value is None or value == "") else value

def _to_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def read_range(conn, start_date: str, end_date: str) -> dict:
    """Returns {date: {category: [records]}} for all imported tables over the inclusive range."""
    cursor = conn.cursor()
    result = {}

    cursor.execute(
        "SELECT transaction_uuid, date, bank_company, account_type, amount, description,"
        " ws_activity_type, ws_symbol, ws_quantity"
        " FROM financial_transactions WHERE date BETWEEN ? AND ? ORDER BY date",
        (start_date, end_date),
    )
    for uuid, date, bank, acct, amount, desc, ws_type, ws_sym, ws_qty in cursor.fetchall():
        result.setdefault(date, {}).setdefault("transactions", []).append({
            "id": uuid, "date": date, "bank_company": bank, "account_type": acct,
            "amount": amount, "description": desc,
            "ws_activity_type": ws_type, "ws_symbol": ws_sym, "ws_quantity": ws_qty,
        })

    cursor.execute(
        "SELECT health_uuid, date, category, metric_type, source, value, unit, start_time, end_time"
        " FROM apple_health WHERE date BETWEEN ? AND ? ORDER BY date",
        (start_date, end_date),
    )
    for uuid, date, cat, metric, source, value, unit, start, end in cursor.fetchall():
        result.setdefault(date, {}).setdefault("apple_health", []).append({
            "id": uuid, "date": date, "category": cat, "type": metric,
            "source": source, "value": value, "unit": unit,
            "start_time": start, "end_time": end,
        })

    cursor.execute(
        "SELECT date, start_time, media_type, title, artist, album, spotify_uri, played_ms, device"
        " FROM spotify_streaming WHERE date BETWEEN ? AND ? ORDER BY date, start_time",
        (start_date, end_date),
    )
    for date, start, media, title, artist, album, uri, played, device in cursor.fetchall():
        result.setdefault(date, {}).setdefault("spotify_streaming", []).append({
            "date": date, "start_time": start, "media_type": media,
            "title": title, "artist": artist, "album": album,
            "spotify_uri": uri, "played_ms": played, "device": device,
        })

    cursor.execute(
        "SELECT message_uuid, date, timestamp, channel_id, channel_name,"
        " channel_type, contents, attachments"
        " FROM discord_messages WHERE date BETWEEN ? AND ? ORDER BY date, timestamp",
        (start_date, end_date),
    )
    for uuid, date, ts, cid, cname, ctype, contents, attachments in cursor.fetchall():
        result.setdefault(date, {}).setdefault("discord_messages", []).append({
            "id": uuid, "date": date, "timestamp": ts,
            "channel_id": cid, "channel_name": cname, "channel_type": ctype,
            "contents": contents, "attachments": attachments,
        })

    return result


def write_records(conn, category: str, records: list):
    """INSERT OR IGNORE a flat list of normalized imported records for one category."""
    cursor = conn.cursor()

    if category == "transactions":
        rows = [
            (
                item.get("id"),
                item.get("date"),
                item.get("bank_company"),
                item.get("account_type"),
                item.get("amount"),
                item.get("description"),
                _or_none(item.get("ws_activity_type")),
                _or_none(item.get("ws_symbol")),
                _to_float(item.get("ws_quantity")),
            )
            for item in records
        ]
        cursor.executemany("""
            INSERT OR IGNORE INTO financial_transactions
                (transaction_uuid, date, bank_company, account_type,
                 amount, description, ws_activity_type, ws_symbol, ws_quantity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows)

    elif category == "apple_health":
        rows = [
            (
                item.get("id"),
                item.get("date"),
                item.get("category"),
                item.get("type"),
                item.get("source"),
                _to_float(item.get("value")),
                item.get("unit"),
                item.get("start_time"),
                item.get("end_time"),
            )
            for item in records
        ]
        cursor.executemany("""
            INSERT OR IGNORE INTO apple_health
                (health_uuid, date, category, metric_type,
                 source, value, unit, start_time, end_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows)

    elif category == "spotify_streaming":
        rows = [
            (
                item.get("date"),
                item.get("start_time"),
                item.get("media_type"),
                item.get("title"),
                item.get("artist"),
                item.get("album"),
                item.get("spotify_uri"),
                item.get("played_ms"),
                item.get("device"),
            )
            for item in records
        ]
        chunk_size = 10_000
        for i in range(0, len(rows), chunk_size):
            cursor.executemany("""
                INSERT INTO spotify_streaming
                    (date, start_time, media_type, title, artist, album,
                     spotify_uri, played_ms, device)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows[i:i + chunk_size])

    elif category == "discord_messages":
        rows = [
            (
                item.get("message_uuid"),
                item.get("date"),
                item.get("timestamp"),
                item.get("channel_id"),
                item.get("channel_name"),
                item.get("channel_type"),
                item.get("contents"),
                _or_none(item.get("attachments")),
            )
            for item in records
        ]
        # Discord exports can be huge; insert in chunks to avoid building one
        # giant statement. INSERT OR IGNORE + UNIQUE(message_uuid) makes
        # re-ingestion idempotent on the message's natural snowflake key.
        chunk_size = 10_000
        for i in range(0, len(rows), chunk_size):
            cursor.executemany("""
                INSERT OR IGNORE INTO discord_messages
                    (message_uuid, date, timestamp, channel_id, channel_name,
                     channel_type, contents, attachments)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, rows[i:i + chunk_size])
