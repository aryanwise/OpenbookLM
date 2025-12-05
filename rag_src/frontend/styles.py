# frontend/styles.py

# --- MODERN THEME PALETTE ---
BG_GRADIENT = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0F1115, stop:1 #181A20)"
BG_SOLID = "#0F1115"
SURFACE_GLASS = "rgba(30, 34, 40, 180)"
SURFACE_HOVER = "rgba(45, 50, 60, 200)"
BORDER_SUBTLE = "rgba(255, 255, 255, 0.08)"
ACCENT_PRIMARY = "#3B82F6"  # Electric Blue
ACCENT_GLOW = "rgba(59, 130, 246, 0.4)"
TEXT_MAIN = "#FFFFFF"
TEXT_SUB = "#94A3B8"

GLOBAL_STYLE = f"""
    QMainWindow {{ background: transparent; }}
    QWidget {{ font-family: 'Segoe UI', sans-serif; font-size: 14px; color: {TEXT_MAIN}; }}
    
    /* Scrollbar Styling - The "Warp" thin look */
    QScrollBar:vertical {{
        border: none; background: transparent; width: 8px; margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: #334155; min-height: 20px; border-radius: 4px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}

    /* Context Menu */
    QMenu {{
        background-color: #1E293B;
        border: 1px solid {BORDER_SUBTLE};
        border-radius: 8px;
        padding: 5px;
    }}
    QMenu::item {{
        padding: 6px 20px;
        border-radius: 4px;
        color: {TEXT_SUB};
    }}
    QMenu::item:selected {{
        background-color: {ACCENT_PRIMARY};
        color: white;
    }}
"""

# The "Floating" Card Look
NOTEBOOK_CARD_STYLE = f"""
    QFrame#NotebookCard {{
        background-color: {SURFACE_GLASS};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: 16px;
    }}
    QFrame#NotebookCard:hover {{
        background-color: {SURFACE_HOVER};
        border: 1px solid {ACCENT_PRIMARY};
    }}
"""

NEW_NOTEBOOK_CARD_STYLE = f"""
    QFrame#NewNotebookCard {{
        background-color: rgba(59, 130, 246, 0.05);
        border: 1px dashed {ACCENT_PRIMARY};
        border-radius: 16px;
    }}
    QFrame#NewNotebookCard:hover {{
        background-color: rgba(59, 130, 246, 0.15);
    }}
"""

# Input Fields (Floating Pills)
INPUT_STYLE = f"""
    QLineEdit {{
        background-color: #1E293B;
        border: 1px solid {BORDER_SUBTLE};
        border-radius: 8px;
        padding: 10px 15px;
        color: white;
        font-size: 14px;
    }}
    QLineEdit:focus {{
        border: 1px solid {ACCENT_PRIMARY};
        background-color: #252e40;
    }}
"""

# Buttons (Gradient & Glow)
BTN_PRIMARY_STYLE = f"""
    QPushButton {{
        background-color: {ACCENT_PRIMARY};
        color: white;
        border-radius: 8px;
        font-weight: 600;
        padding: 8px 16px;
    }}
    QPushButton:hover {{
        background-color: #2563EB;
    }}
"""

SECTION_TITLE_STYLE = f"font-size: 18px; color: {TEXT_MAIN}; font-weight: 700; letter-spacing: 0.5px; margin-top: 20px;"
CARD_TITLE_STYLE = f"font-weight: 600; font-size: 15px; color: {TEXT_MAIN}; border: none; background: transparent;"
CARD_SUBTITLE_STYLE = f"color: {TEXT_SUB}; font-size: 12px; border: none; background: transparent;"