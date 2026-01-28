
import json
import glob
import os

# Find the latest results file
files = glob.glob("tests/ai/blind_test/results/comprehensive_MP_*.json")
if not files:
    print("No results file found.")
    exit(1)
    
latest_file = max(files, key=os.path.getctime)
print(f"Reading: {latest_file}")

with open(latest_file, 'r') as f:
    data = json.load(f)

for bot_result in data:
    bot = bot_result['bot']
    print(f"\nBot: {bot}")
    for pred in bot_result['preds']:
        payload = pred.get('payload', '')
        # DOB Check
        if "dob" in payload.lower() or "dob" in payload:
            # Simple extraction for debug
            try:
                # Find "dob":"..." or DOB:
                import re
                match = re.search(r'("dob":\s*"[^"]+"|\bDOB:[\w-]+)', payload, re.IGNORECASE)
                if match:
                    print(f"  Found: {match.group(1)}")
                else:
                    print(f"  DOB word found but regex failed. Payload start: {payload[:100]}...")
            except:
                print("  Error extracting DOB")
        else:
            print(f"  'dob' NOT found. Payload start: {payload[:100]}...")

        # Current Date Check
        if "current_date" in payload or "Now:" in payload:
             print("  ✅ Current Date/Now found.")
        else:
             print("  ❌ Current Date/Now NOT found.")
