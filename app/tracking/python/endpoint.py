import os
import time
import json
import uuid
import win32gui
import win32api
import win32con
import sys

# Resolve directories up to the project root
PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
TRACKING_DIR = os.path.dirname(PYTHON_DIR)
ROOT_DIR = os.path.dirname(os.path.dirname(TRACKING_DIR))
RAW_DIR = os.path.join(ROOT_DIR, "data", "telemetry", "raw")

os.makedirs(RAW_DIR, exist_ok=True)

CHUNK_SIZE = 10000

class MessageEndpoint:
    _class_counter = 0

    def __init__(self, target_name, target_pid, target_hwnd):
        MessageEndpoint._class_counter += 1
        self.class_name = f"MessageListener_{MessageEndpoint._class_counter}"
        self.target_name = target_name
        self.target_pid = target_pid
        self.target_hwnd = target_hwnd
        
        # Unique session ID for processor.py to group by
        self.session_id = str(uuid.uuid4())
        
        self.message_count = 0
        self.last_hex_id = "0x0"
        self.message_buffer = [] 
        
        self.wc = win32gui.WNDCLASS()
        self.wc.lpfnWndProc = self.wndproc 
        self.wc.lpszClassName = self.class_name
        self.wc.hInstance = win32api.GetModuleHandle(None)
        
        self.class_atom = win32gui.RegisterClass(self.wc)
        self.hwnd = win32gui.CreateWindow(
            self.class_atom, "Listener", 0, 0, 0, 0, 0, 0, 0, self.wc.hInstance, None
        )

    def get_window_title(self):
        """Fetches the actual title of the root window, avoiding blank child control titles."""
        try:
            # GA_ROOT (2) ensures we get the main window title even if we hooked a child thread
            root_hwnd = win32gui.GetAncestor(self.target_hwnd, win32con.GA_ROOT)
            return win32gui.GetWindowText(root_hwnd)
        except Exception:
            # Windows HWNDs can disappear mid-execution, fail gracefully
            return ""

    def wndproc(self, hwnd, msg, wparam, lparam):
        if msg >= win32con.WM_APP:
            real_msg_id = msg - win32con.WM_APP
            hex_id = hex(real_msg_id)
            
            event_data = {
                "msg_id": hex_id,
                "wparam": wparam,
                "lparam": lparam,
                "timestamp": time.time(),
                "pid": self.target_pid,
                "session_id": self.session_id,
                "window_title": self.get_window_title()
            }
            
            self.message_buffer.append(event_data)
            self.message_count += 1
            self.last_hex_id = hex_id
            
            if len(self.message_buffer) >= CHUNK_SIZE:
                self.flush_to_disk()
            
            return 0
        
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
        
    def flush_to_disk(self):
        if not self.message_buffer:
            return

        timestamp_str = str(int(time.time() * 1000))
        stem = f"{self.target_name}_{self.class_name}_{timestamp_str}"
        tmp_path = os.path.join(RAW_DIR, stem + ".tmp")
        final_path = os.path.join(RAW_DIR, stem + ".json")

        try:
            with open(tmp_path, "w") as f:
                json.dump(self.message_buffer, f, indent=4)
            os.replace(tmp_path, final_path)
        except Exception as e:
            print(f"\n[-] Failed to flush buffer to disk: {e}")

        self.message_buffer.clear()

    def destroy(self):
        # Flush whatever we have immediately
        self.flush_to_disk()
        
        # Safely tell the window's owning thread to close it
        if hasattr(self, 'hwnd') and self.hwnd:
            win32gui.PostMessage(self.hwnd, win32con.WM_CLOSE, 0, 0)
            
        if hasattr(self, 'class_atom') and self.class_atom:
            try:
                win32gui.UnregisterClass(self.class_atom, self.wc.hInstance)
            except Exception:
                pass