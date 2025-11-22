from healthcare_rag_backend.app.rag.retriever import retrieve_similar_documents, load_and_store_documents
from healthcare_rag_backend.app.core.llm import get_llm_response

# Initialize vector store on startup
try:
    load_and_store_documents()
except Exception as e:
    print(f"Warning: Could not load documents: {e}")

def build_chain(question: str) -> str:
    """Build and execute RAG chain.
    
    Args:
        question: User's question
    
    Returns:
        Response from the LLM
    """
    # 1. Retrieve similar documents
    relevant_docs = retrieve_similar_documents(question, k=4)
    context = "\n\n".join([doc["content"] for doc in relevant_docs])
    
    # 2. Build prompt
    system_message = {
        "role": "system",
        "content": "You are a clinical assistant. Use only the context provided to answer questions about healthcare.\n\nContext:\n" + context
    }
    user_message = {
        "role": "user",
        "content": question
    }
    
    # 3. Get response from LLM
    response = get_llm_response(
        messages=[system_message, user_message],
        model="gpt-4",
        temperature=0.0
    )
    
    return response
