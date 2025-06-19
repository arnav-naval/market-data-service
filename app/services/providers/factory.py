from fastapi import Query, HTTPException, Depends
from app.core.config import Settings, get_settings
from .alpha_vantage import AlphaVantageProvider

def provider_dependency(
    provider: str = Query("alpha_vantage", description="Which market data provider to use"),
    settings: Settings = Depends(get_settings)
):
    if provider == "alpha_vantage":
        return AlphaVantageProvider(settings)
   
    raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")