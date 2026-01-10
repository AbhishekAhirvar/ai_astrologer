
import pytest
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.dasha_system import VimshottariDashaSystem
from backend.config import KP_AYANAMSA

# Reference Data:
# Standard Logic: 
# Nakshatra 1 (Ashwini) spans 0.00 to 13.33 deg Aries.
# Lord: Ketu (7 Years).
# Test Case 1: Moon at 0.00 Aries. Balance = 7 Years Ketu.
# Test Case 2: Moon at 13.33 Aries (End). Balance ~ 0 Years Ketu. Start Venus.
# Test Case 3: Moon at 6.66 Aries (Mid). Balance ~ 3.5 Years Ketu.

def test_dasha_gold_standard_logic():
    ds = VimshottariDashaSystem()
    
    # CASE 1: Start of Zodiac (Ketu Start)
    # 0.0 degrees
    # Birth JD = 2451545.0 (J2000)
    b_jd = 2451545.0
    
    res_1 = ds.calculate_birth_balance(0.0)
    assert res_1['lord'] == 'Ketu'
    assert res_1['balance_years'] == pytest.approx(7.0, abs=0.01)
    
    # CASE 2: Middle of Ashwini
    # 6.6666 degrees
    res_2 = ds.calculate_birth_balance(20.0/3.0) 
    assert res_2['lord'] == 'Ketu'
    assert res_2['balance_years'] == pytest.approx(3.5, abs=0.01)
    
    # CASE 3: Start of Bharani (Venus)
    # 13.3333... degrees
    res_3 = ds.calculate_birth_balance(40.0/3.0 + 0.0001)
    # Should be Venus, Full 20 years
    assert res_3['lord'] == 'Venus'
    assert res_3['balance_years'] == pytest.approx(20.0, abs=0.01)
    
    # CASE 4: Start of Kritika (Sun)
    # 26.6666... degrees
    res_4 = ds.calculate_birth_balance(80.0/3.0 + 0.0001)
    assert res_4['lord'] == 'Sun'
    assert res_4['balance_years'] == pytest.approx(6.0, abs=0.01)

def test_dasha_timeline_integrity():
    """Verify continuity of timeline generation"""
    ds = VimshottariDashaSystem()
    b_jd = 2451545.0
    moon_lon = 0.0 # Start of Ketu
    
    # Generate 125 years to cover full cycle + loop
    timeline = ds.generate_timeline(moon_lon, b_jd, years_duration=125, max_level=1)
    
    # 1. Ketu (7)
    assert timeline[0]['lord'] == 'Ketu'
    assert timeline[0]['duration_years'] == pytest.approx(7.0)
    assert timeline[0]['start_jd'] == b_jd
    
    # 2. Venus (20)
    assert timeline[1]['lord'] == 'Venus'
    
    # Check sequence
    expected_order = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']
    for i, p in enumerate(expected_order):
        assert timeline[i]['lord'] == p
        
    # Check 10th item (Loop back to Ketu)
    assert timeline[9]['lord'] == 'Ketu'
    
    # Check Time Continuity
    for i in range(len(timeline)-1):
        end_curr = timeline[i]['end_jd']
        start_next = timeline[i+1]['start_jd']
        assert end_curr == pytest.approx(start_next, abs=0.0001)

