"""
API Middleware
Includes logging, timing, and correlation ID tracking
"""
import time
import uuid
import json
from typing import Callable

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from backend.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for JSON logging requests and responses with timing, correlation IDs and size limits"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 1. Request Size Limit (1MB)
        content_length = request.headers.get("Content-Length")
        if content_length and int(content_length) > 1 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Request entity too large")

        # 2. Correlation ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        
        # 3. Log Request (Structured JSON)
        request_log = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": client_ip,
            "event": "request_received"
        }
        logger.info(json.dumps(request_log))
        
        try:
            response = await call_next(request)
            
            process_time_ms = (time.time() - start_time) * 1000
            response.headers["X-Process-Time"] = f"{process_time_ms:.2f}ms"
            response.headers["X-Request-ID"] = request_id
            
            # 4. Log Response (Structured JSON)
            response_log = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(process_time_ms, 2),
                "event": "response_sent"
            }
            logger.info(json.dumps(response_log))
            
            return response
            
        except Exception as e:
            process_time_ms = (time.time() - start_time) * 1000
            error_log = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
                "duration_ms": round(process_time_ms, 2),
                "event": "request_failed"
            }
            logger.error(json.dumps(error_log))
            raise e
