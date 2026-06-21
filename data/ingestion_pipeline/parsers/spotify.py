import json

_PHONE_KEYWORDS    = ['android', 'ios', 'iphone', 'ipad']
_COMPUTER_KEYWORDS = ['windows', 'mac', 'os x', 'linux', 'web player', 'chrome', 'safari']

def _classify_device(platform):
    if not platform:
        return 'unknown'
    p = platform.lower()
    if any(kw in p for kw in _PHONE_KEYWORDS):
        return 'phone'
    if any(kw in p for kw in _COMPUTER_KEYWORDS):
        return 'computer'
    return 'unknown'

def parse(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        raw_records = json.load(f)

    records = []
    for item in raw_records:
        ts          = item.get('ts')
        track_uri   = item.get('spotify_track_uri')
        episode_uri = item.get('spotify_episode_uri')
        book_uri    = item.get('audiobook_uri')

        if track_uri:
            media_type  = 'track'
            title       = item.get('master_metadata_track_name')
            artist      = item.get('master_metadata_album_artist_name')
            album       = item.get('master_metadata_album_album_name')
            spotify_uri = track_uri
        elif episode_uri:
            media_type  = 'episode'
            title       = item.get('episode_name')
            artist      = item.get('episode_show_name')
            album       = None
            spotify_uri = episode_uri
        elif book_uri:
            media_type  = 'audiobook'
            title       = item.get('audiobook_chapter_title')
            artist      = None
            album       = item.get('audiobook_title')
            spotify_uri = book_uri
        else:
            media_type  = 'unknown'
            title = artist = album = spotify_uri = None

        records.append({
            'date':        ts.split('T')[0] if ts else None,
            'start_time':  ts,
            'media_type':  media_type,
            'title':       title,
            'artist':      artist,
            'album':       album,
            'spotify_uri': spotify_uri,
            'played_ms':   item.get('ms_played'),
            'device':      _classify_device(item.get('platform')),
        })

    return {
        'category': 'spotify_streaming',
        'data': records,
    }
