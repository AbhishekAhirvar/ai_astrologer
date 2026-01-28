import sys
import os
import pytest
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.location import get_location_data
from backend.astrology import generate_vedic_chart

@pytest.mark.anyio
async def test_backend_integration():
    """Integration test for backend location and chart generation"""
    
    # 1. Test Location
    print("\n[Location Test]")
    loc = await get_location_data("New Delhi")
    assert loc is not None, "Location not found"
    print(f"SUCCESS: {loc}")
    
    # 2. Test Chart
    print("\n[Chart Test]")
    # 1990-01-01 12:00
    chart = generate_vedic_chart("Test", 1990, 1, 1, 12, 0, "New Delhi", 28.6, 77.2)
    assert chart.error is None, f"Chart generation failed: {chart.error}"
    assert hasattr(chart, 'planets') and 'sun' in chart.planets, "Sun not found in chart"
    print(f"SUCCESS: Chart has {len(chart.planets)} planets")
    print(f"Sun Position: {chart.planets['sun']}")
    
    # 3. Check for API Key
    print("\n[Environment Test]")
    if os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY"):
        print("SUCCESS: API KEY found.")
    else:
        print("WARNING: API KEY NOT FOUND. AI features will fail.")

