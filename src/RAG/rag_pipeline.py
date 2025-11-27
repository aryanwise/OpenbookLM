from data_loader import DocumentLoader
from vectorstore import FaissVectorStore
from embedding import EmbeddingPipeline
from search import RAGsearch

class RAGPipeline:
    # Pipeline architecture 
    def __init__(self):
        self._load_pipeline()

    def _load_pipeline(self):
        # Load documents
        DocumentLoader(data_dir="../data")

        # Load vector stores
        store = FaissVectorStore("faiss_store")
        store.load()
        
        # 
        rag_search = RAGsearch(llm_model="gemma3:4b")
        user_query = "What is supervised learning?"
        print(f"Querying: {user_query}...")
    
        summary = rag_search.search_and_summarize(user_query, top_k=3)
        print("\nSummary Response:\n", summary)