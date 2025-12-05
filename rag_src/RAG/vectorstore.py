import os
import faiss
import numpy as np
import pickle
from typing import List, Any
from sentence_transformers import SentenceTransformer
from embedding import EmbeddingPipeline

class FaissVectorStore:
    def __init__(self, persist_dir: str, embedding_model: str = "all-MiniLM-L6-v2"):
        self.persist_dir = persist_dir
        self.embedding_model = embedding_model
        
        # Paths
        self.faiss_path = os.path.join(self.persist_dir, "faiss.index")
        self.meta_path = os.path.join(self.persist_dir, "metadata.pkl")
        
        self.index = None
        self.metadata = []  # Stores the actual text chunks
        self.model = SentenceTransformer(embedding_model)
        
        # Load existing index if valid, else create new
        if os.path.exists(self.faiss_path) and os.path.exists(self.meta_path):
            self.load()
        else:
            print(f"[INFO] Initializing new FAISS index at {self.persist_dir}")
            # Dimension for all-MiniLM-L6-v2 is 384
            self.index = faiss.IndexFlatL2(384) 

    def add_documents(self, documents: List[Any]):
        """
        Incrementally adds new documents to the existing index.
        """
        if not documents:
            return

        print(f"[INFO] Processing {len(documents)} new documents...")
        
        # 1. Chunking
        emb_pipe = EmbeddingPipeline(model_name=self.embedding_model)
        chunks = emb_pipe.chunk_documents(documents)
        
        if not chunks:
            return

        # 2. Embedding
        embeddings = emb_pipe.embed_chunks(chunks)
        
        # 3. Add to Index
        vector_data = np.array(embeddings).astype('float32')
        self.index.add(vector_data)
        
        # 4. Update Metadata (Keep text linked to vector ID)
        new_metadatas = [{"text": chunk.page_content, "source": chunk.metadata.get("source", "unknown")} for chunk in chunks]
        self.metadata.extend(new_metadatas)
        
        # 5. Save immediately to persist
        self.save()
        print(f"[SUCCESS] Added {len(chunks)} chunks. Total vectors: {self.index.ntotal}")

    def save(self):
        if not os.path.exists(self.persist_dir):
            os.makedirs(self.persist_dir)
        faiss.write_index(self.index, self.faiss_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.metadata, f)

    def load(self):
        self.index = faiss.read_index(self.faiss_path)
        with open(self.meta_path, "rb") as f:
            self.metadata = pickle.load(f)
        print(f"[INFO] Loaded {self.index.ntotal} vectors.")

    def query(self, query_text: str, top_k: int = 5):
        if not self.index or self.index.ntotal == 0:
            return []
            
        query_emb = self.model.encode([query_text]).astype('float32')
        D, I = self.index.search(query_emb, top_k)
        
        results = []
        for idx, dist in zip(I[0], D[0]):
            if idx < len(self.metadata) and idx >= 0:
                results.append({
                    "metadata": self.metadata[idx], 
                    "distance": float(dist)
                })
        return results