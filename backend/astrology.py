import swisseph as swe
from datetime import datetime
import pytz

# Zodiac signs in order
ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def get_zodiac_sign(longitude):
    """Convert ecliptic longitude to zodiac sign and degree."""
    sign_num = int(longitude / 30)
    degree = longitude % 30
    return ZODIAC_SIGNS[sign_num], degree, sign_num

def generate_chart(name, year, month, day, hour, minute, city, lat, lon):
    """
    Generates a Vedic astrology chart using pyswisseph with Lahiri ayanamsa.
    """
    try:
        # Set Sidereal mode with Lahiri ayanamsa (most common in Vedic astrology)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        
        # Create datetime and convert to Julian Day
        # Assuming local time - for precise calculations we'd need timezone
        # For MVP, we'll use UTC offset estimation or assume IST for India
        try:
            tz = pytz.timezone('Asia/Kolkata')  # Default to IST for MVP
            dt = tz.localize(datetime(year, month, day, hour, minute))
            dt_utc = dt.astimezone(pytz.UTC)
            jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, 
                           dt_utc.hour + dt_utc.minute/60.0)
        except:
            # Fallback: use naive time
            jd = swe.julday(year, month, day, hour + minute/60.0)
        
        # Calculate planetary positions (sidereal)
        planets = {
            'sun': swe.SUN,
            'moon': swe.MOON,
            'mercury': swe.MERCURY,
            'venus': swe.VENUS,
            'mars': swe.MARS,
            'jupiter': swe.JUPITER,
            'saturn': swe.SATURN,
            'rahu': swe.TRUE_NODE,  # North Node (Rahu in Vedic)
        }
        
        chart_data = {}
        
        for planet_name, planet_id in planets.items():
            # Calculate sidereal position
            result = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL)
            longitude = result[0][0]  # Ecliptic longitude
            
            sign, degree, sign_num = get_zodiac_sign(longitude)
            
            chart_data[planet_name] = {
                'name': planet_name.capitalize(),
                'sign': sign,
                'degree': round(degree, 2),
                'sign_num': sign_num,
                'abs_pos': round(longitude, 2)
            }
        
        # Calculate Ketu (opposite of Rahu)
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
        
        # Calculate Ascendant (Lagna)
        houses = swe.houses(jd, lat, lon, b'P')  # Placidus house system
        asc_tropical = houses[0][0]  # Tropical ascendant
        
        # Get ayanamsa value
        ayanamsa = swe.get_ayanamsa_ut(jd)
        asc_sidereal = (asc_tropical - ayanamsa) % 360
        
        sign, degree, sign_num = get_zodiac_sign(asc_sidereal)
        chart_data['ascendant'] = {
            'name': 'Ascendant',
            'sign': sign,
            'degree': round(degree, 2),
            'sign_num': sign_num,
            'abs_pos': round(asc_sidereal, 2)
        }
        
        # Add metadata
        chart_data['_metadata'] = {
            'name': name,
            'datetime': f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}",
            'location': city,
            'latitude': lat,
            'longitude': lon,
            'ayanamsa': round(ayanamsa, 2),
            'zodiac_system': 'Sidereal (Lahiri)'
        }
        
        return chart_data
        
    except Exception as e:
        return {"error": str(e)}

from backend.nakshatra_data import NAKSHATRAS, get_nakshatra_by_longitude

# ============================================================================
# NAKSHATRA CALCULATION
# ============================================================================

def calculate_nakshatra(planet_longitude):
    """
    Calculate which nakshatra a planet is in
    
    Args:
        planet_longitude: Float (0-360°)
    
    Returns:
        {
            'nakshatra': 'Rohini',
            'number': 3,
            'lord': 'Moon',
            'pada': 2,
            'element': 'Earth',
            'symbol': '🚗 Chariot'
        }
    """
    nakshatra_dict, pada = get_nakshatra_by_longitude(planet_longitude)
    
    return {
        'nakshatra': nakshatra_dict['name'],
        'number': nakshatra_dict['number'] + 1,
        'lord': nakshatra_dict['lord'],
        'pada': pada,
        'element': nakshatra_dict['element'],
        'symbol': nakshatra_dict['symbol'],
        'deity': nakshatra_dict['deity'],
        'color': nakshatra_dict['color']
    }

# ============================================================================
# DIVISIONAL CHARTS (D-CHARTS)
# ============================================================================

# ============================================================================
# DIVISIONAL CHARTS (D-CHARTS) - FIXED VERSION
# ============================================================================

def calculate_d9_chart(chart_data):
    """
    D9 (Navamsa) - Division of 9
    Used for: Marriage, partnerships, spiritual growth
    
    Formula: D9_position = (planet_position * 9) % 360
    Then map to zodiac sign
    """
    d9_chart = {}
    
    for planet_name, planet_data in chart_data.items():
        # Skip metadata and D-chart keys
        if planet_name in ['_metadata', 'd9_chart', 'd10_chart', 'd12_chart']:
            continue
        
        # Check if planet_data is a dict and has required key
        if not isinstance(planet_data, dict) or 'abs_pos' not in planet_data:
            continue
        
        base_longitude = planet_data['abs_pos']
        
        # D9 calculation
        d9_longitude = (base_longitude * 9) % 360
        
        # Get sign and degree
        sign, degree, sign_num = get_zodiac_sign(d9_longitude)
        
        # Get nakshatra in D9
        nakshatra = calculate_nakshatra(d9_longitude)
        
        d9_chart[planet_name] = {
            'name': planet_data['name'],
            'sign': sign,
            'degree': round(degree, 2),
            'sign_num': sign_num,
            'abs_pos': round(d9_longitude, 2),
            'nakshatra': nakshatra['nakshatra'],
            'nakshatra_lord': nakshatra['lord']
        }
    
    return d9_chart

def calculate_d10_chart(chart_data):
    """
    D10 (Dasamsa) - Division of 10
    Used for: Career, profession, public image, authority
    
    Formula: D10_position = (planet_position * 10) % 360
    """
    d10_chart = {}
    
    for planet_name, planet_data in chart_data.items():
        # Skip metadata and D-chart keys
        if planet_name in ['_metadata', 'd9_chart', 'd10_chart', 'd12_chart']:
            continue
        
        # Check if planet_data is a dict and has required key
        if not isinstance(planet_data, dict) or 'abs_pos' not in planet_data:
            continue
        
        base_longitude = planet_data['abs_pos']
        
        # D10 calculation
        d10_longitude = (base_longitude * 10) % 360
        
        # Get sign and degree
        sign, degree, sign_num = get_zodiac_sign(d10_longitude)
        
        # Get nakshatra in D10
        nakshatra = calculate_nakshatra(d10_longitude)
        
        d10_chart[planet_name] = {
            'name': planet_data['name'],
            'sign': sign,
            'degree': round(degree, 2),
            'sign_num': sign_num,
            'abs_pos': round(d10_longitude, 2),
            'nakshatra': nakshatra['nakshatra'],
            'nakshatra_lord': nakshatra['lord']
        }
    
    return d10_chart

def calculate_d12_chart(chart_data):
    """
    D12 (Dwadasamsa) - Division of 12
    Used for: Parents, family heritage, fortune
    
    Formula: D12_position = (planet_position * 12) % 360
    """
    d12_chart = {}
    
    for planet_name, planet_data in chart_data.items():
        # Skip metadata and D-chart keys
        if planet_name in ['_metadata', 'd9_chart', 'd10_chart', 'd12_chart']:
            continue
        
        # Check if planet_data is a dict and has required key
        if not isinstance(planet_data, dict) or 'abs_pos' not in planet_data:
            continue
        
        base_longitude = planet_data['abs_pos']
        
        # D12 calculation
        d12_longitude = (base_longitude * 12) % 360
        
        # Get sign and degree
        sign, degree, sign_num = get_zodiac_sign(d12_longitude)
        
        # Get nakshatra in D12
        nakshatra = calculate_nakshatra(d12_longitude)
        
        d12_chart[planet_name] = {
            'name': planet_data['name'],
            'sign': sign,
            'degree': round(degree, 2),
            'sign_num': sign_num,
            'abs_pos': round(d12_longitude, 2),
            'nakshatra': nakshatra['nakshatra'],
            'nakshatra_lord': nakshatra['lord']
        }
    
    return d12_chart

# ============================================================================
# ENHANCED CHART WITH NAKSHATRAS
# ============================================================================

def generate_chart_with_nakshatras(name, year, month, day, hour, minute, city, lat, lon):
    """
    Generate complete chart with nakshatra information for all planets
    
    This is an ENHANCED version that includes D-charts
    """
    # Get base chart (existing function)
    base_chart = generate_chart(name, year, month, day, hour, minute, city, lat, lon)
    
    if "error" in base_chart:
        return base_chart
    
    # Add nakshatra to each planet in BASE chart
    for planet_name, planet_data in base_chart.items():
        # Skip metadata
        if planet_name == '_metadata':
            continue
        
        # Check if valid planet data
        if not isinstance(planet_data, dict) or 'abs_pos' not in planet_data:
            continue
        
        nakshatra_info = calculate_nakshatra(planet_data['abs_pos'])
        base_chart[planet_name]['nakshatra'] = nakshatra_info
    
    # Add D-charts (AFTER base chart is complete)
    base_chart['d9_chart'] = calculate_d9_chart(base_chart)
    base_chart['d10_chart'] = calculate_d10_chart(base_chart)
    base_chart['d12_chart'] = calculate_d12_chart(base_chart)
    
    return base_chart
