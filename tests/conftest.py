"""
Pytest configuration and fixtures for end-to-end tests
"""
import pytest
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from typing import AsyncGenerator, List

from app.core.database import async_session
from app.core.config import get_settings
from app.services.kafka_producer import get_kafka_producer, close_kafka_producer
from app.schemas.market_data import PriceEvent
from app.models.prices import PricePoint
from app.models.market_data import RawMarketData
from app.models.averages import MovingAverage
from sqlalchemy import select, desc

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def db_session():
    """Provide a database session for tests"""
    async with async_session() as session:
        yield session

@pytest.fixture
async def kafka_producer():
    """Provide a Kafka producer for tests"""
    producer = get_kafka_producer()
    yield producer
    await close_kafka_producer()

@pytest.fixture
def test_symbol():
    """Provide a test symbol for price events"""
    return f"TEST_{uuid.uuid4().hex[:8].upper()}"

@pytest.fixture
async def sample_price_data(test_symbol: str) -> List[dict]:
    """Generate sample price data for testing"""
    base_price = 100.0
    base_time = datetime.now(timezone.utc)
    
    return [
        {
            "symbol": test_symbol,
            "price": base_price + i,
            "timestamp": (base_time + timedelta(minutes=i)).isoformat(),
            "source": "alpha_vantage",
        }
        for i in range(10)  # Generate 10 price points
    ]

@pytest.fixture
async def setup_price_points(db_session, test_symbol: str, sample_price_data: List[dict]) -> str:
    """Setup price points in database and return raw_response_id"""
    # Create 5 separate price points with different raw_response_ids
    raw_response_ids = []
    
    for i, price_data in enumerate(sample_price_data[:5]):  # Use first 5 for initial setup
        # Create raw market data for each price point
        raw_data = RawMarketData(
            id=str(uuid.uuid4()),
            symbol=test_symbol,
            provider="alpha_vantage",
            raw_response={"test": "data"},
            timestamp=datetime.now(timezone.utc) + timedelta(minutes=i)
        )
        db_session.add(raw_data)
        await db_session.flush()
        
        # Create price point
        price_point = PricePoint(
            symbol=price_data["symbol"],
            price=price_data["price"],
            timestamp=datetime.fromisoformat(price_data["timestamp"]),
            provider=price_data["source"],
            raw_data_id=raw_data.id
        )
        db_session.add(price_point)
        raw_response_ids.append(raw_data.id)
    
    await db_session.commit()
    # Return the first raw_response_id for backward compatibility
    return raw_response_ids[0]

@pytest.fixture
async def cleanup_test_data(db_session, test_symbol: str):
    """Cleanup test data after tests"""
    yield
    # Clean up price points
    await db_session.execute(
        select(PricePoint).where(PricePoint.symbol == test_symbol)
    )
    # Clean up moving averages
    await db_session.execute(
        select(MovingAverage).where(MovingAverage.symbol == test_symbol)
    )
    # Clean up raw market data
    await db_session.execute(
        select(RawMarketData).where(RawMarketData.symbol == test_symbol)
    )
    await db_session.commit() 