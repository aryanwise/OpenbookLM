import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextBrowser, QLineEdit, QPushButton, QComboBox, QToolButton,
    QMenu, QSizePolicy, QListWidget, QListWidgetItem, QLabel
)
from PyQt6.QtGui import QAction, QIcon, QPalette, QColor, QFont
from PyQt6.QtCore import Qt, QEvent, QRect, QPoint, QPropertyAnimation, QEasingCurve, QSize

# --- The Small Widget for "Teams-like Minimize" ---
# (This class is unchanged)
class MiniWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.restore_geometry = main_window.geometry()
        self.initUI()
        self.applyStyles()

    def initUI(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(360, 300)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        top_bar_layout.setSpacing(10)

        self.restore_button = QPushButton("💬")
        self.restore_button.setToolTip("Click to restore")
        self.restore_button.clicked.connect(self.restoreMainWindow)
        self.restore_button.setFixedSize(40, 40)
        self.restore_button.setObjectName("RestoreButton")
        top_bar_layout.addWidget(self.restore_button)

        self.llm_combo = QComboBox()
        self.llm_combo.addItems(["Gemini Pro", "GPT-4o", "Claude 3.5 Sonnet", "Llama 3"])
        self.llm_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        top_bar_layout.addWidget(self.llm_combo)
        
        self.tools_button = QToolButton()
        self.tools_button.setText("Tools")
        self.tools_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        
        self.tools_menu = QMenu(self)
        self.tools_button.setMenu(self.tools_menu)
        
        action_listen = QAction("🎧 Listening", self)
        action_read = QAction("📖 Reading", self)
        action_mcp = QAction("📋 MCP (Copy)", self)
        action_export = QAction("📤 Export Chat", self)
        
        self.tools_menu.addAction(action_listen)
        self.tools_menu.addAction(action_read)
        self.tools_menu.addAction(action_mcp)
        self.tools_menu.addAction(action_export)

        top_bar_layout.addWidget(self.tools_button)
        main_layout.addLayout(top_bar_layout)

        self.mini_chat_display = QTextBrowser()
        self.mini_chat_display.setReadOnly(True)
        self.mini_chat_display.setPlaceholderText("Chat history...")
        main_layout.addWidget(self.mini_chat_display, 1)

        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(5)

        self.mini_input_field = QLineEdit()
        self.mini_input_field.setPlaceholderText("Type here...")
        self.mini_input_field.returnPressed.connect(self.sendMessage)
        input_layout.addWidget(self.mini_input_field)

        self.mini_send_button = QPushButton("Send")
        self.mini_send_button.clicked.connect(self.sendMessage)
        self.mini_send_button.setObjectName("MiniSendButton")
        input_layout.addWidget(self.mini_send_button)

        main_layout.addLayout(input_layout)

    def applyStyles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 30, 0.9);
                border-radius: 10px;
                color: white;
                font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
            }
            QPushButton#RestoreButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 20px;
            }
            QPushButton#RestoreButton:hover { background-color: #0088f0; }
            QPushButton#MiniSendButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton#MiniSendButton:hover { background-color: #0088f0; }
            QComboBox, QToolButton {
                background-color: rgba(45, 45, 45, 0.9);
                border: 1px solid #555;
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
                color: white;
            }
            QComboBox QAbstractItemView {
                background-color: #333;
                border: 1px solid #555;
                selection-background-color: #0078d4;
                color: #f0f0f0;
                outline: 0px;
            }
            QMenu {
                background-color: #333;
                border: 1px solid #555;
                color: #f0f0f0;
                padding: 5px;
            }
            QMenu::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QTextBrowser {
                background-color: rgba(20, 20, 20, 0.85);
                border: 1px solid #444;
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
                color: #f0f0f0;
            }
            QLineEdit {
                background-color: rgba(45, 45, 45, 0.9);
                border: 1px solid #555;
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
                color: white;
            }
        """)

    def sendMessage(self):
        user_text = self.mini_input_field.text().strip()
        if user_text:
            self.main_window.addMessageToDisplay(user_text, "You")
            self.mini_input_field.clear()
            self.main_window.getBotResponse(user_text)

    def restoreMainWindow(self):
        self.main_window.show()
        self.main_window.setGeometry(self.restore_geometry)
        self.main_window.setWindowState(Qt.WindowState.WindowNoState)
        self.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragPos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.dragPos)
            event.accept()

# --- The Main Chat Application Window ---
class ChatApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # REMOVED Frameless and Translucent flags to restore native title bar
        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("Demo Frontend - OpenStudyLM")
        self.setGeometry(100, 100, 800, 900)
        self.setMinimumSize(500, 600)

        self.mini_widget = MiniWidget(self)
        self.last_geometry = self.geometry()
        self.dragPos = QPoint()
        
        self.chat_sessions = {}
        self.current_chat_id = None
        self.chat_counter = 0

        self.initUI()
        self.applyStyles()
        self.startNewChat()

    def initUI(self):
        central_widget_container = QWidget()
        central_widget_container.setObjectName("CentralContainer")
        self.setCentralWidget(central_widget_container)
        
        main_layout = QVBoxLayout(central_widget_container)
        main_layout.setContentsMargins(5, 5, 5, 5) # Updated margins
        main_layout.setSpacing(5) # Updated spacing

        # --- 1. Top Control Bar (Replaces Custom Title Bar) ---
        top_control_bar = QWidget()
        top_control_bar.setObjectName("TopControlBar")
        top_control_bar.setMinimumHeight(40)
        title_bar_layout = QHBoxLayout(top_control_bar)
        title_bar_layout.setContentsMargins(10, 0, 10, 0)
        title_bar_layout.setSpacing(10)

        # Hamburger Menu Button
        self.hamburger_button = QPushButton("☰")
        self.hamburger_button.setObjectName("TitleBarButton")
        self.hamburger_button.setFixedSize(35, 35)
        self.hamburger_button.setToolTip("Toggle Chat History")
        self.hamburger_button.clicked.connect(self.toggleHistoryPanel)
        title_bar_layout.addWidget(self.hamburger_button)

        # Title Label
        self.title_label = QLabel("OpenStudyLM")
        self.title_label.setObjectName("WindowTitleLabel")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft) # Align left now
        title_bar_layout.addWidget(self.title_label)

        title_bar_layout.addStretch()

        main_layout.addWidget(top_control_bar)

        # --- 2. Main Content Area ---
        main_content_layout = QHBoxLayout()
        main_content_layout.setSpacing(0)
        main_content_layout.setContentsMargins(0, 0, 0, 0)

        # --- 2a. History Panel (Sliding) ---
        self.history_panel = QWidget()
        self.history_panel.setObjectName("HistoryPanel")
        self.history_panel.setMaximumWidth(0) # Start hidden
        history_panel_layout = QVBoxLayout(self.history_panel)
        history_panel_layout.setContentsMargins(5, 10, 5, 10)
        
        # New Chat Button (Moved inside panel)
        self.new_chat_button = QPushButton("New Chat")
        self.new_chat_button.setObjectName("NewChatButton")
        self.new_chat_button.setMinimumHeight(40)
        self.new_chat_button.clicked.connect(self.startNewChat)
        history_panel_layout.addWidget(self.new_chat_button)
        
        self.history_list_widget = QListWidget()
        self.history_list_widget.itemClicked.connect(self.selectChatSession)
        history_panel_layout.addWidget(self.history_list_widget)
        
        main_content_layout.addWidget(self.history_panel)
        
        # --- 2b. Chat Area ---
        chat_area_widget = QWidget()
        chat_area_widget.setObjectName("ChatAreaWidget")
        chat_area_layout = QVBoxLayout(chat_area_widget)
        chat_area_layout.setContentsMargins(10, 10, 10, 10)
        chat_area_layout.setSpacing(10)
        
        self.chat_display = QTextBrowser()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText("Welcome! Start a new chat or select one from the history.")
        self.chat_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        chat_area_layout.addWidget(self.chat_display, 1)

        self.tools_strip = QWidget()
        self.tools_strip.setObjectName("ToolsStrip")
        self.tools_strip.setVisible(False)
        self.tools_strip.setMaximumHeight(0)
        
        tools_strip_layout = QHBoxLayout(self.tools_strip)
        tools_strip_layout.setContentsMargins(5, 5, 5, 5)
        tools_strip_layout.setSpacing(10)
        
        btn_listen = QPushButton("🎧 Listening")
        btn_read = QPushButton("📖 Reading")
        btn_mcp = QPushButton("📋 MCP (Copy)")
        btn_export = QPushButton("📤 Export Chat")
        
        tools_strip_layout.addWidget(btn_listen)
        tools_strip_layout.addWidget(btn_read)
        tools_strip_layout.addWidget(btn_mcp)
        tools_strip_layout.addWidget(btn_export)
        tools_strip_layout.addStretch()
        
        chat_area_layout.addWidget(self.tools_strip)

        bottom_controls_layout = QHBoxLayout()
        bottom_controls_layout.setSpacing(10)
        
        self.input_tools_button = QPushButton("+")
        self.input_tools_button.setToolTip("Show Tools")
        self.input_tools_button.setFixedSize(40, 40)
        self.input_tools_button.clicked.connect(self.toggleToolsStrip)
        self.input_tools_button.setObjectName("InputToolsButton")
        bottom_controls_layout.addWidget(self.input_tools_button)
        
        self.llm_combo = QComboBox()
        self.llm_combo.addItems(["Gemini Pro", "GPT-4o", "Claude 3.5 Sonnet", "Llama 3"])
        bottom_controls_layout.addWidget(self.llm_combo)
        
        bottom_controls_layout.addStretch()
        chat_area_layout.addLayout(bottom_controls_layout)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message here...")
        self.input_field.returnPressed.connect(self.sendMessage)
        self.input_field.setMinimumHeight(45)
        input_layout.addWidget(self.input_field)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.sendMessage)
        self.send_button.setObjectName("MainSendButton")
        self.send_button.setMinimumHeight(45)
        input_layout.addWidget(self.send_button)

        chat_area_layout.addLayout(input_layout)
        
        main_content_layout.addWidget(chat_area_widget, 1)
        main_layout.addLayout(main_content_layout, 1)

    # --- Chat History Functions ---

    def startNewChat(self):
        self.chat_counter += 1
        chat_id = f"chat_{self.chat_counter}"
        title = f"New Chat {self.chat_counter}"
        
        self.chat_sessions[chat_id] = {
            "title": title,
            "history": []
        }
        self.current_chat_id = chat_id
        
        item = QListWidgetItem(title)
        item.setData(Qt.ItemDataRole.UserRole, chat_id)
        self.history_list_widget.addItem(item)
        self.history_list_widget.setCurrentItem(item)
        
        self.chat_display.clear()
        self.chat_display.setPlaceholderText("Type a message to start...")

    def selectChatSession(self, item):
        chat_id = item.data(Qt.ItemDataRole.UserRole)
        if chat_id and chat_id != self.current_chat_id:
            self.current_chat_id = chat_id
            self.loadChatHistory(chat_id)

    def loadChatHistory(self, chat_id):
        self.chat_display.clear()
        session = self.chat_sessions.get(chat_id)
        if session:
            for entry in session["history"]:
                self.appendFormattedMessage(entry["text"], entry["sender"])
        
    def appendFormattedMessage(self, text, sender):
        if sender == "You":
            formatted_text = f"<b style='color:#0078d4;'>You:</b> {text}"
        else:
            formatted_text = f"<b style='color:#34a853;'>Bot:</b> {text}"
        
        self.chat_display.append(formatted_text)
        self.mini_widget.mini_chat_display.append(formatted_text)

    # --- End Chat History Functions ---

    def toggleHistoryPanel(self):
        is_visible = self.history_panel.width() > 0
        
        if hasattr(self, "history_animation"):
            self.history_animation.stop()

        self.history_animation = QPropertyAnimation(self.history_panel, b"maximumWidth")
        self.history_animation.setDuration(250)
        self.history_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        if is_visible:
            # Hide
            self.history_animation.setStartValue(240)
            self.history_animation.setEndValue(0)
        else:
            # Show
            self.history_animation.setStartValue(0)
            self.history_animation.setEndValue(240)
            
        self.history_animation.start()

    def toggleToolsStrip(self):
        is_visible = self.tools_strip.isVisible()
        
        if hasattr(self, "strip_animation"):
            self.strip_animation.stop()

        self.strip_animation = QPropertyAnimation(self.tools_strip, b"maximumHeight")
        target_height = 55
        
        if is_visible:
            self.strip_animation.setStartValue(target_height)
            self.strip_animation.setEndValue(0)
            self.strip_animation.finished.connect(lambda: self.tools_strip.setVisible(False))
        else:
            self.tools_strip.setVisible(True)
            self.strip_animation.setStartValue(0)
            self.strip_animation.setEndValue(target_height)
            
        self.strip_animation.setDuration(150)
        self.strip_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.strip_animation.start()


    def applyStyles(self):
        stylesheet = """
            QWidget#CentralContainer {
                background-color: rgba(40, 40, 40, 0.95); /* Made slightly less transparent */
                color: #f0f0f0;
                font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
                /* Removed border and radius for native window */
            }
            /* REMOVED QMainWindow background style */

            /* --- Top Control Bar (Replaces Custom Title Bar) --- */
            QWidget#TopControlBar {
                background-color: transparent;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            /* REMOVED macOS Window Controls */
            
            /* Title Label */
            QLabel#WindowTitleLabel {
                color: #f0f0f0;
                font-weight: bold;
                font-size: 16px;
            }
            
            /* Hamburger Button */
            QPushButton#TitleBarButton {
                background-color: transparent;
                color: #f0f0f0;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 20px;
            }
            QPushButton#TitleBarButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            
            /* --- History Panel --- */
            QWidget#HistoryPanel {
                background-color: rgba(25, 25, 25, 0.7);
                border-right: 1px solid rgba(255, 255, 255, 0.1);
                /* Removed border-bottom-left-radius */
            }
            
            /* New Chat Button inside History Panel */
            QPushButton#NewChatButton {
                background-color: rgba(255, 255, 255, 0.05);
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            }
            QPushButton#NewChatButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            
            QListWidget {
                background-color: transparent;
                border: none;
                color: #f0f0f0;
                font-size: 14px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 12px 10px;
                border-radius: 6px;
            }
            QListWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.05);
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            
            /* --- Chat Area --- */
            QWidget#ChatAreaWidget { background-color: transparent; }
            QTextBrowser {
                background-color: rgba(20, 20, 20, 0.7);
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 16px;
                color: #f0f0f0;
            }
            QLineEdit {
                background-color: rgba(50, 50, 50, 0.8);
                border: 1px solid #555;
                border-radius: 8px;
                padding: 10px;
                font-size: 15px;
                color: white;
            }
            QLineEdit:focus { border: 1px solid #0078d4; }

            /* Main Send Button */
            QPushButton#MainSendButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 15px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton#MainSendButton:hover { background-color: #0088f0; }
            QPushButton#MainSendButton:pressed { background-color: #006ac1; }
            
            /* '+' Tools Button */
            QPushButton#InputToolsButton {
                background-color: rgba(50, 50, 50, 0.8);
                color: #f0f0f0;
                border: 1px solid #555;
                border-radius: 20px;
                padding: 0px;
                font-weight: bold;
                font-size: 24px;
            }
            QPushButton#InputToolsButton:hover {
                background-color: rgba(65, 65, 65, 0.9);
                border-color: #777;
            }
            QPushButton#InputToolsButton:pressed { background-color: #0078d4; }

            /* --- Tool Strip --- */
            QWidget#ToolsStrip { background-color: transparent; }
            QWidget#ToolsStrip QPushButton {
                background-color: rgba(50, 50, 50, 0.8);
                color: #f0f0f0;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: normal;
                font-size: 14px;
                text-align: left;
            }
            QWidget#ToolsStrip QPushButton:hover {
                background-color: #0078d4;
                border-color: #0078d4;
            }

            /* --- LLM ComboBox --- */
            QComboBox {
                background-color: rgba(50, 50, 50, 0.8);
                border: 1px solid #555;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                color: white;
                min-height: 20px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #333;
                border: 1px solid #555;
                selection-background-color: #0078d4;
                color: #f0f0f0;
                outline: 0px;
            }
            
            /* Scrollbar styling */
            QScrollBar:vertical {
                border: none;
                background: rgba(0, 0, 0, 0.2);
                width: 10px;
                margin: 0px 0px 0px 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #555;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """
        self.setStyleSheet(stylesheet)

    # --- Window Dragging and Control Functions ---

    def toggleMaximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
            # We don't change text anymore

    # REMOVED mousePressEvent
    # REMOVED mouseMoveEvent
    # REMOVED mouseReleaseEvent
        
    # --- End Window Functions ---

    def addMessageToDisplay(self, text, sender):
        self.appendFormattedMessage(text, sender)
        if self.current_chat_id:
            session = self.chat_sessions.get(self.current_chat_id)
            if session:
                session["history"].append({"sender": sender, "text": text})

    def getBotResponse(self, user_text):
        # TODO: Add logic here to call an LLM API
        self.addMessageToDisplay("AI under development...", "Bot")

    def sendMessage(self):
        user_text = self.input_field.text().strip()
        if user_text:
            self.addMessageToDisplay(user_text, "You")
            self.input_field.clear()
            self.getBotResponse(user_text)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            if self.windowState() & Qt.WindowState.WindowMinimized:
                self.last_geometry = self.geometry()
                self.mini_widget.restore_geometry = self.last_geometry
                
                screen = QApplication.primaryScreen().availableGeometry()
                widget_pos = QPoint(
                    screen.width() - self.mini_widget.width() - 20,
                    screen.height() - self.mini_widget.height() - 20
                )
                self.mini_widget.move(widget_pos)
                
                self.mini_widget.show()
                self.hide()
                event.ignore()
                return
        super().changeEvent(event)

    def moveEvent(self, event):
        if not self.isMinimized() and not self.isMaximized():
            self.last_geometry = self.geometry()
        super().moveEvent(event)
        
    def resizeEvent(self, event):
        if self.isMaximized():
            pass
        elif not self.isMinimized():
            self.last_geometry = self.geometry()
        super().resizeEvent(event)
        
    def showNormal(self):
        self.setGeometry(self.last_geometry)
        super().showNormal()

    def closeEvent(self, event):
        self.mini_widget.close()
        event.accept()


# --- Main execution ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Inter")
    font.setPointSize(10)
    app.setFont(font)
    
    window = ChatApp()
    window.show()
    sys.exit(app.exec())