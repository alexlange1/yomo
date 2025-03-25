from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import cohere
import requests
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# === Load env variables ===
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
COHERE_KEY = os.getenv("COHERE_API_KEY")
co = cohere.Client(COHERE_KEY)

# === FastAPI app setup ===
app = FastAPI()

# Optional: allow all origins for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict to your Lovable frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Welcome to the Sinclair RAG API!"}

# === Request schema ===
class QuestionRequest(BaseModel):
    question: str
    top_k: int = 5  # Number of context chunks to retrieve

# === Helper: Embed question ===
def embed_query(query):
    response = co.embed(
        texts=[query],
        model="embed-english-v3.0",
        input_type="search_query"
    )
    return response.embeddings[0]

# === Helper: Query Supabase for similar chunks ===
def search_supabase(query_embedding, top_k):
    embedding_str = str(query_embedding).replace("[", "(").replace("]", ")")

    sql = f"""
        SELECT text, page, embedding <#> '{embedding_str}' AS distance
        FROM sinclair_chunks
        ORDER BY distance ASC
        LIMIT {top_k};
    """

    res = requests.post(
        f"{SUPABASE_URL}/rest/v1/rpc/execute_sql",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        },
        json={"sql": sql}
    )

    if res.status_code != 200:
        raise Exception(f"Supabase error: {res.text}")

    return res.json()

# === Helper: Generate answer with Cohere ===
def generate_answer(question, context_chunks):
    context = "\n\n".join(
        [f"(Page {chunk['page']})\n{chunk['text']}" for chunk in context_chunks]
    )

    prompt = f"""
You are a helpful and scientifically grounded AI trained on David Sinclair's research. Use the CONTEXT below to answer the QUESTION. When possible, cite the page number (e.g. “(Page 5)”) where the information comes from.

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

# === Route: POST /ask ===
@app.post("/ask")
def ask_question(request: QuestionRequest):
    try:
        query_embedding = embed_query(request.question)
        chunks = search_supabase(query_embedding, request.top_k)
        answer = generate_answer(request.question, chunks)
        return {"answer": answer, "sources": [{"page": c["page"]} for c in chunks]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
