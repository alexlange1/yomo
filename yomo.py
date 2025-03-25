import fitz  # PyMuPDF
import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
import cohere

# === Step 1: Load API key ===
load_dotenv()
cohere_api_key = os.getenv("COHERE_API_KEY")
if not cohere_api_key:
    raise ValueError("Missing COHERE_API_KEY in .env file")

co = cohere.Client(cohere_api_key)

# === Step 2: Load PDF ===
pdf_path = Path("/Users/alexanderlange/Downloads/Sinclair’s Research.pdf")
doc = fitz.open(pdf_path)

# === Step 3: Chunking helper ===
def chunk_text(text, max_tokens=750):
    import tiktoken
    enc = tiktoken.get_encoding("cl100k_base")
    words = text.split()
    chunks, current = [], []
    for word in words:
        current.append(word)
        if len(enc.encode(" ".join(current))) > max_tokens:
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))
    return chunks

# === Step 4: Extract chunks from PDF ===
all_chunks = []
for page in doc:
    text = page.get_text()
    chunks = chunk_text(text)
    for chunk in chunks:
        all_chunks.append({
            "text": chunk.strip(),
            "page": page.number + 1
        })

print(f"Extracted {len(all_chunks)} chunks")

# === Step 5: Generate embeddings via Cohere ===
texts = [c['text'] for c in all_chunks]

print("⏳ Generating embeddings with Cohere...")
response = co.embed(
    texts=texts,
    model="embed-english-v3.0",
    input_type="search_document"
)
embeddings = response.embeddings

# Attach embeddings to chunks
for i in range(len(all_chunks)):
    all_chunks[i]['embedding'] = embeddings[i]

# === Step 6: Save to JSON ===
with open("sinclair_chunks.json", "w") as f:
    json.dump(all_chunks, f)

print("Saved embedded chunks to sinclair_chunks.json")
