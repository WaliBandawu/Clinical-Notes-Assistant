import asyncio
from typing import Optional, AsyncIterator
from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletionChunk
from healthcare_rag_backend.app.core.config import settings
from healthcare_rag_backend.app.core.logging_config import logger

# Default clients (using env API key)
def get_client(api_key: Optional[str] = None) -> OpenAI:
    """Get OpenAI client with optional API key override."""
    return OpenAI(
        api_key=api_key or settings.OPENAI_API_KEY,
        timeout=settings.OPENAI_TIMEOUT
    )

def get_async_client(api_key: Optional[str] = None) -> AsyncOpenAI:
    """Get async OpenAI client with optional API key override."""
    return AsyncOpenAI(
        api_key=api_key or settings.OPENAI_API_KEY,
        timeout=settings.OPENAI_TIMEOUT
    )

# Default clients for backward compatibility
client = get_client()
async_client = get_async_client()

def get_llm_response(
    messages: list[dict], 
    model: str = None, 
    temperature: float = None,
    max_tokens: int = None,
    api_key: Optional[str] = None
) -> str:
    """Get response from OpenAI API (synchronous).
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model to use (defaults to settings.DEFAULT_MODEL)
        temperature: Temperature for response generation
        max_tokens: Maximum tokens in response
        api_key: Optional API key override
    
    Returns:
        Response text from the model
    """
    try:
        model = model or settings.DEFAULT_MODEL
        temperature = temperature if temperature is not None else settings.DEFAULT_TEMPERATURE
        max_tokens = max_tokens or settings.MAX_TOKENS
        
        logger.info("Calling OpenAI API with model: %s", model)
        
        client_instance = get_client(api_key)
        response = client_instance.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        content = response.choices[0].message.content
        logger.info("Received response of length: %d", len(content))
        return content
        
    except Exception as e:
        logger.error("Error calling OpenAI API: %s", str(e))
        raise

async def get_llm_response_async(
    messages: list[dict], 
    model: str = None, 
    temperature: float = None,
    max_tokens: int = None,
    api_key: Optional[str] = None
) -> str:
    """Get response from OpenAI API (asynchronous).
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model to use (defaults to settings.DEFAULT_MODEL)
        temperature: Temperature for response generation
        max_tokens: Maximum tokens in response
        api_key: Optional API key override
    
    Returns:
        Response text from the model
    """
    try:
        model = model or settings.DEFAULT_MODEL
        temperature = temperature if temperature is not None else settings.DEFAULT_TEMPERATURE
        max_tokens = max_tokens or settings.MAX_TOKENS
        
        logger.info("Calling OpenAI API (async) with model: %s", model)
        
        async_client_instance = get_async_client(api_key)
        response = await async_client_instance.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        content = response.choices[0].message.content
        logger.info("Received response (async) of length: %d", len(content))
        return content
        
    except Exception as e:
        logger.error("Error calling OpenAI API (async): %s", str(e))
        raise

async def stream_llm_response(
    messages: list[dict], 
    model: str = None, 
    temperature: float = None,
    max_tokens: int = None,
    api_key: Optional[str] = None
) -> AsyncIterator[str]:
    """Stream response from OpenAI API.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model to use (defaults to settings.DEFAULT_MODEL)
        temperature: Temperature for response generation
        max_tokens: Maximum tokens in response
        api_key: Optional API key override
    
    Yields:
        Chunks of response text
    """
    try:
        model = model or settings.DEFAULT_MODEL
        temperature = temperature if temperature is not None else settings.DEFAULT_TEMPERATURE
        max_tokens = max_tokens or settings.MAX_TOKENS
        
        logger.info("Streaming from OpenAI API with model: %s", model)
        
        async_client_instance = get_async_client(api_key)
        stream = await async_client_instance.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        logger.error("Error streaming from OpenAI API: %s", str(e))
        raise

