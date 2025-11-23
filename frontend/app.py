import streamlit as st
import requests
import json
from datetime import datetime
from typing import List, Dict

# Backend URL (change to your deployed FastAPI endpoint)
API_BASE_URL = "http://localhost:8000/api"
API_ASK_URL = f"{API_BASE_URL}/ask"
API_STATUS_URL = f"{API_BASE_URL}/status"
API_HEALTH_URL = f"{API_BASE_URL}/health"
API_UPLOAD_URL = f"{API_BASE_URL}/documents/upload"

# Page configuration
st.set_page_config(
    page_title="Clinical RAG Assistant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f1f8e9;
        border-left: 4px solid #4caf50;
    }
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 5px;
    }
    .status-online {
        background-color: #4caf50;
    }
    .status-offline {
        background-color: #f44336;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages: List[Dict] = []

if "document_count" not in st.session_state:
    st.session_state.document_count = 0

if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # API Key Configuration
    st.subheader("🔑 API Configuration")
    api_key_input = st.text_input(
        "OpenAI API Key",
        value=st.session_state.api_key,
        type="password",
        help="Enter your OpenAI API key. Leave empty to use server's default key.",
        placeholder="sk-..."
    )
    
    if api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input
        if api_key_input:
            st.success("✅ API key saved (not stored permanently)")
        else:
            st.info("ℹ️ Using server's default API key")
    
    if st.session_state.api_key:
        # Show masked key
        masked_key = st.session_state.api_key[:7] + "..." + st.session_state.api_key[-4:] if len(st.session_state.api_key) > 11 else "***"
        st.caption(f"Using: {masked_key}")
        
        # Validate API key button
        if st.button("🔍 Validate API Key", use_container_width=True):
            try:
                with st.spinner("Validating API key..."):
                    response = requests.post(
                        f"{API_BASE_URL}/validate-api-key",
                        params={"api_key": st.session_state.api_key}
                    )
                    response.raise_for_status()
                    result = response.json()
                    if result.get("valid"):
                        st.success(f"✅ Valid API key! Model: {result.get('model', 'N/A')}")
                    else:
                        st.error(f"❌ {result.get('message', 'Invalid API key')}")
            except Exception as e:
                st.error(f"❌ Validation error: {e}")
    
    st.divider()
    
    # Health check
    try:
        health_response = requests.get(API_HEALTH_URL, timeout=2)
        if health_response.status_code == 200:
            health_data = health_response.json()
            status_icon = "🟢" if health_data.get("status") == "healthy" else "🟡"
            st.markdown(f"{status_icon} **Status:** {health_data.get('status', 'unknown').title()}")
            st.session_state.document_count = health_data.get("document_count", 0)
            st.info(f"📄 **Documents:** {st.session_state.document_count} chunks indexed")
        else:
            st.error("❌ API is not responding")
    except:
        st.error("❌ Cannot connect to API")
    
    st.divider()
    
    # Document Management
    st.subheader("📄 Document Management")
    
    # Reload documents button
    if st.button("🔄 Reload Default Documents", use_container_width=True, help="Reload documents from the default file path"):
        try:
            with st.spinner("Reloading documents..."):
                params = {}
                if st.session_state.api_key:
                    params["api_key"] = st.session_state.api_key
                response = requests.post(f"{API_BASE_URL}/documents/reload", params=params)
                response.raise_for_status()
                result = response.json()
                st.success(f"✅ {result.get('message', 'Documents reloaded successfully')}")
                st.info(f"📄 Loaded {result.get('document_count', 0)} chunks from: {result.get('file_path', 'default path')}")
                st.rerun()
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Reload failed: {e}")
        except Exception as e:
            st.error(f"⚠️ Error: {e}")
    
    st.divider()
    
    # Document upload
    st.subheader("📤 Upload Documents")
    uploaded_file = st.file_uploader(
        "Upload a clinical document",
        type=["txt", "md"],
        help="Upload a text file containing clinical notes"
    )
    
    if uploaded_file is not None:
        if st.button("Upload & Index"):
            try:
                with st.spinner("Uploading and indexing document..."):
                    files = {"file": (uploaded_file.name, uploaded_file.read(), "text/plain")}
                    params = {}
                    if st.session_state.api_key:
                        params["api_key"] = st.session_state.api_key
                    response = requests.post(API_UPLOAD_URL, files=files, params=params)
                    response.raise_for_status()
                    result = response.json()
                    st.success(f"✅ {result.get('message', 'Document uploaded successfully')}")
                    st.info(f"Created {result.get('chunks_created', 0)} chunks")
                    # Refresh status
                    st.rerun()
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Upload failed: {e}")
            except Exception as e:
                st.error(f"⚠️ Error: {e}")
    
    st.divider()
    
    # Conversation management
    st.subheader("💬 Conversation")
    
    # Export conversation
    if len(st.session_state.messages) > 0:
        conversation_json = json.dumps(st.session_state.messages, indent=2)
        st.download_button(
            "📥 Export Conversation",
            conversation_json,
            file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    # Clear conversation
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    # Model settings
    st.subheader("🤖 Model Settings")
    use_streaming = st.checkbox("Stream responses", value=False, help="Enable streaming for faster initial response")
    top_k = st.slider("Top K documents", min_value=1, max_value=10, value=4, help="Number of documents to retrieve")
    
    st.divider()
    
    # Document Management
    st.subheader("📋 Documents")
    if st.button("📄 View All Documents", use_container_width=True):
        try:
            with st.spinner("Loading documents..."):
                response = requests.get(f"{API_BASE_URL}/documents/list", params={"limit": 50})
                response.raise_for_status()
                result = response.json()
                st.session_state.document_list = result.get("documents", [])
                st.session_state.show_documents = True
                st.rerun()
        except Exception as e:
            st.error(f"❌ Error loading documents: {e}")
    
    # API Info
    st.subheader("ℹ️ API Info")
    st.caption(f"Backend: {API_BASE_URL}")
    if st.button("🔄 Refresh Status"):
        st.rerun()
    
    # Query Suggestions
    st.divider()
    st.subheader("💡 Suggestions")
    if st.button("🎲 Get Query Suggestions", use_container_width=True):
        try:
            response = requests.get(f"{API_BASE_URL}/suggestions")
            response.raise_for_status()
            suggestions = response.json().get("suggestions", [])
            st.session_state.suggestions = suggestions
        except Exception as e:
            st.error(f"❌ Error: {e}")
    
    if "suggestions" in st.session_state and st.session_state.suggestions:
        for suggestion in st.session_state.suggestions[:5]:  # Show first 5
            if st.button(suggestion, key=f"sugg_{suggestion[:20]}", use_container_width=True):
                # This will trigger a query when chat input is available
                st.session_state.suggested_query = suggestion
                st.rerun()

# Main content
st.markdown('<div class="main-header">🩺 Clinical Notes Assistant</div>', unsafe_allow_html=True)
st.markdown("Ask questions about clinical notes using AI-powered retrieval augmented generation.")

# Display conversation history
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        role = message.get("role")
        content = message.get("content")
        timestamp = message.get("timestamp", "")
        
        if role == "user":
            with st.chat_message("user"):
                st.markdown(f"**You:** {content}")
                if timestamp:
                    st.caption(timestamp)
        elif role == "assistant":
            with st.chat_message("assistant"):
                st.markdown(f"**Assistant:** {content}")
                if timestamp:
                    st.caption(timestamp)

# Handle suggested query
if "suggested_query" in st.session_state:
    prompt = st.session_state.suggested_query
    del st.session_state.suggested_query
else:
    prompt = None

# Chat input
if prompt := prompt or st.chat_input("Ask a question about the clinical notes..."):
    # Add user message to history
    user_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "timestamp": user_timestamp
    })
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get assistant response
    with st.chat_message("assistant"):
        try:
            # Prepare request payload
            request_payload = {
                "question": prompt,
                "k": top_k
            }
            if st.session_state.api_key:
                request_payload["api_key"] = st.session_state.api_key
            
            if use_streaming:
                # Streaming response
                with st.spinner("Thinking..."):
                    stream_url = f"{API_BASE_URL}/ask/stream"
                    response = requests.post(
                        stream_url,
                        json=request_payload,
                        stream=True,
                        timeout=60
                    )
                    response.raise_for_status()
                    
                    answer_placeholder = st.empty()
                    full_answer = ""
                    
                    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                        if chunk:
                            full_answer += chunk
                            answer_placeholder.markdown(full_answer + "▌")
                    
                    answer_placeholder.markdown(full_answer)
                    answer = full_answer
            else:
                # Regular response
        with st.spinner("Thinking..."):
                    response = requests.post(
                        API_ASK_URL,
                        json=request_payload,
                        timeout=60
                    )
            response.raise_for_status()
                    result = response.json()
                    answer = result.get("answer", "No answer received.")
                    st.markdown(answer)
                    
                    # Get sources if available (for non-streaming)
                    sources = result.get("sources", [])
            
            # Add assistant message to history
            assistant_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message_data = {
                "role": "assistant",
                "content": answer,
                "timestamp": assistant_timestamp
            }
            if sources:
                message_data["sources"] = sources
            st.session_state.messages.append(message_data)
            
            # Display sources if available
            if sources and len(sources) > 0:
                with st.expander(f"📚 Sources ({len(sources)} documents used)", expanded=False):
                    for i, source in enumerate(sources, 1):
                        similarity = source.get('similarity', 0)
                        st.markdown(f"**Source {i}** (Similarity: {similarity:.1%})")
                        st.text_area(
                            "Content preview",
                            value=source.get("content", ""),
                            height=100,
                            key=f"source_{i}_{assistant_timestamp}",
                            disabled=True,
                            label_visibility="collapsed"
                        )
                        st.caption(f"Key: `{source.get('key', 'N/A')}`")
                
                # Feedback buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("👍 Helpful", key=f"feedback_pos_{assistant_timestamp}", use_container_width=True):
                        try:
                            requests.post(
                                f"{API_BASE_URL}/feedback",
                                json={
                                    "question": prompt,
                                    "answer": answer,
                                    "feedback": "positive"
                                }
                            )
                            st.success("✅ Thank you for your feedback!")
                        except:
                            pass
                with col2:
                    if st.button("👎 Not Helpful", key=f"feedback_neg_{assistant_timestamp}", use_container_width=True):
                        try:
                            requests.post(
                                f"{API_BASE_URL}/feedback",
                                json={
                                    "question": prompt,
                                    "answer": answer,
                                    "feedback": "negative"
                                }
                            )
                            st.info("💬 Thank you for your feedback!")
                        except:
                            pass
            
        except requests.exceptions.Timeout:
            error_msg = "⏱️ Request timed out. Please try again."
            st.error(error_msg)
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    except requests.exceptions.RequestException as e:
            error_msg = f"❌ API error: {str(e)}"
            st.error(error_msg)
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    except Exception as e:
            error_msg = f"⚠️ Unexpected error: {str(e)}"
            st.error(error_msg)
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

# Show document list if requested
if "show_documents" in st.session_state and st.session_state.show_documents:
    st.subheader("📄 Loaded Documents")
    if "document_list" in st.session_state:
        for doc in st.session_state.document_list:
            with st.expander(f"Document: {doc.get('key', 'Unknown')}"):
                st.text(doc.get("content_preview", ""))
                if doc.get("document_id"):
                    st.caption(f"Document ID: {doc.get('document_id')}")
    if st.button("Close Document List"):
        st.session_state.show_documents = False
        st.rerun()
    st.divider()

# Example questions
if len(st.session_state.messages) == 0:
    st.info("💡 **Example questions:**")
    example_questions = [
        "What medications was the patient prescribed?",
        "What are the patient's vital signs?",
        "What is the diagnosis?",
        "What treatment plan was recommended?",
        "What are the patient's symptoms?",
    ]
    
    cols = st.columns(2)
    for i, question in enumerate(example_questions):
        with cols[i % 2]:
            if st.button(question, key=f"example_{i}", use_container_width=True):
                st.rerun()
