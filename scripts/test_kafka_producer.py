#!/usr/bin/env python3
"""
Test script for Kafka producer functionality
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.kafka_producer import get_kafka_producer, close_kafka_producer
from app.schemas.market_data import PriceEvent
from datetime import datetime, timezone

async def test_kafka_producer():
    """Test the Kafka producer with sample data"""
    print("Testing Kafka producer...")
    
    try:
        # Get the Kafka producer
        producer = get_kafka_producer()
        print(f"✓ Kafka producer initialized")
        print(f"  - Bootstrap servers: {producer.settings.KAFKA_BOOTSTRAP_SERVERS}")
        print(f"  - Topic: {producer.topic}")
        
        # Create a sample price event
        sample_event = PriceEvent(
            symbol="AAPL",
            price=150.25,
            timestamp=datetime.now(timezone.utc).isoformat(),
            source="alpha_vantage",
            raw_response_id="test-123"
        )
        
        print(f"✓ Created sample price event: {sample_event.symbol} @ ${sample_event.price}")
        
        # Publish the event
        success = await producer.publish_price_event(sample_event)
        
        if success:
            print("✓ Price event published successfully")
        else:
            print("✗ Failed to publish price event")
            return False
        
        # Flush any pending messages
        remaining = producer.flush(timeout=5.0)
        print(f"✓ Flushed producer (remaining messages: {remaining})")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing Kafka producer: {e}")
        return False
    finally:
        # Close the producer
        await close_kafka_producer()
        print("✓ Kafka producer closed")

async def main():
    """Main test function"""
    print("=" * 50)
    print("Kafka Producer Test")
    print("=" * 50)
    
    success = await test_kafka_producer()
    
    print("=" * 50)
    if success:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 