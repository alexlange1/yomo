from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import os
import hashlib
import requests
import json
from dotenv import load_dotenv
import cohere

# === Load environment variables ===
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
CHUTES_URL = os.getenv("CHUTES_URL")
CHUTES_API_KEY = os.getenv("CHUTES_API_KEY")
COHERE_KEY = os.getenv("COHERE_API_KEY")

# === Initialize Cohere client ===
co = cohere.Client(COHERE_KEY)

# === FastAPI app ===
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === In-memory cache ===
cache: Dict[str, Dict] = {}

# === Request schema ===
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

# === Embedding via Cohere ===
def embed_query(query):
    response = co.embed(
        texts=[query],
        model="embed-english-v3.0",
        input_type="search_query"
    )
    return response.embeddings[0]

# === Supabase vector similarity search ===
def search_supabase(query_embedding, doctor, top_k):
    function_name = f"match_{doctor}_chunks"
    url = f"{SUPABASE_URL}/rest/v1/rpc/{function_name}"

    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }

    payload = {
        "query_embedding": query_embedding,
        "match_count": top_k
    }

    res = requests.post(url, headers=headers, json=payload)

    if res.status_code != 200:
        raise Exception(f"Supabase function error: {res.text}")

    return res.json()

# === DeepSeek-V3 via Chutes ===
def generate_answer(question, context_chunks, doctor):
    context = "\n\n".join([chunk["text"] for chunk in context_chunks])

    prompt = f"""
You are Dr. {doctor.capitalize()}, a world-renowned expert in health and wellness.

Answer the following QUESTION based on the CONTEXT below. Be accurate, empathetic, and informative. Format your answer in clear paragraphs or bullet points when appropriate.

- If the user makes a typo or vague reference, use intelligent inference to guess what they meant and answer accordingly.
- If something is not directly in the context, provide a helpful, educated response without claiming certainty.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHUTES_API_KEY}"
    }
    payload = {
        "model": "deepseek-ai/DeepSeek-V3-0324",
        "messages": [
            {"role": "system", "content": "You are a helpful and expert doctor."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 500
    }

    response = requests.post(CHUTES_URL, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(f"Chutes API error: {response.text}")

    return response.json()["choices"][0]["message"]["content"]

# === Ask endpoint ===
@app.post("/ask")
def ask_question(request: QuestionRequest):
    try:
        key = hashlib.sha256(f"{request.doctor}|{request.question}".encode()).hexdigest()
        if key in cache:
            return cache[key]

        query_embedding = embed_query(request.question)
        chunks = search_supabase(query_embedding, request.doctor, request.top_k)
        answer = generate_answer(request.question, chunks, request.doctor)

        sources = [{"text": c["text"][:120] + "..."} for c in chunks]
        result = {"answer": answer, "sources": sources}

        cache[key] = result

        with open("query_log.txt", "a") as log_file:
            log_file.write(f"Doctor: {request.doctor}\n")
            log_file.write(f"Q: {request.question}\n")
            log_file.write(f"A: {answer}\n\n")

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
