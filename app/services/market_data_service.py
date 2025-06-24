import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.market_data import RawMarketData
from app.models.prices import PricePoint
from app.models.jobs import ProviderEnum
from app.schemas.market_data import PriceResponse, PriceEvent
from app.services.kafka_producer import get_kafka_producer
from app.core.redis import RedisService
from app.core.config import get_settings
from app.core.database import get_db

logger = logging.getLogger(__name__)

class MarketDataService:
    """Service for handling market data operations"""
    
    def __init__(self):
        self.kafka_producer = get_kafka_producer()
        self.redis_service: Optional[RedisService] = None
    
    async def _get_redis_service(self) -> RedisService:
        """Get Redis service instance"""
        if self.redis_service is None:
            settings = get_settings()
            self.redis_service = RedisService(settings)
        return self.redis_service
    
    async def process_price_data(
        self, 
        symbol: str, 
        price: float, 
        timestamp: str, 
        provider: str,
        raw_response: dict,
        db: AsyncSession
    ) -> PriceResponse:
        """
        Process price data: store raw data and publish to Kafka
        
        Args:
            symbol: Stock symbol
            price: Price value
            timestamp: Price timestamp
            provider: Data provider name
            raw_response: Complete raw response from provider
            db: Database session
            
        Returns:
            PriceResponse: Processed price response
        """
        try:
            # 1. Store raw market data
            raw_data_id = await self._store_raw_market_data(
                symbol=symbol,
                provider=provider,
                raw_response=raw_response,
                db=db
            )
            
            # 2. Store price point
            price_point_id = await self._store_price_point(
                symbol=symbol,
                price=price,
                timestamp=timestamp,
                provider=provider,
                raw_data_id=raw_data_id,
                db=db
            )
            
            # 3. Create price event for Kafka
            price_event = PriceEvent(
                symbol=symbol,
                price=price,
                timestamp=timestamp,
                source=provider,
                raw_response_id=str(raw_data_id)
            )
            
            # 4. Publish to Kafka
            await self._publish_to_kafka(price_event)
            
            # 5. Create price response
            price_response = PriceResponse(
                symbol=symbol,
                price=price,
                timestamp=timestamp,
                provider=provider
            )
            
            # 6. Cache the result
            await self._cache_price_response(symbol, price_response)
            
            # 7. Return processed response
            return price_response
            
        except Exception as e:
            logger.error(f"Error processing price data for {symbol}: {e}")
            raise
    
    async def _store_raw_market_data(
        self, 
        symbol: str, 
        provider: str, 
        raw_response: dict,
        db: AsyncSession
    ) -> str:
        """
        Store raw market data in database
        
        Args:
            symbol: Stock symbol
            provider: Data provider name
            raw_response: Complete raw response from provider
            db: Database session
            
        Returns:
            str: ID of the stored raw data record
        """
        try:
            # Convert provider string to enum
            provider_enum = ProviderEnum(provider)
            
            raw_data = RawMarketData(
                symbol=symbol,
                provider=provider_enum,
                raw_response=raw_response,
                timestamp=datetime.now(timezone.utc)
            )
            
            db.add(raw_data)
            await db.commit()
            await db.refresh(raw_data)
            
            logger.info(f"Stored raw market data for {symbol} with ID: {raw_data.id}")
            return raw_data.id
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error storing raw market data for {symbol}: {e}")
            raise
    
    async def _store_price_point(
        self,
        symbol: str,
        price: float,
        timestamp: str,
        provider: str,
        raw_data_id: str,
        db: AsyncSession
    ) -> str:
        """
        Store price point in database
        
        Args:
            symbol: Stock symbol
            price: Price value
            timestamp: Price timestamp
            provider: Data provider name
            raw_data_id: ID of the raw market data record
            db: Database session
            
        Returns:
            str: ID of the stored price point record
        """
        try:
            # Parse timestamp string to datetime
            if isinstance(timestamp, str):
                timestamp_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                timestamp_dt = timestamp
            
            # Convert provider string to enum
            provider_enum = ProviderEnum(provider)
            
            price_point = PricePoint(
                symbol=symbol,
                price=price,
                timestamp=timestamp_dt,
                provider=provider_enum,
                raw_data_id=raw_data_id
            )
            
            db.add(price_point)
            await db.commit()
            await db.refresh(price_point)
            
            logger.info(f"Stored price point for {symbol} with ID: {price_point.id}")
            return price_point.id
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error storing price point for {symbol}: {e}")
            raise
    
    async def _publish_to_kafka(self, price_event: PriceEvent) -> bool:
        """
        Publish price event to Kafka
        
        Args:
            price_event: Price event to publish
            
        Returns:
            bool: True if published successfully
        """
        try:
            success = await self.kafka_producer.publish_price_event(price_event)
            if success:
                logger.info(f"Published price event to Kafka for {price_event.symbol}")
            else:
                logger.error(f"Failed to publish price event to Kafka for {price_event.symbol}")
            return success
            
        except Exception as e:
            logger.error(f"Error publishing to Kafka for {price_event.symbol}: {e}")
            return False
    
    async def _cache_price_response(self, symbol: str, price_response: PriceResponse) -> bool:
        """
        Cache price response in Redis
        
        Args:
            symbol: Stock symbol
            price_response: Price response to cache
            
        Returns:
            bool: True if cached successfully
        """
        try:
            redis_service = await self._get_redis_service()
            cache_key = f"price:{symbol}"
            cache_data = price_response.model_dump()
            
            success = await redis_service.set_cache(cache_key, cache_data)
            if success:
                logger.info(f"Cached price response for {symbol}")
            else:
                logger.warning(f"Failed to cache price response for {symbol}")
            return success
            
        except Exception as e:
            logger.error(f"Error caching price response for {symbol}: {e}")
            return False
    
    async def _get_cached_price(self, symbol: str) -> Optional[PriceResponse]:
        """
        Get price from Redis cache
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Optional[PriceResponse]: Cached price or None
        """
        try:
            redis_service = await self._get_redis_service()
            cache_key = f"price:{symbol}"
            
            cached_data = await redis_service.get_cache(cache_key)
            if cached_data:
                return PriceResponse(**cached_data)
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached price for {symbol}: {e}")
            return None
    
    async def get_latest_processed_price(self, symbol: str) -> Optional[PriceResponse]:
        """
        Get the latest processed price for a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Optional[PriceResponse]: Latest processed price or None
        """
        try:
            # 1. First check Redis cache
            cached_price = await self._get_cached_price(symbol)
            if cached_price:
                logger.info(f"Retrieved cached price for {symbol}")
                return cached_price
            
            logger.info(f"No cached price found for {symbol}, will fetch from provider")
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest processed price for {symbol}: {e}")
            return None
    
    async def _get_latest_price_from_db(self, symbol: str, db: AsyncSession) -> Optional[PriceResponse]:
        """
        Get latest price from database
        
        Args:
            symbol: Stock symbol
            db: Database session
            
        Returns:
            Optional[PriceResponse]: Latest price from database or None
        """
        try:
            # Query the latest price point for the symbol
            stmt = (
                select(PricePoint)
                .where(PricePoint.symbol == symbol)
                .order_by(desc(PricePoint.timestamp))
                .limit(1)
            )
            
            result = await db.execute(stmt)
            price_point = result.scalar_one_or_none()
            
            if price_point:
                return PriceResponse(
                    symbol=price_point.symbol,
                    price=price_point.price,
                    timestamp=price_point.timestamp.isoformat(),
                    provider=price_point.provider.value
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest price from database for {symbol}: {e}")
            return None

# Global service instance
_market_data_service: Optional[MarketDataService] = None

def get_market_data_service() -> MarketDataService:
    """Get or create market data service instance"""
    global _market_data_service
    if _market_data_service is None:
        _market_data_service = MarketDataService()
    return _market_data_service 