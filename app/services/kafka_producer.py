import json
import logging
from typing import Optional
from confluent_kafka import Producer, KafkaError
from app.core.config import Settings, get_settings
from app.schemas.market_data import PriceEvent

logger = logging.getLogger(__name__)

class KafkaProducerService:
    """Kafka producer service for publishing price events"""
    
    def __init__(self, settings: Settings = get_settings()):
        self.settings = settings
        self.producer = self._create_producer()
        self.topic = settings.KAFKA_PRICE_EVENTS_TOPIC
    
    def _create_producer(self) -> Producer:
        """Create and configure Kafka producer"""
        config = {
            'bootstrap.servers': self.settings.KAFKA_BOOTSTRAP_SERVERS,
            'client.id': 'market-data-producer',
            'acks': 'all',  # Wait for all replicas to acknowledge
            'retries': 3,   # Retry failed messages
            'retry.backoff.ms': 1000,  # Backoff between retries
            'compression.type': 'snappy',  # Compress messages
            'batch.size': 16384,  # Batch size in bytes
            'linger.ms': 10,  # Wait time for batching
        }
        
        # Add SASL configuration if provided
        if self.settings.KAFKA_SECURITY_PROTOCOL != "PLAINTEXT":
            config.update({
                'security.protocol': self.settings.KAFKA_SECURITY_PROTOCOL,
                'sasl.mechanism': self.settings.KAFKA_SASL_MECHANISM,
                'sasl.username': self.settings.KAFKA_SASL_USERNAME,
                'sasl.password': self.settings.KAFKA_SASL_PASSWORD,
            })
        
        return Producer(config)
    
    def _delivery_report(self, err: Optional[KafkaError], msg) -> None:
        """Callback for message delivery reports"""
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
    
    async def publish_price_event(self, price_event: PriceEvent) -> bool:
        """
        Publish a price event to Kafka
        
        Args:
            price_event: The price event to publish
            
        Returns:
            bool: True if message was queued successfully, False otherwise
        """
        try:
            # Serialize the price event to JSON
            message_value = price_event.model_dump_json()
            
            # Publish to Kafka
            self.producer.produce(
                topic=self.topic,
                key=price_event.symbol.encode('utf-8'),  # Use symbol as key for partitioning
                value=message_value.encode('utf-8'),
                callback=self._delivery_report
            )
            
            # Trigger any available delivery reports
            self.producer.poll(0)
            
            logger.info(f"Price event queued for symbol: {price_event.symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish price event for {price_event.symbol}: {e}")
            return False
    
    async def publish_price_event_dict(self, event_data: dict) -> bool:
        """
        Publish a price event from dictionary data
        
        Args:
            event_data: Dictionary containing price event data
            
        Returns:
            bool: True if message was queued successfully, False otherwise
        """
        try:
            price_event = PriceEvent(**event_data)
            return await self.publish_price_event(price_event)
        except Exception as e:
            logger.error(f"Failed to create price event from dict: {e}")
            return False
    
    def flush(self, timeout: float = 10.0) -> int:
        """
        Flush any pending messages
        
        Args:
            timeout: Maximum time to wait for messages to be delivered
            
        Returns:
            int: Number of messages still in queue
        """
        return self.producer.flush(timeout)
    
    def close(self) -> None:
        """Close the producer"""
        self.producer.flush()
        logger.info("Kafka producer closed")

# Global producer instance
_kafka_producer: Optional[KafkaProducerService] = None

def get_kafka_producer() -> KafkaProducerService:
    """Get or create Kafka producer instance"""
    global _kafka_producer
    if _kafka_producer is None:
        _kafka_producer = KafkaProducerService()
    return _kafka_producer

async def close_kafka_producer() -> None:
    """Close the global Kafka producer instance"""
    global _kafka_producer
    if _kafka_producer:
        _kafka_producer.close()
        _kafka_producer = None 