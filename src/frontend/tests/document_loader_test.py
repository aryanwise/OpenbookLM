import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QFileDialog, QFrame, 
    QMessageBox, QDialog, QTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor

# Adjust path as needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'RAG')))
try:
    # IMPORT ALL YOUR CLASSES HERE
    from data_loader import DocumentLoader, ExtractLink, ExtractText
except ImportError:
    # Fallback for direct testing
    from data_loader import DocumentLoader, ExtractLink, ExtractText

# --- Dialogs ---

class URLDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Website Link")
        self.setFixedSize(400, 160)
        self.setStyleSheet("""
            QDialog { background-color: #303134; color: white; border: 1px solid #5f6368; }
            QLabel { color: #e8eaed; font-size: 14px; }
            QLineEdit { background-color: #202124; color: white; border: 1px solid #5f6368; padding: 5px; border-radius: 4px; }
            QPushButton { background-color: #8ab4f8; color: #202124; padding: 8px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #a8c7fa; }
        """)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Enter URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")
        layout.addWidget(self.url_input)
        
        self.add_btn = QPushButton("Add Source")
        self.add_btn.clicked.connect(self.accept)
        layout.addWidget(self.add_btn)

    def get_url(self):
        return self.url_input.text().strip()

class TextPasteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paste Text")
        self.resize(500, 400)
        self.setStyleSheet("""
            QDialog { background-color: #303134; color: white; border: 1px solid #5f6368; }
            QLabel { color: #e8eaed; font-weight: bold; }
            QLineEdit, QTextEdit { background-color: #202124; color: white; border: 1px solid #5f6368; padding: 5px; border-radius: 4px; }
            QPushButton { background-color: #8ab4f8; color: #202124; padding: 8px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #a8c7fa; }
        """)
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Title (File Name):"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Meeting Notes")
        layout.addWidget(self.title_input)
        
        layout.addWidget(QLabel("Content:"))
        self.content_area = QTextEdit()
        layout.addWidget(self.content_area)
        
        self.save_btn = QPushButton("Save to Project")
        self.save_btn.clicked.connect(self.accept)
        layout.addWidget(self.save_btn)

    def get_data(self):
        return self.title_input.text().strip(), self.content_area.toPlainText()

# --- Main UI Components ---

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
        
        icon = QLabel(icon_text)
        icon.setStyleSheet("font-size: 20px; margin-bottom: 5px; background: transparent; border: none;")
        
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #e8eaed; background: transparent; border: none;")
        
        s_lbl = QLabel(subtitle)
        s_lbl.setStyleSheet("color: #bdc1c6; font-size: 12px; background: transparent; border: none;")
        
        layout.addWidget(icon)
        layout.addWidget(t_lbl)
        layout.addWidget(s_lbl)
        layout.addStretch()

# --- Main Window ---

class ModernLoaderWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # INSTANTIATE YOUR CLASSES
        self.backend = DocumentLoader()
        self.link_extractor = ExtractLink() # <--- Using your class
        self.text_extractor = ExtractText() # <--- Using your class
        
        self.MAX_SOURCES = 300
        
        self.setWindowTitle("OpenbookLM Data Loader")
        self.resize(1000, 750)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Stylesheet
        self.setStyleSheet("""
            QMainWindow { background-color: transparent; }
            QWidget#CentralWidget { 
                background-color: rgba(32, 33, 36, 240); 
                border-radius: 15px; 
                border: 1px solid #5f6368;
            }
            QLabel { color: #e8eaed; }
            QLineEdit { background-color: #303134; color: white; border: 1px solid #5f6368; border-radius: 4px; padding: 8px; }
            QPushButton { background-color: #8ab4f8; color: #202124; border-radius: 4px; padding: 6px 12px; font-weight: bold; }
            QPushButton#SecondaryBtn { background-color: transparent; color: #8ab4f8; border: 1px solid #5f6368; }
            
            #DropZone { border: 2px dashed #5f6368; background-color: rgba(48, 49, 52, 150); color: #bdc1c6; border-radius: 12px; font-size: 16px; }
            #DropZone:hover { border-color: #8ab4f8; background-color: rgba(60, 64, 67, 200); }
            
            #ActionCard { background-color: rgba(48, 49, 52, 200); border: 1px solid #5f6368; border-radius: 8px; }
            #ActionCard:hover { background-color: rgba(60, 64, 67, 255); border-color: #a8c7fa; }
            
            QProgressBar { border: none; background-color: #3c4043; height: 6px; border-radius: 3px; }
            QProgressBar::chunk { background-color: #a8c7fa; border-radius: 3px; }
        """)

        self.init_ui()
        self.check_initial_config()

    def init_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(50, 40, 50, 40)
        main_layout.setSpacing(25)

        # --- Top Bar ---
        top_bar = QHBoxLayout()
        self.root_label = QLabel("Root: Not Set")
        self.root_label.setStyleSheet("color: #9aa0a6; font-size: 12px; font-style: italic;")
        self.change_root_btn = QPushButton("⚙ Config")
        self.change_root_btn.setObjectName("SecondaryBtn")
        self.change_root_btn.setFixedSize(80, 30)
        self.change_root_btn.clicked.connect(self.select_root_folder)
        top_bar.addWidget(self.root_label)
        top_bar.addStretch()
        top_bar.addWidget(self.change_root_btn)
        main_layout.addLayout(top_bar)

        # --- Project Header ---
        header_layout = QHBoxLayout()
        title = QLabel("Add sources")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.project_input = QLineEdit()
        self.project_input.setPlaceholderText("Project Name...")
        self.project_input.setFixedWidth(200)
        self.project_input.returnPressed.connect(self.setup_project)
        
        self.create_btn = QPushButton("Load Project")
        self.create_btn.clicked.connect(self.setup_project)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.project_input)
        header_layout.addWidget(self.create_btn)
        main_layout.addLayout(header_layout)

        # Subtitle
        sub = QLabel("Sources let OpenbookLM base its responses on the information that matters most to you.")
        sub.setStyleSheet("color: #bdc1c6; font-size: 14px;")
        main_layout.addWidget(sub)

        # --- Drop Zone ---
        self.drop_zone = DropZone(main_window=self)
        self.drop_zone.setFixedHeight(220)
        main_layout.addWidget(self.drop_zone)

        # --- Action Cards ---
        cards_layout = QHBoxLayout()
        self.link_card = ActionCard("Link", "Website", "🔗", self.open_link_dialog)
        self.paste_card = ActionCard("Paste text", "Copied text", "📋", self.open_paste_dialog)
        cards_layout.addWidget(self.link_card)
        cards_layout.addWidget(self.paste_card)
        main_layout.addLayout(cards_layout)
        
        main_layout.addStretch()

        # --- Footer: Source Limit Bar ---
        footer_layout = QHBoxLayout()
        
        limit_icon = QLabel("⬆") 
        limit_icon.setStyleSheet("font-size: 16px; color: #e8eaed;")
        
        limit_lbl = QLabel("Source limit")
        limit_lbl.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.source_progress = QProgressBar()
        self.source_progress.setRange(0, self.MAX_SOURCES)
        self.source_progress.setValue(0)
        self.source_progress.setTextVisible(False)
        self.source_progress.setFixedHeight(6)
        
        self.count_label = QLabel(f"0 / {self.MAX_SOURCES}")
        self.count_label.setStyleSheet("color: #bdc1c6; font-size: 12px; margin-left: 10px;")
        
        footer_layout.addWidget(limit_icon)
        footer_layout.addWidget(limit_lbl)
        footer_layout.addWidget(self.source_progress)
        footer_layout.addWidget(self.count_label)
        
        main_layout.addLayout(footer_layout)

        self.toggle_main_ui(False)

    # --- Logic ---

    def check_initial_config(self):
        if self.backend.base_storage_path:
            self.root_label.setText(f"Root: {self.backend.base_storage_path}")
        else:
            self.select_root_folder()

    def select_root_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Main Storage Folder")
        if folder:
            self.backend.set_storage_location(folder)
            self.root_label.setText(f"Root: {self.backend.base_storage_path}")

    def setup_project(self):
        name = self.project_input.text()
        if not name or not self.backend.base_storage_path:
            return
        
        try:
            self.backend.create_load_project(name)
            self.toggle_main_ui(True)
            self.update_file_count()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def toggle_main_ui(self, enable):
        self.drop_zone.setVisible(enable)
        self.link_card.setVisible(enable)
        self.paste_card.setVisible(enable)

    def check_limit_reached(self):
        current_count = len(self.backend.get_project_files())
        if current_count >= self.MAX_SOURCES:
            QMessageBox.warning(self, "Limit Reached", f"You have reached the maximum limit of {self.MAX_SOURCES} sources.")
            return True
        return False

    def process_files(self, files):
        if self.check_limit_reached(): return
        
        current_count = len(self.backend.get_project_files())
        if current_count + len(files) > self.MAX_SOURCES:
            QMessageBox.warning(self, "Limit Exceeded", f"Cannot add {len(files)} files. Remaining space: {self.MAX_SOURCES - current_count}")
            return

        self.backend.add_files_to_project(files)
        self.update_file_count()

    def open_link_dialog(self):
        if self.check_limit_reached(): return
        dlg = URLDialog(self)
        if dlg.exec():
            url = dlg.get_url()
            if url:
                # 1. Use YOUR ExtractLink class
                docs = self.link_extractor.url_extraction(url)
                
                if docs:
                    # 2. Process data returned by your class
                    content = "\n\n".join([d.page_content for d in docs])
                    title = "website_content" # You could refine this to get title from metadata
                    
                    # 3. Save using DocumentManager
                    self.backend.save_text_to_project(content, f"{title}_{len(url)}")
                    self.update_file_count()
                    QMessageBox.information(self, "Success", "Link extracted and saved!")
                else:
                    QMessageBox.warning(self, "Error", "Failed to extract content from link.")

    def open_paste_dialog(self):
        if self.check_limit_reached(): return
        dlg = TextPasteDialog(self)
        if dlg.exec():
            title, content = dlg.get_data()
            if content:
                # 1. Use YOUR ExtractText class
                formatted_text = self.text_extractor.extract_text(content)
                
                if not title: title = "pasted_text"
                
                # 2. Save using DocumentManager
                self.backend.save_text_to_project(formatted_text, title)
                self.update_file_count()

    def open_file_dialog(self):
        if self.check_limit_reached(): return
        files, _ = QFileDialog.getOpenFileNames(self)
        if files: self.process_files(files)

    def update_file_count(self):
        files = self.backend.get_project_files()
        count = len(files)
        self.source_progress.setValue(count)
        self.count_label.setText(f"{count} / {self.MAX_SOURCES}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModernLoaderWindow()
    window.show()
    sys.exit(app.exec())