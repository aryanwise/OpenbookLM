import requests

class OllamaClient:
    def __init__(self, model="phi3:3.8b"): # set as default model
        self.url = "http://localhost:11434/api/chat"       
        self.model = model

    def chat(self, user_message):
        """Sends a message to Ollama and returns the response string."""
        # print(f"✅ Sending to {self.model}: {user_message}")

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role":"user",
                    "content":user_message
                }
            ],
            "stream":False,
        } 

        try:
            response = requests.post(self.url, json=payload)
            if response.status_code == 200:
                result = response.json()
                return result["message"]["content"]
            else:
                return f"Error {response.status_code}: {response.text}"
        except Exception as e:
            return f"Connection Error: Is Ollama running? ({e})"