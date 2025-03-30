import os
import requests
import cohere
from dotenv import load_dotenv
from pathlib import Path

# === Load env ===
env_path = Path("yomo_backend/.env")
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
COHERE_KEY = os.getenv("COHERE_API_KEY")

co = cohere.Client(COHERE_KEY)

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# === Search a specific table ===
def search_doctor_chunks(query, table_name="sinclair_chunks", match_function="match_sinclair_chunks", top_k=5):
    # Step 1: Get query embedding
    embed_response = co.embed(
        texts=[query],
        model="embed-english-v3.0",
        input_type="search_query"
    )
    query_embedding = embed_response.embeddings[0]

    # Step 2: POST to Supabase RPC function
    rpc_url = f"{SUPABASE_URL}/rest/v1/rpc/{match_function}"
    payload = {
        "query_embedding": query_embedding,
        "match_count": top_k
    }

    res = requests.post(rpc_url, headers=headers, json=payload)

    if res.status_code != 200:
        print(f"❌ Error: {res.status_code} - {res.text}")
        return []

    results = res.json()
    return results


# === Example usage ===
if __name__ == "__main__":
    query = "What does Sinclair recommend for increasing longevity?"
    matches = search_doctor_chunks(query, table_name="sinclair_chunks", match_function="match_sinclair_chunks", top_k=5)

    for i, match in enumerate(matches):
        print(f"\n🔹 Match {i + 1} (similarity: {round(match['similarity'], 3)})")
        print(f"Title: {match['title']}")
        print(f"Text: {match['text'][:300]}...")
