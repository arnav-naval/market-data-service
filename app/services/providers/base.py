from abc import ABC, abstractmethod
from app.schemas.market_data import PriceResponse


class MarketDataProvider(ABC):
    """Abstract base class for market data providers"""
    
    @abstractmethod
    async def get_latest_price(self, symbol: str) -> PriceResponse:
        """Fetch the latest price for a given symbol"""
        pass 