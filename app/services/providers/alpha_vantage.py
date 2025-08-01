import httpx
from datetime import datetime, timezone
from fastapi import Depends
from app.schemas.market_data import PriceResponse
from app.core.config import Settings, get_settings
from .base import MarketDataProvider


class AlphaVantageProvider(MarketDataProvider):
    """Alpha Vantage market data provider implementation"""
    
    def __init__(self, settings: Settings = Depends(get_settings)):
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
    
    async def get_latest_price_with_raw_data(self, symbol: str) -> tuple[PriceResponse, dict]:
        """
        Fetch the latest price and return both processed response and raw data
        
        Args:
            symbol: Stock symbol to fetch
            
        Returns:
            tuple: (PriceResponse, raw_response_dict)
        """
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            raw_data = response.json()
            
            # Extract price from Alpha Vantage response
            quote = raw_data.get("Global Quote", {})
            if not quote:
                raise ValueError(f"No data found for symbol: {symbol}")
            
            price = float(quote.get("05. price", 0))
            timestamp = datetime.now(timezone.utc).isoformat()
            
            price_response = PriceResponse(
                symbol=symbol,
                price=price,
                timestamp=timestamp,
                provider="alpha_vantage"
            )
            
            return price_response, raw_data 