from abc import ABC, abstractmethod
import httpx
from datetime import datetime, timezone
from app.schemas.market_data import PriceResponse
from app.core.config import settings


class MarketDataProvider(ABC):
    """Abstract base class for market data providers"""
    
    @abstractmethod
    async def get_latest_price(self, symbol: str) -> PriceResponse:
        """Fetch the latest price for a given symbol"""
        pass


class AlphaVantageProvider(MarketDataProvider):
    """Alpha Vantage market data provider implementation"""
    
    def __init__(self):
        self.api_key = settings.ALPHA_VANTAGE_API_KEY
        self.base_url = "https://www.alphavantage.co/query"
        self.rate_limit = 5  # calls per minute
    
    async def get_latest_price(self, symbol: str) -> PriceResponse:
        """Fetch the latest price from Alpha Vantage API"""
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extract price from Alpha Vantage response
            quote = data.get("Global Quote", {})
            if not quote:
                raise ValueError(f"No data found for symbol: {symbol}")
            
            price = float(quote.get("05. price", 0))
            timestamp = datetime.now(timezone.utc).isoformat()
            
            return PriceResponse(
                symbol=symbol,
                price=price,
                timestamp=timestamp,
                provider="alpha_vantage"
            )


class ProviderFactory:
    """Factory for creating market data providers"""
    
    @staticmethod
    def get_provider(provider_name: str) -> MarketDataProvider:
        """Get a provider instance by name"""
        if provider_name == "alpha_vantage":
            return AlphaVantageProvider()
        else:
            raise ValueError(f"Unsupported provider: {provider_name}") 