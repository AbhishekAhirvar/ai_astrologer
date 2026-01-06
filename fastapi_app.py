"""
FastAPI Application for Vedic Astrology AI
Provides REST API endpoints for chart generation and AI predictions
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse as APIResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import time
import os
from collections import defaultdict

from backend.location import get_location_data
from backend.astrology import generate_vedic_chart
from backend.ai import get_astrology_prediction
from backend.schemas import ChartResponse
from backend.logger import logger

# Initialize FastAPI app
app = FastAPI(
    title="Vedic Astrology AI API",
    description="REST API for generating Vedic birth charts and AI astrological predictions",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
user_requests = defaultdict(list)
MAX_REQUESTS_PER_MINUTE = 30

def check_rate_limit(identifier: str = "default") -> bool:
    """Check if request is within rate limit"""
    now = time.time()
    user_requests[identifier] = [t for t in user_requests[identifier] if now - t < 60]
    if len(user_requests[identifier]) >= MAX_REQUESTS_PER_MINUTE:
        return False
    user_requests[identifier].append(now)
    return True

# Request/Response Models
class ChartRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    gender: str = Field(..., pattern="^(Male|Female|Other)$")
    birth_date: str = Field(..., description="Format: YYYY-MM-DD")
    birth_time: str = Field(..., description="Format: HH:MM")
    birth_place: str = Field(..., min_length=1)
    
    @validator('birth_date')
    def validate_date(cls, v):
        try:
            dt = datetime.strptime(v, "%Y-%m-%d")
            if not (1800 <= dt.year <= 2100):
                raise ValueError("Year must be between 1800 and 2100")
            return v
        except ValueError as e:
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD. {str(e)}")
    
    @validator('birth_time')
    def validate_time(cls, v):
        try:
            parts = v.split(":")
            if len(parts) != 2:
                raise ValueError("Invalid format")
            hour, minute = int(parts[0]), int(parts[1])
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Invalid hour/minute range")
            return v
        except ValueError:
            raise ValueError("Invalid time format. Use HH:MM (e.g., 14:30)")

class PredictionRequest(BaseModel):
    chart_data: Dict[str, Any] = Field(..., description="Chart data from generate-chart endpoint")
    question: str = Field(..., min_length=1, max_length=500)
    is_kp_mode: bool = Field(default=False, description="Use KP astrology mode")

class PredictionResponse(BaseModel):
    answer: str
    suggestions: List[str] = Field(default_factory=list)

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

# Endpoints
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Vedic Astrology AI API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "generate_chart": "/api/generate-chart",
            "ai_predict": "/api/ai-predict"
        }
    }

@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/generate-chart", response_model=ChartResponse, tags=["Chart"])
async def generate_chart(request: ChartRequest, req: Request):
    """
    Generate Vedic birth chart
    
    - **name**: Person's name
    - **gender**: Male, Female, or Other
    - **birth_date**: Date in YYYY-MM-DD format
    - **birth_time**: Time in HH:MM format
    - **birth_place**: Location name (e.g., "New Delhi, India")
    """
    # Rate limiting
    client_ip = req.client.host if req.client else "unknown"
    if not check_rate_limit(client_ip):
        logger.warning(f"Rate limit exceeded for {client_ip}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please wait a minute.")
    
    logger.info(f"Chart generation request from {client_ip}: {request.name} at {request.birth_place}")
    
    try:
        # Parse date and time
        dt = datetime.strptime(request.birth_date, "%Y-%m-%d")
        time_parts = request.birth_time.split(":")
        hour, minute = int(time_parts[0]), int(time_parts[1])
        
        # Get location data
        loc_data = get_location_data(request.birth_place)
        if not loc_data:
            raise HTTPException(
                status_code=400,
                detail=f"Location '{request.birth_place}' not found. Please check the name."
            )
        
        lat, lon, address = loc_data
        logger.info(f"Location resolved: {address} ({lat}, {lon})")
        
        # Generate chart
        chart = generate_vedic_chart(
            request.name,
            dt.year, dt.month, dt.day,
            hour, minute,
            request.birth_place,
            lat, lon
        )
        
        # Check for errors
        if hasattr(chart, 'error') and chart.error:
            raise HTTPException(status_code=500, detail=chart.error)
        
        # Add gender to metadata
        if hasattr(chart, 'metadata'):
            chart.metadata.gender = request.gender
        
        logger.info(f"Chart generated successfully for {request.name}")
        return chart
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating chart: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating chart: {str(e)}")

@app.post("/api/ai-predict", response_model=PredictionResponse, tags=["AI"])
async def ai_predict(request: PredictionRequest, req: Request):
    """
    Get AI astrological prediction
    
    - **chart_data**: Chart data object from generate-chart endpoint
    - **question**: Astrological question to ask
    - **is_kp_mode**: Use Krishnamurti Paddhati (KP) astrology mode
    """
    # Rate limiting
    client_ip = req.client.host if req.client else "unknown"
    if not check_rate_limit(client_ip):
        logger.warning(f"Rate limit exceeded for {client_ip}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please wait a minute.")
    
    logger.info(f"AI prediction request from {client_ip}: {request.question[:50]}...")
    
    try:
        # Get API key from environment
        api_key = os.getenv("KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        # Get prediction
        response = get_astrology_prediction(
            request.chart_data,
            request.question,
            api_key=api_key,
            is_kp_mode=request.is_kp_mode
        )
        
        # Parse response for suggestions
        text = response
        suggestions = []
        
        if "[SUGGESTIONS]" in response:
            parts = response.split("[SUGGESTIONS]")
            text = parts[0].strip()
            # Split by || for robust separation
            sug_raw = parts[1].split("||")
            suggestions = [s.strip(" -.?*\"") for s in sug_raw if s.strip()][:3]
        
        return PredictionResponse(answer=text, suggestions=suggestions)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AI prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in AI prediction: {str(e)}")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return APIResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return APIResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
