"""
Visualizer and UI helper utilities for Streamlit application.
Renders gothic Victorian themes, state badges, inventory displays, and live progress bars.
"""

import streamlit as st
from typing import Dict, Any


def apply_custom_theme():
    """Applies a rich, immersive Victorian-themed CSS styling to Streamlit."""
    st.markdown(
        """
        <style>
        /* Main background and fonts */
        .main {
            background: linear-gradient(135deg, #12151b 0%, #1a1e26 100%);
            color: #e0d7c6;
            font-family: 'Georgia', serif;
        }
        
        /* Headers */
        h1, h2, h3 {
            color: #d4af37 !important;
            font-family: 'Palatino Linotype', 'Book Antiqua', Palatino, serif;
            text-shadow: 1px 1px 2px #000;
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #161920;
            border-right: 1px solid #3d3423;
        }
        
        /* Badges */
        .status-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 0.85rem;
            margin: 2px;
        }
        .badge-locked {
            background-color: #5c1d1d;
            color: #ff9999;
            border: 1px solid #852b2b;
        }
        .badge-unlocked {
            background-color: #1e4a2c;
            color: #8aff99;
            border: 1px solid #2d6e42;
        }
        .badge-item {
            background-color: #4a3c1e;
            color: #ffd97d;
            border: 1px solid #7a6332;
        }
        .badge-escaped {
            background-color: #0e5c6e;
            color: #7df5ff;
            border: 1px solid #148099;
            font-size: 1.1rem;
            padding: 8px 16px;
            animation: pulse 2s infinite;
        }
        
        /* Code blocks */
        code {
            color: #ffd97d !important;
        }
        
        /* Progress bar */
        .stProgress > div > div > div > div {
            background-color: #d4af37;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_state(state_dict: Dict[str, Any]):
    """Renders the live deterministic Game State HUD in the sidebar for Version 2."""
    st.sidebar.markdown("### 🏰 Live State HUD (Python Engine)")
    
    # Escape Status
    if state_dict.get("escaped", False):
        st.sidebar.markdown('<div class="status-badge badge-escaped">🏆 ESCAPED SAFELY!</div>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown('<div class="status-badge badge-locked">🔒 TRAPPED IN ROOM</div>', unsafe_allow_html=True)

    # Progress Bar
    puzzles = state_dict.get("puzzles_solved", {})
    solved_count = sum(1 for v in puzzles.values() if v)
    total_count = len(puzzles) if puzzles else 4
    progress_val = solved_count / total_count
    st.sidebar.progress(progress_val)
    st.sidebar.caption(f"Escape Progress: {solved_count}/{total_count} Puzzles Cleared ({int(progress_val*100)}%)")

    # Inventory HUD
    st.sidebar.markdown("#### 🎒 Inventory")
    inventory = state_dict.get("inventory", [])
    if inventory:
        for item in inventory:
            st.sidebar.markdown(f'<span class="status-badge badge-item">🗝️ {item.replace("_", " ").title()}</span>', unsafe_allow_html=True)
    else:
        st.sidebar.caption("*(Inventory is empty)*")

    # Objects HUD
    st.sidebar.markdown("#### 🔍 Object States")
    objects = state_dict.get("objects", {})
    
    # Bookshelf
    bs_status = "badge-unlocked" if puzzles.get("bookshelf_cipher") else "badge-locked"
    bs_text = "Decoded (7392)" if puzzles.get("bookshelf_cipher") else "Uninspected"
    st.sidebar.markdown(f"**Bookshelf:** <span class='status-badge {bs_status}'>{bs_text}</span>", unsafe_allow_html=True)

    # Drawer
    dr_status = "badge-unlocked" if objects.get("drawer", {}).get("unlocked") else "badge-locked"
    dr_text = "Unlocked" if objects.get("drawer", {}).get("unlocked") else "Locked"
    st.sidebar.markdown(f"**Desk Drawer:** <span class='status-badge {dr_status}'>{dr_text}</span>", unsafe_allow_html=True)

    # Painting
    pt_status = "badge-unlocked" if objects.get("painting", {}).get("unlocked") else "badge-locked"
    pt_text = "Secret Revealed" if objects.get("painting", {}).get("unlocked") else "Locked Frame"
    st.sidebar.markdown(f"**Founder's Portrait:** <span class='status-badge {pt_status}'>{pt_text}</span>", unsafe_allow_html=True)

    # Exit Door
    dr_status = "badge-unlocked" if state_dict.get("escaped") else "badge-locked"
    dr_text = "Open" if state_dict.get("escaped") else "Locked (Keypad)"
    st.sidebar.markdown(f"**Exit Door:** <span class='status-badge {dr_status}'>{dr_text}</span>", unsafe_allow_html=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Turns Taken:** `{state_dict.get('turn_count', 0)}`")
