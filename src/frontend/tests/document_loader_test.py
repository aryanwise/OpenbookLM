import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QFileDialog, QListWidget, QTextEdit, QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt
# import data loader 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'RAG')))
from data_loader import DocumentLoader

class FileDropList(QListWidget):
    """Custom ListWidget to handle Drag and Drop of files."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.main_window = None 

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        # CRITICAL FIX: You must accept the move event, 
        # otherwise the cursor remains a "prohibited" sign.
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            
            # Extract local file paths
            files = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    files.append(str(url.toLocalFile()))
            
            if self.main_window:
                self.main_window.process_dropped_files(files)
        else:
            event.ignore()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.backend = DocumentLoader()
        self.setWindowTitle("OpenbookLM Data Loader")
        self.resize(800, 600)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Section 1: Storage Configuration ---
        config_group = QGroupBox("1. Configuration")
        config_layout = QVBoxLayout()
        
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select Root Storage Location...")
        self.path_input.setReadOnly(True)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_folder)
        
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_btn)
        
        project_layout = QHBoxLayout()
        self.project_input = QLineEdit()
        self.project_input.setPlaceholderText("Enter Project Name (e.g., Physics)")
        create_proj_btn = QPushButton("Create/Load Project")
        create_proj_btn.clicked.connect(self.setup_project)

        project_layout.addWidget(self.project_input)
        project_layout.addWidget(create_proj_btn)

        config_layout.addLayout(path_layout)
        config_layout.addLayout(project_layout)
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)

        # --- Section 2: File Management (Drag & Drop) ---
        file_group = QGroupBox("2. Project Files (Drag & Drop Here)")
        file_layout = QVBoxLayout()
        
        self.file_list = FileDropList()
        self.file_list.main_window = self # Link back to controller
        
        btn_layout = QHBoxLayout()
        add_file_btn = QPushButton("Add Files via Dialog")
        add_file_btn.clicked.connect(self.open_file_dialog)
        load_docs_btn = QPushButton("3. Process/Load Documents")
        load_docs_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        load_docs_btn.clicked.connect(self.run_loader)

        btn_layout.addWidget(add_file_btn)
        btn_layout.addWidget(load_docs_btn)

        file_layout.addWidget(self.file_list)
        file_layout.addLayout(btn_layout)
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)

        # --- Section 3: Logs ---
        log_group = QGroupBox("Logs")
        log_layout = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        # Initial State
        self.toggle_project_controls(False)

    def log(self, message):
        self.log_output.append(message)

    def toggle_project_controls(self, enable):
        self.file_list.setEnabled(enable)
        # We assume controls are disabled until a project is successfully created/loaded

    # --- Handlers ---

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Root Storage Folder")
        if folder:
            self.path_input.setText(folder)
            success = self.backend.set_storage_location(folder)
            if success:
                self.log(f"Storage set to: {folder}")
            else:
                self.log("Error setting storage path.")

    def setup_project(self):
        base_path = self.path_input.text()
        proj_name = self.project_input.text()
        
        if not base_path or not proj_name:
            QMessageBox.warning(self, "Input Error", "Please set storage path and project name.")
            return

        try:
            # Ensure base path is set in backend
            self.backend.set_storage_location(base_path)
            path = self.backend.create_load_project(proj_name)
            self.log(f"Project active at: {path}")
            self.toggle_project_controls(True)
            self.refresh_file_list()
        except Exception as e:
            self.log(f"Error creating project: {e}")

    def process_dropped_files(self, file_paths):
        if not self.backend.current_project_path:
            QMessageBox.warning(self, "Error", "Please create/load a project first.")
            return
        
        self.backend.add_files_to_project(file_paths)
        self.log(f"Added {len(file_paths)} files via Drag & Drop.")
        self.refresh_file_list()

    def open_file_dialog(self):
        if not self.backend.current_project_path:
            QMessageBox.warning(self, "Error", "Please create/load a project first.")
            return

        files, _ = QFileDialog.getOpenFileNames(self, "Select Documents")
        if files:
            self.backend.add_files_to_project(files)
            self.log(f"Added {len(files)} files via Dialog.")
            self.refresh_file_list()

    def refresh_file_list(self):
        self.file_list.clear()
        files = self.backend.get_project_files()
        self.file_list.addItems(files)

    def run_loader(self):
        if not self.backend.current_project_path:
            return
        
        self.log("--- Starting Document Loading ---")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            docs = self.backend.load_documents()
            self.log(f"Process Complete. Loaded {len(docs)} document chunks.")
        except Exception as e:
            self.log(f"Critical Error during loading: {e}")
        finally:
            QApplication.restoreOverrideCursor()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())