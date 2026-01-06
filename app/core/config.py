# app/core/config.py
from pydantic_settings import BaseSettings
from urllib.parse import quote_plus

class Settings(BaseSettings):
    # --- APP INFO ---
    PROJECT_NAME: str = "Maritime DRS"
    API_V1_STR: str = "/api/v1"
    
    # --- SECURITY ---
    # Pydantic automatically reads "SECRET_KEY" from .env
    SECRET_KEY: str 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 

    # --- DATABASE (Names MUST match .env exactly) ---
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str

    # --- AZURE STORAGE ---
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_CONTAINER_NAME: str = "pdf-repository"
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Constructs the Async PostgreSQL connection string.
        """
        # Encodes password to handle special chars like '@'
        encoded_password = quote_plus(self.DB_PASSWORD)
        
        return f"postgresql+asyncpg://{self.DB_USER}:{encoded_password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"
        case_sensitive = True
        # This tells Pydantic: "If .env has extra variables I don't know, just ignore them, don't crash"
        extra = "ignore" 

settings = Settings()