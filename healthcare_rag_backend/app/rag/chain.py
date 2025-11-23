import asyncio
from typing import Optional, AsyncIterator
from healthcare_rag_backend.app.rag.retriever import (
    retrieve_similar_documents, 
    load_and_store_documents,
    get_document_count
)
from healthcare_rag_backend.app.core.llm import (
    get_llm_response, 
    get_llm_response_async,
    stream_llm_response
)
from healthcare_rag_backend.app.core.config import settings
from healthcare_rag_backend.app.core.logging_config import logger

# Initialize vector store on startup
def initialize_documents():
    """Initialize documents on application startup."""
    try:
        doc_count = get_document_count()
        if doc_count == 0:
            logger.info("No documents found in Redis, loading default documents...")
            load_and_store_documents()
        else:
            logger.info(f"Found {doc_count} existing document chunks in Redis")
    except Exception as e:
        logger.warning(f"Could not initialize documents: {e}")

def build_chain(
    question: str, 
    k: int = None,
    model: str = None,
    temperature: float = None,
    api_key: Optional[str] = None
) -> str:
    """Build and execute RAG chain (synchronous).
    
    Args:
        question: User's question
        k: Number of documents to retrieve
        model: LLM model to use
        temperature: Temperature for response generation
        api_key: Optional API key override
    
    Returns:
        Response from the LLM
    """
    try:
        k = k or settings.DEFAULT_TOP_K
        
        # 1. Retrieve similar documents
        logger.info("Retrieving documents for question: %s...", question[:50])
        relevant_docs = retrieve_similar_documents(question, k=k, min_similarity=0.0, api_key=api_key)  # Lower threshold for initial retrieval
        
        if not relevant_docs:
            doc_count = get_document_count()
            if doc_count == 0:
                return "No documents are currently loaded in the system. Please upload clinical documents using the 'Upload Documents' feature in the sidebar, or ensure the default document file exists at the configured path."
            else:
                return f"I couldn't find any relevant information in the clinical notes to answer your question. There are {doc_count} document chunks loaded, but none matched your query. Please try:\n1. Rephrasing your question\n2. Using more general terms\n3. Checking if the documents contain the information you're looking for"
        
        # Build context from retrieved documents
        context_parts = []
        for i, doc in enumerate(relevant_docs, 1):
            context_parts.append(f"[Document {i} - Similarity: {doc['similarity']:.2f}]\n{doc['content']}")
        
        context = "\n\n".join(context_parts)
        
        # 2. Build prompt
        system_message = {
            "role": "system",
            "content": """You are a clinical assistant specialized in analyzing medical documentation. 
Use only the context provided from clinical notes to answer questions about healthcare.
If the context doesn't contain enough information to answer the question, say so clearly.
Be precise, professional, and cite which document(s) you're referencing when possible.

Context from clinical notes:
""" + context
        }
        user_message = {
            "role": "user",
            "content": question
        }
        
        # 3. Get response from LLM
        logger.info("Generating response from LLM...")
        response = get_llm_response(
            messages=[system_message, user_message],
            model=model,
            temperature=temperature,
            api_key=api_key
        )
        
        return response
        
    except Exception as e:
        logger.error("Error in RAG chain: %s", str(e))
        raise

async def build_chain_async(
    question: str, 
    k: int = None,
    model: str = None,
    temperature: float = None,
    api_key: Optional[str] = None,
    return_sources: bool = True
):
    """Build and execute RAG chain (asynchronous).
    
    Args:
        question: User's question
        k: Number of documents to retrieve
        model: LLM model to use
        temperature: Temperature for response generation
        api_key: Optional API key override
    
    Returns:
        Response from the LLM
    """
    try:
        k = k or settings.DEFAULT_TOP_K
        
        # 1. Retrieve similar documents (run in thread pool to avoid blocking)
        logger.info("Retrieving documents for question: %s...", question[:50])
        loop = asyncio.get_event_loop()
        relevant_docs = await loop.run_in_executor(
            None, 
            retrieve_similar_documents, 
            question, 
            k,
            0.0,  # Lower threshold for initial retrieval
            api_key
        )
        
        if not relevant_docs:
            doc_count = get_document_count()
            if doc_count == 0:
                error_msg = "No documents are currently loaded in the system. Please upload clinical documents using the 'Upload Documents' feature in the sidebar, or ensure the default document file exists at the configured path."
                if return_sources:
                    return error_msg, []
                return error_msg
            else:
                error_msg = f"I couldn't find any relevant information in the clinical notes to answer your question. There are {doc_count} document chunks loaded, but none matched your query. Please try:\n1. Rephrasing your question\n2. Using more general terms\n3. Checking if the documents contain the information you're looking for"
                if return_sources:
                    return error_msg, []
                return error_msg
        
        # Build context from retrieved documents
        context_parts = []
        for i, doc in enumerate(relevant_docs, 1):
            context_parts.append(f"[Document {i} - Similarity: {doc['similarity']:.2f}]\n{doc['content']}")
        
        context = "\n\n".join(context_parts)
        
        # 2. Build prompt
        system_message = {
            "role": "system",
            "content": """You are a clinical assistant specialized in analyzing medical documentation. 
Use only the context provided from clinical notes to answer questions about healthcare.
If the context doesn't contain enough information to answer the question, say so clearly.
Be precise, professional, and cite which document(s) you're referencing when possible.

Context from clinical notes:
""" + context
        }
        user_message = {
            "role": "user",
            "content": question
        }
        
        # 3. Get response from LLM
        logger.info("Generating response from LLM (async)...")
        response = await get_llm_response_async(
            messages=[system_message, user_message],
            model=model,
            temperature=temperature,
            api_key=api_key
        )
        
        # Prepare sources for return
        sources = []
        if return_sources:
            for doc in relevant_docs:
                sources.append({
                    "content": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
                    "similarity": round(doc["similarity"], 3),
                    "key": doc["key"]
                })
        
        return response, sources
        
    except Exception as e:
        logger.error("Error in RAG chain (async): %s", str(e))
        raise

async def build_chain_stream(
    question: str, 
    k: int = None,
    model: str = None,
    temperature: float = None,
    api_key: Optional[str] = None
) -> AsyncIterator[str]:
    """Build and execute RAG chain with streaming (asynchronous).
    
    Args:
        question: User's question
        k: Number of documents to retrieve
        model: LLM model to use
        temperature: Temperature for response generation
        api_key: Optional API key override
    
    Yields:
        Chunks of response text
    """
    try:
        k = k or settings.DEFAULT_TOP_K
        
        # 1. Retrieve similar documents
        logger.info("Retrieving documents for question: %s...", question[:50])
        loop = asyncio.get_event_loop()
        relevant_docs = await loop.run_in_executor(
            None, 
            retrieve_similar_documents, 
            question, 
            k,
            0.0,  # Lower threshold for initial retrieval
            api_key
        )
        
        if not relevant_docs:
            doc_count = get_document_count()
            if doc_count == 0:
                yield "No documents are currently loaded in the system. Please upload clinical documents using the 'Upload Documents' feature in the sidebar, or ensure the default document file exists at the configured path."
            else:
                yield f"I couldn't find any relevant information in the clinical notes to answer your question. There are {doc_count} document chunks loaded, but none matched your query. Please try:\n1. Rephrasing your question\n2. Using more general terms\n3. Checking if the documents contain the information you're looking for"
            return
        
        # Build context from retrieved documents
        context_parts = []
        for i, doc in enumerate(relevant_docs, 1):
            context_parts.append(f"[Document {i} - Similarity: {doc['similarity']:.2f}]\n{doc['content']}")
        
        context = "\n\n".join(context_parts)
        
        # 2. Build prompt
        system_message = {
            "role": "system",
            "content": """You are a clinical assistant specialized in analyzing medical documentation. 
Use only the context provided from clinical notes to answer questions about healthcare.
If the context doesn't contain enough information to answer the question, say so clearly.
Be precise, professional, and cite which document(s) you're referencing when possible.

Context from clinical notes:
""" + context
        }
        user_message = {
            "role": "user",
            "content": question
        }
        
        # 3. Stream response from LLM
        logger.info("Streaming response from LLM...")
        async for chunk in stream_llm_response(
            messages=[system_message, user_message],
            model=model,
            temperature=temperature,
            api_key=api_key
        ):
            yield chunk
        
    except Exception as e:
        logger.error("Error in RAG chain (stream): %s", str(e))
        yield f"Error: {str(e)}"
