import json
import redis.asyncio as redis
from typing import Optional, Any
from fastapi import Depends
from app.core.config import Settings, get_settings


class RedisService:
    """Redis service for caching and data storage"""
    
    def __init__(self, settings: Settings = Depends(get_settings)):
        self.redis_url = settings.REDIS_URL
        self.redis_db = settings.REDIS_DB
        self.redis_password = settings.REDIS_PASSWORD
        self.cache_ttl = settings.REDIS_CACHE_TTL
        self._redis_client: Optional[redis.Redis] = None
    
    async def get_client(self) -> redis.Redis:
        """Get Redis client instance"""
        if self._redis_client is None:
            self._redis_client = redis.from_url(
                self.redis_url,
                db=self.redis_db,
                password=self.redis_password if self.redis_password else None,
                decode_responses=True
            )
        return self._redis_client
    
    async def set_cache(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache with optional TTL"""
        try:
            client = await self.get_client()
            serialized_value = json.dumps(value)
            ttl = ttl or self.cache_ttl
            return await client.setex(key, ttl, serialized_value)
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    async def get_cache(self, key: str) -> Optional[Any]:
        """Get a value from cache"""
        try:
            client = await self.get_client()
            value = await client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    async def delete_cache(self, key: str) -> bool:
        """Delete a key from cache"""
        try:
            client = await self.get_client()
            return bool(await client.delete(key))
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache"""
        try:
            client = await self.get_client()
            return bool(await client.exists(key))
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False
    
    async def set_hash(self, key: str, mapping: dict, ttl: Optional[int] = None) -> bool:
        """Set a hash in cache"""
        try:
            client = await self.get_client()
            result = await client.hset(key, mapping=mapping)
            if ttl:
                await client.expire(key, ttl)
            return bool(result)
        except Exception as e:
            print(f"Redis hset error: {e}")
            return False
    
    async def get_hash(self, key: str, field: Optional[str] = None) -> Optional[Any]:
        """Get a hash or hash field from cache"""
        try:
            client = await self.get_client()
            if field:
                value = await client.hget(key, field)
                return json.loads(value) if value else None
            else:
                hash_data = await client.hgetall(key)
                return {k: json.loads(v) for k, v in hash_data.items()} if hash_data else None
        except Exception as e:
            print(f"Redis hget error: {e}")
            return None
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter"""
        try:
            client = await self.get_client()
            return await client.incrby(key, amount)
        except Exception as e:
            print(f"Redis increment error: {e}")
            return None
    
    async def close(self):
        """Close Redis connection"""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None


# Dependency function
async def get_redis_service(settings: Settings = Depends(get_settings)) -> RedisService:
    """Dependency function to get Redis service"""
    return RedisService(settings) 