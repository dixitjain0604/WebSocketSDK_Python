#!/usr/bin/env python3
"""
One-button launcher for WebSocketSDK
Starts: DeviceBroker daemon + Django web app
Usage:  python start_all.py
"""

import os
import sys
import time
import signal
import subprocess
import webbrowser
from pathlib import Path

BASE_DIR  = Path(__file__).resolve().parent
VENV_DIR  = BASE_DIR / "venv"
DJANGO_DIR = BASE_DIR / "DjangoExample"
PKG_DIR   = BASE_DIR / "packages"

# Detect venv python
if sys.platform == "win32":
    PYTHON = str(VENV_DIR / "Scripts" / "python.exe") if (VENV_DIR / "Scripts" / "python.exe").exists() else sys.executable
else:
    PYTHON = str(VENV_DIR / "bin" / "python") if (VENV_DIR / "bin" / "python").exists() else sys.executable

# Railway sets PORT for the public-facing HTTP port; DeviceBroker stays on 8001
IS_RAILWAY   = bool(os.environ.get("RAILWAY_ENVIRONMENT"))
BROKER_PORT  = 8001
WEBAPP_PORT  = int(os.environ.get("PORT", 8000))
WEBAPP_URL   = f"http://127.0.0.1:{WEBAPP_PORT}"
SYNC_SCRIPT  = BASE_DIR / "sync_engine.py"

# Settings module: use production on Railway, development locally
DJANGO_SETTINGS = os.environ.get(
    "DJANGO_SETTINGS_MODULE",
    "demosite.settings.production" if IS_RAILWAY else "demosite.settings.development",
)

# ── terminal colours ──────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def banner(text, colour=CYAN):
    width = 60
    print(f"\n{colour}{BOLD}{'─' * width}{RESET}")
    print(f"{colour}{BOLD}  {text}{RESET}")
    print(f"{colour}{BOLD}{'─' * width}{RESET}\n")

def log(tag, msg, colour=GREEN):
    print(f"{colour}{BOLD}[{tag}]{RESET} {msg}")

processes = []

def wait_for_port(port, host="127.0.0.1", timeout=30):
    """Block until a TCP port is accepting connections."""
    import socket
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(1)
    return False

def shutdown(sig=None, frame=None):
    print(f"\n{YELLOW}{BOLD}Shutting down all services…{RESET}")
    for name, proc in reversed(processes):
        if proc.poll() is None:
            log("STOP", f"Terminating {name}…", YELLOW)
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    log("DONE", "All services stopped.", GREEN)
    sys.exit(0)

signal.signal(signal.SIGINT,  shutdown)
signal.signal(signal.SIGTERM, shutdown)

# ── apply Django migrations (idempotent) ──────────────────────────────────────
def run_migrations():
    log("MIGRATE", "Applying database migrations…", CYAN)
    env = os.environ.copy()
    env["DJANGO_SETTINGS_MODULE"] = DJANGO_SETTINGS
    env["PYTHONPATH"] = str(PKG_DIR)
    result = subprocess.run(
        [PYTHON, "manage.py", "migrate", "--run-syncdb"],
        cwd=DJANGO_DIR,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        log("MIGRATE", "Migrations applied.", GREEN)
    else:
        log("MIGRATE", f"Migration warning:\n{result.stderr}", YELLOW)

# ── start DeviceBroker ────────────────────────────────────────────────────────
def start_broker():
    log("BROKER", f"Starting DeviceBroker (device port {BROKER_PORT})…", CYAN)
    env = os.environ.copy()
    proc = subprocess.Popen(
        [PYTHON, "-m", "devicebroker",
         "--host", "0.0.0.0",
         "--port", str(BROKER_PORT),
         "--sock-name", "127.0.0.1:8002",       # match Django DEVICEBROKER_ADDRESS
         "--webapp-url", WEBAPP_URL],
        cwd=PKG_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    processes.append(("DeviceBroker", proc))
    time.sleep(1.5)
    if proc.poll() is not None:
        out, _ = proc.communicate()
        log("BROKER", f"Failed to start!\n{out}", RED)
        sys.exit(1)
    log("BROKER", "DeviceBroker running.", GREEN)
    return proc

# ── start Django web app ──────────────────────────────────────────────────────
def start_webapp():
    log("WEBAPP", f"Starting Django web app on port {WEBAPP_PORT}…", CYAN)
    env = os.environ.copy()
    env["DJANGO_SETTINGS_MODULE"] = DJANGO_SETTINGS
    env["PYTHONPATH"] = str(PKG_DIR)
    if IS_RAILWAY:
        cmd = [PYTHON, "-m", "gunicorn", "demosite.wsgi:application",
               "--bind", f"0.0.0.0:{WEBAPP_PORT}", "--workers", "2", "--timeout", "120"]
    else:
        cmd = [PYTHON, "manage.py", "runserver", f"0.0.0.0:{WEBAPP_PORT}"]
    proc = subprocess.Popen(
        cmd,
        cwd=DJANGO_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    processes.append(("Django WebApp", proc))
    time.sleep(2)
    if proc.poll() is not None:
        out, _ = proc.communicate()
        log("WEBAPP", f"Failed to start!\n{out}", RED)
        shutdown()
    log("WEBAPP", f"Web app running → {WEBAPP_URL}", GREEN)
    return proc

# ── start Sync Engine ─────────────────────────────────────────────────────────
def start_sync():
    log("SYNC", "Starting Sync Engine…", CYAN)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PKG_DIR)
    proc = subprocess.Popen(
        [PYTHON, str(SYNC_SCRIPT)],
        cwd=BASE_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    processes.append(("SyncEngine", proc))
    time.sleep(1)
    if proc.poll() is not None:
        out, _ = proc.communicate()
        log("SYNC", f"Failed to start!\n{out}", RED)
        shutdown()
    log("SYNC", "Sync Engine running (polls every 15 s).", GREEN)
    return proc

# ── log streamer (prints each process's output with a prefix) ─────────────────
def stream_logs():
    import threading

    def _tail(name, proc, colour):
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                print(f"{colour}[{name}]{RESET} {line}")

    MAGENTA = "\033[95m"
    for name, proc in processes:
        if "Broker" in name:
            colour = CYAN
        elif "Sync" in name:
            colour = MAGENTA
        else:
            colour = YELLOW
        t = threading.Thread(target=_tail, args=(name, proc, colour), daemon=True)
        t.start()

# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    banner("WebSocketSDK — One-Button Launcher")
    log("INFO", f"Python: {PYTHON}", CYAN)
    log("INFO", f"Base dir: {BASE_DIR}", CYAN)

    run_migrations()
    start_broker()
    start_webapp()

    banner("All services started!", GREEN)
    print(f"  {BOLD}Web App    →{RESET}  {WEBAPP_URL}")
    print(f"  {BOLD}Devices    →{RESET}  ws://0.0.0.0:{BROKER_PORT}")
    print(f"  {BOLD}Sync Engine→{RESET}  running (polls every 15 s)")
    print(f"\n  Press {BOLD}Ctrl+C{RESET} to stop all services.\n")

    # Open browser after a short delay (local only)
    if not IS_RAILWAY:
        try:
            time.sleep(1)
            webbrowser.open(WEBAPP_URL)
        except Exception:
            pass

    # Wait for DeviceBroker management socket before starting sync
    log("SYNC", "Waiting for DeviceBroker management port (8002)…", CYAN)
    if wait_for_port(8002):
        log("SYNC", "DeviceBroker ready.", GREEN)
    else:
        log("SYNC", "DeviceBroker did not respond in 30 s — starting sync anyway.", YELLOW)

    start_sync()

    stream_logs()

    # Keep alive — wait for any process to die
    while True:
        time.sleep(2)
        for name, proc in processes:
            if proc.poll() is not None:
                log("WARN", f"{name} exited unexpectedly (code {proc.returncode}).", RED)
                shutdown()
