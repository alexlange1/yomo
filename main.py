from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import cohere
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client

# === Load environment variables ===
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
COHERE_KEY = os.getenv("COHERE_API_KEY")
co = cohere.Client(COHERE_KEY)

# === Initialize Supabase client ===
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# === FastAPI app ===
app = FastAPI()

# === Allow all CORS (you can restrict to frontend domain later) ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    top_k: int = 5

# === Embed question ===
def embed_query(query):
    response = co.embed(
        texts=[query],
        model="embed-english-v3.0",
        input_type="search_query"
    )
    return response.embeddings[0]

# === Search Supabase chunks using vector similarity ===
def search_supabase(query_embedding, top_k):
    query = f"""
        SELECT text, page, embedding
        FROM sinclair_chunks
        ORDER BY embedding <#> ARRAY{query_embedding}
        LIMIT {top_k};
    """

    response = supabase.rpc("sql", {"query": query}).execute()

    if response.error:
        raise Exception(f"Supabase RPC error: {response.error['message']}")

    return response.data

# === Generate answer using Cohere ===
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

# === POST route ===
@app.post("/ask")
def ask_question(request: QuestionRequest):
    try:
        query_embedding = embed_query(request.question)
        chunks = search_supabase(query_embedding, request.top_k)
        answer = generate_answer(request.question, chunks)

        sources = [{"page": c["page"], "text": c["text"][:120] + "..."} for c in chunks]

        return {
            "answer": answer,
            "sources": sources
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
