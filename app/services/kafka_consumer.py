import json
import logging
import asyncio
import signal
import sys
from typing import List, Optional
from sqlalchemy import select, desc, func
from confluent_kafka import Consumer, KafkaError
from app.core.config import Settings, get_settings
from app.core.database import async_session
from app.schemas.market_data import PriceEvent
from app.models.prices import PricePoint
from app.models.market_data import RawMarketData
from app.models.averages import MovingAverage

logger = logging.getLogger(__name__)

class KafkaConsumerService:
    """Kafka consumer service for processing price events and calculating moving averages"""
    
    def __init__(self, settings: Settings = get_settings()):
        self.settings = settings
        self.consumer = self._create_consumer()
        self.topic = settings.KAFKA_PRICE_EVENTS_TOPIC
        self.running = False
        
    def _create_consumer(self) -> Consumer:
        """Create and configure Kafka consumer"""
        config = {
            'bootstrap.servers': self.settings.KAFKA_BOOTSTRAP_SERVERS,
            'group.id': 'moving-average-consumer',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False,
            'session.timeout.ms': 30000,
            'heartbeat.interval.ms': 3000,
        }
        
        if self.settings.KAFKA_SECURITY_PROTOCOL != "PLAINTEXT":
            config.update({
                'security.protocol': self.settings.KAFKA_SECURITY_PROTOCOL,
                'sasl.mechanism': self.settings.KAFKA_SASL_MECHANISM,
                'sasl.username': self.settings.KAFKA_SASL_USERNAME,
                'sasl.password': self.settings.KAFKA_SASL_PASSWORD,
            })
        
        return Consumer(config)
    
    async def _get_recent_prices(self, symbol: str, limit: int = 5) -> List[PricePoint]:
        """Get the most recent price points for a symbol"""
        async with async_session() as session:
            query = select(PricePoint).where(
                PricePoint.symbol == symbol
            ).order_by(desc(PricePoint.timestamp)).limit(limit)
            
            result = await session.execute(query)
            return result.scalars().all()
    
    async def _calculate_moving_average(self, prices: List[PricePoint]) -> Optional[float]:
        """Calculate moving average from price points"""
        if len(prices) < 5:
            return None
        
        recent_prices = prices[:5]
        total = sum(price.price for price in recent_prices)
        return total / len(recent_prices)
    
    async def _store_moving_average(self, symbol: str, moving_average: float, trigger_price: PricePoint) -> None:
        """Store the calculated moving average in the database using proper upsert logic"""
        async with async_session() as session:
            # Use SQLAlchemy merge for proper upsert (INSERT ... ON CONFLICT DO UPDATE)
            ma = MovingAverage(
                symbol=symbol,
                interval=5,
                timestamp=trigger_price.timestamp,
                moving_average=moving_average,
                price_count=5,
                trigger_price_point_id=trigger_price.id
            )
            
            # Merge will either insert new record or update existing one based on unique constraint
            merged_ma = await session.merge(ma)
            await session.commit()
            
            logger.info(f"Upserted 5-point MA for {symbol}: {moving_average}")
    
    async def _process_price_event(self, price_event: PriceEvent) -> None:
        """Process a single price event and calculate moving average if possible"""
        try:
            async with async_session() as session:
                # Find the price point associated with this raw response
                # Use a more explicit query to avoid multiple results
                price_query = select(PricePoint).join(RawMarketData).where(
                    RawMarketData.id == price_event.raw_response_id
                ).order_by(desc(PricePoint.timestamp))
                result = await session.execute(price_query)
                price_points = result.scalars().all()
                
                logger.info(f"Found {len(price_points)} price points for raw_response_id {price_event.raw_response_id}")
                
                if not price_points:
                    logger.warning(f"Price point not found for raw response ID: {price_event.raw_response_id}")
                    return
                
                # Take the most recent price point
                trigger_price = price_points[0]
                logger.info(f"Using trigger price: {trigger_price.price} for symbol {trigger_price.symbol}")
                
                # Get recent prices for the symbol
                recent_prices = await self._get_recent_prices(price_event.symbol, 5)
                logger.info(f"Got {len(recent_prices)} recent prices: {[p.price for p in recent_prices]}")
                
                # Calculate moving average if we have enough data
                moving_average = await self._calculate_moving_average(recent_prices)
                
                if moving_average is not None:
                    logger.info(f"Calculated moving average: {moving_average}")
                    await self._store_moving_average(price_event.symbol, moving_average, trigger_price)
                else:
                    logger.debug(f"Insufficient data for MA calculation for {price_event.symbol}")
                    
        except Exception as e:
            logger.error(f"Error processing price event for {price_event.symbol}: {e}")
            # Log more details about the error
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
    
    async def start_consuming(self) -> None:
        """Start consuming messages from Kafka"""
        try:
            self.consumer.subscribe([self.topic])
            self.running = True
            logger.info(f"Started consuming from topic: {self.topic}")
            
            while self.running:
                try:
                    msg = self.consumer.poll(timeout=1.0)
                    
                    if msg is None:
                        continue
                    
                    if msg.error():
                        if msg.error().code() == KafkaError._PARTITION_EOF:
                            logger.debug("Reached end of partition")
                        else:
                            logger.error(f"Consumer error: {msg.error()}")
                        continue
                    
                    # Parse and process the message
                    try:
                        event_data = json.loads(msg.value().decode('utf-8'))
                        price_event = PriceEvent(**event_data)
                        await self._process_price_event(price_event)
                        self.consumer.commit(msg)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode message: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"Failed to process message: {e}")
                        continue
                        
                except KeyboardInterrupt:
                    logger.info("Received interrupt signal, stopping consumer")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error in consumer loop: {e}")
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"Failed to start consumer: {e}")
        finally:
            self.stop_consuming()
    
    def stop_consuming(self) -> None:
        """Stop consuming messages"""
        self.running = False
        if self.consumer:
            self.consumer.close()
        logger.info("Kafka consumer stopped")

# Signal handler for graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

async def main():
    """Main function to run the consumer service"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting Kafka Consumer Service...")
    
    try:
        # Create and start consumer
        consumer = KafkaConsumerService()
        await consumer.start_consuming()
    except Exception as e:
        logger.error(f"Failed to start consumer service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 