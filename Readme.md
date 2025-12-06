# ChunkSmith 🚀

**Multimodal RAG System with Image Extraction & Retrieval**

Extract, process, and chat with PDF documents while preserving actual images from source files.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://multi-modul-rag.vercel.app/)

---

## 🎬 See It In Action

Watch ChunkSmith extract and retrieve images from PDFs in real-time:

[![ChunkSmith Demo](https://img.youtube.com/vi/a9Haiu-e7ZU/maxresdefault.jpg)](https://www.youtube.com/watch?v=a9Haiu-e7ZU)

**[▶️ Watch Full Demo](https://www.youtube.com/watch?v=a9Haiu-e7ZU)** | **[🚀 Try Live Demo](https://multi-modul-rag.vercel.app/)**

---

## 💡 Why ChunkSmith?

Most RAG systems **lose images** during document processing. ChunkSmith is different:

✅ **Preserves actual images** from PDFs  
✅ **Returns visual context** with answers  
✅ **Extracts tables** as structured data  
✅ **Supports 90+ languages** with OCR  
✅ **Production-ready** with Docker deployment  

---

## ⚡ Quick Start

### Try It Instantly (No Installation)
👉 **[Live Demo](https://multi-modul-rag.vercel.app/)**

### Run Locally with Docker
```bash
# Pull the image
docker pull anshulnp/chunksmith-backend:latest

# Run the backend
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key anshulnp/chunksmith-backend:latest

# Access at http://localhost:8000
```

**For detailed setup:** See our [Setup Guide](./SETUP.md)

---

## 🎯 Overview

ChunkSmith is a powerful multimodal RAG (Retrieval-Augmented Generation) system that enables intelligent document processing and chat capabilities. It extracts text, images, and tables from PDFs, processes them using advanced AI models, and provides context-aware responses with visual support.

### What Makes It Special?

Unlike traditional RAG systems that strip away visual information, ChunkSmith:
- 🖼️ **Preserves original images** and returns them contextually
- 📊 **Extracts tables** maintaining structure and relationships
- 🌐 **Processes documents** in 90+ languages with Tesseract OCR
- ⚡ **Scales efficiently** with async processing and load balancing
- 💬 **Provides intelligent answers** with both text and visual context

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

**📖 [Setup Guide](./setup.md)**

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
├── Frontend/                      # React frontend application
├── SETUP.md                       # Detailed setup instructions
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

## 🔗 Links & Resources

- **🎬 Demo Video:** https://www.youtube.com/watch?v=a9Haiu-e7ZU
- **🚀 Live Demo:** https://multi-modul-rag.vercel.app/
- **🐳 Docker Image:** `docker pull anshulnp/chunksmith-backend:latest`
- **📖 API Docs:** http://localhost:8000/docs (when running locally)
- **📋 Setup Guide:** [SETUP.md](./SETUP.md)

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. ⭐ Star this repository
2. 🐛 Report bugs or suggest features via [Issues](../../issues)
3. 🔀 Submit Pull Requests
4. 📖 Improve documentation
5. 🎥 Share your use case or demo

See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines.

---

## 📄 License

MIT License - feel free to use this project for personal or commercial purposes.

---

## 📞 Support

- 💬 **Issues:** [GitHub Issues](../../issues)
- 📧 **Email:** [Contact via GitHub profile]
- 🐦 **Social:** Share your experience with #ChunkSmith

---

## 🙏 Acknowledgments

Built with powerful open-source tools:
- Google Gemini for AI capabilities
- LangChain for RAG framework
- ChromaDB for vector storage
- Tesseract for OCR
- FastAPI & React for the stack

---

## ⭐ Show Your Support

If ChunkSmith helps you, please consider:
- ⭐ Starring the repository
- 🐦 Sharing on social media
- 📝 Writing a blog post about your use case
- 🎥 Creating a tutorial or demo

---

**Built with ❤️ by Anshul Parate**

[⬆ Back to Top](#chunksmith-)
