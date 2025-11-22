from fastapi import FastAPI
from healthcare_rag_backend.app.api.routes import router

app = FastAPI(
    title="Healthcare AI RAG API",
    version="1.0"
)

app.include_router(router, prefix="/api")
