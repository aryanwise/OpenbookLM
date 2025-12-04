import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QListWidget, QListWidgetItem, QPushButton, 
    QLineEdit, QTextEdit, QFrame, QMenu, QInputDialog, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QSize, QPoint
from PyQt6.QtGui import QCursor, QAction

try:
    from frontend.styles import GLOBAL_STYLE, PROGRESS_BAR_STYLE
except ImportError:
    pass

from frontend.add_source_dialog import SourceUploadDialog

class WorkspaceWindow(QMainWindow):
    def __init__(self, project_name, backend_instance):
        super().__init__()
        self.project_name = project_name
        self.backend = backend_instance 
        
        self.setWindowTitle(f"{project_name}")
        self.resize(1400, 900)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Unified Theme
        self.setStyleSheet(GLOBAL_STYLE + """
            QMainWindow { background-color: transparent; }
            QWidget#CentralWidget { background-color: rgba(19, 19, 20, 245); }
            QFrame#LeftPanel { background-color: rgba(30, 31, 32, 180); border-right: 1px solid rgba(95, 99, 104, 150); }
        """ + PROGRESS_BAR_STYLE)

        self.init_ui()
        self.refresh_sources_list()

    def init_ui(self):
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- LEFT PANEL ---
        self.source_panel = QFrame()
        self.source_panel.setObjectName("LeftPanel")
        self.source_panel.setFixedWidth(320)
        
        left_layout = QVBoxLayout(self.source_panel)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(15)

        # Header
        top_header = QHBoxLayout()
        back_btn = QPushButton("←")
        back_btn.setFixedSize(30, 30)
        back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        back_btn.setStyleSheet("color: #e8eaed; border: 1px solid #5f6368; border-radius: 15px; background: transparent;")
        back_btn.clicked.connect(self.go_back)
        
        header_title = QLabel("Sources")
        header_title.setStyleSheet("color: #e8eaed; font-size: 18px; font-weight: bold; border: none; background: transparent;")
        
        top_header.addWidget(back_btn)
        top_header.addSpacing(10)
        top_header.addWidget(header_title)
        top_header.addStretch()
        left_layout.addLayout(top_header)

        # Add Source Btn
        self.add_btn = QPushButton("  + Add source")
        self.add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.add_btn.setFixedHeight(45)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #303134; color: #a8c7fa; 
                border-radius: 22px; text-align: left; padding-left: 20px; font-size: 14px; border: none;
            }
            QPushButton:hover { background-color: #3c4043; }
        """)
        self.add_btn.clicked.connect(self.open_add_dialog)
        left_layout.addWidget(self.add_btn)

        # Source List with Context Menu
        self.source_list = QListWidget()
        self.source_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.source_list.customContextMenuRequested.connect(self.show_source_context_menu)
        self.source_list.setStyleSheet("""
            QListWidget { border: none; background: transparent; outline: none; }
            QListWidget::item { color: #e8eaed; padding: 12px; border-radius: 8px; margin-bottom: 4px; }
            QListWidget::item:hover { background-color: rgba(255, 255, 255, 0.05); }
            QListWidget::item:selected { background-color: rgba(168, 199, 250, 0.15); color: #a8c7fa; }
        """)
        left_layout.addWidget(self.source_list)

        # Source Limit Footer
        footer_layout = QVBoxLayout()
        self.limit_lbl = QLabel("Source limit")
        self.limit_lbl.setStyleSheet("color: #bdc1c6; font-size: 12px; background: transparent;")
        self.limit_bar = QProgressBar()
        self.limit_bar.setMaximum(50)
        self.limit_bar.setTextVisible(False)
        self.limit_bar.setFixedHeight(6)
        
        footer_layout.addWidget(self.limit_lbl)
        footer_layout.addWidget(self.limit_bar)
        left_layout.addLayout(footer_layout)

        main_layout.addWidget(self.source_panel)

        # --- RIGHT PANEL (Chat) ---
        chat_panel = QFrame()
        chat_panel.setStyleSheet("background: transparent; border: none;")
        right_layout = QVBoxLayout(chat_panel)
        right_layout.setContentsMargins(50, 40, 50, 40)

        # Title
        chat_header = QLabel(self.project_name)
        chat_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chat_header.setStyleSheet("color: #e8eaed; font-size: 24px; font-weight: 500; background: transparent;")
        right_layout.addWidget(chat_header)

        # History
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setPlaceholderText("Start chatting with your sources...")
        self.chat_history.setStyleSheet("""
            QTextEdit { border: none; background: transparent; color: #bdc1c6; font-size: 16px; line-height: 1.5; }
        """)
        right_layout.addWidget(self.chat_history)

        # Input
        input_container = QFrame()
        input_container.setFixedHeight(60)
        input_container.setStyleSheet("background-color: #1e1f20; border-radius: 30px; border: 1px solid #3c4043;")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(20, 5, 10, 5)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type a question...")
        self.chat_input.setStyleSheet("background: transparent; border: none; color: white; font-size: 16px;")
        self.chat_input.returnPressed.connect(self.send_message)

        send_btn = QPushButton("➤")
        send_btn.setFixedSize(40, 40)
        send_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        send_btn.setStyleSheet("background-color: #e8eaed; color: black; border-radius: 20px; font-size: 16px; border: none;")
        send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(send_btn)

        right_layout.addWidget(input_container)
        main_layout.addWidget(chat_panel)

    # --- Logic ---

    def refresh_sources_list(self):
        self.source_list.clear()
        files = self.backend.get_project_files()
        
        for f in files:
            icon = "📄"
            if f.endswith(".pdf"): icon = "📕"
            elif f.endswith(".txt"): icon = "📝"
            elif "Web_" in f: icon = "🌐"
            
            item = QListWidgetItem(f"{icon}  {f}")
            item.setData(Qt.ItemDataRole.UserRole, f) # Store filename
            self.source_list.addItem(item)
            
        # Update Bar
        count = len(files)
        self.limit_bar.setValue(count)
        self.limit_lbl.setText(f"Source limit ({count}/50)")

    def show_source_context_menu(self, pos):
        item = self.source_list.itemAt(pos)
        if not item: return
        
        filename = item.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu()
        rename_action = QAction("Rename", self)
        delete_action = QAction("Delete", self)
        menu.addAction(rename_action)
        menu.addSeparator()
        menu.addAction(delete_action)
        
        action = menu.exec(self.source_list.mapToGlobal(pos))
        
        if action == delete_action:
            if QMessageBox.question(self, "Delete", f"Remove {filename}?") == QMessageBox.StandardButton.Yes:
                self.backend.delete_source_file(filename)
                self.refresh_sources_list()
        elif action == rename_action:
            new_name, ok = QInputDialog.getText(self, "Rename", "New Filename:", text=filename)
            if ok and new_name:
                self.backend.rename_source_file(filename, new_name)
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
        self.chat_history.append(f"\n<b>You:</b> {msg}")
        self.chat_input.clear()
        self.chat_history.append(f"<b>AI:</b> (Processing against {self.limit_bar.value()} sources...)")