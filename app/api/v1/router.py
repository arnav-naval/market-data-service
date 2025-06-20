from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional, Dict, Any
from app.schemas.market_data import PriceResponse, PollRequest, PollResponse
from app.services.providers.factory import provider_dependency
from app.services.providers.base import MarketDataProvider
from app.core.redis import RedisService, get_redis_service

router = APIRouter()

# Route to get the latest price for a given symbol
@router.get("/prices/latest", response_model=PriceResponse)
async def get_latest_price(
    symbol: str,
    provider: MarketDataProvider = Depends(provider_dependency),
    redis_service: RedisService = Depends(get_redis_service)
) -> PriceResponse:
    """
    Get the latest price for a given symbol with Redis caching
    """
    try:
        # Check cache first
        cache_key = f"price:{symbol}:{provider.__class__.__name__.lower()}"
        cached_data = await redis_service.get_cache(cache_key)
        
        if cached_data:
            return PriceResponse(**cached_data)
        
        # If not in cache, fetch from provider
        price_response = await provider.get_latest_price(symbol)
        
        # Cache the response for 5 minutes (300 seconds)
        await redis_service.set_cache(cache_key, price_response.dict(), ttl=300)
        
        return price_response
            
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

# Redis-specific endpoints
@router.get("/cache/status")
async def get_cache_status(
    redis_service: RedisService = Depends(get_redis_service)
) -> Dict[str, Any]:
    """
    Get Redis cache status and statistics
    """
    try:
        client = await redis_service.get_client()
        info = await client.info()
        
        return {
            "status": "connected",
            "redis_version": info.get("redis_version"),
            "connected_clients": info.get("connected_clients"),
            "used_memory_human": info.get("used_memory_human"),
            "total_commands_processed": info.get("total_commands_processed"),
            "keyspace_hits": info.get("keyspace_hits"),
            "keyspace_misses": info.get("keyspace_misses")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis connection error: {e}")

@router.delete("/cache/clear")
async def clear_cache(
    redis_service: RedisService = Depends(get_redis_service)
) -> Dict[str, str]:
    """
    Clear all cached data
    """
    try:
        client = await redis_service.get_client()
        await client.flushdb()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {e}")

@router.get("/cache/keys")
async def list_cache_keys(
    pattern: str = "*",
    redis_service: RedisService = Depends(get_redis_service)
) -> Dict[str, Any]:
    """
    List cache keys matching a pattern
    """
    try:
        client = await redis_service.get_client()
        keys = await client.keys(pattern)
        return {
            "pattern": pattern,
            "count": len(keys),
            "keys": keys[:100]  # Limit to first 100 keys
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing keys: {e}")

@router.get("/cache/{key}")
async def get_cache_value(
    key: str,
    redis_service: RedisService = Depends(get_redis_service)
) -> Dict[str, Any]:
    """
    Get a specific cached value
    """
    try:
        value = await redis_service.get_cache(key)
        if value is None:
            raise HTTPException(status_code=404, detail=f"Key '{key}' not found")
        return {"key": key, "value": value}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving cache: {e}")

@router.delete("/cache/{key}")
async def delete_cache_key(
    key: str,
    redis_service: RedisService = Depends(get_redis_service)
) -> Dict[str, str]:
    """
    Delete a specific cache key
    """
    try:
        success = await redis_service.delete_cache(key)
        if success:
            return {"message": f"Key '{key}' deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Key '{key}' not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting cache: {e}") 