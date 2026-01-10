"""
KP (Krishnamurti Paddhati) Astrology Calculations - Expert Edition
Implements house cusps (Placidus), robust sub-lords, and Dasha calculations
"""

import swisseph as swe
from typing import Dict, List, Tuple, Optional, Any
from functools import lru_cache
from backend.logger import logger
from backend.config import DEFAULT_AYANAMSA, KP_AYANAMSA

# ============================================================================
# CONSTANTS
# ============================================================================

DASHA_PERIODS = {
    'Ketu': 7,
    'Venus': 20,
    'Sun': 6,
    'Moon': 10,
    'Mars': 7,
    'Rahu': 18,
    'Jupiter': 16,
    'Saturn': 19,
    'Mercury': 17
}

TOTAL_DASHA_YEARS = 120
NAKSHATRA_COUNT = 27
DEGREES_PER_ZODIAC = 360
NAKSHATRA_SPAN_DEGREES = DEGREES_PER_ZODIAC / NAKSHATRA_COUNT  # 13.333...°
DAYS_PER_YEAR = 365.25

PLANET_SEQUENCE = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']

NAKSHATRA_LORDS = [
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury'
] * 3

ZODIAC_SIGNS = [
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]

# ============================================================================
# VALIDATION & HELPERS
# ============================================================================

def validate_astro_inputs(jd: float, lat: Optional[float] = None, lon: Optional[float] = None) -> None:
    """Rigorous check for astronomical input ranges."""
    if jd <= 0:
        raise ValueError(f"Invalid Julian Day: {jd}")
    if lat is not None and not (-90 <= lat <= 90):
        raise ValueError(f"Latitude must be in range [-90, 90]: {lat}")
    if lon is not None and not (-180 <= lon <= 180):
        raise ValueError(f"Longitude must be in range [-180, 180]: {lon}")


def normalize_longitude(longitude: float) -> float:
    """Strictly normalize longitude into [0, 360) range."""
    # Handle floating point precision edge cases like 360.0000000000001 or -1e-14
    lon = longitude % DEGREES_PER_ZODIAC
    if lon < 1e-12 or abs(lon - DEGREES_PER_ZODIAC) < 1e-12:
        return 0.0
    return lon


def get_nakshatra_info(longitude: float) -> Tuple[int, str, float]:
    """Get nakshatra number, lord, and position within the nakshatra."""
    lon = normalize_longitude(longitude)
    nak_num = int(lon / NAKSHATRA_SPAN_DEGREES) % NAKSHATRA_COUNT
    degree_in_nak = lon % NAKSHATRA_SPAN_DEGREES
    return nak_num, NAKSHATRA_LORDS[nak_num], degree_in_nak


# ============================================================================
# KP CORE CALCULATIONS
# ============================================================================

@lru_cache(maxsize=256)
def calculate_placidus_cusps(jd: float, lat: float, lon: float) -> Dict[int, Dict[str, Any]]:
    """Calculate 12 house cusps using Placidus system with KP Ayanamsa."""
    validate_astro_inputs(jd, lat, lon)
    
    try:
        # Enforce KP Ayanamsa
        swe.set_sid_mode(KP_AYANAMSA)
        
        # houses() returns (cusps, ascmc)
        houses_tropical, _ = swe.houses(jd, lat, lon, b'P')
        
        ayanamsa = swe.get_ayanamsa_ut(jd)
        cusps = {}
        
        for i in range(12):
            sidereal_cusp = normalize_longitude(houses_tropical[i] - ayanamsa)
            sign_num = int(sidereal_cusp / 30) % 12
            
            cusps[i + 1] = {
                'cusp_degree': round(sidereal_cusp, 4),
                'sign': ZODIAC_SIGNS[sign_num],
                'sign_num': sign_num,
                'degree_in_sign': round(sidereal_cusp % 30, 4)
            }
        
        return cusps
    except Exception as e:
        logger.error(f"SwissEph error in Placidus calculation: {e}")
        raise RuntimeError(f"Failed to calculate house cusps: {e}")


@lru_cache(maxsize=512)
def calculate_sub_lord(longitude: float) -> str:
    """
    Calculate sub-lord for a given degree using robust fraction-based logic.
    Prevents floating-point drift accumulation.
    """
    _, star_lord, degree_in_nak = get_nakshatra_info(longitude)
    
    # Calculate fraction of Nakshatra traversed (0.0 to 1.0)
    fraction_traversed = degree_in_nak / NAKSHATRA_SPAN_DEGREES
    
    # Map fraction to "Projected Years" in the 120-year cycle
    projected_years = fraction_traversed * TOTAL_DASHA_YEARS
    
    start_index = PLANET_SEQUENCE.index(star_lord)
    cumulative_years = 0.0
    
    for i in range(9):
        lord = PLANET_SEQUENCE[(start_index + i) % 9]
        period = DASHA_PERIODS[lord]
        
        if projected_years < (cumulative_years + period + 1e-12): # Include epsilon for safety
            return lord
        cumulative_years += period
    
    return PLANET_SEQUENCE[(start_index + 8) % 9]


def calculate_vimshottari_dasha(moon_lon: float, birth_jd: float, current_jd: Optional[float] = None) -> Dict[str, Any]:
    """
    Calculate Vimshottari Maha Dasha and Antar Dasha periods with end dates.
    """
    if current_jd is None:
        current_jd = birth_jd
    
    validate_astro_inputs(birth_jd)
    validate_astro_inputs(current_jd)
    
    _, star_lord, degree_in_nak = get_nakshatra_info(moon_lon)
    
    prop_remaining = 1.0 - (degree_in_nak / NAKSHATRA_SPAN_DEGREES)
    elapsed_days = max(0.0, current_jd - birth_jd)
    total_cycle_days = TOTAL_DASHA_YEARS * DAYS_PER_YEAR
    
    effective_elapsed = elapsed_days % total_cycle_days
    
    start_index = PLANET_SEQUENCE.index(star_lord)
    birth_maha_total_days = DASHA_PERIODS[star_lord] * DAYS_PER_YEAR
    birth_maha_rem_days = birth_maha_total_days * prop_remaining
    
    # 1. Find Current Maha Dasha
    current_days = effective_elapsed
    current_maha = None
    maha_rem_days = 0.0
    maha_elapsed_in_period = 0.0
    
    if current_days < birth_maha_rem_days:
        current_maha = star_lord
        maha_rem_days = birth_maha_rem_days - current_days
        maha_elapsed_in_period = birth_maha_total_days - maha_rem_days
    else:
        current_days -= birth_maha_rem_days
        for i in range(1, 10):
            idx = (start_index + i) % 9
            lord = PLANET_SEQUENCE[idx]
            period_days = DASHA_PERIODS[lord] * DAYS_PER_YEAR
            
            if current_days < period_days:
                current_maha = lord
                maha_rem_days = period_days - current_days
                maha_elapsed_in_period = current_days
                break
            current_days -= period_days
            
    if not current_maha:
        current_maha = star_lord
        maha_rem_days = 0.0
        maha_elapsed_in_period = 0.0

    # 2. Find Current Antar Dasha
    antar_start_idx = PLANET_SEQUENCE.index(current_maha)
    total_maha_years = DASHA_PERIODS[current_maha]
    
    current_antar = None
    antar_days_accum = 0.0
    antar_rem_days = 0.0
    
    for i in range(9):
        a_lord = PLANET_SEQUENCE[(antar_start_idx + i) % 9]
        a_span_days = (total_maha_years * DASHA_PERIODS[a_lord] / TOTAL_DASHA_YEARS) * DAYS_PER_YEAR
        
        if maha_elapsed_in_period < antar_days_accum + a_span_days:
            current_antar = a_lord
            antar_rem_days = (antar_days_accum + a_span_days) - maha_elapsed_in_period
            break
        antar_days_accum += a_span_days
    
    return {
        'maha_dasha': {
            'lord': current_maha,
            'balance_years': round(maha_rem_days / DAYS_PER_YEAR, 3),
            'end_date_jd': round(current_jd + maha_rem_days, 4),
            'total_years': total_maha_years
        },
        'antar_dasha': {
            'lord': current_antar or current_maha,
            'balance_years': round(antar_rem_days / DAYS_PER_YEAR, 3),
            'end_date_jd': round(current_jd + antar_rem_days, 4)
        },
        'birth_dasha': {
            'lord': star_lord,
            'balance_years': round(birth_maha_rem_days / DAYS_PER_YEAR, 3)
        }
    }


def generate_kp_data(jd: float, lat: float, lon: float, 
                     planetary_positions: Dict[str, Dict[str, float]],
                     moon_lon: float) -> Dict[str, Any]:
    """Generate complete KP data with expert refinements."""
    try:
        # Ensure KP Ayanamsa is set before any planetary position dependent calculation
        swe.set_sid_mode(KP_AYANAMSA)
        
        cusps = calculate_placidus_cusps(jd, lat, lon)
        
        for h_num, data in cusps.items():
            deg = data['cusp_degree']
            _, star_lord, _ = get_nakshatra_info(deg)
            data['star_lord'] = star_lord
            data['sub_lord'] = calculate_sub_lord(deg)
            
        # Calculate Planetary Sub-lords
        planets_kp = {}
        for p_name, p_data in planetary_positions.items():
            norm_name = p_name.capitalize()
            # Handle 'Ascendant' separately if needed, or map 'rahu'/'true_node'?
            # PLANET_SEQUENCE has 'Rahu', 'Ketu'.
            # PLANET_IDS has 'rahu'.
            
            if norm_name == 'Ascendant' or norm_name in ['Ketu', 'Rahu'] or norm_name in PLANET_SEQUENCE:
                deg = p_data['longitude']
                _, star_lord, _ = get_nakshatra_info(deg)
                
                # Use original p_name as key to match ChartResponse keys (lowercase usually)
                planets_kp[p_name] = {
                    'star_lord': star_lord,
                    'sub_lord': calculate_sub_lord(deg),
                    'longitude': round(deg, 4)
                }

        dasha = calculate_vimshottari_dasha(moon_lon, jd)
        
        return {
            'cusps': cusps,
            'planets': planets_kp,
            'dasha': dasha,
            'house_system': 'Placidus',
            'ayanamsa_name': 'KP (Krishnamurti)'
        }
    except Exception as e:
        logger.error(f"KP Data generation failed: {e}")
        raise
