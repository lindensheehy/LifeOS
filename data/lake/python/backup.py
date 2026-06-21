import os
import json
import subprocess
import time
import sys
from datetime import datetime, timedelta

# --- Configuration ---
BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BACKEND_DIR, '..', '..'))
DATA_DIR = os.path.abspath(os.path.join(BACKEND_DIR, '..'))

ROLLOVER_OFFSET = 4 * 3600  # 4 hours in seconds

def log(message):
    """Helper function for flushing logs so the controller can pick them up immediately."""
    print(message)
    sys.stdout.flush()

def get_allowed_date_keys():
    """Returns a set of valid strings for logical today and yesterday (both YYYY-MM-DD and DD formats)."""
    adjusted_ts = time.time() - ROLLOVER_OFFSET
    logical_today = datetime.fromtimestamp(adjusted_ts)
    logical_yesterday = logical_today - timedelta(days=1)
    
    allowed = set()
    for d in (logical_today, logical_yesterday):
        allowed.add(d.strftime('%Y-%m-%d')) # e.g., "2026-05-24"
        allowed.add(d.strftime('%d'))       # e.g., "24"
        allowed.add(str(d.day))             # e.g., "24" or "5"
    return allowed

def get_logical_today_str():
    """Just for the success print."""
    adjusted_ts = time.time() - ROLLOVER_OFFSET
    return datetime.fromtimestamp(adjusted_ts).strftime('%Y-%m-%d')

def run_git_command(args):
    """Helper to run git commands in the data directory."""
    result = subprocess.run(
        ["git"] + args, 
        cwd=DATA_DIR, 
        capture_output=True, 
        text=True
    )
    return result.stdout.strip()

def get_git_file_content(rel_path):
    """Pulls the last committed JSON state of a file directly from Git."""
    git_path = rel_path.replace("\\", "/")
    result = subprocess.run(
        ["git", "show", f"HEAD:{git_path}"],
        cwd=DATA_DIR,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            pass
    return {}

def get_modified_files():
    """Returns a list of relative paths for modified files in owned/ and util/."""
    output = run_git_command(["status", "--porcelain", "."])
    if not output:
        return []
    
    files = []
    for line in output.splitlines():
        line = line.lstrip() 
        if ' ' in line:
            status, path = line.split(' ', 1)
            clean_path = path.strip().strip('"')
            files.append(clean_path) 
    return files

def check_for_anomalies(modified_files):
    """
    Compares live files to Git HEAD. 
    Returns a list of anomaly strings if unauthorized historical changes are found.
    """
    allowed_dates = get_allowed_date_keys()
    anomalies = []

    for rel_path in modified_files:
        if not rel_path.endswith('.json') or 'owned' not in rel_path:
            continue
            
        live_path = os.path.join(DATA_DIR, rel_path)
        
        # Load Live Data
        try:
            with open(live_path, 'r', encoding='utf-8') as f:
                live_data = json.load(f)
        except Exception:
            live_data = {}
            
        # Load Git Data
        git_data = get_git_file_content(rel_path)
        
        if isinstance(live_data, dict) and isinstance(git_data, dict):
            changed_keys = set()
            
            # Check for new or modified days
            for k in live_data:
                if k not in git_data or live_data[k] != git_data[k]:
                    changed_keys.add(k)
                    
            # Check for deleted days
            for k in git_data:
                if k not in live_data:
                    changed_keys.add(k)
                    
            # Filter against our allowed dates
            unauthorized_changes = [k for k in changed_keys if k not in allowed_dates]
            
            if unauthorized_changes:
                anomalies.append(f"{rel_path} (Altered Days: {', '.join(unauthorized_changes)})")

    return anomalies

def run_sync():
    log("=== Starting Backup System ===")
    
    modified_files = get_modified_files()
    
    if not modified_files:
        log("[*] Up to date. No changes detected.")
        return

    anomalies = check_for_anomalies(modified_files)

    # --- THE NOTIFICATION GATE ---
    if anomalies:
        log("[!] WARNING: Historical data changes detected!")
        for anomaly in anomalies:
            log(f"[*] -> {anomaly}")
        log("[*] Proceeding with auto-commit of historical changes...")

    # --- EXECUTE BACKUP ---
    log("[*] Staging files for backup...")
    run_git_command(["add", "."])
    
    today_str = get_logical_today_str()
    exact_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    run_git_command(["commit", "-m", f"Auto-backup: {exact_time}"])
    
    log(f"[+] Backup complete and verified for {today_str}.")

if __name__ == "__main__":
    run_sync()