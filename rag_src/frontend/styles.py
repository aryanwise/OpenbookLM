# frontend/styles.py

# Global Colors
BG_DARK = "rgba(19, 19, 20, 245)"       # Deep dark, slightly transparent
BG_PANEL = "rgba(30, 31, 32, 200)"      # Lighter panels
ACCENT_BLUE = "#a8c7fa"
TEXT_PRIMARY = "#e8eaed"
TEXT_SECONDARY = "#bdc1c6"
BORDER_COLOR = "rgba(95, 99, 104, 150)"

# Global Stylesheet
GLOBAL_STYLE = f"""
    QMainWindow {{ background: transparent; }}
    QWidget {{ font-family: 'Segoe UI', sans-serif; }}
    QMenu {{
        background-color: #303134;
        border: 1px solid {BORDER_COLOR};
        padding: 5px;
        color: {TEXT_PRIMARY};
    }}
    QMenu::item {{
        padding: 8px 20px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: #3c4043;
    }}
"""

DASHBOARD_STYLE = f"""
    QMainWindow {{ background-color: transparent; }}
    QWidget#CentralWidget {{ background-color: {BG_DARK}; border-radius: 0px; }}
    QScrollArea {{ background: transparent; border: none; }}
    QScrollBar:vertical {{
        border: none; background: #202124; width: 10px; margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: #5f6368; min-height: 20px; border-radius: 5px;
    }}
"""

NOTEBOOK_CARD_STYLE = f"""
    QFrame#NotebookCard {{
        background-color: {BG_PANEL};
        border: 1px solid {BORDER_COLOR};
        border-radius: 12px;
    }}
    QFrame#NotebookCard:hover {{
        background-color: rgba(60, 64, 67, 200);
        border-color: {ACCENT_BLUE};
    }}
"""

NEW_NOTEBOOK_CARD_STYLE = f"""
    QFrame#NewNotebookCard {{
        background-color: transparent;
        border: 2px dashed {BORDER_COLOR};
        border-radius: 12px;
    }}
    QFrame#NewNotebookCard:hover {{
        border-color: {ACCENT_BLUE};
        background-color: rgba(168, 199, 250, 0.1);
    }}
"""

SECTION_TITLE_STYLE = f"font-size: 20px; color: {TEXT_PRIMARY}; font-weight: 600; margin-top: 15px;"
CARD_TITLE_STYLE = f"font-weight: 600; font-size: 15px; color: {TEXT_PRIMARY}; border: none; background: transparent;"
CARD_SUBTITLE_STYLE = f"color: {TEXT_SECONDARY}; font-size: 12px; border: none; background: transparent;"

PROGRESS_BAR_STYLE = f"""
    QProgressBar {{
        border: none;
        background-color: #3c4043;
        height: 6px;
        border-radius: 3px;
    }}
    QProgressBar::chunk {{
        background-color: {ACCENT_BLUE};
        border-radius: 3px;
    }}
"""