"""
src/utils/rate_limiter.py - API rate limiting
"""

import time
from collections import defaultdict
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class RateLimiter:
    """Simple rate limiter"""
    
    def __init__(self):
        self.calls = defaultdict(list)
    
    def check(self, key, max_calls, window_seconds):
        """
        Check if call is allowed
        
        Returns True if allowed, False if rate limited
        """
        now = time.time()
        
        # Clean old calls
        self.calls[key] = [t for t in self.calls[key] 
                          if now - t < window_seconds]
        
        if len(self.calls[key]) >= max_calls:
            logger.warning(f"Rate limit hit for {key}")
            return False
        
        self.calls[key].append(now)
        return True
    
    def wait_if_needed(self, key, max_calls, window_seconds):
        """Wait until call is allowed"""
        while not self.check(key, max_calls, window_seconds):
            time.sleep(1)


# Global rate limiters for different APIs
rate_limiters = {
    'gemini': RateLimiter(),
    'pexels': RateLimiter(),
    'pixabay': RateLimiter(),
    'youtube': RateLimiter(),
    'trends': RateLimiter()
}


def check_rate_limit(api_name, max_calls, window_seconds):
    """Check rate limit for an API"""
    if api_name not in rate_limiters:
        rate_limiters[api_name] = RateLimiter()
    
    return rate_limiters[api_name].check(api_name, max_calls, window_seconds)


def wait_for_rate_limit(api_name, max_calls, window_seconds):
    """Wait for rate limit"""
    if api_name not in rate_limiters:
        rate_limiters[api_name] = RateLimiter()
    
    rate_limiters[api_name].wait_if_needed(api_name, max_calls, window_seconds)
