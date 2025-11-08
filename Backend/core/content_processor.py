"""Content processing module for AI-enhanced summarization"""
import os
import base64
from pathlib import Path
from typing import List, Dict
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage


class ContentProcessor:
    """Processes document chunks with AI-enhanced summaries"""
    
    def __init__(self, image_dir: str, model_name: str = "gemini-2.0-flash-exp", temperature: float = 0):
        self.image_dir = image_dir
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=temperature)
        Path(image_dir).mkdir(parents=True, exist_ok=True)
    
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
    
    def create_ai_enhanced_summary(self, text: str, tables: List[str], images: List[str]) -> str:
        """Create AI-enhanced summary for mixed content"""
        
        try:
            # Build comprehensive prompt
            prompt_text = f"""You are creating a searchable description for document content retrieval.

CONTENT TO ANALYZE:

TEXT CONTENT:
{text}

"""
            
            # Add tables if present
            if tables:
                prompt_text += "TABLES:\n"
                for i, table in enumerate(tables, 1):
                    prompt_text += f"Table {i}:\n{table}\n\n"
            
            # Add detailed instructions
            prompt_text += """
YOUR TASK:
Generate a comprehensive, searchable description that covers:

1. Key facts, numbers, and data points from text and tables
2. Main topics and concepts discussed  
3. Questions this content could answer
4. Visual content analysis (charts, diagrams, patterns in images)
5. Alternative search terms users might use

Make it detailed and searchable - prioritize findability over brevity.

OUTPUT FORMAT:
QUESTIONS: "List all potential questions that can be answered from this content (text, images, tables)"
SUMMARY: "Comprehensive summary of all data and information"
IMAGE_INTERPRETATION: "Detailed description of image content. If images are irrelevant or contain only decorative elements, state: ***DO NOT USE THIS IMAGE***"
TABLE_INTERPRETATION: "Detailed description of table content. If tables are irrelevant, state: ***DO NOT USE THIS TABLE***"

SEARCHABLE DESCRIPTION:"""

            # Build message with text and images
            message_content = [{"type": "text", "text": prompt_text}]
            
            # Add images to message
            for img_b64 in images:
                message_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                })
            
            # Invoke AI
            message = HumanMessage(content=message_content)
            response = self.llm.invoke([message])
            
            return response.content
            
        except Exception as e:
            print(f"     ❌ AI summary failed: {e}")
            # Fallback summary
            summary = f"{text[:300]}..."
            if tables:
                summary += f"\n[Contains {len(tables)} table(s)]"
            if images:
                summary += f"\n[Contains {len(images)} image(s)]"
            return summary
    
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
            
            # Create AI-enhanced summary
            print(f"      Creating AI summary...")
            try:
                enhanced_content = self.create_ai_enhanced_summary(
                    content_data['text'],
                    content_data['tables'], 
                    content_data['image_base64']
                )
                print(f"      ✅ AI summary created")
                print(f"     Preview: {enhanced_content[:150]}...")
            except Exception as e:
                print(f"      ⚠️ AI summary failed, using raw text: {e}")
                enhanced_content = content_data['text']
            
            # Create LangChain Document with metadata
            doc = Document(
                page_content=enhanced_content,
                metadata={
                    "chunk_index": i,
                    "original_text": content_data['text'],
                    "raw_tables_html": content_data['tables'],
                    "image_paths": content_data['images_dirpath'],
                    "page_numbers": content_data['page_no'],
                    "content_types": content_data['types'],
                }
            )
            
            langchain_documents.append(doc)
        
        print(f"\n✅ Successfully processed {len(langchain_documents)} chunks")
        print(f"📊 Total images saved: {image_counter['count'] - 1}")
        
        return langchain_documents