import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from .jobs import ProviderEnum

class PricePoint(Base):
    __tablename__ = "price_points"

    id        = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol    = Column(String, index=True, nullable=False)
    provider  = Column(SQLAlchemyEnum(ProviderEnum), nullable=False)
    timestamp = Column(DateTime(timezone=True), index=True, nullable=False)
    price     = Column(Float, nullable=False)

    raw_data_id = Column(String, ForeignKey("raw_market_data.id"), nullable=False)
    raw_data    = relationship("RawMarketData", back_populates="price_point")

    # Moving averages that this price point triggered (when it completed the window)
    triggered_moving_averages = relationship("MovingAverage", back_populates="trigger_price_point")

    __table_args__ = (
        Index("ix_price_symbol_ts", "symbol", "timestamp"),
    )
    