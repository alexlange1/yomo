import os
import re
import uuid
import requests
import cohere
from tqdm import tqdm
from pathlib import Path
from dotenv import load_dotenv
import json

# === Load credentials from yomo_backend/.env ===
env_path = Path("yomo_backend/.env")
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
COHERE_KEY = os.getenv("COHERE_API_KEY")

# === Init Cohere client ===
co = cohere.Client(COHERE_KEY)

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"  # Add this to ensure proper response handling
}

# === Extract hyperlinks from markdown ===
def extract_links(text):
    return re.findall(r'\[.*?\]\((.*?)\)', text)

# === Split markdown content into idea-based chunks ===
def split_markdown(md_text, doctor):
    print(f"\n=== DEBUG: Markdown Processing ===")
    
    # First, check if we have any headers
    headers = re.findall(r'^(#{1,3} .+)$', md_text, re.MULTILINE)
    print(f"Found {len(headers)} headers:")
    for h in headers[:3]:  # Print first 3 headers
        print(f"  - {h}")
    
    # Split into sections with a simpler pattern first
    sections = md_text.split('\n#')
    if len(sections) > 1:
        # Add back the # that was removed by split
        sections = [sections[0]] + ['#' + s for s in sections[1:]]
    
    chunks = []
    
    # Process the initial section if it exists
    if sections[0].strip():
        chunks.append({
            "id": str(uuid.uuid4()),
            "doctor": doctor,
            "title": "Introduction",
            "text": sections[0].strip(),
            "sources": []
        })
    
    # Process each section
    for section in sections[1:]:
        # Split header from content
        parts = section.split('\n', 1)
        if len(parts) == 2:
            header = parts[0].strip().lstrip('#').strip()
            content = parts[1].strip()
            
            # Split content into smaller chunks
            paragraphs = content.split('\n\n')
            for para in paragraphs:
                if len(para.strip()) > 50:  # Only create chunks for substantial paragraphs
                    chunks.append({
                        "id": str(uuid.uuid4()),
                        "doctor": doctor,
                        "title": header,
                        "text": para.strip(),
                        "sources": []
                    })
    
    print(f"Created {len(chunks)} chunks")
    if chunks:
        print("First chunk preview:")
        print(f"Title: {chunks[0]['title']}")
        print(f"Text: {chunks[0]['text'][:100]}...")
    print("===============================\n")
    
    return chunks


# === Upload chunks to Supabase in batches ===
def upload_chunks(md_file, doctor, supabase_table, batch_size=10):
    if not os.path.exists(md_file):
        print(f"❌ File not found: {md_file}")
        return

    try:
        with open(md_file, "r", encoding="utf-8") as f:
            md_text = f.read()
    except Exception as e:
        print(f"❌ Error reading file {md_file}: {str(e)}")
        return

    # Check if file is empty
    if not md_text.strip():
        print(f"❌ File {md_file} is empty")
        return

    chunks = split_markdown(md_text, doctor)
    print(f"🔹 {doctor}: {len(chunks)} chunks parsed")
    
    # Debug: Print the first few characters of the markdown file to verify content
    print(f"📄 First 100 chars of {md_file}: {md_text[:100]}")
    
    # Debug: Check if the file path is correct
    print(f"📂 File path: {os.path.abspath(md_file)}")
    
    # If no chunks were parsed, exit early
    if not chunks:
        print(f"⚠️ No chunks were parsed for {doctor}. Check if the markdown format is correct.")
        return

    failed_chunks = []

    for i in tqdm(range(0, len(chunks), batch_size), desc=f"Uploading {doctor}"):
        batch = chunks[i:i + batch_size]
        texts = [c["text"] for c in batch]

        try:
            response = co.embed(
                texts=texts,
                model="embed-english-v3.0",
                input_type="search_document"
            )
            embeddings = response.embeddings

            for j, chunk in enumerate(batch):
                # Format the embedding array properly for PostgreSQL
                embedding_array = list(embeddings[j])  # Convert to regular list
                
                payload = {
                    "id": chunk["id"],
                    "doctor": chunk["doctor"],
                    "title": chunk["title"],
                    "text": chunk["text"],
                    "embedding": embedding_array,  # Send as regular array
                    "sources": chunk.get("sources", [])  # Ensure sources is always a list
                }

                # Debug print
                print(f"\nSending payload for chunk {i+j}:")
                print(f"ID: {payload['id']}")
                print(f"Embedding length: {len(payload['embedding'])}")

                res = requests.post(
                    f"{SUPABASE_URL}/rest/v1/{supabase_table}",
                    headers=headers,
                    json=payload
                )

                if res.status_code != 201:
                    print(f"❌ Error details: {res.text}")
                    failed_chunks.append(chunk["id"])
                else:
                    print(f"✅ Successfully uploaded chunk {i+j}")

        except Exception as e:
            print(f"❌ Error during processing: {str(e)}")
            failed_chunks.extend([c["id"] for c in batch])

    if failed_chunks:
        print(f"⚠️ {len(failed_chunks)} chunks failed for {doctor}")
        print(f"Failed chunk IDs: {failed_chunks[:5]}...")
    else:
        print(f"✅ {doctor} upload completed successfully")


def embed_query(query):
    response = co.embed(
        texts=[query],
        model="embed-english-v3.0",  # This model generates 1024-dimensional vectors
        input_type="search_document"  # Changed from search_query to search_document
    )
    
    # Add dimension check
    embedding = response.embeddings[0]
    print(f"DEBUG: Embedding dimensions: {len(embedding)}")
    return embedding


# === Search Supabase chunks using vector similarity via REST API ===
def search_supabase(query_embedding, top_k):
    # Add dimension check
    print(f"DEBUG: Checking embedding dimensions: {len(query_embedding)}")
    if len(query_embedding) != 1024:
        raise ValueError(f"Expected 1024 dimensions, got {len(query_embedding)}")
        
    # ... rest of the function


# === Bulk upload loop ===
if __name__ == "__main__":
    # Verify connection to Supabase
    try:
        test_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/",
            headers=headers
        )
        print(f"Supabase connection test: {test_response.status_code}")
        if test_response.status_code != 200:
            print(f"⚠️ Supabase connection issue: {test_response.text}")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {str(e)}")
    
    # Check if health_reports directory exists
    health_reports_dir = Path("health_reports")
    if not health_reports_dir.exists():
        print(f"❌ Directory not found: {health_reports_dir.absolute()}")
        print("Creating directory...")
        health_reports_dir.mkdir(exist_ok=True)
        print("Please add markdown files for doctors in the health_reports directory.")
        exit(1)
    
    # List available files in health_reports directory
    print(f"📁 Files in health_reports directory:")
    for file in health_reports_dir.glob("*.md"):
        print(f"  - {file.name}")
        # Debug file size
        print(f"    Size: {file.stat().st_size} bytes")
        # Try to read first line
        try:
            with open(file, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                print(f"    First line: {first_line[:50]}...")
        except Exception as e:
            print(f"    Error reading file: {str(e)}")

    # Add this test block before the main loop
    print("\n=== Testing Single File ===")
    test_file = "health_reports/sinclair.md"
    if os.path.exists(test_file):
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"Test file size: {len(content)} bytes")
            print(f"First 200 chars:\n{content[:200]}")
            
            # Test chunk creation
            test_chunks = split_markdown(content, "sinclair")
            print(f"Test chunks created: {len(test_chunks)}")
    else:
        print(f"❌ Test file not found: {test_file}")
    print("======================\n")

    # After your environment variable loading
    print("\n=== Environment Check ===")
    print(f"SUPABASE_URL: {'✅ Set' if SUPABASE_URL else '❌ Missing'}")
    print(f"SUPABASE_KEY: {'✅ Set' if SUPABASE_KEY else '❌ Missing'}")
    print(f"COHERE_KEY: {'✅ Set' if COHERE_KEY else '❌ Missing'}")
    print("======================\n")

    if not all([SUPABASE_URL, SUPABASE_KEY, COHERE_KEY]):
        print("❌ Missing required environment variables!")
        exit(1)

    doctors = [
        ("sinclair", "sinclair_chunks"),
        ("longo", "longo_chunks"),
        ("huberman", "huberman_chunks"),
        ("barzilai", "barzilai_chunks"),
        ("de_grey", "de_grey_chunks"),
        ("campisi", "campisi_chunks")
    ]

    for doctor, table in doctors:
        md_file = f"health_reports/{doctor}.md"
        if not os.path.exists(md_file):
            print(f"⚠️ File not found: {md_file} - skipping {doctor}")
            continue
            
        print(f"\n📚 Uploading: {doctor} → {table}")
        upload_chunks(
            md_file=md_file,
            doctor=doctor,
            supabase_table=table
        )

    print("\n✅ All uploads completed.")
