from openai import OpenAI
from healthcare_rag_backend.app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def get_llm_response(messages: list[dict], model: str = "gpt-4", temperature: float = 0.0) -> str:
    """Get response from OpenAI API.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model to use (default: gpt-4)
        temperature: Temperature for response generation
    
    Returns:
        Response text from the model
    """
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    return response.choices[0].message.content
