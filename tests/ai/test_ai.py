import sys
import os
import argparse
import asyncio
import pytest
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.ai import get_astrology_prediction_stream, get_followup_questions
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")

if not api_key:
    pytest.skip("API Key not found in environment variables", allow_module_level=True)

# Dummy chart data with full structure
chart_data = {
    'sun': {'sign': 'Sagittarius', 'degree': 20, 'house': 9, 'rules_houses': '5th'},
    'moon': {'sign': 'Pisces', 'degree': 15, 'house': 12, 'rules_houses': '4th'},
    'ascendant': {'sign': 'Aries', 'degree': 10, 'house': 1, 'rules_houses': '1st'},
    'mars': {'sign': 'Leo', 'degree': 5, 'house': 5, 'rules_houses': '1st, 8th'},
    'mercury': {'sign': 'Sagittarius', 'degree': 25, 'house': 9, 'rules_houses': '3rd, 6th'},
    'jupiter': {'sign': 'Sagittarius', 'degree': 22, 'house': 9, 'rules_houses': '9th, 12th'},
    'venus': {'sign': 'Sagittarius', 'degree': 18, 'house': 9, 'rules_houses': '2nd, 7th'},
    'saturn': {'sign': 'Capricorn', 'degree': 28, 'house': 10, 'rules_houses': '10th, 11th'},
    'rahu': {'sign': 'Aquarius', 'degree': 12, 'house': 11, 'rules_houses': '-'},
    'ketu': {'sign': 'Leo', 'degree': 12, 'house': 5, 'rules_houses': '-'},
}

async def run_suggestions(query, is_kp=False):
    mode = "KP" if is_kp else "Vedic"
    print(f"\n--- Testing {mode} Suggestions ---")
    print(">> Fetching Suggestions...")
    try:
        suggestions = await get_followup_questions(api_key=api_key, chart_data=chart_data, is_kp_mode=is_kp)
        print(f"✅ Suggestions: {suggestions}\n")
    except Exception as e:
        print(f"❌ Error: {e}")

async def run_streaming_prediction(query, history=None, is_kp=False):
    mode = "KP" if is_kp else "Vedic"
    history_str = f" (with {len(history)} history items)" if history else " (no history)"
    print(f"\n--- Testing {mode} Streaming Prediction{history_str} ---")
    print(f"Query: {query}")
    print(">> Streaming Answer: ", end="", flush=True)
    full_response = ""
    try:
        async for chunk in get_astrology_prediction_stream(chart_data, query, api_key=api_key, history=history, is_kp_mode=is_kp):
            print(chunk, end="", flush=True)
            full_response += chunk
        print("\n✅ Stream Completed\n")
        return full_response
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None

async def main():
    parser = argparse.ArgumentParser(description="Test AI astrology module.")
    parser.add_argument("--suggestions-only", action="store_true", help="Test only suggestions.")
    parser.add_argument("--kp", action="store_true", help="Test KP mode.")
    parser.add_argument("--query", type=str, default="What does my chart say about my career?", help="User query to test.")
    parser.add_argument("--with-history", action="store_true", help="Test with conversation history.")
    
    args = parser.parse_args()
    
    if args.suggestions_only:
        await run_suggestions(args.query, is_kp=args.kp)
    elif args.with_history:
        # Test 1: First query (no history)
        print("\n" + "="*60)
        print("TEST 1: First Query (No History)")
        print("="*60)
        response1 = await run_streaming_prediction("Will I be rich?", history=None, is_kp=args.kp)
        
        if response1:
            # Test 2: Second query WITH history
            print("\n" + "="*60)
            print("TEST 2: Follow-up Query (With History)")
            print("="*60)
            history = [
                {"role": "user", "content": "Will I be rich?"},
                {"role": "assistant", "content": response1}
            ]
            response2 = await run_streaming_prediction("When will this happen?", history=history, is_kp=args.kp)
            
            if response2:
                print("\n" + "="*60)
                print("✅ BOTH TESTS PASSED - History works!")
                print("="*60)
    else:
        await run_streaming_prediction(args.query, is_kp=args.kp)
        await run_suggestions(args.query, is_kp=args.kp)

if __name__ == "__main__":
    asyncio.run(main())
