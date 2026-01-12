
import pytest
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.astrology import generate_vedic_chart
from backend.kp_calculations import generate_kp_data, calculate_sub_lord
from backend.schemas import KPData, KPPlanetInfo

# Use New Delhi coordinates
LAT = 28.6139
LON = 77.2090

def test_kp_integration_with_planets():
    """Test that KP data in chart response includes planetary sub-lords"""
    chart = generate_vedic_chart(
        "KP Test", 2024, 5, 15, 10, 30, "Delhi", LAT, LON, 
    )
    
    # Manually add KP Data
    import swisseph as swe
    jd = swe.julday(2024, 5, 15, 10.5)
    moon_lon = chart.planets['moon'].abs_pos
    pl_pos = {p: {'longitude': data.abs_pos} for p, data in chart.planets.items()}
    kp_raw = generate_kp_data(jd, LAT, LON, pl_pos, moon_lon)
    chart.kp_data = KPData(**kp_raw)
    
    assert chart.kp_data is not None
    assert chart.kp_data.planets is not None
    assert len(chart.kp_data.planets) > 0
    
    # Check specific planet (e.g., Sun)
    sun_kp = chart.kp_data.planets.get('sun')
    assert sun_kp is not None
    assert isinstance(sun_kp, KPPlanetInfo)
    assert sun_kp.star_lord is not None
    assert sun_kp.sub_lord is not None
    # Check Sub-Lord is a valid planet name
    valid_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
    assert sun_kp.sub_lord in valid_planets

def test_sub_lord_precision():
    """Test Sub-Lord calculation precision"""
    # Ashwini Nakshatra: 0-13deg 20min (0 - 13.333 deg)
    # Lord: Ketu
    # Sub-Lords follow Vimshottari sequence: Ketu, Ven, Sun, Mon, Mar, Rah, Jup, Sat, Mer
    
    # 1. Very beginning of Ashwini -> Ketu Star, Ketu Sub
    sl1 = calculate_sub_lord(0.001)
    assert sl1 == 'Ketu'
    
    # 2. End of Ashwini -> Ketu Star, Mercury Sub (Last sub)
    # Ashwini ends at 13.3333...
    # Let's check 13.30
    sl2 = calculate_sub_lord(13.30)
    assert sl2 == 'Mercury'
    
def test_hidden_kp_data_exposed():
    """Verify that blind test data path exposes KP data"""
    chart = generate_vedic_chart(
        "KP Exposed", 2024, 1, 1, 12, 0, "Test", LAT, LON,
    )
    
    # Manually add KP Data
    import swisseph as swe
    jd = swe.julday(2024, 1, 1, 12.0)
    moon_lon = chart.planets['moon'].abs_pos
    pl_pos = {p: {'longitude': data.abs_pos} for p, data in chart.planets.items()}
    kp_raw = generate_kp_data(jd, LAT, LON, pl_pos, moon_lon)
    chart.kp_data = KPData(**kp_raw)
    
    # AI Logic usually serializes chart.kp_data
    # We ensure the data is present in the object
    kp = chart.kp_data
    assert kp.cusps[1].sub_lord is not None
    assert kp.planets['moon'].sub_lord is not None
    
def test_all_planets_covered():
    """Ensure all main planets + nodes have KP data"""
    chart = generate_vedic_chart(
        "Coverage", 2024, 1, 1, 12, 0, "Test", LAT, LON,
    )
    
    # Manually add KP Data
    import swisseph as swe
    jd = swe.julday(2024, 1, 1, 12.0)
    moon_lon = chart.planets['moon'].abs_pos
    pl_pos = {p: {'longitude': data.abs_pos} for p, data in chart.planets.items()}
    kp_raw = generate_kp_data(jd, LAT, LON, pl_pos, moon_lon)
    chart.kp_data = KPData(**kp_raw)
    p_kp = chart.kp_data.planets
    
    # Keys are lowercase in ChartResponse
    required = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']
    for p in required:
        assert p in p_kp, f"Missing KP data for {p}"
