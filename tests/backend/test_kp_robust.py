import pytest
import swisseph as swe
from backend.kp_calculations import (
    normalize_longitude, get_nakshatra_info, calculate_sub_lord, 
    calculate_vimshottari_dasha, calculate_placidus_cusps,
    PLANET_SEQUENCE, DASHA_PERIODS
)

def test_longitude_normalization():
    """Verify longitude wrapping and epsilon safety."""
    assert normalize_longitude(0) == 0
    assert normalize_longitude(360) == 0
    assert normalize_longitude(360.0000000000001) == pytest.approx(0, abs=1e-12)
    assert normalize_longitude(-1e-14) == pytest.approx(0, abs=1e-12)
    assert normalize_longitude(-10) == 350
    assert normalize_longitude(370) == 10
    assert normalize_longitude(720) == 0

def test_nakshatra_boundaries():
    """Verify nakshatra lords at transition points."""
    # 0 deg Aries (Ashwini) -> Ketu
    num, lord, pos = get_nakshatra_info(0)
    assert lord == 'Ketu'
    assert pos == 0
    
    # 13.333... deg Aries -> End of Ashwini
    span = 360/27
    num, lord, pos = get_nakshatra_info(span - 0.000001)
    assert lord == 'Ketu'
    
    # 13.333... deg Aries + epsilon (Bharani) -> Venus
    num, lord, pos = get_nakshatra_info(span + 0.000001)
    assert lord == 'Venus'
    assert num == 1

def test_sub_lord_sequence_start():
    """Verify sub-lord sequence correctly starts from the star lord."""
    # Ashwini (Ketu star) -> First sub should be Ketu
    assert calculate_sub_lord(0.0) == 'Ketu'
    
    # Bharani (Venus star) -> First sub should be Venus
    span = 360/27
    assert calculate_sub_lord(span + 0.0001) == 'Venus'
    
    # Krittika (Sun star) -> First sub should be Sun
    assert calculate_sub_lord(2 * span + 0.0001) == 'Sun'

def test_sub_lord_proportions():
    """Verify sub-lord transitions within a nakshatra based on proportions."""
    # In Ashwini:
    # Ketu sub spans 7/120 * 13.333 = 0.777... degrees
    # So 0.7 degrees is still Ketu
    assert calculate_sub_lord(0.7) == 'Ketu'
    # 0.8 degrees should be Venus (next in sequence)
    assert calculate_sub_lord(0.8) == 'Venus'

def test_dasha_birth_balance():
    """Verify birth dasha balance calculation."""
    # Test with Moon at 0.0 Aries (Start of Ashwini/Ketu)
    # Total Ketu dasha is 7 years. Balance should be 7 years.
    res = calculate_vimshottari_dasha(0.0, 2451545.0) # J2000
    assert res['birth_dasha']['lord'] == 'Ketu'
    assert pytest.approx(res['birth_dasha']['balance_years'], 0.01) == 7.0

    # Moon at 6.666... (Halfway through Ashwini)
    # Balance should be 3.5 years
    res = calculate_vimshottari_dasha(360/54, 2451545.0)
    assert res['birth_dasha']['lord'] == 'Ketu'
    assert pytest.approx(res['birth_dasha']['balance_years'], 0.01) == 3.5

def test_dasha_progression():
    """Verify dasha progression over time."""
    birth_jd = 2451545.0 # Jan 1, 2000
    # Moon at 0.0 (Ketu dasha starts, 7 years balance)
    
    # Check 1 year later (Should still be Ketu)
    res = calculate_vimshottari_dasha(0.0, birth_jd, birth_jd + 365.25)
    assert res['maha_dasha']['lord'] == 'Ketu'
    assert pytest.approx(res['maha_dasha']['balance_years'], 0.01) == 6.0
    
    # Check 8 years later (Should be Venus - next in sequence)
    res = calculate_vimshottari_dasha(0.0, birth_jd, birth_jd + 8 * 365.25)
    assert res['maha_dasha']['lord'] == 'Venus'
    # Balance should be 20 - (8-7) = 19 years
    assert pytest.approx(res['maha_dasha']['balance_years'], 0.01) == 19.0

def test_dasha_antar_dasha():
    """Verify Antar dasha cycles."""
    birth_jd = 2451545.0
    # In Ketu Maha Dasha (7 years), Antar Dashas start with Ketu
    # Ketu/Ketu sub-period = 7 * 7 / 120 = 0.408 years (approx 149 days)
    
    # 10 days after birth -> Ketu/Ketu
    res = calculate_vimshottari_dasha(0.0, birth_jd, birth_jd + 10)
    assert res['maha_dasha']['lord'] == 'Ketu'
    assert res['antar_dasha']['lord'] == 'Ketu'
    
    # 200 days after birth -> Ketu/Venus (Venus is after Ketu)
    res = calculate_vimshottari_dasha(0.0, birth_jd, birth_jd + 200)
    assert res['maha_dasha']['lord'] == 'Ketu'
    assert res['antar_dasha']['lord'] == 'Venus'

def test_dasha_wraparound():
    """Verify dasha wraparound for ages > 120 years."""
    birth_jd = 2451545.0
    # At exactly 120 years later, we should be back at the starting balance
    res = calculate_vimshottari_dasha(0.0, birth_jd, birth_jd + 120 * 365.25)
    assert res['maha_dasha']['lord'] == 'Ketu'
    assert pytest.approx(res['maha_dasha']['balance_years'], 0.01) == 7.0

def test_placidus_cusps_range():
    """Verify Placidus cusps are reasonable for a representative case."""
    # New Delhi, India
    lat, lon = 28.6, 77.2
    jd = 2444436.0 # July 1980
    
    from backend.kp_calculations import generate_kp_data
    moon_lon = 135.0 # Mock Moon
    # Need mock planetary positions for KP sub lord calcs
    mock_planets = {'sun': {'longitude': 100.0}, 'moon': {'longitude': 135.0}}
    kp_data = generate_kp_data(jd, lat, lon, mock_planets, moon_lon)
    
    assert len(kp_data['cusps']) == 12
    # Check all houses have sub-lords
    for h in range(1, 13):
        assert 'sub_lord' in kp_data['cusps'][h]
        assert kp_data['cusps'][h]['sub_lord'] in PLANET_SEQUENCE
        # Sign num should be 0-11
        assert 0 <= kp_data['cusps'][h]['sign_num'] <= 11
