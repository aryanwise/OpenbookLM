import sys
import os
import shutil
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextBrowser, QLineEdit, QPushButton, QComboBox, QToolButton,
    QMenu, QSizePolicy, QListWidget, QListWidgetItem, QLabel, 
    QFileDialog, QProgressBar
)
from PyQt6.QtGui import QAction, QFont, QCursor
from PyQt6.QtCore import Qt, QEvent, QPoint, QPropertyAnimation, QEasingCurve, QThread, pyqtSignal, QSize

# --- Backend Imports ---
try:
    from ..RAG.search import RAGsearch
    from ..RAG.vectorstore import FaissVectorStore
    from ..RAG.data_loader import DocumentLoader
except ImportError as e:
    print(f"Backend modules missing: {e}")
    sys.exit(1)

# --- Constants ---
DATA_DIR = "./data"
os.makedirs(DATA_DIR, exist_ok=True)

# --- Worker Threads (To keep UI Responsive) ---

class IndexingWorker(QThread):
    finished = pyqtSignal(str)
    
    def run(self):
        try:
            # Re-initialize loader and build store
            loader = DocumentLoader(data_dir=DATA_DIR)
            store = FaissVectorStore("faiss_store")
            store.build_from_documents(loader)
            self.finished.emit("Indexing Complete. Knowledge Base Updated.")
        except Exception as e:
            self.finished.emit(f"Indexing Failed: {str(e)}")

class SearchWorker(QThread):
    result_ready = pyqtSignal(str) # returns response text

    def __init__(self, rag_engine, query):
        super().__init__()
        self.rag_engine = rag_engine
        self.query = query

    def run(self):
        try:
            if not self.rag_engine:
                self.result_ready.emit("Error: RAG Engine not initialized.")
                return
            
            # Call your backend logic
            summary = self.rag_engine.search_and_summarize(self.query, top_k=3)
            self.result_ready.emit(summary)
        except Exception as e:
            self.result_ready.emit(f"Error during search: {str(e)}")

# --- Mini Widget (Teams-like Minimize) ---
class MiniWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.restore_geometry = main_window.geometry()
        self.initUI()
        self.applyStyles()

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(360, 350)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        top_bar = QHBoxLayout()
        self.restore_button = QPushButton("🗖")
        self.restore_button.setFixedSize(30, 30)
        self.restore_button.clicked.connect(self.restoreMainWindow)
        
        lbl = QLabel("Assistant (Mini)")
        lbl.setStyleSheet("color: white; font-weight: bold;")
        
        top_bar.addWidget(lbl)
        top_bar.addStretch()
        top_bar.addWidget(self.restore_button)
        main_layout.addLayout(top_bar)

        # Chat Display
        self.mini_chat_display = QTextBrowser()
        self.mini_chat_display.setReadOnly(True)
        main_layout.addWidget(self.mini_chat_display)

        # Input
        input_layout = QHBoxLayout()
        self.mini_input = QLineEdit()
        self.mini_input.setPlaceholderText("Ask...")
        self.mini_input.returnPressed.connect(self.sendMessage)
        
        self.send_btn = QPushButton("➤")
        self.send_btn.setFixedSize(30, 30)
        self.send_btn.clicked.connect(self.sendMessage)
        
        input_layout.addWidget(self.mini_input)
        input_layout.addWidget(self.send_btn)
        main_layout.addLayout(input_layout)

    def applyStyles(self):
        self.setStyleSheet("""
            QWidget { background-color: rgba(30, 30, 30, 0.95); border-radius: 10px; color: white; }
            QTextBrowser { background-color: rgba(0,0,0,0.3); border: none; border-radius: 5px; padding: 5px; }
            QLineEdit { background-color: rgba(255,255,255,0.1); border: 1px solid #555; border-radius: 5px; color: white; padding: 5px;}
            QPushButton { background-color: #0078d4; border: none; border-radius: 5px; color: white; }
            QPushButton:hover { background-color: #0088f0; }
        """)

    def sendMessage(self):
        text = self.mini_input.text().strip()
        if text:
            self.main_window.handleUserMessage(text)
            self.mini_input.clear()

    def restoreMainWindow(self):
        self.main_window.show()
        if self.restore_geometry:
            self.main_window.setGeometry(self.restore_geometry)
        self.main_window.setWindowState(Qt.WindowState.WindowActive)
        self.hide()

    # Drag logic
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragPos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.dragPos)
            event.accept()

# --- Main Window ---
class ChatApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenStudyLM - RAG Workspace")
        self.setGeometry(100, 100, 900, 700)
        
        # Initialize Backend
        self.rag_engine = None
        self.init_backend()

        self.mini_widget = MiniWidget(self)
        self.chat_sessions = {}
        self.current_chat_id = "default"
        
        self.initUI()
        self.applyStyles()
        self.startNewChat()

    def init_backend(self):
        # We try to load the engine silently. If index missing, user must upload.
        try:
            self.rag_engine = RAGsearch(llm_model="gemma3:4b")
        except Exception:
            print("No index found. Waiting for upload.")

    def initUI(self):
        central_widget = QWidget()
        central_widget.setObjectName("CentralContainer")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        # 1. Top Bar
        top_bar = QWidget()
        top_bar.setObjectName("TopControlBar")
        top_bar.setMinimumHeight(50)
        top_layout = QHBoxLayout(top_bar)
        
        self.menu_btn = QPushButton("☰")
        self.menu_btn.setObjectName("TitleBarButton")
        self.menu_btn.setFixedSize(40, 40)
        self.menu_btn.clicked.connect(self.toggleHistoryPanel)
        
        title = QLabel("OpenStudyLM")
        title.setObjectName("WindowTitleLabel")
        
        top_layout.addWidget(self.menu_btn)
        top_layout.addWidget(title)
        top_layout.addStretch()
        
        main_layout.addWidget(top_bar)

        # 2. Main Area (Splitter for History / Chat)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(0)
        
        # Sidebar (History + Upload)
        self.sidebar = QWidget()
        self.sidebar.setObjectName("HistoryPanel")
        self.sidebar.setMaximumWidth(0) # Start hidden
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        
        # Upload Section in Sidebar
        upload_btn = QPushButton("📂 Upload Documents")
        upload_btn.setObjectName("ActionButton")
        upload_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        upload_btn.clicked.connect(self.upload_documents)
        sidebar_layout.addWidget(upload_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(5)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("background: #444; chunk {background: #0078d4;}")
        sidebar_layout.addWidget(self.progress_bar)

        # New Chat
        new_chat_btn = QPushButton("+ New Chat")
        new_chat_btn.setObjectName("ActionButton")
        new_chat_btn.clicked.connect(self.startNewChat)
        sidebar_layout.addWidget(new_chat_btn)

        # File List Label
        lbl_files = QLabel("Knowledge Base:")
        lbl_files.setStyleSheet("color: #aaa; margin-top: 10px; font-size: 12px;")
        sidebar_layout.addWidget(lbl_files)

        self.file_list = QListWidget()
        self.refresh_file_list()
        sidebar_layout.addWidget(self.file_list)
        
        content_layout.addWidget(self.sidebar)

        # Chat Area
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(20, 20, 20, 20)
        
        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(True)
        chat_layout.addWidget(self.chat_display)

        # Tool Strip (Hidden by default)
        self.tools_strip = QWidget()
        self.tools_strip.setVisible(False)
        tools_layout = QHBoxLayout(self.tools_strip)
        
        btn_voice = QPushButton("🎤 Voice Input")
        btn_voice.clicked.connect(self.toggle_voice)
        self.is_listening = False
        self.voice_btn = btn_voice # Ref for styling change
        
        tools_layout.addWidget(btn_voice)
        tools_layout.addStretch()
        chat_layout.addWidget(self.tools_strip)

        # Input Area
        input_frame = QHBoxLayout()
        
        self.tools_toggle = QPushButton("+")
        self.tools_toggle.setFixedSize(40, 40)
        self.tools_toggle.setObjectName("RoundButton")
        self.tools_toggle.clicked.connect(self.toggleToolsStrip)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask your documents...")
        self.input_field.setMinimumHeight(45)
        self.input_field.returnPressed.connect(self.send_clicked)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setMinimumHeight(45)
        self.send_btn.setObjectName("SendButton")
        self.send_btn.clicked.connect(self.send_clicked)
        
        input_frame.addWidget(self.tools_toggle)
        input_frame.addWidget(self.input_field)
        input_frame.addWidget(self.send_btn)
        
        chat_layout.addLayout(input_frame)
        content_layout.addWidget(chat_container)
        
        main_layout.addLayout(content_layout)

    # --- Logic ---

    def startNewChat(self):
        self.chat_display.clear()
        self.append_system_message("Started new session. Ready to query your documents.")

    def upload_documents(self):
        fnames, _ = QFileDialog.getOpenFileNames(self, "Select Documents", "", "Documents (*.pdf *.txt *.docx)")
        if fnames:
            for f in fnames:
                shutil.copy(f, DATA_DIR)
            self.refresh_file_list()
            
            # Start Indexing Thread
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0) # Infinite loading
            self.append_system_message("Structuring knowledge base... please wait.")
            
            self.indexer = IndexingWorker()
            self.indexer.finished.connect(self.on_indexing_finished)
            self.indexer.start()

    def on_indexing_finished(self, msg):
        self.progress_bar.setVisible(False)
        self.append_system_message(msg)
        # Re-init RAG to pick up new index
        self.init_backend()

    def refresh_file_list(self):
        self.file_list.clear()
        if os.path.exists(DATA_DIR):
            for f in os.listdir(DATA_DIR):
                self.file_list.addItem(f"📄 {f}")

    def send_clicked(self):
        text = self.input_field.text().strip()
        if text:
            self.handleUserMessage(text)
            self.input_field.clear()

    def handleUserMessage(self, text):
        # 1. Show User Message
        self.append_message("You", text)
        
        if not self.rag_engine:
            self.append_system_message("Engine not ready. Please upload documents first.")
            return

        # 2. Show 'Thinking' state
        self.input_field.setDisabled(True)
        self.send_btn.setText("...")
        
        # 3. Start Background Thread
        self.worker = SearchWorker(self.rag_engine, text)
        self.worker.result_ready.connect(self.on_search_result)
        self.worker.start()

    def on_search_result(self, response):
        self.input_field.setDisabled(False)
        self.send_btn.setText("Send")
        self.append_message("AI", response)

    def append_message(self, sender, text):
        # HTML Formatting for "Bubble" effect
        if sender == "You":
            color = "#0078d4"
            align = "right"
            bg = "rgba(0, 120, 212, 0.2)"
        else:
            color = "#28a745"
            align = "left"
            bg = "rgba(40, 167, 69, 0.1)"
            
        html = f"""
        <div style="margin: 5px; text-align: {align};">
            <span style="font-weight:bold; color: {color};">{sender}</span><br>
            <div style="background-color: {bg}; padding: 10px; border-radius: 10px; display: inline-block; color: #e0e0e0;">
                {text.replace(chr(10), '<br>')}
            </div>
        </div>
        """
        self.chat_display.append(html)
        
        # Sync to Mini Widget
        self.mini_widget.mini_chat_display.append(f"<b>{sender}:</b> {text}")

    def append_system_message(self, text):
        self.chat_display.append(f"<div style='color: #888; text-align: center; font-style: italic; margin: 10px;'>{text}</div>")

    def toggle_voice(self):
        if not self.is_listening:
            self.is_listening = True
            self.voice_btn.setStyleSheet("background-color: #dc3545; color: white; border: none; padding: 5px;")
            self.voice_btn.setText("🔴 Listening...")
            # Here you would trigger actual STT recording
        else:
            self.is_listening = False
            self.voice_btn.setStyleSheet("")
            self.voice_btn.setText("🎤 Voice Input")
            # Here you would stop recording and transcribe

    # --- Animations & Window States ---

    def toggleHistoryPanel(self):
        width = self.sidebar.width()
        self.anim = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self.anim.setDuration(300)
        self.anim.setStartValue(width)
        self.anim.setEndValue(250 if width == 0 else 0)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.anim.start()

    def toggleToolsStrip(self):
        self.tools_strip.setVisible(not self.tools_strip.isVisible())

    def changeEvent(self, event):
        # Handle minimize to widget
        if event.type() == QEvent.Type.WindowStateChange:
            if self.windowState() & Qt.WindowState.WindowMinimized:
                self.mini_widget.restore_geometry = self.geometry()
                self.mini_widget.move(self.x() + self.width() - 380, self.y() + 50) # Position nicely
                self.mini_widget.show()
                self.hide()
        super().changeEvent(event)
        
    def closeEvent(self, event):
        self.mini_widget.close()
        event.accept()

    def applyStyles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #202124; }
            QWidget#CentralContainer { background-color: #202124; color: #e8eaed; font-family: 'Segoe UI', sans-serif; }
            
            /* Top Bar */
            QWidget#TopControlBar { background-color: #292a2d; border-bottom: 1px solid #3c4043; }
            QLabel#WindowTitleLabel { color: #e8eaed; font-size: 16px; font-weight: bold; }
            QPushButton#TitleBarButton { background: transparent; color: white; border: none; font-size: 20px; }
            QPushButton#TitleBarButton:hover { background: #3c4043; border-radius: 20px; }

            /* Sidebar */
            QWidget#HistoryPanel { background-color: #292a2d; border-right: 1px solid #3c4043; }
            QListWidget { background: transparent; border: none; color: #bdc1c6; }
            QListWidget::item:selected { background: #3c4043; color: white; }
            
            QPushButton#ActionButton {
                background-color: #303134; color: #e8eaed; border: 1px solid #5f6368;
                padding: 10px; border-radius: 8px; font-weight: bold; margin-bottom: 5px;
            }
            QPushButton#ActionButton:hover { background-color: #3c4043; }

            /* Chat Area */
            QTextBrowser { background-color: transparent; border: none; font-size: 14px; }
            
            /* Input Area */
            QLineEdit {
                background-color: #303134; color: white; border: 1px solid #5f6368;
                border-radius: 20px; padding: 10px 15px; font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #8ab4f8; }
            
            QPushButton#SendButton {
                background-color: #8ab4f8; color: #202124; border-radius: 20px;
                padding: 5px 20px; font-weight: bold;
            }
            QPushButton#SendButton:hover { background-color: #aecbfa; }
            
            QPushButton#RoundButton {
                background-color: #303134; color: #e8eaed; border-radius: 20px;
                font-size: 20px; border: 1px solid #5f6368;
            }
            QPushButton#RoundButton:hover { background-color: #3c4043; }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatApp()
    window.show()
    sys.exit(app.exec())