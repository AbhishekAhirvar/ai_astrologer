
import pytest
try:
    import vedastro
    from vedastro import *
except ImportError:
    pytest.skip("vedastro module not installed", allow_module_level=True)

import datetime

def test_vedastro():
    print("Initializing VedAstro...")
    try:
        # Create a GeoLocation object
        location = GeoLocation("New York", -74.0060, 40.7128)
        
        # Create a time object
        # Format: "HH:MM DD/MM/YYYY +HH:MM"
        time = Time("00:00 01/01/2000 +00:00", location)
        
        # Calculate planet positions
        print("Calculating Sun position...")
        sun_long = Calculate.PlanetNirayanaLongitude(PlanetName.Sun, time)
        print(f"Sun Longitude at 2000-01-01 00:00 UTC: {sun_long}")
        
        print("✅ VedAstro Local Library is working!")
        return True
    except Exception as e:
        print(f"❌ Error initializing VedAstro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_vedastro()
