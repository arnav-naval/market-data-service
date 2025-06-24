import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.market_data import RawMarketData
from app.schemas.market_data import PriceResponse, PriceEvent
from app.services.kafka_producer import get_kafka_producer
from app.core.database import get_db

logger = logging.getLogger(__name__)

class MarketDataService:
    """Service for handling market data operations"""
    
    def __init__(self):
        self.kafka_producer = get_kafka_producer()
    
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
            
            # 2. Create price event for Kafka
            price_event = PriceEvent(
                symbol=symbol,
                price=price,
                timestamp=timestamp,
                source=provider,
                raw_response_id=str(raw_data_id)
            )
            
            # 3. Publish to Kafka
            await self._publish_to_kafka(price_event)
            
            # 4. Return processed response
            return PriceResponse(
                symbol=symbol,
                price=price,
                timestamp=timestamp,
                provider=provider
            )
            
        except Exception as e:
            logger.error(f"Error processing price data for {symbol}: {e}")
            raise
    
    async def _store_raw_market_data(
        self, 
        symbol: str, 
        provider: str, 
        raw_response: dict,
        db: AsyncSession
    ) -> int:
        """
        Store raw market data in database
        
        Args:
            symbol: Stock symbol
            provider: Data provider name
            raw_response: Complete raw response from provider
            db: Database session
            
        Returns:
            int: ID of the stored raw data record
        """
        try:
            raw_data = RawMarketData(
                symbol=symbol,
                provider=provider,
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
    
    async def get_latest_processed_price(self, symbol: str, db: AsyncSession) -> Optional[PriceResponse]:
        """
        Get the latest processed price for a symbol
        
        Args:
            symbol: Stock symbol
            db: Database session
            
        Returns:
            Optional[PriceResponse]: Latest processed price or None
        """
        # TODO: Implement this when we have processed price table
        # For now, return None to indicate we need to fetch fresh data
        return None

# Global service instance
_market_data_service: Optional[MarketDataService] = None

def get_market_data_service() -> MarketDataService:
    """Get or create market data service instance"""
    global _market_data_service
    if _market_data_service is None:
        _market_data_service = MarketDataService()
    return _market_data_service 