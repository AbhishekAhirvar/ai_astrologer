import pytest
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
    # Aries (Movable) 3.5 degrees -> 2nd division of D9 -> Taurus
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
    # Aries(0) (Odd in Vedic 1) 3.5 degrees -> 2nd division -> Taurus
    chart = {'sun': {'name': 'Sun', 'sign_num': 0, 'degree': 3.5}}
    res = calculate_varga(chart, 10, 'odd_even')
    assert res['sun']['sign'] == 'Taurus'
    
    # Taurus(1) (Even in Vedic 2) 1 degree -> 1st division -> 9th from it (Capricorn)
    chart2 = {'sun': {'name': 'Sun', 'sign_num': 1, 'degree': 1.0}}
    res2 = calculate_varga(chart2, 10, 'odd_even')
    assert res2['sun']['sign'] == 'Capricorn'

def test_calculate_varga_boundary_high():
    # Extreme boundary 29.99
    chart = {'sun': {'name': 'Sun', 'sign_num': 0, 'degree': 29.999}}
    res = calculate_varga(chart, 9, 'movable_fixed_dual')
    # Should be in 9th division of Aries -> Sagittarius
    assert res['sun']['sign'] == 'Sagittarius'
    assert res['sun']['degree'] < 30.0

def test_calculate_varga_boundary_zero():
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
