
import sys
import os
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

def extract_full_payloads():
    # Setup results dir
    results_dir = Path(__file__).parent / "payload_dumps"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Generate sample chart (Steve Jobs)
    print("Generating Chart...")
    chart = generate_vedic_chart(
        name="Steve Jobs",
        year=1955, month=2, day=24,
        hour=19, minute=15,
        city="San Francisco", lat=37.77, lon=-122.42,
        timezone_str="America/Los_Angeles",
        
    )

    user_query = "What is my primary life purpose?"

    # === 1. KP MODE PAYLOAD ===
    print("Building KP Payload...")
    # System Instruction
    kp_sys = OMKAR_SYSTEM_INSTRUCTION_V2.format(user_name="Steve Jobs")
    # Context
    kp_context = _build_optimized_json_context(chart)
    # User Prompt
    kp_user = _build_optimized_user_prompt(kp_context, user_query)
    
    kp_full = [
        {"role": "system", "content": kp_sys},
        {"role": "user", "content": kp_user}
    ]
    
    kp_file = results_dir / "kp_full_payload.json"
    with open(kp_file, 'w') as f:
        json.dump(kp_full, f, indent=2)

    # === 2. PARASHARA MODE PAYLOAD ===
    print("Building Parashara Payload...")
    # System Instruction
    parashara_sys = OMKAR_SYSTEM_INSTRUCTION.format(user_name="Steve Jobs")
    
    # Context Processing
    chart_dict = _get_serializable_chart_data(chart)
    planets_str = format_planetary_data(chart_dict)
    
    # Generic Dasha/Shadbala for example
    shadbala_str = ""
    if hasattr(chart, 'shadbala') and chart.shadbala:
        sb = chart.shadbala.total_shadbala
        sb_list = [f"{k}: {v:.1f}" for k, v in sb.items()]
        shadbala_str = f"\n\nSHADBALA: {', '.join(sb_list)}"
        
    full_context_str = f"\n\nDASHA: (Current Dasha Hierarchy){shadbala_str}"
    
    # User Prompt
    parashara_user = _build_user_prompt("Steve Jobs", planets_str, full_context_str, user_query, is_first_message=True)
    
    parashara_full = [
        {"role": "system", "content": parashara_sys},
        {"role": "user", "content": parashara_user}
    ]
    
    parashara_file = results_dir / "parashara_full_payload.json"
    with open(parashara_file, 'w') as f:
        json.dump(parashara_full, f, indent=2)

    print(f"\n✅ Payloads extracted to {results_dir}")
    print(f"   1. {kp_file.name}")
    print(f"   2. {parashara_file.name}")

if __name__ == "__main__":
    extract_full_payloads()
