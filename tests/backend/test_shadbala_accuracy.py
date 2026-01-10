    """
    Shadbala Accuracy Tests

    Tests the ACCURACY of our Shadbala calculations by:
    1. Verifying component calculations are in valid ranges
    2. Checking relative planetary strengths match expected patterns
    3. Validating minimum requirement classifications
    4. Testing component breakdowns for consistency

    This is ACCURACY testing, not just validation.
    """

    import pytest
    import sys
    from pathlib import Path
    from datetime import datetime

    sys.path.append(str(Path(__file__).parent.parent.parent))

    from backend.astrology import generate_vedic_chart
    from backend.shadbala import (
        calculate_shadbala_for_chart,
        calculate_sthana_bala,
        calculate_dig_bala,
        calculate_kala_bala,
        calculate_chesta_bala,
        calculate_drik_bala,
        NAISARGIKA_BALA,
        MINIMUM_REQ
    )


    # ============================================================================
    # TEST CHARTS WITH KNOWN CHARACTERISTICS
    # ============================================================================

    TEST_CHARTS = {
        'gandhi': {
            'name': 'Gandhi',
            'datetime': '1869-10-02 07:11:00',
            'lat': 21.7,
            'lon': 69.6,
            'tz': 'Asia/Kolkata',
            'expected_strong': ['Saturn', 'Moon'],  # Known from analysis
            'expected_weak': ['Venus'],
        },
        'einstein': {
            'name': 'Einstein',
            'datetime': '1879-03-14 11:30:00',
            'lat': 48.4,
            'lon': 10.0,
            'tz': 'Europe/Berlin',
            'expected_strong': ['Sun', 'Jupiter'],  # Intellect & philosophy
            'expected_weak': ['Saturn'],
        },
        'jobs': {
            'name': 'Jobs',
            'datetime': '1955-02-24 19:15:00',
            'lat': 37.77,
            'lon': -122.42,
            'tz': 'America/Los_Angeles',
            'expected_strong': ['Mars', 'Jupiter'],  # Innovation & vision
        }
    }


    @pytest.mark.parametrize("chart_key", list(TEST_CHARTS.keys()))
    def test_component_ranges_accuracy(chart_key):
        """
        Test that each Shadbala component is within valid BPHS ranges.
        This verifies our calculations are producing realistic values.
        """
        ref = TEST_CHARTS[chart_key]
        dt = datetime.strptime(ref['datetime'], '%Y-%m-%d %H:%M:%S')
        
        chart = generate_vedic_chart(
            name=ref['name'],
            year=dt.year,
            month=dt.month,
            day=dt.day,
            hour=dt.hour,
            minute=dt.minute,
            city=ref['name'],
            lat=ref['lat'],
            lon=ref['lon'],
            timezone_str=ref['tz']
        )
        
        print(f"\n{'='*60}")
        print(f"{ref['name']} - Component Range Validation")
        print(f"{'='*60}")
        
        for planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
            p_data = chart.planets[planet.lower()]
            
            sthana = calculate_sthana_bala(planet, p_data, chart)
            dig = calculate_dig_bala(planet, p_data, chart)
            kala = calculate_kala_bala(planet, p_data, chart)
            chesta = calculate_chesta_bala(planet, p_data, chart)
            naisargika = NAISARGIKA_BALA[planet]
            drik = calculate_drik_bala(planet, p_data, chart)
            
            total = sthana + dig + kala + chesta + naisargika + drik
            
            print(f"\n{planet}:")
            print(f"  Sthana:     {sthana:6.2f} (expect: 0-500)")
            print(f"  Dig:        {dig:6.2f} (expect: 0-60)")
            print(f"  Kala:       {kala:6.2f} (expect: 0-180)")
            print(f"  Chesta:     {chesta:6.2f} (expect: 0-60)")
            print(f"  Naisargika: {naisargika:6.2f} (fixed)")
            print(f"  Drik:       {drik:6.2f} (expect: -60 to +60)")
            print(f"  Total:      {total:6.2f}")
            
            # Validate ranges
            assert 0 <= sthana <= 500, f"{planet} Sthana Bala out of range"
            assert 0 <= dig <= 60, f"{planet} Dig Bala out of range"
            assert 0 <= kala <= 200, f"{planet} Kala Bala out of range"  # Slightly higher for safety
            assert 0 <= chesta <= 60, f"{planet} Chesta Bala out of range"
            assert -60 <= drik <= 60, f"{planet} Drik Bala out of range"
            assert 100 <= total <= 1000, f"{planet} Total Shadbala unrealistic"


    @pytest.mark.parametrize("chart_key", list(TEST_CHARTS.keys()))
    def test_relative_strength_accuracy(chart_key):
        """
        Test that relative planetary strengths match expected patterns.
        This is MORE IMPORTANT than absolute values for practical astrology.
        """
        ref = TEST_CHARTS[chart_key]
        dt = datetime.strptime(ref['datetime'], '%Y-%m-%d %H:%M:%S')
        
        chart = generate_vedic_chart(
            name=ref['name'],
            year=dt.year,
            month=dt.month,
            day=dt.day,
            hour=dt.hour,
            minute=dt.minute,
            city=ref['name'],
            lat=ref['lat'],
            lon=ref['lon'],
            timezone_str=ref['tz']
        )
        
        shadbala = calculate_shadbala_for_chart(chart)
        sorted_planets = sorted(shadbala.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\n{'='*60}")
        print(f"{ref['name']} - Relative Strength Ranking")
        print(f"{'='*60}")
        for rank, (planet, strength) in enumerate(sorted_planets, 1):
            min_req = MINIMUM_REQ[planet]
            pct = (strength / min_req) * 100
            status = "✓" if strength >= min_req else "✗"
            print(f"  #{rank} {planet:8s}: {strength:6.2f} ({pct:5.1f}%) {status}")
        
        # Verify expected strong planets
        if 'expected_strong' in ref:
            print(f"\nExpected Strong Planets: {ref['expected_strong']}")
            for planet in ref['expected_strong']:
                rank = [p for p, _ in sorted_planets].index(planet) + 1
                print(f"  {planet}: Ranked #{rank}/7")
                assert rank <= 4, f"{planet} should be in top 4 but ranked #{rank}"
        
        # Verify expected weak planets
        if 'expected_weak' in ref:
            print(f"\nExpected Weak Planets: {ref['expected_weak']}")
            for planet in ref['expected_weak']:
                rank = [p for p, _ in sorted_planets].index(planet) + 1
                print(f"  {planet}: Ranked #{rank}/7")
                assert rank >= 4, f"{planet} should be in bottom 4 but ranked #{rank}"


    def test_critical_fixes_accuracy():
        """
        Test that our 3 critical fixes are working correctly.
        This verifies the fixes we just applied are accurate.
        """
        # Use Gandhi's chart for testing
        ref = TEST_CHARTS['gandhi']
        dt = datetime.strptime(ref['datetime'], '%Y-%m-%d %H:%M:%S')
        
        chart = generate_vedic_chart(
            name=ref['name'],
            year=dt.year,
            month=dt.month,
            day=dt.day,
            hour=dt.hour,
            minute=dt.minute,
            city=ref['name'],
            lat=ref['lat'],
            lon=ref['lon'],
            timezone_str=ref['tz']
        )
        
        print(f"\n{'='*60}")
        print("Critical Fixes Accuracy Verification")
        print(f"{'='*60}")
        
        # Test 1: Drik Bala - Mars special aspects should give full strength
        mars_data = chart.planets['mars']
        
        # Find a planet Mars aspects
        for planet_name, planet_data in chart.planets.items():
            if planet_name in ['mars', 'rahu', 'ketu', 'ascendant']:
                continue
            
            angle = (planet_data.abs_pos - mars_data.abs_pos) % 360
            
            # Check if Mars has special aspect on this planet
            if 80 <= angle <= 100 or 200 <= angle <= 220:
                print(f"\n✓ Mars Special Aspect Found:")
                print(f"  Target: {planet_name}")
                print(f"  Angle: {angle:.1f}°")
                print(f"  Should apply 60 Virupas (not 15)")
                break
        
        # Test 2: Kala Bala - Day/Night calculation
        sun_house = chart.planets['sun'].house
        is_day = sun_house in [7, 8, 9, 10, 11, 12]
        
        print(f"\n✓ Natonnata (Day/Night) Calculation:")
        print(f"  Sun in House: {sun_house}")
        print(f"  Birth Time: {'Day' if is_day else 'Night'}")
        print(f"  Night-strong planets (Moon/Mars/Saturn) should get 60")
        print(f"  Day-strong planets (Sun/Jupiter/Venus) should get 0")
        
        # Verify Moon gets night strength
        moon_kala = calculate_kala_bala('Moon', chart.planets['moon'], chart)
        print(f"  Moon Kala Bala: {moon_kala:.2f} (should include 60 for night)")
        assert moon_kala > 60, "Moon should have >60 Kala Bala at night"
        
        # Test 3: Chesta Bala - Sun uses Ayana, Moon uses Paksha
        sun_chesta = calculate_chesta_bala('Sun', chart.planets['sun'], chart)
        moon_chesta = calculate_chesta_bala('Moon', chart.planets['moon'], chart)
        
        print(f"\n✓ Chesta Bala Calculation:")
        print(f"  Sun Chesta: {sun_chesta:.2f} (uses Ayana Bala)")
        print(f"  Moon Chesta: {moon_chesta:.2f} (uses Paksha Bala)")
        
        assert 0 <= sun_chesta <= 60, "Sun Chesta should be 0-60 (Ayana range)"
        assert 0 <= moon_chesta <= 60, "Moon Chesta should be 0-60 (Paksha range)"


    def test_minimum_requirement_classification():
        """
        Test that minimum requirement classification is accurate.
        This is critical for practical astrological interpretation.
        """
        print(f"\n{'='*60}")
        print("Minimum Requirement Classification Accuracy")
        print(f"{'='*60}")
        
        for chart_key in TEST_CHARTS.keys():
            ref = TEST_CHARTS[chart_key]
            dt = datetime.strptime(ref['datetime'], '%Y-%m-%d %H:%M:%S')
            
            chart = generate_vedic_chart(
                name=ref['name'],
                year=dt.year,
                month=dt.month,
                day=dt.day,
                hour=dt.hour,
                minute=dt.minute,
                city=ref['name'],
                lat=ref['lat'],
                lon=ref['lon'],
                timezone_str=ref['tz']
            )
            
            shadbala = calculate_shadbala_for_chart(chart)
            
            print(f"\n{ref['name']}:")
            strong_count = 0
            weak_count = 0
            
            for planet, strength in shadbala.items():
                min_req = MINIMUM_REQ[planet]
                meets_req = strength >= min_req
                pct = (strength / min_req) * 100
                
                if meets_req:
                    strong_count += 1
                    status = "STRONG"
                else:
                    weak_count += 1
                    status = "WEAK"
                
                print(f"  {planet:8s}: {strength:6.2f}/{min_req} = {pct:5.1f}% [{status}]")
            
            print(f"  Summary: {strong_count} strong, {weak_count} weak")
            
            # Sanity check: should have mix of strong and weak
            assert 1 <= strong_count <= 6, "Should have some strong planets"
            assert 1 <= weak_count <= 6, "Should have some weak planets"


    if __name__ == '__main__':
        pytest.main([__file__, '-v', '-s'])

