import redis
import json
from pathlib import Path
from typing import List, Dict, Optional
from openai import OpenAI
from healthcare_rag_backend.app.core.config import settings
from healthcare_rag_backend.app.core.logging_config import logger

def get_openai_client(api_key: Optional[str] = None) -> OpenAI:
    """Get OpenAI client with optional API key override."""
    return OpenAI(
        api_key=api_key or settings.OPENAI_API_KEY,
        timeout=settings.OPENAI_TIMEOUT
    )

# Default client for backward compatibility
client = get_openai_client()

# Initialize Redis connection pool
redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL,
    max_connections=settings.REDIS_MAX_CONNECTIONS,
    decode_responses=False
)

def get_redis_client():
    """Get a Redis client from the connection pool."""
    return redis.Redis(connection_pool=redis_pool)

def get_embeddings(text: str, model: str = None, api_key: Optional[str] = None) -> list:
    """Get embeddings from OpenAI API.
    
    Args:
        text: Text to embed
        model: Embedding model to use (defaults to settings.EMBEDDING_MODEL)
        api_key: Optional API key override
    
    Returns:
        Embedding vector as a list
    """
    try:
        model = model or settings.EMBEDDING_MODEL
        logger.debug("Getting embeddings for text of length: %d", len(text))
        
        client_instance = get_openai_client(api_key)
        response = client_instance.embeddings.create(
            model=model,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error("Error getting embeddings: %s", str(e))
        raise

def chunk_text(text: str, chunk_size: int = None, chunk_overlap: int = None) -> List[str]:
    """Split text into overlapping chunks.
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk
        chunk_overlap: Overlap between chunks
    
    Returns:
        List of text chunks
    """
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
    chunks = []
    
    for i in range(0, len(text), chunk_size - chunk_overlap):
        chunk = text[i:i + chunk_size]
        if chunk.strip():
            chunks.append(chunk)
    
    return chunks

def load_and_store_documents(file_path: str = None, clear_existing: bool = False, api_key: Optional[str] = None):
    """Load clinical documents and store them in Redis.
    
    Args:
        file_path: Path to the document file (defaults to settings.CLINICAL_NOTES_FILE)
        clear_existing: Whether to clear existing documents before loading
        api_key: Optional API key override for embeddings
    """
    redis_client = get_redis_client()
    file_path = file_path or settings.CLINICAL_NOTES_FILE
    
    try:
        # Check if file exists
        if not Path(file_path).exists():
            logger.warning("Document file not found: %s", file_path)
            return
        
        logger.info("Loading documents from: %s", file_path)
        
        # Clear existing documents if requested
        if clear_existing:
            logger.info("Clearing existing documents from Redis")
            doc_keys = redis_client.smembers("documents")
            if doc_keys:
                redis_client.delete(*[key for key in doc_keys])
            redis_client.delete("documents")
        
        # Load documents
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if not content.strip():
            logger.warning("Document file is empty")
            return
        
        # Split into chunks
        chunks = chunk_text(content)
        logger.info("Created %d chunks from document", len(chunks))
        
        # Store chunks with embeddings in Redis
        stored_count = 0
        for idx, chunk in enumerate(chunks):
            try:
                embedding = get_embeddings(chunk, api_key=api_key)
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
                stored_count += 1
            except Exception as e:
                logger.error("Error storing chunk %d: %s", idx, str(e))
                continue
        
        logger.info("Successfully stored %d document chunks in Redis", stored_count)
        
    except FileNotFoundError:
        logger.error("File not found: %s", file_path)
        raise
    except Exception as e:
        logger.error("Error loading and storing documents: %s", str(e))
        raise

def upload_and_store_document(content: str, document_id: str = None, api_key: Optional[str] = None) -> str:
    """Upload and store a new document in Redis.
    
    Args:
        content: Document content to store
        document_id: Optional document ID (auto-generated if not provided)
        api_key: Optional API key override for embeddings
    
    Returns:
        Document ID
    """
    redis_client = get_redis_client()
    
    if not document_id:
        # Generate document ID based on existing count
        existing_docs = redis_client.smembers("documents")
        document_id = f"doc:{len(existing_docs)}"
    
    try:
        logger.info("Uploading document with ID: %s", document_id)
        
        # Split into chunks
        chunks = chunk_text(content)
        logger.info("Created %d chunks from uploaded document", len(chunks))
        
        # Store chunks
        for idx, chunk in enumerate(chunks):
            embedding = get_embeddings(chunk, api_key=api_key)
            chunk_key = f"{document_id}:chunk:{idx}"
            redis_client.hset(
                chunk_key,
                mapping={
                    "content": chunk,
                    "embedding": json.dumps(embedding),
                    "document_id": document_id
                }
            )
            redis_client.sadd("documents", chunk_key)
            redis_client.sadd(f"doc:{document_id}:chunks", chunk_key)
        
        logger.info("Successfully uploaded document: %s", document_id)
        return document_id
        
    except Exception as e:
        logger.error("Error uploading document: %s", str(e))
        raise

def retrieve_similar_documents(
    query: str, 
    k: int = None, 
    min_similarity: float = None,
    api_key: Optional[str] = None
) -> List[Dict]:
    """Retrieve documents similar to the query.
    
    Args:
        query: Query text
        k: Number of documents to retrieve (defaults to settings.DEFAULT_TOP_K)
        min_similarity: Minimum similarity threshold (defaults to settings.MIN_SIMILARITY_THRESHOLD)
        api_key: Optional API key override for embeddings
    
    Returns:
        List of similar documents with content and similarity scores
    """
    redis_client = get_redis_client()
    k = k or settings.DEFAULT_TOP_K
    min_similarity = min_similarity if min_similarity is not None else settings.MIN_SIMILARITY_THRESHOLD
    
    try:
        logger.debug("Retrieving similar documents for query: %s...", query[:50])
        
        query_embedding = get_embeddings(query, api_key=api_key)
        doc_keys = redis_client.smembers("documents")
        similarities = []
        
        if not doc_keys:
            logger.warning("No documents found in Redis")
            return []
        
        for doc_key in doc_keys:
            try:
                doc_data = redis_client.hgetall(doc_key)
                if b"embedding" in doc_data:
                    stored_embedding = json.loads(doc_data[b"embedding"])
                    similarity = cosine_similarity(query_embedding, stored_embedding)
                    
                    if similarity >= min_similarity:
                        similarities.append({
                            "key": doc_key.decode() if isinstance(doc_key, bytes) else doc_key,
                            "content": doc_data[b"content"].decode("utf-8"),
                            "similarity": similarity
                        })
            except Exception as e:
                logger.warning("Error processing document %s: %s", doc_key, str(e))
                continue
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        results = similarities[:k]
        
        logger.info("Retrieved %d similar documents (min similarity: %.2f)", len(results), min_similarity)
        return results
        
    except Exception as e:
        logger.error("Error retrieving similar documents: %s", str(e))
        raise

def get_document_count() -> int:
    """Get the total number of document chunks stored in Redis.
    
    Returns:
        Number of document chunks
    """
    redis_client = get_redis_client()
    try:
        count = redis_client.scard("documents")
        return count
    except Exception as e:
        logger.error("Error getting document count: %s", str(e))
        return 0

def clear_all_documents() -> bool:
    """Clear all documents from Redis.
    
    Returns:
        True if successful
    """
    redis_client = get_redis_client()
    try:
        doc_keys = redis_client.smembers("documents")
        if doc_keys:
            redis_client.delete(*[key for key in doc_keys])
        redis_client.delete("documents")
        logger.info("Cleared all documents from Redis")
        return True
    except Exception as e:
        logger.error("Error clearing documents: %s", str(e))
        return False

def cosine_similarity(a: list, b: list) -> float:
    """Calculate cosine similarity between two vectors."""
    import math
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x ** 2 for x in a))
    norm_b = math.sqrt(sum(x ** 2 for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0
    return dot_product / (norm_a * norm_b)
