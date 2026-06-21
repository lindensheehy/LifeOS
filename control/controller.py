import tkinter as tk
from tkinter import ttk
import subprocess
import os
import sys
import re
import threading
import logging
from datetime import datetime

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

class MasterController(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LifeOS Controller")
        self.geometry("1500x660")
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.log_dir = os.path.join(self.root_dir, "logs")
        os.makedirs(self.log_dir, exist_ok=True)

        controller_log_path = os.path.join(self.log_dir, "controller.log")
        _handler = logging.FileHandler(controller_log_path, encoding='utf-8')
        _handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S'))
        self.clog = logging.getLogger('MasterController')
        self.clog.setLevel(logging.INFO)
        self.clog.addHandler(_handler)
        self.clog.propagate = False
        self.clog.info("=== Controller started ===")

        self.processes = {}

        self.prod_services = {
            "Backend (Prod)":  {"script": "server.py",    "dir": os.path.join("prod", "backend"),            "args": ["--port", "5000"]},
            "Injector (Prod)": {"script": "injector.py",  "dir": os.path.join("prod", "tracking", "python")},
            "Database (Prod)": {"script": "server.py",    "dir": os.path.join("prod", "database")},
            "Processor":       {"script": "processor.py", "dir": os.path.join("data", "telemetry")},
        }

        self.dev_services = {
            "Backend (Dev)":   {"script": "server.py",    "dir": os.path.join("dev",  "backend"),            "args": ["--port", "5001"]},
            "Injector (Dev)":  {"script": "injector.py",  "dir": os.path.join("dev",  "tracking", "python")},
            "Database (Dev)":  {"script": "server.py",    "dir": os.path.join("dev",  "database")},
        }

        self.service_configs = {**self.prod_services, **self.dev_services}

        self.script_configs = {
            "Backup":          {"script": "backup.py", "dir": os.path.join("data", "lake", "python")},
            "Import Pipeline": {"script": "master.py", "dir": os.path.join("data", "ingestion_pipeline")},
        }

        self.tools_configs = {
            "Deploy":    {"script": "deploy.py",            "dir": "control"},
            "Whitelist": {"script": "whitelist_manager.py", "dir": os.path.join("data", "lake", "python")},
        }

        self.all_configs = {**self.service_configs, **self.script_configs, **self.tools_configs}

        self.log_files = {}
        for app_name, config in self.all_configs.items():
            clean_dir    = config["dir"].replace("\\", "_").replace("/", "_")
            clean_script = config["script"].replace(".py", "")
            self.log_files[app_name] = os.path.join(self.log_dir, f"{clean_dir}_{clean_script}.log")
        self.log_files["Controller"] = os.path.join(self.log_dir, "controller.log")

        # Which log tabs are visible for each left panel tab
        self.log_groups = {
            "Prod":    list(self.prod_services.keys()) + ["Controller"],
            "Dev":     list(self.dev_services.keys())  + ["Controller"],
            "Scripts": list(self.script_configs.keys()) + ["Controller"],
            "Tools":   list(self.tools_configs.keys())  + ["Controller"],
        }

        self.file_cursors   = {name: 0 for name in self.log_files}
        self.text_widgets   = {}
        self.status_labels  = {}
        self.action_buttons = {}
        self.log_tab_frames = {}

        self.create_widgets()
        self.poll_logs()

    def create_widgets(self):
        # --- Left panel ---
        control_frame = ttk.Frame(self, width=420, padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y)
        control_frame.pack_propagate(False)

        ttk.Label(control_frame, text="System Controls", font=("Arial", 14, "bold")).pack(pady=(0, 10))

        self.control_notebook = ttk.Notebook(control_frame)
        self.control_notebook.pack(fill=tk.BOTH, expand=True)
        self.control_notebook.bind("<<NotebookTabChanged>>", self._on_left_tab_changed)

        prod_tab    = ttk.Frame(self.control_notebook, padding=5)
        dev_tab     = ttk.Frame(self.control_notebook, padding=5)
        scripts_tab = ttk.Frame(self.control_notebook, padding=5)
        tools_tab   = ttk.Frame(self.control_notebook, padding=5)

        self.control_notebook.add(prod_tab,    text="Prod")
        self.control_notebook.add(dev_tab,     text="Dev")
        self.control_notebook.add(scripts_tab, text="Scripts")
        self.control_notebook.add(tools_tab,   text="Tools")

        # Prod tab
        btn_bar = ttk.Frame(prod_tab)
        btn_bar.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(btn_bar, text="▶ Start All", command=self.start_all_prod).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(btn_bar, text="⏹ Stop All",  command=self.stop_all_prod ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        for name, config in self.prod_services.items():
            self._build_service_row(prod_tab, name, config)

        # Dev tab
        btn_bar = ttk.Frame(dev_tab)
        btn_bar.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(btn_bar, text="▶ Start All", command=self.start_all_dev).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(btn_bar, text="⏹ Stop All",  command=self.stop_all_dev ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        for name, config in self.dev_services.items():
            self._build_service_row(dev_tab, name, config)

        # Scripts tab
        for app_name, config in self.script_configs.items():
            self._build_oneshot_row(scripts_tab, app_name, config)

        # Tools tab
        for app_name, config in self.tools_configs.items():
            self._build_oneshot_row(tools_tab, app_name, config)

        # --- Right panel: log viewer ---
        log_frame = ttk.Frame(self, padding=10)
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.log_notebook = ttk.Notebook(log_frame)
        self.log_notebook.pack(fill=tk.BOTH, expand=True)

        for name in self.log_files:
            tab = ttk.Frame(self.log_notebook)
            self.log_notebook.add(tab, text=name)
            self.log_tab_frames[name] = tab

            txt = tk.Text(tab, wrap=tk.WORD, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 10))
            txt.pack(fill=tk.BOTH, expand=True)
            self.text_widgets[name] = txt

            if os.path.exists(self.log_files[name]):
                with open(self.log_files[name], "r", encoding="utf-8") as f:
                    content = f.read()
                    txt.insert(tk.END, content)
                    self.file_cursors[name] = f.tell()
                    txt.see(tk.END)

        # Set initial log filter to match the default selected left tab (Prod)
        self._apply_log_filter("Prod")

    def _build_service_row(self, parent, name, config):
        frame = ttk.LabelFrame(parent, text=name, padding=6)
        frame.pack(fill=tk.X, pady=4)
        row = ttk.Frame(frame)
        row.pack(fill=tk.X)

        lbl = ttk.Label(row, text="⚫ Offline", foreground="gray")
        lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.status_labels[name] = lbl

        btn = ttk.Button(row, text="▶ Start", width=8,
                         command=lambda k=name, c=config: self.toggle_process(k, c))
        btn.pack(side=tk.RIGHT)
        self.action_buttons[name] = btn

    def _build_oneshot_row(self, parent, name, config):
        frame = ttk.LabelFrame(parent, text=name, padding=8)
        frame.pack(fill=tk.X, pady=5)
        row = ttk.Frame(frame)
        row.pack(fill=tk.X)

        lbl = ttk.Label(row, text="⚫ Ready", foreground="gray")
        lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.status_labels[name] = lbl

        btn = ttk.Button(row, text="▶ Run", width=8,
                         command=lambda k=name, c=config: self.toggle_process(k, c))
        btn.pack(side=tk.RIGHT)
        self.action_buttons[name] = btn

    def _on_left_tab_changed(self, event):
        selected = self.control_notebook.tab(self.control_notebook.select(), 'text')
        self._apply_log_filter(selected)

    def _apply_log_filter(self, group_name: str):
        visible = set(self.log_groups.get(group_name, []))

        # Select a visible tab first so tkinter never has a hidden tab selected
        for name in self.log_groups.get(group_name, []):
            if name in self.log_tab_frames:
                self.log_notebook.select(self.log_tab_frames[name])
                break

        for name, frame in self.log_tab_frames.items():
            self.log_notebook.tab(frame, state='normal' if name in visible else 'hidden')

    def toggle_process(self, name, config):
        if name in self.processes and self.processes[name][0].poll() is None:
            self.stop_process(name)
        else:
            self.launch_process(name, config["script"], config["dir"], config.get("args"))

    def launch_process(self, name, script_name, working_dir, extra_args=None):
        if name in self.processes and self.processes[name][0].poll() is None:
            return

        self.clog.info(f"Launching '{name}' | script={script_name} | dir={working_dir}")
        log_file = open(self.log_files[name], "a", encoding="utf-8")

        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"\n\n\n{'='*20} NEW RUN STARTING - {start_time} {'='*20}\n")
        log_file.flush()

        env = os.environ.copy()
        env["GUI_MODE"] = "1"

        cmd = [sys.executable, "-u", script_name] + (extra_args or [])

        kwargs = {}
        if os.name == 'nt':
            kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW

        proc = subprocess.Popen(
            cmd,
            cwd=os.path.join(self.root_dir, working_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            **kwargs
        )

        def stream_reader(pipe, file):
            try:
                for line in iter(pipe.readline, b''):
                    decoded_line = line.decode('utf-8', errors='replace').rstrip('\r\n')
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    file.write(f"[{timestamp}] {decoded_line}\n")
                    file.flush()
            except (ValueError, OSError):
                pass

        threading.Thread(target=stream_reader, args=(proc.stdout, log_file), daemon=True).start()

        self.processes[name] = (proc, log_file)
        self.clog.info(f"'{name}' launched (pid={proc.pid})")

        self.action_buttons[name].config(text="⏹ Stop")
        if name in self.service_configs:
            self.status_labels[name].config(text="🟢 Online", foreground="green")
        else:
            self.status_labels[name].config(text="🟢 Running...", foreground="green")

    def stop_process(self, name):
        if name in self.processes:
            proc, log_file = self.processes[name]

            config = self.all_configs[name]
            script_base = config["script"].replace(".py", "")
            stop_file = os.path.join(self.root_dir, config["dir"], f"{script_base}.stop")

            self.clog.info(f"Stopping '{name}' (pid={proc.pid}) via stop file: {stop_file}")
            with open(stop_file, "w") as f:
                f.write("stop")

            try:
                proc.wait(timeout=2)
                self.clog.info(f"'{name}' exited cleanly")
            except subprocess.TimeoutExpired:
                self.clog.info(f"'{name}' did not exit in time — sending terminate()")
                proc.terminate()

            if os.path.exists(stop_file):
                try:
                    os.remove(stop_file)
                except OSError:
                    pass

            log_file.close()
            del self.processes[name]

        if name in self.service_configs:
            self.status_labels[name].config(text="⚫ Offline", foreground="gray")
            self.action_buttons[name].config(text="▶ Start")
        else:
            self.status_labels[name].config(text="⚫ Ready", foreground="gray")
            self.action_buttons[name].config(text="▶ Run")

    def start_all_prod(self):
        self.clog.info("Starting all Prod services")
        for name, config in self.prod_services.items():
            self.launch_process(name, config["script"], config["dir"], config.get("args"))

    def stop_all_prod(self):
        self.clog.info("Stopping all Prod services")
        for name in list(self.prod_services.keys()):
            if name in self.processes:
                self.stop_process(name)

    def start_all_dev(self):
        self.clog.info("Starting all Dev services")
        for name, config in self.dev_services.items():
            self.launch_process(name, config["script"], config["dir"], config.get("args"))

    def stop_all_dev(self):
        self.clog.info("Stopping all Dev services")
        for name in list(self.dev_services.keys()):
            if name in self.processes:
                self.stop_process(name)

    def poll_logs(self):
        for app_name in list(self.processes.keys()):
            proc, _ = self.processes[app_name]
            if proc.poll() is not None:
                self.clog.info(f"'{app_name}' stopped unexpectedly (exit code={proc.poll()}) — cleaning up")
                self.stop_process(app_name)

        for name, filepath in self.log_files.items():
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    f.seek(self.file_cursors[name])
                    new_data = f.read()
                    if new_data:
                        clean_data = ANSI_ESCAPE.sub('', new_data)
                        self.text_widgets[name].insert(tk.END, clean_data)
                        self.text_widgets[name].see(tk.END)
                    self.file_cursors[name] = f.tell()

        self.after(500, self.poll_logs)

    def destroy(self):
        self.clog.info("=== Controller shutting down ===")
        for app_name in list(self.processes.keys()):
            self.stop_process(app_name)
        super().destroy()

if __name__ == "__main__":
    app = MasterController()
    app.mainloop()
