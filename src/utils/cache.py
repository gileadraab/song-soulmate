import hashlib
import json
import logging
import os
from functools import wraps
from typing import Any, Optional

import redis

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Unified caching manager that supports both Redis and in-memory fallback.
    Provides automatic serialization/deserialization and cache key generation.
    """

    def __init__(self):
        self.redis_client = None
        self.memory_cache = {}
        self.use_redis = False
        self._initialize_cache()

    def _initialize_cache(self):
        """Initialize Redis connection with fallback to memory cache."""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )

            # Test connection
            self.redis_client.ping()
            self.use_redis = True
            logger.info("Redis cache initialized successfully")

        except Exception as e:
            logger.warning(f"Redis not available, falling back to memory cache: {e}")
            self.use_redis = False
            self.memory_cache = {}

    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a consistent cache key from function arguments."""
        # Create a string representation of all arguments
        key_data = {"args": args, "kwargs": sorted(kwargs.items()) if kwargs else {}}

        # Create hash of the arguments for consistent key generation
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:16]

        return f"{prefix}:{key_hash}"

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            if self.use_redis and self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            else:
                return self.memory_cache.get(key)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
        return None

    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in cache with expiration."""
        try:
            if self.use_redis and self.redis_client:
                serialized_value = json.dumps(value, default=str)
                return self.redis_client.setex(key, expire, serialized_value)
            else:
                # Simple memory cache without expiration (for fallback)
                self.memory_cache[key] = value
                return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
        return False

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            if self.use_redis and self.redis_client:
                return bool(self.redis_client.delete(key))
            else:
                return bool(self.memory_cache.pop(key, None))
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
        return False

    def clear(self) -> bool:
        """Clear all cache."""
        try:
            if self.use_redis and self.redis_client:
                return self.redis_client.flushdb()
            else:
                self.memory_cache.clear()
                return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
        return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            if self.use_redis and self.redis_client:
                return bool(self.redis_client.exists(key))
            else:
                return key in self.memory_cache
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
        return False

    def get_cache_info(self) -> dict:
        """Get cache statistics and info."""
        info = {
            "type": "redis" if self.use_redis else "memory",
            "status": "connected" if self.use_redis else "fallback",
        }

        try:
            if self.use_redis and self.redis_client:
                redis_info = self.redis_client.info()
                info.update(
                    {
                        "used_memory": redis_info.get("used_memory_human", "unknown"),
                        "connected_clients": redis_info.get("connected_clients", 0),
                        "total_commands_processed": redis_info.get(
                            "total_commands_processed", 0
                        ),
                    }
                )
            else:
                info.update(
                    {
                        "memory_keys": len(self.memory_cache),
                    }
                )
        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            info["error"] = str(e)

        return info


# Global cache manager instance
cache_manager = CacheManager()


def cached(expire: int = 3600, key_prefix: str = "cache"):
    """
    Decorator for caching function results.

    Args:
        expire: Cache expiration time in seconds (default: 1 hour)
        key_prefix: Prefix for cache keys

    Usage:
        @cached(expire=1800, key_prefix="spotify_api")
        def get_user_data(user_id, access_token):
            # Expensive API call
            return api_response
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_manager._generate_cache_key(
                key_prefix, func.__name__, *args, **kwargs
            )

            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result

            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}, executing function")
            result = func(*args, **kwargs)

            # Cache the result
            cache_manager.set(cache_key, result, expire)

            return result

        return wrapper

    return decorator


def cache_spotify_response(expire: int = 1800):
    """
    Specialized caching decorator for Spotify API responses.
    Default cache time: 30 minutes (1800 seconds)
    """
    return cached(expire=expire, key_prefix="spotify_api")


def cache_affinity_result(expire: int = 3600):
    """
    Specialized caching decorator for affinity calculations.
    Default cache time: 1 hour (3600 seconds)
    """
    return cached(expire=expire, key_prefix="affinity_calc")


def cache_user_stats(expire: int = 900):
    """
    Specialized caching decorator for user statistics.
    Default cache time: 15 minutes (900 seconds)
    """
    return cached(expire=expire, key_prefix="user_stats")


def invalidate_user_cache(user_id: str):
    """
    Invalidate all cache entries for a specific user.
    Useful when user data changes or tokens are refreshed.
    """
    try:
        # Pattern matching for user-specific cache keys
        if cache_manager.use_redis and cache_manager.redis_client:
            # Get all keys matching user pattern
            pattern = f"*{user_id}*"
            keys = cache_manager.redis_client.keys(pattern)
            if keys:
                cache_manager.redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries for user {user_id}")
        else:
            # For memory cache, remove keys containing user_id
            keys_to_remove = [
                key for key in cache_manager.memory_cache.keys() if user_id in key
            ]
            for key in keys_to_remove:
                cache_manager.memory_cache.pop(key, None)
            logger.info(
                f"Invalidated {len(keys_to_remove)} memory cache entries "
                f"for user {user_id}"
            )
    except Exception as e:
        logger.error(f"Error invalidating cache for user {user_id}: {e}")


def warm_cache():
    """
    Pre-warm cache with commonly accessed data.
    Can be called during application startup.
    """
    logger.info("Cache warming started")
    try:
        # Add any cache warming logic here
        # For example, pre-fetch common genre data, popular artists, etc.
        pass
    except Exception as e:
        logger.error(f"Cache warming failed: {e}")


# Health check function for cache
def cache_health_check() -> dict:
    """
    Perform health check on cache system.
    Returns status information.
    """
    health_status = {
        "cache_type": "redis" if cache_manager.use_redis else "memory",
        "status": "unknown",
        "latency_ms": None,
        "error": None,
    }

    try:
        import time

        start_time = time.time()

        # Test cache operations
        test_key = "health_check_test"
        test_value = {"timestamp": time.time(), "test": True}

        # Test set
        cache_manager.set(test_key, test_value, expire=60)

        # Test get
        retrieved_value = cache_manager.get(test_key)

        # Test delete
        cache_manager.delete(test_key)

        end_time = time.time()
        latency_ms = round((end_time - start_time) * 1000, 2)

        if retrieved_value and retrieved_value.get("test") is True:
            health_status.update({"status": "healthy", "latency_ms": latency_ms})
        else:
            health_status.update(
                {"status": "degraded", "error": "Cache read/write test failed"}
            )

    except Exception as e:
        health_status.update({"status": "unhealthy", "error": str(e)})

    return health_status
