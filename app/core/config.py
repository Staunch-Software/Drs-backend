import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from urllib.parse import quote_plus  # <--- IMPORT THIS

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # --- APP INFO ---
    PROJECT_NAME: str = "Maritime DRS"
    API_V1_STR: str = "/api/v1"
    
    # --- SECURITY ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "drs_super_secret_key_2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 

    # --- DATABASE ---
    POSTGRES_USER: str = os.getenv("DB_USER", "Deepa")
    POSTGRES_PASSWORD: str = os.getenv("DB_PASSWORD", "Admin@123")
    POSTGRES_SERVER: str = os.getenv("DB_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("DB_PORT", "5432")
    POSTGRES_DB: str = os.getenv("DB_NAME", "Drs")

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Constructs the Async PostgreSQL connection string.
        We encode the password to handle special characters like '@'
        """
        # Encodes 'Admin@123' -> 'Admin%40123' so the URL doesn't break
        encoded_password = quote_plus(self.POSTGRES_PASSWORD)
        
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{encoded_password}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        case_sensitive = True

settings = Settings()