from typing import Dict
from backend.logger import logger

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def get_varga_sign(longitude: float) -> int:
    """Helper to get sign number from longitude (0-11)"""
    return int(longitude / 30) % 12

def calculate_varga(chart_data: Dict, divisor: int, start_rule: str) -> Dict:
    """
    Calculate varga chart with proper boundary handling and precision.
    
    Args:
        chart_data: Dictionary containing planetary positions (sign_num, degree).
        divisor: The division number (e.g., 9 for Navamsa).
        start_rule: Rule to determine starting sign ('same', 'odd_even', 'movable_fixed_dual').
        
    Returns:
        Dict: Varga chart data for all planets.

    Example:
        >>> chart = {'sun': {'name': 'Sun', 'sign_num': 0, 'degree': 10.5}}
        >>> d9 = calculate_varga(chart, 9, 'movable_fixed_dual')
    """
    if divisor <= 0 or divisor > 60:
        logger.error(f"Invalid divisor: {divisor}")
        return {}
    
    VALID_RULES = {'same', 'odd_even', 'movable_fixed_dual'}
    if start_rule not in VALID_RULES:
        logger.error(f"Invalid start_rule: {start_rule}")
        return {}
    
    varga_chart = {}
    div_size = 30.0 / divisor
    NINTH_OFFSET = 8
    FIFTH_OFFSET = 4
    
    for planet_name, planet_data in chart_data.items():
        if planet_name == '_metadata' or not isinstance(planet_data, dict):
            continue
            
        if 'sign_num' not in planet_data or 'degree' not in planet_data:
            continue
            
        sign_num = planet_data['sign_num']
        degree = planet_data['degree']
        
        # Validate inputs
        if not (0 <= degree <= 30):
            logger.warning(f"{planet_name}: degree {degree} out of expected [0, 30] range")
            degree = max(0, min(degree, 29.9999))
            
        if not (0 <= sign_num < 12):
            logger.error(f"{planet_name}: sign_num {sign_num} out of range [0, 12)")
            continue
        
        # Calculate division (0-indexed internally)
        division_index = int(degree / div_size)
        division_index = min(division_index, divisor - 1)  # Handle boundary
        division = division_index + 1
        
        # Calculate starting sign based on rule
        if start_rule == 'same':
            start_sign = sign_num
        elif start_rule == 'odd_even':
            # Odd: Aries(0), Gemini(2)... (Vedic counting 1, 3...)
            # Note: sign_num % 2 == 0 corresponds to Odd signs (1, 3, 5, 7, 9, 11)
            start_sign = sign_num if (sign_num % 2 == 0) else (sign_num + NINTH_OFFSET) % 12
        elif start_rule == 'movable_fixed_dual':
            if sign_num in [0, 3, 6, 9]:  # Movable
                start_sign = sign_num
            elif sign_num in [1, 4, 7, 10]:  # Fixed
                start_sign = (sign_num + NINTH_OFFSET) % 12
            else:  # Dual [2, 5, 8, 11]
                start_sign = (sign_num + FIFTH_OFFSET) % 12
        
        varga_sign_num = (start_sign + division - 1) % 12
        
        # Degree within varga sign - handle boundary properly
        degree_in_division = degree - (division_index * div_size)
        v_degree = (degree_in_division / div_size) * 30.0
        v_degree = min(v_degree, 29.9999)  # Cap at sign boundary
        
        v_longitude = varga_sign_num * 30 + v_degree
        
        varga_chart[planet_name] = {
            'name': planet_data['name'],
            'sign': ZODIAC_SIGNS[varga_sign_num],
            'sign_num': varga_sign_num,
            'degree': round(v_degree, 4),
            'abs_pos': round(v_longitude, 4)
        }
    
    logger.debug(f"Calculated {divisor} varga with rule {start_rule}")
    return varga_chart

def calculate_d2_hora(chart_data: Dict) -> Dict:
    """D2 - Hora (Wealth)"""
    d2 = {}
    for p_name, p_data in chart_data.items():
        if p_name == '_metadata' or not isinstance(p_data, dict) or 'abs_pos' not in p_data: continue
        sign_num = p_data['sign_num']
        degree = p_data['degree']
        
        # Odd sign: 0-15 Sun (Leo/4), 15-30 Moon (Cancer/3)
        # Even sign: 0-15 Moon (Cancer/3), 15-30 Sun (Leo/4)
        is_odd = (sign_num % 2 == 0)
        if is_odd:
            h_sign = 4 if degree < 15 else 3
        else:
            h_sign = 3 if degree < 15 else 4
            
        d2[p_name] = {
            'name': p_data['name'],
            'sign': ZODIAC_SIGNS[h_sign],
            'sign_num': h_sign,
            'degree': round((degree % 15) * 2, 2),
            'abs_pos': h_sign * 30 + (degree % 15) * 2
        }
    return d2

def calculate_d3_drekkana(chart_data: Dict) -> Dict:
    """D3 - Drekkana (Siblings) - 1, 5, 9 houses from same sign"""
    d3 = {}
    for p_name, p_data in chart_data.items():
        if p_name == '_metadata' or not isinstance(p_data, dict) or 'abs_pos' not in p_data: continue
        sign_num = p_data['sign_num']
        degree = p_data['degree']
        
        div = int(degree / 10) # 0, 1, 2
        d3_sign = (sign_num + (div * 4)) % 12
        
        d3[p_name] = {
            'name': p_data['name'],
            'sign': ZODIAC_SIGNS[d3_sign],
            'sign_num': d3_sign,
            'degree': round((degree % 10) * 3, 2),
            'abs_pos': d3_sign * 30 + (degree % 10) * 3
        }
    return d3

def calculate_d4_chaturthamsa(chart_data: Dict) -> Dict:
    """D4 - Chaturthamsa (Property) - 1, 4, 7, 10 houses"""
    d4 = {}
    for p_name, p_data in chart_data.items():
        if p_name == '_metadata' or not isinstance(p_data, dict) or 'abs_pos' not in p_data: continue
        sign_num = p_data['sign_num']
        degree = p_data['degree']
        
        div = int(degree / 7.5) # 0, 1, 2, 3
        d4_sign = (sign_num + (div * 3)) % 12 # 1st, 4th, 7th, 10th
        
        d4[p_name] = {
            'name': p_data['name'],
            'sign': ZODIAC_SIGNS[d4_sign],
            'sign_num': d4_sign,
            'degree': round((degree % 7.5) * 4, 2),
            'abs_pos': d4_sign * 30 + (degree % 7.5) * 4
        }
    return d4

def calculate_d7_saptamsa(chart_data: Dict) -> Dict:
    """D7 - Saptamsa (Children) - Odd: from same, Even: from 7th"""
    return calculate_varga(chart_data, 7, 'odd_even_d7') # Wait, I need to update calculate_varga for this

def calculate_d5_panchamsa(chart_data: Dict) -> Dict:
    """D5 - Panchamsa"""
    return calculate_varga(chart_data, 5, 'odd_even') # Simplified standard

def calculate_d6_shashtamsa(chart_data: Dict) -> Dict:
    """D6 - Shashtamsa"""
    return calculate_varga(chart_data, 6, 'odd_even') # Simplified standard

def calculate_d7_explicit(chart_data: Dict) -> Dict:
    d7 = {}
    div_size = 30.0 / 7
    for p_name, p_data in chart_data.items():
        if p_name == '_metadata' or not isinstance(p_data, dict) or 'abs_pos' not in p_data: continue
        sign_num = p_data['sign_num']
        degree = p_data['degree']
        div_idx = int(degree / div_size)
        
        if sign_num % 2 == 0: # Odd sign
            start_sign = sign_num
        else: # Even sign
            start_sign = (sign_num + 6) % 12 # 7th from it
            
        d7_sign = (start_sign + div_idx) % 12
        d7[p_name] = {
            'name': p_data['name'],
            'sign': ZODIAC_SIGNS[d7_sign],
            'sign_num': d7_sign,
            'degree': round((degree % div_size) * (30/div_size), 2),
            'abs_pos': d7_sign * 30 + (degree % div_size) * (30/div_size)
        }
    return d7

def calculate_d8_ashtamsa(chart_data: Dict) -> Dict:
    """D8 - Ashtamsa"""
    d8 = {}
    div_size = 30.0 / 8
    for p_name, p_data in chart_data.items():
        if p_name == '_metadata' or not isinstance(p_data, dict) or 'abs_pos' not in p_data: continue
        sign_num = p_data['sign_num']
        degree = p_data['degree']
        div_idx = int(degree / div_size)
        
        if sign_num in [0, 3, 6, 9]: start_sign = 0 # Movable
        elif sign_num in [1, 4, 7, 10]: start_sign = 8 # Fixed
        else: start_sign = 4 # Dual
            
        d8_sign = (start_sign + div_idx) % 12
        d8[p_name] = {
            'name': p_data['name'],
            'sign': ZODIAC_SIGNS[d8_sign],
            'sign_num': d8_sign,
            'degree': round((degree % div_size) * (30/div_size), 2),
            'abs_pos': d8_sign * 30 + (degree % div_size) * (30/div_size)
        }
    return d8

def calculate_d16_shodasamsa(chart_data: Dict) -> Dict:
    """D16 - Shodasamsa (Vehicles, Comfort)"""
    d16 = {}
    div_size = 30.0 / 16
    for p_name, p_data in chart_data.items():
        if p_name == '_metadata' or not isinstance(p_data, dict) or 'abs_pos' not in p_data: continue
        sign_num = p_data['sign_num']
        degree = p_data['degree']
        div_idx = int(degree / div_size)
        
        if sign_num in [0, 3, 6, 9]: # Movable: starts Aries (0)
            start_sign = 0
        elif sign_num in [1, 4, 7, 10]: # Fixed: starts Leo (4)
            start_sign = 4
        else: # Dual: starts Sagittarius (8)
            start_sign = 8
            
        d16_sign = (start_sign + div_idx) % 12
        d16[p_name] = {
            'name': p_data['name'],
            'sign': ZODIAC_SIGNS[d16_sign],
            'sign_num': d16_sign,
            'degree': round((degree % div_size) * (30/div_size), 2),
            'abs_pos': d16_sign * 30 + (degree % div_size) * (30/div_size)
        }
    return d16

def calculate_d11_rudramsa(chart_data: Dict) -> Dict:
    """D11 - Rudramsa"""
    # Simple cyclic for now
    return calculate_varga(chart_data, 11, 'same')

def calculate_d20_vimsamsa(chart_data: Dict) -> Dict:
    """D20 - Vimsamsa (Spirituality)"""
    d20 = {}
    div_size = 30.0 / 20
    for p_name, p_data in chart_data.items():
        if p_name == '_metadata' or not isinstance(p_data, dict) or 'abs_pos' not in p_data: continue
        sign_num = p_data['sign_num']
        degree = p_data['degree']
        div_idx = int(degree / div_size)
        
        if sign_num in [0, 3, 6, 9]: # Movable: starts Aries (0)
            start_sign = 0
        elif sign_num in [1, 4, 7, 10]: # Fixed: starts Sagittarius (8)
            start_sign = 8
        else: # Dual: starts Leo (4)
            start_sign = 4
            
        d20_sign = (start_sign + div_idx) % 12
        d20[p_name] = {
            'name': p_data['name'],
            'sign': ZODIAC_SIGNS[d20_sign],
            'sign_num': d20_sign,
            'degree': round((degree % div_size) * (30/div_size), 2),
            'abs_pos': d20_sign * 30 + (degree % div_size) * (30/div_size)
        }
    return d20

def calculate_d24_siddhamsa(chart_data: Dict) -> Dict:
    """D24 - Siddhamsa (Education)"""
    d24 = {}
    div_size = 30.0 / 24
    for p_name, p_data in chart_data.items():
        if p_name == '_metadata' or not isinstance(p_data, dict) or 'abs_pos' not in p_data: continue
        sign_num = p_data['sign_num']
        degree = p_data['degree']
        div_idx = int(degree / div_size)
        
        # Odd starts Leo(4), Even starts Cancer(3)
        if sign_num % 2 == 0: start_sign = 4
        else: start_sign = 3
            
        d24_sign = (start_sign + div_idx) % 12
        d24[p_name] = {
            'name': p_data['name'],
            'sign': ZODIAC_SIGNS[d24_sign],
            'sign_num': d24_sign,
            'degree': round((degree % div_size) * (30/div_size), 2),
            'abs_pos': d24_sign * 30 + (degree % div_size) * (30/div_size)
        }
    return d24

def calculate_d27_nakshatramsa(chart_data: Dict) -> Dict:
    """D27 - Nakshatramsa (Strengths)"""
    d27 = {}
    div_size = 30.0 / 27
    for p_name, p_data in chart_data.items():
        if p_name == '_metadata' or not isinstance(p_data, dict) or 'abs_pos' not in p_data: continue
        sign_num = p_data['sign_num']
        degree = p_data['degree']
        div_idx = int(degree / div_size)
        
        # Fire(0,4,8) starts Aries(0), Earth(1,5,9) starts Capricorn(9), 
        # Air(2,6,10) starts Libra(6), Water(3,7,11) starts Cancer(3)
        group = sign_num % 4
        if group == 0: start_sign = 0 # Fire
        elif group == 1: start_sign = 9 # Earth
        elif group == 2: start_sign = 6 # Air
        else: start_sign = 3 # Water
            
        d27_sign = (start_sign + div_idx) % 12
        d27[p_name] = {
            'name': p_data['name'],
            'sign': ZODIAC_SIGNS[d27_sign],
            'sign_num': d27_sign,
            'degree': round((degree % div_size) * (30/div_size), 2),
            'abs_pos': d27_sign * 30 + (degree % div_size) * (30/div_size)
        }
    return d27

def calculate_d30_trimsamsa(chart_data: Dict) -> Dict:
    """D30 - Trimsamsa (Misfortunes) - Parashara method"""
    d30 = {}
    for p_name, p_data in chart_data.items():
        if p_name == '_metadata' or not isinstance(p_data, dict) or 'abs_pos' not in p_data: continue
        sign_num = p_data['sign_num']
        degree = p_data['degree']
        
        is_odd = (sign_num % 2 == 0)
        t_sign = 0
        if is_odd:
            if degree < 5: t_sign = 0 # Aries (Mars)
            elif degree < 10: t_sign = 10 # Aquarius (Saturn)
            elif degree < 18: t_sign = 8 # Sagittarius (Jupiter)
            elif degree < 25: t_sign = 2 # Gemini (Mercury)
            else: t_sign = 6 # Libra (Venus)
        else:
            if degree < 5: t_sign = 1 # Taurus (Venus)
            elif degree < 12: t_sign = 5 # Virgo (Mercury)
            elif degree < 20: t_sign = 11 # Pisces (Jupiter)
            elif degree < 25: t_sign = 9 # Capricorn (Saturn)
            else: t_sign = 7 # Scorpio (Mars)
            
        d30[p_name] = {
            'name': p_data['name'],
            'sign': ZODIAC_SIGNS[t_sign],
            'sign_num': t_sign,
            'degree': 0, # Not usually degree-based in D30 common representation
            'abs_pos': t_sign * 30
        }
    return d30

def calculate_d40_khavedamsa(chart_data: Dict) -> Dict:
    """D40 - Khavedamsa (Auspicious effects)"""
    d40 = {}
    div_size = 30.0 / 40
    for p_name, p_data in chart_data.items():
        if p_name == '_metadata' or not isinstance(p_data, dict) or 'abs_pos' not in p_data: continue
        sign_num = p_data['sign_num']
        degree = p_data['degree']
        div_idx = int(degree / div_size)
        
        # Odd starts Aries(0), Even starts Libra(6)
        if sign_num % 2 == 0: start_sign = 0
        else: start_sign = 6
            
        d40_sign = (start_sign + div_idx) % 12
        d40[p_name] = {
            'name': p_data['name'],
            'sign': ZODIAC_SIGNS[d40_sign],
            'sign_num': d40_sign,
            'degree': round((degree % div_size) * (30/div_size), 2),
            'abs_pos': d40_sign * 30 + (degree % div_size) * (30/div_size)
        }
    return d40

def calculate_d45_akshavedamsa(chart_data: Dict) -> Dict:
    """D45 - Akshavedamsa (All areas)"""
    d45 = {}
    div_size = 30.0 / 45
    for p_name, p_data in chart_data.items():
        if p_name == '_metadata' or not isinstance(p_data, dict) or 'abs_pos' not in p_data: continue
        sign_num = p_data['sign_num']
        degree = p_data['degree']
        div_idx = int(degree / div_size)
        
        if sign_num in [0, 3, 6, 9]: start_sign = 0 # Movable
        elif sign_num in [1, 4, 7, 10]: start_sign = 4 # Fixed
        else: start_sign = 8 # Dual
            
        d45_sign = (start_sign + div_idx) % 12
        d45[p_name] = {
            'name': p_data['name'],
            'sign': ZODIAC_SIGNS[d45_sign],
            'sign_num': d45_sign,
            'degree': round((degree % div_size) * (30/div_size), 2),
            'abs_pos': d45_sign * 30 + (degree % div_size) * (30/div_size)
        }
    return d45

def calculate_d60_shashtyamsa(chart_data: Dict) -> Dict:
    """D60 - Shashtyamsa (General/Subtle) - Counts from same sign"""
    d60 = {}
    div_size = 30.0 / 60
    for p_name, p_data in chart_data.items():
        if p_name == '_metadata' or not isinstance(p_data, dict) or 'abs_pos' not in p_data: continue
        sign_num = p_data['sign_num']
        degree = p_data['degree']
        div_idx = int(degree / div_size)
        
        d60_sign = (sign_num + div_idx) % 12
        d60[p_name] = {
            'name': p_data['name'],
            'sign': ZODIAC_SIGNS[d60_sign],
            'sign_num': d60_sign,
            'degree': round((degree % div_size) * (30/div_size), 2),
            'abs_pos': d60_sign * 30 + (degree % div_size) * (30/div_size)
        }
    return d60

def calculate_moon_chart(chart_data: Dict) -> Dict:
    """Moon Chart (Chandra Lagna) - D1 with Moon as Ascendant"""
    moon_sign = chart_data.get('moon', {}).get('sign_num', 0)
    res = {k: v for k, v in chart_data.items() if k != '_metadata'}
    res['ascendant'] = chart_data['moon'].copy()
    res['ascendant']['name'] = 'Chandra Lagna'
    return res

def calculate_sun_chart(chart_data: Dict) -> Dict:
    """Sun Chart (Surya Lagna) - D1 with Sun as Ascendant"""
    sun_sign = chart_data.get('sun', {}).get('sign_num', 0)
    res = {k: v for k, v in chart_data.items() if k != '_metadata'}
    res['ascendant'] = chart_data['sun'].copy()
    res['ascendant']['name'] = 'Surya Lagna'
    return res

def calculate_arudha_lagna(chart_data: Dict) -> Dict:
    """Arudha Lagna (AL) Calculation"""
    # Simple version: AL = Lagna Lord pos from Lagna, then same distance from Lord
    # We need SIGN_LORDS from astrology.py, let's just use a local copy or import
    SIGN_LORDS_LOCAL = {0:'Mars',1:'Venus',2:'Mercury',3:'Moon',4:'Sun',5:'Mercury',
                        6:'Venus',7:'Mars',8:'Jupiter',9:'Saturn',10:'Saturn',11:'Jupiter'}
    
    asc_sign = chart_data.get('ascendant', {}).get('sign_num', 0)
    lord_name = SIGN_LORDS_LOCAL.get(asc_sign).lower()
    lord_sign = chart_data.get(lord_name, {}).get('sign_num', asc_sign)
    
    # Distance from Lagna to Lord
    dist = (lord_sign - asc_sign) % 12
    # Potential Arudha is dist from Lord
    al_sign = (lord_sign + dist) % 12
    
    # Parasara Exceptions:
    # 1. If Arudha falls in 1st house from starting point, take 10th therefrom
    if al_sign == asc_sign:
        al_sign = (al_sign + 9) % 12
    # 2. If Arudha falls in 7th house from starting point, take 4th therefrom
    elif (al_sign - asc_sign) % 12 == 6:
        al_sign = (al_sign + 3) % 12
    
    res = {k: v for k, v in chart_data.items() if k != '_metadata'}
    asc = chart_data['ascendant'].copy()
    asc['sign_num'] = al_sign
    asc['sign'] = ZODIAC_SIGNS[al_sign]
    asc['name'] = 'Arudha Lagna'
    asc['abs_pos'] = al_sign * 30
    res['ascendant'] = asc
    return res

def calculate_all_vargas(chart_data: Dict) -> Dict:
    """Calculate all varga charts and return a dictionary"""
    vargas = {
        'd1_chart': {k: v for k, v in chart_data.items() if k != '_metadata'},
        'moon_chart': calculate_moon_chart(chart_data),
        'sun_chart': calculate_sun_chart(chart_data),
        'arudha_chart': calculate_arudha_lagna(chart_data),
        'd2_chart': calculate_d2_hora(chart_data),
        'd3_chart': calculate_d3_drekkana(chart_data),
        'd4_chart': calculate_d4_chaturthamsa(chart_data),
        'd5_chart': calculate_d5_panchamsa(chart_data),
        'd6_chart': calculate_d6_shashtamsa(chart_data),
        'd7_chart': calculate_d7_explicit(chart_data),
        'd8_chart': calculate_d8_ashtamsa(chart_data),
        'd9_chart': calculate_varga(chart_data, 9, 'movable_fixed_dual'),
        'd10_chart': calculate_varga(chart_data, 10, 'odd_even'),
        'd11_chart': calculate_d11_rudramsa(chart_data),
        'd12_chart': calculate_varga(chart_data, 12, 'same'),
        'd16_chart': calculate_d16_shodasamsa(chart_data),
        'd20_chart': calculate_d20_vimsamsa(chart_data),
        'd24_chart': calculate_d24_siddhamsa(chart_data),
        'd27_chart': calculate_d27_nakshatramsa(chart_data),
        'd30_chart': calculate_d30_trimsamsa(chart_data),
        'd40_chart': calculate_d40_khavedamsa(chart_data),
        'd45_chart': calculate_d45_akshavedamsa(chart_data),
        'd60_chart': calculate_d60_shashtyamsa(chart_data)
    }
    return vargas
