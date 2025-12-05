import sys
import os
import random
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QFrame, QScrollArea, QInputDialog, QMessageBox,
    QPushButton, QFileDialog, QMenu, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QCursor, QAction, QColor

# --- 1. SETUP PATHS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..', 'RAG'))
sys.path.append(root_dir)
sys.path.append(os.path.abspath(os.path.join(current_dir, '..')))

# --- 2. IMPORTS ---
from frontend.flow_layout import FlowLayout 

try:
    from frontend.styles import *
except ImportError:
    pass

try:
    from data_loader import DocumentLoader
except ImportError:
    pass

# --- 3. NOTEBOOK CARD WIDGET ---
class NotebookCard(QFrame):
    clicked = pyqtSignal(str) 
    action_triggered = pyqtSignal(str, str)

    def __init__(self, title, subtitle, is_new=False, emoji="📁"):
        super().__init__()
        self.title = title
        self.setFixedSize(260, 170) 
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Drop Shadow for depth (The "Floating" look)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)
        
        # Apply Styles from styles.py
        if is_new:
            self.setObjectName("NewNotebookCard")
            self.setStyleSheet(NEW_NOTEBOOK_CARD_STYLE)
        else:
            self.setObjectName("NotebookCard")
            self.setStyleSheet(NOTEBOOK_CARD_STYLE)
            
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Icon
        icon_lbl = QLabel("➕" if is_new else emoji)
        icon_lbl.setStyleSheet("font-size: 32px; background: transparent; border: none;")
        
        # Title
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(CARD_TITLE_STYLE)
        title_lbl.setWordWrap(True)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
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
            layout.addSpacing(12)
            layout.addWidget(title_lbl)
            layout.addWidget(sub_lbl)
            layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.title)
        elif event.button() == Qt.MouseButton.RightButton and self.objectName() != "NewNotebookCard":
            self.show_context_menu(event.globalPosition().toPoint())

    def show_context_menu(self, pos):
        menu = QMenu()
        rename_action = QAction("Rename", self)
        delete_action = QAction("Delete", self)
        
        menu.addAction(rename_action)
        menu.addSeparator()
        menu.addAction(delete_action)
        
        action = menu.exec(pos)
        if action == rename_action:
            self.action_triggered.emit("rename", self.title)
        elif action == delete_action:
            self.action_triggered.emit("delete", self.title)

# --- 4. MAIN DASHBOARD ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.backend = DocumentLoader()
        
        self.setWindowTitle("OpenbookLM")
        self.resize(1280, 850)
        
        # Apply the Global Gradient Background
        self.setStyleSheet(GLOBAL_STYLE + f"QMainWindow {{ background: {BG_GRADIENT}; }}")
        
        self.init_ui()
        QTimer.singleShot(100, self.check_initial_setup)

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        
        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll Area (Transparent)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer_layout.addWidget(scroll)
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;") # Important for gradient
        scroll.setWidget(content_widget)
        
        self.main_layout = QVBoxLayout(content_widget)
        self.main_layout.setContentsMargins(80, 50, 80, 50)
        self.main_layout.setSpacing(40)
        
        # --- HEADER ---
        header = QHBoxLayout()
        
        logo = QLabel("OpenbookLM")
        logo.setStyleSheet(f"font-size: 28px; font-weight: 800; color: {TEXT_MAIN}; letter-spacing: -0.5px;")
        
        self.create_btn = QPushButton("+ New Notebook")
        self.create_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        # Use the "Electric Blue" button style
        self.create_btn.setStyleSheet(BTN_PRIMARY_STYLE)
        self.create_btn.clicked.connect(self.prompt_create_notebook)
        
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(40, 40)
        settings_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.05);
                color: {TEXT_SUB};
                border-radius: 20px;
                border: 1px solid {BORDER_SUBTLE};
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
                color: {TEXT_MAIN};
            }}
        """)
        settings_btn.clicked.connect(lambda: self.change_root_directory(initial=False))

        header.addWidget(logo)
        header.addStretch()
        header.addWidget(self.create_btn)
        header.addSpacing(15)
        header.addWidget(settings_btn)
        
        self.main_layout.addLayout(header)

        # --- SECTIONS ---
        self.add_section_title("Recent Projects")
        
        # Responsive Flow Layout
        self.recent_container = QWidget()
        self.recent_layout = FlowLayout(self.recent_container, margin=0, spacing=24)
        self.main_layout.addWidget(self.recent_container)
        
        self.main_layout.addStretch()

    def add_section_title(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(SECTION_TITLE_STYLE)
        self.main_layout.addWidget(lbl)

    # --- LOGIC ---

    def check_initial_setup(self):
        if self.backend.base_storage_path and os.path.exists(self.backend.base_storage_path):
            self.load_notebooks()
        else:
            self.change_root_directory(initial=True)

    def change_root_directory(self, initial=False):
        folder = QFileDialog.getExistingDirectory(self, "Select Storage Folder")
        if folder:
            self.backend.set_storage_location(folder)
            self.load_notebooks()

    def load_notebooks(self):
        # Clear layout
        while self.recent_layout.count():
            item = self.recent_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.backend.base_storage_path: return

        try:
            root = self.backend.base_storage_path
            projects = [d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]
            emojis = ["📘", "📙", "📒", "📕", "📓", "🧠", "💡"]

            for proj in projects:
                proj_path = os.path.join(root, proj)
                file_count = len([f for f in os.listdir(proj_path) if os.path.isfile(os.path.join(proj_path, f))])
                
                card = NotebookCard(proj, f"{file_count} sources", emoji=random.choice(emojis))
                card.clicked.connect(self.open_notebook)
                card.action_triggered.connect(self.handle_card_action)
                
                self.recent_layout.addWidget(card)
                    
        except Exception as e:
            print(f"Error: {e}")

    def handle_card_action(self, action, project_name):
        if action == "delete":
            reply = QMessageBox.question(self, 'Delete', f"Delete '{project_name}' permanently?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.backend.delete_project(project_name)
                self.load_notebooks()
        elif action == "rename":
            new_name, ok = QInputDialog.getText(self, "Rename", "New Name:", text=project_name)
            if ok and new_name:
                self.backend.rename_project(project_name, new_name)
                self.load_notebooks()

    def prompt_create_notebook(self):
        name, ok = QInputDialog.getText(self, 'Create New', 'Notebook Title:')
        if ok and name:
            self.backend.create_load_project(name)
            self.load_notebooks()

    def open_notebook(self, name):
        self.backend.create_load_project(name)
        from frontend.workspace_window import WorkspaceWindow
        self.workspace = WorkspaceWindow(name, self.backend)
        self.workspace.show()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())