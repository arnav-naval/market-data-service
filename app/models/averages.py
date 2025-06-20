import uuid
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class MovingAverage(Base):
    __tablename__ = "symbol_averages"

    id             = Column(String,  primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol         = Column(String,  index=True, nullable=False)
    interval       = Column(Integer, nullable=False)   # e.g. 5 for 5-point MA
    timestamp      = Column(DateTime(timezone=True), index=True, nullable=False)
    moving_average = Column(Float, nullable=False)
    
    # Additional metadata about the calculation
    calculation_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)  # when this MA was calculated
    price_count = Column(Integer, nullable=False)  # how many prices were used in calculation
    
    # Foreign key to the price point that "triggered" this MA calculation
    trigger_price_point_id = Column(String, ForeignKey("price_points.id"), nullable=False)
    trigger_price_point = relationship("PricePoint", back_populates="triggered_moving_averages")

    # ensure one MA record per (symbol, interval, timestamp)
    __table_args__ = (
        UniqueConstraint("symbol", "interval", "timestamp", name="uq_symbol_interval_timestamp"),
        Index("ix_ma_symbol_interval_ts", "symbol", "interval", "timestamp"),
    )