import asyncio
import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.providers.factory import get_provider
from app.services.providers.base import MarketDataProvider
from app.services.market_data_service import get_market_data_service
from app.models.jobs import ProviderEnum
from app.core.database import async_session

logger = logging.getLogger(__name__)

class PollingService:
    """Service for polling market data for multiple symbols"""
    
    def __init__(self):
        self.market_data_service = get_market_data_service()
        # Rate limiting: track last request time per provider
        self._last_request_time: dict[str, float] = {}
        self._rate_limits = {
            "alpha_vantage": 12,  # 5 calls per minute = 12 seconds between calls
            "yahoo_finance": 1,   # No strict rate limit, but be respectful
            "finnhub": 60         # 60 calls per minute = 1 second between calls
        }
    
    async def poll_symbols(
        self,
        symbols: List[str],
        provider: str,
        job_id: str
    ):
        """
        Poll all symbols in the list
        
        Args:
            symbols: List of stock symbols to poll
            provider: Data provider name
            job_id: Associated job ID
        """
        logger.info(f"Polling {len(symbols)} symbols with provider {provider}")
        
        # Get provider instance
        provider_instance = get_provider(provider)
        
        # Process symbols with rate limiting
        for symbol in symbols:
            try:
                await self._poll_single_symbol(
                    symbol=symbol,
                    provider_instance=provider_instance,
                    provider_name=provider,
                    job_id=job_id
                )
                
                # Rate limiting delay
                await self._rate_limit_delay(provider)
                
            except Exception as e:
                logger.error(f"Error polling symbol {symbol}: {e}")
                # Continue with next symbol despite errors
    
    async def _poll_single_symbol(
        self,
        symbol: str,
        provider_instance: MarketDataProvider,
        provider_name: str,
        job_id: str
    ):
        """
        Poll a single symbol
        
        Args:
            symbol: Stock symbol
            provider_instance: Provider instance
            provider_name: Provider name string
            job_id: Associated job ID
        """
        try:
            # Fetch latest price with raw data
            price_response, raw_response = await provider_instance.get_latest_price_with_raw_data(symbol)
            
            # Process through existing market data pipeline using session factory
            async with async_session() as session:
                await self.market_data_service.process_price_data(
                    symbol=symbol,
                    price=price_response.price,
                    timestamp=price_response.timestamp,
                    provider=provider_name,
                    raw_response=raw_response,
                    db=session
                )
            
            logger.info(f"Successfully polled {symbol}: ${price_response.price}")
            
        except Exception as e:
            logger.error(f"Failed to poll {symbol}: {e}")
            raise
    
    async def _rate_limit_delay(self, provider: str):
        """
        Implement rate limiting delay for provider
        
        Args:
            provider: Provider name
        """
        if provider not in self._rate_limits:
            return
        
        min_interval = self._rate_limits[provider]
        last_request = self._last_request_time.get(provider, 0)
        
        # Calculate time since last request
        import time
        current_time = time.time()
        time_since_last = current_time - last_request
        
        if time_since_last < min_interval:
            delay = min_interval - time_since_last
            logger.debug(f"Rate limiting: waiting {delay:.2f}s for {provider}")
            await asyncio.sleep(delay)
        
        # Update last request time
        self._last_request_time[provider] = time.time()
    
    async def validate_polling_request(
        self,
        symbols: List[str],
        interval: int,
        provider: str
    ) -> bool:
        """
        Validate polling request parameters
        
        Args:
            symbols: List of stock symbols
            interval: Polling interval in seconds
            provider: Provider name
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Validate symbols
        if not symbols:
            raise ValueError("At least one symbol must be provided")
        
        if len(symbols) > 10:  # Reasonable limit
            raise ValueError("Maximum 10 symbols allowed per job")
        
        # Validate interval
        if interval < 30:  # Minimum 30 seconds
            raise ValueError("Minimum polling interval is 30 seconds")
        
        if interval > 3600:  # Maximum 1 hour
            raise ValueError("Maximum polling interval is 3600 seconds (1 hour)")
        
        # Validate provider
        try:
            ProviderEnum(provider)
        except ValueError:
            raise ValueError(f"Invalid provider: {provider}")
        
        return True 