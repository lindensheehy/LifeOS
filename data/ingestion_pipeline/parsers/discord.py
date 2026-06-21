import json

# Discord export timestamps are space-separated local strings, e.g.
# "2025-08-30 21:42:06" (not ISO-8601 with a 'T').
def _split_date(timestamp):
    if not timestamp:
        return None
    return timestamp.split(' ')[0]

def _or_none(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None

def parse(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        raw_records = json.load(f)

    records = []
    for item in raw_records:
        # The Discord snowflake is the natural, globally-unique identity for a
        # message and serves as our dedup key downstream. Skip anything missing
        # it rather than poisoning the key space with NULLs.
        message_id = item.get('ID')
        if message_id is None:
            continue

        timestamp = item.get('Timestamp')

        records.append({
            'message_uuid': str(message_id),
            'date':         _split_date(timestamp),
            'timestamp':    timestamp,
            'channel_id':   item.get('ChannelID'),
            'channel_name': item.get('ChannelName'),
            'channel_type': item.get('ChannelType') or 'UNKNOWN',
            # Contents is the primary payload and may be very long; preserve it
            # verbatim (empty string => attachment-only / system message).
            'contents':     item.get('Contents'),
            'attachments':  _or_none(item.get('Attachments')),
        })

    return {
        'category': 'discord_messages',
        'data': records,
    }
