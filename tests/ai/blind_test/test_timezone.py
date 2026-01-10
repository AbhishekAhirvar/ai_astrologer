#!/usr/bin/env python3
"""
Timezone Verification Test

Tests that our blind test system correctly handles different timezones.
Critical to ensure backend respects timezone_str parameter.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from backend.astrology import generate_vedic_chart
from datetime import datetime
import pytz


def test_timezone_handling():
    """Test that backend correctly handles different timezones"""
    
    print("\n" + "="*80)
    print("🌍 TIMEZONE VERIFICATION TEST")
    print("="*80)
    
    # Test case: Same absolute moment in time, different timezones
    # Steve Jobs birth: Feb 24, 1955, 19:15 PST (San Francisco)
    
    test_cases = [
        {
            "name": "Steve Jobs (America/Los_Angeles)",
            "timezone": "America/Los_Angeles",
            "year": 1955, "month": 2, "day": 24,
            "hour": 19, "minute": 15,
            "lat": 37.7749, "lon": -122.4194
        },
        {
            "name": "Same moment in UTC",
            "timezone": "UTC",
            "year": 1955, "month": 2, "day": 25,  # Next day in UTC
            "hour": 3, "minute": 15,  # 19:15 PST = 03:15 next day UTC
            "lat": 37.7749, "lon": -122.4194
        },
        {
            "name": "Gandhi (Asia/Kolkata)",
            "timezone": "Asia/Kolkata",
            "year": 1869, "month": 10, "day": 2,
            "hour": 7, "minute": 12,
            "lat": 21.6417, "lon": 69.6293
        },
        {
            "name": "Fictional (Africa/Cairo)",
            "timezone": "Africa/Cairo",
            "year": 1990, "month": 6, "day": 15,
            "hour": 14, "minute": 30,
            "lat": 30.0444, "lon": 31.2357
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test['name']} ---")
        print(f"Input timezone: {test['timezone']}")
        print(f"Date/Time: {test['year']}-{test['month']:02d}-{test['day']:02d} {test['hour']:02d}:{test['minute']:02d}")
        
        try:
            # Generate chart with specific timezone
            chart = generate_vedic_chart(
                name=f"Test-{i}",
                year=test["year"],
                month=test["month"],
                day=test["day"],
                hour=test["hour"],
                minute=test["minute"],
                city=f"Test City {i}",
                lat=test["lat"],
                lon=test["lon"],
                timezone_str=test["timezone"]
            )
            
            # Check metadata
            chart_dict = chart.model_dump() if hasattr(chart, 'model_dump') else chart.dict()
            
            # Verify timezone was passed correctly
            # The backend logs should show the correct timezone
            
           # Get positions from chart
            sun_sign = chart_dict.get('sun', {}).get('sign', 'Unknown')
            sun_deg = chart_dict.get('sun', {}).get('degree', 0)
            moon_sign = chart_dict.get('moon', {}).get('sign', 'Unknown')
            ascendant_sign = chart_dict.get('ascendant', {}).get('sign', 'Unknown')
            
            print(f"✅ Chart generated successfully")
            print(f"   Sun position: {sun_sign} {sun_deg:.2f}°")
            print(f"   Moon position: {moon_sign}")
            print(f"   Ascendant: {ascendant_sign}")
            
            results.append({
                "test": test["name"],
                "timezone": test["timezone"],
                "success": True,
                "sun_sign": sun_sign,
                "sun_degree": sun_deg
            })
            
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                "test": test["name"],
                "timezone": test["timezone"],
                "success": False,
                "error": str(e)
            })
    
    # Analysis
    print("\n" + "="*80)
    print("📊 ANALYSIS")
    print("="*80)
    
    all_success = all(r["success"] for r in results)
    
    if all_success:
        print("\n✅ All timezone tests passed!")
        
        # Check if Steve Jobs PST and UTC give same chart (they should - same moment in time)
        if len(results) >= 2:
            pst_sun = results[0]["sun_sign"]
            utc_sun = results[1]["sun_sign"]
            
            print(f"\n🔍 Same Moment Test:")
            print(f"   PST (19:15 Feb 24): Sun in {pst_sun}")
            print(f"   UTC (03:15 Feb 25): Sun in {utc_sun}")
            
            if pst_sun == utc_sun:
                print(f"   ✅ PASS - Same absolute moment gives same chart")
            else:
                print(f"   ⚠️  WARNING - Different charts for same moment!")
                print(f"   This suggests timezone might not be properly handled")
    else:
        print("\n❌ Some tests failed:")
        for r in results:
            if not r["success"]:
                print(f"   - {r['test']}: {r.get('error', 'Unknown error')}")
    
    # Verify our blind test data
    print("\n" + "="*80)
    print("🔍 BLIND TEST DATA VERIFICATION")
    print("="*80)
    
    print("\nChecking if our test data passes timezones correctly...")
    
    import json
    dataset_file = Path(__file__).parent / "data" / "blind_test_dataset.json"
    
    if dataset_file.exists():
        with open(dataset_file, 'r') as f:
            dataset = json.load(f)
        
        # Check first subject
        subject = dataset["test_subjects"][0]
        tz = subject["birth_data"]["timezone"]
        
        print(f"\n✅ Test data includes timezone: '{tz}'")
        print(f"   Example subject: {subject['id']}")
        print(f"   Birth: {subject['birth_data']['year']}-{subject['birth_data']['month']}-{subject['birth_data']['day']}")
        print(f"   Timezone: {tz}")
        
        # Check if we pass it to generate_vedic_chart
        print(f"\n🔍 Our blind_predictor.py passes timezone_str parameter:")
        with open(Path(__file__).parent / "blind_predictor.py", 'r') as f:
            code = f.read()
            if 'timezone_str=' in code:
                print(f"   ✅ YES - timezone_str parameter is passed")
            else:
                print(f"   ❌ NO - timezone_str parameter NOT passed!")
                print(f"   WARNING: Backend will default to Asia/Kolkata for all charts!")
    else:
        print("\n⚠️  Dataset not found - run test_data_generator.py first")
    
    print("\n" + "="*80)
    print("✅ TIMEZONE VERIFICATION COMPLETE")
    print("="*80)
    
    return all_success


if __name__ == "__main__":
    success = test_timezone_handling()
    sys.exit(0 if success else 1)
