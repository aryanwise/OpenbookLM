import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QListWidget, QListWidgetItem, QPushButton, 
    QLineEdit, QFrame, QScrollArea, QSizePolicy, QScrollBar, QProgressBar, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QCursor, QAction

# --- PATH SETUP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..', 'RAG'))
sys.path.append(root_dir)
sys.path.append(os.path.abspath(os.path.join(current_dir, '..')))

# --- IMPORTS ---
try:
    from frontend.styles import *
    from frontend.add_source_dialog import SourceUploadDialog
    from RAG.rag_pipeline import RAGPipeline # <--- The new brain
except ImportError as e:
    print(f"Import Error: {e}")

# --- WORKER 1: SYNC FILES (Background Indexing) ---
class SyncWorker(QThread):
    finished_sync = pyqtSignal(str) # Emits status message

    def __init__(self, pipeline):
        super().__init__()
        self.pipeline = pipeline

    def run(self):
        # This takes time (embedding PDFs), so we run it here
        status = self.pipeline.sync_project_files()
        self.finished_sync.emit(status)

# --- WORKER 2: RAG CHAT (Background Generation) ---
class RAGWorker(QThread):
    response_received = pyqtSignal(str) 

    def __init__(self, query, pipeline):
        super().__init__()
        self.query = query
        self.pipeline = pipeline

    def run(self):
        # This takes time (LLM Inference), so we run it here
        response = self.pipeline.answer_query(self.query)
        self.response_received.emit(response)

# --- CHAT BUBBLE WIDGET (Same as before) ---
class MessageBubble(QWidget):
    def __init__(self, text, is_user=False, is_thinking=False):
        super().__init__()
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 5, 0, 5)
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        font_size = "16px"
        line_height = "1.6"
        
        if is_thinking:
            self.label.setStyleSheet(f"color: {TEXT_SUB}; font-style: italic; font-size: 14px; background: transparent;")
            self.layout.addWidget(self.label)
            self.layout.addStretch() 
        elif is_user:
            self.label.setStyleSheet(f"QLabel {{ background-color: {ACCENT_PRIMARY}; color: white; border-radius: 12px; padding: 12px 18px; font-size: {font_size}; line-height: {line_height}; }}")
            self.layout.addStretch()
            self.layout.addWidget(self.label)
            self.label.setMaximumWidth(650)
        else:
            self.label.setStyleSheet(f"QLabel {{ background-color: transparent; color: {TEXT_MAIN}; padding: 4px 0px; font-size: {font_size}; line-height: {line_height}; }}")
            self.label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            self.layout.addWidget(self.label)

# --- MAIN WINDOW ---
class WorkspaceWindow(QMainWindow):
    def __init__(self, project_name, backend_instance):
        super().__init__()
        self.project_name = project_name
        self.backend = backend_instance # This is DocumentManager
        
        # 1. Initialize RAG Engine
        # We assume the project path is set in the backend manager
        if self.backend.current_project_path:
            self.rag = RAGPipeline(self.backend.current_project_path)
        else:
            print("Error: No project path found")
            self.rag = None

        self.thinking_bubble = None 
        self.setWindowTitle(f"{project_name}")
        self.resize(1400, 950)
        
        # Apply Theme
        self.setStyleSheet(GLOBAL_STYLE + f"""
            QMainWindow {{ background: {BG_GRADIENT}; }}
            QFrame#LeftPanel {{ background-color: rgba(15, 17, 21, 0.6); border-right: 1px solid {BORDER_SUBTLE}; }}
            QListWidget {{ background: transparent; border: none; outline: none; }}
            QListWidget::item {{ color: {TEXT_SUB}; padding: 12px 16px; margin-bottom: 4px; border-radius: 6px; }}
            QListWidget::item:hover {{ background-color: {SURFACE_HOVER}; color: {TEXT_MAIN}; }}
            QListWidget::item:selected {{ background-color: rgba(59, 130, 246, 0.1); color: {ACCENT_PRIMARY}; border-left: 3px solid {ACCENT_PRIMARY}; }}
        """)

        self.init_ui()
        
        # 2. Start Background Sync (Don't freeze UI!)
        if self.rag:
            self.start_sync()
            self.load_chat_history()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- LEFT PANEL ---
        self.source_panel = QFrame()
        self.source_panel.setObjectName("LeftPanel")
        self.source_panel.setFixedWidth(300)
        left_layout = QVBoxLayout(self.source_panel)
        left_layout.setContentsMargins(20, 30, 20, 30)
        left_layout.setSpacing(20)

        # Header
        top_header = QHBoxLayout()
        back_btn = QPushButton("←")
        back_btn.setFixedSize(32, 32)
        back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        back_btn.setStyleSheet(f"QPushButton {{ background: transparent; border: 1px solid {BORDER_SUBTLE}; border-radius: 16px; color: {TEXT_SUB}; font-weight: bold; }} QPushButton:hover {{ border-color: {TEXT_MAIN}; color: {TEXT_MAIN}; }}")
        back_btn.clicked.connect(self.go_back)
        header_title = QLabel("Sources")
        header_title.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 16px; font-weight: 700;")
        top_header.addWidget(back_btn)
        top_header.addSpacing(12)
        top_header.addWidget(header_title)
        top_header.addStretch()
        left_layout.addLayout(top_header)

        # Add Btn
        self.add_btn = QPushButton("  + Add Source")
        self.add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.add_btn.setFixedHeight(40)
        self.add_btn.setStyleSheet(f"QPushButton {{ background-color: rgba(255, 255, 255, 0.03); color: {ACCENT_PRIMARY}; border: 1px dashed {BORDER_SUBTLE}; border-radius: 8px; text-align: left; padding-left: 15px; font-weight: 600; }} QPushButton:hover {{ background-color: rgba(59, 130, 246, 0.1); border-color: {ACCENT_PRIMARY}; }}")
        self.add_btn.clicked.connect(self.open_add_dialog)
        left_layout.addWidget(self.add_btn)

        # List
        self.source_list = QListWidget()
        self.source_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.source_list.customContextMenuRequested.connect(self.show_source_context_menu)
        left_layout.addWidget(self.source_list)

        # Footer
        footer_layout = QVBoxLayout()
        self.limit_lbl = QLabel("Source limit")
        self.limit_lbl.setStyleSheet(f"color: {TEXT_SUB}; font-size: 11px; margin-bottom: 5px;")
        self.limit_bar = QProgressBar()
        self.limit_bar.setMaximum(50)
        self.limit_bar.setTextVisible(False)
        self.limit_bar.setFixedHeight(4)
        self.limit_bar.setStyleSheet(f"QProgressBar {{ border: none; background: #334155; border-radius: 2px; }} QProgressBar::chunk {{ background: {ACCENT_PRIMARY}; border-radius: 2px; }}")
        footer_layout.addWidget(self.limit_lbl)
        footer_layout.addWidget(self.limit_bar)
        left_layout.addLayout(footer_layout)
        main_layout.addWidget(self.source_panel)

        # --- RIGHT PANEL ---
        chat_panel = QFrame()
        chat_panel.setStyleSheet("background: transparent; border: none;")
        right_layout = QVBoxLayout(chat_panel)
        right_layout.setContentsMargins(100, 40, 100, 40)

        chat_header = QLabel(self.project_name)
        chat_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chat_header.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 28px; font-weight: 700; margin-bottom: 20px;")
        right_layout.addWidget(chat_header)

        # Scroll Area
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("background: transparent; border: none;")
        self.chat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(10, 10, 20, 10)
        self.chat_layout.setSpacing(30)
        self.chat_layout.addStretch() 
        
        self.chat_scroll.setWidget(self.chat_container)
        right_layout.addWidget(self.chat_scroll)

        # Input
        input_container = QFrame()
        input_container.setFixedHeight(70)
        input_container.setStyleSheet(f"QFrame {{ background-color: rgba(30, 34, 40, 0.8); border: 1px solid {BORDER_SUBTLE}; border-radius: 35px; }}")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(25, 5, 10, 5)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type a question...")
        self.chat_input.setStyleSheet(f"background: transparent; border: none; color: {TEXT_MAIN}; font-size: 16px;")
        self.chat_input.returnPressed.connect(self.send_message)

        self.send_btn = QPushButton("➤")
        self.send_btn.setFixedSize(45, 45)
        self.send_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.send_btn.setStyleSheet(f"background-color: {ACCENT_PRIMARY}; color: white; border-radius: 22px; font-size: 18px; border: none;")
        self.send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(self.send_btn)
        right_layout.addWidget(input_container)
        main_layout.addWidget(chat_panel)

    # --- LOGIC ---

    def start_sync(self):
        """Starts the background file indexer."""
        self.refresh_sources_list()
        self.limit_lbl.setText("Syncing files...")
        
        self.sync_worker = SyncWorker(self.rag)
        self.sync_worker.finished_sync.connect(self.on_sync_complete)
        self.sync_worker.start()

    def on_sync_complete(self, status):
        self.refresh_sources_list()
        print(f"[SYNC] {status}")

    def load_chat_history(self):
        """Loads previous messages from SQLite."""
        history = self.rag.get_history()
        # Remove the stretch item temporarily
        stretch = self.chat_layout.takeAt(self.chat_layout.count()-1)
        
        for msg in history:
            role = msg['role']
            content = msg['content']
            is_user = (role == "user")
            bubble = MessageBubble(content, is_user=is_user)
            self.chat_layout.addWidget(bubble)
            
        # Add stretch back
        self.chat_layout.addItem(stretch)
        self.scroll_to_bottom()

    def refresh_sources_list(self):
        self.source_list.clear()
        files = self.backend.get_project_files()
        for f in files:
            icon = "📄"
            if f.endswith(".pdf"): icon = "📕"
            elif f.endswith(".txt"): icon = "📝"
            item = QListWidgetItem(f"{icon}  {f}")
            item.setData(Qt.ItemDataRole.UserRole, f)
            self.source_list.addItem(item)
        count = len(files)
        self.limit_bar.setValue(count)
        self.limit_lbl.setText(f"Source limit ({count}/50)")

    def send_message(self):
        msg = self.chat_input.text().strip()
        if not msg: return
        
        # Add User Bubble
        user_bubble = MessageBubble(msg, is_user=True)
        self.chat_layout.insertWidget(self.chat_layout.count()-1, user_bubble)
        self.chat_input.clear()
        
        # Add Thinking Bubble
        self.thinking_bubble = MessageBubble("Ollama is thinking...", is_thinking=True)
        self.chat_layout.insertWidget(self.chat_layout.count()-1, self.thinking_bubble)
        self.scroll_to_bottom()

        # Disable Input
        self.chat_input.setDisabled(True)
        self.send_btn.setDisabled(True)

        # Start RAG Worker
        self.worker = RAGWorker(msg, self.rag)
        self.worker.response_received.connect(self.handle_ai_response)
        self.worker.start()

    def handle_ai_response(self, response_text):
        if self.thinking_bubble:
            self.thinking_bubble.deleteLater()
            self.thinking_bubble = None
        
        ai_bubble = MessageBubble(response_text, is_user=False)
        self.chat_layout.insertWidget(self.chat_layout.count()-1, ai_bubble)
        
        self.chat_input.setDisabled(False)
        self.send_btn.setDisabled(False)
        self.chat_input.setFocus()
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        QTimer.singleShot(100, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        ))

    # --- Standard UI Methods (Same as before) ---
    def show_source_context_menu(self, pos):
        item = self.source_list.itemAt(pos)
        if not item: return
        filename = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu()
        menu.addAction(QAction("Delete", self))
        action = menu.exec(self.source_list.mapToGlobal(pos))
        if action and action.text() == "Delete":
            if QMessageBox.question(self, "Delete", f"Remove {filename}?") == QMessageBox.StandardButton.Yes:
                self.backend.delete_source_file(filename)
                self.refresh_sources_list()

    def open_add_dialog(self):
        self.dialog = SourceUploadDialog(self.backend, self)
        # When dialog closes, trigger sync again to index new files
        self.dialog.sources_added.connect(self.start_sync)
        self.dialog.exec()

    def go_back(self):
        from frontend.main_window import MainWindow
        self.dashboard = MainWindow()
        self.dashboard.show()
        self.close()