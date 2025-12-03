import sys
import os
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QFileDialog, QFrame, 
    QMessageBox, QTextEdit, QProgressBar, QGridLayout, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QCursor, QColor

# Import Backend Classes
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'RAG')))
try:
    from data_loader import DocumentLoader, ExtractLink, ExtractText
except ImportError:
    pass

# --- 1. Helper: Small "Chip" Button (e.g. 'Website', 'YouTube') ---
class SourceChip(QPushButton):
    def __init__(self, icon, text, callback):
        super().__init__()
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.clicked.connect(callback)
        self.setFixedSize(140, 40)
        
        # Layout inside button
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("background: transparent; border: none; font-size: 16px;")
        
        lbl_text = QLabel(text)
        lbl_text.setStyleSheet("background: transparent; border: none; font-weight: bold; color: #e8eaed;")
        
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

# --- 2. Helper: Group Container (e.g. 'Link', 'Paste text') ---
class SourceGroup(QFrame):
    def __init__(self, title, icon, buttons):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #202124; 
                border: 1px solid #3c4043; 
                border-radius: 12px;
            }
            QLabel { border: none; background: transparent; }
        """)
        self.setFixedSize(260, 140)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Header
        header_layout = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("color: #bdc1c6; font-size: 16px;")
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #e8eaed; font-weight: bold; font-size: 14px;")
        
        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        layout.addSpacing(10)
        
        # Buttons Row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        for btn in buttons:
            btn_layout.addWidget(btn)
        
        layout.addLayout(btn_layout)
        layout.addStretch()

# --- 3. Sub-Dialogs (Link & Paste) ---
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
        btn = QPushButton("Add Source")
        btn.setStyleSheet("background-color: #8ab4f8; color: #202124; border-radius: 4px; padding: 8px; font-weight: bold;")
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
        self.title.setPlaceholderText("Title (e.g. Meeting Notes)")
        self.title.setStyleSheet("background: #202124; border: 1px solid #5f6368; padding: 8px; color: white; border-radius: 4px;")
        self.area = QTextEdit()
        self.area.setPlaceholderText("Paste text here...")
        self.area.setStyleSheet("background: #202124; border: 1px solid #5f6368; color: white; border-radius: 4px;")
        btn = QPushButton("Add Source")
        btn.setStyleSheet("background-color: #8ab4f8; color: #202124; border-radius: 4px; padding: 8px; font-weight: bold;")
        btn.clicked.connect(self.accept)
        layout.addWidget(QLabel("Title:"))
        layout.addWidget(self.title)
        layout.addWidget(QLabel("Content:"))
        layout.addWidget(self.area)
        layout.addWidget(btn)
    def get_data(self): return self.title.text(), self.area.toPlainText()

# --- 4. Main Dialog Class ---

class SourceUploadDialog(QDialog):
    sources_added = pyqtSignal() 

    def __init__(self, backend_instance, parent=None):
        super().__init__(parent)
        self.backend = backend_instance 
        self.link_extractor = ExtractLink()
        self.text_extractor = ExtractText()
        
        self.setWindowTitle("Add sources")
        self.resize(950, 650)
        # Main Dialog Style
        self.setStyleSheet("""
            QDialog { background-color: #1e1f20; }
            QLabel { color: #bdc1c6; font-size: 13px; }
            QProgressBar { border: none; background: #3c4043; height: 6px; border-radius: 3px; } 
            QProgressBar::chunk { background: #a8c7fa; border-radius: 3px; }
        """)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)

        # 1. Header
        header_lbl = QLabel("Add sources")
        header_lbl.setStyleSheet("font-size: 24px; color: #e8eaed; font-weight: 500;")
        main_layout.addWidget(header_lbl)
        
        sub_lbl = QLabel("Sources let OpenbookLM base its responses on the information that matters most to you.\n(Examples: marketing plans, course reading, research notes, etc.)")
        sub_lbl.setWordWrap(True)
        main_layout.addWidget(sub_lbl)

        # 2. Drop Zone (Big Central Area)
        self.drop_zone = QLabel("⬆\n\nUpload sources\nDrag & drop or choose file to upload")
        self.drop_zone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_zone.setObjectName("DropZone")
        self.drop_zone.setFixedHeight(220)
        self.drop_zone.setAcceptDrops(True)
        self.drop_zone.setStyleSheet("""
            QLabel#DropZone { 
                border: 2px dashed #5f6368; 
                background-color: rgba(32, 33, 36, 150); 
                border-radius: 12px; 
                color: #e8eaed; font-size: 15px; font-weight: bold;
            }
            QLabel#DropZone:hover { 
                border-color: #8ab4f8; 
                background-color: rgba(48, 49, 52, 200); 
            }
        """)
        # Connect Events
        self.drop_zone.dragEnterEvent = self.dragEnterEvent
        self.drop_zone.dragMoveEvent = self.dragMoveEvent
        self.drop_zone.dropEvent = self.dropEvent
        self.drop_zone.mousePressEvent = lambda e: self.open_file_dialog()
        main_layout.addWidget(self.drop_zone)

        main_layout.addWidget(QLabel("Supported file types: PDF, .txt, .docx, .md, Audio (mp3), etc."))

        # 3. Source Options Grid (The "Cards")
        grid_layout = QHBoxLayout()
        grid_layout.setSpacing(20)

        # Group 1: Google (Placeholder)
        drive_btn = SourceChip("📂", "Google Drive", lambda: print("Drive Todo"))
        group_drive = SourceGroup("Google Workspace", "G", [drive_btn])
        
        # Group 2: Link
        web_btn = SourceChip("🌐", "Website", self.open_link)
        yt_btn = SourceChip("▶️", "YouTube", self.open_link) # Can reuse logic or add specific Youtube logic
        group_link = SourceGroup("Link", "🔗", [web_btn, yt_btn])

        # Group 3: Text
        paste_btn = SourceChip("📋", "Copied text", self.open_paste)
        group_text = SourceGroup("Paste text", "T", [paste_btn])

        grid_layout.addWidget(group_drive)
        grid_layout.addWidget(group_link)
        grid_layout.addWidget(group_text)
        
        main_layout.addLayout(grid_layout)
        main_layout.addStretch()

        # 4. Footer Limit
        footer = QHBoxLayout()
        footer.addWidget(QLabel("Source limit"))
        self.bar = QProgressBar()
        self.bar.setValue(len(self.backend.get_project_files()))
        self.bar.setMaximum(50)
        footer.addWidget(self.bar)
        
        count_lbl = QLabel(f"{self.bar.value()} / 50")
        footer.addWidget(count_lbl)
        
        main_layout.addLayout(footer)

    # --- Logic Handlers (Same as before) ---
    def dragEnterEvent(self, e): e.accept()
    def dragMoveEvent(self, e): e.accept()
    
    def dropEvent(self, e):
        if e.mimeData().hasUrls():
            files = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
            self.backend.add_files_to_project(files)
            self.sources_added.emit()
            self.bar.setValue(len(self.backend.get_project_files()))
            QMessageBox.information(self, "Success", f"Added {len(files)} files")

    def open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(self)
        if files:
            self.backend.add_files_to_project(files)
            self.sources_added.emit()
            self.bar.setValue(len(self.backend.get_project_files()))

    def open_link(self):
        dlg = URLDialog(self)
        if dlg.exec():
            url = dlg.get_url()
            docs = self.link_extractor.url_extraction(url)
            if docs:
                content = "\n".join([d.page_content for d in docs])
                self.backend.save_text_to_project(content, f"Web_{len(url)}")
                self.sources_added.emit()
                self.bar.setValue(len(self.backend.get_project_files()))
                QMessageBox.information(self, "Success", "Link content added")

    def open_paste(self):
        dlg = TextPasteDialog(self)
        if dlg.exec():
            t, c = dlg.get_data()
            if c:
                self.backend.save_text_to_project(c, t or "Pasted")
                self.sources_added.emit()
                self.bar.setValue(len(self.backend.get_project_files()))