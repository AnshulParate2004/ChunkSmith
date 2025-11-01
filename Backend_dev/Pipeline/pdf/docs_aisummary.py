import os
from unstructured.documents.elements import Element
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbedding

def create_ai_enhanced_summary(text: str, tables: list[str], images: list[str]) -> str:
    """Create AI-enhanced summary for mixed content"""
    
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0)
        
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
        response = llm.invoke([message])
        
        return response.content
        
    except Exception as e:
        print(f"      AI summary failed: {e}")
        # Fallback summary
        summary = f"{text[:300]}..."
        if tables:
            summary += f"\n[Contains {len(tables)} table(s)]"
        if images:
            summary += f"\n[Contains {len(images)} image(s)]"
        return summary