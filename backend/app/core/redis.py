# backend/app/core/redis.py
"""
Redis connection manager for caching and session storage.
"""

import redis
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_redis() -> redis.Redis:
    """
    Get Redis connection instance.
    
    Returns:
        Redis client instance
    """
    try:
        # Parse Redis URL
        redis_url = settings.redis_url
        
        # Create Redis client
        client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            max_connections=10
        )
        
        # Test connection
        client.ping()
        
        return client
    
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        # Return dummy client for development
        if settings.environment == "development":
            logger.warning("Using dummy Redis for development")
            return redis.Redis(decode_responses=True)
        raise


# Redis client instance
redis_client = get_redis()
