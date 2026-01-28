"""
AI Prediction Router
Handles AI astrological prediction endpoints
"""
from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.ai import get_astrology_prediction
from backend.logger import logger
from astro_api.v1.deps import get_api_key, get_client_ip, check_rate_limit


router = APIRouter(prefix="/ai", tags=["AI"])


class PredictionRequest(BaseModel):
    """Request model for AI predictions"""
    chart_data: Dict[str, Any] = Field(..., description="Chart data from generate-chart endpoint")
    question: str = Field(..., min_length=1, max_length=500)
    is_kp_mode: bool = Field(default=False, description="Use KP astrology mode")


class PredictionResponse(BaseModel):
    """Response model for AI predictions"""
    answer: str
    suggestions: List[str] = Field(default_factory=list)


@router.post("/predict", response_model=PredictionResponse, dependencies=[Depends(check_rate_limit)])
async def ai_predict(
    request: PredictionRequest,
    api_key: str = Depends(get_api_key),
    client_ip: str = Depends(get_client_ip)
) -> PredictionResponse:
    """
    Get AI astrological prediction
    
    - **chart_data**: Chart data object from generate-chart endpoint
    - **question**: Astrological question to ask
    - **is_kp_mode**: Use Krishnamurti Paddhati (KP) astrology mode
    """
    logger.info(f"AI prediction request from {client_ip}: {request.question[:50]}...")
    
    try:
        # Get prediction
        response = get_astrology_prediction(
            request.chart_data,
            request.question,
            api_key=api_key,
            is_kp_mode=request.is_kp_mode
        )
        
        # Parse response for suggestions
        text = response
        suggestions: List[str] = []
        
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
