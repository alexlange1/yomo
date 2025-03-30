import requests

response = requests.post(
    "http://127.0.0.1:8000/ask",
    headers={"Content-Type": "application/json"},
    json={
        "question": "What does David Sinclair think about NMN?",
        "top_k": 3,
        "doctor": "sinclair"
    }
)

print(response.json())
