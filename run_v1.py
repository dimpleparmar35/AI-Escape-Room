"""
Launcher for Version 1 (Baseline Pure-LLM Escape Room).
Preselects Version 1 in the Streamlit application.
"""

import os
import sys
import subprocess

if __name__ == "__main__":
    os.environ["DEFAULT_ESCAPE_VERSION"] = "v1"
    print("Launching AI Escape Room - Version 1 (Baseline Pure-LLM)...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py", "--", "--version", "v1"])
