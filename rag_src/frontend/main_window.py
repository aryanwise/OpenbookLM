import sys
import os
import random
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QFrame, QScrollArea, QInputDialog, QMessageBox,
    QPushButton, QFileDialog, QMenu, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QCursor, QAction

# Import the new FlowLayout
from frontend.flow_layout import FlowLayout 

try:
    from frontend.styles import *
except ImportError:
    from styles import *

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'RAG')))
try:
    from data_loader import DocumentLoader
except ImportError:
    pass

class NotebookCard(QFrame):
    clicked = pyqtSignal(str) 
    action_triggered = pyqtSignal(str, str)

    def __init__(self, title, subtitle, is_new=False, emoji="📁"):
        super().__init__()
        self.title = title
        # Fixed size ensures they flow correctly
        self.setFixedSize(260, 170) 
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        if is_new:
            self.setObjectName("NewNotebookCard")
            self.setStyleSheet(NEW_NOTEBOOK_CARD_STYLE)
        else:
            self.setObjectName("NotebookCard")
            self.setStyleSheet(NOTEBOOK_CARD_STYLE)
            
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        icon_lbl = QLabel("➕" if is_new else emoji)
        icon_lbl.setStyleSheet("font-size: 28px; background: transparent; border: none;")
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(CARD_TITLE_STYLE)
        title_lbl.setWordWrap(True)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.backend = DocumentLoader()
        
        self.setWindowTitle("OpenbookLM")
        self.resize(1200, 850)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(GLOBAL_STYLE + DASHBOARD_STYLE)
        
        self.init_ui()
        QTimer.singleShot(100, self.check_initial_setup)

    def init_ui(self):
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        
        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        # Fix scroll behavior
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer_layout.addWidget(scroll)
        
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        
        self.main_layout = QVBoxLayout(content_widget)
        self.main_layout.setContentsMargins(60, 40, 60, 40)
        self.main_layout.setSpacing(30)
        
        # Header
        header = QHBoxLayout()
        logo = QLabel("OpenbookLM")
        logo.setStyleSheet("font-size: 26px; font-weight: bold; color: #e8eaed;")
        
        self.create_btn = QPushButton("➕ Create new")
        self.create_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.create_btn.setFixedSize(140, 40)
        self.create_btn.setStyleSheet("""
            background-color: #e8eaed; color: #202124; border-radius: 20px; font-weight: 600;
        """)
        self.create_btn.clicked.connect(self.prompt_create_notebook)
        
        header.addWidget(logo)
        header.addStretch()
        header.addWidget(self.create_btn)
        self.main_layout.addLayout(header)

        # Recent Section
        self.add_section_title("Recent Openbooks")
        
        # --- RESPONSIVE LAYOUT ---
        # Instead of a Grid, we use a plain widget with our FlowLayout
        self.recent_container = QWidget()
        self.recent_layout = FlowLayout(self.recent_container, margin=0, spacing=20)
        self.main_layout.addWidget(self.recent_container)
        
        self.main_layout.addStretch()

    def add_section_title(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(SECTION_TITLE_STYLE)
        self.main_layout.addWidget(lbl)

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
        # Clear existing items correctly for FlowLayout
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
                
                # Simply add to layout; FlowLayout handles position
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