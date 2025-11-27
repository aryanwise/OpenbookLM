import os
from pathlib import Path
from typing import List, Any
from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader, PyMuPDFLoader
from langchain_community.document_loaders import Docx2txtLoader
from langchain_community.document_loaders.excel import UnstructuredExcelLoader
from langchain_community.document_loaders import JSONLoader

class DocumentLoader:

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir).resolve()
        print(f"[DEBUG] Data path: {self.data_dir}")
        self._load_documents()
        self.base_storage_path = None

    def _load_documents(self):
        self.documents = []
        # Mapping from file extensions to their respective loaders
        loader_map = {
            ".pdf": PyMuPDFLoader,
            ".txt": TextLoader,
            ".csv": CSVLoader,
            ".docx": Docx2txtLoader,
            ".xlsx": UnstructuredExcelLoader,
            ".json": JSONLoader, # Assuming a simple JSONLoader, adjust if specific schema is needed
        }

        for ext, loader_class in loader_map.items():
            for file_path in self.data_dir.glob(f'**/*{ext}'):
                print(f"[DEBUG] Loading {ext} file: {file_path}")
                try:
                    # For JSONLoader, you might need to specify jq_schema, e.g., JSONLoader(file_path, jq_schema='.', text_content=False)
                    # For now, assuming a generic initialization.
                    if ext == ".json":
                        loader = loader_class(str(file_path), jq_schema='.', text_content=False)
                    else:
                        loader = loader_class(str(file_path))
                    
                    loaded_docs = loader.load()
                    print(f"[DEBUG] Loaded {len(loaded_docs)} documents from {file_path}")
                    self.documents.extend(loaded_docs)
                except Exception as e:
                    print(f"[ERROR] Failed to load {file_path}: {e}")
        if not self.documents:
            print("[WARNING] No documents were loaded. Please check the 'data' directory and file types.")
                    
    def set_storage_location(self):
        """
        Sets the root directory for the application (e.g., User/Documents/OpenbookLM).
        """
        print("Please enter the system path where you want to save the 'OpenbookLM' folder.")
        print("(Example: C:/Users/Name/Documents or /home/user/docs)")
        
        user_input = str(input("Enter data location:\n> ")).strip()
        
        # Validate path
        if not os.path.exists(user_input):
            print(f"[ERROR] The path '{user_input}' does not exist on this system.")
            return False

        # Create the main OpenbookLM directory
        self.base_storage_path = os.path.join(user_input, "OpenbookLM-Projects")
        
        if not os.path.exists(self.base_storage_path):
            os.makedirs(self.base_storage_path)
            print(f"[SUCCESS] Created root folder at: {self.base_storage_path}")
        else:
            print(f"[INFO] Found existing root folder at: {self.base_storage_path}")
        
        return True


    def create_project(self):
        """
        Creates a project subdirectory inside the OpenbookLM-Projects folder.
        """
        # Ensure base location is set before creating a project
        if not self.base_storage_path:
            success = self.set_storage_location()
            if not success:
                return

        print("\nPlease enter your project name (e.g., 'Maths', 'Physics'):")
        project_name = str(input("Project Name:\n> ")).strip()
        
        # Build the full project path
        project_path = os.path.join(self.base_storage_path, project_name)

        if not os.path.exists(project_path):
            os.makedirs(project_path)
            print(f"[SUCCESS] Project '{project_name}' created at: {project_path}")
        else:
            print(f"[INFO] Opening existing project at: {project_path}")

        # Update the main data_dir to point to this specific project
        # self.data_dir = Path(project_path)
        # print(f"[READY] Active project directory set to: {self.data_dir}")
