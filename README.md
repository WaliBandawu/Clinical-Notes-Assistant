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

- **Document Processing**: Automatically chunks and indexes clinical documents
- **Vector Embeddings**: Uses OpenAI's `text-embedding-3-small` for semantic understanding
- **RAG Pipeline**: Retrieves relevant context before generating responses
- **RESTful API**: FastAPI backend with comprehensive error handling
- **Interactive UI**: Streamlit-based web interface for seamless user experience
- **Scalable Architecture**: Docker-ready for easy deployment

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

```env
OPENAI_API_KEY=your_openai_api_key_here
REDIS_URL=redis://localhost:6379
VECTOR_STORE_INDEX_NAME=healthcare_index
```

**Note**: Replace `your_openai_api_key_here` with your actual OpenAI API key.

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

---

## 📡 API Documentation

### Endpoint: `POST /api/ask`

Query the clinical notes assistant with a question.

**Request Body:**
```json
{
  "question": "What medications was the patient prescribed?"
}
```

**Response:**
```json
{
  "question": "What medications was the patient prescribed?",
  "answer": "Based on the clinical notes, the patient was prescribed..."
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the patient diagnosis?"}'
```

**Python Example:**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/ask",
    json={"question": "What medications was the patient prescribed?"}
)
print(response.json())
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

