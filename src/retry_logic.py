"""
Retry logic for API failures - Bonus Feature
"""

import time
import functools
from src.logger import logger
import config


def retry_on_failure(max_retries=None, delay=None):
    """
    Decorator for retrying failed API calls with exponential backoff
    
    Usage:
        @retry_on_failure(max_retries=3, delay=2)
        def some_api_call():
            ...
    """
    if max_retries is None:
        max_retries = config.MAX_RETRIES if config.RETRY_ENABLED else 0
    if delay is None:
        delay = config.RETRY_DELAY
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        wait_time = delay * (2 ** (attempt - 1))  # Exponential backoff
                        logger.warning(f"Retry {attempt}/{max_retries} for {func.__name__} "
                                     f"(waiting {wait_time}s)...")
                        time.sleep(wait_time)
                    
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    error_msg = str(e)
                    
                    # Don't retry on certain errors
                    if any(msg in error_msg.lower() for msg in [
                        'authentication', 'unauthorized', 'forbidden', 
                        'invalid grant', 'token', 'permission'
                    ]):
                        logger.error(f"Authentication error in {func.__name__}: {error_msg[:100]}")
                        break
                    
                    # Don't retry on client errors (4xx)
                    if hasattr(e, 'resp') and hasattr(e.resp, 'status') and 400 <= e.resp.status < 500:
                        logger.error(f"Client error in {func.__name__} (HTTP {e.resp.status}): "
                                   f"{error_msg[:100]}")
                        break
                    
                    if attempt < max_retries:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: "
                                     f"{error_msg[:100]}")
                    else:
                        logger.error(f"Final attempt failed for {func.__name__}: "
                                   f"{error_msg[:100]}")
            
            # All retries failed
            if last_exception:
                logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
                raise last_exception
        
        return wrapper
    return decorator


class APIRetryHandler:
    """Handler for API operations with retry logic"""
    
    def __init__(self, max_retries=None, delay=None):
        self.max_retries = max_retries or config.MAX_RETRIES
        self.delay = delay or config.RETRY_DELAY
    
    def execute_with_retry(self, func, *args, **kwargs):
        """Execute function with retry logic"""
        return retry_on_failure(self.max_retries, self.delay)(func)(*args, **kwargs)
    
    def batch_execute_with_retry(self, func, items, batch_size=10):
        """Execute function on batch of items with retry logic"""
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            try:
                batch_results = self.execute_with_retry(func, batch)
                results.extend(batch_results)
                logger.debug(f"Processed batch {i//batch_size + 1}/{(len(items)-1)//batch_size + 1}")
            except Exception as e:
                logger.error(f"Failed to process batch starting at index {i}: {e}")
        return results