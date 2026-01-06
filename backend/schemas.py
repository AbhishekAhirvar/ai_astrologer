from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Union, Any

class NakshatraInfo(BaseModel):
    nakshatra: str
    lord: str
    pada: int
    symbol: Optional[str] = None
    element: Optional[str] = None

class PlanetPosition(BaseModel):
    name: str
    sign: str
    degree: float
    sign_num: int
    abs_pos: float
    karaka: Optional[str] = None
    house: Optional[int] = None
    rules_houses: Optional[str] = None
    relationship: Optional[str] = None
    nakshatra: Optional[NakshatraInfo] = None

    @validator('degree', 'abs_pos', pre=True)
    def round_floats(cls, v):
        return round(v, 2) if isinstance(v, float) else v

class ChartMetadata(BaseModel):
    name: str
    datetime: str
    location: str
    latitude: float
    longitude: float
    ayanamsa: float
    zodiac_system: str
    house_system: str
    gender: Optional[str] = None

    @validator('latitude', 'longitude', 'ayanamsa', pre=True)
    def round_floats(cls, v):
        return round(v, 2) if isinstance(v, float) else v

class VargaPlanet(BaseModel):
    """Simplified planet model for divisional charts"""
    name: str
    sign: str
    sign_num: int
    degree: float
    abs_pos: float

    @validator('degree', 'abs_pos', pre=True)
    def round_floats(cls, v):
        return round(v, 2) if isinstance(v, float) else v

class ChartResponse(BaseModel):
    """Complete chart response model"""
    # Main planets (Sun, Moon, etc.) mapped by key (sun, moon...)
    # We use a flexible dict because keys are dynamic (sun, moon, ascendant, rahu...)
    # But we can try to be specific if we want. For now, Dict is safer for existing code migration.
    planets: Dict[str, PlanetPosition] = Field(default_factory=dict)
    
    # Metadata
    metadata: ChartMetadata

    # Varga Charts
    vargas: Dict[str, Dict[str, VargaPlanet]] = Field(default_factory=dict)
    
    # Error field (legacy support)
    error: Optional[str] = None

    class Config:
        # Allow extra fields during transition if needed
        extra = "allow"
