# backend/app/core/rate_limiter.py
"""
Rate limiter for Telegram API requests.
Implements token bucket and leaky bucket algorithms for request throttling.
"""

import asyncio
import time
from collections import deque
from typing import Dict, Deque
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter for Telegram API requests using leaky bucket algorithm.
    Prevents flood wait errors by controlling request rate.
    """
    
    def __init__(self, max_requests: int = None, time_window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per time window (default from settings)
            time_window: Time window in seconds
        """
        self.max_requests = max_requests or settings.rate_limit_per_minute
        self.time_window = time_window
        
        # Request timestamps for each user
        self.requests: Dict[int, Deque[float]] = {}
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        
        logger.info(f"Rate limiter initialized: {self.max_requests} requests per {time_window} seconds")
    
    async def acquire(self, user_id: int) -> None:
        """
        Acquire permission to make a request.
        Blocks if rate limit is exceeded.
        
        Args:
            user_id: User identifier for rate limiting
        """
        async with self._lock:
            # Initialize request queue for user if not exists
            if user_id not in self.requests:
                self.requests[user_id] = deque()
            
            queue = self.requests[user_id]
            current_time = time.time()
            
            # Remove old requests outside time window
            while queue and queue[0] < current_time - self.time_window:
                queue.popleft()
            
            # Check if limit exceeded
            if len(queue) >= self.max_requests:
                # Calculate wait time
                oldest_request = queue[0]
                wait_time = (oldest_request + self.time_window) - current_time
                
                logger.warning(
                    f"Rate limit exceeded for user {user_id}. "
                    f"Waiting {wait_time:.2f} seconds"
                )
                
                # Release lock while waiting
                self._lock.release()
                await asyncio.sleep(wait_time)
                await self._lock.acquire()
                
                # Clean queue again after waiting
                while queue and queue[0] < time.time() - self.time_window:
                    queue.popleft()
            
            # Add current request timestamp
            queue.append(current_time)
            logger.debug(f"Request acquired for user {user_id}. Queue size: {len(queue)}")
    
    async def get_remaining_requests(self, user_id: int) -> int:
        """
        Get remaining requests for user in current time window.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of remaining requests
        """
        async with self._lock:
            if user_id not in self.requests:
                return self.max_requests
            
            queue = self.requests[user_id]
            current_time = time.time()
            
            # Clean old requests
            while queue and queue[0] < current_time - self.time_window:
                queue.popleft()
            
            remaining = self.max_requests - len(queue)
            return max(0, remaining)
    
    async def reset(self, user_id: int) -> None:
        """
        Reset rate limit for a user.
        
        Args:
            user_id: User identifier
        """
        async with self._lock:
            if user_id in self.requests:
                self.requests[user_id].clear()
                logger.info(f"Rate limit reset for user {user_id}")
    
    def get_max_requests(self) -> int:
        """
        Get maximum allowed requests per time window.
        
        Returns:
            Maximum requests
        """
        return self.max_requests


# Global rate limiter instance
rate_limiter = RateLimiter()
