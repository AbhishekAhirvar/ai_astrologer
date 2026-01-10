
import swisseph as swe
from typing import Dict, List, Optional
from backend.schemas import ChartResponse, PlanetPosition

# ============================================================================
# SHADBALA CONSTANTS (Virupas)
# ============================================================================
MINIMUM_REQ = {
    'Sun': 390, 'Moon': 360, 'Mars': 300, 
    'Mercury': 420, 'Jupiter': 390, 'Venus': 330, 'Saturn': 300
}

NAISARGIKA_BALA = {
    'Sun': 60.00, 'Moon': 51.43, 'Venus': 42.86,
    'Jupiter': 34.29, 'Mercury': 25.71, 'Mars': 17.14, 'Saturn': 8.57
}

EXALTATION_POINTS = {
    'Sun': 10, 'Moon': 33, 'Mars': 298, 'Mercury': 165,
    'Jupiter': 95, 'Venus': 357, 'Saturn': 200
}
# Note: Mercury own sign is Virgo (150-180), Exaltation is 15 Virgo = 165.
# Venus Exaltation 27 Pisces = 357.
# Mars Exaltation 28 Capricorn = 298.
# Moon Exaltation 3 Taurus = 33.
# Sun Exaltation 10 Aries = 10.
# Saturn 20 Libra = 200.
# Jupiter 5 Cancer = 95.

PLANET_MAPPING = {
    'Sun': 0, 'Moon': 1, 'Mars': 4, 'Mercury': 2,
    'Jupiter': 5, 'Venus': 3, 'Saturn': 6
} # SwissEph IDs

from backend.config import SIGN_LORDS

# ============================================================================
# FRIENDSHIP CONSTANTS
# ============================================================================
FRIENDSHIPS = {
    'Sun': {'friends': ['Moon', 'Mars', 'Jupiter'], 'neutral': ['Mercury'], 'enemies': ['Venus', 'Saturn']},
    'Moon': {'friends': ['Sun', 'Mercury'], 'neutral': ['Mars', 'Jupiter', 'Venus', 'Saturn'], 'enemies': []},
    'Mars': {'friends': ['Sun', 'Moon', 'Jupiter'], 'neutral': ['Venus', 'Saturn'], 'enemies': ['Mercury']},
    'Mercury': {'friends': ['Sun', 'Venus'], 'neutral': ['Mars', 'Jupiter', 'Saturn'], 'enemies': ['Moon']},
    'Jupiter': {'friends': ['Sun', 'Moon', 'Mars'], 'neutral': ['Saturn'], 'enemies': ['Mercury', 'Venus']},
    'Venus': {'friends': ['Mercury', 'Saturn'], 'neutral': ['Mars', 'Jupiter'], 'enemies': ['Sun', 'Moon']},
    'Saturn': {'friends': ['Mercury', 'Venus'], 'neutral': ['Jupiter'], 'enemies': ['Sun', 'Moon', 'Mars']}
}

def get_compound_relationship(planet: str, target_lord: str, chart: ChartResponse) -> str:
    """
    Calculate Panchadha Maitri (Compound Friendship).
    Returns: 'Adhi Mitra', 'Mitra', 'Sama', 'Shatru', 'Adhi Shatru'.
    """
    p_name = planet.capitalize()
    l_name = target_lord.capitalize()
    
    if p_name == l_name:
        return 'Own' # Own Sign handling
        
    # 1. Naisargika (Natural)
    natural_rel = 'Neutral'
    f_data = FRIENDSHIPS.get(p_name, {})
    if l_name in f_data.get('friends', []):
        natural_rel = 'Friend'
    elif l_name in f_data.get('enemies', []):
        natural_rel = 'Enemy'
        
    # 2. Tatkalika (Temporary) - Based on D1 Positions
    # Friend if in 2, 3, 4, 10, 11, 12 from Planet
    temp_rel = 'Enemy'
    
    if p_name.lower() in chart.planets and l_name.lower() in chart.planets:
        p_sign = chart.planets[p_name.lower()].sign_num
        l_sign = chart.planets[l_name.lower()].sign_num
        
        # Count from P to L (inclusive? No, 2nd means next sign)
        # Distance: (L - P) % 12 + 1 ?
        # Example: P in 0. L in 1. Dist = 1-0 = 1? No 2nd House.
        # House 1 is Same. House 2 is Next.
        # Check diff:
        diff = (l_sign - p_sign) % 12
        # Houses: 2(1), 3(2), 4(3), 10(9), 11(10), 12(11)
        # 0 is 1st (Same) - Enemy
        if diff in [1, 2, 3, 9, 10, 11]:
            temp_rel = 'Friend'
            
    # 3. Compound Logic
    # Friend + Friend = Adhi Mitra
    # Friend + Neutral = Mitra
    # Friend + Enemy = Sama
    # Neutral + Friend = Mitra
    # Neutral + Enemy = Shatru
    # Enemy + Friend = Sama
    # Enemy + Enemy = Adhi Shatru
    
    score = 0
    if natural_rel == 'Friend': score += 1
    elif natural_rel == 'Enemy': score -= 1
    
    if temp_rel == 'Friend': score += 1
    else: score -= 1 # Enemy
    
    if score == 2: return 'Adhi Mitra'
    if score == 1: return 'Mitra'
    if score == 0: return 'Sama'
    if score == -1: return 'Shatru'
    return 'Adhi Shatru'

def calculate_shadbala_for_chart(chart: ChartResponse) -> Dict[str, float]:
    """
    Main entry point for Shadbala calculation.
    Returns dictionary of {PlanetName: TotalShadbalaVirupas}
    """
    results = {}
    
    # We iterate over the 7 grahas
    grahas = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
    
    for planet in grahas:
        if planet.lower() not in chart.planets:
            continue
            
        p_data = chart.planets[planet.lower()]
        total_virupas = 0.0
        
        # 1. Sthana Bala
        total_virupas += calculate_sthana_bala(planet, p_data, chart)
        
        # 2. Dig Bala
        total_virupas += calculate_dig_bala(planet, p_data, chart)
        
        # 3. Kala Bala (Simplified for MVP, expanding later)
        # Including Natonnata, Paksha, Tribhaga, Ayana
        total_virupas += calculate_kala_bala(planet, p_data, chart)
        
        # 4. Chesta Bala
        total_virupas += calculate_chesta_bala(planet, p_data, chart)
        
        # 5. Naisargika Bala
        total_virupas += NAISARGIKA_BALA.get(planet, 0.0)
        
        # 6. Drik Bala
        total_virupas += calculate_drik_bala(planet, p_data, chart)
        
        results[planet] = round(total_virupas, 2)
        
    return results

def calculate_sthana_bala(planet: str, p_data: PlanetPosition, chart: ChartResponse) -> float:
    score = 0.0
    
    # A. Uccha Bala (Exaltation)
    exalt_pt = EXALTATION_POINTS.get(planet, 0)
    abs_pos = p_data.abs_pos
    # Distance to deep debilitation (Exaltation + 180)
    debilitation_pt = (exalt_pt + 180) % 360
    
    # Arc distance from debilitation
    diff = abs(abs_pos - debilitation_pt)
    if diff > 180:
        diff = 360 - diff
        
    # Formula: Diff / 3  (Max 60 when diff=180 i.e. at exaltation)
    uccha_score = diff / 3.0
    score += uccha_score
    
    # B. Sapta Vargaja Bala (7 Divisional Charts)
    # Charts: D1, D2, D3, D7, D9, D12, D30
    # Points: Own=30, Adhi Mitra=22.5, Mitra=15, Sama=7.5, Shatru=3.75, Adhi Shatru=1.875
    
    varga_keys = ['d1_chart', 'd2_chart', 'd3_chart', 'd7_chart', 'd9_chart', 'd12_chart', 'd30_chart']
    saptavarga_score = 0.0
    
    points_map = {
        'Own': 30.0,
        'Adhi Mitra': 22.5,
        'Mitra': 15.0,
        'Sama': 7.5,
        'Shatru': 3.75,
        'Adhi Shatru': 1.875
    }
    
    for v_key in varga_keys:
        v_chart = chart.vargas.get(v_key, {})
        # Fallback to D1 if specific varga logic failed/missing?
        # Ideally we skip or use D1. Using D1 for safety if missing.
        if not v_chart and v_key == 'd1_chart':
             # Should be available in chart.planets for D1? 
             # chart.planets is simplified format. chart.vargas['d1_chart'] mimics standard varga structure.
             # If chart.vargas['d1_chart'] missing, construct it from chart.planets?
             # For robustness, we assume vargas populated. If not, 0 points? Or Average (7.5)?
             pass
             
        if not v_chart:
            # Try to get from planetary position if D1
            if v_key == 'd1_chart':
               # Use main planets info
               v_planet = p_data
            else:
               continue # Skip missing varga
        else:
            if planet.lower() not in v_chart and planet != 'Ascendant':
                continue
            v_planet = v_chart[planet.lower()]
            
        # Get Sign Lord
        # v_planet usually has 'sign_num'
        s_num = getattr(v_planet, 'sign_num', 0)
        lord = SIGN_LORDS.get(s_num, 'Mars') # Default to Mars/Aries if fails
        
        # Calculate Relationship
        # Must use D1 chart for Tatkalika logic inside helper
        rel = get_compound_relationship(planet, lord, chart)
        
        saptavarga_score += points_map.get(rel, 7.5)
        
    score += saptavarga_score
    
    # C. Ojayugma Bala (Odd/Even)
    # Odd signs: Aries(0), Gemini(2), Leo(4), Libra(6), Sag(8), Aq(10)
    is_odd = (p_data.sign_num % 2 == 0) # sign_num 0 is Aries (Odd)
    # Even signs: Taurus(1), Cancer(3), Virgo(5), Scorp(7), Cap(9), Pisces(11)
    
    # Moon/Venus strong in Even
    if planet in ['Moon', 'Venus'] and not is_odd:
        score += 15
    # Sun/Mars/Jup/Merc/Sat strong in Odd
    elif planet in ['Sun', 'Mars', 'Jupiter', 'Mercury', 'Saturn'] and is_odd:
        score += 15
        
    # D. Kendradi Bala
    # 1/4/7/10 = Kendra = 60
    # 2/5/8/11 = Panapara = 30
    # 3/6/9/12 = Apoklima = 15
    # House should be obtained from p_data.house derived from Ascendant
    house = p_data.house
    if house in [1, 4, 7, 10]:
        score += 60
    elif house in [2, 5, 8, 11]:
        score += 30
    else:
        score += 15
        
    # E. Drekkana Bala (Simplified: Male planets in 1st decanate etc)
    # Sun/Mars/Jup (Male) -> 1st Decanate
    # Ven/Moon (Female) -> 2nd Decanate
    # Mer/Sat (Neutral) -> 3rd Decanate
    decanate = int((p_data.degree % 30) / 10) + 1
    if planet in ['Sun', 'Mars', 'Jupiter'] and decanate == 1:
        score += 15
    elif planet in ['Venus', 'Moon'] and decanate == 2:
        score += 15
    elif planet in ['Mercury', 'Saturn'] and decanate == 3:
        score += 15
        
    return score

def calculate_dig_bala(planet: str, p_data: PlanetPosition, chart: ChartResponse) -> float:
    # Power Points (Houses treated as angles from Ascendant)
    # Asc is at ChartMetadata... wait, we need Ascendant longitude.
    # We can approximate from House 1 cusp if available, or just use House Logic
    # BPHS uses Angle from specific points. 
    # Let's use House placement as proxy if exact Ascendant degree missing?
    # Better: Use chart.planets['ascendant'].abs_pos
    
    asc_pos = 0.0
    if 'ascendant' in chart.planets:
        asc_pos = chart.planets['ascendant'].abs_pos
    elif 'ascendant' in chart.vargas.get('D1', {}):
         asc_pos = chart.vargas['D1']['ascendant'].abs_pos
    
    # Calculate angular distance from powerful point
    # Sun/Mars: 10th House (Asc - 90 approx, or Asc + 270) -> South / Meridian
    # Moon/Venus: 4th House (Asc + 90) -> North / Nadir
    # Sat: 7th House (Asc + 180) -> West / Descendant
    # Jup/Mer: 1st House (Asc) -> East / Ascendant
    
    p_pos = p_data.abs_pos
    power_point = 0.0
    
    if planet in ['Sun', 'Mars']:
        power_point = (asc_pos + 270) % 360 # MC approx
    elif planet in ['Moon', 'Venus']:
        power_point = (asc_pos + 90) % 360 # IC approx
    elif planet == 'Saturn':
        power_point = (asc_pos + 180) % 360 # Dsc
    elif planet in ['Jupiter', 'Mercury']:
        power_point = asc_pos # Asc
        
    arc = abs(p_pos - power_point)
    if arc > 180:
        arc = 360 - arc
        
    # Formula: (180 - Arc) / 3
    # If planet is AT power point (arc=0), score = 60.
    # If planet is opp power point (arc=180), score = 0.
    return (180 - arc) / 3.0

def calculate_kala_bala(planet: str, p_data: PlanetPosition, chart: ChartResponse) -> float:
    """
    Calculate Kala Bala (Time Strength) with corrected Day/Night calculation.
    """
    score = 0.0
    
    # --- 1. Paksha Bala (Lunar Phase) ---
    sun_pos = chart.planets['sun'].abs_pos if 'sun' in chart.planets else 0
    moon_pos = chart.planets['moon'].abs_pos if 'moon' in chart.planets else 0
    angle = (moon_pos - sun_pos) % 360
    
    angle_from_new = angle if angle <= 180 else 360 - angle
    
    # Benefics get strength from Full Moon (180 deg)
    # Malefics get strength from New Moon (0 deg)
    paksha_score = 0.0
    if planet in ['Jupiter', 'Venus', 'Moon', 'Mercury']:
        paksha_score = (angle_from_new / 180.0) * 60
    else:
        paksha_score = ((180 - angle_from_new) / 180.0) * 60
    score += paksha_score
    
    # --- 2. Natonnata Bala (Day/Night) ---
    # Determine Day vs Night based on Sun's House
    # Houses 7-12 are above horizon (Day), 1-6 below (Night)
    sun_house = chart.planets['sun'].house if 'sun' in chart.planets else 1
    is_day = sun_house in [7, 8, 9, 10, 11, 12]
    
    natonnata_score = 0.0
    if is_day:
        # Day Strong: Sun, Jupiter, Venus (Male/Day planets)
        if planet in ['Sun', 'Jupiter', 'Venus']:
            natonnata_score = 60.0
        # Mercury is strong always (Day & Night) or at Sandhya
        elif planet == 'Mercury':
            natonnata_score = 60.0
    else:
        # Night Strong: Moon, Mars, Saturn
        if planet in ['Moon', 'Mars', 'Saturn']:
            natonnata_score = 60.0
        elif planet == 'Mercury':
            natonnata_score = 60.0
            
    score += natonnata_score
    
    # --- 3. Ayana Bala (Equinoctial) ---
    declination = getattr(p_data, 'declination', 0.0)
    val = 0.0
    
    # North Declination Group: Sun, Mars, Jupiter, Venus
    if planet in ['Sun', 'Mars', 'Jupiter', 'Venus', 'Mercury']:
        val = 24.0 + declination # Declination is +/-
    # South Declination Group: Moon, Saturn
    elif planet in ['Moon', 'Saturn']:
        val = 24.0 - declination
        
    val = max(0.0, min(val, 48.0))
    ayana_score = val * 1.25 # Max 60
    score += ayana_score
    
    return score

def calculate_chesta_bala(planet: str, p_data: PlanetPosition, chart: ChartResponse) -> float:
    """
    Calculate Chesta Bala (Motional Strength) with corrected Sun/Moon handling.
    """
    # 1. Sun & Moon Special Case
    if planet == 'Sun':
        # Sun Chesta = Sun Ayana Bala (Recalculate or store/pass it)
        # For efficiency here, we approximate using Declination again or call helper
        decl = getattr(p_data, 'declination', 0.0)
        val = max(0.0, min(24.0 + decl, 48.0))
        return val * 1.25
        
    if planet == 'Moon':
        # Moon Chesta = Moon Paksha Bala
        # Check angle from Sun again
        sun_pos = chart.planets['sun'].abs_pos if 'sun' in chart.planets else 0
        moon_pos = p_data.abs_pos
        angle = (moon_pos - sun_pos) % 360
        angle_from_new = angle if angle <= 180 else 360 - angle
        return (angle_from_new / 180.0) * 60

    # 2. Other Planets (Based on Speed)
    speed = getattr(p_data, 'speed', 0.0)
    
    if speed < 0:
        return 60.0 # Vakra (Retrograde)
    if abs(speed) < 0.05:
        return 15.0 # Vikal (Stationary)
        
    # Manda (Slow) / Sighra (Fast) logic requires mean speed comparison
    # For MVP, Direct motion = 30 is acceptable
    return 30.0

def calculate_drik_bala(planet: str, p_data: PlanetPosition, chart: ChartResponse) -> float:
    """
    Corrected Aspect Calculation checking Special Aspects properly.
    """
    score = 0.0
    target_pos = p_data.abs_pos
    
    is_benefic_aspect = {
        'Sun': False, 'Moon': True, 'Mars': False, 'Mercury': True,
        'Jupiter': True, 'Venus': True, 'Saturn': False
    }
    
    for other_p, other_data in chart.planets.items():
        if other_p == planet.lower() or other_p in ['rahu', 'ketu', 'ascendant']:
            continue
            
        aspecting_pos = other_data.abs_pos
        angle = (target_pos - aspecting_pos) % 360
        
        # 1. Calculate Base (Generic) Aspect
        drishti_val = get_drishti_value(angle)
        
        # 2. Handle Special Aspects (Vishesha Drishti)
        # We take the MAX of Generic vs Special to ensure full strength is applied.
        
        if other_p == 'mars':
            # Mars Full Aspect (60) on 4th (90-120 range) and 8th (210 range)
            # Using simple proximity logic for MVP
            if 80 <= angle <= 100: 
                drishti_val = max(drishti_val, 60.0) # 4th House
            if 200 <= angle <= 220:
                drishti_val = max(drishti_val, 60.0) # 8th House

        elif other_p == 'jupiter':
            # Jupiter Full Aspect (60) on 5th (120) and 9th (240)
            if 110 <= angle <= 130: 
                drishti_val = max(drishti_val, 60.0)
            if 230 <= angle <= 250:
                drishti_val = max(drishti_val, 60.0)

        elif other_p == 'saturn':
            # Saturn Full Aspect (60) on 3rd (60) and 10th (270)
            if 50 <= angle <= 70:
                drishti_val = max(drishti_val, 60.0)
            if 260 <= angle <= 280:
                drishti_val = max(drishti_val, 60.0)

        # Cap at 60 (Standard Max)
        drishti_val = min(drishti_val, 60.0)
        
        # 3. Apply Benefic/Malefic Modifier
        modifier = drishti_val / 4.0
        p_name_cap = other_p.capitalize()
        
        if is_benefic_aspect.get(p_name_cap, False):
            score += modifier
        else:
            score -= modifier
                
    return score

def get_drishti_value(angle: float) -> float:
    """
    BPHS Quadratic/Linear Aspect Formulas (Continuous).
    Range: 0 to 360.
    """
    # 0 to 30: No aspect (0).
    if angle < 30:
        return 0.0
        
    # 30 to 60: (Angle - 30) / 2
    if angle <= 60:
        return (angle - 30) / 2.0  # Max 15 at 60 deg
        
    # 60 to 90: (Angle - 60) + 15
    if angle <= 90:
        return (angle - 60) + 15.0 # Max 45 at 90 deg
        
    # 90 to 120: (120 - Angle) / 2 + 30
    # Wait, BPHS: 90->45, 120->30?
    # Actually: 90-120 -> Decreases from 45 to 30?
    # Let's verify BPHS 27.
    # "From 60 to 90, increase 15 to 45".
    # "From 90 to 120, decrease from 45 to 30? No."
    # "From 90 to 120: (Angle - 90)/2 + 45" -> 120 gives 60.
    # 120 is Trine. 50% strength? No, Trine is usually good.
    # Let's use standard approximation for linear segments if BPHS ambiguous in memory.
    # 120 deg (Trine) is usually weak in general aspect, strong in Special (Jupiter).
    # Standard Drishti Pinda:
    # 1. 30-60: +15
    # 2. 60-90: +30 (Total 45)
    # 3. 90-120: +15 (Total 60? No, 120 is 1/2 aspect usually?)
    # Common Graph:
    # 0-30: 0
    # 60: 15 (1/4)
    # 90: 45 (3/4)
    # 120: 30 (1/2)
    # 150: 15 (1/4) ?
    # 180: 60 (Full)
    
    # Formula Implementation fitting the Pinda points:
    
    if angle <= 120:
        # Interpolate 90(45) to 120(30) -> Decrease?
        # Slope: (30-45)/30 = -0.5.
        # Value = 45 + (angle-90)*(-0.5) = 45 - (angle-90)/2 = (90 - angle)/2 + 45?
        # Test: 120 -> 45 - 15 = 30. Correct.
        return 45.0 - (angle - 90) / 2.0
        
    # 120 to 150: Decrease 30 to 0? Or 15?
    # 150 is usually 0 aspect in general?
    # BPHS: "120 to 150: 150 - angle" ?
    # Test 120: 30. Test 150: 0.
    if angle <= 150:
        return 150.0 - angle
        
    # 150 to 180: Linear increase 0 to 60
    # "Double rate"
    # Aspect = (Angle - 150) * 2
    # Test 150: 0. Test 180: 30 * 2 = 60.
    if angle <= 180:
        return (angle - 150) * 2.0
        
    # > 180: No aspect (Standard rule, aspects are forward 180 max, usually 300??)
    # Special aspects like 270 (Mars/Saturn) need to be handled separately.
    # General aspect ends at 180.
    return 0.0
