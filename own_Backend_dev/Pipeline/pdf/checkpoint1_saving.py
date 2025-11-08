import json
import pickle
from pathlib import Path
from unstructured.documents.elements import Element

def save_elements(elements, pkl_path: str, json_path: str = None):
    """
    Save a Python variable `elements` to pickle and optionally to JSON.
    Automatically converts unstructured Element objects to dicts for JSON.

    Args:
        elements: Python variable to save (list, dict, etc.)
        pkl_path: Path to save the pickle file (required)
    """
    # Ensure parent directories exist
    Path(pkl_path).parent.mkdir(parents=True, exist_ok=True)
    if json_path:
        Path(json_path).parent.mkdir(parents=True, exist_ok=True)

    # Save as Pickle
    with open(pkl_path, "wb") as f:
        pickle.dump(elements, f)
    print(f"✅ Saved elements to pickle: {pkl_path}")

    # # Save as JSON (optional)
    # if json_path:
    #     # Convert Element objects to dicts automatically
    #     def to_serializable(el):
    #         return el.to_dict() if isinstance(el, Element) else el
        
    #     elements_serializable = [to_serializable(el) for el in elements]

    #     with open(json_path, "w", encoding="utf-8") as f:
    #         json.dump(elements_serializable, f, indent=4, ensure_ascii=False)
    #     print(f"✅ Saved elements to JSON: {json_path}")


# -----------------------------
# Example usage
# your Python variable, e.g., output of partition_pdf



############  Using the partition_document_launcher function from docs_partition.py  ############
# pkl_file = r"D:\MultiModulRag\Backend\SmartPipelinedef\Pickel\checkpoint1.pkl"

# save_elements(checkpoint1, pkl_file) 