import os
import sys
import json
import hashlib
import requests
from collections import defaultdict

# --- Bulletproof Path Setup ---
PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))

UNPROCESSED_DIR = os.path.join(PIPELINE_DIR, "unprocessed")
PROCESSED_DIR   = os.path.join(PIPELINE_DIR, "processed")
FAILED_DIR      = os.path.join(PIPELINE_DIR, "failed")

DB_URL = "http://127.0.0.1:4999"

if PIPELINE_DIR not in sys.path:
    sys.path.insert(0, PIPELINE_DIR)

import dispatcher


def _post_imported(category, records):
    try:
        resp = requests.post(
            f"{DB_URL}/api/imported",
            json={"category": category, "records": records},
            timeout=120,
        )
        if resp.ok:
            print(f"DB: Wrote {len(records)} {category} records")
        else:
            print(f"[DB Write Error] /api/imported {category} returned {resp.status_code}: {resp.text}")
    except requests.exceptions.ConnectionError:
        print(f"[DB Write Error] Database server not reachable at {DB_URL}.")
    except Exception as e:
        print(f"[DB Write Error] /api/imported {category} failed: {e}")


def _generate_id(item_dict, occurrence):
    stable_dict = {k: v for k, v in item_dict.items() if k != 'id'}
    raw = json.dumps(stable_dict, sort_keys=True) + f"_occurrence:{occurrence}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]


def _assign_ids(records):
    """Assigns a deterministic content-based 'id' to every record in-place."""
    occurrence_tracker = defaultdict(int)
    for item in records:
        key = json.dumps({k: v for k, v in item.items() if k != 'id'}, sort_keys=True)
        item['id'] = _generate_id(item, occurrence_tracker[key])
        occurrence_tracker[key] += 1
    return records


def process_pipeline():
    print("--- Starting ETL Pipeline ---")
    os.makedirs(UNPROCESSED_DIR, exist_ok=True)

    files_to_process = [
        f for f in os.listdir(UNPROCESSED_DIR)
        if os.path.isfile(os.path.join(UNPROCESSED_DIR, f))
    ]

    if not files_to_process:
        print("No files found in unprocessed directory.")
        return

    for filename in files_to_process:
        filepath = os.path.join(UNPROCESSED_DIR, filename)

        payload = dispatcher.dispatch(
            filepath,
            processed_dir=PROCESSED_DIR,
            failed_dir=FAILED_DIR,
        )

        if not payload or 'data' not in payload or not payload['data']:
            continue

        category = payload['category']
        records  = _assign_ids(payload['data'])

        print(f"Master: Dispatched {len(records)} {category} records")
        _post_imported(category, records)


if __name__ == "__main__":
    process_pipeline()
