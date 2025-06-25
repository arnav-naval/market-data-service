#!/usr/bin/env python3
"""
Test script for Kafka consumer running in Docker container
"""
import asyncio
import sys
import os
import time
import traceback

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.kafka_consumer import KafkaConsumerService
from app.core.config import get_settings


async def test_database_connection():
    """Test database connection with detailed error reporting"""
    print("=== Database Connection Test ===")
    
    try:
        # Get settings
        settings = get_settings()
        settings.DATABASE_URL = "postgresql+asyncpg://arnav:market123@localhost:5432/market_data"
        print(f"✓ Settings loaded")
        print(f"  - Database URL: {settings.DATABASE_URL}")
        
        # Check if DATABASE_URL is properly set
        if not settings.DATABASE_URL or settings.DATABASE_URL == "default":
            print("✗ DATABASE_URL is not properly configured")
            print("  Please check your environment variables or .env file")
            return False
        
        # Parse database URL for debugging
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(settings.DATABASE_URL)
            print(f"  - Database type: {parsed_url.scheme}")
            print(f"  - Host: {parsed_url.hostname}")
            print(f"  - Port: {parsed_url.port}")
            print(f"  - Database: {parsed_url.path[1:] if parsed_url.path else 'N/A'}")
            print(f"  - Username: {parsed_url.username}")
        except Exception as e:
            print(f"  - Warning: Could not parse DATABASE_URL: {e}")
        
        # Test database connection
        print("Testing database connection...")
        from app.core.database import async_session, async_engine
        
        # Test engine creation
        print("  - Testing engine creation...")
        try:
            # Test if we can create the engine
            print(f"    Engine created successfully")
            
            # Test connection
            print("  - Testing connection...")
            async with async_engine.begin() as conn:
                result = await conn.execute("SELECT 1 as test")
                row = result.fetchone()
                print(f"    ✓ Connection test successful: {row[0]}")
            
            # Test session
            print("  - Testing session...")
            async with async_session() as session:
                from sqlalchemy import text
                result = await session.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                print(f"    ✓ Session test successful: {row[0]}")
                
                # Test if tables exist
                result = await session.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                tables = [row[0] for row in result.fetchall()]
                print(f"    ✓ Available tables: {tables}")
            
            return True
            
        except Exception as e:
            print(f"    ✗ Database connection failed: {e}")
            print(f"    Error type: {type(e).__name__}")
            print(f"    Full traceback:")
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"✗ Settings or import error: {e}")
        print(f"Error type: {type(e).__name__}")
        print(f"Full traceback:")
        traceback.print_exc()
        return False

async def test_container_consumer():
    """Test consumer in container environment"""
    print("=== Container Consumer Test ===")
    print("Testing consumer in container environment...")
    
    try:
        # Get settings
        settings = get_settings()
        print(f"✓ Settings loaded")
        print(f"  - Bootstrap servers: {settings.KAFKA_BOOTSTRAP_SERVERS}")
        print(f"  - Topic: {settings.KAFKA_PRICE_EVENTS_TOPIC}")
        print(f"  - Database URL: {settings.DATABASE_URL}")
        
        # Create consumer
        consumer = KafkaConsumerService(settings)
        print(f"✓ Consumer created")
        
        # Test subscription
        consumer.consumer.subscribe([consumer.topic])
        print(f"✓ Subscribed to topic: {consumer.topic}")
        
        # Test polling (non-blocking)
        print("Testing message polling...")
        msg = consumer.consumer.poll(timeout=2.0)
        if msg is None:
            print("✓ No messages available (expected)")
        else:
            print(f"✓ Received message: {msg.value()}")
        
        # Test database connection with detailed error reporting
        db_success = await test_database_connection()
        if not db_success:
            print("✗ Database connection test failed")
            return False
        
        consumer.stop_consuming()
        print("✓ Consumer stopped successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Container test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        print(f"Full traceback:")
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("Starting Container Consumer Test...")
    print("=" * 50)
    
    # Test database connection first
    print("Testing database connection...")
    db_success = await test_database_connection()
    
    if not db_success:
        print("\n" + "=" * 50)
        print("✗ Database connection test failed!")
        print("Please check:")
        print("1. Database is running and accessible")
        print("2. DATABASE_URL environment variable is set correctly")
        print("3. Database credentials are correct")
        print("4. Network connectivity to database host")
        print("5. Database port is open and accessible")
        sys.exit(1)
    
    # Test consumer
    print("\nTesting consumer...")
    success = await test_container_consumer()
    
    print("=" * 50)
    if success:
        print("✓ Container consumer test passed!")
        print("Consumer is ready to run in container environment.")
    else:
        print("✗ Container consumer test failed!")
        print("Check container logs and configuration.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 