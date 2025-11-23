# 🩺 Clinical Notes Assistant

<div align="center">

**An intelligent RAG-powered healthcare assistant for querying clinical notes using Redis vector storage and OpenAI**

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Docker Deployment](#-docker-deployment)
- [Contributing](#-contributing)

---

## 🎯 Overview

The **Clinical Notes Assistant** is a Retrieval Augmented Generation (RAG) system designed to help healthcare professionals quickly query and extract information from clinical documentation. By leveraging Redis as a vector database and OpenAI's embedding models, the system provides accurate, context-aware responses to medical queries.

### Key Capabilities

- 🔍 **Semantic Search**: Find relevant clinical information using vector similarity search
- 💬 **Natural Language Queries**: Ask questions in plain English about clinical notes
- 🧠 **Context-Aware Responses**: Get answers based on actual clinical documentation
- ⚡ **Fast Retrieval**: Redis-powered vector storage for efficient similarity search
- 🎨 **User-Friendly Interface**: Clean Streamlit frontend for easy interaction

---

## ✨ Features

### Core Features
- **Document Processing**: Automatically chunks and indexes clinical documents
- **Vector Embeddings**: Uses OpenAI's `text-embedding-3-small` for semantic understanding
- **RAG Pipeline**: Retrieves relevant context before generating responses
- **RESTful API**: FastAPI backend with comprehensive error handling
- **Interactive UI**: Streamlit-based web interface for seamless user experience
- **Scalable Architecture**: Docker-ready for easy deployment

### Enhanced Features (v2.0)
- 🚀 **Async Support**: Fully asynchronous API for better performance
- 📤 **Document Upload**: Upload and index new documents via API or UI
- 💬 **Conversation History**: Maintain chat history in the frontend
- 🌊 **Streaming Responses**: Real-time streaming of AI responses
- 🔍 **Health Monitoring**: Health check and status endpoints
- 📊 **Structured Logging**: Comprehensive logging with file and console output
- ⚙️ **Configurable Settings**: Extensive configuration via environment variables
- 🔄 **Connection Pooling**: Redis connection pooling for better resource management
- 🎯 **Similarity Thresholding**: Filter results by similarity score
- 🛡️ **Enhanced Error Handling**: Better error messages and exception handling
- 📱 **Improved UI**: Modern, responsive interface with sidebar controls

---

## 🏗️ Architecture

```
┌─────────────────┐
│  Streamlit UI   │
│   (Frontend)    │
└────────┬────────┘
         │ HTTP POST
         ▼
┌─────────────────┐
│   FastAPI       │
│   (Backend)     │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────┐
│ Redis  │ │  OpenAI  │
│ Vector │ │   GPT-4  │
│ Store  │ │ Embeddings│
└────────┘ └──────────┘
```

### RAG Pipeline Flow

1. **Document Ingestion**: Clinical notes are loaded and chunked
2. **Embedding Generation**: Each chunk is converted to vector embeddings
3. **Vector Storage**: Embeddings stored in Redis with document metadata
4. **Query Processing**: User questions are embedded and compared
5. **Retrieval**: Top-k similar documents retrieved using cosine similarity
6. **Generation**: LLM generates response using retrieved context

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **Redis** - In-memory vector database for embeddings
- **OpenAI API** - GPT-4 for generation, text-embedding-3-small for embeddings
- **Pydantic** - Data validation using Python type annotations

### Frontend
- **Streamlit** - Rapid web app development framework

### Infrastructure
- **Docker** - Containerization for easy deployment
- **Uvicorn** - ASGI server for FastAPI

---

## 📦 Prerequisites

Before you begin, ensure you have the following installed:

- **Python** 3.11 or higher
- **Redis** server (local or remote)
- **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))
- **pip** or **conda** package manager

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Clinical-Notes-Assistant
```

### 2. Install Backend Dependencies

```bash
cd healthcare_rag_backend
pip install -r requirements.txt
```

### 3. Install Frontend Dependencies

```bash
cd ../frontend
pip install streamlit requests
```

### 4. Set Up Redis

**Option A: Local Redis**
```bash
# macOS
brew install redis
brew services start redis

# Linux
sudo apt-get install redis-server
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:latest
```

**Option B: Redis Cloud**
- Sign up at [Redis Cloud](https://redis.com/try-free/)
- Get your connection URL

---

## ⚙️ Configuration

### 1. Create Environment File

Create a `.env` file in the `healthcare_rag_backend` directory:

```bash
cd healthcare_rag_backend
touch .env
```

### 2. Add Environment Variables

Create a `.env` file with the following variables:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here
REDIS_URL=redis://localhost:6379

# Optional (with defaults)
VECTOR_STORE_INDEX_NAME=healthcare_index
DEFAULT_MODEL=gpt-4
EMBEDDING_MODEL=text-embedding-3-small
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
DEFAULT_TOP_K=4
MIN_SIMILARITY_THRESHOLD=0.5
CORS_ORIGINS=http://localhost:8501,http://localhost:3000
LOG_LEVEL=INFO
```

**Note**: Replace `your_openai_api_key_here` with your actual OpenAI API key. See `healthcare_rag_backend/.env.example` for all available configuration options.

---

## 💻 Usage

### Starting the Backend Server

```bash
cd healthcare_rag_backend
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

- **API Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs**: `http://localhost:8000/redoc` (ReDoc)

### Starting the Frontend

```bash
cd frontend
streamlit run app.py
```

The Streamlit app will open in your browser at `http://localhost:8501`

### Using the Application

1. **Start both services** (backend and frontend)
2. **Open the Streamlit app** in your browser
3. **Enter your question** about the clinical notes
4. **Click "Ask"** to get an AI-powered response

**Example Questions:**
- "What medications was the patient prescribed?"
- "What are the patient's vital signs?"
- "What is the diagnosis?"
- "What treatment plan was recommended?"

### Frontend Features

The enhanced Streamlit frontend includes:

- 💬 **Chat Interface**: Natural conversation flow with message history
- 📤 **Document Upload**: Upload new clinical documents directly from the UI
- ⚙️ **Settings Panel**: Configure model parameters (Top K, streaming, etc.)
- 📊 **Status Monitoring**: Real-time health and document count display
- 🎨 **Modern UI**: Clean, responsive design with custom styling
- 🔄 **Auto-refresh**: Automatic status updates

### Uploading Documents

You can upload documents in two ways:

1. **Via UI**: Use the sidebar uploader in the Streamlit app
2. **Via API**: Use the `/api/documents/upload` endpoint

---

## 📡 API Documentation

### Endpoints

#### `POST /api/ask`
Query the clinical notes assistant with a question.

**Request Body:**
```json
{
  "question": "What medications was the patient prescribed?",
  "k": 4,
  "model": "gpt-4",
  "temperature": 0.0,
  "stream": false
}
```

**Response:**
```json
{
  "question": "What medications was the patient prescribed?",
  "answer": "Based on the clinical notes, the patient was prescribed...",
  "document_count": 42
}
```

#### `POST /api/ask/stream`
Stream responses in real-time (Server-Sent Events).

**Request Body:** Same as `/api/ask` with `stream: true`

**Response:** Streaming text/plain

#### `GET /api/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "document_count": 42,
  "redis_connected": true
}
```

#### `GET /api/status`
Get application status.

**Response:**
```json
{
  "document_count": 42,
  "redis_connected": true
}
```

#### `POST /api/documents/upload`
Upload and index a new clinical document.

**Request:** Multipart form data with `file` field

**Response:**
```json
{
  "document_id": "clinical_notes.txt",
  "chunks_created": 15,
  "message": "Document 'clinical_notes.txt' uploaded and indexed successfully"
}
```

#### `POST /api/documents/upload-text`
Upload document content as text.

**Query Parameters:**
- `content`: Document text content
- `document_id` (optional): Custom document ID

#### `DELETE /api/documents/clear`
Clear all documents from the vector store.

**Examples:**

**cURL - Basic Query:**
```bash
curl -X POST "http://localhost:8000/api/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the patient diagnosis?"}'
```

**cURL - Upload Document:**
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@clinical_notes.txt"
```

**Python - Async Query:**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/ask",
    json={
        "question": "What medications was the patient prescribed?",
        "k": 5,
        "temperature": 0.0
    }
)
print(response.json())
```

**Python - Streaming:**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/ask/stream",
    json={"question": "What are the symptoms?"},
    stream=True
)

for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
    if chunk:
        print(chunk, end='', flush=True)
```

---

## 📁 Project Structure

```
Clinical-Notes-Assistant/
│
├── healthcare_rag_backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── api/
│   │   │   └── routes.py        # API route definitions
│   │   ├── core/
│   │   │   ├── config.py        # Configuration settings
│   │   │   └── llm.py           # LLM client setup
│   │   └── rag/
│   │       ├── chain.py         # RAG chain implementation
│   │       └── retriever.py     # Document retrieval logic
│   ├── data/
│   │   └── clinical_docs/
│   │       └── clinical_notes.txt  # Clinical documents
│   ├── Dockerfile               # Docker configuration
│   └── requirements.txt        # Python dependencies
│
├── frontend/
│   └── app.py                  # Streamlit frontend application
│
└── README.md                   # This file
```

---

## 🐳 Docker Deployment

### Build the Docker Image

```bash
cd healthcare_rag_backend
docker build -t clinical-notes-assistant .
```

### Run the Container

```bash
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_api_key \
  -e REDIS_URL=redis://host.docker.internal:6379 \
  --name clinical-assistant \
  clinical-notes-assistant
```

**Note**: Ensure Redis is accessible from the Docker container. For local Redis, use `host.docker.internal` on macOS/Windows or the host IP on Linux.

---

## 🔧 Development

### Running in Development Mode

Backend with auto-reload:
```bash
cd healthcare_rag_backend
uvicorn app.main:app --reload
```

Frontend with auto-reload:
```bash
cd frontend
streamlit run app.py --server.runOnSave true
```

### Adding New Documents

1. Place your clinical documents in `healthcare_rag_backend/data/clinical_docs/`
2. Update the file path in `retriever.py` if needed
3. Restart the backend server to re-index documents

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is part of a portfolio demonstration. Please ensure you have proper licensing for production use.

---

## 🙏 Acknowledgments

- **OpenAI** for providing powerful language models and embeddings
- **Redis** for efficient vector storage capabilities
- **FastAPI** and **Streamlit** communities for excellent frameworks

---

## 📧 Contact

For questions or support, please open an issue in the repository.

---

<div align="center">

**Built with ❤️ for healthcare professionals**

⭐ Star this repo if you find it helpful!

</div>

