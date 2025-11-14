"""FastAPI routes for document processing with WebSocket streaming"""
import os
import shutil
import json
import asyncio
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, List, Dict

from config.settings import settings
from core.document_parser import DocumentParser
from core.content_processor import ContentProcessor
from core.vector_store import VectorStoreManager
from utils.file_helpers import FileHandler

router = APIRouter()

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}


class ProcessRequest(BaseModel):
    """Request model for document processing"""
    max_characters: Optional[int] = settings.MAX_CHARACTERS
    new_after_n_chars: Optional[int] = settings.NEW_AFTER_N_CHARS
    combine_text_under_n_chars: Optional[int] = settings.COMBINE_TEXT_UNDER_N_CHARS
    extract_images: Optional[bool] = settings.EXTRACT_IMAGES
    extract_tables: Optional[bool] = settings.EXTRACT_TABLES
    languages: Optional[List[str]] = settings.LANGUAGES


class ProcessResponse(BaseModel):
    """Response model for document processing"""
    success: bool
    message: str
    document_id: str
    chunks_processed: int
    images_extracted: int
    pickle_path: str
    json_path: str
    vector_store_path: str


class SearchRequest(BaseModel):
    """Request model for vector search"""
    query: str
    k: Optional[int] = 5
    document_id: Optional[str] = None


async def send_ws_message(document_id: str, message_type: str, data: dict):
    """Send message to WebSocket client"""
    if document_id in active_connections:
        try:
            await active_connections[document_id].send_json({
                "type": message_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Error sending WebSocket message: {e}")


@router.websocket("/ws/{document_id}")
async def websocket_endpoint(websocket: WebSocket, document_id: str):
    """
    WebSocket endpoint for real-time processing updates
    
    Connect to this endpoint: ws://localhost:8000/api/ws/{document_id}
    """
    await websocket.accept()
    active_connections[document_id] = websocket
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "data": {"message": "WebSocket connected", "document_id": document_id}
        })
        
        # Keep connection alive
        while True:
            try:
                # Receive messages from client (optional)
                data = await websocket.receive_text()
                # Echo back or handle commands
                await websocket.send_json({
                    "type": "echo",
                    "data": {"received": data}
                })
            except WebSocketDisconnect:
                break
    
    except Exception as e:
        print(f"WebSocket error: {e}")
    
    finally:
        # Cleanup connection
        if document_id in active_connections:
            del active_connections[document_id]
        print(f"WebSocket disconnected: {document_id}")


@router.get("/languages")
async def get_supported_languages():
    """Get list of all supported OCR languages"""
    from core.document_parser import DocumentParser
    
    languages = DocumentParser.get_supported_languages()
    
    return {
        "success": True,
        "count": len(languages),
        "languages": languages,
        "examples": {
            "english": "eng",
            "hindi": "hin",
            "spanish": "spa",
            "chinese": "chi_sim",
            "arabic": "ara"
        }
    }


@router.post("/process-pdf")
async def process_pdf(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    max_characters: int = settings.MAX_CHARACTERS,
    new_after_n_chars: int = settings.NEW_AFTER_N_CHARS,
    combine_text_under_n_chars: int = settings.COMBINE_TEXT_UNDER_N_CHARS,
    extract_images: bool = settings.EXTRACT_IMAGES,
    extract_tables: bool = settings.EXTRACT_TABLES,
    languages: str = "english",
):
    """
    Process a PDF document through the entire pipeline with WebSocket streaming
    """
    
    # Generate unique document ID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    document_id = f"{file.filename.replace('.pdf', '')}_{timestamp}"
    
    # Start processing in background
    background_tasks.add_task(
        process_pdf_task,
        file,
        document_id,
        max_characters,
        new_after_n_chars,
        combine_text_under_n_chars,
        extract_images,
        extract_tables,
        languages
    )
    
    return {
        "success": True,
        "message": "Processing started",
        "document_id": document_id,
        "websocket_url": f"/api/ws/{document_id}"
    }


async def process_pdf_task(
    file: UploadFile,
    document_id: str,
    max_characters: int,
    new_after_n_chars: int,
    combine_text_under_n_chars: int,
    extract_images: bool,
    extract_tables: bool,
    languages: str
):
    """Background task for PDF processing with WebSocket updates"""
    
    try:
        # Step 1: Upload
        await send_ws_message(document_id, "step", {
            "step": 1,
            "name": "upload",
            "message": f"Uploading file...",
            "progress": 0
        })
        
        # Reset file pointer
        await file.seek(0)
        
        # Save uploaded file
        upload_path = os.path.join(settings.UPLOAD_DIR, f"{document_id}.pdf")
        with open(upload_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Validate PDF
        is_valid, error_msg = FileHandler.validate_pdf(upload_path, settings.MAX_FILE_SIZE // (1024 * 1024))
        if not is_valid:
            os.remove(upload_path)
            await send_ws_message(document_id, "error", {"message": error_msg})
            return
        
        await send_ws_message(document_id, "step", {
            "step": 1,
            "name": "upload",
            "message": "File uploaded successfully",
            "progress": 25
        })
        
        # Step 2: Parse PDF
        await send_ws_message(document_id, "step", {
            "step": 2,
            "name": "parsing",
            "message": "Parsing PDF document...",
            "progress": 25
        })
        
        language_list = [lang.strip() for lang in languages.split(',')]
        parser = DocumentParser(image_output_dir=str(settings.IMAGE_DIR))
        elements = parser.partition_pdf_document(
            file_path=upload_path,
            max_characters=max_characters,
            new_after_n_chars=new_after_n_chars,
            combine_text_under_n_chars=combine_text_under_n_chars,
            extract_images=extract_images,
            extract_tables=extract_tables,
            languages=language_list
        )
        
        checkpoint1_path = os.path.join(settings.PICKLE_DIR, f"{document_id}_checkpoint1.pkl")
        FileHandler.save_pickle(elements, checkpoint1_path)
        
        await send_ws_message(document_id, "step", {
            "step": 2,
            "name": "parsing",
            "message": f"Extracted {len(elements)} elements",
            "progress": 40,
            "elements_count": len(elements)
        })
        
        # Step 3: AI Processing
        await send_ws_message(document_id, "step", {
            "step": 3,
            "name": "ai_processing",
            "message": "Processing chunks with AI...",
            "progress": 40,
            "total_chunks": len(elements)
        })
        
        processor = ContentProcessor(
            image_dir=str(settings.IMAGE_DIR),
            model_name=settings.GEMINI_MODEL,
            temperature=settings.TEMPERATURE
        )
        
        # Process chunks with progress updates
        documents = await process_chunks_with_updates(processor, elements, document_id)
        
        image_count = len(list(settings.IMAGE_DIR.glob("*.png")))
        
        output_pickle_path = os.path.join(settings.PICKLE_DIR, f"{document_id}_processed.pkl")
        output_json_path = os.path.join(settings.JSON_DIR, f"{document_id}_processed.json")
        
        FileHandler.save_pickle(documents, output_pickle_path)
        FileHandler.save_json(documents, output_json_path)
        
        await send_ws_message(document_id, "step", {
            "step": 3,
            "name": "ai_processing",
            "message": f"Processed {len(documents)} chunks",
            "progress": 80,
            "chunks_processed": len(documents)
        })
        
        # Step 4: Vector Store
        await send_ws_message(document_id, "step", {
            "step": 4,
            "name": "vectorization",
            "message": "Creating vector embeddings...",
            "progress": 80
        })
        
        vector_store_path = os.path.join(settings.CHROMA_DIR, document_id)
        vector_manager = VectorStoreManager(embedding_model=settings.EMBEDDING_MODEL)
        vectorstore = vector_manager.create_vector_store(
            documents=documents,
            persist_directory=vector_store_path,
            collection_name=document_id
        )
        
        await send_ws_message(document_id, "step", {
            "step": 4,
            "name": "vectorization",
            "message": "Vector store created",
            "progress": 100
        })
        
        # Complete
        result = {
            "success": True,
            "message": "Document processed successfully",
            "document_id": document_id,
            "chunks_processed": len(documents),
            "images_extracted": image_count,
            "pickle_path": output_pickle_path,
            "json_path": output_json_path,
            "vector_store_path": vector_store_path
        }
        
        await send_ws_message(document_id, "complete", {
            "message": "Processing complete!",
            "progress": 100,
            "result": result
        })
    
    except Exception as e:
        await send_ws_message(document_id, "error", {
            "message": str(e),
            "progress": 0
        })
        print(f"Error processing PDF: {e}")


async def process_chunks_with_updates(processor, chunks, document_id):
    """Process chunks and send WebSocket updates"""
    documents = []
    total_chunks = len(chunks)
    
    for i, chunk in enumerate(chunks, 1):
        # Send progress update
        progress = 40 + int((i / total_chunks) * 40)
        await send_ws_message(document_id, "chunk_progress", {
            "current": i,
            "total": total_chunks,
            "progress": progress,
            "message": f"Processing chunk {i}/{total_chunks}"
        })
        
        # Process chunk (synchronous call)
        # You would need to modify ContentProcessor to work with async
        # For now, we'll call it synchronously
        await asyncio.sleep(0)  # Yield control
    
    # Process all chunks at once (original behavior)
    documents = processor.summarise_chunks(chunks)
    
    return documents


@router.post("/search")
async def search_documents(request: SearchRequest):
    """Search documents in vector store"""
    try:
        if request.document_id:
            vector_store_path = os.path.join(settings.CHROMA_DIR, request.document_id)
            if not os.path.exists(vector_store_path):
                raise HTTPException(status_code=404, detail=f"Document ID '{request.document_id}' not found")
            collection_name = request.document_id
        else:
            vector_store_path = str(settings.CHROMA_DIR)
            collection_name = "multimodal_rag"
        
        vector_manager = VectorStoreManager(embedding_model=settings.EMBEDDING_MODEL)
        vectorstore = vector_manager.load_vector_store(
            persist_directory=vector_store_path,
            collection_name=collection_name
        )
        
        results = vector_manager.search(vectorstore, request.query, k=request.k)
        
        formatted_results = []
        for i, doc in enumerate(results, 1):
            formatted_results.append({
                "rank": i,
                "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                "metadata": doc.metadata
            })
        
        return {
            "success": True,
            "query": request.query,
            "results_count": len(results),
            "results": formatted_results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def download_all_project_data():
    """Download all project data as a zip file"""
    import zipfile
    import tempfile
    from fastapi.responses import FileResponse
    
    try:
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if settings.PICKLE_DIR.exists():
                for pkl_file in settings.PICKLE_DIR.glob("*.pkl"):
                    zipf.write(pkl_file, f"pickle/{pkl_file.name}")
            
            if settings.JSON_DIR.exists():
                for json_file in settings.JSON_DIR.glob("*.json"):
                    zipf.write(json_file, f"json/{json_file.name}")
            
            if settings.IMAGE_DIR.exists():
                for img_file in settings.IMAGE_DIR.glob("*"):
                    if img_file.is_file():
                        zipf.write(img_file, f"images/{img_file.name}")
            
            if settings.CHROMA_DIR.exists():
                for chroma_item in settings.CHROMA_DIR.rglob("*"):
                    if chroma_item.is_file():
                        rel_path = chroma_item.relative_to(settings.CHROMA_DIR)
                        zipf.write(chroma_item, f"chroma_db/{rel_path}")
        
        return FileResponse(
            path=temp_zip.name,
            filename="project_data.zip",
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=project_data.zip"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create archive: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "upload_dir": str(settings.UPLOAD_DIR),
        "image_dir": str(settings.IMAGE_DIR),
        "chroma_dir": str(settings.CHROMA_DIR),
        "active_connections": len(active_connections)
    }