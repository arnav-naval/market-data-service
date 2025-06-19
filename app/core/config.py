from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Alpha Vantage API
    ALPHA_VANTAGE_API_KEY: str = "default"
    
    # App settings
    DEBUG: bool = False
    APP_NAME: str = "Market Data Service"
    
    class Config:
        env_file = ".env"  # Same as require('dotenv').config()


# Global instance (like module.exports in Node.js)
settings = Settings() 