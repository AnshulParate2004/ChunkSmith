import json
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

def create_vector_store(documents, persist_directory=r"D:\MultiModulRag\Backend_dev\Database\chroma_db"):
    """Create and persist ChromaDB vector store"""
    print("🔮 Creating embeddings and storing in ChromaDB...")
    
    # Convert list metadata to JSON strings
    for doc in documents:
        if "raw_tables_html" in doc.metadata:
            doc.metadata["raw_tables_html"] = json.dumps(doc.metadata["raw_tables_html"])
        if "image_paths" in doc.metadata:
            doc.metadata["image_paths"] = json.dumps(doc.metadata["image_paths"])
        if "page_numbers" in doc.metadata:
            doc.metadata["page_numbers"] = json.dumps(doc.metadata["page_numbers"])
        if "content_types" in doc.metadata:
            doc.metadata["content_types"] = json.dumps(doc.metadata["content_types"])
    
    embedding_model = GoogleGenerativeAIEmbeddings(model="text-embedding-004")
    
    print("--- Creating vector store ---")
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embedding_model,
        persist_directory=persist_directory,
        collection_metadata={"hnsw:space": "cosine"}
    )
    print("--- Finished creating vector store ---")
    
    print(f"✅ Vector store created and saved to {persist_directory}")
    return vectorstore

# Create the vector store
db = create_vector_store(loaded_docs)