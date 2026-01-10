import pytest
import swisseph as swe
from backend.astrology import (
    calculate_julian_day, get_zodiac_sign, get_house_number,
    calculate_chara_karakas, calculate_planetary_positions
)

def test_calculate_julian_day():
    """Verify Julian Day calculation against known EPOCH."""
    # Jan 1, 2000, 12:00 UTC is JD 2451545.0
    # Our function uses timezone localization. Use UTC for pure check.
    jd = calculate_julian_day(2000, 1, 1, 12, 0, "UTC")
    assert jd == 2451545.0
    
    # Check another known date
    jd2 = calculate_julian_day(1980, 4, 25, 12, 0, "UTC")
    assert jd2 == 2444355.0

def test_get_zodiac_sign():
    """Verify mapping of longitude to zodiac signs."""
    # 0 deg -> Aries
    sign, deg, num = get_zodiac_sign(0.0)
    assert sign == 'Aries'
    assert num == 0
    assert deg == 0.0
    
    # 45 deg -> 15 deg Taurus (45 - 30)
    sign, deg, num = get_zodiac_sign(45.0)
    assert sign == 'Taurus'
    assert num == 1
    assert deg == 15.0
    
    # 359.9 -> 29.9 Pisces
    sign, deg, num = get_zodiac_sign(359.9)
    assert sign == 'Pisces'
    assert num == 11
    assert pytest.approx(deg, 0.1) == 29.9

def test_get_house_number_whole_sign():
    """Verify house numbering from Ascendant using Whole Sign system."""
    # Ascendant in Aries (0), Planet in Leo (4) -> 5th House
    house = get_house_number(4, 0)
    assert house == 5
    
    # Ascendant in Pisces (11), Planet in Aries (0) -> 2nd House
    house = get_house_number(0, 11)
    assert house == 2
    
    # Same sign -> 1st House
    assert get_house_number(5, 5) == 1

def test_calculate_chara_karakas():
    """Verify Jaimini Chara Karakas ranking by degree within sign."""
    chart_data = {
        'sun': {'degree': 10.0},      # rank 4
        'moon': {'degree': 25.0},     # rank 2
        'mars': {'degree': 5.0},      # rank 5
        'mercury': {'degree': 2.0},   # rank 6
        'jupiter': {'degree': 29.9}, # rank 1 (AK)
        'venus': {'degree': 1.1},     # rank 7 (DK)
        'saturn': {'degree': 15.0},   # rank 3
    }
    karaka_map = calculate_chara_karakas(chart_data)
    
    assert karaka_map['jupiter'] == 'AK'
    assert karaka_map['moon'] == 'AmK'
    assert karaka_map['venus'] == 'DK'
    assert len(karaka_map) == 7

def test_planetary_positions_plausibility():
    """Basic plausibility check for planetary positions (not real data, just math)."""
    # Use a JD where we know roughly where things are or just check structure
    jd = 2451545.0
    positions = calculate_planetary_positions(jd)
    
    assert 'sun' in positions
    assert 'moon' in positions
    assert 'rahu' in positions
    assert 'ketu' in positions
    
    # Ketu should be 180 deg from Rahu
    # Note: Using abs_pos for math
    rahu_pos = positions['rahu']['abs_pos']
    ketu_pos = positions['ketu']['abs_pos']
    diff = abs(rahu_pos - ketu_pos)
    assert pytest.approx(diff, 0.1) == 180 or pytest.approx(diff, 0.1) == 180 # modulo check
    assert pytest.approx((rahu_pos + 180) % 360, 0.1) == ketu_pos
