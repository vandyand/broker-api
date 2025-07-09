import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./data/broker.db"
    
    # OANDA Configuration
    oanda_api_key: Optional[str] = None
    oanda_account_id: Optional[str] = None
    oanda_environment: str = "practice"
    
    # Bitunix Configuration
    bitunix_api_key: Optional[str] = None
    bitunix_secret_key: Optional[str] = None
    
    # Application
    debug: bool = True
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields from .env file


settings = Settings() 