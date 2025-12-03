# frontend/styles.py

DARK_THEME = """
    QMainWindow { background-color: transparent; }
    
    QWidget#CentralWidget { 
        background-color: rgba(32, 33, 36, 245); 
        border-radius: 16px; 
        border: 1px solid #5f6368;
    }

    QLabel { color: #e8eaed; font-family: 'Segoe UI', sans-serif; }
    
    QLineEdit, QTextEdit { 
        background-color: #202124; 
        color: white; 
        border: 1px solid #5f6368; 
        border-radius: 8px; 
        padding: 10px; 
        font-size: 14px;
    }
    
    QLineEdit:focus, QTextEdit:focus {
        border: 1px solid #8ab4f8;
    }

    QPushButton { 
        background-color: #8ab4f8; 
        color: #202124; 
        border-radius: 18px; 
        padding: 8px 20px; 
        font-weight: bold; 
        font-size: 14px;
    }
    
    QPushButton:hover { background-color: #a1c1fa; }

    /* Secondary transparent button */
    QPushButton#SecondaryBtn { 
        background-color: transparent; 
        color: #bdc1c6; 
        border: 1px solid #5f6368; 
    }
    QPushButton#SecondaryBtn:hover { 
        background-color: rgba(255, 255, 255, 0.1); 
        color: white; 
    }
"""

DROPZONE_STYLE = """
    QLabel#DropZone { 
        border: 2px dashed #5f6368; 
        background-color: rgba(32, 33, 36, 150); 
        color: #bdc1c6; 
        border-radius: 12px; 
        font-size: 16px; 
    }
    QLabel#DropZone:hover { 
        border-color: #8ab4f8; 
        background-color: rgba(48, 49, 52, 200); 
        color: #e8eaed;
    }
"""

CARD_STYLE = """
    QFrame#ActionCard { 
        background-color: #303134; 
        border: 1px solid #3c4043; 
        border-radius: 12px; 
    }
    QFrame#ActionCard:hover { 
        background-color: #3c4043; 
        border-color: #5f6368; 
        cursor: pointer;
    }
"""

PROGRESS_BAR_STYLE = """
    QProgressBar { 
        border: none; 
        background-color: #3c4043; 
        height: 8px; 
        border-radius: 4px; 
    }
    QProgressBar::chunk { 
        background-color: #a8c7fa; 
        border-radius: 4px; 
    }
"""

DASHBOARD_STYLE = """
    QMainWindow { background-color: #202124; }
    QScrollArea { background-color: transparent; border: none; }
    QWidget { background-color: transparent; }
"""

SECTION_TITLE_STYLE = """
    font-size: 22px; 
    color: #e8eaed; 
    font-weight: 500;
    margin-top: 20px;
    margin-bottom: 10px;
"""

# Cleaned up Card Styles (Removed cursor property to avoid parsing errors)
NOTEBOOK_CARD_STYLE = """
    QFrame#NotebookCard {
        background-color: #303134;
        border: 1px solid #5f6368;
        border-radius: 16px;
    }
    QFrame#NotebookCard:hover {
        background-color: #3c4043;
        border-color: #a8c7fa;
    }
"""

NEW_NOTEBOOK_CARD_STYLE = """
    QFrame#NewNotebookCard {
        background-color: #202124;
        border: 2px solid #5f6368;
        border-radius: 16px;
    }
    QFrame#NewNotebookCard:hover {
        background-color: #303134;
        border-color: #8ab4f8;
    }
"""

CARD_TITLE_STYLE = "font-weight: bold; font-size: 16px; color: #e8eaed; border: none; background: transparent;"
CARD_SUBTITLE_STYLE = "color: #bdc1c6; font-size: 12px; border: none; background: transparent;"

CARD_TITLE_STYLE = "font-weight: bold; font-size: 16px; color: #e8eaed; border: none; background: transparent;"
CARD_SUBTITLE_STYLE = "color: #bdc1c6; font-size: 12px; border: none; background: transparent;"