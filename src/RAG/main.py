from data_loader import DocumentLoader
from embedding import EmbeddingPipeline
if __name__ == "__main__":
    load_data = DocumentLoader(data_dir="../data")
    print("Total documents loaded", len(load_data.documents))
    # document example
    # TODO: change this to loading document selected by user in frontend 
    # for doc in load_data.documents[:-1]:
        # print(doc.page_content)    
    emb_pipe = EmbeddingPipeline() # Initialize the embedding pipeline
    chunks = emb_pipe.chunk_documents(load_data.documents)
    embeddings = emb_pipe.embed_chunks(chunks)
    print("[INFO] Example embedding:", embeddings[0] if len(embeddings) > 0 else None)
