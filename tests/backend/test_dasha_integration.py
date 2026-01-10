
import pytest
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.astrology import generate_vedic_chart
from backend.schemas import ChartResponse

def test_chart_generation_with_dasha():
    """Verify that complete dasha is generated when requested."""
    
    # Generate chart
    chart = generate_vedic_chart(
        name="Test Dasha", year=1990, month=1, day=1,
        hour=12, minute=0, city="New Delhi",
        lat=28.6, lon=77.2,
        include_complete_dasha=True
    )
    
    # verify response structure
    assert isinstance(chart, ChartResponse)
    assert chart.complete_dasha is not None
    
    cd = chart.complete_dasha
    
    # Verify Current State
    state = cd.current_state
    assert state.maha_dasha is not None
    assert state.antar_dasha is not None
    assert state.pratyantar_dasha is not None
    assert state.sookshma_dasha is not None
    assert state.prana_dasha is not None
    
    assert state.maha_dasha.is_current == True
    
    # Verify Timeline
    timeline = cd.timeline
    assert len(timeline) > 0
    # Should cover 120 years approximately
    total_dur = sum(p.duration_years for p in timeline)
    # Timeline starts from birth balance + subsequent periods
    # Logic in dasha_system generates periods until 120 years covered
    # Birth balance might be partial.
    assert total_dur >= 119.0 # Approximate
    
def test_chart_generation_without_dasha():
    """Verify default behavior."""
    chart = generate_vedic_chart(
        name="Test No Dasha", year=1990, month=1, day=1,
        hour=12, minute=0, city="New Delhi",
        lat=28.6, lon=77.2,
        include_complete_dasha=False
    )
    assert chart.complete_dasha is None
