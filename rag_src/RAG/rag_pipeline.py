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
        
        # 1. Create Hidden Dependency Folder
        self.dep_path = os.path.join(project_path, DEPENDENCY_DIR)
        if not os.path.exists(self.dep_path):
            os.makedirs(self.dep_path)

        # 2. Point components to this hidden folder
        self.db = DBManager(self.dep_path) # DB lives in dependency folder
        self.index_dir = os.path.join(self.dep_path, "vector_index") # Vector store too
        self.store = FaissVectorStore(persist_dir=self.index_dir)
        
        # LLM Settings
        self.ollama_url = "http://localhost:11434/api/chat"
        self.model = "phi3:3.8b" 

    def sync_project_files(self):
        """Scans ROOT folder for sources, ignores dependency folder."""
        valid_exts = {".pdf", ".txt", ".csv", ".docx", ".md"}
        
        # Get files ONLY from root project dir, avoiding the dependency folder
        all_files = []
        for f in os.listdir(self.project_path):
            full_path = os.path.join(self.project_path, f)
            # Skip directories (like project_dependency)
            if os.path.isdir(full_path): 
                continue
            if os.path.splitext(f)[1] in valid_exts:
                all_files.append(full_path)
        
        new_docs = []
        
        for file_path in all_files:
            filename = os.path.basename(file_path)
            current_hash = self.db.calculate_file_hash(file_path)
            stored_hash = self.db.get_file_hash(filename)
            
            if current_hash != stored_hash:
                print(f"[INDEXING] Processing: {filename}")
                try:
                    if file_path.endswith(".pdf"): loader = PyPDFLoader(file_path)
                    elif file_path.endswith(".txt"): loader = TextLoader(file_path)
                    else: continue
                    
                    loaded = loader.load()
                    for doc in loaded:
                        doc.metadata["source"] = filename
                        
                    new_docs.extend(loaded)
                    self.db.update_file_hash(filename, current_hash)
                except Exception as e:
                    print(f"[ERROR] Failed to load {filename}: {e}")

        if new_docs:
            self.store.add_documents(new_docs)
            return f"Indexed {len(new_docs)} new documents."
        return "Project up to date."

    def answer_query(self, query):
        self.db.add_chat_message("user", query)
        
        results = self.store.query(query, top_k=5)
        context_text = "\n\n".join([r['metadata'].get('text', '') for r in results])
        
        if not context_text:
            context_text = "No relevant context found in documents."

        system_msg = "You are a helpful assistant. Answer the query based ONLY on the provided context."
        user_msg = f"Context:\n{context_text}\n\nQuery: {query}"
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            "stream": False
        }
        
        try:
            response = requests.post(self.ollama_url, json=payload)
            response.raise_for_status()
            ai_text = response.json()["message"]["content"]
        except Exception as e:
            ai_text = f"Error generating response: {e}"

        self.db.add_chat_message("assistant", ai_text)
        return ai_text

    def get_history(self):
        return self.db.get_chat_history()