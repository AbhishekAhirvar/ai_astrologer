import pytest
import logging
from backend.varga_charts import calculate_varga, ZODIAC_SIGNS

def test_calculate_varga_d12_same():
    # D12 - Same rule (D12 starts from same sign)
    # Aries 2.5 degrees -> 2nd division of D12 -> Taurus
    chart = {'sun': {'name': 'Sun', 'sign_num': 0, 'degree': 2.6}}
    res = calculate_varga(chart, 12, 'same')
    assert res['sun']['sign'] == 'Taurus'
    assert res['sun']['sign_num'] == 1
    # Check degree: (2.6 % 2.5) / 2.5 * 30 = 0.1 / 2.5 * 30 = 1.2
    assert pytest.approx(res['sun']['degree'], 0.001) == 1.2

def test_calculate_varga_d9_movable():
    # D9 - Movable sign starts from itself
    # Aries (Movable) 3.5 degrees -> 2nd division of D9 (3.33 to 6.66) -> Taurus
    # div_size = 30/9 = 3.3333...
    # 3.5 is in 2nd division (index 1)
    chart = {'sun': {'name': 'Sun', 'sign_num': 0, 'degree': 3.5}}
    res = calculate_varga(chart, 9, 'movable_fixed_dual')
    assert res['sun']['sign'] == 'Taurus'
    assert res['sun']['sign_num'] == 1

def test_calculate_varga_d9_fixed():
    # D9 - Fixed sign starts from 9th
    # Taurus (Fixed) 1 degree -> 1st division of D9 -> 9th from Taurus (Capricorn)
    chart = {'sun': {'name': 'Sun', 'sign_num': 1, 'degree': 1.0}}
    res = calculate_varga(chart, 9, 'movable_fixed_dual')
    assert res['sun']['sign'] == 'Capricorn'
    assert res['sun']['sign_num'] == 9

def test_calculate_varga_d10_odd_even():
    # D10 - Odd sign starts from itself
    chart = {'sun': {'name': 'Sun', 'sign_num': 0, 'degree': 3.5}}
    res = calculate_varga(chart, 10, 'odd_even')
    assert res['sun']['sign'] == 'Taurus'
    
    # Taurus(1) (Even in Vedic) -> 9th from it (Capricorn)
    chart2 = {'sun': {'name': 'Sun', 'sign_num': 1, 'degree': 1.0}}
    res2 = calculate_varga(chart2, 10, 'odd_even')
    assert res2['sun']['sign'] == 'Capricorn'

def test_calculate_varga_boundary_high():
    # Extreme high boundary checks
    # 29.9999 should stay as is and calculate correctly
    chart = {'sun': {'name': 'Sun', 'sign_num': 0, 'degree': 29.9999}}
    res = calculate_varga(chart, 9, 'movable_fixed_dual')
    # 29.9999 is in last (9th) division of Aries -> Sagittarius (8)
    assert res['sun']['sign'] == 'Sagittarius'
    assert res['sun']['sign_num'] == 8
    # It should be at the very end of the sign
    assert res['sun']['degree'] > 29.9

def test_calculate_varga_degree_30_capping(caplog):
    # Test strict < 30 check. Input 30.0 should trigger warning and be clamped
    chart = {'sun': {'name': 'Sun', 'sign_num': 0, 'degree': 30.0}}
    with caplog.at_level(logging.WARNING):
        res = calculate_varga(chart, 9, 'same')
    
    assert "degree 30.0 out of expected [0, 30) range" in caplog.text
    # Should still process as 29.9999 which is last division
    assert res['sun']['sign_num'] == 8 # 9th division of Aries (same rule) -> Sagittarius
    assert res['sun']['degree'] > 29.9 # Floating point math might result in 29.9991 approx

def test_calculate_varga_boundary_zero():
    # Strict 0.0 check
    chart = {'sun': {'name': 'Sun', 'sign_num': 0, 'degree': 0.0}}
    res = calculate_varga(chart, 9, 'same')
    assert res['sun']['sign'] == 'Aries'
    assert res['sun']['degree'] == 0.0

def test_invalid_divisor():
    chart = {'sun': {'name': 'Sun', 'sign_num': 0, 'degree': 10}}
    res = calculate_varga(chart, 0, 'same')
    assert res == {}

def test_invalid_rule():
    chart = {'sun': {'name': 'Sun', 'sign_num': 0, 'degree': 10}}
    res = calculate_varga(chart, 9, 'invalid_rule')
    assert res == {}

def test_non_standard_divisor_warning(caplog):
    # 13 is not a standard Vedic divisor
    chart = {'sun': {'name': 'Sun', 'sign_num': 0, 'degree': 10}}
    with caplog.at_level(logging.WARNING):
        calculate_varga(chart, 13, 'same')
    assert "Using non-standard Vedic divisor: 13" in caplog.text

def test_floating_point_stability():
    # Test a value that might cause floating point issues near boundary
    # 30 / 3 = 10.0 per division. 
    # value 10.0 should be exactly start of 2nd division, index 1
    chart = {'sun': {'name': 'Sun', 'sign_num': 0, 'degree': 10.0}}
    res = calculate_varga(chart, 3, 'same') # Drekkana-like
    # Should be 2nd division (10-20)
    assert res['sun']['sign_num'] == 1 # Taurus
    assert res['sun']['degree'] == 0.0 # Start of sign

    # value 9.999999 should be end of 1st division
    chart2 = {'sun': {'name': 'Sun', 'sign_num': 0, 'degree': 9.99999}}
    res2 = calculate_varga(chart2, 3, 'same')
    assert res2['sun']['sign_num'] == 0 # Aries
    assert res2['sun']['degree'] > 29.9
