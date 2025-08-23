import hashlib
import json
import logging
from typing import Dict, Optional, Any, Callable
from functools import wraps
from data.database import DatabaseManager
import time

class CacheManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.memory_cache = {}  # In-memory cache for frequently accessed data
        self.max_memory_cache_size = 1000
    
    def generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a unique cache key from function arguments"""
        # Create a string representation of all arguments
        key_data = {
            'prefix': prefix,
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        
        # Create hash of the key data
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def cache_api_call(self, expiry_hours: int = 24):
        """Decorator to cache API calls"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self.generate_cache_key(func.__name__, *args, **kwargs)
                
                # Try to get from memory cache first
                if cache_key in self.memory_cache:
                    logging.debug(f"Memory cache hit for {func.__name__}")
                    return self.memory_cache[cache_key]
                
                # Try to get from database cache
                cached_data = self.db.get_cached_response(cache_key)
                if cached_data is not None:
                    logging.debug(f"Database cache hit for {func.__name__}")
                    # Store in memory cache for faster access
                    self._store_in_memory_cache(cache_key, cached_data)
                    return cached_data
                
                # Cache miss - call the actual function
                logging.debug(f"Cache miss for {func.__name__}, calling API")
                result = func(*args, **kwargs)
                
                # Cache the result
                if result is not None:
                    self.db.cache_api_response(cache_key, result, expiry_hours)
                    self._store_in_memory_cache(cache_key, result)
                
                return result
            
            return wrapper
        return decorator
    
    def _store_in_memory_cache(self, key: str, data: Any):
        """Store data in memory cache with size limit"""
        if len(self.memory_cache) >= self.max_memory_cache_size:
            # Remove oldest entries (simple FIFO)
            oldest_key = next(iter(self.memory_cache))
            del self.memory_cache[oldest_key]
        
        self.memory_cache[key] = data
    
    def clear_memory_cache(self):
        """Clear in-memory cache"""
        self.memory_cache.clear()
        logging.info("Memory cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        # Memory cache stats
        memory_size = len(self.memory_cache)
        
        # Database cache stats (approximate)
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) as count FROM api_cache")
            db_cache_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM api_cache WHERE expires_at > datetime('now')")
            active_cache_count = cursor.fetchone()['count']
            
        except Exception as e:
            logging.error(f"Error getting cache stats: {e}")
            db_cache_count = 0
            active_cache_count = 0
        finally:
            conn.close()
        
        return {
            'memory_cache_size': memory_size,
            'database_cache_total': db_cache_count,
            'database_cache_active': active_cache_count
        }
    
    def cleanup_expired_cache(self):
        """Clean up expired cache entries"""
        self.db.clean_expired_cache()
        
        # Also clean up memory cache of old entries
        # (In a real implementation, you might want to track timestamps)
        if len(self.memory_cache) > self.max_memory_cache_size * 0.8:
            # Remove 20% of entries
            keys_to_remove = list(self.memory_cache.keys())[:int(len(self.memory_cache) * 0.2)]
            for key in keys_to_remove:
                del self.memory_cache[key]