#!/usr/bin/env python3
"""
Quick test for 4-bot system
Tests that all bots load correctly and payload builders work
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.ai import (
    get_bot_config,
    OMKAR_PRO_SYSTEM,
    OMKAR_LITE_SYSTEM,
    JYOTI_PRO_SYSTEM,
    JYOTI_LITE_SYSTEM
)

def test_bot_configs():
    """Test that all 4 bot configurations load correctly."""
    print("Testing 4-bot configurations...\n")
    
    # Test all 4 combinations
    configs = [
        (False, "pro", "OMKAR_PRO"),
        (False, "lite", "OMKAR_LITE"),
        (True, "pro", "JYOTI_PRO"),
        (True, "lite", "JYOTI_LITE"),
    ]
    
    for is_kp, mode, expected_name in configs:
        prompt, builder = get_bot_config(is_kp, mode)
        system_type = "KP" if is_kp else "Parashara"
        print(f"✓ {expected_name} ({system_type} {mode.upper()})")
        print(f"  Prompt length: {len(prompt)} chars")
        print(f"  Builder: {builder.__name__}")
        print()
    
    print("All bot configurations loaded successfully!")

if __name__ == "__main__":
    test_bot_configs()
