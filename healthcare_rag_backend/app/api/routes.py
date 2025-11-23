from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
from healthcare_rag_backend.app.rag.chain import (
    build_chain_async, 
    build_chain_stream
)
from healthcare_rag_backend.app.rag.retriever import (
    upload_and_store_document,
    get_document_count,
    clear_all_documents
)
from healthcare_rag_backend.app.core.logging_config import logger

router = APIRouter()

# Request/Response Models
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The question to ask about clinical notes")
    k: Optional[int] = Field(None, ge=1, le=20, description="Number of documents to retrieve")
    model: Optional[str] = Field(None, description="LLM model to use")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Temperature for response generation")
    stream: Optional[bool] = Field(False, description="Whether to stream the response")
    api_key: Optional[str] = Field(None, description="Optional OpenAI API key override")

class SourceDocument(BaseModel):
    content: str
    similarity: float
    key: str

class QueryResponse(BaseModel):
    answer: str
    question: str
    document_count: Optional[int] = None
    sources: Optional[list[SourceDocument]] = None

class DocumentUploadResponse(BaseModel):
    document_id: str
    chunks_created: int
    message: str

class HealthResponse(BaseModel):
    status: str
    document_count: int
    redis_connected: bool

class StatusResponse(BaseModel):
    document_count: int
    redis_connected: bool

class DocumentInfo(BaseModel):
    key: str
    content_preview: str
    document_id: Optional[str] = None

class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo]
    total_count: int

class ApiKeyValidationResponse(BaseModel):
    valid: bool
    message: str
    model: Optional[str] = None

class FeedbackRequest(BaseModel):
    question: str
    answer: str
    feedback: str = Field(..., description="'positive' or 'negative'")
    comment: Optional[str] = None

class FeedbackResponse(BaseModel):
    message: str
    feedback_id: str

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        from healthcare_rag_backend.app.rag.retriever import get_redis_client
        redis_client = get_redis_client()
        redis_client.ping()
        redis_connected = True
    except Exception as e:
        logger.error("Redis health check failed: %s", str(e))
        redis_connected = False
    
    doc_count = get_document_count()
    
    status = "healthy" if redis_connected else "degraded"
    
    return HealthResponse(
        status=status,
        document_count=doc_count,
        redis_connected=redis_connected
    )

@router.get("/status", response_model=StatusResponse)
async def get_status():
    """Get application status."""
    try:
        from healthcare_rag_backend.app.rag.retriever import get_redis_client
        redis_client = get_redis_client()
        redis_client.ping()
        redis_connected = True
    except Exception:
        redis_connected = False
    
    doc_count = get_document_count()
    
    return StatusResponse(
        document_count=doc_count,
        redis_connected=redis_connected
    )

@router.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """Process a healthcare question using RAG."""
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Execute RAG chain asynchronously
        answer, sources = await build_chain_async(
            question=request.question,
            k=request.k,
            model=request.model,
            temperature=request.temperature,
            api_key=request.api_key,
            return_sources=True
        )
        
        doc_count = get_document_count()
        
        return QueryResponse(
            question=request.question,
            answer=answer,
            document_count=doc_count,
            sources=sources
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing question: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e

@router.post("/ask/stream")
async def ask_question_stream(request: QueryRequest):
    """Process a healthcare question using RAG with streaming response."""
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        async def generate():
            async for chunk in build_chain_stream(
                question=request.question,
                k=request.k,
                model=request.model,
                temperature=request.temperature,
                api_key=request.api_key
            ):
                yield chunk
        
        return StreamingResponse(generate(), media_type="text/plain")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error streaming response: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e

@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    api_key: Optional[str] = Query(None, description="Optional OpenAI API key override")
):
    """Upload and index a new clinical document."""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        # Read file content
        content = await file.read()
        try:
            text_content = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text") from exc
        
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Upload and store document
        document_id = upload_and_store_document(text_content, document_id=file.filename, api_key=api_key)
        
        # Get chunk count for this document
        from healthcare_rag_backend.app.rag.retriever import get_redis_client
        redis_client = get_redis_client()
        chunk_keys = redis_client.smembers(f"doc:{document_id}:chunks")
        chunks_created = len(chunk_keys) if chunk_keys else 0
        
        logger.info("Uploaded document: %s with %d chunks", document_id, chunks_created)
        
        return DocumentUploadResponse(
            document_id=document_id,
            chunks_created=chunks_created,
            message=f"Document '{file.filename}' uploaded and indexed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error uploading document: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}") from e

@router.post("/documents/upload-text", response_model=DocumentUploadResponse)
async def upload_document_text(
    content: str = Query(..., min_length=1),
    document_id: str = Query(None),
    api_key: Optional[str] = Query(None, description="Optional OpenAI API key override")
):
    """Upload and index document content as text."""
    try:
        if not content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        
        # Upload and store document
        doc_id = upload_and_store_document(content, document_id=document_id, api_key=api_key)
        
        # Get chunk count
        from healthcare_rag_backend.app.rag.retriever import get_redis_client
        redis_client = get_redis_client()
        chunk_keys = redis_client.smembers(f"doc:{doc_id}:chunks")
        chunks_created = len(chunk_keys) if chunk_keys else 0
        
        logger.info("Uploaded text document: %s with %d chunks", doc_id, chunks_created)
        
        return DocumentUploadResponse(
            document_id=doc_id,
            chunks_created=chunks_created,
            message="Document uploaded and indexed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error uploading text document: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}") from e

@router.delete("/documents/clear")
async def clear_documents():
    """Clear all documents from the vector store."""
    try:
        success = clear_all_documents()
        if success:
            return {"message": "All documents cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear documents")
    except Exception as e:
        logger.error("Error clearing documents: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error clearing documents: {str(e)}") from e

@router.post("/documents/reload")
async def reload_documents(api_key: Optional[str] = Query(None, description="Optional OpenAI API key override")):
    """Reload documents from the default file path."""
    try:
        from healthcare_rag_backend.app.rag.retriever import load_and_store_documents
        from healthcare_rag_backend.app.core.config import settings
        
        # Check if file exists
        from pathlib import Path
        file_path = settings.CLINICAL_NOTES_FILE
        
        if not Path(file_path).exists():
            raise HTTPException(
                status_code=404, 
                detail=f"Document file not found at: {file_path}. Please upload a document or ensure the file exists."
            )
        
        # Clear and reload
        load_and_store_documents(clear_existing=True, api_key=api_key)
        doc_count = get_document_count()
        
        return {
            "message": "Documents reloaded successfully",
            "document_count": doc_count,
            "file_path": file_path
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error reloading documents: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error reloading documents: {str(e)}") from e

@router.get("/documents/list", response_model=DocumentListResponse)
async def list_documents(limit: int = Query(20, ge=1, le=100)):
    """List all document chunks with previews."""
    try:
        from healthcare_rag_backend.app.rag.retriever import get_redis_client
        redis_client = get_redis_client()
        
        doc_keys = list(redis_client.smembers("documents"))[:limit]
        documents = []
        
        for doc_key in doc_keys:
            try:
                doc_data = redis_client.hgetall(doc_key)
                if b"content" in doc_data:
                    content = doc_data[b"content"].decode("utf-8")
                    key_str = doc_key.decode() if isinstance(doc_key, bytes) else doc_key
                    document_id = doc_data.get(b"document_id")
                    
                    documents.append(DocumentInfo(
                        key=key_str,
                        content_preview=content[:200] + "..." if len(content) > 200 else content,
                        document_id=document_id.decode("utf-8") if document_id else None
                    ))
            except Exception as e:
                logger.warning("Error processing document %s: %s", doc_key, str(e))
                continue
        
        total_count = redis_client.scard("documents")
        
        return DocumentListResponse(
            documents=documents,
            total_count=total_count
        )
    except Exception as e:
        logger.error("Error listing documents: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}") from e

@router.delete("/documents/{document_key}")
async def delete_document(document_key: str):
    """Delete a specific document chunk."""
    try:
        from healthcare_rag_backend.app.rag.retriever import get_redis_client
        redis_client = get_redis_client()
        
        # Check if document exists
        if not redis_client.exists(document_key):
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Remove from documents set
        redis_client.srem("documents", document_key)
        
        # Delete the document
        redis_client.delete(document_key)
        
        logger.info("Deleted document: %s", document_key)
        return {"message": f"Document {document_key} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting document: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}") from e

@router.post("/validate-api-key", response_model=ApiKeyValidationResponse)
async def validate_api_key(api_key: str = Query(..., description="OpenAI API key to validate")):
    """Validate an OpenAI API key."""
    try:
        from healthcare_rag_backend.app.core.llm import get_client
        
        client = get_client(api_key)
        
        # Try a simple API call to validate the key
        try:
            response = client.models.list()
            # If successful, get the first available model
            model_name = "gpt-4" if any(m.id.startswith("gpt-4") for m in response.data) else "gpt-3.5-turbo"
            
            return ApiKeyValidationResponse(
                valid=True,
                message="API key is valid",
                model=model_name
            )
        except Exception as e:
            error_msg = str(e)
            if "Invalid API key" in error_msg or "Incorrect API key" in error_msg:
                return ApiKeyValidationResponse(
                    valid=False,
                    message="Invalid API key"
                )
            else:
                return ApiKeyValidationResponse(
                    valid=False,
                    message=f"API key validation failed: {error_msg}"
                )
    except Exception as e:
        logger.error("Error validating API key: %s", str(e), exc_info=True)
        return ApiKeyValidationResponse(
            valid=False,
            message=f"Error validating API key: {str(e)}"
        )

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """Submit feedback for a query response."""
    try:
        import uuid
        from datetime import datetime
        
        feedback_id = str(uuid.uuid4())
        
        # In a production system, you'd store this in a database
        # For now, we'll just log it
        logger.info(
            "Feedback received - ID: %s, Type: %s, Question: %s, Comment: %s",
            feedback_id,
            request.feedback,
            request.question[:50],
            request.comment
        )
        
        return FeedbackResponse(
            message="Thank you for your feedback!",
            feedback_id=feedback_id
        )
    except Exception as e:
        logger.error("Error submitting feedback: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}") from e

@router.get("/suggestions")
async def get_query_suggestions():
    """Get suggested questions based on loaded documents."""
    try:
        # Common healthcare questions
        suggestions = [
            "What medications was the patient prescribed?",
            "What are the patient's vital signs?",
            "What is the diagnosis?",
            "What treatment plan was recommended?",
            "What are the patient's symptoms?",
            "What are the lab results?",
            "What is the patient's medical history?",
            "What procedures were performed?",
            "What are the discharge instructions?",
            "What follow-up care is needed?"
        ]
        
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error("Error getting suggestions: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting suggestions: {str(e)}") from e
