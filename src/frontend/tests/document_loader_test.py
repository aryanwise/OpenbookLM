import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QFileDialog, QGroupBox, QFrame, 
    QGridLayout, QDialog, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QCursor

# Adjust import path as needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'RAG')))
from data_loader import DocumentLoader, ExtractLink, ExtractText

# --- Reusing Custom Widgets (DropZone, ActionCard, Dialogs) from previous response ---
# (Copy DropZone, ActionCard, URLDialog, TextPasteDialog classes here)
# For the sake of space, I am pasting the abbreviated DropZone to ensure the code runs.

class DropZone(QLabel):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setAcceptDrops(True)
        self.setText("⬆\n\nUpload sources\nDrag & drop or choose file to upload")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setObjectName("DropZone")
    
    def dragEnterEvent(self, e): e.accept() if e.mimeData().hasUrls() else e.ignore()
    def dragMoveEvent(self, e): e.accept() if e.mimeData().hasUrls() else e.ignore()
    def dropEvent(self, e):
        if e.mimeData().hasUrls():
            files = [str(u.toLocalFile()) for u in e.mimeData().urls() if u.isLocalFile()]
            if self.main_window: self.main_window.process_files(files)
    def mousePressEvent(self, e): 
        if self.main_window: self.main_window.open_file_dialog()

class ActionCard(QFrame):
    def __init__(self, title, subtitle, icon_text, callback):
        super().__init__()
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.mousePressEvent = lambda e: callback()
        self.setObjectName("ActionCard")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(icon_text))
        layout.addWidget(QLabel(title))
        layout.addWidget(QLabel(subtitle))

# --- Main Window ---

class ModernLoaderWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.backend = DocumentLoader()
        self.link_extractor = ExtractLink()
        
        self.setWindowTitle("OpenbookLM Data Loader")
        self.resize(1000, 750)
        # Dark Theme
        self.setStyleSheet("""
            QMainWindow { background-color: #202124; }
            QLabel { color: #e8eaed; }
            QLineEdit { background-color: #303134; color: white; border: 1px solid #5f6368; border-radius: 4px; padding: 8px; }
            QPushButton { background-color: #8ab4f8; color: #202124; border-radius: 4px; padding: 6px 12px; font-weight: bold; }
            QPushButton#SecondaryBtn { background-color: transparent; color: #8ab4f8; border: 1px solid #5f6368; }
            #DropZone { border: 1px dashed #5f6368; background-color: #202124; color: #bdc1c6; border-radius: 12px; font-size: 16px; }
            #ActionCard { background-color: #303134; border: 1px solid #5f6368; border-radius: 8px; }
            #ActionCard:hover { background-color: #3c4043; border-color: #a8c7fa; }
        """)

        self.init_ui()
        self.check_initial_config()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 20, 40, 40)
        main_layout.setSpacing(20)

        # 1. Top Bar: Root Config
        top_bar = QHBoxLayout()
        self.root_label = QLabel("Root: Not Set")
        self.root_label.setStyleSheet("color: #bdc1c6; font-size: 12px; font-style: italic;")
        
        self.change_root_btn = QPushButton("⚙ Change Root")
        self.change_root_btn.setObjectName("SecondaryBtn")
        self.change_root_btn.setFixedSize(120, 30)
        self.change_root_btn.clicked.connect(self.select_root_folder)
        
        top_bar.addWidget(self.root_label)
        top_bar.addStretch()
        top_bar.addWidget(self.change_root_btn)
        main_layout.addLayout(top_bar)

        # 2. Project Selection Header
        header_layout = QHBoxLayout()
        title = QLabel("Project:")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.project_input = QLineEdit()
        self.project_input.setPlaceholderText("Enter Project Name (e.g. Physics_101)")
        self.project_input.setFixedWidth(300)
        # Pressing Enter triggers project creation
        self.project_input.returnPressed.connect(self.setup_project)
        
        self.create_btn = QPushButton("Create/Open")
        self.create_btn.clicked.connect(self.setup_project)
        
        header_layout.addWidget(title)
        header_layout.addWidget(self.project_input)
        header_layout.addWidget(self.create_btn)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)

        # 3. Drop Zone
        self.drop_zone = DropZone(main_window=self)
        self.drop_zone.setFixedHeight(220)
        main_layout.addWidget(self.drop_zone)

        # 4. Action Cards
        grid_layout = QHBoxLayout()
        self.link_card = ActionCard("Link", "Website", "🔗", self.dummy_link) # Replace with real dialog
        self.paste_card = ActionCard("Paste text", "Copied text", "📋", self.dummy_paste) # Replace with real dialog
        grid_layout.addWidget(self.link_card)
        grid_layout.addWidget(self.paste_card)
        main_layout.addLayout(grid_layout)
        
        # 5. Source Limit / Status
        self.status_label = QLabel("0 Sources")
        main_layout.addWidget(self.status_label)

        # Disable main UI initially
        self.toggle_main_ui(False)

    def check_initial_config(self):
        """Checks if backend has a saved path on startup."""
        if self.backend.base_storage_path:
            self.root_label.setText(f"Root: {self.backend.base_storage_path}")
            self.project_input.setEnabled(True)
            self.create_btn.setEnabled(True)
        else:
            self.root_label.setText("Root: Not Set (Please Select)")
            # Force user to select
            QMessageBox.information(self, "Welcome", "Please select a Main Directory where all projects will be stored.")
            self.select_root_folder()

    def select_root_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Main Storage Folder")
        if folder:
            success = self.backend.set_storage_location(folder)
            if success:
                self.root_label.setText(f"Root: {self.backend.base_storage_path}")
                self.project_input.setEnabled(True)
                self.create_btn.setEnabled(True)
                QMessageBox.information(self, "Success", "Main directory set! Now create a project.")

    def setup_project(self):
        if not self.backend.base_storage_path:
            self.select_root_folder()
            return

        proj_name = self.project_input.text()
        if not proj_name: return

        try:
            path = self.backend.create_load_project(proj_name)
            self.toggle_main_ui(True)
            self.update_file_count()
            self.status_label.setText(f"Active Project: {proj_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def toggle_main_ui(self, enable):
        self.drop_zone.setVisible(enable)
        self.link_card.setVisible(enable)
        self.paste_card.setVisible(enable)

    def process_files(self, files):
        self.backend.add_files_to_project(files)
        self.update_file_count()

    def update_file_count(self):
        count = len(self.backend.get_project_files())
        self.status_label.setText(f"Sources: {count}")
    
    def dummy_link(self): print("Link dialog here")
    def dummy_paste(self): print("Paste dialog here")
    def open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(self)
        if files: self.process_files(files)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModernLoaderWindow()
    window.show()
    sys.exit(app.exec())