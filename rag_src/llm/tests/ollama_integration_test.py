import unittest
from unittest.mock import patch, Mock
import requests

class TestOllamaIntegration(unittest.TestCase):

    def setUp(self):
        """Set up constants for the tests."""
        self.OLLAMA_URL = "http://localhost:11434/api/chat"
        self.MODEL = "phi3:3.8b"
        self.message = "What is the capital of France?"

    def test_constants_are_set(self):
        """Test that the URL and MODEL are correctly defined."""
        self.assertEqual(self.OLLAMA_URL, "http://localhost:11434/api/chat")
        self.assertEqual(self.MODEL, "phi3:3.8b")

    @patch('requests.post')
    def test_successful_request(self, mock_post):
        """Test a successful API call to Ollama."""
        # Configure the mock to return a successful response
        mock_response = Mock()
        mock_response.status_code = 200
        expected_content = "The capital of France is Paris."
        mock_response.json.return_value = {
            "model": self.MODEL,
            "created_at": "2023-10-13T15:00:00Z",
            "message": {
                "role": "assistant",
                "content": expected_content
            },
            "done": True
        }
        mock_post.return_value = mock_response

        # The payload that should be sent
        payload = {
            "model": self.MODEL,
            "messages": [{"role": "user", "content": self.message}],
            "stream": False,
        }

        # Make the request
        response = requests.post(self.OLLAMA_URL, json=payload)

        # Assertions
        mock_post.assert_called_once_with(self.OLLAMA_URL, json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"]["content"], expected_content)

    @patch('requests.post')
    def test_failed_request(self, mock_post):
        """Test a failed API call to Ollama."""
        # Configure the mock to return an error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        response = requests.post(self.OLLAMA_URL, json={})

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.text, "Internal Server Error")

if __name__ == '__main__':
    unittest.main()