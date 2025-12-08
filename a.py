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