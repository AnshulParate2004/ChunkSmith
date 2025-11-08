"""FastAPI routes for document processing"""
import os
import shutil
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List

from config.settings import settings
from core.document_parser import DocumentParser
from core.content_processor import ContentProcessor
from core.vector_store import VectorStoreManager
from utils.file_helpers import FileHandler

router = APIRouter()


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


@router.post("/process-pdf", response_model=ProcessResponse)
async def process_pdf(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    max_characters: int = settings.MAX_CHARACTERS,
    new_after_n_chars: int = settings.NEW_AFTER_N_CHARS,
    combine_text_under_n_chars: int = settings.COMBINE_TEXT_UNDER_N_CHARS,
    extract_images: bool = settings.EXTRACT_IMAGES,
    extract_tables: bool = settings.EXTRACT_TABLES,
):
    """
    Process a PDF document through the entire pipeline:
    1. Upload and validate PDF
    2. Parse and chunk document
    3. Extract images and tables
    4. Generate AI summaries
    5. Create vector store
    6. Save outputs (pickle, JSON)
    """
    
    # Generate unique document ID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    document_id = f"{file.filename.replace('.pdf', '')}_{timestamp}"
    
    try:
        # Step 1: Validate and save uploaded file
        print(f"\n{'='*60}")
        print(f"📥 STEP 1: Uploading file: {file.filename}")
        print(f"{'='*60}")
        
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        # Save uploaded file
        upload_path = os.path.join(settings.UPLOAD_DIR, f"{document_id}.pdf")
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Validate PDF
        is_valid, error_msg = FileHandler.validate_pdf(upload_path, settings.MAX_FILE_SIZE // (1024 * 1024))
        if not is_valid:
            os.remove(upload_path)
            raise HTTPException(status_code=400, detail=error_msg)
        
        print(f"✅ File uploaded successfully: {upload_path}")
        
        # Step 2: Parse document
        print(f"\n{'='*60}")
        print(f"📄 STEP 2: Parsing PDF document")
        print(f"{'='*60}")
        
        parser = DocumentParser(image_output_dir=str(settings.IMAGE_DIR))
        elements = parser.partition_pdf_document(
            file_path=upload_path,
            max_characters=max_characters,
            new_after_n_chars=new_after_n_chars,
            combine_text_under_n_chars=combine_text_under_n_chars,
            extract_images=extract_images,
            extract_tables=extract_tables,
            languages=settings.LANGUAGES
        )
        
        # Save checkpoint 1 (raw elements)
        checkpoint1_path = os.path.join(settings.PICKLE_DIR, f"{document_id}_checkpoint1.pkl")
        FileHandler.save_pickle(elements, checkpoint1_path)
        
        # Step 3: Process chunks with AI
        print(f"\n{'='*60}")
        print(f"🧠 STEP 3: Processing chunks with AI summaries")
        print(f"{'='*60}")
        
        processor = ContentProcessor(
            image_dir=str(settings.IMAGE_DIR),
            model_name=settings.GEMINI_MODEL,
            temperature=settings.TEMPERATURE
        )
        documents = processor.summarise_chunks(elements)
        
        # Count images
        image_count = len(list(settings.IMAGE_DIR.glob("*.png")))
        
        # Save processed documents
        output_pickle_path = os.path.join(settings.PICKLE_DIR, f"{document_id}_processed.pkl")
        output_json_path = os.path.join(settings.JSON_DIR, f"{document_id}_processed.json")
        
        FileHandler.save_pickle(documents, output_pickle_path)
        FileHandler.save_json(documents, output_json_path)
        
        # Step 4: Create vector store
        print(f"\n{'='*60}")
        print(f"🔮 STEP 4: Creating vector store")
        print(f"{'='*60}")
        
        vector_store_path = os.path.join(settings.CHROMA_DIR, document_id)
        vector_manager = VectorStoreManager(embedding_model=settings.EMBEDDING_MODEL)
        vectorstore = vector_manager.create_vector_store(
            documents=documents,
            persist_directory=vector_store_path,
            collection_name=document_id
        )
        
        print(f"\n{'='*60}")
        print(f"✅ PROCESSING COMPLETE!")
        print(f"{'='*60}")
        print(f"📊 Document ID: {document_id}")
        print(f"📄 Chunks processed: {len(documents)}")
        print(f"🖼️  Images extracted: {image_count}")
        print(f"{'='*60}\n")
        
        return ProcessResponse(
            success=True,
            message="Document processed successfully",
            document_id=document_id,
            chunks_processed=len(documents),
            images_extracted=image_count,
            pickle_path=output_pickle_path,
            json_path=output_json_path,
            vector_store_path=vector_store_path
        )
    
    except Exception as e:
        # Cleanup on failure
        if os.path.exists(upload_path):
            os.remove(upload_path)
        
        print(f"\n❌ ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_documents(request: SearchRequest):
    """
    Search documents in vector store
    """
    try:
        # Determine which vector store to search
        if request.document_id:
            vector_store_path = os.path.join(settings.CHROMA_DIR, request.document_id)
            if not os.path.exists(vector_store_path):
                raise HTTPException(status_code=404, detail=f"Document ID '{request.document_id}' not found")
            collection_name = request.document_id
        else:
            # Search in default/combined store
            vector_store_path = str(settings.CHROMA_DIR)
            collection_name = "multimodal_rag"
        
        # Load vector store
        vector_manager = VectorStoreManager(embedding_model=settings.EMBEDDING_MODEL)
        vectorstore = vector_manager.load_vector_store(
            persist_directory=vector_store_path,
            collection_name=collection_name
        )
        
        # Perform search
        results = vector_manager.search(vectorstore, request.query, k=request.k)
        
        # Format results
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
    """
    Download all project data as a zip file containing:
    - Pickle files (.pkl)
    - JSON files (.json)
    - Image files
    - Chroma DB data
    """
    import zipfile
    import tempfile
    from fastapi.responses import FileResponse
    
    try:
        # Create temporary zip file
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            
            # Add pickle files
            if settings.PICKLE_DIR.exists():
                for pkl_file in settings.PICKLE_DIR.glob("*.pkl"):
                    zipf.write(pkl_file, f"pickle/{pkl_file.name}")
            
            # Add JSON files
            if settings.JSON_DIR.exists():
                for json_file in settings.JSON_DIR.glob("*.json"):
                    zipf.write(json_file, f"json/{json_file.name}")
            
            # Add image files
            if settings.IMAGE_DIR.exists():
                for img_file in settings.IMAGE_DIR.glob("*"):
                    if img_file.is_file():
                        zipf.write(img_file, f"images/{img_file.name}")
            
            # Add ChromaDB data
            if settings.CHROMA_DIR.exists():
                for chroma_item in settings.CHROMA_DIR.rglob("*"):
                    if chroma_item.is_file():
                        rel_path = chroma_item.relative_to(settings.CHROMA_DIR)
                        zipf.write(chroma_item, f"chroma_db/{rel_path}")
        
        print(f"✅ Created project data archive: {temp_zip.name}")
        
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
        "chroma_dir": str(settings.CHROMA_DIR)
    }