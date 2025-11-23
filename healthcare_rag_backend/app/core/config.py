import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Redis Configuration
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
    VECTOR_STORE_INDEX_NAME = os.getenv("VECTOR_STORE_INDEX_NAME", "healthcare_index")
    
    # Document Configuration
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data" / "clinical_docs"
    CLINICAL_NOTES_FILE = os.getenv(
        "CLINICAL_NOTES_FILE", 
        str(DATA_DIR / "clinical_notes.txt")
    )
    
    # Chunking Configuration
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    # LLM Configuration
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.0"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))
    
    # RAG Configuration
    DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "4"))
    MIN_SIMILARITY_THRESHOLD = float(os.getenv("MIN_SIMILARITY_THRESHOLD", "0.3"))  # Lowered from 0.5 for better retrieval
    
    # API Configuration
    API_TITLE = "Healthcare AI RAG API"
    API_VERSION = "2.0"
    API_DESCRIPTION = "Enhanced RAG-powered API for clinical notes querying"
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8501,http://localhost:3000").split(",")
    
    # Timeout Configuration
    OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "30"))
    REDIS_TIMEOUT = int(os.getenv("REDIS_TIMEOUT", "5"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()
