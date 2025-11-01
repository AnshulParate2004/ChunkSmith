import os
from pathlib import Path
from typing import List
from unstructured.partition.pdf import partition_pdf

def partition_document_launcher(
    file_path: str,
    max_characters: int,
    new_after_n_chars: int,
    combine_text_under_n_chars: int,
    extract_images: bool = False,
    extract_tables: bool = False,
    languages: List[str] = ['eng']
):
    """
    Extract elements from PDF using unstructured library.
    
    Args:
        file_path: Path to the PDF file to process (REQUIRED)
        max_characters: Maximum characters per chunk (REQUIRED)
        new_after_n_chars: Start new chunk after this many characters (REQUIRED)
        combine_text_under_n_chars: Combine small text blocks under this count (REQUIRED)
        extract_images: Whether to extract images from the PDF 'True' or 'False'
        extract_tables: Whether to infer table structure 'True' or 'False'
        languages: List of language codes (defaults to ['eng'])
    
    Returns:
        List of extracted elements from the PDF
    
    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        ValueError: If invalid parameters are provided
    """
    # Validate input file
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    
    # Validate chunk parameters
    if max_characters >= new_after_n_chars:
        raise ValueError("max_characters must be less than new_after_n_chars")
    
    # Set image output directory (fixed path)
    image_output_dir = r"D:\MultiModulRag\Backend\SmartPipelinedef\Images"
    
    # Create image directory if extracting images
    if extract_images:
        Path(image_output_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"📄 Partitioning document: {file_path}")
    print(f"⚙️  Settings: Images={extract_images}, Tables={extract_tables}, Languages={languages}")
    print(f"📊 Chunk settings: max={max_characters}, new_after={new_after_n_chars}, combine={combine_text_under_n_chars}")

    elements = partition_pdf(
        ### File path is always require and important ###
        filename=file_path,

        ### Core parameters (Fixed Parameters) ###
        strategy="hi_res",
        hi_res_model_name="yolox",
        chunking_strategy="by_title",
        include_orig_elements=True,

        ### Language and extraction parameters ###
        languages=languages,  # Use the parameter instead of empty list
        
        ### Image extraction parameters ###
        extract_images_in_pdf=extract_images,
        extract_image_block_to_payload=extract_images,
        extract_image_block_output_dir=image_output_dir if extract_images else None,
        extract_image_block_types=["Image"] if extract_images else [],
        
        ### Table extraction ###
        infer_table_structure=extract_tables,  # Use the parameter
        
        ### Chunk parameters ###
        max_characters=max_characters,
        new_after_n_chars=new_after_n_chars,
        combine_text_under_n_chars=combine_text_under_n_chars,
    )
    
    print(f"✅ Extracted {len(elements)} elements")
    
    # Print element breakdown
    element_types = {}
    for elem in elements:
        elem_type = type(elem).__name__
        element_types[elem_type] = element_types.get(elem_type, 0) + 1
    print(f"📋 Element breakdown: {dict(element_types)}")
    
    return elements