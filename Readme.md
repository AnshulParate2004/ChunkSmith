# ChunkSmith 🚀

**Multimodal RAG System with Image Extraction & Retrieval**

Extract, process, and chat with PDF documents while preserving actual images from source files.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

---

## 🎯 Overview

ChunkSmith is a powerful multimodal RAG (Retrieval-Augmented Generation) system that enables intelligent document processing and chat capabilities. It extracts text, images, and tables from PDFs, processes them using advanced AI models, and provides context-aware responses with visual support.

---

## ✨ Key Features

- 🖼️ **Image Retrieval** - Returns actual images from PDFs in responses
- 🌍 **90+ Languages** - Multi-language OCR support with Tesseract
- ⚡ **Async Processing** - Multi-API key load balancing for high throughput
- 💬 **Smart Chat** - Context-aware Q&A with visual and textual support
- 📦 **Data Export** - Download chunks, images, and embeddings
- 🔄 **Streaming Responses** - Real-time Server-Sent Events (SSE) for chat
- 🎨 **Modern UI** - Intuitive React-based frontend
- 🐳 **Docker Ready** - Easy deployment with Docker containers

---

## 🛠️ Tech Stack

**Backend:**
- FastAPI - High-performance async web framework
- Google Gemini 2.5 Pro - Advanced AI model for processing
- LangChain - Framework for LLM applications
- ChromaDB - Vector database for embeddings
- Tesseract OCR - Multi-language text extraction
- PyMuPDF - PDF processing

**Frontend:**
- React 18+ - Modern UI framework
- Axios - HTTP client
- TailwindCSS - Utility-first CSS
- Deployed on Vercel

**Storage & Infrastructure:**
- ChromaDB - Vector storage
- JSON - Metadata storage
- Docker - Containerization

---

## 🚀 Getting Started

### Docker Deployment (Recommended)

For quick and easy deployment using Docker, please refer to our comprehensive setup guide:

**📖 [Setup Guide](./SETUP.md)**

The setup guide includes:
- Docker installation and prerequisites
- Environment configuration
- Container management commands
- Troubleshooting tips
- Frontend integration

### Frontend Access

The ChunkSmith frontend is hosted and accessible at:

**🌐 https://multi-modul-rag.vercel.app/**

Simply configure your API endpoint in the frontend to point to your running backend instance (default: `http://localhost:8000`).

---

## 📚 API Documentation

### Core Endpoints

#### Document Processing
```http
POST   /api/process-pdf
```
Upload and process PDF documents with text extraction, image extraction, and AI-powered analysis.

#### Progress Streaming
```http
GET    /api/process-pdf-stream/{doc_id}
```
Server-Sent Events endpoint for real-time processing updates.

#### Chat Initialization
```http
POST   /api/chat/init/{doc_id}
```
Initialize a chat session for a processed document.

#### Chat Streaming
```http
GET    /api/chat/stream/{session_id}?message={query}
```
Stream chat responses with context-aware answers and relevant images.

#### Data Export
```http
GET    /api/documents/{doc_id}/chunks
```
Download processed document data including chunks, images, and embeddings.

#### Vector Search
```http
POST   /api/search
```
Perform semantic search across document embeddings.

#### Document Management
```http
GET    /api/documents              # List all documents
DELETE /api/documents/{doc_id}    # Delete document
GET    /api/languages              # Supported OCR languages
GET    /api/health                 # Health check
```

**Full API Documentation:** Access interactive Swagger docs at `http://localhost:8000/docs` when backend is running.

---

## 🏗️ Project Architecture

```
ChunkSmith/
├── Backend/
│   ├── main.py                    # FastAPI application entry point
│   ├── api/
│   │   └── routes.py              # API endpoints
│   ├── core/
│   │   ├── document_parser.py     # PDF parsing and extraction
│   │   ├── content_processor.py   # AI-powered content processing
│   │   ├── vector_store.py        # ChromaDB vector operations
│   │   └── chat_agent.py          # Chat logic and RAG
│   ├── models/                    # Pydantic models
│   ├── utils/                     # Helper functions
│   ├── data/                      # Generated data storage
│   │   ├── chroma_db/             # Vector database
│   │   ├── images/                # Extracted images
│   │   └── metadata/              # Document metadata
│   ├── requirements.txt           # Python dependencies
│   └── Dockerfile                 # Docker configuration
├── setup.md                       # Detailed setup instructions
└── Readme.md                      # This file
```

---

## 🔧 Configuration

### Supported Languages

ChunkSmith supports 70+ languages for OCR including:
- **European:** English, Spanish, French, German, Italian, Portuguese, Russian
- **Indic:** Hindi, Bengali, Tamil, Telugu, Gujarati, Marathi, Punjabi
- **East Asian:** Chinese (Simplified & Traditional), Japanese, Korean
- **Middle Eastern:** Arabic, Hebrew, Persian, Turkish
- And many more...

### Processing Options

| Option | Description | Default |
|--------|-------------|---------|
| `MAX_CHARACTERS` | Maximum characters per chunk | 3000 |
| `EXTRACT_IMAGES` | Enable/disable image extraction | true |
| `EXTRACT_TABLES` | Enable/disable table extraction | true |
| `MAX_UPLOAD_SIZE` | Maximum PDF file size | 50MB |
| `ALLOWED_EXTENSIONS` | Supported file types | [".pdf"] |

---

## 🌟 Use Cases

- 📚 **Document Analysis** - Extract insights from research papers and reports
- 📖 **E-Learning** - Interactive textbook chat and Q&A systems
- 🏢 **Enterprise Knowledge Base** - Build searchable knowledge repositories
- 📰 **Content Processing** - Automated content extraction and summarization
- 🔍 **Research & Investigation** - Quick information retrieval from large documents
- 💼 **Legal & Compliance** - Document review and analysis
- 🏥 **Medical Records** - Healthcare document processing
- 📊 **Data Extraction** - Table and structured data extraction from PDFs

---

## 🚦 Quick Start Workflow

1. **Deploy Backend** - Follow [setup.md](./setup.md) to run Docker container
2. **Access Frontend** - Open https://multi-modul-rag.vercel.app/
3. **Configure API** - Set API URL to `http://localhost:8000` in frontend
4. **Upload PDF** - Upload your PDF document through the UI
5. **Start Chatting** - Ask questions about your document with image support

---

## 🔗 Links & Resources

- **Live Frontend:** https://multi-modul-rag.vercel.app/
- **Docker Image:** `docker pull anshulnp/chunksmith-backend:latest`
- **API Docs:** http://localhost:8000/docs (when running locally)
- **Setup Guide:** [setup.md](./setup.md)

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

MIT License - feel free to use this project for personal or commercial purposes.

---

## 📞 Support

For issues, questions, or feature requests, please open an issue on the repository.

---

**Built with ❤️ By Anshul Parate**
