import os
import shutil
from pathlib import Path
from typing import List, Any
from langchain_community.document_loaders import (
    PyPDFLoader, TextLoader, CSVLoader, PyMuPDFLoader,
    Docx2txtLoader, JSONLoader, WebBaseLoader
)
from langchain_community.document_loaders.excel import UnstructuredExcelLoader
from bs4 import BeautifulSoup

class DocumentManager:
    def __init__(self):
        self.base_storage_path = None
        self.current_project_path = None
        self.current_project_name = None

    def set_storage_location(self, path: str) -> bool:
        """Sets the root directory based on UI input."""
        if not os.path.exists(path):
            return False

        self.base_storage_path = os.path.join(path, "OpenbookLM-Projects")
        
        if not os.path.exists(self.base_storage_path):
            os.makedirs(self.base_storage_path)
            print(f"[SUCCESS] Created root folder at: {self.base_storage_path}")
        else:
            print(f"[INFO] Found existing root folder at: {self.base_storage_path}")
        
        return True

    def create_load_project(self, project_name: str) -> str:
        """Creates or loads a project subdirectory."""
        if not self.base_storage_path:
            raise ValueError("Base storage path not set.")

        self.current_project_name = project_name.strip()
        self.current_project_path = os.path.join(self.base_storage_path, self.current_project_name)

        if not os.path.exists(self.current_project_path):
            os.makedirs(self.current_project_path)
            print(f"[SUCCESS] Project '{project_name}' created at: {self.current_project_path}")
        else:
            print(f"[INFO] Opening existing project at: {self.current_project_path}")
        
        return self.current_project_path

    def add_files_to_project(self, file_paths: List[str]):
        """
        Copies files into the project directory.
        """
        if not self.current_project_path:
            raise ValueError("No project selected.")

        for file_path in file_paths:
            if os.path.isfile(file_path):
                file_name = os.path.basename(file_path)
                destination = os.path.join(self.current_project_path, file_name)
                try:
                    shutil.copy2(file_path, destination)
                    print(f"[SUCCESS] Added {file_name} to project.")
                except Exception as e:
                    print(f"[ERROR] Could not copy {file_name}: {e}")

    def get_project_files(self) -> List[str]:
        """Returns a list of filenames currently in the project folder."""
        if not self.current_project_path:
            return []
        return [f for f in os.listdir(self.current_project_path) if os.path.isfile(os.path.join(self.current_project_path, f))]


class DocumentLoader(DocumentManager):
    def __init__(self):
        super().__init__()
        self.documents = []
    
    def load_documents(self):
        """
        Reads all files inside the current created project dir.
        """
        if not self.current_project_path:
            print("[ERROR] No project directory set.")
            return

        self.documents = []
        path_obj = Path(self.current_project_path)
        
        loader_map = {
            ".pdf": PyMuPDFLoader,
            ".txt": TextLoader,
            ".csv": CSVLoader,
            ".docx": Docx2txtLoader,
            ".xlsx": UnstructuredExcelLoader,
            ".json": JSONLoader,
        }

        print(f"[INFO] Scanning directory: {self.current_project_path}")

        for ext, loader_class in loader_map.items():
            # glob matches recursively or just in the folder
            for file_path in path_obj.glob(f'*{ext}'): 
                print(f"[DEBUG] Loading {ext} file: {file_path.name}")
                try:
                    if ext == ".json":
                        loader = loader_class(str(file_path), jq_schema='.', text_content=False)
                    else:
                        loader = loader_class(str(file_path))
                    
                    loaded_docs = loader.load()
                    self.documents.extend(loaded_docs)
                except Exception as e:
                    print(f"[ERROR] Failed to load {file_path.name}: {e}")
        
        print(f"[SUMMARY] Total documents loaded: {len(self.documents)}")
        return self.documents
    
    # TODO: Function to load documents from Obsidian, Notion, etc -> MCP or Connectors 

class ExtractLink:
    # TODO: Implement diverse link extraction logic 
    pass

def url_extraction(url):
    """
    Extracts html text using WebBaseLoader
    """
    # TODO: Save the file content and metadata inside current created project dir in .txt format
    # TODO: Rename the files based on 'title' from metadata...if not title, then move to default
    # TODO: Take input for list of urls as input that is seperate by new line or comma(,) -> Implement this in UI
    loader = WebBaseLoader(url)
    loader.requests_kwargs = {'verify':False}
    docs = loader.load() 
    print(f"Document Content:\n{docs[0]}") 
    print(f"\nDocument Metadata:\n{docs[0].metadata}")

class ExtractText:
    # TODO: Copies user text and creates a .txt file to store the text 
    # Loads the document
    pass

class ExtractTables:
    # TODO: Load and work with csv or excel files
    pass