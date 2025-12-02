import sys
import os
import random
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QGridLayout, QFrame, QScrollArea, QInputDialog, QMessageBox,
    QPushButton, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer  # <--- Added QTimer
from PyQt6.QtGui import QIcon, QCursor, QFont

# Import Styles
try:
    from frontend.styles import (
        DASHBOARD_STYLE, SECTION_TITLE_STYLE, NOTEBOOK_CARD_STYLE, 
        NEW_NOTEBOOK_CARD_STYLE, CARD_TITLE_STYLE, CARD_SUBTITLE_STYLE
    )
except ImportError:
    from styles import (
        DASHBOARD_STYLE, SECTION_TITLE_STYLE, NOTEBOOK_CARD_STYLE, 
        NEW_NOTEBOOK_CARD_STYLE, CARD_TITLE_STYLE, CARD_SUBTITLE_STYLE
    )

# Backend Import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'RAG')))
try:
    from data_loader import DocumentLoader
except ImportError:
    from data_loader import DocumentLoader

class NotebookCard(QFrame):
    """Represents a single project folder."""
    clicked = pyqtSignal(str) 

    def __init__(self, title, subtitle, is_new=False, emoji="📁"):
        super().__init__()
        self.title = title
        self.setFixedSize(280, 180)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Assign Object Name FIRST before styling
        if is_new:
            self.setObjectName("NewNotebookCard")
            self.setStyleSheet(NEW_NOTEBOOK_CARD_STYLE)
        else:
            self.setObjectName("NotebookCard")
            self.setStyleSheet(NOTEBOOK_CARD_STYLE)
            
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Icon
        icon_lbl = QLabel("➕" if is_new else emoji)
        icon_lbl.setStyleSheet("font-size: 32px; background: transparent; border: none;")
        
        # Title
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(CARD_TITLE_STYLE)
        title_lbl.setWordWrap(True)
        
        # Subtitle
        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet(CARD_SUBTITLE_STYLE)
        
        if is_new:
            layout.addStretch()
            layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
            layout.addStretch()
        else:
            layout.addWidget(icon_lbl)
            layout.addSpacing(10)
            layout.addWidget(title_lbl)
            layout.addWidget(sub_lbl)
            layout.addStretch()

    def mousePressEvent(self, event):
        self.clicked.emit(self.title)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.backend = DocumentLoader() 
        
        self.setWindowTitle("OpenbookLM")
        self.resize(1200, 850)
        self.setStyleSheet(DASHBOARD_STYLE)
        
        self.init_ui()
        
        # --- UX FIX: Delay the check until the window is visible ---
        # 100ms delay ensures the UI is painted before the popup appears
        QTimer.singleShot(100, self.check_initial_setup)

    def init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.setCentralWidget(scroll)
        
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        
        self.main_layout = QVBoxLayout(content_widget)
        self.main_layout.setContentsMargins(60, 40, 60, 40)
        self.main_layout.setSpacing(30)
        
        # Header
        header_layout = QHBoxLayout()
        logo = QLabel("OpenbookLM")
        logo.setStyleSheet("font-size: 26px; font-weight: bold; color: white;")
        
        self.create_btn = QPushButton("➕ Create new")
        self.create_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.create_btn.setFixedSize(140, 40)
        self.create_btn.clicked.connect(self.prompt_create_notebook)
        
        settings_btn = QPushButton("⚙ Settings")
        settings_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        settings_btn.setObjectName("SecondaryBtn")
        settings_btn.setStyleSheet("background: transparent; color: #bdc1c6; border: none; font-size: 14px;")
        settings_btn.clicked.connect(lambda: self.change_root_directory(initial=False))
        
        header_layout.addWidget(logo)
        header_layout.addStretch()
        header_layout.addWidget(self.create_btn)
        header_layout.addSpacing(15)
        header_layout.addWidget(settings_btn)
        
        self.main_layout.addLayout(header_layout)

        # Featured Section
        self.add_section_title("Featured notebooks")
        featured_layout = QHBoxLayout()
        featured_layout.setSpacing(20)
        
        f1 = NotebookCard("Trends in Health", "Apr 15 • 24 sources", emoji="🌍")
        f2 = NotebookCard("Globalisation", "Nov 4 • 26 sources", emoji="📊") 
        f3 = NotebookCard("Genetics & Health", "Jul 9 • 16 sources", emoji="🧬")
        
        featured_layout.addWidget(f1)
        featured_layout.addWidget(f2)
        featured_layout.addWidget(f3)
        featured_layout.addStretch()
        
        self.main_layout.addLayout(featured_layout)

        # Recent Section
        self.add_section_title("Recent Openbooks")
        self.recent_grid = QGridLayout()
        self.recent_grid.setSpacing(20)
        self.main_layout.addLayout(self.recent_grid)
        self.main_layout.addStretch()

    def add_section_title(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(SECTION_TITLE_STYLE)
        self.main_layout.addWidget(lbl)

    # --- Logic ---

    def check_initial_setup(self):
        """Runs shortly after startup. Checks if we have a valid root folder."""
        # 1. Check if backend has a path
        if self.backend.base_storage_path and os.path.exists(self.backend.base_storage_path):
            self.load_notebooks()
        else:
            # 2. Show Explanation Pop-up FIRST
            QMessageBox.information(
                self, 
                "Welcome to OpenbookLM", 
                "To get started, please select a folder where all your notebooks will be stored."
            )
            # 3. THEN open the file dialog
            self.change_root_directory(initial=True)

    def change_root_directory(self, initial=False):
        """Opens dialog to select root folder."""
        msg = "Select Storage Folder"
        folder = QFileDialog.getExistingDirectory(self, msg)
        
        if folder:
            success = self.backend.set_storage_location(folder)
            if success:
                self.load_notebooks()
            else:
                QMessageBox.warning(self, "Error", "Could not set storage location.")
        elif initial:
            # If they cancel the initial setup, we can't really proceed.
            # You might want to close the app or just leave it empty.
            QMessageBox.warning(self, "Setup Incomplete", "A storage folder is required to save your notebooks.")

    def load_notebooks(self):
        """Scans the root directory and populates the grid."""
        # Clear existing items
        for i in reversed(range(self.recent_grid.count())): 
            widget = self.recent_grid.itemAt(i).widget()
            if widget: widget.setParent(None)

        if not self.backend.base_storage_path: return

        try:
            root = self.backend.base_storage_path
            projects = [d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]
            
            row, col = 0, 0
            max_cols = 4 
            emojis = ["📘", "📙", "📒", "📕", "📓", "🧠", "💡"]

            for proj in projects:
                proj_path = os.path.join(root, proj)
                file_count = len([f for f in os.listdir(proj_path) if os.path.isfile(os.path.join(proj_path, f))])
                
                card = NotebookCard(proj, f"{file_count} sources", emoji=random.choice(emojis))
                card.clicked.connect(self.open_notebook)
                
                self.recent_grid.addWidget(card, row, col)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
                    
        except Exception as e:
            print(f"Error loading notebooks: {e}")

    def prompt_create_notebook(self):
        if not self.backend.base_storage_path:
             QMessageBox.warning(self, "Error", "Please configure a storage folder first.")
             return

        name, ok = QInputDialog.getText(self, 'Create New', 'Notebook Title:')
        if ok and name:
            try:
                self.backend.create_load_project(name)
                self.load_notebooks() 
                self.open_notebook(name) 
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def open_notebook(self, name):
        self.backend.create_load_project(name) 
        QMessageBox.information(self, "Open Project", f"Opening: {name}\nPath: {self.backend.current_project_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())