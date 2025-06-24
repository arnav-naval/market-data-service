from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.market_data import PriceResponse, PollRequest, PollResponse
from app.services.providers.factory import provider_dependency
from app.services.providers.base import MarketDataProvider
from app.services.market_data_service import get_market_data_service
from app.core.database import get_db

router = APIRouter()

# Route to get the latest price for a given symbol
@router.get("/prices/latest", response_model=PriceResponse)
async def get_latest_price(
    symbol: str,
    provider: MarketDataProvider = Depends(provider_dependency),
    db: AsyncSession = Depends(get_db)
) -> PriceResponse:
    """
    Get the latest price for a given symbol
    """
    try:
        market_data_service = get_market_data_service()
        
        # Check if we have a recent processed price in Redis
        cached_price = await market_data_service.get_latest_processed_price(symbol)
        if cached_price:
            return cached_price
        
        # Fetch fresh data from provider
        price_response, raw_response = await provider.get_latest_price_with_raw_data(symbol)
        
        # Process the data: store raw data and publish to Kafka
        processed_response = await market_data_service.process_price_data(
            symbol=symbol,
            price=price_response.price,
            timestamp=price_response.timestamp,
            provider=price_response.provider,
            raw_response=raw_response,
            db=db
        )
        
        return processed_response
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching price for {symbol}: {e}")

# Route to start polling for prices of given symbols
@router.post("/prices/poll")
async def start_polling(
    request: PollRequest,
    provider: MarketDataProvider = Depends(provider_dependency)
) -> PollResponse:
    """
    Start polling for prices of given symbols
    """
    # TODO: Implement actual polling logic
    return PollResponse(
        job_id="poll_123",
        status="accepted",
        config={
            "symbols": request.symbols,
            "interval": request.interval,
            "provider": "alpha_vantage"  # This could be extracted from the provider instance
        }
    ) 