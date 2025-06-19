from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from app.schemas.market_data import PriceResponse, PollRequest, PollResponse
from app.services.providers import ProviderFactory

router = APIRouter()

# Endpoints
@router.get("/prices/latest", response_model=PriceResponse)
async def get_latest_price(symbol: str, provider: Optional[str] = "alpha_vantage") -> PriceResponse:
    """
    Get the latest price for a given symbol
    """
    try:
        # Get the appropriate provider
        market_data_provider = ProviderFactory.get_provider(provider)
        
        # Fetch the latest price using the provider
        return await market_data_provider.get_latest_price(symbol)
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching price for {symbol}: {e}")

@router.post("/prices/poll")
async def start_polling(request: PollRequest) -> PollResponse:
    """
    Start polling for prices of given symbols
    """
    # TODO: Implement actual polling logic
    return PollResponse(
        job_id="poll_123",
        status="accepted",
        config={
            "symbols": request.symbols,
            "interval": request.interval
        }
    ) 