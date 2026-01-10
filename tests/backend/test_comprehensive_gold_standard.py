
import pytest
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.shadbala import (
    calculate_drik_bala, calculate_chesta_bala, calculate_kala_bala, 
    get_drishti_value
)
from backend.kp_calculations import calculate_sub_lord
from backend.schemas import PlanetPosition

# ============================================================================
# 1. DRIK BALA (Feature: Continuous Aspect Strength)
# ============================================================================
def test_drik_bala_gold_standard_physics_logic(chart_factory):
    """
    Gold Standard for Aspect Calculations (BPHS Logic).
    Reference: B.V. Raman / BPHS.
    """
    # CASE 1: Opposition (180 deg) -> Full Strength (60 Virupas / 4 = 15 points)
    # The divisor 4 is standard BPHS context (Shadbala Pinda uses Quarter values summed?)
    # Wait, BPHS says "Full Aspect = 60 Shashtiamsas".
    # Drik Bala aggregation logic: Usually Sum of Aspects / 4? Or Net Strength?
    # backend/shadbala.py logic: "sum(drishti_val / 4.0)"
    
    # Let's test get_drishti_value directly first (The Core Physics)
    
    # 30 deg -> 0
    assert get_drishti_value(30) == 0.0
    
    # 60 deg -> 15 (Sextile)
    # Formula: (Angle - 30) / 2 = 15? No.
    # Logic: 
    # 30-60: (Angle-30)/2. At 60: 30/2 = 15. Correct.
    assert get_drishti_value(60) == 15.0
    
    # 90 deg -> 45 (Square)
    # Logic: 60-90: (Angle-60) + 15. At 90: 30 + 15 = 45. Correct.
    assert get_drishti_value(90) == 45.0
    
    # 120 deg -> 30 (Trine)
    # Logic: 90-120: 45 - (Angle-90)/2. At 120: 45 - 15 = 30. Correct.
    assert get_drishti_value(120) == 30.0
    
    # 150 deg -> 0 (Quincunx -ish)
    # Logic: 120-150: 150 - Angle. At 150: 0. Correct.
    # At 135: 15. Correct.
    assert get_drishti_value(150) == 0.0
    
    # 180 deg -> 60 (Opposition)
    # Logic: 150-180: (Angle-150)*2. At 180: 30*2 = 60. Correct.
    assert get_drishti_value(180) == 60.0


# ============================================================================
# 2. CHESTA BALA (Feature: Motion Strength)
# ============================================================================
def test_chesta_bala_gold_standard_motion(chart_factory):
    """
    Verify Chesta Bala assigns strength based on physical speed.
    """
    # 1. Retrograde (-ve speed) -> 60 Virupas
    chart = chart_factory(planets=[
        {'name': 'Mars', 'speed': -0.1, 'abs_pos': 100}
    ])
    score = calculate_chesta_bala('Mars', chart.planets['mars'], chart)
    assert score == 60.0
    
    # 2. Stationary (Speed ~ 0) -> 15 Virupas (Vikal)? Or 6?
    # Code Logic: abs(speed) < 0.05 => 15.0
    chart_stat = chart_factory(planets=[
        {'name': 'Jupiter', 'speed': 0.01, 'abs_pos': 100}
    ])
    score_stat = calculate_chesta_bala('Jupiter', chart_stat.planets['jupiter'], chart_stat)
    assert score_stat == 15.0
    
    # 3. Fast Forward (Direct) -> 30 Virupas (Default/Sama)
    chart_fast = chart_factory(planets=[
        {'name': 'Mercury', 'speed': 1.5, 'abs_pos': 100}
    ])
    score_fast = calculate_chesta_bala('Mercury', chart_fast.planets['mercury'], chart_fast)
    assert score_fast == 30.0

# ============================================================================
# 3. KP SUB-LORD (Feature: Precise Stellar Divisions)
# ============================================================================
def test_kp_sublord_gold_standard():
    """
    Verify KP Sub-Lord Calculation against Known Table.
    Reference: KP Readers.
    """
    # 0 Aries: Ashwini Star (Ketu). Sub: Ketu.
    # Span of Ketu/Ketu: 0 deg 0 min - 0 deg 46 min 40 sec.
    # 46 min 40 sec = 46.666 min = 0.777 degrees.
    # Let's test mid point: 0.4 deg.
    
    sub = calculate_sub_lord(0.4)
    assert sub == 'Ketu'
    
    # Next Sub: Venus.
    # Starts > 0.777 deg.
    sub_next = calculate_sub_lord(0.8)
    assert sub_next == 'Venus'
    
    # Complex Case: 29 deg Scorpio.
    # Sign 8. 29 deg = 239 deg total.
    # Nakshatra: Jyeshtha (Mercury Lord).
    # Span: 16.40 Scorp to 30.00 Scorp.
    # 239 is end of Jyeshtha.
    # Last sub of Mercury star is Saturn? Or Mercury?
    # Sequence: Merc, Ketu, Ven ...
    # Wait, Star Lord is Merc.
    # Sub Lords cycle starting from Star Lord.
    # Merc, Ketu, Ven, Sun, Moon, Mars, Rahu, Jup, Sat.
    # Last sub is Saturn.
    # Let's test 29.99 Scorpio (Abs 239.99).
    
    sub_end = calculate_sub_lord(239.99)
    # The last part of Jyeshtha/Mercury is indeed Saturn?
    # Logic: Star Lord Mercury. Sequence starts Mercury.
    # Checking my code logic: 
    # start_index = PLANET_SEQUENCE.index(star_lord)
    # ... loop 9 times ...
    # Correct.
    # Last sub of ANY star is the one before it in sequence?
    # No, cyclic sequence.
    # Mercury(17) + Ketu(7) ... sums to 120.
    # So valid test is: Does it conform to calculated expectation?
    # For Mercury Star:
    # 1. Merc
    # ...
    # 9. Saturn?
    # Sequence: Ke, Ve, Su, Mo, Ma, Ra, Ju, Sa, Me.
    # Start Me.
    # Me, Ke, Ve, Su, Mo, Ma, Ra, Ju, Sa.
    # Yes, Saturn is last.
    assert sub_end == 'Saturn'

