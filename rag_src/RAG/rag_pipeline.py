import os
from data_loader import DocumentLoader
from vectorstore import FaissVectorStore
from db_manager import DBManager
from langchain_community.document_loaders import PyPDFLoader, TextLoader
import requests 

DEPENDENCY_DIR = "project_dependency"

class RAGPipeline:
    def __init__(self, project_path):
        self.project_path = project_path
        
        # 1. Setup Paths (Fast)
        self.dep_path = os.path.join(project_path, DEPENDENCY_DIR)
        if not os.path.exists(self.dep_path):
            os.makedirs(self.dep_path)

        # 2. Connect DB (Fast - SQLite is lazy)
        self.db = DBManager(self.dep_path) 
        
        # 3. Setup Vector Store Paths (Fast - DO NOT LOAD INDEX YET)
        self.index_dir = os.path.join(self.dep_path, "vector_index")
        
        # Optimization: We pass 'lazy_load=True' (we need to add this support to VectorStore)
        # OR we just initialize the class but don't load vectors until needed.
        self.store = FaissVectorStore(persist_dir=self.index_dir, lazy=True)
        
        self.ollama_url = "http://localhost:11434/api/chat"
        self.model = "phi3:3.8b" 

    def sync_project_files(self):
        """Now ensures index is loaded before adding."""
        # Ensure index is loaded before we try to add to it
        self.store.ensure_index_loaded()
        
        valid_exts = {".pdf", ".txt", ".csv", ".docx", ".md"}
        all_files = []
        for f in os.listdir(self.project_path):
            full_path = os.path.join(self.project_path, f)
            if os.path.isdir(full_path): continue
            if os.path.splitext(f)[1] in valid_exts:
                all_files.append(full_path)
        
        new_docs = []
        for file_path in all_files:
            filename = os.path.basename(file_path)
            
            # Smart Check (Timestamp)
            current_mtime = os.path.getmtime(file_path)
            stored_hash, stored_mtime = self.db.get_file_metadata(filename)
            
            if stored_mtime and abs(current_mtime - stored_mtime) < 1.0:
                continue 

            print(f"[INDEXING] Scanning: {filename}")
            current_hash = self.db.calculate_file_hash(file_path)
            
            if current_hash != stored_hash:
                try:
                    if file_path.endswith(".pdf"): loader = PyPDFLoader(file_path)
                    elif file_path.endswith(".txt"): loader = TextLoader(file_path)
                    else: continue
                    
                    loaded = loader.load()
                    for doc in loaded: doc.metadata["source"] = filename
                    new_docs.extend(loaded)
                    self.db.update_file_registry(filename, current_hash, current_mtime)
                except Exception as e:
                    print(f"[ERROR] {filename}: {e}")

        if new_docs:
            self.store.add_documents(new_docs)
            return f"Indexed {len(new_docs)} new documents."
        return "Project up to date."

    def answer_query(self, query):
        # Ensure index is loaded before query
        self.store.ensure_index_loaded()
        
        self.db.add_chat_message("user", query)
        results = self.store.query(query, top_k=5)
        context_text = "\n\n".join([r['metadata'].get('text', '') for r in results])
        
        if not context_text: context_text = "No relevant context found."

        system_msg = "You are a helpful assistant. Answer based ONLY on context."
        user_msg = f"Context:\n{context_text}\n\nQuery: {query}"
        
        try:
            response = requests.post(self.ollama_url, json={
                "model": self.model,
                "messages": [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
                "stream": False
            })
            response.raise_for_status()
            ai_text = response.json()["message"]["content"]
        except Exception as e:
            ai_text = f"Error: {e}"

        self.db.add_chat_message("assistant", ai_text)
        return ai_text

    def get_history(self):
        return self.db.get_chat_history()