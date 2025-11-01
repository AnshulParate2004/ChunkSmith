from clean_image import clean_image_directory
from docs_combining import separate_content_types
from docs_aisummary import create_ai_enhanced_summary
from langchain_core.documents import Document

def summarise_chunks(chunks, image_dir: str = r"D:\MultiModulRag\Backend\SmartPipelinedef\Images") -> list[Document]:
    
    """
    Process all chunks with AI Summaries.

    Args:
        chunks: List of document chunks to process
        image_dir: Directory to store extracted images
        
    Returns:
        List of LangChain Documents with enhanced summaries
    """

    print("🧠 Processing chunks with AI Summaries...")
    
    # Clean image directory once
    clean_image_directory(image_dir)
    
    langchain_documents = []
    total_chunks = len(chunks)
    image_counter = {'count': 1}  # Use mutable dict to pass by reference
    
    for i, chunk in enumerate(chunks, 1):
        print(f"\n   📄 Processing chunk {i}/{total_chunks}")
        
        # Analyze chunk content
        content_data = separate_content_types(chunk, image_dir, image_counter)
        
        # Debug info
        print(f"     Types found: {', '.join(content_data['types'])}")
        print(f"     Tables: {len(content_data['tables'])}, Images: {len(content_data['image_base64'])}")
        if content_data['page_no']:
            print(f"     Pages: {content_data['page_no']}")
        
        # Create AI-enhanced summary for ALL chunks
        print(f"      Creating AI summary...")
        try:
            enhanced_content = create_ai_enhanced_summary(
                content_data['text'],
                content_data['tables'], 
                content_data['image_base64']
            )
            print(f"      AI summary created")
            print(f"     Preview: {enhanced_content[:150]}...")
        except Exception as e:
            print(f"      AI summary failed, using raw text: {e}")
            enhanced_content = content_data['text']
        
        # Create LangChain Document with metadata
        # Store image paths instead of base64 to reduce memory usage
        doc = Document(
            page_content=enhanced_content,
                # 'text': chunk.text,
                # 'tables': [],
                # 'images_base64': [],
                # 'images_dirpath': [],
                # 'page_no': [],
                # 'types': ['text']
            metadata={
                "chunk_index": i,
                "original_text": content_data['text'],
                "raw_tables_html": content_data['tables'],
                "image_paths": content_data['images_dirpath'],
                "page_numbers": content_data['page_no'],
                "content_types": content_data['types'],
                # "num_tables": len(content_data['tables']),
                # "num_images": len(content_data['images_dirpath']),
                # "original_content": json.dumps({
                # "raw_text": content_data['text'],
                # Don't store base64 in metadata to save space
                # "has_images": len(content_data['images_base64']) > 0
                # })
            }
        )
        
        langchain_documents.append(doc)
    
    print(f"\n✅ Successfully processed {len(langchain_documents)} chunks")
    print(f"📊 Total images saved: {image_counter['count'] - 1}")
    
    return langchain_documents

# output = summarise_chunks(loaded1)