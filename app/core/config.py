from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Alpha Vantage API
    ALPHA_VANTAGE_API_KEY: str = "default"
    
    # Database settings
    DATABASE_URL: str = "postgresql://user:password@localhost/market_data"
    
    # Redis settings
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_CACHE_TTL: int = 60  # 1 minutes cache TTL
    
    # App settings
    DEBUG: bool = False
    APP_NAME: str = "Market Data Service"
    
    class Config:
        env_file = ".env" 


@lru_cache()
def get_settings() -> Settings:
    """Dependency function to get settings"""
    return Settings() 