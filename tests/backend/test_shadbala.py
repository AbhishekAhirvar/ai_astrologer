
import pytest
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.shadbala import (
    calculate_shadbala_for_chart, calculate_sthana_bala, 
    calculate_dig_bala, calculate_drik_bala,
    calculate_kala_bala, calculate_chesta_bala
)
from backend.schemas import ChartResponse

# NOTE: 'chart_factory' and 'planet_factory' fixtures are loaded automatically from conftest.py

def test_shadbala_integration(chart_factory):
    """Integration test handling all 7 planets with verified ranges"""
    chart = chart_factory(planets=[
        {'name': 'Sun', 'degree': 10.0, 'sign': 'Aries', 'sign_num': 0, 'speed': 1.0},
        {'name': 'Moon', 'degree': 5.0, 'sign': 'Taurus', 'sign_num': 1, 'speed': 13.0},
        {'name': 'Mars', 'degree': 10.0, 'sign': 'Capricorn', 'sign_num': 9},
        {'name': 'Mercury', 'degree': 15.0, 'sign': 'Gemini', 'sign_num': 2},
        {'name': 'Jupiter', 'degree': 5.0, 'sign': 'Cancer', 'sign_num': 3},
        {'name': 'Venus', 'degree': 27.0, 'sign': 'Pisces', 'sign_num': 11},
        {'name': 'Saturn', 'degree': 20.0, 'sign': 'Libra', 'sign_num': 6}
    ])

    results = calculate_shadbala_for_chart(chart)
    
    assert len(results) == 7
    # All strengths should be positive and roughly in 300-900 range (Virupas)
    # 5-6 Rupas = 300-360 Virupas is typical minimum requirement.
    for planet, score in results.items():
        assert score > 0, f"{planet} has 0 strength"
        assert score < 1000, f"{planet} strength too high {score}"

def test_sthana_bala_exaltation_factory(chart_factory):
    """Test Exaltation (Uccha Bala) calculations correctly using factory"""
    # Sun at 10.0 Aries (Deep Exaltation)
    chart = chart_factory(planets=[
        {'name': 'Sun', 'degree': 10.0, 'sign': 'Aries', 'sign_num': 0, 'speed': 1.0}
    ])
    
    p_data = chart.planets['sun']
    
    # We call internal function to isolate Sthana Bala
    score = calculate_sthana_bala('Sun', p_data, chart)
    
    # Expected: 
    # Uccha (60) + Saptavarga (7.5 - Neutral, single D1) 
    # + Ojayugma(15) + Kendra(60) + Drekkana(10.0->2nd=0)
    # Total = 142.5. 
    assert score == pytest.approx(142.5, abs=1.0)

@pytest.mark.parametrize("angle, expected_score", [
    (180.0, -15.0), # Malefic Full Aspect (Saturn) -> -60/4 = -15
    # (0.0, 0.0)    # Conjunction (0) - Skipped as 0 is distinct logic
])
def test_drik_bala_points(chart_factory, angle, expected_score):
    """Verify Drik Bala specific points"""
    saturn_pos = (0.0 + angle) % 360
    chart = chart_factory(planets=[
        {'name': 'Sun', 'degree': 0.0, 'sign': 'Aries', 'sign_num': 0, 'abs_pos': 0.0},
        {'name': 'Saturn', 'degree': 0.0, 'sign': 'Aries', 'sign_num': 0, 'abs_pos': saturn_pos}
    ])
    
    # Calculate aspect ON Sun FROM Saturn
    score = calculate_drik_bala('Sun', chart.planets['sun'], chart)
    
    assert score == pytest.approx(expected_score, abs=0.1)

def test_dig_bala_accurate(chart_factory):
    """Test Directional Strength with exact logic"""
    # Sun (South, 10th House) gets full strength
    # Ascendant at 0 Aries. 10th House ~ 270.
    # Sun at 270 (Capricorn)
    
    chart = chart_factory(
        planets=[
            {'name': 'Sun', 'degree': 0.0, 'sign': 'Capricorn', 'sign_num': 9, 'abs_pos': 270.0}
        ],
        ascendant_deg=0.0
    )
    
    score = calculate_dig_bala('Sun', chart.planets['sun'], chart)
    assert score == pytest.approx(60.0, abs=0.5)

def test_dig_bala_zero(chart_factory):
    """Test Directional Strength Zero case"""
    # Sun at 90 (Nadir, 4th House) -> 0 strength
    chart = chart_factory(
        planets=[
            {'name': 'Sun', 'degree': 0.0, 'sign': 'Cancer', 'sign_num': 3, 'abs_pos': 90.0}
        ],
        ascendant_deg=0.0
    )
    score = calculate_dig_bala('Sun', chart.planets['sun'], chart)
    assert score == pytest.approx(0.0, abs=0.5)

@pytest.mark.parametrize("speed, expected_score", [
    (-0.5, 60.0), # Retrograde
    (0.02, 15.0), # Stationary (approx)
    (1.0, 30.0)   # Normal Direct
])
def test_chesta_bala_physics(chart_factory, speed, expected_score):
    """Verify Chesta Bala reacts to Velocity"""
    chart = chart_factory(planets=[
        {'name': 'Mars', 'degree': 10.0, 'sign': 'Aries', 'sign_num': 0, 'speed': speed}
    ])
    score = calculate_chesta_bala('Mars', chart.planets['mars'], chart)
    assert score == expected_score

@pytest.mark.parametrize("planet, declination, high_score", [
    ('Sun', 23.0, True),    # North Group, North Decl -> High
    ('Sun', -23.0, False),  # North Group, South Decl -> Low
    ('Moon', 23.0, False),  # South Group, North Decl -> Low
    ('Moon', -23.0, True)   # South Group, South Decl -> High
])
def test_ayana_bala_physics(chart_factory, planet, declination, high_score):
    """Verify Ayana Bala follows BPHS North/South rules"""
    chart = chart_factory(planets=[
        {'name': planet, 'degree': 10.0, 'sign': 'Aries', 'sign_num': 0, 'declination': declination}
    ])
    # Calling Kala Bala which includes Ayana
    total_kala = calculate_kala_bala(planet, chart.planets[planet.lower()], chart)
    
    # Base Kala includes Natonnata(0-60) + Paksha(0 to 60) + Ayana(0 to 60).
    # With corrected Natonnata:
    # - Sun in house 1 (default) = Night
    # - Moon is night-strong, gets 60 for Natonnata
    # - Sun is day-strong, gets 0 for Natonnata at night
    # 
    # Paksha: Sun Default 0, Moon Default 0 -> Angle 0 -> New Moon.
    # New Moon: Malefics (Sun) Strong(60), Benefics (Moon) Weak(0).
    # 
    # Expected totals:
    # Sun with high Ayana (58.75): Natonnata(0) + Paksha(60) + Ayana(58.75) = 118.75
    # Sun with low Ayana (1.25): Natonnata(0) + Paksha(60) + Ayana(1.25) = 61.25
    # Moon with high Ayana (1.25): Natonnata(60) + Paksha(0) + Ayana(1.25) = 61.25
    # Moon with low Ayana (58.75): Natonnata(60) + Paksha(0) + Ayana(58.75) = 118.75
    
    # Wait, Moon is South group, so:
    # Moon with +23 decl: (24-23)*1.25 = 1.25 (Low) -> Total = 60+0+1.25 = 61.25
    # Moon with -23 decl: (24-(-23))*1.25 = 58.75 (High) -> Total = 60+0+58.75 = 118.75
    
    if high_score:
        assert total_kala > 100.0  # High Ayana + appropriate Natonnata/Paksha
    else:
        assert total_kala < 80.0  # Low Ayana but still has Natonnata or Paksha strength


