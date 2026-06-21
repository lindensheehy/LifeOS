import os
import sys
import time
import subprocess
import threading
import atexit
import argparse
from flask import Flask, render_template
from datetime import datetime
from routes import api_bp
import cache as cache_layer

# 1. Figure out where we are currently sitting
BASE_DIR = os.path.abspath(os.path.dirname(__file__))       # Gets the /backend/ folder
PROJECT_ROOT = os.path.dirname(BASE_DIR)                    # Goes up one level to /journal_project/

# 2. Define exactly where the frontend lives
FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'frontend')
HTML_DIR = os.path.join(FRONTEND_DIR, 'html')

# 3. Tell Flask to use our custom folders
app = Flask(__name__, 
            template_folder=HTML_DIR,   # Looks here for render_template()
            static_folder=FRONTEND_DIR, # Looks here for CSS, JS, Images, etc.
            static_url_path=''          # Strips the default '/static' prefix from URLs
)

app.register_blueprint(api_bp)

@app.route('/')
def home():
    return render_template('index.html')

def prewarm_cache():
    cache_layer.cache.preload_util()
    
    # Grab the current year-month (e.g., "2026-05")
    current_month = datetime.now().strftime("%Y-%m")
    cache_layer.cache.load_month(current_month)

_bundler_processes = []

def cleanup_bundlers():
    if not _bundler_processes:
        return
    print("\nStopping esbuild watchers...")
    for proc in _bundler_processes:
        proc.terminate()
    for proc in _bundler_processes:
        proc.wait()

def start_bundler_watch():
    """Starts esbuild in watch mode in the background"""
    print("Starting esbuild watch mode for JS and CSS...")

    esbuild_exe = os.path.join(BASE_DIR, 'esbuild.exe')

    # --- JAVASCRIPT BUNDLER ---
    js_entry = os.path.join(FRONTEND_DIR, 'js', 'main.js')
    js_out = os.path.join(FRONTEND_DIR, 'js', 'bundle.js')

    js_process = subprocess.Popen([
        esbuild_exe,
        js_entry,
        "--bundle",
        f"--outfile={js_out}",
        "--sourcemap",
        "--watch=forever"
    ])

    # --- CSS BUNDLER ---
    css_entry = os.path.join(FRONTEND_DIR, 'css', 'main.css')
    css_out = os.path.join(FRONTEND_DIR, 'css', 'bundle.css')

    css_process = subprocess.Popen([
        esbuild_exe,
        css_entry,
        "--bundle",
        f"--outfile={css_out}",
        "--sourcemap",
        "--watch=forever"
    ])

    _bundler_processes.extend([js_process, css_process])
    atexit.register(cleanup_bundlers)

def check_stop_signal():
    """Background thread that constantly watches for the controller's stop file."""
    while True:
        if os.path.exists("server.stop"):
            print("[!] Shutdown signal file detected. Stopping server...")
            os.remove("server.stop")
            cleanup_bundlers()
            os._exit(0)  # Immediately kills the Flask process
        time.sleep(1)

# Start the watcher thread before starting the Flask server
threading.Thread(target=check_stop_signal, daemon=True).start()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args()

    if not cache_layer.ping():
        print("[FATAL] Database server is not running on port 4999. Start database/server.py first.")
        sys.exit(1)

    prewarm_cache()
    start_bundler_watch()
    # use_reloader=False keeps Flask as a single process, which makes the stop
    # file signal reliable (no Werkzeug child-process that gets restarted on exit).
    app.run(debug=True, use_reloader=False, port=args.port)