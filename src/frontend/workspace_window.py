import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QListWidget, QListWidgetItem, QPushButton, 
    QLineEdit, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QCursor

from frontend.add_source_dialog import SourceUploadDialog

class WorkspaceWindow(QMainWindow):
    def __init__(self, project_name, backend_instance):
        super().__init__()
        self.project_name = project_name
        self.backend = backend_instance 
        
        self.setWindowTitle(f"{project_name} - OpenbookLM")
        self.resize(1400, 900)
        self.setStyleSheet("background-color: #131314;") 

        self.init_ui()
        self.refresh_sources_list()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- LEFT PANEL: Sources ---
        self.source_panel = QFrame()
        self.source_panel.setFixedWidth(350)
        self.source_panel.setStyleSheet("background-color: #1e1f20; border-right: 1px solid #3c4043;")
        
        left_layout = QVBoxLayout(self.source_panel)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(15)

        # --- 1. NEW: Back Button Header ---
        top_header_layout = QHBoxLayout()
        
        back_btn = QPushButton("←")
        back_btn.setFixedSize(30, 30)
        back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        back_btn.setStyleSheet("color: white; font-weight: bold; border: 1px solid #3c4043; border-radius: 15px;")
        back_btn.clicked.connect(self.go_back_to_dashboard) # Connect action
        
        header_title = QLabel("Sources")
        header_title.setStyleSheet("color: white; font-size: 18px; font-weight: bold; border: none;")
        
        top_header_layout.addWidget(back_btn)
        top_header_layout.addSpacing(10)
        top_header_layout.addWidget(header_title)
        top_header_layout.addStretch()
        
        left_layout.addLayout(top_header_layout)
        # -----------------------------------

        # Add Source Button
        self.add_btn = QPushButton("  + Add source")
        self.add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.add_btn.setFixedHeight(45)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #303134; color: #a8c7fa; 
                border-radius: 22px; text-align: left; padding-left: 20px; font-size: 14px;
            }
            QPushButton:hover { background-color: #3c4043; }
        """)
        self.add_btn.clicked.connect(self.open_add_source_dialog)
        left_layout.addWidget(self.add_btn)

        # Source List
        self.source_list = QListWidget()
        self.source_list.setStyleSheet("""
            QListWidget { border: none; background: transparent; }
            QListWidget::item { color: #e8eaed; padding: 10px; border-radius: 8px; margin-bottom: 5px; }
            QListWidget::item:hover { background-color: #303134; }
        """)
        left_layout.addWidget(self.source_list)
        
        main_layout.addWidget(self.source_panel)

        # --- RIGHT PANEL: Chat ---
        chat_panel = QFrame()
        chat_panel.setStyleSheet("background-color: #131314; border: none;")
        right_layout = QVBoxLayout(chat_panel)
        right_layout.setContentsMargins(50, 40, 50, 40)

        # Chat Title
        chat_title = QLabel(f"{self.project_name}")
        chat_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chat_title.setStyleSheet("color: #e8eaed; font-size: 20px; font-weight: 500;")
        right_layout.addWidget(chat_title)

        # Chat History
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setPlaceholderText("OpenbookLM can answer questions about your sources...")
        self.chat_history.setStyleSheet("""
            QTextEdit { border: none; background: transparent; color: #bdc1c6; font-size: 16px; }
        """)
        right_layout.addWidget(self.chat_history)

        # Input Area
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
        send_btn.setStyleSheet("background-color: white; color: black; border-radius: 20px; font-size: 16px;")
        send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(send_btn)

        right_layout.addWidget(input_container)
        
        main_layout.addWidget(chat_panel)

    # --- Logic ---

    def refresh_sources_list(self):
        """Fetches files from backend and populates list."""
        self.source_list.clear()
        files = self.backend.get_project_files()
        
        for f in files:
            # Simple icon logic based on extension
            icon = "📄"
            if f.endswith(".pdf"): icon = "📕"
            elif f.endswith(".txt"): icon = "📝"
            
            item = QListWidgetItem(f"{icon}  {f}")
            self.source_list.addItem(item)

    def open_add_source_dialog(self):
        self.dialog = SourceUploadDialog(self.backend, self)
        self.dialog.sources_added.connect(self.refresh_sources_list)
        self.dialog.exec()

    def go_back_to_dashboard(self):
        """Closes workspace and re-opens the main dashboard."""
        from frontend.main_window import MainWindow # Lazy import to avoid circular dependency
        self.dashboard = MainWindow()
        self.dashboard.show()
        self.close()

    def send_message(self):
        msg = self.chat_input.text().strip()
        if not msg: return
        
        self.chat_history.append(f"\n<b>You:</b> {msg}")
        self.chat_input.clear()
        self.chat_history.append(f"<b>AI:</b> (Processing...)")