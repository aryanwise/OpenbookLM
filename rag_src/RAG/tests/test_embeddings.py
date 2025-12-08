import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import os
import sys
from langchain_core.documents import Document

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from embedding import EmbeddingPipeline
class TestEmbeddingPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = EmbeddingPipeline(model_name="nomic-embed-text:latest")
        self.sample_text = "This is a test sentence for embedding. " * 50
        self.doc = Document(page_content=self.sample_text, metadata={"source": "test"})

    def test_chunk_documents(self):
        """Test if documents are split correctly."""
        chunks = self.pipeline.chunk_documents([self.doc])
        self.assertTrue(len(chunks) > 0)
        self.assertIsInstance(chunks[0], Document)
        # Ensure chunk size limit is respected
        self.assertTrue(len(chunks[0].page_content) <= self.pipeline.chunk_size)

    @patch('requests.post')
    def test_embed_chunks(self, mock_post):
        """Test embedding generation with mocked API response."""
        # Mock successful Ollama response
        mock_response = MagicMock()
        mock_response.status_code = 200
        # specific vector size for nomic-embed-text is usually 768
        dummy_vector = [0.1] * 768 
        mock_response.json.return_value = {"embedding": dummy_vector}
        mock_post.return_value = mock_response

        # Create dummy chunks
        chunks = self.pipeline.chunk_documents([self.doc])
        
        # Run embedding
        embeddings = self.pipeline.embed_chunks(chunks)

        # Assertions
        self.assertIsInstance(embeddings, np.ndarray)
        self.assertEqual(embeddings.shape[0], len(chunks)) # Rows = num chunks
        self.assertEqual(embeddings.shape[1], 768)         # Cols = vector dim
        
        # Verify API was called correct number of times
        self.assertEqual(mock_post.call_count, len(chunks))

if __name__ == '__main__':
    unittest.main()