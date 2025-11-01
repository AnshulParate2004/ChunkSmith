import os, json, pickle

pkl_path = r"D:\MultiModulRag\Backend\SmartPipelinedef\Pickel\output.pkl"
json_path = r"D:\MultiModulRag\Backend\SmartPipelinedef\JSON\output.json"

os.makedirs(os.path.dirname(pkl_path), exist_ok=True)
os.makedirs(os.path.dirname(json_path), exist_ok=True)

# 💾 Save Pickle
with open(pkl_path, "wb") as f:
    pickle.dump(output, f)
print(f"✅ Pickle saved: {pkl_path}")

# 🧩 Convert to clean JSON format (including enhanced content)
clean_json = [
    {
        "chunk_index": doc.metadata.get("chunk_index"),
        "enhanced_content": getattr(doc, "page_content", ""),  # from Document
        "original_text": doc.metadata.get("original_text", ""),
        "raw_tables_html": doc.metadata.get("raw_tables_html", []),
        "image_paths": doc.metadata.get("image_paths", []),
        "page_numbers": doc.metadata.get("page_numbers", []),
        "content_types": doc.metadata.get("content_types", []),
    }
    for doc in output
]

# 💾 Save JSON
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(clean_json, f, indent=4, ensure_ascii=False)

print(f"✅ JSON saved: {json_path}")
