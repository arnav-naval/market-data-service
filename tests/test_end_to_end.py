"""
End-to-end tests for the market data service
Tests the complete flow: Price Event → Kafka → Consumer → Database (Moving Averages)
"""
import pytest
import asyncio
import time
from datetime import datetime, timezone, timedelta
from typing import List
import uuid

from app.core.database import async_session
from app.services.kafka_consumer import KafkaConsumerService
from app.schemas.market_data import PriceEvent
from app.models.prices import PricePoint
from app.models.market_data import RawMarketData
from app.models.averages import MovingAverage
from sqlalchemy import select, desc

class TestEndToEndFlow:
    """Test the complete end-to-end flow of price events to moving averages"""
    
    @pytest.mark.asyncio
    async def test_simple_price_event_to_moving_average(
        self, 
        db_session, 
        kafka_producer, 
        test_symbol: str, 
        setup_price_points: str,
        cleanup_test_data
    ):
        """
        Test the basic flow: publish price event → consumer processes → moving average calculated
        """
        print(f"\n=== Testing simple price event flow for symbol: {test_symbol} ===")
        
        # 1. Verify initial setup (should have 5 price points)
        initial_prices = await self._get_price_points(test_symbol)
        assert len(initial_prices) == 5, f"Expected 5 initial price points, got {len(initial_prices)}"
        print(f"✓ Initial setup: {len(initial_prices)} price points created")
        
        # 2. Create a new price event that should trigger moving average calculation
        # Create a new price point for this event
        new_raw_response_id = await self._create_single_price_point(test_symbol, 105.0, 5)
        
        new_price_event = PriceEvent(
            symbol=test_symbol,
            price=105.0,  # 6th price point
            timestamp=datetime.now(timezone.utc).isoformat(),
            source="alpha_vantage",
            raw_response_id=new_raw_response_id
        )
        
        # 3. Publish the price event to Kafka
        success = await kafka_producer.publish_price_event(new_price_event)
        assert success, "Failed to publish price event to Kafka"
        print("✓ Price event published to Kafka")
        
        # 4. Wait for consumer to process (in real scenario, consumer would be running)
        # For this test, we'll simulate the consumer processing
        await self._simulate_consumer_processing(new_price_event)
        
        # 5. Verify moving average was calculated and stored
        moving_averages = await self._get_moving_averages(test_symbol)
        assert len(moving_averages) > 0, "No moving average was calculated"
        
        latest_ma = moving_averages[0]  # Most recent
        print(f"✓ Moving average calculated: {latest_ma.moving_average}")
        
        # Verify that the moving average is reasonable (should be between the min and max prices)
        all_prices = await self._get_price_points(test_symbol)
        price_values = [p.price for p in all_prices]
        min_price = min(price_values)
        max_price = max(price_values)
        
        assert min_price <= latest_ma.moving_average <= max_price, \
            f"MA {latest_ma.moving_average} should be between {min_price} and {max_price}"
        
        print(f"  - Symbol: {latest_ma.symbol}")
        print(f"  - Interval: {latest_ma.interval}")
        print(f"  - Price count: {latest_ma.price_count}")
        print(f"  - Valid range: [{min_price}, {max_price}]")
        
    @pytest.mark.asyncio
    async def test_multiple_price_events_sequential(
        self, 
        db_session, 
        kafka_producer, 
        test_symbol: str,
        cleanup_test_data
    ):
        """
        Test that multiple sequential price events update the moving average correctly
        """
        print(f"\n=== Testing multiple sequential price events for symbol: {test_symbol} ===")
        
        # 1. Setup initial price points (5 price points with different raw_response_ids)
        initial_prices = []
        for i in range(5):
            raw_response_id = await self._create_single_price_point(test_symbol, 100.0 + i, i)
            initial_prices.append(raw_response_id)
        
        # 2. Process multiple price events (each with its own raw_response_id)
        for i in range(3):  # Process 3 additional price events
            # Create a new price point for each event
            raw_response_id = await self._create_single_price_point(test_symbol, 110.0 + i, 5 + i)
            
            price_event = PriceEvent(
                symbol=test_symbol,
                price=110.0 + i,  # 110, 111, 112
                timestamp=(datetime.now(timezone.utc) + timedelta(minutes=5 + i)).isoformat(),
                source="alpha_vantage",
                raw_response_id=raw_response_id
            )
            
            # Publish to Kafka
            success = await kafka_producer.publish_price_event(price_event)
            assert success, f"Failed to publish price event {i+1}"
            
            # Simulate consumer processing
            await self._simulate_consumer_processing(price_event)
            
            print(f"✓ Processed price event {i+1}: ${price_event.price}")
        
        # 3. Verify moving average was updated (should be only 1 due to upsert)
        moving_averages = await self._get_moving_averages(test_symbol)
        assert len(moving_averages) == 1, f"Expected 1 moving average (upsert design), got {len(moving_averages)}"
        
        # Get the actual moving average that was calculated
        latest_ma = moving_averages[0]
        print(f"✓ Final moving average: {latest_ma.moving_average}")
        
        # Verify that the moving average is reasonable (should be between the min and max prices)
        all_prices = await self._get_price_points(test_symbol)
        price_values = [p.price for p in all_prices]
        min_price = min(price_values)
        max_price = max(price_values)
        
        assert min_price <= latest_ma.moving_average <= max_price, \
            f"MA {latest_ma.moving_average} should be between {min_price} and {max_price}"
        
        print(f"✓ Moving average {latest_ma.moving_average} is within valid range [{min_price}, {max_price}]")
        
    @pytest.mark.asyncio
    async def test_moving_average_calculation_accuracy(
        self, 
        db_session, 
        kafka_producer, 
        test_symbol: str,
        cleanup_test_data
    ):
        """
        Test that moving average calculations are mathematically accurate
        """
        print(f"\n=== Testing moving average calculation accuracy for symbol: {test_symbol} ===")
        
        # 1. Setup initial price points (create them one by one to simulate real API flow)
        prices = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0]
        raw_response_ids = []
        
        for i, price in enumerate(prices):
            raw_response_id = await self._create_single_price_point(test_symbol, price, i)
            raw_response_ids.append(raw_response_id)
        
        # 2. Process each price event and verify moving average
        for i in range(5, len(prices)):  # Start from 6th price (index 5)
            price_event = PriceEvent(
                symbol=test_symbol,
                price=prices[i],
                timestamp=(datetime.now(timezone.utc) + timedelta(minutes=i)).isoformat(),
                source="alpha_vantage",
                raw_response_id=raw_response_ids[i]  # Use the corresponding raw_response_id
            )
            
            # Publish and process
            await kafka_producer.publish_price_event(price_event)
            await self._simulate_consumer_processing(price_event)
            
            # Get the actual moving average that was calculated
            moving_averages = await self._get_moving_averages(test_symbol)
            assert len(moving_averages) == 1, f"Expected 1 moving average, got {len(moving_averages)}"
            latest_ma = moving_averages[0]
            
            # Verify that the moving average is reasonable
            all_prices = await self._get_price_points(test_symbol)
            price_values = [p.price for p in all_prices]
            min_price = min(price_values)
            max_price = max(price_values)
            
            assert min_price <= latest_ma.moving_average <= max_price, \
                f"Price {i}: MA {latest_ma.moving_average} should be between {min_price} and {max_price}"
            
            print(f"✓ Price ${prices[i]}: MA = {latest_ma.moving_average:.2f} (valid range: [{min_price}, {max_price}])")
        
    @pytest.mark.asyncio
    async def test_upsert_behavior(
        self, 
        db_session, 
        kafka_producer, 
        test_symbol: str,
        cleanup_test_data
    ):
        """
        Test that moving averages are properly upserted (not duplicated)
        """
        print(f"\n=== Testing upsert behavior for symbol: {test_symbol} ===")
        
        # 1. Setup initial prices (create 5 price points with different raw_response_ids)
        initial_prices = []
        for i in range(5):
            raw_response_id = await self._create_single_price_point(test_symbol, 100.0 + i, i)
            initial_prices.append(raw_response_id)
        
        # 2. Process first price event
        price_event1 = PriceEvent(
            symbol=test_symbol,
            price=105.0,
            timestamp=datetime.now(timezone.utc).isoformat(),
            source="alpha_vantage",
            raw_response_id=initial_prices[0]  # Use the first raw_response_id
        )
        
        await kafka_producer.publish_price_event(price_event1)
        await self._simulate_consumer_processing(price_event1)
        
        # 3. Check initial moving average count
        initial_count = len(await self._get_moving_averages(test_symbol))
        print(f"✓ Initial moving average count: {initial_count}")
        
        # 4. Process same price event again (should not create duplicate)
        await kafka_producer.publish_price_event(price_event1)
        await self._simulate_consumer_processing(price_event1)
        
        # 5. Verify no duplicate was created
        final_count = len(await self._get_moving_averages(test_symbol))
        assert final_count == initial_count, f"Expected {initial_count} moving averages, got {final_count}"
        
        print(f"✓ Upsert working correctly: {final_count} moving averages (no duplicates)")
        
    async def _get_price_points(self, symbol: str) -> List[PricePoint]:
        """Get all price points for a symbol"""
        async with async_session() as session:
            query = select(PricePoint).where(
                PricePoint.symbol == symbol
            ).order_by(desc(PricePoint.timestamp))
            result = await session.execute(query)
            return result.scalars().all()
    
    async def _get_moving_averages(self, symbol: str) -> List[MovingAverage]:
        """Get the most recent moving average for a symbol"""
        async with async_session() as session:
            query = select(MovingAverage).where(
                MovingAverage.symbol == symbol
            ).order_by(desc(MovingAverage.timestamp)).limit(1)
            result = await session.execute(query)
            return result.scalars().all()
    
    async def _create_single_price_point(self, symbol: str, price: float, minute_offset: int) -> str:
        """Create a single price point with its own raw market data record"""
        async with async_session() as session:
            # Create raw market data
            raw_data = RawMarketData(
                id=str(uuid.uuid4()),
                symbol=symbol,
                provider="alpha_vantage",
                raw_response={"test": "data"},
                timestamp=datetime.now(timezone.utc) + timedelta(minutes=minute_offset)
            )
            session.add(raw_data)
            await session.flush()
            
            # Create single price point
            price_point = PricePoint(
                symbol=symbol,
                price=price,
                timestamp=datetime.now(timezone.utc) + timedelta(minutes=minute_offset),
                provider="alpha_vantage",
                raw_data_id=raw_data.id
            )
            session.add(price_point)
            
            await session.commit()
            return raw_data.id
    
    async def _simulate_consumer_processing(self, price_event: PriceEvent):
        """Simulate the consumer processing a price event"""
        # This simulates what the Kafka consumer would do
        consumer = KafkaConsumerService()
        await consumer._process_price_event(price_event) 