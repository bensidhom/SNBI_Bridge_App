import multiprocessing
import webview
import subprocess
import sys
import os
import time
import socket
import shutil

# ----------------------------
# PyInstaller-safe resource path
# ----------------------------
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ----------------------------
# Copy DB to user home (once)
# ----------------------------
USER_DB = os.path.join(os.path.expanduser("~"), "snbi_bridges.db")

if not os.path.exists(USER_DB):
    shutil.copy(resource_path("bridges.db"), USER_DB)

# ----------------------------
# Streamlit config
# ----------------------------
PORT = 8501
URL = f"http://127.0.0.1:{PORT}"

process = None

# ----------------------------
# Start Streamlit subprocess
# ----------------------------
def start_streamlit():
    env = os.environ.copy()
    env["BRIDGEGUARD_CHILD"] = "1"  # mark child ONLY

    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            resource_path("app.py"),
            "--server.port", str(PORT),
            "--server.address", "127.0.0.1",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )

# ----------------------------
# Wait for Streamlit server
# ----------------------------
def server_ready(timeout=180):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False

# ----------------------------
# Cleanup on window close
# ----------------------------
def on_closed():
    global process
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

# ----------------------------
# Main
# ----------------------------
def main():
    global process

    # 🚫 If this is the Streamlit child process, DO NOTHING
    if os.environ.get("BRIDGEGUARD_CHILD") == "1":
        return

    # Start Streamlit backend
    process = start_streamlit()

    if not server_ready():
        process.terminate()
        sys.exit(1)

    # Create the UI (parent only)
    window = webview.create_window(
        "BridgeGuard",
        URL,
        width=1200,
        height=800,
    )

    window.events.closed += on_closed

    webview.start(
        gui="edgechromium",  # remove this if WebView2 causes issues
        icon=resource_path("logo.ico"),
    )

# ----------------------------
# Windows multiprocessing guard
# ----------------------------
if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
