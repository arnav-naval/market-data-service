from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Alpha Vantage API
    ALPHA_VANTAGE_API_KEY: str = "default"
    
    # App settings
    DEBUG: bool = False
    APP_NAME: str = "Market Data Service"
    
    class Config:
        env_file = ".env" 


@lru_cache()
def get_settings() -> Settings:
    """Dependency function to get settings"""
    return Settings() 