import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_loader import DocumentLoader, DocumentManager 

if __name__ == "__main__":
    data_manager = DocumentManager()
    data_loader = DocumentLoader()
    try:
        data_manager.set_storage_location()
        data_manager.create_project()
    except Exception as e:
        print(f"Error: {e}")