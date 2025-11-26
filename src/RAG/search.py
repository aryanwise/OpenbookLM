import os 
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from vectorstore import FaissVectorStore

load_dotenv()

class RAGsearch:
    def __init__(self, persist_dir: str = "faiss_store", embedding_model: str = "all-MiniLM-L6-v2", llm_model: str = "gemma3:4b"):
        """
        Initialize RAGSearch with local Ollama support.
        
        Args:
            persist_dir: Directory where Faiss index is stored.
            embedding_model: HuggingFace embedding model name.
            llm_model: Ollama model tag (e.g., 'gemma3:4b').
        """
        self.vectorstore = FaissVectorStore(persist_dir, embedding_model)
        
        # Load or build vectorstore logic preserved from your snippet
        faiss_path = os.path.join(persist_dir, "faiss.index")
        meta_path = os.path.join(persist_dir, "metadata.pkl")
        
        if not (os.path.exists(faiss_path) and os.path.exists(meta_path)):
            print(f"[INFO] Index not found at {persist_dir}. Building from data...")
            # specific import inside to avoid circular dependencies if any
            try:
                from data_loader import DocumentLoader
                docs = DocumentLoader("../data")
                self.vectorstore.build_from_documents(docs)
            except ImportError:
                print("[ERROR] Could not import 'data_loader'. Ensure your project structure is correct.")
        else:
            print(f"[INFO] Loading existing index from {persist_dir}...")
            self.vectorstore.load()

        # Initialize Ollama locally
        # base_url defaults to http://localhost:11434
        self.llm = ChatOllama(
            model=llm_model,
            temperature=0
        )
        print(f"[INFO] Local Ollama LLM initialized: {llm_model}")

    def search_and_summarize(self, query: str, top_k: int = 5) -> str:
        """
        Retrieve context from vectorstore and summarize using Ollama.
        """
        # 1. Retrieve relevant documents
        results = self.vectorstore.query(query, top_k=top_k)
        
        # Extract text from metadata (handling potential missing keys)
        texts = [r["metadata"].get("text", "") for r in results if r.get("metadata")]
        context = "\n\n".join(texts)

        if not context:
            return "No relevant documents found in the vector store."

        # 2. Construct Prompt
        # Using a proper chat template is often more reliable for instruct models
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant. Answer the user query based ONLY on the provided context."),
            ("user", "Context:\n{context}\n\nQuery: {query}")
        ])
        
        chain = prompt_template | self.llm

        # 3. Invoke LLM
        response = chain.invoke({"context": context, "query": query})
        
        return response.content

