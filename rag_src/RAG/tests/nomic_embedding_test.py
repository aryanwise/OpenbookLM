# Nomic Embedding Test
# Open-Source embedding model 

import requests

# API endpoint and payload
url = "http://localhost:11434/api/embeddings"
payload = {
    "model": "nomic-embed-text",
    "prompt": "The sky is blue because of Rayleigh scattering"
}

# Send the POST request
response = requests.post(url, json=payload)

# Check if the request was successful and parse the response
if response.status_code == 200:
    result = response.json()
    embedding = result["embedding"]
    print("Embedding generated:", embedding)
else:
    print("Error:", response.status_code, response.text)   