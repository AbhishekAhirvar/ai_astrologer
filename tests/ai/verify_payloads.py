#!/usr/bin/env python3
"""
Verify payload output for all 4 bots
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.astrology import generate_vedic_chart
from backend.ai import get_bot_config
import json

# Sample chart data
chart = generate_vedic_chart(
    name="TestUser",
    year=1990, month=5, day=15,
    hour=10, minute=30,
    city="Mumbai",
    lat=19.0760, lon=72.8777,
    timezone_str="Asia/Kolkata",
    
)

print("=" * 80)
print("PAYLOAD VERIFICATION FOR ALL 4 BOTS")
print("=" * 80)

# Test each bot
configs = [
    ("Parashara", False, "pro", "OMKAR_PRO"),
    ("Parashara", False, "lite", "OMKAR_LITE"),
    ("KP", True, "pro", "JYOTI_PRO"),
    ("KP", True, "lite", "JYOTI_LITE"),
]

sample_query = "Will I succeed in my career?"

for system_name, is_kp, mode, bot_name in configs:
    print(f"\n{'='*80}")
    print(f"{bot_name} ({system_name} {mode.upper()})")
    print("=" * 80)
    
    prompt, builder = get_bot_config(is_kp, mode)
    
    # Build payload
    if mode == "pro":
        payload = builder(chart, sample_query)
    else:
        payload = builder(chart)
    
    print(f"Payload size: {len(payload)} chars")
    print(f"\nPayload preview (first 500 chars):")
    print("-" * 80)
    print(payload[:500])
    if len(payload) > 500:
        print(f"... ({len(payload) - 500} more chars)")
    print()

print("\n" + "=" * 80)
print("✓ Payload verification complete")
print("=" * 80)
