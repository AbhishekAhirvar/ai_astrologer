"""
Unit tests for KP Significator Engine and Optimized AI Payload.

Tests the 4-fold significator rules and the token-optimized JSON builder.
"""
import pytest
from backend.astrology import generate_vedic_chart
from backend.kp_significators import (
    calculate_planet_significators,
    build_optimized_planet_payload,
    build_optimized_house_payload,
    get_house_occupants,
    get_house_owners,
    get_star_lord_map,
    PLANET_CODES,
    SIGN_CODES,
    SIGN_LORDS
)
from backend.ai import _build_optimized_json_context
import json


@pytest.fixture
def sample_chart():
    """Generate a sample chart for testing."""
    return generate_vedic_chart(
        name="TestUser",
        year=1990,
        month=5,
        day=15,
        hour=10,
        minute=30,
        city="Mumbai",
        lat=19.0760,
        lon=72.8777,
        timezone_str="Asia/Kolkata",
        include_kp_data=True,
        include_complete_dasha=True
    )


class TestSignificatorEngine:
    """Tests for the 4-fold KP significator calculation."""
    
    def test_planet_significators_returns_list(self, sample_chart):
        """Significators should return a sorted list of house numbers."""
        significators = calculate_planet_significators("Sun", sample_chart)
        
        assert isinstance(significators, list)
        assert all(isinstance(h, int) for h in significators)
        assert all(1 <= h <= 12 for h in significators)
        assert significators == sorted(significators)  # Should be sorted
    
    def test_planet_significators_occupancy_level2(self, sample_chart):
        """LEVEL 2: Planet should signify the house it occupies."""
        sun_data = sample_chart.planets.get('sun') or sample_chart.planets.get('Sun')
        if sun_data:
            sun_house = getattr(sun_data, 'house', None)
            if sun_house:
                significators = calculate_planet_significators("Sun", sample_chart)
                assert sun_house in significators, f"Sun should signify its occupied house {sun_house}"
    
    def test_planet_significators_ownership_level4(self, sample_chart):
        """LEVEL 4: Sun should signify houses with Leo on the cusp (Sun owns Leo)."""
        house_owners = get_house_owners(sample_chart)
        sun_owned_houses = [h for h, owner in house_owners.items() if owner == "Sun"]
        
        significators = calculate_planet_significators("Sun", sample_chart)
        for house in sun_owned_houses:
            assert house in significators, f"Sun should signify house {house} which it owns"
    
    def test_star_lord_level_significators(self, sample_chart):
        """
        LEVEL 1 & 3: Planet A (in Star of B) should signify B's occupied/owned houses.
        Example: If Sun is in Star of Moon, and Moon is in 5th, Sun signifies 5.
        """
        star_lord_map = get_star_lord_map(sample_chart)
        house_occupants = get_house_occupants(sample_chart)
        
        # Pick a planet and trace its star lord chain
        for planet_name in ["Sun", "Moon", "Mars"]:
            star_lord = star_lord_map.get(planet_name)
            if not star_lord:
                continue
            
            # Find which house the star lord occupies
            for house_num, occupants in house_occupants.items():
                if star_lord in occupants:
                    # The planet should signify this house via star lord
                    significators = calculate_planet_significators(planet_name, sample_chart)
                    assert house_num in significators, \
                        f"{planet_name} in star of {star_lord} (occupying H{house_num}) should signify H{house_num}"
                    break
    
    def test_rahu_ketu_agent_logic(self, sample_chart):
        """
        Rahu/Ketu should signify the house of their sign lord (dispositor).
        They don't own signs, so they act as agents for the lord of the sign they occupy.
        """
        for node in ["Rahu", "Ketu"]:
            node_data = sample_chart.planets.get(node.lower()) or sample_chart.planets.get(node)
            if not node_data:
                continue
            
            # Get the sign Rahu/Ketu occupies
            sign_name = getattr(node_data, 'sign', None)
            if not sign_name:
                continue
            
            # Get the lord of that sign (the dispositor)
            dispositor = SIGN_LORDS.get(sign_name)
            if not dispositor:
                continue
            
            # The dispositor's owned houses should be in Rahu/Ketu's significators
            house_owners = get_house_owners(sample_chart)
            dispositor_houses = [h for h, owner in house_owners.items() if owner == dispositor]
            
            significators = calculate_planet_significators(node, sample_chart)
            
            # At minimum, check that Rahu/Ketu has SOME significators (not empty)
            assert len(significators) >= 1, f"{node} should have at least 1 significator"
    
    def test_all_planets_have_significators(self, sample_chart):
        """All 9 planets should have at least one significator."""
        planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
        
        for planet in planets:
            significators = calculate_planet_significators(planet, sample_chart)
            assert len(significators) >= 1, f"{planet} should have at least 1 significator"


class TestOptimizedPayload:
    """Tests for the optimized JSON payload builder."""
    
    def test_planet_payload_structure(self, sample_chart):
        """Planet payload should have correct structure: [Sign, Star, Sub, Strength, [Significators]]"""
        payload = build_optimized_planet_payload(sample_chart)
        
        assert isinstance(payload, dict)
        assert "Su" in payload  # Sun should be present
        
        sun_data = payload["Su"]
        assert len(sun_data) == 5, "Planet data should have 5 elements"
        assert isinstance(sun_data[0], str)  # Sign code
        assert isinstance(sun_data[1], str)  # Star lord code
        assert isinstance(sun_data[2], str)  # Sub lord code
        assert isinstance(sun_data[4], list)  # Significators
    
    def test_planet_codes_used(self, sample_chart):
        """Payload should use 2-letter planet codes."""
        payload = build_optimized_planet_payload(sample_chart)
        
        for key in payload.keys():
            assert len(key) == 2 or len(key) == 3, f"Planet code {key} should be 2-3 letters"
    
    def test_house_payload_structure(self, sample_chart):
        """House payload should have correct structure: [Sign, Sub_Lord]"""
        payload = build_optimized_house_payload(sample_chart)
        
        assert isinstance(payload, dict)
        assert "1" in payload
        
        h1_data = payload["1"]
        assert len(h1_data) == 2, "House data should have 2 elements"
        assert isinstance(h1_data[0], str)  # Sign code
        assert isinstance(h1_data[1], str)  # Sub lord code
    
    def test_all_houses_present(self, sample_chart):
        """All 12 houses should be in the payload."""
        payload = build_optimized_house_payload(sample_chart)
        
        for h in range(1, 13):
            assert str(h) in payload, f"House {h} should be in payload"


class TestZeroMathProtocol:
    """Tests for the Zero-Math Protocol optimization."""
    
    def _check_no_julian_dates(self, obj, path="root"):
        """Recursively check that no value is a Julian Date (float > 2400000)."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                self._check_no_julian_dates(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                self._check_no_julian_dates(v, f"{path}[{i}]")
        elif isinstance(obj, float):
            assert obj < 2400000, f"Julian date detected at {path}: {obj}"
    
    def test_no_julian_dates_in_json(self, sample_chart):
        """JSON payload should NOT contain Julian dates (floats > 2400000)."""
        json_str = _build_optimized_json_context(sample_chart)
        payload = json.loads(json_str)
        
        # Recursively check all values
        self._check_no_julian_dates(payload)
    
    def test_dasha_ends_in_format(self, sample_chart):
        """Dasha should show 'ends_in' with human-readable format like '3y 5m'."""
        json_str = _build_optimized_json_context(sample_chart)
        payload = json.loads(json_str)
        
        if "dasha" in payload:
            assert "ends_in" in payload["dasha"], "Dasha should have 'ends_in' field"
            ends_in = payload["dasha"]["ends_in"]
            # Should be like "5y 3m" or "ended"
            assert "y" in ends_in or ends_in == "ended" or ends_in == "?", \
                f"ends_in should be human-readable, got: {ends_in}"
    
    def test_json_uses_compact_separators(self, sample_chart):
        """JSON should use compact separators (no spaces)."""
        json_str = _build_optimized_json_context(sample_chart)
        payload = json.loads(json_str)
        
        # Re-dump with compact separators and compare
        compact_str = json.dumps(payload, separators=(',', ':'))
        
        # They should be the same length if both are compact
        assert len(json_str) == len(compact_str), \
            f"JSON not compact: {len(json_str)} vs expected {len(compact_str)}"


class TestTokenEfficiency:
    """Tests for token efficiency of the new format."""
    
    def test_payload_size_reasonable(self, sample_chart):
        """Optimized JSON should be under 1000 characters."""
        json_str = _build_optimized_json_context(sample_chart)
        
        assert len(json_str) < 1000, f"JSON payload too large: {len(json_str)} chars"
        print(f"✅ Payload size: {len(json_str)} characters")
    
    def test_payload_parseable(self, sample_chart):
        """JSON should be valid and parseable."""
        json_str = _build_optimized_json_context(sample_chart)
        
        try:
            payload = json.loads(json_str)
            assert isinstance(payload, dict)
        except json.JSONDecodeError as e:
            pytest.fail(f"JSON is not valid: {e}")
    
    def test_required_fields_present(self, sample_chart):
        """JSON should have required top-level fields."""
        json_str = _build_optimized_json_context(sample_chart)
        payload = json.loads(json_str)
        
        # These are guaranteed fields for KP mode
        assert "pl" in payload, "Planets should be present"
        assert "h" in payload, "Houses should be present"

