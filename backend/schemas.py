from pydantic import BaseModel, Field, field_validator, ConfigDict
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
    speed: float = 0.0 # Daily motion in degrees (New for Chesta Bala)
    declination: float = 0.0 # Declination in degrees (New for Ayana Bala)
    is_retrograde: bool = False
    karaka: Optional[str] = None
    house: Optional[int] = None
    rules_houses: Optional[str] = None
    relationship: Optional[str] = None
    nakshatra: Optional[NakshatraInfo] = None

    @field_validator('degree', 'abs_pos', mode='before')
    @classmethod
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

    @field_validator('latitude', 'longitude', 'ayanamsa', mode='before')
    @classmethod
    def round_floats(cls, v):
        return round(v, 2) if isinstance(v, float) else v

class VargaPlanet(BaseModel):
    """Simplified planet model for divisional charts"""
    name: str
    sign: str
    sign_num: int
    degree: float
    abs_pos: float

    @field_validator('degree', 'abs_pos', mode='before')
    @classmethod
    def round_floats(cls, v):
        return round(v, 2) if isinstance(v, float) else v

class KPCuspInfo(BaseModel):
    """KP house cusp information"""
    cusp_degree: float
    sign: str
    sign_num: int
    degree_in_sign: float
    star_lord: str
    sub_lord: str

    @field_validator('cusp_degree', 'degree_in_sign', mode='before')
    @classmethod
    def round_floats(cls, v):
        return round(v, 4) if isinstance(v, float) else v

class KPPlanetInfo(BaseModel):
    """KP Planet information (Sub Lord, etc)"""
    star_lord: str
    sub_lord: str
    longitude: float

class ShadbalaData(BaseModel):
    """Shadbala (Planetary Strength) Data"""
    total_shadbala: Dict[str, float]
    # We can add detail breakdown fields later if needed

class DashaInfo(BaseModel):
    """Vimshottari Dasha information"""
    maha_dasha: Dict[str, Any]
    antar_dasha: Dict[str, Any]
    birth_dasha: Dict[str, Any]

class KPData(BaseModel):
    """Complete KP astrology data"""
    cusps: Dict[int, KPCuspInfo]
    planets: Optional[Dict[str, KPPlanetInfo]] = None
    dasha: DashaInfo
    house_system: str = "Placidus"

class DashaPeriod(BaseModel):
    lord: str
    level: int  # 1=Maha, 2=Antar, 3=Pratyantar...
    start_jd: float
    end_jd: float
    duration_days: float = 0.0
    duration_years: float = 0.0
    sub_periods: List['DashaPeriod'] = []
    is_current: bool = False
    
class CurrentDashaState(BaseModel):
    maha_dasha: DashaPeriod
    antar_dasha: DashaPeriod
    pratyantar_dasha: DashaPeriod
    sookshma_dasha: Optional[DashaPeriod] = None
    prana_dasha: Optional[DashaPeriod] = None

class CompleteDashaInfo(BaseModel):
    current_state: CurrentDashaState
    timeline: List[DashaPeriod]

class HouseData(BaseModel):
    sign: str
    sign_num: int
    degree: float
    degree_in_sign: float
    cusp_degree: float

    @field_validator('degree', 'degree_in_sign', 'cusp_degree', mode='before')
    @classmethod
    def round_floats(cls, v):
        return round(v, 2) if isinstance(v, float) else v

class ChartResponse(BaseModel):
    metadata: ChartMetadata
    planets: Dict[str, PlanetPosition]
    houses: Dict[int, HouseData] = Field(default_factory=dict)
    ascendant: Optional[float] = None # Deprecated? Using planets['Ascendant']
    ayanamsa: float = 0.0 # Deprecated? In metadata
    kp_data: Optional[KPData] = None
    shadbala: Optional[ShadbalaData] = None
    complete_dasha: Optional[CompleteDashaInfo] = None # NEW
    vargas: Dict[str, Dict[str, VargaPlanet]] = Field(default_factory=dict)
    
    # Error field (legacy support)
    error: Optional[str] = None
    
    model_config = ConfigDict(extra="allow")
