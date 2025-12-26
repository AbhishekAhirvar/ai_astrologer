"""
Vedic Astrology Chart Generator
Uses Swiss Ephemeris with Lahiri Ayanamsa
Implements proper Vedic calculation methods
"""

import swisseph as swe
from datetime import datetime
import pytz
from typing import Dict, Tuple, Optional, List
from enum import Enum
from backend.nakshatra_data import get_nakshatra_by_longitude


# ============================================================================
# CONSTANTS
# ============================================================================

class ZodiacSign(Enum):
    """Zodiac signs enumeration"""
    ARIES = 0
    TAURUS = 1
    GEMINI = 2
    CANCER = 3
    LEO = 4
    VIRGO = 5
    LIBRA = 6
    SCORPIO = 7
    SAGITTARIUS = 8
    CAPRICORN = 9
    AQUARIUS = 10
    PISCES = 11


ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Sign lords for Vedic astrology
SIGN_LORDS = {
    0: 'Mars',      # Aries
    1: 'Venus',     # Taurus
    2: 'Mercury',   # Gemini
    3: 'Moon',      # Cancer
    4: 'Sun',       # Leo
    5: 'Mercury',   # Virgo
    6: 'Venus',     # Libra
    7: 'Mars',      # Scorpio
    8: 'Jupiter',   # Sagittarius
    9: 'Saturn',    # Capricorn
    10: 'Saturn',   # Aquarius
    11: 'Jupiter'   # Pisces
}

# Natural relationships (Friend=1, Neutral=0, Enemy=-1)
NATURAL_RELATIONSHIPS = {
    'Sun': {'Moon': 1, 'Mars': 1, 'Jupiter': 1, 'Mercury': 0, 'Venus': -1, 'Saturn': -1},
    'Moon': {'Sun': 1, 'Mercury': 1, 'Mars': 0, 'Jupiter': 0, 'Venus': 0, 'Saturn': 0},
    'Mars': {'Sun': 1, 'Moon': 1, 'Jupiter': 1, 'Venus': 0, 'Saturn': 0, 'Mercury': -1},
    'Mercury': {'Sun': 1, 'Venus': 1, 'Mars': 0, 'Jupiter': 0, 'Saturn': 0, 'Moon': -1},
    'Jupiter': {'Sun': 1, 'Moon': 1, 'Mars': 1, 'Mercury': -1, 'Venus': -1, 'Saturn': 0},
    'Venus': {'Mercury': 1, 'Saturn': 1, 'Mars': 0, 'Jupiter': 0, 'Sun': -1, 'Moon': -1},
    'Saturn': {'Venus': 1, 'Mercury': 1, 'Jupiter': 0, 'Sun': -1, 'Moon': -1, 'Mars': -1},
    'Rahu': {'Venus': 1, 'Saturn': 1, 'Mercury': 1, 'Jupiter': 0, 'Sun': -1, 'Moon': -1, 'Mars': -1},
    'Ketu': {'Mars': 1, 'Jupiter': 1, 'Sun': 1, 'Moon': 1, 'Venus': 0, 'Saturn': 0, 'Mercury': -1}
}

# Karaka labels (Atmakaraka to Darakaraka)
KARAKA_LABELS = ['AK', 'AmK', 'BK', 'MK', 'PK', 'GK', 'DK']

# Swiss Ephemeris planet IDs
PLANET_IDS = {
    'sun': swe.SUN,
    'moon': swe.MOON,
    'mercury': swe.MERCURY,
    'venus': swe.VENUS,
    'mars': swe.MARS,
    'jupiter': swe.JUPITER,
    'saturn': swe.SATURN,
    'rahu': swe.TRUE_NODE,
}


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
                         hour: int, minute: int) -> float:
    """
    Calculate Julian Day for given datetime (assumes IST).
    
    Args:
        year, month, day, hour, minute: Date and time components
    
    Returns:
        Julian Day number
    """
    try:
        tz = pytz.timezone('Asia/Kolkata')
        dt = tz.localize(datetime(year, month, day, hour, minute))
        dt_utc = dt.astimezone(pytz.UTC)
        return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, 
                         dt_utc.hour + dt_utc.minute / 60.0)
    except Exception:
        # Fallback: treat as UTC
        return swe.julday(year, month, day, hour + minute / 60.0)


def calculate_planetary_positions(jd: float) -> Dict:
    """
    Calculate sidereal positions of all planets.
    
    Args:
        jd: Julian Day number
    
    Returns:
        Dictionary with planet positions
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    chart_data = {}
    
    for planet_name, planet_id in PLANET_IDS.items():
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
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    # Get houses (we only need ascendant)
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

def calculate_d9_navamsa(chart_data: Dict) -> Dict:
    """
    Calculate D9 (Navamsa) chart using proper Vedic method.
    
    Rules:
    - Each sign divided into 9 parts of 3°20' each
    - Movable signs (Aries, Cancer, Libra, Capricorn): Start from same sign
    - Fixed signs (Taurus, Leo, Scorpio, Aquarius): Start from 9th sign
    - Dual signs (Gemini, Virgo, Sagittarius, Pisces): Start from 5th sign
    
    Args:
        chart_data: Base chart data
    
    Returns:
        D9 chart dictionary
    """
    d9_chart = {}
    
    # Movable, Fixed, Dual sign classifications
    movable = [0, 3, 6, 9]    # Aries, Cancer, Libra, Capricorn
    fixed = [1, 4, 7, 10]      # Taurus, Leo, Scorpio, Aquarius
    dual = [2, 5, 8, 11]       # Gemini, Virgo, Sagittarius, Pisces
    
    for planet_name, planet_data in chart_data.items():
        if planet_name in ['_metadata', 'd9_chart', 'd10_chart', 'd12_chart']:
            continue
        
        if not isinstance(planet_data, dict) or 'sign_num' not in planet_data:
            continue
        
        sign_num = planet_data['sign_num']
        degree = planet_data['degree']
        
        # Determine which pada (1-9)
        pada = int(degree / (30 / 9)) + 1
        if pada > 9:
            pada = 9
        
        # Determine starting sign for navamsa
        if sign_num in movable:
            start_sign = sign_num
        elif sign_num in fixed:
            start_sign = (sign_num + 8) % 12  # 9th sign
        else:  # dual
            start_sign = (sign_num + 4) % 12  # 5th sign
        
        # Calculate D9 sign
        d9_sign_num = (start_sign + pada - 1) % 12
        
        # Calculate degree within D9 sign (proportional distribution)
        degree_fraction = (degree % (30 / 9)) / (30 / 9)
        d9_degree = degree_fraction * 30
        d9_longitude = d9_sign_num * 30 + d9_degree
        
        sign, deg, _ = get_zodiac_sign(d9_longitude)
        
        d9_chart[planet_name] = {
            'name': planet_data['name'],
            'sign': sign,
            'degree': round(deg, 2),
            'sign_num': d9_sign_num,
            'abs_pos': round(d9_longitude, 2)
        }
    
    return d9_chart


def calculate_d10_dasamsa(chart_data: Dict) -> Dict:
    """
    Calculate D10 (Dasamsa) chart for career analysis.
    
    Rules:
    - Each sign divided into 10 parts of 3° each
    - Odd signs: Start from same sign
    - Even signs: Start from 9th sign from it
    
    Args:
        chart_data: Base chart data
    
    Returns:
        D10 chart dictionary
    """
    d10_chart = {}
    
    for planet_name, planet_data in chart_data.items():
        if planet_name in ['_metadata', 'd9_chart', 'd10_chart', 'd12_chart']:
            continue
        
        if not isinstance(planet_data, dict) or 'sign_num' not in planet_data:
            continue
        
        sign_num = planet_data['sign_num']
        degree = planet_data['degree']
        
        # Determine which division (1-10)
        division = int(degree / 3) + 1
        if division > 10:
            division = 10
        
        # Odd signs (Aries, Gemini, Leo, etc.) = 0, 2, 4, 6, 8, 10
        if sign_num % 2 == 0:  # Odd sign in zodiac sequence
            start_sign = sign_num
        else:  # Even sign
            start_sign = (sign_num + 8) % 12
        
        d10_sign_num = (start_sign + division - 1) % 12
        
        degree_fraction = (degree % 3) / 3
        d10_degree = degree_fraction * 30
        d10_longitude = d10_sign_num * 30 + d10_degree
        
        sign, deg, _ = get_zodiac_sign(d10_longitude)
        
        d10_chart[planet_name] = {
            'name': planet_data['name'],
            'sign': sign,
            'degree': round(deg, 2),
            'sign_num': d10_sign_num,
            'abs_pos': round(d10_longitude, 2)
        }
    
    return d10_chart


def calculate_d12_dwadasamsa(chart_data: Dict) -> Dict:
    """
    Calculate D12 (Dwadasamsa) chart for parents and ancestry.
    
    Rules:
    - Each sign divided into 12 parts of 2°30' each
    - Start counting from same sign
    
    Args:
        chart_data: Base chart data
    
    Returns:
        D12 chart dictionary
    """
    d12_chart = {}
    
    for planet_name, planet_data in chart_data.items():
        if planet_name in ['_metadata', 'd9_chart', 'd10_chart', 'd12_chart']:
            continue
        
        if not isinstance(planet_data, dict) or 'sign_num' not in planet_data:
            continue
        
        sign_num = planet_data['sign_num']
        degree = planet_data['degree']
        
        # Determine which division (1-12)
        division = int(degree / 2.5) + 1
        if division > 12:
            division = 12
        
        # D12 starts from same sign
        d12_sign_num = (sign_num + division - 1) % 12
        
        degree_fraction = (degree % 2.5) / 2.5
        d12_degree = degree_fraction * 30
        d12_longitude = d12_sign_num * 30 + d12_degree
        
        sign, deg, _ = get_zodiac_sign(d12_longitude)
        
        d12_chart[planet_name] = {
            'name': planet_data['name'],
            'sign': sign,
            'degree': round(deg, 2),
            'sign_num': d12_sign_num,
            'abs_pos': round(d12_longitude, 2)
        }
    
    return d12_chart


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
                        lat: float, lon: float) -> Dict:
    """
    Generate complete Vedic astrology chart with all calculations.
    
    Args:
        name: Person's name
        year, month, day, hour, minute: Birth datetime
        city: Birth city name
        lat: Latitude
        lon: Longitude
    
    Returns:
        Complete chart dictionary with all calculations
    """
    try:
        # Calculate Julian Day
        jd = calculate_julian_day(year, month, day, hour, minute)
        
        # Get planetary positions
        chart_data = calculate_planetary_positions(jd)
        
        # Get ascendant
        chart_data['ascendant'] = calculate_ascendant(jd, lat, lon)
        asc_sign_num = chart_data['ascendant']['sign_num']
        
        # Calculate Chara Karakas
        karaka_map = calculate_chara_karakas(chart_data)
        
        # Enhance each planet with additional data
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
            nak_dict, pada = get_nakshatra_by_longitude(planet_data['abs_pos'])
            planet_data['nakshatra'] = {
                'nakshatra': nak_dict['name'],
                'lord': nak_dict['lord'],
                'pada': pada
            }
        
        # Calculate divisional charts
        chart_data['d9_chart'] = calculate_d9_navamsa(chart_data)
        chart_data['d10_chart'] = calculate_d10_dasamsa(chart_data)
        chart_data['d12_chart'] = calculate_d12_dwadasamsa(chart_data)
        
        # Add metadata
        chart_data['_metadata'] = {
            'name': name,
            'datetime': f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}",
            'location': city,
            'latitude': lat,
            'longitude': lon,
            'ayanamsa': round(swe.get_ayanamsa_ut(jd), 2),
            'zodiac_system': 'Sidereal (Lahiri)',
            'house_system': 'Whole Sign'
        }
        
        return chart_data
        
    except Exception as e:
        return {"error": str(e)}