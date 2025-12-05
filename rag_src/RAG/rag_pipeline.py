import os
from data_loader import DocumentLoader
from vectorstore import FaissVectorStore
from db_manager import DBManager
from langchain_community.document_loaders import PyPDFLoader, TextLoader, WebBaseLoader
import requests # Using direct API for speed/simplicity

class RAGPipeline:
    def __init__(self, project_path):
        self.project_path = project_path
        self.db = DBManager(project_path)
        
        # Vector Store
        self.index_dir = os.path.join(project_path, "vector_index")
        self.store = FaissVectorStore(persist_dir=self.index_dir)
        
        # LLM Settings
        self.ollama_url = "http://localhost:11434/api/chat"
        self.model = "phi3:3.8b" # Or "gemma2:2b", etc.

    def sync_project_files(self):
        """Scans folder, finds new files, embeds them, and updates DB."""
        valid_exts = {".pdf", ".txt", ".csv", ".docx", ".md"}
        all_files = [
            os.path.join(self.project_path, f) 
            for f in os.listdir(self.project_path) 
            if os.path.splitext(f)[1] in valid_exts
        ]
        
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
                    # Add source metadata just in case
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
        """Full RAG Flow: Search -> Prompt -> LLM -> History"""
        # 1. Save User Message
        self.db.add_chat_message("user", query)
        
        # 2. Retrieve Context
        results = self.store.query(query, top_k=5)
        context_text = "\n\n".join([r['metadata'].get('text', '') for r in results])
        
        if not context_text:
            context_text = "No relevant context found in documents."

        # 3. Construct Prompt
        system_msg = "You are a helpful assistant. Answer the query based ONLY on the provided context. If the answer is not in the context, say you don't know."
        user_msg = f"Context:\n{context_text}\n\nQuery: {query}"
        
        # 4. Call Ollama
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

        # 5. Save AI Message
        self.db.add_chat_message("assistant", ai_text)
        
        return ai_text

    def get_history(self):
        return self.db.get_chat_history()