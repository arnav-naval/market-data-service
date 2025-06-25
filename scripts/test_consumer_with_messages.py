#!/usr/bin/env python3
"""
Comprehensive test script for Kafka consumer functionality
Tests consumer by publishing messages and verifying processing
"""
import asyncio
import sys
import os
import time
import uuid
from datetime import datetime, timezone

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.kafka_consumer import KafkaConsumerService
from app.services.kafka_producer import get_kafka_producer, close_kafka_producer
from app.schemas.market_data import PriceEvent
from app.core.config import get_settings
from app.core.database import async_session
from app.models.prices import PricePoint
from app.models.market_data import RawMarketData
from app.models.averages import MovingAverage
from sqlalchemy import select, desc

async def setup_test_data():
    """Create test data in the database"""
    print("Setting up test data...")
    
    try:
        async with async_session() as session:
            # Create test raw market data
            raw_data = RawMarketData(
                id=str(uuid.uuid4()),
                symbol="TEST",
                provider="test_provider",
                raw_response={"test": "data"},
                timestamp=datetime.now(timezone.utc)
            )
            session.add(raw_data)
            await session.flush()  # Get the ID
            
            # Create test price points (need 5 for moving average)
            for i in range(5):
                price_point = PricePoint(
                    symbol="TEST",
                    price=100.0 + i,  # 100, 101, 102, 103, 104
                    timestamp=datetime.now(timezone.utc),
                    provider="test_provider",
                    raw_market_data_id=raw_data.id
                )
                session.add(price_point)
            
            await session.commit()
            print(f"✓ Created test data with raw_response_id: {raw_data.id}")
            return raw_data.id
            
    except Exception as e:
        print(f"✗ Error setting up test data: {e}")
        return None

async def publish_test_message(raw_response_id: str):
    """Publish a test message to Kafka"""
    print("Publishing test message to Kafka...")
    
    try:
        producer = get_kafka_producer()
        
        # Create test price event
        test_event = PriceEvent(
            symbol="TEST",
            price=105.0,
            timestamp=datetime.now(timezone.utc).isoformat(),
            source="test_provider",
            raw_response_id=raw_response_id
        )
        
        # Publish to Kafka
        success = await producer.publish_price_event(test_event)
        
        if success:
            print("✓ Test message published successfully")
            # Flush to ensure delivery
            producer.flush(timeout=5.0)
            return True
        else:
            print("✗ Failed to publish test message")
            return False
            
    except Exception as e:
        print(f"✗ Error publishing test message: {e}")
        return False

async def verify_moving_average():
    """Verify that moving average was calculated and stored"""
    print("Verifying moving average calculation...")
    
    try:
        async with async_session() as session:
            # Check if moving average was created
            query = select(MovingAverage).where(
                MovingAverage.symbol == "TEST"
            ).order_by(desc(MovingAverage.timestamp))
            
            result = await session.execute(query)
            moving_average = result.scalar_one_or_none()
            
            if moving_average:
                print(f"✓ Moving average found: {moving_average.moving_average}")
                print(f"  - Symbol: {moving_average.symbol}")
                print(f"  - Interval: {moving_average.interval}")
                print(f"  - Price count: {moving_average.price_count}")
                return True
            else:
                print("✗ No moving average found")
                return False
                
    except Exception as e:
        print(f"✗ Error verifying moving average: {e}")
        return False

async def test_consumer_with_messages():
    """Test the consumer by publishing messages and verifying processing"""
    print("=== Comprehensive Kafka Consumer Test ===")
    
    try:
        # 1. Setup test data
        raw_response_id = await setup_test_data()
        if not raw_response_id:
            return False
        
        # 2. Get settings and create consumer
        settings = get_settings()
        print(f"✓ Settings loaded")
        print(f"  - Bootstrap servers: {settings.KAFKA_BOOTSTRAP_SERVERS}")
        print(f"  - Topic: {settings.KAFKA_PRICE_EVENTS_TOPIC}")
        
        consumer = KafkaConsumerService(settings)
        print(f"✓ Consumer created")
        
        # 3. Start consumer in background
        print("Starting consumer...")
        consumer_task = asyncio.create_task(consumer.start_consuming())
        
        # 4. Wait a moment for consumer to start
        await asyncio.sleep(2)
        
        # 5. Publish test message
        message_published = await publish_test_message(raw_response_id)
        if not message_published:
            consumer.stop_consuming()
            return False
        
        # 6. Wait for processing (consumer should process the message)
        print("Waiting for message processing...")
        await asyncio.sleep(5)
        
        # 7. Stop consumer
        consumer.stop_consuming()
        print("✓ Consumer stopped")
        
        # 8. Verify results
        moving_average_created = await verify_moving_average()
        
        return moving_average_created
        
    except Exception as e:
        print(f"✗ Error in comprehensive test: {e}")
        return False

async def test_consumer_connection():
    """Test basic consumer connectivity"""
    print("=== Basic Consumer Connection Test ===")
    
    try:
        settings = get_settings()
        consumer = KafkaConsumerService(settings)
        
        # Test consumer creation (this tests connection)
        print("✓ Consumer created successfully")
        print(f"  - Bootstrap servers: {settings.KAFKA_BOOTSTRAP_SERVERS}")
        print(f"  - Topic: {settings.KAFKA_PRICE_EVENTS_TOPIC}")
        
        # Test subscription
        consumer.consumer.subscribe([consumer.topic])
        print("✓ Consumer subscribed to topic")
        
        # Test polling (non-blocking)
        msg = consumer.consumer.poll(timeout=1.0)
        print("✓ Consumer polling works")
        
        consumer.stop_consuming()
        print("✓ Consumer stopped successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("Starting Kafka Consumer Tests...")
    print("=" * 50)
    
    # Test 1: Basic connection
    connection_success = await test_consumer_connection()
    
    if not connection_success:
        print("\n✗ Basic connection test failed. Check Kafka connectivity.")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    
    # Test 2: Full message processing test
    processing_success = await test_consumer_with_messages()
    
    print("\n" + "=" * 50)
    
    if processing_success:
        print("✓ All consumer tests passed!")
        print("Consumer is working correctly and processing messages.")
    else:
        print("✗ Message processing test failed!")
        print("Check logs for detailed error information.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 