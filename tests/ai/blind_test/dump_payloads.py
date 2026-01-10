
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from backend.astrology import generate_vedic_chart
from backend.ai import (
    _build_optimized_json_context, 
    _build_optimized_user_prompt,
    _get_serializable_chart_data,
    format_planetary_data,
    _build_user_prompt,
    OMKAR_SYSTEM_INSTRUCTION,
    OMKAR_SYSTEM_INSTRUCTION_V2
)

def dump_accurate_payloads():
    # SETUP: Use EXACT anonymous ID from blind tests
    ANON_ID = "Subject-6VUF87" 
    CHART_NAME = ANON_ID # This is the critical part
    
    chart = generate_vedic_chart(
        name=CHART_NAME, 
        year=1955, month=2, day=24,
        hour=19, minute=15,
        city="Coordinates: 37.77N, -122.42E",
        lat=37.77, lon=-122.42,
        timezone_str="America/Los_Angeles",
        include_kp_data=True
    )

    query = "What is my primary life purpose?"

    # mode 1: KP
    kp_sys = OMKAR_SYSTEM_INSTRUCTION_V2.format(user_name=ANON_ID)
    kp_context = _build_optimized_json_context(chart)
    kp_user = _build_optimized_user_prompt(kp_context, query)
    kp_payload = [{"role": "system", "content": kp_sys}, {"role": "user", "content": kp_user}]
    
    # mode 2: Parashara
    par_sys = OMKAR_SYSTEM_INSTRUCTION.format(user_name=ANON_ID)
    planets_str = format_planetary_data(_get_serializable_chart_data(chart))
    par_user = _build_user_prompt(ANON_ID, planets_str, "\n[Dasha/Shadbala Data]", query, True)
    par_payload = [{"role": "system", "content": par_sys}, {"role": "user", "content": par_user}]

    # SAVE
    with open("kp_raw.json", "w") as f: json.dump(kp_payload, f, indent=2)
    with open("parashara_raw.json", "w") as f: json.dump(par_payload, f, indent=2)

if __name__ == "__main__":
    dump_accurate_payloads()
