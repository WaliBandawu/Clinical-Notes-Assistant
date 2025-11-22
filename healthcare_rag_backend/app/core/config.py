import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    VECTOR_STORE_INDEX_NAME = os.getenv("VECTOR_STORE_INDEX_NAME", "healthcare_index")

settings = Settings()
