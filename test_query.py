import requests

response = requests.post(
    "https://yomo-api.onrender.com/ask",  # ✅ Deployed Render URL
    headers={"Content-Type": "application/json"},
    json={
        "question": "What does David Sinclair think about NMN?",
        "top_k": 3,
        "doctor": "sinclair"
    }
)

print(response.status_code)
print(response.json())
