import sys
import os
from pathlib import Path

def run_import_test():
    print("------------------------------------------------")
    print("🔍 DIAGNOSTIC: Testing RAG Imports from Frontend")
    print("------------------------------------------------")

    # 1. LOCATE DIRECTORIES
    # Get the path of this script (src/frontend/test.py)
    current_file = Path(__file__).resolve()
    frontend_dir = current_file.parent
    src_dir = frontend_dir.parent
    rag_dir = src_dir / "RAG"

    print(f"📂 Current Dir:  {frontend_dir}")
    print(f"📂 RAG Target:   {rag_dir}")

    # 2. CHECK EXISTENCE
    if not rag_dir.exists():
        print(f"❌ CRITICAL ERROR: The directory '{rag_dir}' does not exist.")
        print("   Please check your folder structure.")
        return

    # 3. MODIFY SYSTEM PATH
    # This is the magic line. It allows Python to find 'search.py' inside 'src/RAG'
    sys.path.append(str(rag_dir))
    print(f"✅ path added to sys.path")

    # 4. ATTEMPT IMPORTS
    print("\n--- Attempting Imports ---")

    # Test 1: Vector Store
    try:
        print("1️⃣  Importing FaissVectorStore...", end=" ")
        from vectorstore import FaissVectorStore
        print("✅ SUCCESS")
    except ImportError as e:
        print(f"❌ FAILED\n   Error: {e}")

    # Test 2: Data Loader
    try:
        print("2️⃣  Importing DocumentLoader...", end=" ")
        from data_loader import DocumentLoader
        print("✅ SUCCESS")
    except ImportError as e:
        print(f"❌ FAILED\n   Error: {e}")

    # Test 3: Search (The one causing issues usually)
    try:
        print("3️⃣  Importing RAGsearch...", end=" ")
        from search import RAGsearch
        print("✅ SUCCESS")
    except ImportError as e:
        print(f"❌ FAILED\n   Error: {e}")
        print("   (Note: If this fails but others worked, check imports INSIDE search.py)")

    # Test 4: Embedding 
    try:
        print("4️⃣ Importing Embedding...", end=" ")
        from embedding import EmbeddingPipeline
        print("✅ SUCCESS")
    except ImportError as e:
        print(f"❌ FAILED\n   Error: {e}")

    print("\n------------------------------------------------")
    print("🏁 Test Complete")

if __name__ == "__main__":
    run_import_test()