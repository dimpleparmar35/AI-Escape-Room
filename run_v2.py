"""
Launcher for Version 2 (Reliable State-Validated Escape Room).
Preselects Version 2 in the Streamlit application.
"""

import os
import sys
import subprocess

if __name__ == "__main__":
    os.environ["DEFAULT_ESCAPE_VERSION"] = "v2"
    print("Launching AI Escape Room - Version 2 (Reliable State-Engine)...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py", "--", "--version", "v2"])
