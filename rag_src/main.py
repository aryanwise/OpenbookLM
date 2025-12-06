import sys
import os

def main():
    # 1. Setup Paths
    # Get the directory where main.py is located
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add 'rag_src' to python path so 'import frontend' works
    src_path = os.path.join(base_dir, 'rag_src')
    if src_path not in sys.path:
        sys.path.append(src_path)

    # Add 'RAG' folder to path for backend logic
    rag_path = os.path.join(base_dir, 'RAG')
    if rag_path not in sys.path:
        sys.path.append(rag_path)

    # 2. Launch App
    from PyQt6.QtWidgets import QApplication
    from frontend.main_window import MainWindow

    app = QApplication(sys.argv)
    
    # Optional: Set global app icon here
    # app.setWindowIcon(...)
    
    window = MainWindow()
    window.show()
    
    print("🚀 OpenbookLM (Local) Started...")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()