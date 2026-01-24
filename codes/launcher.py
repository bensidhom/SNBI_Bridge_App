import multiprocessing
from streamlit_desktop_app import start_desktop_app
import os
import shutil
import sys

# Force writable config/cache dirs (critical for frozen Windows EXEs)
os.environ["XDG_CONFIG_HOME"] = os.path.join(os.path.expanduser("~"), ".streamlit")  # Helps Streamlit find config
os.makedirs(os.environ["XDG_CONFIG_HOME"], exist_ok=True)
cache_dir = os.path.join(os.environ["XDG_CONFIG_HOME"], "cache")
os.makedirs(cache_dir, exist_ok=True)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# DB copy logic
USER_DB = os.path.join(os.path.expanduser("~"), "snbi_bridges.db")
if not os.path.exists(USER_DB):
    bundled_db = resource_path("bridges.db")
    if os.path.exists(bundled_db):  # Extra safety
        shutil.copy(bundled_db, USER_DB)
        print("Copied initial database to user folder.")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    # Use absolute path for the Streamlit script
    app_script_path = resource_path("app.py")
    
    start_desktop_app(
        app_script_path,  # Absolute path – safer in frozen mode
        title="BridgeGuard",
        width=1200,
        height=800,
        options={
            "server.headless": True
        }
    )