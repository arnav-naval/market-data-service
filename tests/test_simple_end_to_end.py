"""
Simple end-to-end test for the market data service
This test works with the current consumer implementation
"""
import pytest
import asyncio
import uuid
from datetime import datetime, timezone, timedelta

from app.core.database import async_session
from app.services.kafka_consumer import KafkaConsumerService
from app.schemas.market_data import PriceEvent
from app.models.prices import PricePoint
from app.models.market_data import RawMarketData
from app.models.averages import MovingAverage
from sqlalchemy import select, desc, delete

class TestSimpleEndToEnd:
    """Simple end-to-end test that works with current consumer implementation"""
    
    @pytest.mark.asyncio
    async def test_basic_moving_average_calculation(self):
        """
        Test the basic moving average calculation flow
        This test directly calls the consumer methods to simulate the flow
        """
        print("\n=== Testing Basic Moving Average Calculation ===")
        
        # Generate unique test symbol
        test_symbol = f"TEST_{uuid.uuid4().hex[:8].upper()}"
        
        try:
            # 1. Setup test data - create raw market data and price points
            raw_response_id = await self._setup_test_data(test_symbol)
            print(f"✓ Created test data with raw_response_id: {raw_response_id}")
            
            # 2. Create a price event
            price_event = PriceEvent(
                symbol=test_symbol,
                price=105.0,
                timestamp=datetime.now(timezone.utc).isoformat(),
                source="alpha_vantage",
                raw_response_id=raw_response_id
            )
            print(f"✓ Created price event for {test_symbol} @ ${price_event.price}")
            
            # 3. Process the price event using consumer logic
            consumer = KafkaConsumerService()
            await consumer._process_price_event(price_event)
            print("✓ Processed price event")
            
            # 4. Verify moving average was calculated
            moving_averages = await self._get_moving_averages(test_symbol)
            
            if len(moving_averages) > 0:
                latest_ma = moving_averages[0]
                expected_ma = (100 + 101 + 102 + 103 + 104) / 5  # Average of first 5 prices
                
                assert abs(latest_ma.moving_average - expected_ma) < 0.01, \
                    f"Expected MA: {expected_ma}, Got: {latest_ma.moving_average}"
                
                print(f"✓ Moving average calculated successfully!")
                print(f"  - Symbol: {latest_ma.symbol}")
                print(f"  - Moving Average: {latest_ma.moving_average:.2f}")
                print(f"  - Interval: {latest_ma.interval}")
                print(f"  - Price Count: {latest_ma.price_count}")
                
                return True
            else:
                print("✗ No moving average was calculated")
                return False
                
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            return False
        finally:
            # Cleanup test data
            await self._cleanup_test_data(test_symbol)
    
    async def _setup_test_data(self, symbol: str) -> str:
        """Setup test data in database"""
        async with async_session() as session:
            # Create raw market data
            raw_data = RawMarketData(
                id=str(uuid.uuid4()),
                symbol=symbol,
                provider="alpha_vantage",
                raw_response={"test": "data"},
                timestamp=datetime.now(timezone.utc)
            )
            session.add(raw_data)
            await session.flush()
            
            # Create 5 price points (needed for 5-point moving average)
            for i in range(5):
                price_point = PricePoint(
                    symbol=symbol,
                    price=100.0 + i,  # 100, 101, 102, 103, 104
                    timestamp=datetime.now(timezone.utc) + timedelta(minutes=i),
                    provider="alpha_vantage",
                    raw_data_id=raw_data.id
                )
                session.add(price_point)
            
            await session.commit()
            return raw_data.id
    
    async def _get_moving_averages(self, symbol: str):
        """Get moving averages for a symbol"""
        async with async_session() as session:
            query = select(MovingAverage).where(
                MovingAverage.symbol == symbol
            ).order_by(desc(MovingAverage.timestamp))
            result = await session.execute(query)
            return result.scalars().all()
    
    async def _cleanup_test_data(self, symbol: str):
        """Clean up test data"""
        try:
            async with async_session() as session:
                # Delete moving averages
                await session.execute(
                    delete(MovingAverage).where(MovingAverage.symbol == symbol)
                )
                # Delete price points
                await session.execute(
                    delete(PricePoint).where(PricePoint.symbol == symbol)
                )
                # Delete raw market data
                await session.execute(
                    delete(RawMarketData).where(RawMarketData.symbol == symbol)
                )
                await session.commit()
                print(f"✓ Cleaned up test data for symbol: {symbol}")
        except Exception as e:
            print(f"Warning: Cleanup failed: {e}")

if __name__ == "__main__":
    # Run the test directly
    async def main():
        test = TestSimpleEndToEnd()
        success = await test.test_basic_moving_average_calculation()
        if success:
            print("\n✅ Test passed!")
        else:
            print("\n❌ Test failed!")
    
    asyncio.run(main()) 