#utils/rate_limiter.py

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List
from utils.exceptions import RateLimitExceededError
from utils.logger import logger
import redis
from config import settings

class RateLimiter:
    def __init__(self):
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL)
            self.use_redis = True
        except:
            # Fallback to in-memory if Redis is not available
            self.requests: Dict[str, List[datetime]] = defaultdict(list)
            self.use_redis = False
            logger.warning("Redis not available, using in-memory rate limiting")
    
    def is_allowed(self, identifier: str, max_requests: int = 10, 
                   time_window: int = 60) -> bool:
        """Check if request is within rate limits"""
        
        if self.use_redis:
            return self._check_redis_limit(identifier, max_requests, time_window)
        else:
            return self._check_memory_limit(identifier, max_requests, time_window)
    
    def _check_redis_limit(self, identifier: str, max_requests: int, time_window: int) -> bool:
        """Redis-based rate limiting"""
        try:
            pipe = self.redis_client.pipeline()
            key = f"rate_limit:{identifier}"
            
            # Remove expired entries
            cutoff = datetime.now().timestamp() - time_window
            pipe.zremrangebyscore(key, 0, cutoff)
            
            # Count current requests
            pipe.zcard(key)
            
            # Add current request
            current_time = datetime.now().timestamp()
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiry
            pipe.expire(key, time_window)
            
            results = pipe.execute()
            current_count = results[1]
            
            return current_count < max_requests
        except Exception as e:
            logger.error(f"Redis rate limiting error: {e}")
            return True  # Allow request if Redis fails
    
    def _check_memory_limit(self, identifier: str, max_requests: int, time_window: int) -> bool:
        """In-memory rate limiting"""
        now = datetime.now()
        window_start = now - timedelta(seconds=time_window)
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        # Check if under limit
        if len(self.requests[identifier]) < max_requests:
            self.requests[identifier].append(now)
            return True
        
        return False
    
    def get_remaining_time(self, identifier: str, time_window: int = 60) -> int:
        """Get remaining time until rate limit resets"""
        if not self.use_redis:
            if identifier in self.requests and self.requests[identifier]:
                oldest_request = min(self.requests[identifier])
                reset_time = oldest_request + timedelta(seconds=time_window)
                remaining = (reset_time - datetime.now()).total_seconds()
                return max(0, int(remaining))
        return 0

# Global instance
rate_limiter = RateLimiter()