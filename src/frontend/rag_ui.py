import sys
import os
import shutil
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QPushButton, QLabel, QFrame, QScrollArea, 
    QLineEdit, QFileDialog, QProgressBar, QTextBrowser, QSizePolicy,
    QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QFont, QColor, QCursor, QIcon
from PyQt6.QtCore import Qt, QSize, QTimer, QThread, pyqtSignal

# ---------------------------------------------------------
# CRITICAL FIX: Backend Import Logic (Matched to test.py)
# ---------------------------------------------------------
# 1. Resolve paths relative to this file
current_file = Path(__file__).resolve()
frontend_dir = current_file.parent  # src/frontend
src_dir = frontend_dir.parent       # src
rag_dir = src_dir / "RAG"           # src/RAG

# 2. Add 'src/RAG' to sys.path so Python finds 'search', 'vectorstore', etc.
sys.path.append(str(rag_dir))

# 3. Define Data Directory
DATA_DIR = src_dir / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 4. Import Backend Modules
try:
    from search import RAGsearch
    from vectorstore import FaissVectorStore
    from data_loader import DocumentLoader
    print("✅ Backend loaded successfully.")
except ImportError as e:
    print(f"❌ CRITICAL ERROR: Could not import Backend modules. Details: {e}")
    sys.exit(1)
# ---------------------------------------------------------

# --- Stylesheet (NotebookLM Dark Theme) ---
STYLESHEET = """
QMainWindow { background-color: #131314; }
QLabel { color: #E3E3E3; font-family: 'Segoe UI', sans-serif; }
QLabel#HeaderTitle { font-size: 22px; font-weight: 500; }
QLabel#SectionTitle { font-size: 18px; font-weight: 500; color: #E3E3E3; margin-bottom: 10px; }
QLabel#CardTitle { font-size: 16px; font-weight: 600; color: #ffffff; }
QLabel#CardSubtext { font-size: 12px; color: #9aa0a6; }

QFrame#NotebookCard { 
    background-color: #1E1F20; border-radius: 12px; border: 1px solid #3c4043;
}
QFrame#NotebookCard:hover { 
    background-color: #2D2E30; border: 1px solid #5f6368;
}
QFrame#CreateCard {
    background-color: #1E1F20; border-radius: 12px; border: 1px solid #3c4043;
}
QFrame#CreateCard:hover { background-color: #2D2E30; }

QPushButton#SettingsBtn { background: transparent; color: #e3e3e3; border: 1px solid #5f6368; border-radius: 18px; padding: 5px 15px; font-weight: 600;}
QPushButton#SettingsBtn:hover { background-color: #303134; }

QLineEdit { 
    background-color: #1E1F20; color: white; border: 1px solid #5f6368; 
    border-radius: 25px; padding: 15px; font-size: 14px; 
}
QLineEdit:focus { border: 1px solid #8ab4f8; }
QTextBrowser { background-color: transparent; border: none; font-size: 15px; color: #e3e3e3; }
QProgressBar { background: transparent; }
QProgressBar::chunk { background-color: #8ab4f8; }
"""

# --- Custom Widgets ---
class NotebookCard(QFrame):
    clicked = pyqtSignal(str) 

    def __init__(self, title, date, sources, emoji="📓"):
        super().__init__()
        self.setObjectName("NotebookCard")
        self.setFixedSize(300, 180)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.title = title
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        top_row = QHBoxLayout()
        icon_lbl = QLabel(emoji)
        icon_lbl.setStyleSheet("font-size: 24px; background: transparent;")
        top_row.addWidget(icon_lbl)
        top_row.addStretch()
        menu_lbl = QLabel("⋮") 
        menu_lbl.setStyleSheet("font-size: 20px; color: #9aa0a6;")
        top_row.addWidget(menu_lbl)
        layout.addLayout(top_row)
        
        # Title
        layout.addStretch()
        title_lbl = QLabel(title)
        title_lbl.setObjectName("CardTitle")
        layout.addWidget(title_lbl)
        
        # Footer
        meta_lbl = QLabel(f"{date} · {sources} sources")
        meta_lbl.setObjectName("CardSubtext")
        layout.addWidget(meta_lbl)

    def mousePressEvent(self, event):
        self.clicked.emit(self.title)
        super().mousePressEvent(event)

class CreateCard(QFrame):
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("CreateCard")
        self.setFixedSize(300, 180)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        plus_lbl = QLabel("+")
        plus_lbl.setStyleSheet("font-size: 40px; color: #8ab4f8; font-weight: 300;")
        plus_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        text_lbl = QLabel("Create new notebook")
        text_lbl.setStyleSheet("font-size: 16px; color: #e3e3e3; font-weight: 500; margin-top: 10px;")
        
        layout.addWidget(plus_lbl)
        layout.addWidget(text_lbl)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

# --- Workers ---
class SearchWorker(QThread):
    result_ready = pyqtSignal(str)
    def __init__(self, rag_engine, query):
        super().__init__()
        self.rag_engine = rag_engine
        self.query = query
    def run(self):
        try:
            summary = self.rag_engine.search_and_summarize(self.query, top_k=3)
            self.result_ready.emit(summary)
        except Exception as e:
            self.result_ready.emit(f"Error: {e}")

class IndexingWorker(QThread):
    finished = pyqtSignal(str)
    def run(self):
        try:
            loader = DocumentLoader(data_dir=str(DATA_DIR))
            store = FaissVectorStore("faiss_store")
            store.build_from_documents(loader)
            self.finished.emit("Done")
        except Exception as e:
            self.finished.emit(f"Error: {e}")

# --- Main Application ---
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NotebookLM Clone (PyQt6)")
        self.resize(1200, 800)
        self.setStyleSheet(STYLESHEET)
        
        self.rag_engine = None
        
        # Navigation Stack
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_stack = QVBoxLayout(self.central_widget)
        self.main_stack.setContentsMargins(0, 0, 0, 0)
        
        self.dashboard_view = self.create_dashboard_ui()
        self.chat_view = self.create_chat_ui()
        self.chat_view.setVisible(False)
        
        self.main_stack.addWidget(self.dashboard_view)
        self.main_stack.addWidget(self.chat_view)
        
        # Initialize Backend
        QTimer.singleShot(100, self.init_backend)

    def init_backend(self):
        try:
            self.rag_engine = RAGsearch(llm_model="gemma3:4b")
        except Exception as e:
            print(f"Engine Init Warning: {e}")

    # --- UI Construction ---
    def create_dashboard_ui(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        logo = QLabel("NotebookLM")
        logo.setObjectName("HeaderTitle")
        header.addWidget(logo)
        header.addStretch()
        
        settings_btn = QPushButton("Settings")
        settings_btn.setObjectName("SettingsBtn")
        header.addWidget(settings_btn)
        layout.addLayout(header)

        # Grid
        layout.addSpacing(20)
        lbl_recent = QLabel("Recent notebooks")
        lbl_recent.setObjectName("SectionTitle")
        layout.addWidget(lbl_recent)

        grid_area = QScrollArea()
        grid_area.setWidgetResizable(True)
        grid_area.setStyleSheet("background: transparent; border: none;")
        
        grid_container = QWidget()
        grid_container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.grid_layout.setSpacing(20)

        create_card = CreateCard()
        create_card.clicked.connect(self.on_create_notebook)
        self.grid_layout.addWidget(create_card, 0, 0)

        # Examples
        self.add_notebook_card("Maths", "Mar 3, 2025", 26, "👨‍🏫", 0, 1)
        self.add_notebook_card("Globalisation", "Nov 4, 2025", 12, "🌍", 0, 2)

        grid_area.setWidget(grid_container)
        layout.addWidget(grid_area)
        return widget

    def add_notebook_card(self, title, date, sources, emoji, row, col):
        card = NotebookCard(title, date, sources, emoji)
        card.clicked.connect(lambda t=title: self.open_notebook(t))
        self.grid_layout.addWidget(card, row, col)

    def create_chat_ui(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Top Bar
        top_bar = QFrame()
        top_bar.setStyleSheet("background-color: #1E1F20; border-bottom: 1px solid #3c4043;")
        top_bar.setFixedHeight(60)
        tb_layout = QHBoxLayout(top_bar)
        
        back_btn = QPushButton("← Dashboard")
        back_btn.setStyleSheet("color: #8ab4f8; font-weight: bold; border: none; font-size: 14px;")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.go_to_dashboard)
        
        self.chat_title = QLabel("Notebook")
        self.chat_title.setStyleSheet("font-size: 18px; font-weight: 500; color: white;")
        
        upload_btn = QPushButton("Add Source")
        upload_btn.setObjectName("SettingsBtn")
        upload_btn.clicked.connect(self.upload_file)

        tb_layout.addWidget(back_btn)
        tb_layout.addSpacing(20)
        tb_layout.addWidget(self.chat_title)
        tb_layout.addStretch()
        tb_layout.addWidget(upload_btn)
        layout.addWidget(top_bar)

        # Chat
        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(True)
        self.chat_display.setStyleSheet("""
            QScrollBar:vertical { background: #131314; width: 10px; }
            QScrollBar::handle:vertical { background: #5f6368; border-radius: 5px; }
        """)
        layout.addWidget(self.chat_display)

        self.pbar = QProgressBar()
        self.pbar.setFixedHeight(4)
        self.pbar.setTextVisible(False)
        self.pbar.setVisible(False)
        layout.addWidget(self.pbar)

        # Input
        input_container = QWidget()
        input_container.setStyleSheet("background-color: #131314;")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(20, 20, 20, 20)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask a question about the sources...")
        self.input_field.returnPressed.connect(self.send_message)
        
        send_btn = QPushButton("➤")
        send_btn.setFixedSize(50, 50)
        send_btn.setStyleSheet("background-color: #8ab4f8; border-radius: 25px; color: #131314; font-size: 20px;")
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(send_btn)
        layout.addWidget(input_container)
        return widget

    # --- Actions ---
    def go_to_dashboard(self):
        self.chat_view.setVisible(False)
        self.dashboard_view.setVisible(True)

    def open_notebook(self, title):
        self.chat_title.setText(title)
        self.dashboard_view.setVisible(False)
        self.chat_view.setVisible(True)
        self.chat_display.clear()
        self.append_system_msg(f"Loaded notebook: {title}")

    def on_create_notebook(self):
        self.open_notebook("New Project")
        self.upload_file()

    def upload_file(self):
        fnames, _ = QFileDialog.getOpenFileNames(self, "Select Documents", "", "Documents (*.pdf *.txt *.docx)")
        if fnames:
            for f in fnames:
                shutil.copy(f, str(DATA_DIR))
            
            self.pbar.setVisible(True)
            self.pbar.setRange(0,0)
            self.append_system_msg("Structuring new sources...")
            
            self.worker = IndexingWorker()
            self.worker.finished.connect(self.on_indexing_done)
            self.worker.start()

    def on_indexing_done(self, msg):
        self.pbar.setVisible(False)
        self.append_system_msg("Sources added. You can now chat.")
        try:
            self.rag_engine = RAGsearch(llm_model="gemma3:4b")
        except:
            pass

    def send_message(self):
        text = self.input_field.text().strip()
        if not text: return
        
        self.append_chat_bubble(text, is_user=True)
        self.input_field.clear()
        
        if not self.rag_engine:
            self.append_system_msg("⚠️ Backend not ready. Upload a file first.")
            return

        self.pbar.setVisible(True)
        self.pbar.setRange(0,0)
        self.search_worker = SearchWorker(self.rag_engine, text)
        self.search_worker.result_ready.connect(self.on_bot_reply)
        self.search_worker.start()

    def on_bot_reply(self, text):
        self.pbar.setVisible(False)
        self.append_chat_bubble(text, is_user=False)

    def append_chat_bubble(self, text, is_user):
        align = "right" if is_user else "left"
        bg_color = "#3c4043" if is_user else "transparent"
        style = f"""
            <div style="text-align: {align}; margin-bottom: 10px;">
                <div style="display: inline-block; background-color: {bg_color}; 
                            padding: 10px 15px; border-radius: 15px; color: white; font-size: 16px;">
                    {text}
                </div>
            </div>
        """
        self.chat_display.append(style)

    def append_system_msg(self, text):
        self.chat_display.append(f"<div style='text-align: center; color: #9aa0a6; margin: 10px;'><i>{text}</i></div>")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())