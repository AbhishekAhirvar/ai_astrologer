"""
FastAPI Application for Vedic Astrology AI
Clean modular architecture with v1 API routers
"""
import sys
from pathlib import Path

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).parent.absolute()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.logger import logger
from astro_api.v1.routers import chart as chart_router
from astro_api.v1.routers import ai as ai_router
from astro_api.v1.routers import health as health_router
from astro_api.v1.config import settings
from astro_api.v1.middleware import LoggingMiddleware


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="""
## Vedic Astrology AI API

REST API for generating Vedic birth charts and AI astrological predictions.

### Features
- **Birth Chart Generation**: Generate accurate Vedic birth charts with planetary positions
- **KP Astrology**: Krishnamurti Paddhati (KP) system support
- **AI Predictions**: Get AI-powered astrological predictions

### Endpoints
- `POST /api/v1/chart/generate` - Generate birth chart
- `POST /api/v1/ai/predict` - Get AI prediction
- `GET /api/v1/health` - Health check
    """,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Logging & Timing Middleware
app.add_middleware(LoggingMiddleware)

# Include v1 routers
app.include_router(health_router.router)
app.include_router(chart_router.router, prefix="/api/v1")
app.include_router(ai_router.router, prefix="/api/v1")


from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Specific handler for validation errors to return 422"""
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body})
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
