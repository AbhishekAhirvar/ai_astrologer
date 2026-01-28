"""
Health Check Router
Provides health and status endpoints
"""
from datetime import datetime

from fastapi import APIRouter, Depends

from astro_api.v1.config import Settings, get_settings


router = APIRouter(tags=["Health"])


@router.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Vedic Astrology AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/api/v1/health",
            "generate_chart": "/api/v1/chart/generate",
            "ai_predict": "/api/v1/ai/predict"
        }
    }


@router.get("/api/v1/health")
async def health_check(settings: Settings = Depends(get_settings)):
    """Health check endpoint with timestamp and dependency status"""
    # Check dependencies
    ai_status = "configured" if settings.openai_api_key else "not_configured"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.app_version,
        "dependencies": {
            "ai_service": ai_status
        }
    }
