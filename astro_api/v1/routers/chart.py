"""
Chart Generation Router
Handles birth chart generation endpoints
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from backend.location import get_location_data
from backend.astrology import generate_vedic_chart
from backend.schemas import ChartResponse
from backend.logger import logger
from astro_api.v1.deps import get_client_ip, check_rate_limit


router = APIRouter(prefix="/chart", tags=["Chart"])


class ChartRequest(BaseModel):
    """Request model for chart generation"""
    name: str = Field(..., min_length=1, max_length=100)
    gender: str = Field(..., pattern="^(Male|Female|Other)$")
    birth_date: str = Field(..., description="Format: YYYY-MM-DD")
    birth_time: str = Field(..., description="Format: HH:MM")
    birth_place: str = Field(..., min_length=1)
    
    @field_validator('birth_date', mode='before')
    @classmethod
    def validate_date(cls, v: str) -> str:
        try:
            dt = datetime.strptime(v, "%Y-%m-%d")
            if not (1800 <= dt.year <= 2100):
                raise ValueError("Year must be between 1800 and 2100")
            return v
        except ValueError as e:
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD. {str(e)}")
    
    @field_validator('birth_time', mode='before')
    @classmethod
    def validate_time(cls, v: str) -> str:
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


@router.post("/generate", response_model=ChartResponse, dependencies=[Depends(check_rate_limit)])
async def generate_chart(
    request: ChartRequest,
    client_ip: str = Depends(get_client_ip)
) -> ChartResponse:
    """
    Generate Vedic birth chart
    
    - **name**: Person's name
    - **gender**: Male, Female, or Other
    - **birth_date**: Date in YYYY-MM-DD format
    - **birth_time**: Time in HH:MM format
    - **birth_place**: Location name (e.g., "New Delhi, India")
    """
    logger.info(f"Chart generation request from {client_ip}: {request.name} at {request.birth_place}")
    
    try:
        # Parse date and time
        dt = datetime.strptime(request.birth_date, "%Y-%m-%d")
        time_parts = request.birth_time.split(":")
        hour, minute = int(time_parts[0]), int(time_parts[1])
        
        # Get location data
        loc_data = await get_location_data(request.birth_place)
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
