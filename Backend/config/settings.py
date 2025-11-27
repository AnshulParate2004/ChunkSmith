"""Configuration settings for the application"""
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Base paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    
    # Data subdirectories
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    IMAGE_DIR: Path = DATA_DIR / "images"
    PICKLE_DIR: Path = DATA_DIR / "pickle"
    JSON_DIR: Path = DATA_DIR / "json"
    CHROMA_DIR: Path = DATA_DIR / "chroma_db"
    
    # PDF Processing settings
    MAX_CHARACTERS: int = 3000
    NEW_AFTER_N_CHARS: int = 3800
    COMBINE_TEXT_UNDER_N_CHARS: int = 200
    EXTRACT_IMAGES: bool = True
    EXTRACT_TABLES: bool = True
    LANGUAGES: list = ["eng"]
    
    # AI Model settings
    GEMINI_MODEL: str = "gemini-2.5-pro"
    EMBEDDING_MODEL: str = "text-embedding-004"
    TEMPERATURE: float = 0.0
    
    # API settings
    API_TITLE: str = "MultiModal RAG API"
    API_VERSION: str = "1.0.0"
    ALLOWED_EXTENSIONS: set = {".pdf"}
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50 MB
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories on initialization
        for dir_path in [self.UPLOAD_DIR, self.IMAGE_DIR, self.PICKLE_DIR, 
                         self.JSON_DIR, self.CHROMA_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)

settings = Settings()