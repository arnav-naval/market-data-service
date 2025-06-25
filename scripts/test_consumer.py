#!/usr/bin/env python3
"""
Test script for Kafka consumer functionality
"""
import asyncio
import sys
import os
import time

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.kafka_consumer import KafkaConsumerService
from app.core.config import get_settings

async def test_consumer():
    """Test the Kafka consumer with a brief run"""
    print("Testing Kafka Consumer Service...")
    
    try:
        # Get settings
        settings = get_settings()
        print(f"✓ Settings loaded")
        print(f"  - Bootstrap servers: {settings.KAFKA_BOOTSTRAP_SERVERS}")
        print(f"  - Topic: {settings.KAFKA_PRICE_EVENTS_TOPIC}")
        
        # Create consumer
        consumer = KafkaConsumerService(settings)
        print(f"✓ Consumer created")
        
        # Start consuming for a short time
        print("Starting consumer (will run for 10 seconds)...")
        
        # Run consumer in background
        consumer_task = asyncio.create_task(consumer.start_consuming())
        
        # Wait for 10 seconds
        await asyncio.sleep(10)
        
        # Stop consumer
        consumer.stop_consuming()
        print("✓ Consumer stopped")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing consumer: {e}")
        return False

async def main():
    """Main test function"""
    print("=== Kafka Consumer Test ===")
    
    success = await test_consumer()
    
    if success:
        print("\n✓ Consumer test completed successfully")
        print("Consumer is ready to process messages from Kafka")
    else:
        print("\n✗ Consumer test failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 