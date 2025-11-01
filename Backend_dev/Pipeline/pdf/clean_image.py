import os
from pathlib import Path

def clean_image_directory(image_dir: str) -> None:
    """Clean existing images from directory"""
    Path(image_dir).mkdir(parents=True, exist_ok=True)
    
    for file in Path(image_dir).glob("*"):
        if file.is_file():
            try:
                file.unlink()
                print(f"     🗑️  Deleted old image: {file.name}")
            except Exception as e:
                print(f"     ⚠️  Could not delete {file.name}: {e}")