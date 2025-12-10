
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv

# Load .env file from project root (2 levels up from backend/app/config.py)
project_root = Path(__file__).resolve().parents[2]
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)
    print(f"✅ Loaded .env from: {env_path}")
else:
    print(f"⚠️  Warning: .env file not found at {env_path}")

class Settings(BaseSettings):
    # Database settings
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "postgres")  # Default to postgres (Supabase default)
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "")
    
    # Database URL
    @property
    def database_url(self) -> str:
        # Remove https:// if present (database connections don't use HTTPS)
        host = self.db_host.replace("https://", "").replace("http://", "")
        # For Supabase, ensure db. prefix if it's a supabase.co domain
        if "supabase.co" in host and not host.startswith("db."):
            host = f"db.{host}"
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{host}:{self.db_port}/{self.db_name}"
    
    # Blockchain settings
    blockchain_provider: str = os.getenv("BLOCKCHAIN_PROVIDER", "bigchaindb")
    blockchain_node: str = os.getenv("BLOCKCHAIN_NODE", "http://localhost:9984")
    
    # Security settings
    jwt_secret: str = os.getenv("JWT_SECRET", "change-this-secret-key-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expiry: int = int(os.getenv("JWT_EXPIRY", "3600"))
    encryption_key: str = os.getenv("ENCRYPTION_KEY", "")
    
    # API settings
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    api_reload: bool = os.getenv("API_RELOAD", "true").lower() == "true"
    
    # CORS settings
    cors_origins: List[str] = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")]
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        # Use absolute path to .env in project root
        env_file = str(project_root / ".env")
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Global settings instance
settings = get_settings()
