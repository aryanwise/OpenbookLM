import os
import shutil
import json
import re
from pathlib import Path
from typing import List, Any
from langchain_community.document_loaders import (
    PyPDFLoader, TextLoader, CSVLoader, PyMuPDFLoader,
    Docx2txtLoader, JSONLoader, WebBaseLoader
)
from langchain_community.document_loaders.excel import UnstructuredExcelLoader
from bs4 import BeautifulSoup
import textwrap

CONFIG_FILE = "config.json"

class DocumentManager:
    def __init__(self):
        self.base_storage_path = None
        self.current_project_path = None
        self.current_project_name = None
        self.load_config()

    def load_config(self):
        """Checks if a root path was previously saved."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.base_storage_path = data.get("root_path")
                    if self.base_storage_path and not os.path.exists(self.base_storage_path):
                        # Handle case where folder was deleted manually
                        self.base_storage_path = None
            except Exception as e:
                print(f"[ERROR] Could not load config: {e}")

    def save_config(self):
        """Saves the current root path to a file."""
        if self.base_storage_path:
            try:
                with open(CONFIG_FILE, 'w') as f:
                    json.dump({"root_path": self.base_storage_path}, f)
            except Exception as e:
                print(f"[ERROR] Could not save config: {e}")

    def set_storage_location(self, path: str) -> bool:
        """Sets the root directory and saves it for future use."""
        if not os.path.exists(path): return False
        self.base_storage_path = os.path.join(path, "OpenbookLM-Projects")
        if not os.path.exists(self.base_storage_path):
            os.makedirs(self.base_storage_path)
        self.save_config()
        return True
    
    def create_load_project(self, project_name: str) -> str:
        """Creates or loads a project subdirectory inside the established root."""
        if not self.base_storage_path:
            raise ValueError("Root storage path not set.")
        self.current_project_name = project_name.strip()
        self.current_project_path = os.path.join(self.base_storage_path, self.current_project_name)
        if not os.path.exists(self.current_project_path):
            os.makedirs(self.current_project_path)
        return self.current_project_path

    def add_files_to_project(self, file_paths: List[str]):
        """
        Copies files into the project directory.
        """
        if not self.current_project_path: return
        for file_path in file_paths:
            if os.path.isfile(file_path):
                dest = os.path.join(self.current_project_path, os.path.basename(file_path))
                try: shutil.copy2(file_path, dest)
                except: pass  
                    
    def save_text_to_project(self, text_content: str, file_name: str):
        """
        Saves given text content to a .txt file in the current project directory.
        """
        if not self.current_project_path: return False
        
        # Sanitize filename
        safe_name = re.sub(r'[\\/*?:"<>|]', "", file_name)
        if not safe_name.endswith(".txt"): safe_name += ".txt"
        
        try:
            with open(os.path.join(self.current_project_path, safe_name), "w", encoding="utf-8") as f:
                f.write(text_content)
            return True
        except Exception as e:
            print(f"Error saving text: {e}")
            return False

    def get_project_files(self) -> List[str]:
        """Returns a list of filenames currently in the project folder."""
        if not self.current_project_path: return []
        return [f for f in os.listdir(self.current_project_path) 
                if os.path.isfile(os.path.join(self.current_project_path, f))]

    def delete_project(self, project_name: str):
        if not self.base_storage_path: return
        path = os.path.join(self.base_storage_path, project_name)
        if os.path.exists(path):
            shutil.rmtree(path) # CAUTION: Deletes folder and contents
            print(f"Deleted project: {project_name}")

    def rename_project(self, old_name: str, new_name: str):
        if not self.base_storage_path: return
        old_path = os.path.join(self.base_storage_path, old_name)
        new_path = os.path.join(self.base_storage_path, new_name)
        if os.path.exists(old_path) and not os.path.exists(new_path):
            os.rename(old_path, new_path)

    def delete_source_file(self, filename: str):
        if not self.current_project_path: return
        path = os.path.join(self.current_project_path, filename)
        if os.path.exists(path):
            os.remove(path)

    def rename_source_file(self, old_name: str, new_name: str):
        if not self.current_project_path: return
        old_path = os.path.join(self.current_project_path, old_name)
        # Ensure extension is kept or handled
        if "." in old_name and "." not in new_name:
            ext = old_name.split(".")[-1]
            new_name = f"{new_name}.{ext}"
            
        new_path = os.path.join(self.current_project_path, new_name)
        if os.path.exists(old_path):
            os.rename(old_path, new_path)


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
            return []

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
    
    def process_and_save_link(self, url: str):
        """Extracts content from URL and saves it to the project."""
        try:
            loader = WebBaseLoader(url)
            loader.requests_kwargs = {'verify': False}
            docs = loader.load()
            
            if not docs: return False
            
            # Use page title or URL as filename
            title = docs[0].metadata.get('title', 'website_content')
            if not title: title = url.split("//")[-1].split("/")[0]
            
            content = "\n\n".join([d.page_content for d in docs])
            content = f"Source: {url}\n\n{content}"
            
            return self.save_text_to_project(content, title)
        except Exception as e:
            print(f"Link processing error: {e}")
            return False
    
    # TODO: Function to load documents from Obsidian, Notion, etc -> MCP or Connectors 


class ExtractLink:
    # TODO: Implement diverse link extraction logic 
    def url_extraction(self, url):
        """
        Extracts html text using WebBaseLoader
        """
        # TODO: Save the file content and metadata inside current created project dir in .txt format
        # TODO: Rename the files based on 'title' from metadata...if not title, then move to default
        # TODO: Take list of urls as input that is seperated by new line or comma(,) -> Implement this in UI
        try:
            loader = WebBaseLoader(url)
            loader.requests_kwargs = {'verify': False}
            docs = loader.load()
            return docs  # Returns a list of Document objects
        except Exception as e:
            print(f"Error extracting link: {e}")
            return None

class ExtractText:
    # TODO: Copies user text and creates a .txt file to store the text 
    # Loads the document
    def extract_text(self, text: str):
        # Extract multi line text from user input and prints it     
        wrapped_text = textwrap.fill(text, width=100)
        return wrapped_text

class ExtractTables:
    # TODO: Load and work with csv or excel files
    pass 