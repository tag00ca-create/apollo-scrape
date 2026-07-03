"""
Utility functions for Apollo scraper Apify Actor.
"""

import time
import random
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from functools import wraps


def random_delay(min_seconds: int = 3, max_seconds: int = 7) -> float:
    """Sleep for a random duration to mimic human behavior"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)
    return delay


def retry_on_failure(max_retries: int = 3):
    """Decorator to retry function on failure with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    print(f"⚠️  Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2
                        print(f"⏳ Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
            raise last_exception
        return wrapper
    return decorator


def log_message(message: str, level: str = 'INFO'):
    """Simple logging with timestamps"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    prefix = {
        'INFO': 'ℹ️ ',
        'SUCCESS': '✅',
        'WARNING': '⚠️ ',
        'ERROR': '❌',
        'DEBUG': '🔍'
    }.get(level, 'ℹ️ ')
    
    print(f"[{timestamp}] {prefix} {message}")


def clean_text(text: str) -> str:
    """Clean extracted text"""
    if not text:
        return ''
    text = ' '.join(text.split())
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    return text.strip()


def is_valid_url(url: str) -> bool:
    """Check if URL is valid Apollo.io URL"""
    return url.startswith('https://app.apollo.io') or url.startswith('http://app.apollo.io')
