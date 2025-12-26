import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.astrology import generate_vedic_chart
import json

def verify_test_chart():
    # Example birth details (You can change these to match your known data)
    name = "Test User"
    year, month, day = 1990, 1, 15
    hour, minute = 12, 30
    city = "New Delhi"
    lat, lon = 28.6139, 77.2090
    
    print(f"--- Generating Chart for: {name} ---")
    print(f"Details: {year}-{month}-{day} {hour}:{minute} at {city}\n")
    
    chart = generate_vedic_chart(name, year, month, day, hour, minute, city, lat, lon)
    
    if "error" in chart:
        print(f"Error: {chart['error']}")
        return

    # 1. Planetary Table
    print(f"{'Planet':<12} | {'Karaka':<6} | {'Degree':<10} | {'Rasi':<12} | {'Navamsa':<12} | {'Nakshatra':<15} | {'Pada':<4} | {'Relationship':<15}")
    print("-" * 105)
    
    planets = ['ascendant', 'sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']
    
    for p_key in planets:
        p = chart.get(p_key, {})
        nak = p.get('nakshatra', {})
        d9 = chart.get('d9_chart', {}).get(p_key, {})
        
        print(f"{p.get('name', p_key.capitalize()):<12} | "
              f"{p.get('karaka', '-'):<6} | "
              f"{p.get('degree', 0):>8.2f}° | "
              f"{p.get('sign', 'N/A'):<12} | "
              f"{d9.get('sign', 'N/A'):<12} | "
              f"{nak.get('nakshatra', 'N/A'):<15} | "
              f"{nak.get('pada', 'N/A'):<4} | "
              f"{p.get('relationship', 'N/A'):<15}")

    # 2. D10 Verification
    print("\n--- D10 (Dasamsa) Signs ---")
    d10 = chart.get('d10_chart', {})
    for p_key in planets:
        p_d10 = d10.get(p_key, {})
        print(f"{p_key.capitalize():<12}: {p_d10.get('sign', 'N/A')}")

    # 3. House Lords Info
    print("\n--- House Info ---")
    for p_key in planets:
        p = chart.get(p_key, {})
        if p_key == 'ascendant': continue
        print(f"{p.get('name', p_key.capitalize()):<12}: House {p.get('house', '-')} (Rules: {p.get('rules_houses', '-')})")

if __name__ == "__main__":
    verify_test_chart()
