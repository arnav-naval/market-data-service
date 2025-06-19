from sqlalchemy import Column, Integer, String, DateTime, JSON, Index
from sqlalchemy.sql import func
from app.core.database import Base

class RawMarketData(Base):
    """Raw market data responses from providers"""
    __tablename__ = "raw_market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    provider = Column(String(50), nullable=False)
    raw_response = Column(JSON, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_raw_market_data_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_raw_market_data_provider_timestamp', 'provider', 'timestamp'),
    ) 