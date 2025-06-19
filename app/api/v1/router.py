from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from app.schemas.market_data import PriceResponse, PollRequest, PollResponse
from app.services.providers.factory import provider_dependency
from app.services.providers.base import MarketDataProvider

router = APIRouter()

# Route to get the latest price for a given symbol
@router.get("/prices/latest", response_model=PriceResponse)
async def get_latest_price(
    symbol: str,
    provider: MarketDataProvider = Depends(provider_dependency)
) -> PriceResponse:
    """
    Get the latest price for a given symbol
    """
    try:
        return await provider.get_latest_price(symbol)
            
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