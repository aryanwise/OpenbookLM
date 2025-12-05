import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QListWidget, QListWidgetItem, QPushButton, 
    QLineEdit, QFrame, QMenu, QInputDialog, QMessageBox, 
    QProgressBar, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QCursor, QAction

# --- 1. SETUP PATHS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..', 'RAG'))
sys.path.append(root_dir)
sys.path.append(os.path.abspath(os.path.join(current_dir, '..')))

# --- 2. IMPORTS ---
try:
    from frontend.styles import *
    from frontend.add_source_dialog import SourceUploadDialog
except ImportError:
    pass

try:
    from llm.ollama_integration import OllamaClient
except ImportError as e:
    class OllamaClient:
        def chat(self, msg): return "Error: LLM Client not found."

# --- WORKER THREAD ---
class OllamaWorker(QThread):
    response_received = pyqtSignal(str) 

    def __init__(self, prompt, client):
        super().__init__()
        self.prompt = prompt
        self.client = client

    def run(self):
        if self.client:
            response = self.client.chat(self.prompt)
            self.response_received.emit(response)

# --- 3. CUSTOM CHAT BUBBLE WIDGET ---
class MessageBubble(QWidget):
    def __init__(self, text, is_user=False, is_thinking=False):
        super().__init__()
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 5, 0, 5)

        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        # Font settings (High legibility)
        font_size = "16px"
        line_height = "1.6"
        
        if is_thinking:
            self.label.setStyleSheet(f"color: {TEXT_SUB}; font-style: italic; font-size: 14px; background: transparent;")
            self.layout.addWidget(self.label)
            self.layout.addStretch() 
            
        elif is_user:
            # USER: Right Aligned, Compact Blue Bubble
            self.label.setStyleSheet(f"""
                QLabel {{
                    background-color: {ACCENT_PRIMARY};
                    color: white;
                    border-radius: 12px;
                    padding: 12px 18px;
                    font-size: {font_size};
                    line-height: {line_height};
                }}
            """)
            self.layout.addStretch() # Pushes bubble to the right
            self.layout.addWidget(self.label)
            self.label.setMaximumWidth(650) # Keep user messages readable/compact
            
        else:
            # AI: Left Aligned, FULL WIDTH Plain Text
            self.label.setStyleSheet(f"""
                QLabel {{
                    background-color: transparent;
                    color: {TEXT_MAIN};
                    padding: 4px 0px;
                    font-size: {font_size};
                    line-height: {line_height};
                }}
            """)
            
            # --- FIX: FULL WIDTH LOGIC ---
            # 1. We allow the label to expand horizontally to fill space
            self.label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            
            # 2. Add the widget directly. DO NOT addStretch() afterwards.
            # This ensures it takes all available width in the layout.
            self.layout.addWidget(self.label)

# --- MAIN WINDOW ---
class WorkspaceWindow(QMainWindow):
    def __init__(self, project_name, backend_instance):
        super().__init__()
        self.project_name = project_name
        self.backend = backend_instance 
        self.ollama_client = OllamaClient() 
        self.thinking_bubble = None 
        
        self.setWindowTitle(f"{project_name}")
        self.resize(1400, 950)
        
        # Theme
        self.setStyleSheet(GLOBAL_STYLE + f"""
            QMainWindow {{ background: {BG_GRADIENT}; }}
            QFrame#LeftPanel {{ 
                background-color: rgba(15, 17, 21, 0.6); 
                border-right: 1px solid {BORDER_SUBTLE}; 
            }}
            QListWidget {{ background: transparent; border: none; outline: none; }}
            QListWidget::item {{ color: {TEXT_SUB}; padding: 12px 16px; margin-bottom: 4px; border-radius: 6px; }}
            QListWidget::item:hover {{ background-color: {SURFACE_HOVER}; color: {TEXT_MAIN}; }}
            QListWidget::item:selected {{ background-color: rgba(59, 130, 246, 0.1); color: {ACCENT_PRIMARY}; border-left: 3px solid {ACCENT_PRIMARY}; }}
        """)

        self.init_ui()
        self.refresh_sources_list()

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
        back_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: 1px solid {BORDER_SUBTLE}; border-radius: 16px; color: {TEXT_SUB}; font-weight: bold; }}
            QPushButton:hover {{ border-color: {TEXT_MAIN}; color: {TEXT_MAIN}; }}
        """)
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
        self.add_btn.setStyleSheet(f"""
            QPushButton {{ background-color: rgba(255, 255, 255, 0.03); color: {ACCENT_PRIMARY}; border: 1px dashed {BORDER_SUBTLE}; border-radius: 8px; text-align: left; padding-left: 15px; font-weight: 600; }}
            QPushButton:hover {{ background-color: rgba(59, 130, 246, 0.1); border-color: {ACCENT_PRIMARY}; }}
        """)
        self.add_btn.clicked.connect(self.open_add_dialog)
        left_layout.addWidget(self.add_btn)

        # Source List
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

        # --- RIGHT PANEL (CHAT AREA) ---
        chat_panel = QFrame()
        chat_panel.setStyleSheet("background: transparent; border: none;")
        right_layout = QVBoxLayout(chat_panel)
        right_layout.setContentsMargins(100, 40, 100, 40) # Margins control total chat width constraints

        # Title
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
        
        # Chat Messages Container
        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(10, 10, 20, 10) # Right margin for scrollbar space
        
        # Spacing between User Question and AI Response
        self.chat_layout.setSpacing(30) 
        self.chat_layout.addStretch() 
        
        self.chat_scroll.setWidget(self.chat_container)
        right_layout.addWidget(self.chat_scroll)

        # Input Area
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
        self.dialog.sources_added.connect(self.refresh_sources_list)
        self.dialog.exec()

    def go_back(self):
        from frontend.main_window import MainWindow
        self.dashboard = MainWindow()
        self.dashboard.show()
        self.close()

    def send_message(self):
        msg = self.chat_input.text().strip()
        if not msg: return
        
        # 1. Add User Bubble
        user_bubble = MessageBubble(msg, is_user=True)
        self.chat_layout.insertWidget(self.chat_layout.count()-1, user_bubble)
        self.chat_input.clear()
        
        # 2. Add Thinking Bubble
        self.thinking_bubble = MessageBubble("Ollama is thinking...", is_thinking=True)
        self.chat_layout.insertWidget(self.chat_layout.count()-1, self.thinking_bubble)
        
        self.scroll_to_bottom()

        # 3. Disable Input
        self.chat_input.setDisabled(True)
        self.send_btn.setDisabled(True)

        # 4. Start Worker
        self.worker = OllamaWorker(msg, self.ollama_client)
        self.worker.response_received.connect(self.handle_ai_response)
        self.worker.start()

    def handle_ai_response(self, response_text):
        # 1. Remove Thinking
        if self.thinking_bubble:
            self.thinking_bubble.deleteLater()
            self.thinking_bubble = None
        
        # 2. Add AI Bubble
        ai_bubble = MessageBubble(response_text, is_user=False)
        self.chat_layout.insertWidget(self.chat_layout.count()-1, ai_bubble)
        
        # 3. Re-enable Input
        self.chat_input.setDisabled(False)
        self.send_btn.setDisabled(False)
        self.chat_input.setFocus()
        
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        QTimer.singleShot(100, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        ))