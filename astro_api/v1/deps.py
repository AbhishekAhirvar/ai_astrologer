"""
Dependency Injection for FastAPI endpoints
Provides reusable dependencies for settings, validation, etc.
"""
import time
from collections import defaultdict
from typing import Dict, List, Generator

from fastapi import Depends, HTTPException, Request

from astro_api.v1.config import Settings, get_settings


def get_api_key(
    request: Request,
    settings: Settings = Depends(get_settings)
) -> str:
    """
    Dependency to get and validate API key.
    Returns the OpenAI API key or raises HTTPException if not configured.
    """
    api_key = settings.openai_api_key
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="AI service not configured. Please set the KEY environment variable."
        )
    return api_key


def get_client_ip(request: Request) -> str:
    """Extract client IP from request for rate limiting"""
    if request.client:
        return request.client.host
    return "unknown"


# Rate Limiter State (In-memory for now, could be moved to Redis)
_request_history: Dict[str, List[float]] = defaultdict(list)

def check_rate_limit(
    request: Request,
    settings: Settings = Depends(get_settings)
) -> None:
    """
    Dependency to enforce rate limits using a sliding window.
    Raises 429 Too Many Requests if limit exceeded.
    """
    client_ip = get_client_ip(request)
    now = time.time()
    
    # 1. Clean up old requests outside the 1 minute window
    window_start = now - 60
    _request_history[client_ip] = [t for t in _request_history[client_ip] if t > window_start]
    
    # 2. Check if limit exceeded
    if len(_request_history[client_ip]) >= settings.max_requests_per_minute:
        from backend.logger import logger
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait a minute."
        )
    
    # 3. Record this request
    _request_history[client_ip].append(now)
