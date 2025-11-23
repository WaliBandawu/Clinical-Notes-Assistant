import streamlit as st
import requests
import json
from datetime import datetime
from typing import List, Dict, Optional

# ----------------------
# Configuration
# ----------------------
API_BASE_URL = "http://localhost:8000/api"  # change to your deployed FastAPI endpoint
API_ASK_URL = f"{API_BASE_URL}/ask"
API_STATUS_URL = f"{API_BASE_URL}/status"
API_HEALTH_URL = f"{API_BASE_URL}/health"
API_UPLOAD_URL = f"{API_BASE_URL}/documents/upload"

# ----------------------
# Page config & CSS
# ----------------------
st.set_page_config(
    page_title="Clinical RAG Assistant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
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
    """,
    unsafe_allow_html=True,
)

# ----------------------
# Session state defaults
# ----------------------
if "messages" not in st.session_state:
    st.session_state.messages: List[Dict] = []

if "document_count" not in st.session_state:
    st.session_state.document_count = 0

if "api_key" not in st.session_state:
    st.session_state.api_key = ""

if "suggestions" not in st.session_state:
    st.session_state.suggestions = []

if "document_list" not in st.session_state:
    st.session_state.document_list = []

if "show_documents" not in st.session_state:
    st.session_state.show_documents = False

# ----------------------
# Helper functions
# ----------------------
def validate_api_key_on_server(api_key: str) -> Dict:
    """Call backend endpoint to validate API key (backend should implement this)."""
    resp = requests.post(f"{API_BASE_URL}/validate-api-key", params={"api_key": api_key}, timeout=10)
    resp.raise_for_status()
    return resp.json()


def check_health() -> Optional[Dict]:
    """Get health info from backend. Returns None on connection error."""
    try:
        resp = requests.get(API_HEALTH_URL, timeout=3)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def reload_documents(api_key: Optional[str] = None) -> Dict:
    params = {}
    if api_key:
        params["api_key"] = api_key
    resp = requests.post(f"{API_BASE_URL}/documents/reload", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def upload_document_to_api(uploaded_file, api_key: Optional[str] = None) -> Dict:
    files = {"file": (uploaded_file.name, uploaded_file.read(), "text/plain")}
    params = {}
    if api_key:
        params["api_key"] = api_key
    resp = requests.post(API_UPLOAD_URL, files=files, params=params, timeout=60)
    resp.raise_for_status()
    return resp.json()


def list_documents(limit: int = 50) -> Dict:
    resp = requests.get(f"{API_BASE_URL}/documents/list", params={"limit": limit}, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_suggestions_from_api() -> List[str]:
    resp = requests.get(f"{API_BASE_URL}/suggestions", timeout=10)
    resp.raise_for_status()
    return resp.json().get("suggestions", [])


def ask_question_stream(payload: Dict, timeout: int = 60):
    """Send question to API with streaming. Returns a generator of chunks (strings)."""
    stream_url = f"{API_BASE_URL}/ask/stream"
    resp = requests.post(stream_url, json=payload, stream=True, timeout=timeout)
    resp.raise_for_status()
    for chunk in resp.iter_content(chunk_size=None, decode_unicode=True):
        if chunk:
            yield chunk


def ask_question(payload: Dict, timeout: int = 60) -> Dict:
    """Send question to API without streaming. Returns the JSON response dict."""
    resp = requests.post(API_ASK_URL, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


# ----------------------
# Sidebar UI
# ----------------------
with st.sidebar:
    st.header("⚙️ Settings")

    st.subheader("🔑 API Configuration")
    api_key_input = st.text_input(
        "OpenAI API Key",
        value=st.session_state.api_key,
        type="password",
        help="Enter your OpenAI API key. Leave empty to use server's default key.",
        placeholder="sk-...",
    )

    if api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input
        if api_key_input:
            st.success("✅ API key saved (not stored permanently)")
        else:
            st.info("ℹ️ Using server's default API key")

    if st.session_state.api_key:
        masked_key = (
            st.session_state.api_key[:7] + "..." + st.session_state.api_key[-4:]
            if len(st.session_state.api_key) > 11
            else "***"
        )
        st.caption(f"Using: {masked_key}")

        if st.button("🔍 Validate API Key", use_container_width=True):
            try:
                with st.spinner("Validating API key..."):
                    result = validate_api_key_on_server(st.session_state.api_key)
                    if result.get("valid"):
                        st.success(f"✅ Valid API key! Model: {result.get('model', 'N/A')}")
                    else:
                        st.error(f"❌ {result.get('message', 'Invalid API key')}")
            except Exception as e:
                st.error(f"❌ Validation error: {e}")

    st.divider()

    # Health check
    st.subheader("🔎 API Health")
    health_data = check_health()
    if health_data:
        status_icon = "🟢" if health_data.get("status") == "healthy" else "🟡"
        st.markdown(f"{status_icon} **Status:** {health_data.get('status', 'unknown').title()}")
        st.session_state.document_count = health_data.get("document_count", st.session_state.document_count)
        st.info(f"📄 **Documents:** {st.session_state.document_count} chunks indexed")
    else:
        st.error("❌ Cannot connect to API")

    st.divider()

    # Document Management
    st.subheader("📄 Document Management")

    if st.button("🔄 Reload Default Documents", use_container_width=True, help="Reload documents from the default file path"):
        try:
            with st.spinner("Reloading documents..."):
                result = reload_documents(st.session_state.api_key or None)
                st.success(f"✅ {result.get('message', 'Documents reloaded successfully')}")
                st.info(f"📄 Loaded {result.get('document_count', 0)} chunks from: {result.get('file_path', 'default path')}")
                st.rerun()
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Reload failed: {e}")
        except Exception as e:
            st.error(f"⚠️ Error: {e}")

    st.divider()

    st.subheader("📤 Upload Documents")
    uploaded_file = st.file_uploader("Upload a clinical document", type=["txt", "md"], help="Upload a text file containing clinical notes")

    if uploaded_file is not None:
        if st.button("Upload & Index"):
            try:
                with st.spinner("Uploading and indexing document..."):
                    result = upload_document_to_api(uploaded_file, st.session_state.api_key or None)
                    st.success(f"✅ {result.get('message', 'Document uploaded successfully')}")
                    st.info(f"Created {result.get('chunks_created', 0)} chunks")
                    st.rerun()
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Upload failed: {e}")
            except Exception as e:
                st.error(f"⚠️ Error: {e}")

    st.divider()

    # Conversation management
    st.subheader("💬 Conversation")

    if len(st.session_state.messages) > 0:
        conversation_json = json.dumps(st.session_state.messages, indent=2)
        st.download_button(
            "📥 Export Conversation",
            conversation_json,
            file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
        )

    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    # Model settings
    st.subheader("🤖 Model Settings")
    use_streaming = st.checkbox("Stream responses", value=False, help="Enable streaming for faster initial response")
    top_k = st.slider("Top K documents", min_value=1, max_value=10, value=4, help="Number of documents to retrieve")

    st.divider()

    st.subheader("📋 Documents")
    if st.button("📄 View All Documents", use_container_width=True):
        try:
            with st.spinner("Loading documents..."):
                result = list_documents(limit=50)
                st.session_state.document_list = result.get("documents", [])
                st.session_state.show_documents = True
                st.rerun()
        except Exception as e:
            st.error(f"❌ Error loading documents: {e}")

    st.divider()
    st.subheader("ℹ️ API Info")
    st.caption(f"Backend: {API_BASE_URL}")
    if st.button("🔄 Refresh Status"):
        st.rerun()

    st.divider()
    st.subheader("💡 Suggestions")
    if st.button("🎲 Get Query Suggestions", use_container_width=True):
        try:
            suggestions = get_suggestions_from_api()
            st.session_state.suggestions = suggestions
        except Exception as e:
            st.error(f"❌ Error: {e}")

    if st.session_state.suggestions:
        for i, suggestion in enumerate(st.session_state.suggestions[:5]):
            # Use unique key per suggestion
            if st.button(suggestion, key=f"sugg_{i}", use_container_width=True):
                st.session_state.suggested_query = suggestion
                st.rerun()

# ----------------------
# Main UI
# ----------------------
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

# If a suggested query exists, use it
if "suggested_query" in st.session_state:
    prompt = st.session_state.suggested_query
    del st.session_state.suggested_query
else:
    prompt = None

# Chat input
user_input = prompt or st.chat_input("Ask a question about the clinical notes...")

if user_input:
    # add user message
    user_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.messages.append({"role": "user", "content": user_input, "timestamp": user_timestamp})

    # show the user message immediately in the chat UI
    with st.chat_message("user"):
        st.markdown(user_input)

    # assistant response
    with st.chat_message("assistant"):
        try:
            # Prepare payload
            request_payload = {"question": user_input, "k": top_k}
            if st.session_state.api_key:
                request_payload["api_key"] = st.session_state.api_key

            # -------------------------
            # STREAMING MODE
            # -------------------------
            if use_streaming:
                with st.spinner("Thinking..."):
                    full_answer = ""
                    answer_placeholder = st.empty()

                    # Stream chunks as they come
                    for chunk in ask_question_stream(request_payload, timeout=120):
                        full_answer += chunk
                        answer_placeholder.markdown(full_answer + "▌")

                    answer_placeholder.markdown(full_answer)
                    answer = full_answer
                    sources = []

            # -------------------------
            # NON-STREAMING MODE
            # -------------------------
            else:
                with st.spinner("Thinking..."):
                    result = ask_question(request_payload, timeout=120)
                    
                    answer = result.get("answer", "No answer received.")
                    st.markdown(answer)

                    sources = result.get("sources", [])

            # -------------------------
            # SAVE ASSISTANT MESSAGE
            # -------------------------
            assistant_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            msg = {
                "role": "assistant",
                "content": answer,
                "timestamp": assistant_timestamp,
            }
            if sources:
                msg["sources"] = sources
            st.session_state.messages.append(msg)

            # -------------------------
            # SHOW SOURCES (NON-STREAMING)
            # -------------------------
            if sources:
                with st.expander(f"📚 Sources ({len(sources)} documents used)", expanded=False):
                    for i, source in enumerate(sources, 1):
                        similarity = source.get("similarity", 0)

                        st.markdown(f"**Source {i}** (Similarity: {similarity:.1%})")
                        st.text_area(
                            "Content preview",
                            value=source.get("content", ""),
                            height=100,
                            key=f"source_{i}_{assistant_timestamp}",
                            disabled=True,
                            label_visibility="collapsed",
                        )
                        st.caption(f"Key: `{source.get('key', 'N/A')}`")

                # -------------------------
                # FEEDBACK
                # -------------------------
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("👍 Helpful", key=f"positive_{assistant_timestamp}"):
                        try:
                            requests.post(
                                f"{API_BASE_URL}/feedback",
                                json={"question": user_input, "answer": answer, "feedback": "positive"},
                                timeout=5,
                            )
                            st.success("Thank you! 🙌")
                        except Exception:
                            st.warning("⚠️ Could not send feedback.")

                with col2:
                    if st.button("👎 Not Helpful", key=f"negative_{assistant_timestamp}"):
                        try:
                            requests.post(
                                f"{API_BASE_URL}/feedback",
                                json={"question": user_input, "answer": answer, "feedback": "negative"},
                                timeout=5,
                            )
                            st.info("Thanks for letting us know.")
                        except Exception:
                            st.warning("⚠️ Could not send feedback.")

        # -------------------------
        # ERROR HANDLING
        # -------------------------
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

# ----------------------
# Show documents list if requested
# ----------------------
if st.session_state.show_documents:
    st.subheader("📄 Loaded Documents")
    if st.session_state.document_list:
        for doc in st.session_state.document_list:
            with st.expander(f"Document: {doc.get('key', 'Unknown')}"):
                st.text(doc.get("content_preview", ""))
                if doc.get("document_id"):
                    st.caption(f"Document ID: {doc.get('document_id')}")
    else:
        st.info("No documents loaded.")
    if st.button("Close Document List"):
        st.session_state.show_documents = False
        st.rerun()

# ----------------------
# Example questions
# ----------------------
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
                st.session_state.suggested_query = question
                st.rerun()
