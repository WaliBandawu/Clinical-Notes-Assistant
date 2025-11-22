from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from healthcare_rag_backend.app.rag.chain import build_chain

router = APIRouter()

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    question: str

@router.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """Process a healthcare question using RAG."""
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Execute RAG chain
        answer = build_chain(request.question)
        
        return QueryResponse(
            question=request.question,
            answer=answer
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
