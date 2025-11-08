"""Vector store operations using ChromaDB"""
import json
from typing import List
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma


class VectorStoreManager:
    """Manages ChromaDB vector store operations"""
    
    def __init__(self, embedding_model: str = "text-embedding-004"):
        self.embedding_model = GoogleGenerativeAIEmbeddings(model=embedding_model)
    
    def create_vector_store(
        self, 
        documents: List[Document], 
        persist_directory: str,
        collection_name: str = "multimodal_rag"
    ):
        """
        Create and persist ChromaDB vector store
        
        Args:
            documents: List of LangChain documents
            persist_directory: Directory to persist the database
            collection_name: Name of the collection
            
        Returns:
            ChromaDB vector store instance
        """
        print("🔮 Creating embeddings and storing in ChromaDB...")
        
        # Convert list metadata to JSON strings (ChromaDB requirement)
        for doc in documents:
            if "raw_tables_html" in doc.metadata:
                doc.metadata["raw_tables_html"] = json.dumps(doc.metadata["raw_tables_html"])
            if "image_paths" in doc.metadata:
                doc.metadata["image_paths"] = json.dumps(doc.metadata["image_paths"])
            if "page_numbers" in doc.metadata:
                doc.metadata["page_numbers"] = json.dumps(doc.metadata["page_numbers"])
            if "content_types" in doc.metadata:
                doc.metadata["content_types"] = json.dumps(doc.metadata["content_types"])
        
        print("--- Creating vector store ---")
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embedding_model,
            persist_directory=persist_directory,
            collection_name=collection_name,
            collection_metadata={"hnsw:space": "cosine"}
        )
        print("--- Finished creating vector store ---")
        
        print(f"✅ Vector store created with {len(documents)} documents")
        print(f"💾 Saved to {persist_directory}")
        
        return vectorstore
    
    def load_vector_store(
        self, 
        persist_directory: str,
        collection_name: str = "multimodal_rag"
    ):
        """
        Load existing ChromaDB vector store
        
        Args:
            persist_directory: Directory where database is persisted
            collection_name: Name of the collection
            
        Returns:
            ChromaDB vector store instance
        """
        print(f"📂 Loading vector store from {persist_directory}")
        
        vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embedding_model,
            collection_name=collection_name
        )
        
        print(f"✅ Vector store loaded successfully")
        return vectorstore
    
    def search(
        self, 
        vectorstore, 
        query: str, 
        k: int = 5,
        filter_dict: dict = None
    ):
        """
        Search the vector store
        
        Args:
            vectorstore: ChromaDB instance
            query: Search query
            k: Number of results to return
            filter_dict: Optional metadata filter
            
        Returns:
            List of relevant documents
        """
        print(f"🔍 Searching for: {query}")
        
        if filter_dict:
            results = vectorstore.similarity_search(query, k=k, filter=filter_dict)
        else:
            results = vectorstore.similarity_search(query, k=k)
        
        print(f"✅ Found {len(results)} results")
        return results