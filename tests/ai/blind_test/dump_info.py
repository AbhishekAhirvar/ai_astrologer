
import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime
import json
import swisseph as swe

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from backend.astrology import generate_vedic_chart, calculate_julian_day
from backend.ai import _build_kp_pro_payload
from backend.ai_prompts import JYOTI_PRO_SYSTEM
from backend.shadbala import calculate_shadbala_for_chart
from backend.dasha_system import VimshottariDashaSystem
from backend.kp_calculations import generate_kp_data
from backend.schemas import KPData, ShadbalaData
import pytz

def dump_info():
    print("="*80)
    print("🤖 AI INFORMATION DUMP FOR ANALYSIS")
    print("="*80)
    
    # SYSTEM PROMPT
    print("\n[1] SYSTEM INSTRUCTION (JYOTI_PRO):")
    print("-" * 40)
    print(JYOTI_PRO_SYSTEM)
    print("-" * 40)
    
    # PAYLOAD
    print("\n[2] GENERATING PAYLOAD FOR EINSTEIN...")
    
    # 1. Subject Data (Einstein)
    subject = {
        "id": "Subject-1LV76F",
        "birth_data": {
            "year": 1879, "month": 3, "day": 14,
            "hour": 11, "minute": 30,
            "location_display": "Ulm, Germany",
            "lat": 48.4011, "lon": 9.9876,
            "timezone": "Europe/Berlin"
        }
    }
    
    birth_data = subject["birth_data"]
    
    # 2. Generate Chart
    chart = generate_vedic_chart(
        name=subject["id"], 
        year=birth_data["year"],
        month=birth_data["month"],
        day=birth_data["day"],
        hour=birth_data["hour"],
        minute=birth_data["minute"],
        city=birth_data["location_display"],
        lat=birth_data["lat"],
        lon=birth_data["lon"],
        timezone_str=birth_data["timezone"]
    )
    
    # 3. Enrich Chart (Shadbala, Dasha, KP)
    chart.shadbala = ShadbalaData(total_shadbala=calculate_shadbala_for_chart(chart))
    
    dasha_sys = VimshottariDashaSystem()
    now_utc = datetime.now(pytz.UTC)
    cur_jd = calculate_julian_day(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, "UTC") # Dynamic current date!
    birth_jd = calculate_julian_day(birth_data["year"], birth_data["month"], birth_data["day"], 
                                   birth_data["hour"], birth_data["minute"], birth_data["timezone"])
    moon_pos = chart.planets['moon'].abs_pos
    chart.complete_dasha = dasha_sys.calculate_complete_dasha(moon_pos, birth_jd, cur_jd)
    
    pp_positions = {p: {"longitude": pos.abs_pos} for p, pos in chart.planets.items()}
    if hasattr(chart, 'ascendant') and chart.ascendant:
        pp_positions['ascendant'] = {"longitude": chart.ascendant}
        
    chart.kp_data = KPData(**generate_kp_data(
        jd=birth_jd,
        lat=birth_data["lat"],
        lon=birth_data["lon"],
        planetary_positions=pp_positions,
        moon_lon=moon_pos
    ))
    
    # 4. Build Payload
    # Fake user query to simulate real call
    query = "Will I achieve recognition in my field?"
    payload = _build_kp_pro_payload(chart, query)
    
    print("\n[3] PAYLOAD SENT TO AI:")
    print("-" * 40)
    print(payload)
    print("-" * 40)
    
    print("\n✅ DUMP COMPLETE")

if __name__ == "__main__":
    dump_info()
