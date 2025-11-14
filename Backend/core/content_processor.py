"""Content processing module for AI-enhanced summarization"""
import os
import base64
import time
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
    """Processes document chunks with AI-enhanced summaries"""
    
    def __init__(self, image_dir: str, model_name: str = "gemini-2.0-flash-exp", temperature: float = 0):
        self.image_dir = image_dir
        self.model_name = model_name
        self.temperature = temperature
        
        # Initialize LLM with single API key from environment
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
        
        self.api_key = api_key
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name, 
            temperature=self.temperature,
            google_api_key=api_key
        )
        self.llm_structured = self.llm.with_structured_output(AIParser)
        
        Path(image_dir).mkdir(parents=True, exist_ok=True)
        print(f"✅ Initialized ContentProcessor with model: {model_name}")
    
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
    
    def _is_rate_limit_error(self, error_str: str) -> bool:
        """Check if error is a rate limit error"""
        rate_limit_keywords = [
            "rate limit",
            "quota",
            "429",
            "resource_exhausted",
            "too many requests",
            "quota exceeded",
            "resourceexhausted",
            "rate_limit_exceeded"
        ]
        error_lower = error_str.lower()
        return any(keyword in error_lower for keyword in rate_limit_keywords)
    
    def _is_api_key_error(self, error_str: str) -> bool:
        """Check if error is an API key error"""
        api_key_keywords = [
            "api key not valid",
            "api_key_invalid",
            "invalid api key",
            "unauthorized",
            "authentication failed",
            "invalid credentials"
        ]
        error_lower = error_str.lower()
        return any(keyword in error_lower for keyword in api_key_keywords)
    
    def create_ai_enhanced_summary(
        self, 
        text: str, 
        tables: List[str], 
        images: List[str],
        max_retries: int = 5,
        initial_wait: float = 2.0,
        max_wait: float = 60.0
    ) -> AIParser:
        """
        Create AI-enhanced summary with exponential backoff retry logic
        
        Args:
            text: Text content to summarize
            tables: List of HTML tables
            images: List of base64 encoded images
            max_retries: Maximum number of retry attempts (default: 5)
            initial_wait: Initial wait time in seconds (default: 2.0)
            max_wait: Maximum wait time between retries (default: 60.0)
        
        Returns:
            AIParser object with structured summary
        """
        
        for attempt in range(max_retries):
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
                
                # Make API call
                response = self.llm_structured.invoke([message])
                
                # Success! Return response
                if attempt > 0:
                    print(f"      ✅ Success after {attempt + 1} attempts")
                return response
                
            except Exception as e:
                error_str = str(e)
                
                # Check if it's an API key error (no point retrying)
                if self._is_api_key_error(error_str):
                    print(f"     ❌ API Key Error: {error_str[:150]}")
                    print(f"     ⚠️  Please check your GOOGLE_API_KEY in .env file")
                    break  # Don't retry for invalid API key
                
                # Check if it's a rate limit error
                is_rate_limit = self._is_rate_limit_error(error_str)
                
                if is_rate_limit:
                    # Calculate wait time with exponential backoff
                    wait_time = min(initial_wait * (2 ** attempt), max_wait)
                    
                    print(f"     ⚠️  Rate limit hit (attempt {attempt + 1}/{max_retries})")
                    
                    if attempt < max_retries - 1:
                        print(f"     ⏳ Waiting {wait_time:.1f}s before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"     ❌ Max retries reached after rate limits")
                else:
                    # Other error
                    print(f"     ⚠️  Error (attempt {attempt + 1}/{max_retries}): {error_str[:150]}")
                    
                    if attempt < max_retries - 1:
                        # Shorter wait for non-rate-limit errors
                        wait_time = min(initial_wait * (1.5 ** attempt), 10.0)
                        print(f"     ⏳ Waiting {wait_time:.1f}s before retry...")
                        time.sleep(wait_time)
                        continue
        
        # All retries failed - return fallback
        print(f"     ❌ All {max_retries} attempts failed, using fallback summary")
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
    
    def summarise_chunks(self, chunks) -> List[Document]:
        """
        Process all chunks with AI Summaries.
        
        Args:
            chunks: List of document chunks to process
            
        Returns:
            List of LangChain Documents with enhanced summaries
        """
        print("🧠 Processing chunks with AI Summaries...")
        
        # Clean entire workspace before processing
        from config.settings import settings
        self.clean_directory(settings.DATA_DIR)
        
        langchain_documents = []
        total_chunks = len(chunks)
        image_counter = {'count': 1}
        
        for i, chunk in enumerate(chunks, 1):
            print(f"\n   📄 Processing chunk {i}/{total_chunks}")
            
            # Analyze chunk content
            content_data = self.separate_content_types(chunk, image_counter)
            
            # Debug info
            print(f"     Types found: {', '.join(content_data['types'])}")
            print(f"     Tables: {len(content_data['tables'])}, Images: {len(content_data['image_base64'])}")
            if content_data['page_no']:
                print(f"     Pages: {content_data['page_no']}")
            
            # Create AI-enhanced summary with retry logic
            print(f"      Creating AI summary...")
            ai_response = self.create_ai_enhanced_summary(
                content_data['text'],
                content_data['tables'], 
                content_data['image_base64'],
                max_retries=5,  # Try up to 5 times
                initial_wait=2.0,  # Start with 2 second wait
                max_wait=60.0  # Cap at 60 seconds
            )
            print(f"      ✅ AI summary created")
            
            # Create combined searchable content from structured output
            combined_content = f"""QUESTIONS: {ai_response.question}

SUMMARY: {ai_response.summary}

IMAGE ANALYSIS: {ai_response.image_interpretation}

TABLE ANALYSIS: {ai_response.table_interpretation}"""
            
            print(f"     Preview: {ai_response.summary[:150]}...")
            
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
        print(f"📊 Total images saved: {image_counter['count'] - 1}")
        
        return langchain_documents