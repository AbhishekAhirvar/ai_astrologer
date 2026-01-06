"""
Vedic Astrology Chart Generator
Uses Swiss Ephemeris with Lahiri Ayanamsa
Implements proper Vedic calculation methods
"""

import swisseph as swe
from datetime import datetime
import pytz
from typing import Dict, Tuple, Optional, List, Union
from enum import Enum
from backend.nakshatra_data import get_nakshatra_by_longitude
from backend.varga_charts import calculate_all_vargas
from backend.logger import logger
from backend.schemas import (
    ChartResponse, PlanetPosition, ChartMetadata, 
    NakshatraInfo, VargaPlanet
)
from backend.config import (
    ZODIAC_SIGNS, SIGN_LORDS, NATURAL_RELATIONSHIPS, 
    KARAKA_LABELS, PLANET_IDS, DEFAULT_AYANAMSA
)
from backend.exceptions import (
    AstrologyError, InvalidDateError, InvalidLocationError, 
    EphemerisCalculationError
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def validate_input(year: int, month: int, day: int, 
                   hour: int, minute: int, lat: float, lon: float) -> None:
    """Validate date, time, and location inputs."""
    try:
        datetime(year, month, day, hour, minute)
    except ValueError as e:
        logger.error(f"Invalid date/time input: {year}-{month}-{day} {hour}:{minute} - {str(e)}")
        raise InvalidDateError(f"Invalid date/time: {str(e)}")

    if not (-90 <= lat <= 90):
        logger.error(f"Invalid latitude: {lat}")
        raise InvalidLocationError("Latitude must be between -90 and 90 degrees.")
    
    if not (-180 <= lon <= 180):
        logger.error(f"Invalid longitude: {lon}")
        raise InvalidLocationError("Longitude must be between -180 and 180 degrees.")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_zodiac_sign(longitude: float) -> Tuple[str, float, int]:
    """
    Convert ecliptic longitude to zodiac sign and degree.
    
    Args:
        longitude: Ecliptic longitude in degrees (0-360)
    
    Returns:
        Tuple of (sign_name, degree_in_sign, sign_number)
    """
    sign_num = int(longitude / 30) % 12
    degree = longitude % 30
    return ZODIAC_SIGNS[sign_num], degree, sign_num


def get_house_number(planet_sign_num: int, asc_sign_num: int) -> int:
    """
    Calculate house number using Whole Sign house system.
    
    Args:
        planet_sign_num: Sign number where planet is located (0-11)
        asc_sign_num: Sign number of ascendant (0-11)
    
    Returns:
        House number (1-12)
    """
    return ((planet_sign_num - asc_sign_num) % 12) + 1


def get_ordinal_suffix(n: int) -> str:
    """Get ordinal suffix for a number (1st, 2nd, 3rd, etc.)"""
    if 11 <= n % 100 <= 13:
        return f"{n}th"
    suffixes = {1: "st", 2: "nd", 3: "rd"}
    return f"{n}{suffixes.get(n % 10, 'th')}"


# ============================================================================
# CORE CHART GENERATION
# ============================================================================

def calculate_julian_day(year: int, month: int, day: int, 
                         hour: int, minute: int, timezone_str: str = "Asia/Kolkata") -> float:
    """
    Calculate Julian Day for given datetime (handles Timezones).
    
    Args:
        year, month, day, hour, minute: Date and time components
        timezone_str: Timezone string (e.g. "Asia/Kolkata", "UTC")
    
    Returns:
        Julian Day number
    """
    try:
        # Input validation implicit in datetime constructor
        try:
            tz = pytz.timezone(timezone_str)
        except pytz.UnknownTimeZoneError:
            logger.warning(f"Unknown timezone {timezone_str}, defaulting to Asia/Kolkata")
            tz = pytz.timezone('Asia/Kolkata')
            
        dt = tz.localize(datetime(year, month, day, hour, minute))
        dt_utc = dt.astimezone(pytz.UTC)
        
        logger.info(f"Calculating Julian Day for input {year}-{month}-{day} {hour}:{minute} {timezone_str} (UTC: {dt_utc})")
        
        jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, 
                         dt_utc.hour + dt_utc.minute / 60.0)
        return jd
    except Exception as e:
        logger.error(f"Failed to calculate Julian Day: {e}")
        raise EphemerisCalculationError(f"Julian Day calculation failed: {str(e)}")


def calculate_planetary_positions(jd: float) -> Dict:
    """
    Calculate sidereal positions of all planets.
    
    Args:
        jd: Julian Day number
    
    Returns:
        Dictionary with planet positions
        
    Raises:
        EphemerisCalculationError: If swisseph fails
    """
    try:
        swe.set_sid_mode(DEFAULT_AYANAMSA)
        chart_data = {}
        
        logger.info("Calculating planetary positions...")
        
        for planet_name, planet_id in PLANET_IDS.items():
            try:
                result = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL)
                longitude = result[0][0]
                
                sign, degree, sign_num = get_zodiac_sign(longitude)
                
                chart_data[planet_name] = {
                    'name': planet_name.capitalize(),
                    'sign': sign,
                    'degree': round(degree, 2),
                    'sign_num': sign_num,
                    'abs_pos': round(longitude, 2)
                }
            except swe.Error as e:
                logger.error(f"Error calculating {planet_name}: {e}")
                raise EphemerisCalculationError(f"Failed to calculate position for {planet_name}: {e}")
        
        # Calculate Ketu (180° opposite to Rahu)
        rahu_pos = chart_data['rahu']['abs_pos']
        ketu_pos = (rahu_pos + 180) % 360
        sign, degree, sign_num = get_zodiac_sign(ketu_pos)
        
        chart_data['ketu'] = {
            'name': 'Ketu',
            'sign': sign,
            'degree': round(degree, 2),
            'sign_num': sign_num,
            'abs_pos': round(ketu_pos, 2)
        }
        
        return chart_data
    except Exception as e:
        logger.critical(f"Critical error in planetary calculations: {e}")
        raise EphemerisCalculationError(f"Planetary calculation failed: {str(e)}")


def calculate_ascendant(jd: float, lat: float, lon: float) -> Dict:
    """
    Calculate sidereal ascendant (Lagna) using Whole Sign houses.
    
    Args:
        jd: Julian Day number
        lat: Latitude
        lon: Longitude
    
    Returns:
        Dictionary with ascendant data
    """
    try:
        swe.set_sid_mode(DEFAULT_AYANAMSA)
        
        # Get houses (we only need ascendant)
        # Handle potential error if lat/lon is invalid for swisseph
        houses = swe.houses(jd, lat, lon, b'P')
        asc_tropical = houses[0][0]
        
        # Convert to sidereal
        ayanamsa = swe.get_ayanamsa_ut(jd)
        asc_sidereal = (asc_tropical - ayanamsa) % 360
        
        sign, degree, sign_num = get_zodiac_sign(asc_sidereal)
        
        return {
            'name': 'Ascendant',
            'sign': sign,
            'degree': round(degree, 2),
            'sign_num': sign_num,
            'abs_pos': round(asc_sidereal, 2)
        }
    except Exception as e:
        logger.error(f"Error calculating Ascendant: {e}")
        raise EphemerisCalculationError(f"Ascendant calculation failed: {str(e)}")


# ============================================================================
# CHARA KARAKA CALCULATION (CORRECTED)
# ============================================================================

def calculate_chara_karakas(chart_data: Dict) -> Dict[str, str]:
    """
    Calculate Chara Karakas using degrees WITHIN signs (Jaimini system).
    Excludes Rahu and Ketu as per traditional method.
    
    Args:
        chart_data: Dictionary with planetary positions
    
    Returns:
        Dictionary mapping planet names to karaka labels
    """
    planets_to_rank = []
    
    # Only use seven planets (Sun to Saturn)
    for planet in ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn']:
        if planet in chart_data:
            degree_in_sign = chart_data[planet]['degree']
            planets_to_rank.append((planet, degree_in_sign))
    
    # Sort by degree within sign (descending)
    planets_to_rank.sort(key=lambda x: x[1], reverse=True)
    
    karaka_map = {}
    for i, (planet, _) in enumerate(planets_to_rank):
        if i < len(KARAKA_LABELS):
            karaka_map[planet] = KARAKA_LABELS[i]
    
    return karaka_map


# ============================================================================
# DIVISIONAL CHARTS (CORRECTED)
# ============================================================================

# Divisional chart functions moved to backend/varga_charts.py


# ============================================================================
# HOUSE LORDS & RELATIONSHIPS
# ============================================================================

def get_house_lords_ruled(planet_name: str, asc_sign_num: int) -> str:
    """
    Get houses ruled by a planet.
    
    Args:
        planet_name: Name of the planet
        asc_sign_num: Ascendant sign number
    
    Returns:
        Formatted string of house numbers (e.g., "1st, 8th")
    """
    planet_cap = planet_name.capitalize()
    houses_ruled = []
    
    for house in range(1, 13):
        house_sign = (asc_sign_num + house - 1) % 12
        lord = SIGN_LORDS.get(house_sign)
        if lord == planet_cap:
            houses_ruled.append(get_ordinal_suffix(house))
    
    return ", ".join(houses_ruled) if houses_ruled else "-"


def calculate_compound_relationship(planet_name: str, sign_num: int, 
                                   chart_data: Dict) -> str:
    """
    Calculate compound relationship (natural + temporal).
    
    Args:
        planet_name: Name of the planet
        sign_num: Sign number where planet is located
        chart_data: Full chart data
    
    Returns:
        Relationship status string
    """
    planet_cap = planet_name.capitalize()
    
    if planet_cap == 'Ascendant':
        return "-"
    
    # Get sign lord
    sign_lord = SIGN_LORDS.get(sign_num)
    if not sign_lord:
        return "Neutral"
    
    # Check for Own Sign
    if planet_cap == sign_lord:
        return "Own Sign"
    
    # Natural relationship
    rel_map = NATURAL_RELATIONSHIPS.get(planet_cap, {})
    natural_score = rel_map.get(sign_lord, 0)
    
    # Temporal relationship (simplified)
    # Based on house position from sign lord's position
    lord_sign = -1
    for p, data in chart_data.items():
        if p.capitalize() == sign_lord:
            lord_sign = data.get('sign_num', -1)
            break
    
    if lord_sign == -1:
        return "Neutral"
    
    # Houses 2, 3, 4, 10, 11, 12 from a planet are friendly
    house_diff = (sign_num - lord_sign) % 12
    temporal_score = 1 if house_diff in [1, 2, 3, 9, 10, 11] else -1
    
    # Compound score
    total = natural_score + temporal_score
    
    if total >= 2:
        return "Great Friend"
    elif total == 1:
        return "Friend"
    elif total == 0:
        return "Neutral"
    elif total == -1:
        return "Enemy"
    else:
        return "Great Enemy"


# ============================================================================
# MAIN CHART GENERATOR
# ============================================================================

def generate_vedic_chart(name: str, year: int, month: int, day: int,
                        hour: int, minute: int, city: str, 
                        lat: float, lon: float, timezone_str: str = "Asia/Kolkata") -> Union[Dict, ChartResponse]:
    """
    Generate complete Vedic astrology chart with all calculations.
    Returns a Pydantic Model (ChartResponse) for robustness.
    """
    try:
        logger.info(f"Generating chart for {name} ({city}, {year}-{month}-{day}) Tz: {timezone_str}")
        
        # 1. Validation Layer
        validate_input(year, month, day, hour, minute, lat, lon)
        
        # 2. Calculate Julian Day
        jd = calculate_julian_day(year, month, day, hour, minute, timezone_str)
        
        # 3. Get planetary positions
        chart_data = calculate_planetary_positions(jd)
        
        # 4. Get ascendant
        chart_data['ascendant'] = calculate_ascendant(jd, lat, lon)
        asc_sign_num = chart_data['ascendant']['sign_num']
        
        # 5. Calculate Chara Karakas
        karaka_map = calculate_chara_karakas(chart_data)
        
        # 6. Enhance each planet with additional data
        for planet_name, planet_data in chart_data.items():
            if planet_name == '_metadata':
                continue
            
            if not isinstance(planet_data, dict) or 'sign_num' not in planet_data:
                continue
            
            # Add Karaka
            planet_data['karaka'] = karaka_map.get(planet_name, '-')
            
            # Add House number (Whole Sign system)
            house_num = get_house_number(planet_data['sign_num'], asc_sign_num)
            planet_data['house'] = house_num
            
            # Add houses ruled
            planet_data['rules_houses'] = get_house_lords_ruled(planet_name, asc_sign_num)
            
            # Add compound relationship
            planet_data['relationship'] = calculate_compound_relationship(
                planet_name, planet_data['sign_num'], chart_data
            )
            
            # Add Nakshatra
            try:
                nak_dict, pada = get_nakshatra_by_longitude(planet_data['abs_pos'])
                planet_data['nakshatra'] = {
                    'nakshatra': nak_dict['name'],
                    'lord': nak_dict['lord'],
                    'pada': pada,
                    'symbol': nak_dict['symbol'],
                    'element': nak_dict['element']
                }
            except Exception as e:
                logger.warning(f"Failed to calculate nakshatra for {planet_name}: {e}")
                planet_data['nakshatra'] = {'nakshatra': 'Unknown', 'lord': '-', 'pada': 0}
        
        # 7. Calculate divisional charts (Vargas)
        varga_data = {}
        try:
            vargas_raw = calculate_all_vargas(chart_data)
            
            # Convert vargas to schema format
            for v_name, v_chart in vargas_raw.items():
                v_planets = {}
                for p_name, p_data in v_chart.items():
                     if isinstance(p_data, dict) and 'sign' in p_data:
                         v_planets[p_name] = VargaPlanet(**p_data)
                varga_data[v_name] = v_planets
                
        except Exception as e:
            logger.error(f"Varga calculation failed: {e}")
            # Don't fail entire chart for vargas
        
        # 8. Add metadata
        metadata = ChartMetadata(
            name=name,
            datetime=f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}",
            location=city,
            latitude=lat,
            longitude=lon,
            ayanamsa=round(swe.get_ayanamsa_ut(jd), 2),
            zodiac_system='Sidereal (Lahiri)',
            house_system='Whole Sign',
            gender='Unknown' # Default
        )

        # 9. Construct Response
        planets_dict = {}
        for p_name, p_data in chart_data.items():
            if not isinstance(p_data, dict): continue
            
            # Convert Nakshatra to schema
            if 'nakshatra' in p_data and isinstance(p_data['nakshatra'], dict):
                p_data['nakshatra'] = NakshatraInfo(**p_data['nakshatra'])
            
            planets_dict[p_name] = PlanetPosition(**p_data)
            
        response = ChartResponse(
            planets=planets_dict,
            metadata=metadata,
            vargas=varga_data
        )
        
        logger.info("Chart generation completed successfully (Pydantic).")
        return response
        
    except AstrologyError as e:
        logger.error(f"Astrology Error: {e}")
        return {"error": str(e), "type": e.__class__.__name__}
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        return {"error": f"Internal Server Error: {str(e)}"}