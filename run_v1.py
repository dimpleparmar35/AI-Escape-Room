"""
Standalone CLI and Streamlit Launcher for Version 1 (Baseline Pure-LLM).
"""

import sys
import os

if __name__ == "__main__":
    # If run via python directly, launch streamlit app pointing to v1 mode
    os.system("streamlit run app.py")
