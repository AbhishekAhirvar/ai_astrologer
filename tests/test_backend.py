import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.location import get_location_data
from backend.astrology import generate_chart
import os

print("--- Testing Backend ---")

# 1. Test Location
print("\n[Location Test]")
loc = get_location_data("New Delhi")
if loc:
    print(f"SUCCESS: {loc}")
else:
    print("FAILURE: Location not found")

# 2. Test Chart
print("\n[Chart Test]")
# 1990-01-01 12:00
chart = generate_chart("Test", 1990, 1, 1, 12, 0, "New Delhi", 28.6, 77.2)
if "error" not in chart and "sun" in chart:
    print(f"SUCCESS: Chart Keys: {list(chart.keys())}")
    print(f"Sun Position: {chart['sun']}")
else:
    print(f"FAILURE: {chart}")

# 3. Check for API Key
print("\n[Environment Test]")
if os.getenv("GEMINI_API_KEY"):
    print("SUCCESS: GEMINI_API_KEY found.")
else:
    print("WARNING: GEMINI_API_KEY NOT FOUND. AI features will fail.")
