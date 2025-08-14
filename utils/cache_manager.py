#utils/cache_manager.py

import redis
import json
import pickle
from typing import Optional, List, Dict, Any
from datetime import timedelta
from config import settings
from utils.logger import logger

class CacheManager:
    def __init__(self):
        try:
            # Only attempt connection if REDIS_URL is set
            if settings.REDIS_URL:
                self.redis_client = redis.from_url(settings.REDIS_URL)
                self.redis_client.ping()  # Test connection
                self.use_redis = True
                logger.info("Redis cache initialized successfully")
            else:
                logger.warning("REDIS_URL not set, caching disabled.")
                self.use_redis = False
        except Exception as e:
            logger.warning(f"Redis not available, caching disabled: {e}")
            self.use_redis = False
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set a value in cache"""
        if not self.use_redis:
            return False
        
        try:
            serialized_value = json.dumps(value, default=str)
            return self.redis_client.setex(key, ttl, serialized_value)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
  
    def get(self, key: str) -> Any | None:
        """Get a value from cache"""
        if not self.use_redis:
            return None
        
        try:
            cached = self.redis_client.get(key)
            return json.loads(cached) if cached else None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
       
# class CacheManager:
#     def __init__(self):
#         try:
#             self.redis_client = redis.from_url(settings.REDIS_URL)
#             self.redis_client.ping()  # Test connection
#             self.use_redis = True
#             logger.info("Redis cache initialized successfully")
#         except Exception as e:
#             logger.warning(f"Redis not available, caching disabled: {e}")
#             self.use_redis = False
    
#     def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
#         """Set a value in cache"""
#         if not self.use_redis:
#             return False
        
#         try:
#             serialized_value = json.dumps(value, default=str)
#             return self.redis_client.setex(key, ttl, serialized_value)
#         except Exception as e:
#             logger.error(f"Cache set error: {e}")
#             return False
    
#     def get(self, key: str) -> Optional[Any]:
#         """Get a value from cache"""
#         if not self.use_redis:
#             return None
        
#         try:
#             cached = self.redis_client.get(key)
#             return json.loads(cached) if cached else None
#         except Exception as e:
#             logger.error(f"Cache get error: {e}")
#             return None
    
    def delete(self, key: str) -> bool:
        """Delete a value from cache"""
        if not self.use_redis:
            return False
        
        try:
            return self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        if not self.use_redis:
            return 0
        
        try:
            keys = list(self.redis_client.scan_iter(match=pattern))
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache pattern invalidation error: {e}")
            return 0
    
    # Specific cache methods
    def cache_doctors_by_specialization(self, specialization: str, doctors: List[Dict], ttl: int = 3600):
        """Cache doctors list for a specialization"""
        key = f"doctors:spec:{specialization}"
        return self.set(key, doctors, ttl)
    
    def get_cached_doctors_by_specialization(self, specialization: str) -> Optional[List[Dict]]:
        """Get cached doctors for specialization"""
        key = f"doctors:spec:{specialization}"
        return self.get(key)
    
    def cache_available_slots(self, doctor_id: int, date: str, slots: List[str], ttl: int = 1800):
        """Cache available slots for a doctor on a date"""
        key = f"slots:{doctor_id}:{date}"
        return self.set(key, slots, ttl)
    
    def get_cached_available_slots(self, doctor_id: int, date: str) -> Optional[List[str]]:
        """Get cached available slots"""
        key = f"slots:{doctor_id}:{date}"
        return self.get(key)
    
    def invalidate_doctor_slots(self, doctor_id: int, date: str = None):
        """Invalidate slots cache for a doctor"""
        if date:
            pattern = f"slots:{doctor_id}:{date}"
            self.delete(pattern)
        else:
            pattern = f"slots:{doctor_id}:*"
            self.invalidate_pattern(pattern)

# Global instance
cache_manager = CacheManager()