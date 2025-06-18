from typing import List
from pydantic import BaseModel

class PriceResponse(BaseModel):
    symbol: str
    price: float
    timestamp: str
    provider: str


class PollRequest(BaseModel):
    symbols: List[str]
    interval: int
    provider: str


class PollResponse(BaseModel):
    job_id: str
    status: str
    config: dict 