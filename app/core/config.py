from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Alpha Vantage API
    ALPHA_VANTAGE_API_KEY: str = "default"
    
    # Database settings
    DATABASE_URL: str = "postgresql+asyncpg://arnav:market123@postgres:5432/market_data"
    
    # Redis settings
    REDIS_URL: str = "default"
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_CACHE_TTL: int = 60  # 1 minutes cache TTL
    
    # Kafka settings
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_PRICE_EVENTS_TOPIC: str = "price-events"
    KAFKA_SECURITY_PROTOCOL: str = "PLAINTEXT"
    KAFKA_SASL_MECHANISM: str = ""
    KAFKA_SASL_USERNAME: str = ""
    KAFKA_SASL_PASSWORD: str = ""
    
    # App settings
    DEBUG: bool = False
    APP_NAME: str = "Market Data Service"
    
    class Config:
        env_file = ".env" 


@lru_cache()
def get_settings() -> Settings:
    """Dependency function to get settings"""
    return Settings() 