from typing import List
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