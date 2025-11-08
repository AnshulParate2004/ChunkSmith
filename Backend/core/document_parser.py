"""Document parsing module using unstructured library"""
import os
from pathlib import Path
from typing import List
from unstructured.partition.pdf import partition_pdf


class DocumentParser:
    """Handles PDF document parsing and chunking"""
    
    def __init__(self, image_output_dir: str):
        self.image_output_dir = image_output_dir
        Path(image_output_dir).mkdir(parents=True, exist_ok=True)
    
    def partition_pdf_document(
        self,
        file_path: str,
        max_characters: int,
        new_after_n_chars: int,
        combine_text_under_n_chars: int,
        extract_images: bool = True,
        extract_tables: bool = True,
        languages: List[str] = ['eng']
    ):
        """
        Extract elements from PDF using unstructured library.
        
        Args:
            file_path: Path to the PDF file
            max_characters: Maximum characters per chunk
            new_after_n_chars: Start new chunk after this many characters
            combine_text_under_n_chars: Combine small text blocks
            extract_images: Whether to extract images
            extract_tables: Whether to infer table structure
            languages: List of language codes
        
        Returns:
            List of extracted elements
        """
        # Validate file
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        # Validate chunk parameters
        if max_characters >= new_after_n_chars:
            raise ValueError("max_characters must be less than new_after_n_chars")
        
        print(f"📄 Partitioning document: {file_path}")
        print(f"⚙️  Settings: Images={extract_images}, Tables={extract_tables}, Languages={languages}")
        print(f"📊 Chunk settings: max={max_characters}, new_after={new_after_n_chars}, combine={combine_text_under_n_chars}")

        elements = partition_pdf(
            filename=file_path,
            strategy="hi_res",
            hi_res_model_name="yolox",
            chunking_strategy="by_title",
            include_orig_elements=True,
            languages=languages,
            extract_images_in_pdf=extract_images,
            extract_image_block_to_payload=extract_images,
            extract_image_block_output_dir=self.image_output_dir if extract_images else None,
            extract_image_block_types=["Image"] if extract_images else [],
            infer_table_structure=extract_tables,
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