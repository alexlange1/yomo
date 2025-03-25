import os
import json
import requests
from dotenv import load_dotenv

# Load Supabase credentials from .env
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Load JSON file
with open("sinclair_chunks.json", "r") as f:
    chunks = json.load(f)

# Upload each chunk
for i, chunk in enumerate(chunks):
    payload = {
        "text": chunk["text"],
        "page": chunk["page"],
        "embedding": chunk["embedding"]
    }

    res = requests.post(
        f"{SUPABASE_URL}/rest/v1/sinclair_chunks",
        headers=headers,
        json=payload
    )

    if res.status_code != 201:
        print(f"❌ Error uploading chunk {i}: {res.text}")
    else:
        print(f"✅ Uploaded chunk {i+1}/{len(chunks)}")
