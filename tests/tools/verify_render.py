import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.astrology import generate_vedic_chart
from backend.chart_renderer import generate_all_charts
from app import create_planetary_table_image, create_detailed_nakshatra_table
import shutil

def verify_rendering():
    name = "Abhishek"
    year, month, day = 2025, 12, 27
    hour, minute = 12, 0
    city = "New Delhi"
    lat, lon = 28.6139, 77.2090
    
    output_dir = "test_outputs"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    
    print("--- Generating Chart Data ---")
    chart = generate_vedic_chart(name, year, month, day, hour, minute, city, lat, lon)
    
    print("--- Testing Divisional Charts Rendering ---")
    try:
        chart_images = generate_all_charts(chart, person_name=name, output_dir=output_dir)
        for k, v in chart_images.items():
            if v and os.path.exists(v):
                print(f"SUCCESS: {k} chart generated at {v}")
            else:
                print(f"FAILURE: {k} chart generation failed")
    except Exception as e:
        print(f"ERROR in generate_all_charts: {e}")

    print("\n--- Testing Planetary Table Rendering ---")
    table_path = os.path.join(output_dir, f"{name}_planetary_table.png")
    try:
        create_planetary_table_image(chart, table_path)
        if os.path.exists(table_path):
            print(f"SUCCESS: Planetary table generated at {table_path}")
        else:
            print("FAILURE: Planetary table generation failed")
    except Exception as e:
        print(f"ERROR in create_planetary_table_image: {e}")

    print("\n--- Testing Nakshatra Detailed Table Rendering ---")
    nak_table_path = os.path.join(output_dir, f"{name}_nakshatra_detailed.png")
    try:
        create_detailed_nakshatra_table(chart, nak_table_path)
        if os.path.exists(nak_table_path):
            print(f"SUCCESS: Nakshatra detailed table generated at {nak_table_path}")
        else:
            print("FAILURE: Nakshatra detailed table generation failed")
    except Exception as e:
        print(f"ERROR in create_detailed_nakshatra_table: {e}")

if __name__ == "__main__":
    verify_rendering()
