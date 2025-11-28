markdown# ChunkSmite 🚀

**Multimodal RAG System with Image Extraction & Retrieval**

Extract, process, and chat with PDF documents while preserving actual images from source files.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)

---

## ✨ Features

- 🖼️ **Image Retrieval** - Returns actual images from PDFs in responses
- 🌍 **70+ Languages** - Multi-language OCR support
- ⚡ **Async Processing** - Multi-API key load balancing
- 💬 **Smart Chat** - Context-aware Q&A with visual support
- 📦 **Data Export** - Download chunks, images, and embeddings

---

## 🛠️ Tech Stack

**Backend:** FastAPI, Python, Gemini 2.5 Pro, LangChain, ChromaDB, Tesseract OCR  
**Frontend:** React, Axios, TailwindCSS  
**Storage:** ChromaDB, JSON, Pickle

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 16+
- Tesseract OCR
- Google Gemini API Key

### Install Tesseract
```bash
# Windows
https://github.com/UB-Mannheim/tesseract/wiki

# Linux
sudo apt install tesseract-ocr libtesseract-dev

# macOS
brew install tesseract
```

### Backend Setup
```bash
cd Backend
pip install -r requirements.txt
```

Create `Backend/.env`:
```env
GOOGLE_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-pro
EMBEDDING_MODEL=text-embedding-004
```

Get API key: [Google AI Studio](https://makersuite.google.com/app/apikey)

**Run:**
```bash
python main.py
```
Backend: `http://localhost:8000`

### Frontend Setup
```bash
cd Frontend
npm install
```

Create `Frontend/.env`:
```env
REACT_APP_API_BASE_URL=http://localhost:8000
```

**Run:**
```bash
npm start
```
Frontend: `http://localhost:3000`

---

## 📚 API Endpoints
```http
POST   /api/process-pdf                    # Upload & process PDF
GET    /api/process-pdf-stream/{doc_id}    # Stream progress (SSE)
POST   /api/chat/init/{doc_id}             # Initialize chat
GET    /api/chat/stream/{session_id}       # Chat with streaming (SSE)
GET    /api/documents/{doc_id}/chunks      # Download processed data
POST   /api/search                         # Vector search
GET    /api/documents                      # List documents
DELETE /api/documents/{doc_id}             # Delete document
GET    /api/languages                      # Supported languages
GET    /api/health                         # Health check
```

---

## 💡 Usage

### Python
```python
import requests

# Upload PDF
files = {'file': open('document.pdf', 'rb')}
response = requests.post('http://localhost:8000/api/process-pdf', files=files)
doc_id = response.json()['document_id']

# Chat
chat = requests.post(f'http://localhost:8000/api/chat/init/{doc_id}')
session_id = chat.json()['session_id']
```

### JavaScript
```javascript
// Initialize chat
const response = await fetch(`http://localhost:8000/api/chat/init/${docId}`, {
  method: 'POST'
});
const { session_id } = await response.json();

// Stream responses
const eventSource = new EventSource(
  `http://localhost:8000/api/chat/stream/${session_id}?message=${encodeURIComponent(question)}`
);

eventSource.addEventListener('message', (e) => {
  const data = JSON.parse(e.data);
  if (data.type === 'content') console.log(data.data.content);
  if (data.type === 'image') console.log('Image:', data.data.filename);
});
```

---

## 🏗️ Project Structure
```
chunksmite/
├── Backend/
│   ├── main.py                    # Entry point
│   ├── api/routes.py              # Endpoints
│   ├── core/
│   │   ├── document_parser.py     # PDF parsing
│   │   ├── content_processor.py   # AI processing
│   │   ├── vector_store.py        # Vector DB
│   │   └── chat_agent.py          # Chat logic
│   └── data/                      # Generated files
└── Frontend/
    ├── src/
    │   ├── components/
    │   └── services/
    └── package.json
```

---

## 🐳 Docker
```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./Backend
    ports: ["8000:8000"]
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
  frontend:
    build: ./Frontend
    ports: ["3000:80"]
```

**Run:**
```bash
docker-compose up -d
```

---

## 🔧 Configuration

### Environment Variables
```env
# API Keys (multiple for load balancing)
GOOGLE_API_KEY_1=key1
GOOGLE_API_KEY_2=key2

# Processing
MAX_CHARACTERS=3000
EXTRACT_IMAGES=True
EXTRACT_TABLES=True

# Languages (comma-separated)
LANGUAGES=english,hindi,spanish
```

---

## 🚨 Troubleshooting

**Tesseract not found:**
```bash
tesseract --version  # Verify installation
```

**API key error:**
- Check `.env` file exists with valid key
- Enable Gemini API at Google Cloud Console

**Memory error:**
- Reduce `MAX_CHARACTERS` in config
- Process smaller PDFs

---

## 📝 License

MIT License

---

**Built with FastAPI, React, Gemini 2.5 Pro, ChromaDB**Claude can make mistakes. Please double-check responses.