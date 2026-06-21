import os
import sys
import json
import psutil
import tkinter as tk
from tkinter import ttk, messagebox

PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
LAKE_DIR = os.path.dirname(PYTHON_DIR)
WHITELIST_PATH = os.path.join(LAKE_DIR, "util", "whitelist.json")
STOP_FILE = os.path.join(PYTHON_DIR, "whitelist_manager.stop")


def log(message):
    print(message)
    sys.stdout.flush()


def load_whitelist():
    try:
        with open(WHITELIST_PATH, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def get_running_processes():
    seen = set()
    for proc in psutil.process_iter(["name"]):
        try:
            name = proc.info["name"].lower()
            if name.endswith(".exe"):
                seen.add(name)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return seen


class WhitelistManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Process Whitelist Manager")
        self.root.geometry("420x540")
        self.root.minsize(300, 300)
        self.vars = {}
        self._build_ui()
        self._populate()
        self.root.after(500, self._check_stop)

    def _check_stop(self):
        if os.path.exists(STOP_FILE):
            log("[!] Stop signal received.")
            self.root.destroy()
            return
        self.root.after(500, self._check_stop)

    def _build_ui(self):
        top = tk.Frame(self.root)
        top.pack(fill=tk.X, padx=10, pady=(10, 0))
        tk.Button(top, text="Refresh", command=self._populate).pack(side=tk.LEFT)

        # Scrollable frame
        outer = tk.Frame(self.root, relief=tk.SUNKEN, bd=1)
        outer.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        self._canvas = tk.Canvas(outer, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=self._canvas.yview)
        self.scroll_frame = tk.Frame(self._canvas)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        )
        self._canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self._canvas.configure(yscrollcommand=scrollbar.set)

        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._canvas.bind("<Enter>", self._bind_mousewheel)
        self._canvas.bind("<Leave>", self._unbind_mousewheel)

        # Bottom bar
        bottom = tk.Frame(self.root)
        bottom.pack(fill=tk.X, padx=10, pady=(0, 10))
        tk.Button(bottom, text="Save", width=8, command=self._save).pack(side=tk.LEFT)
        self.status_label = tk.Label(bottom, text="", anchor="w")
        self.status_label.pack(side=tk.LEFT, padx=10)

    def _bind_mousewheel(self, _):
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, _):
        self._canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _populate(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.vars.clear()
        self.status_label.config(text="")

        whitelist = load_whitelist()
        running = get_running_processes()

        tracked = sorted(whitelist)
        untracked_running = sorted(p for p in running if p not in whitelist)

        if tracked:
            self._section_label("Tracked Processes")
            for name in tracked:
                is_running = name in running
                display = name if is_running else f"{name}  (not running)"
                fg = "#000000" if is_running else "#888888"
                self._add_row(name, checked=True, label=display, fg=fg)

        if untracked_running:
            self._section_label("Other Running Processes", top_pad=12)
            for name in untracked_running:
                self._add_row(name, checked=False, label=name, fg="#000000")

        if not tracked and not untracked_running:
            tk.Label(self.scroll_frame, text="No processes found.", fg="#888888").pack(anchor="w", padx=6, pady=6)

    def _section_label(self, text, top_pad=4):
        tk.Label(
            self.scroll_frame, text=text,
            font=(None, 9, "bold"), anchor="w"
        ).pack(fill=tk.X, padx=6, pady=(top_pad, 2))
        ttk.Separator(self.scroll_frame, orient="horizontal").pack(fill=tk.X, padx=6, pady=(0, 4))

    def _add_row(self, name, checked, label, fg):
        var = tk.BooleanVar(value=checked)
        self.vars[name] = var
        cb = tk.Checkbutton(
            self.scroll_frame, text=label, variable=var,
            anchor="w", fg=fg, activeforeground=fg
        )
        cb.pack(fill=tk.X, padx=6)

    def _save(self):
        checked = sorted(name for name, var in self.vars.items() if var.get())
        try:
            with open(WHITELIST_PATH, "w") as f:
                json.dump(checked, f, indent=4)
            log(f"Whitelist saved: {checked}")
            self.status_label.config(text="Saved.", fg="green")
            self.root.after(3000, lambda: self.status_label.config(text=""))
        except Exception as e:
            messagebox.showerror("Save failed", str(e))


def main():
    log("=== Whitelist Manager started ===")
    root = tk.Tk()
    WhitelistManager(root)
    root.mainloop()
    log("[+] Whitelist Manager closed.")


if __name__ == "__main__":
    main()
