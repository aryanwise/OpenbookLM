import sys
import os
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QFileDialog, QFrame, 
    QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor

# --- 1. SETUP PATHS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, '..')))

# --- 2. IMPORTS ---
try:
    from data_loader import DocumentLoader
except ImportError:
    pass

# --- CUSTOM WIDGETS ---

class DropZone(QLabel):
    """
    A specific widget that handles Drag & Drop reliably.
    """
    files_dropped = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setText("⬆\n\nUpload sources\nDrag & drop or choose file to upload")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(220)
        self.setAcceptDrops(True) # CRITICAL: This widget accepts drops
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Default Style
        self.default_style = """
            QLabel { 
                border: 2px dashed #5f6368; 
                background-color: rgba(32, 33, 36, 150); 
                border-radius: 12px; 
                color: #e8eaed; font-size: 15px; font-weight: bold;
            }
            QLabel:hover { 
                border-color: #8ab4f8; 
                background-color: rgba(48, 49, 52, 200); 
            }
        """
        # Active Drag Style
        self.drag_style = """
            QLabel { 
                border: 2px dashed #8ab4f8; 
                background-color: rgba(59, 130, 246, 0.2); 
                border-radius: 12px; 
                color: #ffffff; font-size: 15px; font-weight: bold;
            }
        """
        self.setStyleSheet(self.default_style)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self.setStyleSheet(self.drag_style)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self.default_style)
        event.accept()

    def dropEvent(self, event):
        self.setStyleSheet(self.default_style)
        if event.mimeData().hasUrls():
            files = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    files.append(url.toLocalFile())
            
            if files:
                self.files_dropped.emit(files)
                event.acceptProposedAction()
        else:
            event.ignore()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Trigger file dialog via parent or signal
            # For simplicity, we can let the parent handle the click if needed,
            # but usually the drop zone itself handles the click signal.
            # We will rely on the parent connecting the click logic manually if not dragging.
            super().mousePressEvent(event)


class SourceChip(QPushButton):
    def __init__(self, icon, text, callback):
        super().__init__()
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.clicked.connect(callback)
        self.setFixedSize(140, 45)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("background: transparent; border: none; font-size: 18px;")
        
        lbl_text = QLabel(text)
        lbl_text.setStyleSheet("background: transparent; border: none; font-weight: 600; color: #e8eaed;")
        
        layout.addWidget(lbl_icon)
        layout.addWidget(lbl_text)
        layout.addStretch()
        
        self.setStyleSheet("""
            QPushButton {
                background-color: #303134; 
                border: 1px solid #5f6368; 
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #3c4043;
                border-color: #a8c7fa;
            }
        """)

class SourceGroup(QFrame):
    def __init__(self, title, icon, buttons):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #202124; 
                border: 1px solid #3c4043; 
                border-radius: 12px;
            }
        """)
        self.setFixedSize(280, 150)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        
        header = QHBoxLayout()
        header.addWidget(QLabel(icon))
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #e8eaed; font-weight: bold; font-size: 14px; border: none;")
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)
        
        btn_layout = QHBoxLayout()
        for btn in buttons:
            btn_layout.addWidget(btn)
        
        layout.addLayout(btn_layout)

# --- DIALOGS ---
class URLDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Link")
        self.setFixedSize(400, 150)
        self.setStyleSheet("background-color: #303134; color: white; border: 1px solid #5f6368;")
        layout = QVBoxLayout(self)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")
        self.url_input.setStyleSheet("background: #202124; border: 1px solid #5f6368; padding: 8px; color: white; border-radius: 4px;")
        btn = QPushButton("Add")
        btn.setStyleSheet("background-color: #8ab4f8; color: #202124; border-radius: 4px; padding: 6px; font-weight: bold;")
        btn.clicked.connect(self.accept)
        layout.addWidget(QLabel("Enter URL:"))
        layout.addWidget(self.url_input)
        layout.addWidget(btn)
    def get_url(self): return self.url_input.text().strip()

class TextPasteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paste Text")
        self.resize(500, 400)
        self.setStyleSheet("background-color: #303134; color: white; border: 1px solid #5f6368;")
        layout = QVBoxLayout(self)
        self.title = QLineEdit()
        self.title.setPlaceholderText("Title")
        self.title.setStyleSheet("background: #202124; border: 1px solid #5f6368; padding: 8px; color: white; border-radius: 4px;")
        self.area = QTextEdit()
        self.area.setStyleSheet("background: #202124; border: 1px solid #5f6368; color: white; border-radius: 4px;")
        btn = QPushButton("Save")
        btn.setStyleSheet("background-color: #8ab4f8; color: #202124; border-radius: 4px; padding: 6px; font-weight: bold;")
        btn.clicked.connect(self.accept)
        layout.addWidget(self.title)
        layout.addWidget(self.area)
        layout.addWidget(btn)
    def get_data(self): return self.title.text(), self.area.toPlainText()

# --- MAIN UPLOAD DIALOG ---
class SourceUploadDialog(QDialog):
    sources_added = pyqtSignal() 

    def __init__(self, backend_instance, parent=None):
        super().__init__(parent)
        self.backend = backend_instance 
        
        self.setWindowTitle("Add sources")
        self.resize(950, 650)
        self.setStyleSheet("""
            QDialog { background-color: #1e1f20; }
            QLabel { color: #bdc1c6; font-size: 13px; }
        """)
        # We don't rely on the Dialog accepting drops anymore, 
        # the DropZone widget handles it.
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)

        # Header
        header_lbl = QLabel("Add sources")
        header_lbl.setStyleSheet("font-size: 24px; color: #e8eaed; font-weight: 500;")
        main_layout.addWidget(header_lbl)
        
        main_layout.addWidget(QLabel("Sources let NotebookLM base its responses on information that matters most to you."))

        # Drop Zone (Using the custom class)
        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self.handle_dropped_files)
        
        # Make the whole box clickable for file dialog too
        # We override mousePress in the class, or we can just map the signal here if we added one.
        # Simple hack: Reuse mousePressEvent of the widget
        self.drop_zone.mousePressEvent = self.handle_click_dropzone
        
        main_layout.addWidget(self.drop_zone)

        # Groups
        grid_layout = QHBoxLayout()
        
        # Link Group
        web_btn = SourceChip("🌐", "Website", self.open_link)
        group_link = SourceGroup("Link", "🔗", [web_btn])
        
        # Text Group
        paste_btn = SourceChip("📋", "Paste text", self.open_paste)
        group_text = SourceGroup("Paste text", "T", [paste_btn])

        grid_layout.addWidget(group_link)
        grid_layout.addWidget(group_text)
        grid_layout.addStretch()
        
        main_layout.addLayout(grid_layout)
        main_layout.addStretch()

    # --- HANDLERS ---

    def handle_click_dropzone(self, event):
        # Trigger standard file dialog
        self.open_file_dialog()

    def handle_dropped_files(self, files):
        if files:
            self.backend.add_files_to_project(files)
            self.sources_added.emit()
            QMessageBox.information(self, "Success", f"Added {len(files)} files.")

    def open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files")
        if files:
            self.backend.add_files_to_project(files)
            self.sources_added.emit()

    def open_link(self):
        dlg = URLDialog(self)
        if dlg.exec():
            url = dlg.get_url()
            if url:
                success = self.backend.process_and_save_link(url)
                if success:
                    self.sources_added.emit()
                    QMessageBox.information(self, "Success", "Link content added.")
                else:
                    QMessageBox.warning(self, "Error", "Failed to extract content from link.")

    def open_paste(self):
        dlg = TextPasteDialog(self)
        if dlg.exec():
            title, content = dlg.get_data()
            if content:
                if not title: title = "Pasted_Text"
                success = self.backend.save_text_to_project(content, title)
                if success:
                    self.sources_added.emit()
                else:
                    QMessageBox.warning(self, "Error", "Failed to save text.")