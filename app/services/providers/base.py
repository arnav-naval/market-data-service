from abc import ABC, abstractmethod
from app.schemas.market_data import PriceResponse


class MarketDataProvider(ABC):
    """Abstract base class for market data providers"""
    
    @abstractmethod
    async def get_latest_price(self, symbol: str) -> PriceResponse:
        """Fetch the latest price for a given symbol"""
        pass
    
    async def get_latest_price_with_raw_data(self, symbol: str) -> tuple[PriceResponse, dict]:
        """
        Fetch the latest price and return both processed response and raw data
        
        Args:
            symbol: Stock symbol to fetch
            
        Returns:
            tuple: (PriceResponse, raw_response_dict)
        """
        # Default implementation - can be overridden by providers
        price_response = await self.get_latest_price(symbol)
        # Return empty dict as raw data - providers should override this
        return price_response, {} 