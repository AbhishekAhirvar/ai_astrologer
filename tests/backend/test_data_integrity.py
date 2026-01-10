
import pytest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.astrology import generate_vedic_chart

def test_physics_data_population():
    """
    Verify that Speed and Declination are correctly populated 
    from Swiss Ephemeris and are not just default 0.0.
    """
    # Use a date where we know planets are moving and declination varies
    # Jan 1st 2024
    chart = generate_vedic_chart(
        "Physics Test", 2024, 1, 1, 12, 0, "London", 51.5, -0.1
    )
    
    planets = chart.planets
    
    # Check Sun (Should have speed ~1 deg/day, Declination ~23 deg S)
    sun = planets['sun']
    assert sun.speed != 0.0, "Sun speed is 0.0"
    assert 0.9 <= sun.speed <= 1.1, f"Sun speed {sun.speed} out of expected range ~1.0"
    assert sun.declination != 0.0, "Sun declination is 0.0"
    # Jan 1 is near Winter Solstice (Dec 21), Declination should be near -23.
    assert -24.0 <= sun.declination <= -22.0, f"Sun declination {sun.declination} unexpected for Jan 1"
    
    # Check Moon (Speed ~13 deg/day)
    moon = planets['moon']
    assert moon.speed != 0.0
    assert 11.0 <= moon.speed <= 15.0, f"Moon speed {moon.speed} unexpected"
    
    # Check Retrograde Planet?
    # Hard to predict retrograde without exact date knowledge, 
    # but we can check boolean consistency.
    for p_name, p in planets.items():
        if p.speed < 0:
            assert p.is_retrograde is True, f"{p_name} has neg speed but is_retrograde=False"
        else:
            assert p.is_retrograde is False, f"{p_name} has pos speed but is_retrograde=True"

def test_node_physics():
    """Verify Nodes (Rahu/Ketu) have data"""
    chart = generate_vedic_chart("Node Test", 2024, 1, 1, 12, 0, "London", 51.5, -0.1)
    rahu = chart.planets['rahu']
    ketu = chart.planets['ketu']
    
    # Nodes typically move retrograde (-0.05 deg/day approx, or -3 mins/day)
    # Speed might be very small negative.
    assert rahu.speed != 0.0
    assert ketu.speed != 0.0
    
    # Check approximation logic (Ketu = -Rahu Declination)
    # Use pytest.approx because floating point sign flip might drift slightly? 
    # Actually I implemented logic as `declination: -chart_data['rahu']['declination']`.
    # So it should be exact.
    assert ketu.declination == -rahu.declination
    assert ketu.speed == rahu.speed
    assert ketu.is_retrograde == rahu.is_retrograde
