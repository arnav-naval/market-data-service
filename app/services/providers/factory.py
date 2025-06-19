from fastapi import Query, HTTPException
from .alpha_vantage import AlphaVantageProvider

def provider_dependency(
    provider: str = Query("alpha_vantage", description="Which market data provider to use")
):
    if provider == "alpha_vantage":
        return AlphaVantageProvider()
   
    raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")