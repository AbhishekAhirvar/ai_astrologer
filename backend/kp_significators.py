"""
KP Significator Engine

This module implements the 4-fold KP significator rules to pre-compute
which houses each planet signifies. This is the core of the "Compute Once, Send Results"
architecture for token-optimized AI payloads.

The 4 levels of signification (in order of strength):
1. Planets in the star of the occupant of a house
2. Occupant of a house
3. Planets in the star of the owner of a house
4. Owner of a house sign
"""
from typing import Dict, List, Optional, Set
from backend.schemas import ChartResponse, KPPlanetInfo

# Sign to Lord mapping (Vedic rulership)
SIGN_LORDS: Dict[str, str] = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
}

# Short codes for planets and signs
PLANET_CODES: Dict[str, str] = {
    "Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
    "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke",
    "Ascendant": "Asc"
}

SIGN_CODES: Dict[int, str] = {
    0: "Ari", 1: "Tau", 2: "Gem", 3: "Can", 4: "Leo", 5: "Vir",
    6: "Lib", 7: "Sco", 8: "Sag", 9: "Cap", 10: "Aqu", 11: "Pis"
}

SIGN_NAMES: Dict[int, str] = {
    0: "Aries", 1: "Taurus", 2: "Gemini", 3: "Cancer", 4: "Leo", 5: "Virgo",
    6: "Libra", 7: "Scorpio", 8: "Sagittarius", 9: "Capricorn", 10: "Aquarius", 11: "Pisces"
}


def get_house_occupants(chart: ChartResponse) -> Dict[int, List[str]]:
    """
    Returns a mapping of house number -> list of planet names occupying that house.
    """
    occupants: Dict[int, List[str]] = {i: [] for i in range(1, 13)}
    
    for planet_name, planet_data in chart.planets.items():
        if planet_name.lower() == "ascendant":
            continue
        house = getattr(planet_data, 'house', None)
        if house and 1 <= house <= 12:
            occupants[house].append(planet_name.capitalize())
    
    return occupants


def get_house_owners(chart: ChartResponse) -> Dict[int, str]:
    """
    Returns a mapping of house number -> owner planet name.
    Based on the sign on the cusp of each house.
    """
    owners: Dict[int, str] = {}
    
    for house_num, house_data in chart.houses.items():
        sign_name = getattr(house_data, 'sign', None)
        if sign_name and sign_name in SIGN_LORDS:
            owners[house_num] = SIGN_LORDS[sign_name]
    
    return owners


def get_star_lord_map(chart: ChartResponse) -> Dict[str, str]:
    """
    Returns a mapping of planet name -> star lord name.
    Uses KP data if available.
    """
    star_lords: Dict[str, str] = {}
    
    if chart.kp_data and chart.kp_data.planets:
        for planet_name, kp_info in chart.kp_data.planets.items():
            star_lords[planet_name.capitalize()] = kp_info.star_lord
    
    return star_lords


def calculate_planet_significators(
    planet_name: str, 
    chart: ChartResponse,
    house_occupants: Optional[Dict[int, List[str]]] = None,
    house_owners: Optional[Dict[int, str]] = None,
    star_lord_map: Optional[Dict[str, str]] = None
) -> List[int]:
    """
    Calculates the house significators for a given planet using KP 4-fold rules.
    
    Args:
        planet_name: Name of the planet (e.g., "Sun", "Moon")
        chart: The complete chart response with KP and house data
        house_occupants: Pre-computed house occupants (optional, for performance)
        house_owners: Pre-computed house owners (optional, for performance)
        star_lord_map: Pre-computed star lord map (optional, for performance)
    
    Returns:
        Sorted, deduplicated list of house numbers this planet signifies.
        Example: [2, 7, 11]
    """
    significators: Set[int] = set()
    
    planet_key = planet_name.capitalize()
    
    # Use pre-computed data if provided, otherwise compute (for backward compatibility)
    if house_occupants is None:
        house_occupants = get_house_occupants(chart)
    if house_owners is None:
        house_owners = get_house_owners(chart)
    if star_lord_map is None:
        star_lord_map = get_star_lord_map(chart)
    
    # Get this planet's star lord
    planet_star_lord = star_lord_map.get(planet_key)
    
    # --- Level 1 & 2: Signification through Occupation ---
    # Check if this planet's star lord occupies any house
    if planet_star_lord:
        for house_num, occupants in house_occupants.items():
            if planet_star_lord in occupants:
                # Level 1: Planet in star of occupant signifies that house
                significators.add(house_num)
    
    # Level 2: Direct occupation
    planet_data = chart.planets.get(planet_key.lower()) or chart.planets.get(planet_key)
    if planet_data:
        house = getattr(planet_data, 'house', None)
        if house and 1 <= house <= 12:
            significators.add(house)
    
    # --- Level 3 & 4: Signification through Ownership ---
    # Check if this planet's star lord owns any house
    if planet_star_lord:
        for house_num, owner in house_owners.items():
            if owner == planet_star_lord:
                # Level 3: Planet in star of owner signifies that house
                significators.add(house_num)
    
    # Level 4: Direct ownership
    for house_num, owner in house_owners.items():
        if owner == planet_key:
            significators.add(house_num)
    
    return sorted(list(significators))


def build_optimized_planet_payload(chart: ChartResponse) -> Dict[str, List]:
    """
    Builds the optimized planet payload for AI context.
    
    Format: "Su": ["Pis", "Ven", "Sun", 395, [2, 7, 1]]
            [Sign, Star_Lord, Sub_Lord, Shadbala, [Significators]]
    
    Returns:
        Dictionary with 2-letter planet codes as keys.
    """
    payload: Dict[str, List] = {}
    
    # === PERFORMANCE: Pre-compute helper data ONCE ===
    house_occupants = get_house_occupants(chart)
    house_owners = get_house_owners(chart)
    star_lord_map = get_star_lord_map(chart)
    
    # Get Shadbala scores if available (normalize keys for consistent lookup)
    shadbala_scores: Dict[str, float] = {}
    if chart.shadbala and chart.shadbala.total_shadbala:
        shadbala_scores = {k.lower(): v for k, v in chart.shadbala.total_shadbala.items()}
    
    # Get KP data
    kp_planets: Dict[str, KPPlanetInfo] = {}
    if chart.kp_data and chart.kp_data.planets:
        kp_planets = chart.kp_data.planets
    
    planets_to_process = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu", "Ascendant"]
    
    for planet_name in planets_to_process:
        planet_code = PLANET_CODES.get(planet_name, planet_name[:2])
        
        # Get planet position
        planet_data = chart.planets.get(planet_name.lower()) or chart.planets.get(planet_name)
        if not planet_data:
            continue
        
        # Sign code
        sign_num = getattr(planet_data, 'sign_num', 1)
        sign_code = SIGN_CODES.get(sign_num, "?")
        
        # KP data (Star/Sub Lords)
        kp_info = kp_planets.get(planet_name.lower()) or kp_planets.get(planet_name)
        star_lord = PLANET_CODES.get(kp_info.star_lord, kp_info.star_lord[:2]) if kp_info else "?"
        sub_lord = PLANET_CODES.get(kp_info.sub_lord, kp_info.sub_lord[:2]) if kp_info else "?"
        
        # Shadbala (None for Rahu/Ketu) - use lowercase lookup
        strength = shadbala_scores.get(planet_name.lower())
        if strength:
            strength = round(strength, 1)
        
        # Significators (pass pre-computed data for performance)
        significators = calculate_planet_significators(
            planet_name, chart, house_occupants, house_owners, star_lord_map
        )
        
        payload[planet_code] = [sign_code, star_lord, sub_lord, strength, significators]
    
    return payload


def build_optimized_house_payload(chart: ChartResponse) -> Dict[str, List]:
    """
    Builds the optimized house cusp payload for AI context.
    
    Format: "1": ["Pis", "Rah"]
            [Cusp_Sign, Sub_Lord]
    
    Returns:
        Dictionary with house number strings as keys.
    """
    payload: Dict[str, List] = {}
    
    if not chart.kp_data or not chart.kp_data.cusps:
        return payload
    
    for house_num in range(1, 13):
        cusp = chart.kp_data.cusps.get(house_num)
        if cusp:
            sign_num = cusp.sign_num
            sign_code = SIGN_CODES.get(sign_num, "?")
            sub_lord = PLANET_CODES.get(cusp.sub_lord, cusp.sub_lord[:2]) if cusp.sub_lord else "?"
            
            payload[str(house_num)] = [sign_code, sub_lord]
    
    return payload
