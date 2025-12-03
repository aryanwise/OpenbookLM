# from data_loader import DocumentLoader
# from embedding import EmbeddingPipeline
# from vectorstore import FaissVectorStore
# from search import RAGsearch

# if __name__ == "__main__":
#     # Load document
#     docs = DocumentLoader(data_dir="../data")
#     # print("Total documents loaded", len(docs.documents))
#     # document example
#     # TODO: change this to loading document selected by user in frontend 
#     # for doc in load_data.documents[:-1]:
#         # print(doc.page_content)    

#     # Load vectors
#     store = FaissVectorStore("faiss_store")
#     # TODO: make a function to check if the vector store is already created
#     # if not the run the script below 
#     # store.build_from_documents(docs) 
#     store.load()
#     # print(store.query("What is supervised learning?", top_k=3))
#     rag_search = RAGsearch(llm_model="gemma3:4b")
#     user_query = "What is supervised learning?"
#     print(f"Querying: {user_query}...")
    
#     summary = rag_search.search_and_summarize(user_query, top_k=3)
#     print("\nSummary Response:\n", summary)

from rag_pipeline import RAGPipeline
if __name__ == "__main__":
    rag_pipeline = RAGPipeline()
    rag_pipeline.search()