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

    def _load_documents(self):
        # Document loading
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
                    
        

