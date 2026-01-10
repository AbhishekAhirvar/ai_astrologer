
import pytest
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = str(Path(__file__).parent.parent.absolute())
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.schemas import PlanetPosition, ChartResponse, ChartMetadata, ShadbalaData, VargaPlanet

@pytest.fixture
def chart_factory():
    """
    Factory fixture to create consistent ChartResponse objects for testing.
    """
    def _create(planets=None, ascendant_deg=0.0):
        if planets is None:
            planets = []
            
        p_dict = {}
        for p in planets:
            # Default values if not specified
            defaults = {
                'sign': 'Aries', 'sign_num': 0, 'degree': 0.0, 'abs_pos': 0.0,
                'speed': 1.0, 'declination': 0.0, 'is_retrograde': False,
                'house': 1, 'rules_houses': '1'
            }
            defaults.update(p)
            
            # Simple calc for abs_pos if not provided but sign_num/degree are
            if 'abs_pos' not in p and 'sign_num' in defaults and 'degree' in defaults:
                defaults['abs_pos'] = defaults['sign_num'] * 30 + defaults['degree']
                
            p_dict[defaults['name'].lower()] = PlanetPosition(**defaults)
            
        # Ensure Ascendant exists
        if 'ascendant' not in p_dict:
            p_dict['ascendant'] = PlanetPosition(
                name='Ascendant', sign='Aries', degree=ascendant_deg,
                sign_num=int(ascendant_deg // 30), abs_pos=ascendant_deg,
                speed=0, declination=0, is_retrograde=False, house=1
            )

        # Create Mock Varga Data (D1 is essential for Saptavarga fallback)
        d1_varga = {}
        for name, p in p_dict.items():
            # Convert PlanetPosition to VargaPlanet subset
            d1_varga[name] = VargaPlanet(
                name=p.name, sign=p.sign, sign_num=p.sign_num, 
                degree=p.degree, abs_pos=p.abs_pos
            )

        return ChartResponse(
            planets=p_dict,
            vargas={'d1_chart': d1_varga}, # Pre-populate D1
            metadata=ChartMetadata(
                name="Mock Chart", datetime="2024-01-01", location="Test",
                latitude=0.0, longitude=0.0, ayanamsa=24.0, 
                zodiac_system="Sidereal", house_system="Placidus"
            )
        )
    return _create

@pytest.fixture
def planet_factory():
    """Create a single PlanetPosition"""
    def _create(name, abs_pos, **overrides):
        sign_num = int(abs_pos // 30)
        degree = abs_pos % 30
        sign_names = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                      "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        sign = sign_names[sign_num] if 0 <= sign_num < 12 else "Unknown"
        
        defaults = {
            'name': name, 'sign': sign, 'sign_num': sign_num,
            'degree': degree, 'abs_pos': abs_pos,
            'speed': 1.0, 'declination': 0.0, 'is_retrograde': False,
            'house': 1
        }
        defaults.update(overrides)
        return PlanetPosition(**defaults)
    return _create
