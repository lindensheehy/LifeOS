import os
import sys
import time
import signal
import requests
import psutil
import ctypes
import ctypes.wintypes
import win32gui
import win32process
import win32con

# Import our modularized components
import build
from endpoint import MessageEndpoint

# Resolve directories
PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
TRACKING_DIR = os.path.dirname(PYTHON_DIR)
BIN_DIR = os.path.join(TRACKING_DIR, "bin")
STOP_FILE = os.path.join(PYTHON_DIR, "injector.stop")

DB_URL = "http://127.0.0.1:4999"

WM_INCEPTION_CONFIG = win32con.WM_USER + 1
FLUSH_INTERVAL = 300  # 5 minutes

def load_whitelist():
    try:
        r = requests.get(f"{DB_URL}/api/system/config")
        r.raise_for_status()
        return set(r.json().get("whitelist", []))
    except requests.exceptions.ConnectionError:
        log("[DB ERROR] Database server unreachable. Whitelist fetch failed, using empty set.")
        return set()
    except requests.exceptions.RequestException as e:
        log(f"[DB ERROR] Whitelist fetch failed: {e}. Using empty set.")
        return set()

def log(message):
    """Helper function for flushing logs so the controller can pick them up immediately."""
    print(message)
    sys.stdout.flush()

def graceful_exit(signum, frame):
    raise KeyboardInterrupt

signal.signal(signal.SIGTERM, graceful_exit)
signal.signal(signal.SIGINT, graceful_exit)

def get_new_targets(hooked_threads):
    """Scans for active UI threads of whitelisted apps that aren't already hooked."""
    whitelist = load_whitelist()
    targets = []
    seen_threads = set(hooked_threads)

    def enum_callback(hwnd, _):
        tid, pid = win32process.GetWindowThreadProcessId(hwnd)

        if tid in seen_threads:
            return True

        try:
            proc = psutil.Process(pid)
            proc_name = proc.name().lower()

            if proc_name in whitelist:
                targets.append((proc_name, pid, tid, hwnd))
                seen_threads.add(tid)

                # --- Chromium/Electron Child Window Sweep ---
                def enum_child_callback(child_hwnd, _):
                    child_tid, child_pid = win32process.GetWindowThreadProcessId(child_hwnd)
                    if child_tid not in seen_threads:
                        try:
                            child_proc = psutil.Process(child_pid)
                            if child_proc.name().lower() in whitelist:
                                targets.append((child_proc.name().lower(), child_pid, child_tid, child_hwnd))
                                seen_threads.add(child_tid)
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    return True

                win32gui.EnumChildWindows(hwnd, enum_child_callback, None)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        return True

    win32gui.EnumWindows(enum_callback, None)
    return targets

def main():
    log("=== Starting Telemetry Injector ===")

    # 0. Verify database server is up before doing anything else
    try:
        requests.get(f"{DB_URL}/api/system/config", timeout=2)
    except requests.exceptions.ConnectionError:
        log("[FATAL] Database server is not running on port 4999. Start database/server.py first.")
        sys.exit(1)

    # 1. Run the build/pre-flight checks
    if not build.ensure_directories() or not build.compile_hooks():
        log("[-] Pre-flight failed. Exiting.")
        sys.exit(1)

    # 2. Load the compiled DLL
    dll_path = os.path.join(BIN_DIR, "messageHook.dll")
    try:
        hook_dll = ctypes.WinDLL(dll_path)
    except Exception as e:
        log(f"[-] Failed to load {dll_path}: {e}")
        sys.exit(1)

    install_hooks = hook_dll.InstallHooks
    install_hooks.restype = ctypes.wintypes.BOOL
    install_hooks.argtypes = [ctypes.wintypes.DWORD]

    # 3. State management for dynamic hooks
    endpoints = {}  # Map of tid -> MessageEndpoint
    
    gui_mode = os.environ.get("GUI_MODE") == "1"
    loop_counter = 0
    last_flush_time = time.time()
    last_buffered_msgs = -1
    
    log("[*] Entering dynamic injection and telemetry loop. Press Ctrl+C to exit.")

    try:
        while True:
            # Check for external shutdown signal (matches controller.py)
            if os.path.exists(STOP_FILE):
                log("[!] Shutdown signal file detected.")
                break

            # Pump messages for all active MessageEndpoints
            win32gui.PumpWaitingMessages()
            
            current_time = time.time()
            
            # --- DYNAMIC DISCOVERY & CLEANUP (Run roughly every 5 seconds) ---
            if loop_counter % 100 == 0:
                
                # A. Clean up closed processes
                dead_tids = []
                for tid, ep in endpoints.items():
                    try:
                        proc = psutil.Process(ep.target_pid)
                        # Check if the thread still exists inside the process
                        if not any(t.id == tid for t in proc.threads()):
                            dead_tids.append(tid)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        dead_tids.append(tid)

                for tid in dead_tids:
                    ep = endpoints.pop(tid)
                    if gui_mode:
                        log(f"[-] Process closed. Cleaning up {ep.target_name} (PID: {ep.target_pid}, TID: {tid})")
                    ep.destroy() # Automatically flushes remaining data to disk
                
                # B. Hook new processes
                new_targets = get_new_targets(endpoints.keys())
                for name, pid, tid, hwnd in new_targets:
                    if install_hooks(tid):
                        # Pass PID and HWND to the endpoint on creation
                        ep = MessageEndpoint(name, pid, hwnd)
                        endpoints[tid] = ep
                        win32gui.SendMessage(hwnd, WM_INCEPTION_CONFIG, ep.hwnd, 0)
                        if gui_mode:
                            log(f"[+] Hooked new thread: {name} (PID: {pid}, TID: {tid})")

                # C. Log active un-flushed buffer counts
                if gui_mode:
                    buffered_msgs = sum(len(ep.message_buffer) for ep in endpoints.values())
                    if buffered_msgs != last_buffered_msgs:
                        log(f"[*] Current buffered messages (unflushed): {buffered_msgs}")
                        last_buffered_msgs = buffered_msgs

            # --- AUTO-FLUSH LOGIC (5 MINUTE INTERVAL) ---
            if current_time - last_flush_time >= FLUSH_INTERVAL:
                for ep in endpoints.values():
                    ep.flush_to_disk()
                if gui_mode:
                    log("[*] Auto-dump triggered: Flushed all active buffers to disk.")
                last_flush_time = current_time

            time.sleep(0.05)
            loop_counter += 1
            
    except KeyboardInterrupt:
        log("\n[!] Ctrl+C caught. Breaking the telemetry loop...")
    finally:
        log("[*] Cleaning up hooks and windows...")
        hook_dll.RemoveHooks() 
        
        for ep in endpoints.values():
            ep.destroy()
            
        if os.path.exists(STOP_FILE):
            os.remove(STOP_FILE)
            
        log("[+] Hooks and endpoints removed cleanly.")

if __name__ == "__main__":
    main()