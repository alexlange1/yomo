import numpy as np
from scipy.spatial.distance import cosine
from supabase import create_client
import cohere
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase_client = create_client(supabase_url, supabase_key)

# Initialize Cohere client
co = cohere.Client(os.getenv("COHERE_API_KEY"))

# === 1. Embed user query using Cohere ===
def get_query_embedding(query):
    response = co.embed(
        texts=[query],
        model="embed-english-v3.0",
        input_type="search_query"  # use "search_document" for chunks
    )
    return response.embeddings[0]

# === 2. Query Supabase and compare embeddings ===
def get_most_similar_chunk(query_embedding):
    response = supabase_client.from_("sinclair_chunks").select("id, text, embedding").execute()
    
    similarities = []
    for row in response.data:
        chunk_embedding = np.array(row['embedding'])
        similarity = 1 - cosine(query_embedding, chunk_embedding)
        similarities.append((row['id'], row['text'], similarity))
    
    # Sort and return top 3
    similarities.sort(key=lambda x: x[2], reverse=True)
    return similarities[:3]

# === 3. Combine into context string ===
def get_relevant_context(user_query):
    query_embedding = get_query_embedding(user_query)
    relevant_chunks = get_most_similar_chunk(query_embedding)
    context = "\n\n".join([chunk[1] for chunk in relevant_chunks])
    return context
