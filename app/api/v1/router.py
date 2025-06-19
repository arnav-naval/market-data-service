from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
import httpx
from datetime import datetime, timezone
from app.schemas.market_data import PriceResponse, PollRequest, PollResponse

router = APIRouter()

# Endpoints
@router.get("/prices/latest", response_model=PriceResponse)
async def get_latest_price(symbol: str, provider: Optional[str] = None) -> PriceResponse:
    """
    Get the latest price for a given symbol
    """
    try:
        # For now, only support alpha_vantage
        if provider and provider != "alpha_vantage":
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
        
        # Alpha Vantage API call
        api_key = "demo"  # Replace with actual API key later
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": api_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extract price from Alpha Vantage response
            quote = data.get("Global Quote", {})
            if not quote:
                raise HTTPException(status_code=404, detail=f"No data found for symbol: {symbol}")
            
            price = float(quote.get("05. price", 0))
            timestamp = datetime.now(timezone.utc).isoformat()
            
            return PriceResponse(
                symbol=symbol,
                price=price,
                timestamp=timestamp,
                provider="alpha_vantage"
            )
            
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"API request failed: {e}")
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