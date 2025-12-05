"""
Utility functions for ETL pipeline
Rate limiting, error handling, and data processing
"""

import time
import logging
import random
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)


def exponential_backoff(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
):
    """
    Decorator for exponential backoff retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Add random jitter to prevent thundering herd
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        
                        if jitter:
                            delay = delay * (0.5 + random.random())
                        
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_retries} attempts failed for {func.__name__}: {e}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


class RateLimiter:
    """Simple rate limiter for API requests."""
    
    def __init__(self, requests_per_minute: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute
        """
        self.delay = 60.0 / requests_per_minute
        self.last_request = 0
    
    def wait(self):
        """Wait if necessary to respect rate limit."""
        elapsed = time.time() - self.last_request
        
        if elapsed < self.delay:
            sleep_time = self.delay - elapsed
            time.sleep(sleep_time)
        
        self.last_request = time.time()


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure logging for ETL pipeline.
    
    Args:
        level: Logging level
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def clean_cnpj(cnpj: str) -> str:
    """
    Clean and normalize CNPJ string.
    
    Args:
        cnpj: Raw CNPJ string
    
    Returns:
        Formatted CNPJ (XX.XXX.XXX/XXXX-XX)
    """
    import re
    
    # Remove all non-digits
    digits = re.sub(r'[^\d]', '', cnpj)
    
    if len(digits) != 14:
        return cnpj  # Return as-is if invalid
    
    # Format consistently
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"


def format_currency_brl(value: float) -> str:
    """
    Format value as Brazilian Real currency.
    
    Args:
        value: Numeric value
    
    Returns:
        Formatted string (R$ X.XXX,XX)
    """
    if value is None:
        return "R$ 0,00"
    
    # Brazilian format: dots for thousands, comma for decimals
    formatted = f"{value:,.2f}"
    # Swap dots and commas
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    
    return f"R$ {formatted}"


def parse_date(date_str: str, formats: list = None) -> Optional[str]:
    """
    Parse date string to ISO format.
    
    Args:
        date_str: Date string in various formats
        formats: List of format strings to try
    
    Returns:
        ISO formatted date (YYYY-MM-DD) or None
    """
    from datetime import datetime
    
    if formats is None:
        formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%fZ",
        ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            continue
    
    return None
