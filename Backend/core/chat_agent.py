"""
AI Chat Agent with RAG capabilities
File: D:\MultiModulRag\Backend\core\chat_agent.py
"""
import os
import json
import base64
from pathlib import Path
from typing import List, Dict, AsyncGenerator
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from core.vector_store import VectorStoreManager
from config.settings import settings
from dotenv import load_dotenv
import re

load_dotenv()


class ChatAgent:
    """Chat agent with RAG capabilities"""
    
    def __init__(self, document_id: str):
        """
        Initialize chat agent for a specific document
        
        Args:
            document_id: ID of the document to chat about
        """
        self.document_id = document_id
        self.conversation_history = []
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            temperature=0.2,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            streaming=True
        )
        
        # Load vector store
        vector_store_path = os.path.join(settings.CHROMA_DIR, document_id)
        if not os.path.exists(vector_store_path):
            raise FileNotFoundError(f"Vector store not found for document: {document_id}")
        
        self.vector_manager = VectorStoreManager(embedding_model=settings.EMBEDDING_MODEL)
        self.vectorstore = self.vector_manager.load_vector_store(
            persist_directory=vector_store_path,
            collection_name=document_id
        )
        
        # System prompt
        self.system_prompt = """You are a helpful AI assistant that answers questions based on document content.

INSTRUCTIONS:
1. Use the provided context from the document to answer questions
2. When images are RELEVANT and would help answer the question, mention them using this EXACT format:
   [SHOW_IMAGE: filename.png]
3. Only mention images that directly support your answer
4. If tables are relevant, describe them clearly
5. If the answer isn't in the context, say so honestly
6. Be concise but thorough

IMPORTANT: Only use [SHOW_IMAGE: filename.png] format when an image would genuinely help answer the user's question.

CONTEXT:
{context}

CONVERSATION HISTORY:
{chat_history}

Answer the user's question based on the context and conversation history."""
    
    def search_relevant_context(self, query: str, k: int = 5) -> List[Dict]:
        """
        Search for relevant context in vector store
        
        Args:
            query: User's question
            k: Number of results to retrieve
            
        Returns:
            List of relevant document chunks with metadata
        """
        results = self.vector_manager.search(
            vectorstore=self.vectorstore,
            query=query,
            k=k
        )
        
        context_chunks = []
        for doc in results:
            chunk_data = {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "original_text": doc.metadata.get("original_text", ""),
                "ai_summary": doc.metadata.get("ai_summary", ""),
                "image_paths": json.loads(doc.metadata.get("image_paths", "[]")) if isinstance(doc.metadata.get("image_paths"), str) else doc.metadata.get("image_paths", []),
                "page_numbers": json.loads(doc.metadata.get("page_numbers", "[]")) if isinstance(doc.metadata.get("page_numbers"), str) else doc.metadata.get("page_numbers", []),
                "tables": json.loads(doc.metadata.get("raw_tables_html", "[]")) if isinstance(doc.metadata.get("raw_tables_html"), str) else doc.metadata.get("raw_tables_html", [])
            }
            context_chunks.append(chunk_data)
        
        return context_chunks
    
    def get_image_base64(self, image_path: str) -> str:
        """
        Get base64 encoded image
        
        Args:
            image_path: Relative path to image
            
        Returns:
            Base64 encoded image with data URI
        """
        try:
            # Construct full path
            full_path = os.path.join(settings.IMAGE_DIR, Path(image_path).name)
            
            if os.path.exists(full_path):
                with open(full_path, 'rb') as img_file:
                    image_data = img_file.read()
                    base64_image = base64.b64encode(image_data).decode('utf-8')
                    
                    # Determine MIME type
                    ext = Path(full_path).suffix.lower()
                    mime_type = 'image/png' if ext == '.png' else 'image/jpeg'
                    
                    return f"data:{mime_type};base64,{base64_image}"
            else:
                return None
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return None
    
    def format_context(self, context_chunks: List[Dict]) -> str:
        """Format context chunks for prompt"""
        formatted_context = []
        
        for i, chunk in enumerate(context_chunks, 1):
            chunk_text = f"\n--- Context Chunk {i} ---\n"
            chunk_text += f"Summary: {chunk['ai_summary']}\n"
            
            if chunk['page_numbers']:
                chunk_text += f"Pages: {chunk['page_numbers']}\n"
            
            if chunk['image_paths']:
                chunk_text += f"Available Images: {', '.join([Path(p).name for p in chunk['image_paths']])}\n"
            
            if chunk['tables']:
                chunk_text += f"Contains {len(chunk['tables'])} table(s)\n"
            
            chunk_text += f"\nContent:\n{chunk['original_text'][:500]}...\n"
            formatted_context.append(chunk_text)
        
        return "\n".join(formatted_context)
    
    def format_chat_history(self) -> str:
        """Format conversation history"""
        if not self.conversation_history:
            return "No previous conversation"
        
        history = []
        for msg in self.conversation_history[-6:]:  # Last 3 exchanges
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            history.append(f"{role}: {msg.content}")
        
        return "\n".join(history)
    
    def extract_image_references(self, text: str) -> tuple[str, List[str]]:
        """
        Extract [SHOW_IMAGE: filename.png] references from AI response
        
        Args:
            text: AI response text
            
        Returns:
            Tuple of (cleaned_text, list_of_image_filenames)
        """
        # Pattern to match [SHOW_IMAGE: filename.png]
        pattern = r'\[SHOW_IMAGE:\s*([^\]]+)\]'
        
        # Find all image references
        image_refs = re.findall(pattern, text)
        
        # Remove the [SHOW_IMAGE: ...] tags from text
        cleaned_text = re.sub(pattern, '', text)
        
        # Clean up image filenames
        image_filenames = [ref.strip() for ref in image_refs]
        
        return cleaned_text, image_filenames
    
    def find_image_path(self, filename: str, context_chunks: List[Dict]) -> str:
        """
        Find the full path of an image by filename
        
        Args:
            filename: Image filename (e.g., "image_0001.png")
            context_chunks: Context chunks containing image paths
            
        Returns:
            Full image path or None
        """
        for chunk in context_chunks:
            for img_path in chunk['image_paths']:
                if Path(img_path).name == filename:
                    return img_path
        return None
    
    async def chat_stream(
        self, 
        user_message: str
    ) -> AsyncGenerator[Dict, None]:
        """
        Stream chat responses with SSE
        
        Args:
            user_message: User's message
            
        Yields:
            Dict with event type and data
        """
        try:
            # Step 1: Search for relevant context
            yield {
                "type": "search_start",
                "data": {"message": "Searching document for relevant information..."}
            }
            
            context_chunks = self.search_relevant_context(user_message, k=5)
            
            yield {
                "type": "search_complete",
                "data": {
                    "message": f"Found {len(context_chunks)} relevant sections",
                    "chunks_count": len(context_chunks)
                }
            }
            
            # Step 2: Format context and generate response
            context_text = self.format_context(context_chunks)
            chat_history_text = self.format_chat_history()
            
            # Create prompt
            prompt = self.system_prompt.format(
                context=context_text,
                chat_history=chat_history_text
            )
            
            # Prepare messages
            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content=user_message)
            ]
            
            # Step 3: Stream AI response
            yield {
                "type": "response_start",
                "data": {"message": "Generating response..."}
            }
            
            full_response = ""
            async for chunk in self.llm.astream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    content = chunk.content
                    full_response += content
                    
                    yield {
                        "type": "content",
                        "data": {"content": content}
                    }
            
            # Step 4: Extract image references from AI response
            cleaned_response, image_filenames = self.extract_image_references(full_response)
            
            # Step 5: Send only referenced images
            images_sent = 0
            if image_filenames:
                yield {
                    "type": "images_found",
                    "data": {
                        "message": f"AI referenced {len(image_filenames)} image(s)",
                        "count": len(image_filenames)
                    }
                }
                
                for filename in image_filenames:
                    # Find the image path in context
                    img_path = self.find_image_path(filename, context_chunks)
                    
                    if img_path:
                        image_base64 = self.get_image_base64(img_path)
                        if image_base64:
                            yield {
                                "type": "image",
                                "data": {
                                    "filename": filename,
                                    "data": image_base64,
                                    "path": img_path
                                }
                            }
                            images_sent += 1
            
            # Step 6: Update conversation history (with cleaned response)
            self.conversation_history.append(HumanMessage(content=user_message))
            self.conversation_history.append(AIMessage(content=cleaned_response))
            
            # Keep only last 10 messages
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            # Step 7: Send completion
            yield {
                "type": "complete",
                "data": {
                    "message": "Response complete",
                    "images_shown": images_sent,
                    "context_chunks": len(context_chunks)
                }
            }
            
        except Exception as e:
            yield {
                "type": "error",
                "data": {
                    "message": str(e),
                    "error": str(e)
                }
            }
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        