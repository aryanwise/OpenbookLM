import os
import faiss
import numpy as np
import pickle
from typing import List, Any
from sentence_transformers import SentenceTransformer
from embedding import EmbeddingPipeline

class FaissVectorStore:
    def __init__(self, persist_dir: str, embedding_model: str = "all-MiniLM-L6-v2", lazy=False):
        self.persist_dir = persist_dir
        self.embedding_model = embedding_model
        
        self.faiss_path = os.path.join(self.persist_dir, "faiss.index")
        self.meta_path = os.path.join(self.persist_dir, "metadata.pkl")
        
        self.index = None
        self.metadata = []
        self.model = SentenceTransformer(embedding_model)
        
        self.is_loaded = False
        
        # If NOT lazy, load immediately (old behavior)
        # If lazy, we wait.
        if not lazy:
            self.ensure_index_loaded()

    def ensure_index_loaded(self):
        """Loads index from disk if not already loaded."""
        if self.is_loaded:
            return

        if os.path.exists(self.faiss_path) and os.path.exists(self.meta_path):
            print(f"[INFO] Loading FAISS index from disk...")
            self.index = faiss.read_index(self.faiss_path)
            with open(self.meta_path, "rb") as f:
                self.metadata = pickle.load(f)
            print(f"[INFO] Loaded {self.index.ntotal} vectors.")
        else:
            print(f"[INFO] Initializing new FAISS index.")
            self.index = faiss.IndexFlatL2(384)
            self.metadata = []
        
        self.is_loaded = True

    def add_documents(self, documents: List[Any]):
        self.ensure_index_loaded()
        if not documents: return

        print(f"[INFO] Embedding {len(documents)} documents...")
        emb_pipe = EmbeddingPipeline(model_name=self.embedding_model)
        chunks = emb_pipe.chunk_documents(documents)
        if not chunks: return

        embeddings = emb_pipe.embed_chunks(chunks)
        vector_data = np.array(embeddings).astype('float32')
        self.index.add(vector_data)
        
        new_metadatas = [{"text": c.page_content, "source": c.metadata.get("source", "unknown")} for c in chunks]
        self.metadata.extend(new_metadatas)
        
        self.save()

    def save(self):
        if not os.path.exists(self.persist_dir):
            os.makedirs(self.persist_dir)
        faiss.write_index(self.index, self.faiss_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.metadata, f)

    def query(self, query_text: str, top_k: int = 5):
        self.ensure_index_loaded()
        if not self.index or self.index.ntotal == 0:
            return []
            
        query_emb = self.model.encode([query_text]).astype('float32')
        D, I = self.index.search(query_emb, top_k)
        
        results = []
        for idx, dist in zip(I[0], D[0]):
            if idx < len(self.metadata) and idx >= 0:
                results.append({"metadata": self.metadata[idx], "distance": float(dist)})
        return results