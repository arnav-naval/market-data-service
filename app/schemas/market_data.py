from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

# PriceResponse schema
class PriceResponse(BaseModel):
    symbol: str
    price: float
    timestamp: str
    provider: str

# PollRequest schema
class PollRequest(BaseModel):
    symbols: List[str]
    interval: int
    provider: str

# PollResponse schema
class PollResponse(BaseModel):
    job_id: str
    status: str
    config: dict

# JobStatus schema
class JobStatus(BaseModel):
    job_id: str
    status: str
    symbols: List[str]
    interval: int
    provider: str
    created_at: Optional[str] = None

# JobList schema
class JobList(BaseModel):
    jobs: List[JobStatus]

# JobStopResponse schema
class JobStopResponse(BaseModel):
    message: str

# PricePoint schema
class PricePoint(BaseModel):
    id: str
    symbol: str
    price: float
    timestamp: str
    provider: str
    raw_response_id: str

# PriceEvent schema for Kafka messages
class PriceEvent(BaseModel):
    symbol: str
    price: float
    timestamp: str
    source: str
    raw_response_id: str 