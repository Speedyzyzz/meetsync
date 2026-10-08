import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "MeetSync"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API configuration
    API_V1_STR: str = "/api"
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    
    # Database configuration
    # Default to a local SQLite database for instant zero-dependency execution,
    # or override with PostgreSQL via DATABASE_URL
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/meetsync.db",
        description="Async SQLAlchemy database URL"
    )
    
    # AI & Transcription configuration
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key for Whisper & GPT models")
    LLM_MODEL: str = Field(default="gpt-4o-mini", description="LLM model used for structured extraction")
    WHISPER_MODEL: str = Field(default="whisper-1", description="Transcription model")
    
    # Default multi-tenancy IDs for local/demo workflows
    DEFAULT_WORKSPACE_ID: str = "00000000-0000-0000-0000-000000000001"
    DEFAULT_USER_ID: str = "00000000-0000-0000-0000-000000000002"
    
    # Upload storage directory
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE_BYTES: int = 100 * 1024 * 1024  # 100 MB
    ALLOWED_AUDIO_EXTENSIONS: List[str] = [".mp3", ".wav", ".m4a", ".ogg", ".webm", ".flac"]

    model_config = ConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# Ensure data directories exist
os.makedirs("./data", exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
