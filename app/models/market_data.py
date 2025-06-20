import uuid
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Index, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from .jobs import ProviderEnum

class RawMarketData(Base):
    __tablename__ = "raw_market_data"

    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol       = Column(String, index=True, nullable=False)
    provider     = Column(SQLAlchemyEnum(ProviderEnum), nullable=False)
    timestamp    = Column(DateTime(timezone=True), index=True, nullable=False)
    raw_response = Column(JSON, nullable=False)

    job_id = Column(String, ForeignKey("polling_job_configs.id"), nullable=True)
    job    = relationship("PollingJobConfig", back_populates="raw_responses")

    # one-to-one link to the parsed price-point
    price_point = relationship("PricePoint", uselist=False, back_populates="raw_data")

    # composite index
    __table_args__ = (
        Index("ix_raw_symbol_ts", "symbol", "timestamp"),
    )