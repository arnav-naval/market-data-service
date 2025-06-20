import uuid
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class ProviderEnum(str, Enum):
    alpha_vantage = "alpha_vantage"
    yahoo_finance  = "yahoo_finance"
    finnhub        = "finnhub"

class PollingJobStatus(str, Enum):
    accepted  = "accepted"
    pending   = "pending"
    running   = "running"
    completed = "completed"
    failed    = "failed"

class PollingJobConfig(Base):
    __tablename__ = "polling_job_configs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    symbols = Column(JSON, nullable=False)   # e.g. ["AAPL","MSFT"]
    interval = Column(Integer, nullable=False)   # seconds
    provider = Column(SQLAlchemyEnum(ProviderEnum), nullable=False)
    status = Column(SQLAlchemyEnum(PollingJobStatus), nullable=False, default=PollingJobStatus.accepted)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    raw_responses = relationship("RawMarketData", back_populates="job")
