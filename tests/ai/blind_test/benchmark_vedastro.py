
import sys
from pathlib import Path
import json
import pandas as pd
from datetime import datetime
import pytz

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from backend.astrology import generate_vedic_chart
from backend.config import PLANET_IDS
import vedastro
from vedastro import *

def compare_calculations():
    # Test subjects
    subjects = [
        {
            "name": "Steve Jobs",
            "year": 1955, "month": 2, "day": 24, "hour": 19, "minute": 15,
            "lat": 37.7749, "lon": -122.4194, "tz": "America/Los_Angeles"
        },
        {
            "name": "Mahatma Gandhi",
            "year": 1869, "month": 10, "day": 2, "hour": 7, "minute": 12,
            "lat": 21.6417, "lon": 69.6293, "tz": "Asia/Kolkata"
        }
    ]

    results = []

    for sub in subjects:
        print(f"\nBenchmarking {sub['name']}...")
        
        # 1. Our Backend Calculation
        our_chart = generate_vedic_chart(
            name=sub['name'],
            year=sub['year'], month=sub['month'], day=sub['day'],
            hour=sub['hour'], minute=sub['minute'],
            city="Test City", lat=sub['lat'], lon=sub['lon'],
            timezone_str=sub['tz']
        )
        
        # 2. VedAstro Calculation
        # Prep VedAstro Time and Location
        location = GeoLocation(sub['name'], sub['lon'], sub['lat'])
        # Convert local time to string format "HH:MM DD/MM/YYYY +HH:MM"
        # We need to get the offset for the specific date
        tz = pytz.timezone(sub['tz'])
        dt = tz.localize(datetime(sub['year'], sub['month'], sub['day'], sub['hour'], sub['minute']))
        offset_seconds = dt.utcoffset().total_seconds()
        offset_hours = int(offset_seconds / 3600)
        offset_minutes = int((offset_seconds % 3600) / 60)
        offset_str = f"{'+' if offset_hours >= 0 else '-'}{abs(offset_hours):02d}:{abs(offset_minutes):02d}"
        
        time_str = f"{sub['hour']:02d}:{sub['minute']:02d} {sub['day']:02d}/{sub['month']:02d}/{sub['year']} {offset_str}"
        veda_time = Time(time_str, location)

        # Compare planets
        planet_map = {
            'sun': PlanetName.Sun,
            'moon': PlanetName.Moon,
            'mars': PlanetName.Mars,
            'mercury': PlanetName.Mercury,
            'jupiter': PlanetName.Jupiter,
            'venus': PlanetName.Venus,
            'saturn': PlanetName.Saturn,
            'rahu': PlanetName.Rahu,
            'ketu': PlanetName.Ketu
        }

        for p_key, v_planet in planet_map.items():
            our_pos = our_chart.planets[p_key].abs_pos
            veda_raw = Calculate.PlanetNirayanaLongitude(v_planet, veda_time)
            veda_pos = float(veda_raw['TotalDegrees'])
            
            diff = abs(our_pos - veda_pos)
            if diff > 180: diff = 360 - diff
            
            results.append({
                "Subject": sub['name'],
                "Planet": p_key.capitalize(),
                "Our Pos": our_pos,
                "VedAstro Pos": veda_pos,
                "Diff (deg)": round(diff, 4)
            })

    df = pd.DataFrame(results)
    print("\n" + "="*80)
    print("CALCULATION COMPARISON SUMMARY")
    print("="*80)
    print(df.to_string(index=False))
    
    avg_diff = df["Diff (deg)"].mean()
    print(f"\nAverage Difference: {avg_diff:.4f} degrees")
    
    if avg_diff < 0.1:
        print("✅ Calculations are highly consistent!")
    else:
        print("⚠️ Significant differences found. Ayanamsa mismatch likely.")

if __name__ == "__main__":
    compare_calculations()
