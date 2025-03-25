import os
import cohere
import requests
from dotenv import load_dotenv

# === Load API keys and project settings from .env ===
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
COHERE_KEY = os.getenv("COHERE_API_KEY")

# === Initialize Cohere client ===
co = cohere.Client(COHERE_KEY)

# === Headers for Supabase requests ===
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# === Step 1: Embed the user question ===
def embed_query(query):
    response = co.embed(
        texts=[query],
        model="embed-english-v3.0",
        input_type="search_query"
    )
    return response.embeddings[0]

# === Step 2: Query Supabase for similar chunks ===
def search_supabase(query_embedding, top_k=5):
    # SQL-safe array string for pgvector
    embedding_str = str(query_embedding).replace("[", "(").replace("]", ")")

    sql = f"""
        SELECT text, page, embedding <#> '{embedding_str}' AS distance
        FROM sinclair_chunks
        ORDER BY distance ASC
        LIMIT {top_k};
    """

    res = requests.post(
        f"{SUPABASE_URL}/rest/v1/rpc/execute_sql",  # requires PostgREST or SQL function endpoint
        headers=headers,
        json={"sql": sql}
    )

    if res.status_code != 200:
        raise Exception(f"Supabase query failed: {res.text}")

    return res.json()

# === Step 3: Generate an answer using Cohere Command R+ ===
def generate_answer(question, context_chunks):
    # Add page numbers to each chunk
    context = "\n\n".join([f"(Page {chunk['page']})\n{chunk['text']}" for chunk in context_chunks])

    prompt = f"""
You are a helpful and scientifically grounded AI trained on David Sinclair's research. Use the following CONTEXT to answer the QUESTION as clearly and accurately as possible.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""

    response = co.chat(
        model="command-r-plus",
        message=prompt,
        temperature=0.3,
        max_tokens=500
    )

    return response.text

# === Main Function ===
if __name__ == "__main__":
    question = input("Ask something based on Sinclair’s research: ")

    print("🔎 Embedding your query...")
    query_embedding = embed_query(question)

    print("📥 Searching for relevant context in Supabase...")
    chunks = search_supabase(query_embedding)

    print("🤖 Generating answer with Cohere Command R+...")
    answer = generate_answer(question, chunks)

    print("\n💬 Answer:\n")
    print(answer)
