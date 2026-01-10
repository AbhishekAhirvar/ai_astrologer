
import pytest
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.dasha_system import VimshottariDashaSystem, DASHA_PERIODS
from datetime import datetime

def test_drill_down_logic():
    ds = VimshottariDashaSystem()
    
    # Test 0 offset (Start of Cycle -> Ketu/Ketu/Ketu/Ketu/Ketu)
    res = ds._drill_down_dasha(0.0)
    assert res['maha']['lord'] == 'Ketu'
    assert res['antar']['lord'] == 'Ketu'
    assert res['prana']['lord'] == 'Ketu'
    
    # Test offset into Venus Maha Dasha
    # Ketu (7 years). Venus starts at Year 7.
    # Offset 7.0 + epsilon
    res = ds._drill_down_dasha(7.001)
    assert res['maha']['lord'] == 'Venus'
    assert res['antar']['lord'] == 'Venus' # First Antar of Venus is Venus
    
    # Test offset into Venus/Sun Antar Dasha
    # Venus/Venus duration = 20 * 20 / 120 = 400/120 = 3.333 years.
    # Venus/Sun starts at 7 + 3.333 = 10.333
    res = ds._drill_down_dasha(10.5)
    assert res['maha']['lord'] == 'Venus'
    assert res['antar']['lord'] == 'Sun'

def test_timeline_generation_structure():
    ds = VimshottariDashaSystem()
    # Mock Moon at 0 Aries (Ketu)
    # Balance = 7 years.
    birth_jd = 2451545.0 # J2000
    
    timeline = ds.generate_timeline(0.0, birth_jd, years_duration=120, max_level=2)
    
    # Expect sequence starting with Ketu
    assert timeline[0]['lord'] == 'Ketu'
    assert timeline[0]['duration_years'] == pytest.approx(7.0)
    
    # Check 2nd Maha Dasha (Venus)
    assert timeline[1]['lord'] == 'Venus'
    assert timeline[1]['duration_years'] == 20.0
    
    # Check max level recursion (Antar Dasha present)
    assert 'sub_periods' in timeline[1]
    antars = timeline[1]['sub_periods']
    assert len(antars) == 9
    assert antars[0]['lord'] == 'Venus' # Venus/Venus

def test_birth_balance_mid_period():
    ds = VimshottariDashaSystem()
    # Moon at Middle of Ashwini (Ketu).
    # Nakshatra Span 13.33. Moon at 6.666.
    # Balance should be 3.5 years.
    
    balance = ds.calculate_birth_balance(13.333333 / 2.0)
    assert balance['lord'] == 'Ketu'
    assert balance['balance_years'] == pytest.approx(3.5, rel=1e-2)
    
    # Timeline should start with fractional Ketu period
    birth_jd = 2451545.0
    timeline = ds.generate_timeline(13.333333 / 2.0, birth_jd, max_level=1)
    
    assert timeline[0]['lord'] == 'Ketu'
    assert timeline[0]['duration_years'] == pytest.approx(3.5, rel=1e-2)
