"""Content processing module with multi-API key async processing"""
import os
import base64
import asyncio
from pathlib import Path
from typing import List, Dict
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class AIParser(BaseModel):
    """AI Parser Model for text, image and table information"""
    question: str = Field(description="List all potential questions that can be answered from this content (text, images, tables). Try to keep words similar to original content")
    summary: str = Field(description="Comprehensive summary of all data and information. Try to keep words similar to original content")
    image_interpretation: str = Field(description="Detailed description of image content. If images are irrelevant or contain only decorative elements, state: ***DO NOT USE THIS IMAGE***")
    table_interpretation: str = Field(description="Detailed description of table content. If tables are irrelevant, state: ***DO NOT USE THIS TABLE***")


class ContentProcessor:
    """Processes document chunks with AI-enhanced summaries using multiple API keys"""
    
    def __init__(self, image_dir: str, model_name: str = "gemini-2.0-flash-exp", temperature: float = 0):
        self.image_dir = image_dir
        self.model_name = model_name
        self.temperature = temperature
        
        # Load all available API keys from environment
        self.api_keys = self._load_api_keys()
        
        if not self.api_keys:
            raise ValueError("No GOOGLE_API_KEY found in environment")
        
        print(f"✅ Initialized ContentProcessor with {len(self.api_keys)} API keys")
        print(f"✅ Model: {model_name}")
        
        Path(image_dir).mkdir(parents=True, exist_ok=True)
    
    def _load_api_keys(self) -> List[str]:
        """
        Load all available Google API keys from environment
        Looks for GOOGLE_API_KEY_1 through GOOGLE_API_KEY_10
        Falls back to GOOGLE_API_KEY if numbered keys not found
        
        Returns:
            List of API keys
        """
        api_keys = []
        
        # Try to load numbered API keys (1-10)
        for i in range(1, 11):
            key = os.getenv(f"GOOGLE_API_KEY_{i}")
            if key and key.strip():
                api_keys.append(key.strip())
        
        # Fallback to single GOOGLE_API_KEY if no numbered keys found
        if not api_keys:
            single_key = os.getenv("GOOGLE_API_KEY")
            if single_key and single_key.strip():
                api_keys.append(single_key.strip())
        
        return api_keys
    
    def _get_llm_for_key(self, api_key: str):
        """
        Create LLM instance for specific API key
        
        Args:
            api_key: Google API key
            
        Returns:
            LLM instance with structured output
        """
        llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=self.temperature,
            google_api_key=api_key
        )
        return llm.with_structured_output(AIParser)
    
    @staticmethod
    def clean_directory(base_dir: Path) -> None:
        """
        Clean all project data directories before processing new PDF.
        Deletes: pickle files, JSON files, images, and ChromaDB data.
        
        Args:
            base_dir: Base data directory containing all subdirectories
        """
        from config.settings import settings
        
        directories_to_clean = [
            (settings.PICKLE_DIR, "*.pkl", "Pickle files"),
            (settings.JSON_DIR, "*.json", "JSON files"),
            (settings.IMAGE_DIR, "*", "Image files"),
            (settings.CHROMA_DIR, "*", "ChromaDB data")
        ]
        
        print("\n🧹 Cleaning workspace before processing new PDF...")
        print("="*60)
        
        for directory, pattern, description in directories_to_clean:
            if not directory.exists():
                continue
            
            deleted_count = 0
            
            # For ChromaDB, delete entire subdirectories
            if directory == settings.CHROMA_DIR:
                for item in directory.iterdir():
                    if item.is_dir():
                        try:
                            import shutil
                            shutil.rmtree(item)
                            deleted_count += 1
                            print(f"  🗑️  Deleted ChromaDB collection: {item.name}")
                        except Exception as e:
                            print(f"  ⚠️  Could not delete {item.name}: {e}")
            else:
                # For other directories, delete matching files
                for file in directory.glob(pattern):
                    if file.is_file():
                        try:
                            file.unlink()
                            deleted_count += 1
                        except Exception as e:
                            print(f"  ⚠️  Could not delete {file.name}: {e}")
            
            if deleted_count > 0:
                print(f"  ✅ Deleted {deleted_count} {description}")
        
        print("="*60)
        print("✅ Workspace cleaned successfully!\n")
    
    def separate_content_types(self, chunk, image_counter: dict) -> Dict:
        """
        Analyze chunk content and extract text, tables, and images.
        
        Args:
            chunk: Document chunk to process
            image_counter: Mutable dict to track image counter
            
        Returns:
            Dictionary with separated content types
        """
        content_data = {
            'text': chunk.text,
            'tables': [],
            'image_base64': [],
            'images_dirpath': [],
            'page_no': [],
            'types': ['text']
        }

        for element in chunk.metadata.orig_elements:
            element_type = type(element).__name__

            # Handle page numbers
            if 'metadata' in element.to_dict():
                page_no = element.to_dict()['metadata'].get('page_number')
                if page_no and page_no not in content_data['page_no']:
                    content_data['page_no'].append(page_no)

            # Handle tables
            if element_type == 'Table':
                if 'table' not in content_data['types']:
                    content_data['types'].append('table')
                table_html = getattr(element.metadata, 'text_as_html', element.text)
                content_data['tables'].append(table_html)

            # Handle images
            elif element_type == 'Image':
                if hasattr(element.metadata, 'image_base64'):
                    if 'image' not in content_data['types']:
                        content_data['types'].append('image')

                    image_base64 = element.metadata.image_base64

                    try:
                        # Generate filename and path
                        image_filename = f"image_{image_counter['count']:04d}.png"
                        image_path = os.path.join(self.image_dir, image_filename)

                        # Decode and save image
                        with open(image_path, "wb") as img_file:
                            img_file.write(base64.b64decode(image_base64))

                        # Store relative path
                        folder_name = os.path.basename(self.image_dir.rstrip(os.sep))
                        relative_path = os.path.join(folder_name, image_filename).replace("\\", "/")
                        content_data['images_dirpath'].append(relative_path)

                        # Keep base64 for AI processing
                        content_data['image_base64'].append(image_base64)

                        print(f"     ✅ Saved: {relative_path}")
                        image_counter['count'] += 1

                    except Exception as e:
                        print(f"     ❌ Failed to save image {image_counter['count']}: {e}")

        return content_data
    
    async def create_ai_enhanced_summary_async(
        self, 
        text: str, 
        tables: List[str], 
        images: List[str],
        api_key: str,
        chunk_index: int
    ) -> AIParser:
        """
        Create AI-enhanced summary asynchronously with specific API key
        
        Args:
            text: Text content to summarize
            tables: List of HTML tables
            images: List of base64 encoded images
            api_key: Google API key to use
            chunk_index: Index of chunk for logging
        
        Returns:
            AIParser object with structured summary
        """
        
        try:
            # Build prompt
            prompt_text = f"""You are creating a searchable description for document content retrieval.

CONTENT TO ANALYZE:

TEXT CONTENT:
{text}

"""
            
            if tables:
                prompt_text += "TABLES:\n"
                for i, table in enumerate(tables, 1):
                    prompt_text += f"Table {i}:\n{table}\n\n"
            
            prompt_text += """
YOUR TASK:
Generate a comprehensive, searchable description that covers:

1. Key facts, numbers, and data points from text and tables
2. Main topics and concepts discussed  
3. Questions this content could answer
4. Visual content analysis (charts, diagrams, patterns in images)
5. Alternative search terms users might use

Make it detailed and searchable - prioritize findability over brevity.
Keep words similar to the original content for better search accuracy.

IMPORTANT: Return structured output with these fields:
- question: All potential questions this content answers
- summary: Comprehensive summary of all information
- image_interpretation: Description of images (or "***DO NOT USE THIS IMAGE***" if irrelevant)
- table_interpretation: Description of tables (or "***DO NOT USE THIS TABLE***" if irrelevant)
"""

            message_content = [{"type": "text", "text": prompt_text}]
            
            for img_b64 in images:
                message_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                })
            
            message = HumanMessage(content=message_content)
            
            # Get LLM for this specific API key
            llm_structured = self._get_llm_for_key(api_key)
            
            # Make async API call
            print(f"     🔄 Chunk {chunk_index}: Sending to API (key #{self.api_keys.index(api_key) + 1})")
            response = await llm_structured.ainvoke([message])
            print(f"     ✅ Chunk {chunk_index}: Response received")
            
            return response
                
        except Exception as e:
            # Return fallback on any error
            print(f"     ❌ Chunk {chunk_index}: Error - {str(e)[:100]}")
            print(f"     ⚠️  Chunk {chunk_index}: Using fallback summary")
            
            fallback_summary = f"{text[:300]}..."
            if tables:
                fallback_summary += f"\n[Contains {len(tables)} table(s)]"
            if images:
                fallback_summary += f"\n[Contains {len(images)} image(s)]"
            
            return AIParser(
                question="Unable to generate questions due to processing error",
                summary=fallback_summary,
                image_interpretation="***DO NOT USE THIS IMAGE***" if images else "No images present",
                table_interpretation="***DO NOT USE THIS TABLE***" if tables else "No tables present"
            )
    
    async def process_chunks_async(self, chunks_data: List[Dict]) -> List[AIParser]:
        """
        Process multiple chunks asynchronously using different API keys
        
        Args:
            chunks_data: List of dictionaries containing chunk data
            
        Returns:
            List of AIParser responses
        """
        tasks = []
        
        # Create async tasks for each chunk with corresponding API key
        for i, chunk_data in enumerate(chunks_data):
            # Use modulo to cycle through API keys if we have more chunks than keys
            api_key_index = i % len(self.api_keys)
            api_key = self.api_keys[api_key_index]
            
            task = self.create_ai_enhanced_summary_async(
                text=chunk_data['text'],
                tables=chunk_data['tables'],
                images=chunk_data['image_base64'],
                api_key=api_key,
                chunk_index=i + 1
            )
            tasks.append(task)
        
        # Run all tasks concurrently
        print(f"\n🚀 Processing {len(tasks)} chunks asynchronously with {min(len(tasks), len(self.api_keys))} API keys...")
        responses = await asyncio.gather(*tasks)
        print(f"✅ All {len(responses)} chunks processed!\n")
        
        return responses
    
    def summarise_chunks(self, chunks) -> List[Document]:
        """
        Process all chunks with AI Summaries using multiple API keys asynchronously.
        
        Args:
            chunks: List of document chunks to process
            
        Returns:
            List of LangChain Documents with enhanced summaries
        """
        print("🧠 Processing chunks with AI Summaries (Multi-API Async Mode)...")
        
        # Clean entire workspace before processing
        from config.settings import settings
        self.clean_directory(settings.DATA_DIR)
        
        total_chunks = len(chunks)
        image_counter = {'count': 1}
        
        # Step 1: Extract content from all chunks (synchronous)
        print(f"\n📦 Extracting content from {total_chunks} chunks...")
        chunks_data = []
        
        for i, chunk in enumerate(chunks, 1):
            print(f"   📄 Extracting chunk {i}/{total_chunks}")
            
            # Analyze chunk content
            content_data = self.separate_content_types(chunk, image_counter)
            
            # Debug info
            print(f"     Types: {', '.join(content_data['types'])}, "
                  f"Tables: {len(content_data['tables'])}, "
                  f"Images: {len(content_data['image_base64'])}")
            if content_data['page_no']:
                print(f"     Pages: {content_data['page_no']}")
            
            chunks_data.append(content_data)
        
        print(f"\n✅ Content extraction complete!")
        print(f"📊 Total images saved: {image_counter['count'] - 1}")
        
        # Step 2: Process all chunks asynchronously with different API keys
        print(f"\n🔮 Starting async AI processing...")
        print(f"   Using {len(self.api_keys)} API key(s)")
        print(f"   Processing {total_chunks} chunk(s)")
        
        # Run async processing
        ai_responses = asyncio.run(self.process_chunks_async(chunks_data))
        
        # Step 3: Create LangChain documents
        print(f"\n📚 Creating LangChain documents...")
        langchain_documents = []
        
        for i, (content_data, ai_response) in enumerate(zip(chunks_data, ai_responses), 1):
            # Create combined searchable content
            combined_content = f"""QUESTIONS: {ai_response.question}

SUMMARY: {ai_response.summary}

IMAGE ANALYSIS: {ai_response.image_interpretation}

TABLE ANALYSIS: {ai_response.table_interpretation}"""
            
            print(f"   📄 Document {i}: {ai_response.summary[:100]}...")
            
            # Create LangChain Document with metadata
            doc = Document(
                page_content=combined_content,
                metadata={
                    "chunk_index": i,
                    "original_text": content_data['text'],
                    "raw_tables_html": content_data['tables'],
                    "ai_questions": ai_response.question,
                    "ai_summary": ai_response.summary,
                    "image_interpretation": ai_response.image_interpretation,
                    "table_interpretation": ai_response.table_interpretation,
                    "image_paths": content_data['images_dirpath'],
                    "page_numbers": content_data['page_no'],
                    "content_types": content_data['types'],
                }
            )
            
            langchain_documents.append(doc)
        
        print(f"\n✅ Successfully processed {len(langchain_documents)} chunks")
        print(f"⚡ Used async processing with {len(self.api_keys)} API key(s)")
        
        return langchain_documents