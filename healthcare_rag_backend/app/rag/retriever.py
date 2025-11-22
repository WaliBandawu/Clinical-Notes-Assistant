import redis
import json
import os
from openai import OpenAI
from healthcare_rag_backend.app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Initialize Redis connection
redis_url = settings.REDIS_URL
redis_client = redis.from_url(redis_url, decode_responses=False)

def get_embeddings(text: str, model: str = "text-embedding-3-small") -> list:
    """Get embeddings from OpenAI API."""
    response = client.embeddings.create(
        model=model,
        input=text
    )
    return response.data[0].embedding

def load_and_store_documents():
    """Load clinical documents and store them in Redis."""
    # Load documents
    with open("/Users/waliyyullah/Desktop/Portforlio/Redis Healthcare/healthcare_rag_backend/data/clinical_docs/clinical_notes.txt", "r") as f:
        content = f.read()
    
    # Split into chunks
    chunk_size = 1000
    chunk_overlap = 200
    chunks = []
    
    for i in range(0, len(content), chunk_size - chunk_overlap):
        chunk = content[i:i + chunk_size]
        if chunk.strip():
            chunks.append(chunk)
    
    # Store chunks with embeddings in Redis
    for idx, chunk in enumerate(chunks):
        embedding = get_embeddings(chunk)
        doc_key = f"doc:{idx}"
        redis_client.hset(
            doc_key,
            mapping={
                "content": chunk,
                "embedding": json.dumps(embedding)
            }
        )
        # Add to sorted set for similarity search
        redis_client.sadd("documents", doc_key)

def retrieve_similar_documents(query: str, k: int = 4) -> list:
    """Retrieve documents similar to the query."""
    query_embedding = get_embeddings(query)
    
    doc_keys = redis_client.smembers("documents")
    similarities = []
    
    for doc_key in doc_keys:
        doc_data = redis_client.hgetall(doc_key)
        if b"embedding" in doc_data:
            stored_embedding = json.loads(doc_data[b"embedding"])
            # Calculate cosine similarity
            similarity = cosine_similarity(query_embedding, stored_embedding)
            similarities.append({
                "key": doc_key,
                "content": doc_data[b"content"].decode(),
                "similarity": similarity
            })
    
    # Sort by similarity and return top k
    similarities.sort(key=lambda x: x["similarity"], reverse=True)
    return similarities[:k]

def cosine_similarity(a: list, b: list) -> float:
    """Calculate cosine similarity between two vectors."""
    import math
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x ** 2 for x in a))
    norm_b = math.sqrt(sum(x ** 2 for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0
    return dot_product / (norm_a * norm_b)
