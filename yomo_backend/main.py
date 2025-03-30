from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import os
import hashlib
import cohere
import requests
import json
from dotenv import load_dotenv

# === Load environment variables ===
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
COHERE_KEY = os.getenv("COHERE_API_KEY")
co = cohere.Client(COHERE_KEY)

# === FastAPI app ===
app = FastAPI()

# === Allow all CORS (adjust for prod) ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === In-memory cache ===
cache: Dict[str, Dict] = {}

# === Pydantic schema ===
class QuestionRequest(BaseModel):
    question: str
    top_k: int = 5
    doctor: str = "sinclair"

@app.get("/")
def root():
    return {"message": "Welcome to the Doctor GPT RAG API!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

# === Embedding with Cohere ===
def embed_query(query):
    response = co.embed(
        texts=[query],
        model="embed-english-v3.0",
        input_type="search_query"
    )
    return response.embeddings[0]

# === Supabase vector similarity search ===
def search_supabase(query_embedding, doctor, top_k):
    table = f"{doctor}_chunks"
    url = f"{SUPABASE_URL}/rest/v1/{table}"

    params = {
        'select': 'text,page',
        'order': f'embedding.<->.{json.dumps(query_embedding)}',
        'limit': str(top_k)
    }

    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }

    res = requests.get(url, params=params, headers=headers)

    if res.status_code != 200:
        raise Exception(f"Supabase query error: {res.text}")

    return res.json()

# === Generate answer using Cohere Command R ===
def generate_answer(question, context_chunks, doctor):
    context = "\n\n".join(
        [f"(Page {chunk['page']})\n{chunk['text']}" for chunk in context_chunks]
    )

    prompt = f"""
You are Dr. {doctor.capitalize()}, a world-renowned expert in health and wellness. Use the CONTEXT below to answer the QUESTION. Cite the page number when possible.

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

# === Main POST endpoint ===
@app.post("/ask")
def ask_question(request: QuestionRequest):
    try:
        key = hashlib.sha256(f"{request.doctor}|{request.question}".encode()).hexdigest()
        if key in cache:
            return cache[key]

        query_embedding = embed_query(request.question)
        chunks = search_supabase(query_embedding, request.doctor, request.top_k)
        answer = generate_answer(request.question, chunks, request.doctor)

        sources = [{"page": c["page"], "text": c["text"][:120] + "..."} for c in chunks]
        result = {"answer": answer, "sources": sources}

        cache[key] = result

        with open("query_log.txt", "a") as log_file:
            log_file.write(f"Doctor: {request.doctor}\n")
            log_file.write(f"Q: {request.question}\n")
            log_file.write(f"A: {answer}\n\n")

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
