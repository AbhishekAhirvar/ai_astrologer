
import pytest
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.shadbala import calculate_shadbala_for_chart, get_compound_relationship, calculate_sthana_bala

def test_raman_chart_configurations(chart_factory):
    """
    Validation against B.V. Raman's Horoscope Logic (Approximate).
    Chart Details:
    Ascendant: Aquarius (Saturn)
    Sun: Cancer (22 deg) - In Moon's sign.
    Moon: Taurus (23 deg) - Exalted.
    Mars: Leo (21 deg) - In Sun's sign.
    Jupiter: Scorpio (12 deg) - In Mars' sign.
    """
    
    # Setup approximate chart
    # Note: Speed, Declination are defaults unless specified. (Physics verified elsewhere)
    # Focus here is on Logic Integration (Friendship, Sthana).
    
    chart = chart_factory(
        planets=[
            {'name': 'Sun', 'sign': 'Cancer', 'sign_num': 3, 'degree': 22.0},
            {'name': 'Moon', 'sign': 'Taurus', 'sign_num': 1, 'degree': 23.0}, # Exalted
            {'name': 'Mars', 'sign': 'Leo', 'sign_num': 4, 'degree': 21.0},
            {'name': 'Jupiter', 'sign': 'Scorpio', 'sign_num': 7, 'degree': 12.0}
        ],
        ascendant_deg=312.0 # Aquarius
    )
    
    # 1. Verify Sun Relationship logic
    # Sun in Cancer (Moon).
    # Natural: Sun -> Moon is Friend.
    # Tatkalika: Moon in Taurus.
    # Count Cancer(3) to Taurus(1). 3->4->...->0->1.
    # Distance: 11th House (Upachaya).
    # 11th is Friend.
    # Result: Friend + Friend = Adhi Mitra.
    rel_sun = get_compound_relationship('Sun', 'Moon', chart)
    assert rel_sun == 'Adhi Mitra'
    
    # 2. Verify Moon Exaltation
    # Moon Exalted in Taurus.
    # Exalt Point: 3 deg Taurus.
    # Moon at 23 deg Taurus. Diff = 20 deg.
    # Uccha Bala = (180 - 20) / 3 = 160 / 3 = 53.33.
    # Wait, Formula: Diff is distance from Debilitation?
    # Exalt Point = 33 deg (3 Taurus).
    # Debil Point = 213 deg (3 Scorpio).
    # Moon Pos = 30 + 23 = 53 deg.
    # Dist from Debil = |53 - 213| = 160.
    # Score = 160 / 3 = 53.33.
    # My code:
    # diff = abs(abs_pos - debilitation_pt)
    # if diff > 180: diff = 360 - diff.
    # 160 <= 180.
    # uccha_score = diff / 3.0.
    # Correct.
    
    # 3. Verify Mars Relationship
    # Mars in Leo (Sun).
    # Lord Sun. Sun in Cancer.
    # Leo(4) -> Cancer(3).
    # Distance: 12th House.
    # 12th is Friend.
    # Natural: Mars -> Sun is Friend.
    # Result: Adhi Mitra.
    rel_mars = get_compound_relationship('Mars', 'Sun', chart)
    assert rel_mars == 'Adhi Mitra'
    
    # 4. Total Sthana Integration Check (Mars)
    # Mars:
    # Uccha: Mars Exalt 298 (28 Cap). Pos: Leo 21 (141).
    # Debil: 28 Cancer (118).
    # Dist from Debil: |141 - 118| = 23.
    # Uccha Score: 23 / 3 = 7.66.
    # Saptavarga (D1): Adhi Mitra (22.5).
    # Ojayugma: Leo (Odd). Mars (Male). Score 15.
    # Kendra: Leo (7th from Asc Aquarius). Kendra. Score 60.
    # Drekkana: 21 deg Leo. 3rd Decan (Aries/Sag).
    # 20-30 deg -> 3rd.
    # Mars (Male). 1st Decan strong. 3rd?
    # My Code: "Sun/Mars/Jup (Male) -> 1st Decanate". 3rd gets 0.
    # Total Expected: 7.66 + 22.5 + 15 + 60 + 0 = 105.16. (Approx 1.75 Rupas).
    
    p_data_mars = chart.planets['mars']
    score_mars = calculate_sthana_bala('Mars', p_data_mars, chart)
    
    assert score_mars == pytest.approx(105.16, abs=1.0)
