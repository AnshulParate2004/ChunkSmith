"""FastAPI routes for document processing with Server-Sent Events (SSE)"""
import os
import shutil
import json
import asyncio
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, AsyncGenerator
import zipfile
import tempfile

from config.settings import settings
from core.document_parser import DocumentParser
from core.content_processor import ContentProcessor
from core.vector_store import VectorStoreManager
from utils.file_helpers import FileHandler
from core.chat_agent import ChatAgent
from typing import Dict

# Store active chat agents
chat_agents: Dict[str, ChatAgent] = {}
router = APIRouter()

# Store processing status for each document
processing_status = {}


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


async def send_sse_message(message_type: str, data: dict) -> str:
    """Format SSE message"""
    message = {
        "type": message_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    return f"data: {json.dumps(message)}\n\n"

@router.post("/process-pdf")
async def initiate_pdf_processing(
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
    Initiate PDF processing and return document_id for SSE streaming
    
    After calling this endpoint, connect to /api/process-pdf-stream/{document_id}
    to receive real-time progress updates via Server-Sent Events
    """
    try:
        # Generate unique document ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        document_id = f"{file.filename.replace('.pdf', '')}_{timestamp}"
        
        # Save uploaded file
        upload_path = os.path.join(settings.UPLOAD_DIR, f"{document_id}.pdf")
        with open(upload_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Validate PDF
        is_valid, error_msg = FileHandler.validate_pdf(
            upload_path, 
            settings.MAX_FILE_SIZE // (1024 * 1024)
        )
        if not is_valid:
            os.remove(upload_path)
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Initialize status
        processing_status[document_id] = {
            "status": "queued",
            "progress": 0,
            "message": "Processing queued"
        }
        
        # Start background processing
        background_tasks.add_task(
            process_pdf_background,
            document_id,
            upload_path,
            max_characters,
            new_after_n_chars,
            combine_text_under_n_chars,
            extract_images,
            extract_tables,
            languages
        )
        
        return {
            "success": True,
            "message": "Processing initiated",
            "document_id": document_id,
            "stream_url": f"/api/process-pdf-stream/{document_id}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/process-pdf-stream/{document_id}")
async def stream_pdf_processing(document_id: str): 
    """
    Stream processing updates via Server-Sent Events (SSE)
    
    Connect to this endpoint after initiating processing to receive real-time updates
    """
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for processing updates"""
        
        try:
            # Wait for processing to start
            max_wait = 30  # 30 seconds timeout
            waited = 0
            while document_id not in processing_status and waited < max_wait:
                await asyncio.sleep(0.5)
                waited += 0.5
            
            if document_id not in processing_status:
                yield await send_sse_message("error", {
                    "message": "Processing not found or timed out"
                })
                return
            
            # Send initial connection message
            yield await send_sse_message("connected", {
                "message": "Connected to processing stream",
                "document_id": document_id
            })
            
            last_status = None
            
            # Stream updates
            while True:
                if document_id in processing_status:
                    current_status = processing_status[document_id]
                    
                    # Only send if status changed
                    if current_status != last_status:
                        yield await send_sse_message("progress", current_status)
                        last_status = current_status.copy()
                    
                    # Check if completed or failed
                    if current_status.get("status") in ["completed", "failed"]:
                        # Send final message
                        if current_status.get("status") == "completed":
                            yield await send_sse_message("complete", current_status)
                        else:
                            yield await send_sse_message("error", current_status)
                        
                        # Cleanup after 5 seconds
                        await asyncio.sleep(5)
                        if document_id in processing_status:
                            del processing_status[document_id]
                        break
                
                await asyncio.sleep(1)  # Poll every second
        
        except asyncio.CancelledError:
            # Client disconnected
            pass
        except Exception as e:
            yield await send_sse_message("error", {
                "message": f"Stream error: {str(e)}"
            })
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


async def process_pdf_background(
    document_id: str,
    upload_path: str,
    max_characters: int,
    new_after_n_chars: int,
    combine_text_under_n_chars: int,
    extract_images: bool,
    extract_tables: bool,
    languages: str
):
    """Background task for PDF processing with status updates"""
    
    try:
        # Update status: Starting
        processing_status[document_id] = {
            "status": "processing",
            "step": 1,
            "step_name": "upload",
            "progress": 5,
            "message": "📤 File uploaded and validated"
        }
        await asyncio.sleep(0.5)  # Brief pause for UI
        
        # Step 2: Parse PDF
        processing_status[document_id] = {
            "status": "processing",
            "step": 2,
            "step_name": "parsing",
            "progress": 10,
            "message": "🔍 Step 2: Parsing PDF document..."
        }
        
        # ✅ Convert comma-separated languages to list
        # The DocumentParser.get_language_codes() will handle the conversion
        language_list = [lang.strip() for lang in languages.split(',')]
        
        # Debug logging
        print(f"📝 Input languages from frontend: {language_list}")
        
        parser = DocumentParser(image_output_dir=str(settings.IMAGE_DIR))
        
        # Simulate async behavior for parsing (runs in thread pool)
        loop = asyncio.get_event_loop()
        elements = await loop.run_in_executor(
            None,
            parser.partition_pdf_document,
            upload_path,
            max_characters,
            new_after_n_chars,
            combine_text_under_n_chars,
            extract_images,
            extract_tables,
            language_list  # Pass language names directly - parser will convert them
        )
        
        checkpoint1_path = os.path.join(settings.PICKLE_DIR, f"{document_id}_checkpoint1.pkl")
        FileHandler.save_pickle(elements, checkpoint1_path)
        
        processing_status[document_id] = {
            "status": "processing",
            "step": 2,
            "step_name": "parsing",
            "progress": 30,
            "message": f"✅ Extracted {len(elements)} elements",
            "elements_count": len(elements)
        }
        await asyncio.sleep(0.5)
        
        # Step 3: AI Processing
        processing_status[document_id] = {
            "status": "processing",
            "step": 3,
            "step_name": "ai_processing",
            "progress": 35,
            "message": "🤖 Step 3: Processing chunks with AI (this may take a while)...",
            "total_chunks": len(elements)
        }
        
        processor = ContentProcessor(
            image_dir=str(settings.IMAGE_DIR),
            model_name=settings.GEMINI_MODEL,
            temperature=settings.TEMPERATURE
        )
        
        # Process chunks (runs in thread pool)
        documents = await loop.run_in_executor(
            None,
            processor.summarise_chunks,
            elements
        )
        
        image_count = len(list(settings.IMAGE_DIR.glob("*.png")))
        
        output_pickle_path = os.path.join(settings.PICKLE_DIR, f"{document_id}_processed.pkl")
        output_json_path = os.path.join(settings.JSON_DIR, f"{document_id}_processed.json")
        
        FileHandler.save_pickle(documents, output_pickle_path)
        FileHandler.save_json(documents, output_json_path)
        
        processing_status[document_id] = {
            "status": "processing",
            "step": 3,
            "step_name": "ai_processing",
            "progress": 70,
            "message": f"✅ Processed {len(documents)} chunks",
            "chunks_processed": len(documents),
            "images_extracted": image_count
        }
        await asyncio.sleep(0.5)
        
        # Step 4: Vector Store
        processing_status[document_id] = {
            "status": "processing",
            "step": 4,
            "step_name": "vectorization",
            "progress": 75,
            "message": "🔮 Step 4: Creating vector embeddings..."
        }
        
        vector_store_path = os.path.join(settings.CHROMA_DIR, document_id)
        vector_manager = VectorStoreManager(embedding_model=settings.EMBEDDING_MODEL)
        
        # Create vector store (runs in thread pool)
        vectorstore = await loop.run_in_executor(
            None,
            vector_manager.create_vector_store,
            documents,
            vector_store_path,
            document_id
        )
        
        processing_status[document_id] = {
            "status": "processing",
            "step": 4,
            "step_name": "vectorization",
            "progress": 95,
            "message": "✅ Vector store created"
        }
        await asyncio.sleep(0.5)
        
        # Complete
        processing_status[document_id] = {
            "status": "completed",
            "progress": 100,
            "message": "✅ Processing complete!",
            "result": {
                "document_id": document_id,
                "chunks_processed": len(documents),
                "images_extracted": image_count,
                "pickle_path": output_pickle_path,
                "json_path": output_json_path,
                "vector_store_path": vector_store_path
            }
        }
    
    except Exception as e:
        processing_status[document_id] = {
            "status": "failed",
            "progress": 0,
            "message": f"❌ Error: {str(e)}"
        }
        print(f"Error processing PDF: {e}")

@router.post("/chat/init/{document_id}")
async def initialize_chat(document_id: str):
    """
    Initialize chat session for a document
    
    Args:
        document_id: ID of the document to chat about
    """
    try:
        # Check if document exists
        vector_store_path = os.path.join(settings.CHROMA_DIR, document_id)
        if not os.path.exists(vector_store_path):
            raise HTTPException(
                status_code=404, 
                detail=f"Document '{document_id}' not found. Please process the PDF first."
            )
        
        # Create chat agent
        chat_agent = ChatAgent(document_id=document_id)
        session_id = f"{document_id}_{len(chat_agents)}"
        chat_agents[session_id] = chat_agent
        
        return {
            "success": True,
            "session_id": session_id,
            "document_id": document_id,
            "message": "Chat session initialized successfully"
        }
    
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/stream/{session_id}")
async def chat_stream(session_id: str, message: str):
    """
    Stream chat responses via SSE
    
    Args:
        session_id: Chat session ID from initialization
        message: User's message/question
    
    Usage:
        1. First call /chat/init/{document_id} to get session_id
        2. Then connect to this endpoint: /chat/stream/{session_id}?message=your_question
    """
    
    if session_id not in chat_agents:
        raise HTTPException(
            status_code=404,
            detail="Chat session not found. Please initialize chat first using /chat/init/{document_id}"
        )
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for chat responses"""
        try:
            chat_agent = chat_agents[session_id]
            
            # Send connection confirmation
            yield f"data: {json.dumps({'type': 'connected', 'message': 'Connected to chat stream'})}\n\n"
            
            # Stream chat responses
            async for event in chat_agent.chat_stream(message):
                event_type = event["type"]
                event_data = event["data"]
                
                # Format as SSE
                sse_message = {
                    "type": event_type,
                    **event_data
                }
                
                yield f"data: {json.dumps(sse_message)}\n\n"
            
            # Send end signal
            yield f"data: {json.dumps({'type': 'end'})}\n\n"
            
        except asyncio.CancelledError:
            # Client disconnected
            pass
        except Exception as e:
            error_message = str(e).replace('"', '\\"').replace("\n", " ")
            yield f"data: {json.dumps({'type': 'error', 'message': error_message})}\n\n"
            yield f"data: {json.dumps({'type': 'end'})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*"
        }
    )


@router.post("/chat/clear/{session_id}")
async def clear_chat_history(session_id: str):
    """
    Clear conversation history for a chat session
    
    Args:
        session_id: Chat session ID
    """
    if session_id not in chat_agents:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    try:
        chat_agents[session_id].clear_history()
        return {
            "success": True,
            "message": "Chat history cleared successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chat/session/{session_id}")
async def delete_chat_session(session_id: str):
    """
    Delete a chat session
    
    Args:
        session_id: Chat session ID
    """
    if session_id not in chat_agents:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    try:
        del chat_agents[session_id]
        return {
            "success": True,
            "message": "Chat session deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/sessions")
async def list_chat_sessions():
    """
    List all active chat sessions
    """
    sessions = [
        {
            "session_id": session_id,
            "document_id": agent.document_id,
            "history_length": len(agent.conversation_history)
        }
        for session_id, agent in chat_agents.items()
    ]
    
    return {
        "success": True,
        "count": len(sessions),
        "sessions": sessions
    }

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


# @router.post("/process-pdf")
# async def initiate_pdf_processing(
#     file: UploadFile = File(...),
#     background_tasks: BackgroundTasks = None,
#     max_characters: int = settings.MAX_CHARACTERS,
#     new_after_n_chars: int = settings.NEW_AFTER_N_CHARS,
#     combine_text_under_n_chars: int = settings.COMBINE_TEXT_UNDER_N_CHARS,
#     extract_images: bool = settings.EXTRACT_IMAGES,
#     extract_tables: bool = settings.EXTRACT_TABLES,
#     languages: str = "english",
# ):
#     """
#     Initiate PDF processing and return document_id for SSE streaming
    
#     After calling this endpoint, connect to /api/process-pdf-stream/{document_id}
#     to receive real-time progress updates via Server-Sent Events
#     """
#     try:
#         # Generate unique document ID
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         document_id = f"{file.filename.replace('.pdf', '')}_{timestamp}"
        
#         # Save uploaded file
#         upload_path = os.path.join(settings.UPLOAD_DIR, f"{document_id}.pdf")
#         with open(upload_path, "wb") as buffer:
#             content = await file.read()
#             buffer.write(content)
        
#         # Validate PDF
#         is_valid, error_msg = FileHandler.validate_pdf(
#             upload_path, 
#             settings.MAX_FILE_SIZE // (1024 * 1024)
#         )
#         if not is_valid:
#             os.remove(upload_path)
#             raise HTTPException(status_code=400, detail=error_msg)
        
#         # Initialize status
#         processing_status[document_id] = {
#             "status": "queued",
#             "progress": 0,
#             "message": "Processing queued"
#         }
        
#         # Start background processing
#         background_tasks.add_task(
#             process_pdf_background,
#             document_id,
#             upload_path,
#             max_characters,
#             new_after_n_chars,
#             combine_text_under_n_chars,
#             extract_images,
#             extract_tables,
#             languages
#         )
        
#         return {
#             "success": True,
#             "message": "Processing initiated",
#             "document_id": document_id,
#             "stream_url": f"/api/process-pdf-stream/{document_id}"
#         }
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/process-pdf-stream/{document_id}")
# async def stream_pdf_processing(document_id: str): 
#     """
#     Stream processing updates via Server-Sent Events (SSE)
    
#     Connect to this endpoint after initiating processing to receive real-time updates
#     """
    
#     async def event_generator() -> AsyncGenerator[str, None]:
#         """Generate SSE events for processing updates"""
        
#         try:
#             # Wait for processing to start
#             max_wait = 30  # 30 seconds timeout
#             waited = 0
#             while document_id not in processing_status and waited < max_wait:
#                 await asyncio.sleep(0.5)
#                 waited += 0.5
            
#             if document_id not in processing_status:
#                 yield await send_sse_message("error", {
#                     "message": "Processing not found or timed out"
#                 })
#                 return
            
#             # Send initial connection message
#             yield await send_sse_message("connected", {
#                 "message": "Connected to processing stream",
#                 "document_id": document_id
#             })
            
#             last_status = None
            
#             # Stream updates
#             while True:
#                 if document_id in processing_status:
#                     current_status = processing_status[document_id]
                    
#                     # Only send if status changed
#                     if current_status != last_status:
#                         yield await send_sse_message("progress", current_status)
#                         last_status = current_status.copy()
                    
#                     # Check if completed or failed
#                     if current_status.get("status") in ["completed", "failed"]:
#                         # Send final message
#                         if current_status.get("status") == "completed":
#                             yield await send_sse_message("complete", current_status)
#                         else:
#                             yield await send_sse_message("error", current_status)
                        
#                         # Cleanup after 5 seconds
#                         await asyncio.sleep(5)
#                         if document_id in processing_status:
#                             del processing_status[document_id]
#                         break
                
#                 await asyncio.sleep(1)  # Poll every second
        
#         except asyncio.CancelledError:
#             # Client disconnected
#             pass
#         except Exception as e:
#             yield await send_sse_message("error", {
#                 "message": f"Stream error: {str(e)}"
#             })
    
#     return StreamingResponse(
#         event_generator(),
#         media_type="text/event-stream",
#         headers={
#             "Cache-Control": "no-cache",
#             "Connection": "keep-alive",
#             "X-Accel-Buffering": "no"  # Disable nginx buffering
#         }
#     )


# async def process_pdf_background(
#     document_id: str,
#     upload_path: str,
#     max_characters: int,
#     new_after_n_chars: int,
#     combine_text_under_n_chars: int,
#     extract_images: bool,
#     extract_tables: bool,
#     languages: str
# ):
#     """Background task for PDF processing with status updates"""
    
#     try:
#         # Update status: Starting
#         processing_status[document_id] = {
#             "status": "processing",
#             "step": 1,
#             "step_name": "upload",
#             "progress": 5,
#             "message": "📤 File uploaded and validated"
#         }
#         await asyncio.sleep(0.5)  # Brief pause for UI
        
#         # Step 2: Parse PDF
#         processing_status[document_id] = {
#             "status": "processing",
#             "step": 2,
#             "step_name": "parsing",
#             "progress": 10,
#             "message": "🔍 Step 2: Parsing PDF document..."
#         }
        
#         language_list = [lang.strip() for lang in languages.split(',')]
#         parser = DocumentParser(image_output_dir=str(settings.IMAGE_DIR))
        
#         # Simulate async behavior for parsing (runs in thread pool)
#         loop = asyncio.get_event_loop()
#         elements = await loop.run_in_executor(
#             None,
#             parser.partition_pdf_document,
#             upload_path,
#             max_characters,
#             new_after_n_chars,
#             combine_text_under_n_chars,
#             extract_images,
#             extract_tables,
#             language_list
#         )
        
#         checkpoint1_path = os.path.join(settings.PICKLE_DIR, f"{document_id}_checkpoint1.pkl")
#         FileHandler.save_pickle(elements, checkpoint1_path)
        
#         processing_status[document_id] = {
#             "status": "processing",
#             "step": 2,
#             "step_name": "parsing",
#             "progress": 30,
#             "message": f"✅ Extracted {len(elements)} elements",
#             "elements_count": len(elements)
#         }
#         await asyncio.sleep(0.5)
        
#         # Step 3: AI Processing
#         processing_status[document_id] = {
#             "status": "processing",
#             "step": 3,
#             "step_name": "ai_processing",
#             "progress": 35,
#             "message": "🤖 Step 3: Processing chunks with AI (this may take a while)...",
#             "total_chunks": len(elements)
#         }
        
#         processor = ContentProcessor(
#             image_dir=str(settings.IMAGE_DIR),
#             model_name=settings.GEMINI_MODEL,
#             temperature=settings.TEMPERATURE
#         )
        
#         # Process chunks (runs in thread pool)
#         documents = await loop.run_in_executor(
#             None,
#             processor.summarise_chunks,
#             elements
#         )
        
#         image_count = len(list(settings.IMAGE_DIR.glob("*.png")))
        
#         output_pickle_path = os.path.join(settings.PICKLE_DIR, f"{document_id}_processed.pkl")
#         output_json_path = os.path.join(settings.JSON_DIR, f"{document_id}_processed.json")
        
#         FileHandler.save_pickle(documents, output_pickle_path)
#         FileHandler.save_json(documents, output_json_path)
        
#         processing_status[document_id] = {
#             "status": "processing",
#             "step": 3,
#             "step_name": "ai_processing",
#             "progress": 70,
#             "message": f"✅ Processed {len(documents)} chunks",
#             "chunks_processed": len(documents),
#             "images_extracted": image_count
#         }
#         await asyncio.sleep(0.5)
        
#         # Step 4: Vector Store
#         processing_status[document_id] = {
#             "status": "processing",
#             "step": 4,
#             "step_name": "vectorization",
#             "progress": 75,
#             "message": "🔮 Step 4: Creating vector embeddings..."
#         }
        
#         vector_store_path = os.path.join(settings.CHROMA_DIR, document_id)
#         vector_manager = VectorStoreManager(embedding_model=settings.EMBEDDING_MODEL)
        
#         # Create vector store (runs in thread pool)
#         vectorstore = await loop.run_in_executor(
#             None,
#             vector_manager.create_vector_store,
#             documents,
#             vector_store_path,
#             document_id
#         )
        
#         processing_status[document_id] = {
#             "status": "processing",
#             "step": 4,
#             "step_name": "vectorization",
#             "progress": 95,
#             "message": "✅ Vector store created"
#         }
#         await asyncio.sleep(0.5)
        
#         # Complete
#         processing_status[document_id] = {
#             "status": "completed",
#             "progress": 100,
#             "message": "✅ Processing complete!",
#             "result": {
#                 "document_id": document_id,
#                 "chunks_processed": len(documents),
#                 "images_extracted": image_count,
#                 "pickle_path": output_pickle_path,
#                 "json_path": output_json_path,
#                 "vector_store_path": vector_store_path
#             }
#         }
    
#     except Exception as e:
#         processing_status[document_id] = {
#             "status": "failed",
#             "progress": 0,
#             "message": f"❌ Error: {str(e)}"
#         }
#         print(f"Error processing PDF: {e}")


@router.post("/search")
async def search_documents(request: SearchRequest):
    """Search documents in vector store"""
    try:
        if request.document_id:
            vector_store_path = os.path.join(settings.CHROMA_DIR, request.document_id)
            if not os.path.exists(vector_store_path):
                raise HTTPException(
                    status_code=404, 
                    detail=f"Document ID '{request.document_id}' not found"
                )
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
async def list_processed_documents():
    """List all processed document IDs"""
    try:
        document_ids = []
        
        if settings.CHROMA_DIR.exists():
            for item in settings.CHROMA_DIR.iterdir():
                if item.is_dir():
                    document_ids.append(item.name)
        
        return {
            "success": True,
            "count": len(document_ids),
            "documents": document_ids
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}")
async def get_document_info(document_id: str):
    """Get information about a specific document"""
    try:
        vector_store_path = os.path.join(settings.CHROMA_DIR, document_id)
        
        if not os.path.exists(vector_store_path):
            raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found")
        
        # Load vector store to get document count
        vector_manager = VectorStoreManager(embedding_model=settings.EMBEDDING_MODEL)
        vectorstore = vector_manager.load_vector_store(
            persist_directory=vector_store_path,
            collection_name=document_id
        )
        
        # Get collection stats
        collection = vectorstore._collection
        doc_count = collection.count()
        
        # Check for associated files
        pickle_path = os.path.join(settings.PICKLE_DIR, f"{document_id}_processed.pkl")
        json_path = os.path.join(settings.JSON_DIR, f"{document_id}_processed.json")
        
        return {
            "success": True,
            "document_id": document_id,
            "vector_store_path": vector_store_path,
            "chunks_count": doc_count,
            "has_pickle": os.path.exists(pickle_path),
            "has_json": os.path.exists(json_path),
            "pickle_path": pickle_path if os.path.exists(pickle_path) else None,
            "json_path": json_path if os.path.exists(json_path) else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download-all")
async def download_all_project_data():
    """Download all project data as a zip file"""
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


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a specific document and all associated files"""
    try:
        deleted_items = []
        
        # Delete vector store
        vector_store_path = os.path.join(settings.CHROMA_DIR, document_id)
        if os.path.exists(vector_store_path):
            shutil.rmtree(vector_store_path)
            deleted_items.append("vector_store")
        
        # Delete pickle files
        for pkl_file in settings.PICKLE_DIR.glob(f"{document_id}*.pkl"):
            pkl_file.unlink()
            deleted_items.append(f"pickle/{pkl_file.name}")
        
        # Delete JSON files
        for json_file in settings.JSON_DIR.glob(f"{document_id}*.json"):
            json_file.unlink()
            deleted_items.append(f"json/{json_file.name}")
        
        # Delete uploaded PDF
        upload_file = os.path.join(settings.UPLOAD_DIR, f"{document_id}.pdf")
        if os.path.exists(upload_file):
            os.remove(upload_file)
            deleted_items.append("uploaded_pdf")
        
        if not deleted_items:
            raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found")
        
        return {
            "success": True,
            "message": f"Document '{document_id}' deleted successfully",
            "deleted_items": deleted_items
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "upload_dir": str(settings.UPLOAD_DIR),
        "image_dir": str(settings.IMAGE_DIR),
        "chroma_dir": str(settings.CHROMA_DIR),
        "api_version": settings.API_VERSION,
        "active_processing": len(processing_status)
    }
    
import base64
from pathlib import Path

@router.get("/documents/{document_id}/chunks")
async def view_processed_chunks(
    document_id: str,
    include_images: bool = True
):
    """
    View processed chunks for a specific document with optional image inclusion
    Returns the content of the JSON file containing processed chunks
    
    Parameters:
    - document_id: The document identifier
    - include_images: Whether to include base64-encoded images (default: True)
    """
    try:
        # Construct the JSON file path
        json_file_path = os.path.join(settings.JSON_DIR, f"{document_id}_processed.json")
        
        # Check if file exists
        if not os.path.exists(json_file_path):
            raise HTTPException(
                status_code=404, 
                detail=f"Processed chunks not found for document '{document_id}'. JSON file does not exist."
            )
        
        # Read the JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            chunks_data = json.load(f)
        
        # Process images if requested
        if include_images and isinstance(chunks_data, list):
            for chunk in chunks_data:
                if 'image_paths' in chunk and chunk['image_paths']:
                    chunk['images_base64'] = []
                    
                    for image_path in chunk['image_paths']:
                        # Construct full image path
                        full_image_path = os.path.join(settings.IMAGE_DIR, Path(image_path).name)
                        
                        try:
                            if os.path.exists(full_image_path):
                                with open(full_image_path, 'rb') as img_file:
                                    image_data = img_file.read()
                                    base64_image = base64.b64encode(image_data).decode('utf-8')
                                    
                                    # Get image extension for proper MIME type
                                    ext = Path(full_image_path).suffix.lower()
                                    mime_type = 'image/png' if ext == '.png' else 'image/jpeg'
                                    
                                    chunk['images_base64'].append({
                                        'filename': Path(image_path).name,
                                        'data': f"data:{mime_type};base64,{base64_image}",
                                        'path': image_path
                                    })
                            else:
                                chunk['images_base64'].append({
                                    'filename': Path(image_path).name,
                                    'error': 'Image file not found',
                                    'path': image_path
                                })
                        except Exception as img_error:
                            chunk['images_base64'].append({
                                'filename': Path(image_path).name,
                                'error': str(img_error),
                                'path': image_path
                            })
        
        # Get file stats
        file_stats = os.stat(json_file_path)
        file_size_kb = file_stats.st_size / 1024
        
        return {
            "success": True,
            "document_id": document_id,
            "file_path": json_file_path,
            "file_size_kb": round(file_size_kb, 2),
            "chunks_count": len(chunks_data) if isinstance(chunks_data, list) else 1,
            "images_included": include_images,
            "chunks": chunks_data
        }
    
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to parse JSON file: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error reading processed chunks: {str(e)}"
        )


@router.get("/documents/{document_id}/chunks/{chunk_index}")
async def view_single_chunk(
    document_id: str, 
    chunk_index: int,
    include_images: bool = True
):
    """
    View a specific chunk by index from processed document with optional images
    
    Parameters:
    - document_id: The document identifier
    - chunk_index: The index of the chunk (0-based)
    - include_images: Whether to include base64-encoded images (default: True)
    """
    try:
        # Construct the JSON file path
        json_file_path = os.path.join(settings.JSON_DIR, f"{document_id}_processed.json")
        
        # Check if file exists
        if not os.path.exists(json_file_path):
            raise HTTPException(
                status_code=404, 
                detail=f"Processed chunks not found for document '{document_id}'"
            )
        
        # Read the JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            chunks_data = json.load(f)
        
        # Validate chunk index
        if not isinstance(chunks_data, list):
            raise HTTPException(
                status_code=400,
                detail="Chunks data is not in expected list format"
            )
        
        if chunk_index < 0 or chunk_index >= len(chunks_data):
            raise HTTPException(
                status_code=404,
                detail=f"Chunk index {chunk_index} out of range. Valid range: 0-{len(chunks_data)-1}"
            )
        
        chunk = chunks_data[chunk_index]
        
        # Process images if requested
        if include_images and 'image_paths' in chunk and chunk['image_paths']:
            chunk['images_base64'] = []
            
            for image_path in chunk['image_paths']:
                # Construct full image path
                full_image_path = os.path.join(settings.IMAGE_DIR, Path(image_path).name)
                
                try:
                    if os.path.exists(full_image_path):
                        with open(full_image_path, 'rb') as img_file:
                            image_data = img_file.read()
                            base64_image = base64.b64encode(image_data).decode('utf-8')
                            
                            # Get image extension for proper MIME type
                            ext = Path(full_image_path).suffix.lower()
                            mime_type = 'image/png' if ext == '.png' else 'image/jpeg'
                            
                            chunk['images_base64'].append({
                                'filename': Path(image_path).name,
                                'data': f"data:{mime_type};base64,{base64_image}",
                                'path': image_path
                            })
                    else:
                        chunk['images_base64'].append({
                            'filename': Path(image_path).name,
                            'error': 'Image file not found',
                            'path': image_path
                        })
                except Exception as img_error:
                    chunk['images_base64'].append({
                        'filename': Path(image_path).name,
                        'error': str(img_error),
                        'path': image_path
                    })
        
        return {
            "success": True,
            "document_id": document_id,
            "chunk_index": chunk_index,
            "total_chunks": len(chunks_data),
            "images_included": include_images,
            "chunk": chunk
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error reading chunk: {str(e)}"
        )


@router.get("/images/{image_filename}")
async def get_image(image_filename: str):
    """
    Get a specific image file directly
    
    Parameters:
    - image_filename: Name of the image file (e.g., 'image_0001.png')
    """
    try:
        image_path = os.path.join(settings.IMAGE_DIR, image_filename)
        
        if not os.path.exists(image_path):
            raise HTTPException(
                status_code=404,
                detail=f"Image '{image_filename}' not found"
            )
        
        # Validate it's actually an image file
        allowed_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
        if Path(image_path).suffix.lower() not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type"
            )
        
        return FileResponse(
            path=image_path,
            media_type="image/png" if image_path.endswith('.png') else "image/jpeg",
            filename=image_filename
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving image: {str(e)}"
        )