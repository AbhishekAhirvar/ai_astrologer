import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.ai import get_astrology_prediction, get_followup_questions
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: GEMINI_API_KEY not found in environment variables!")
    print("Please set it in your .env file")
    sys.exit(1)

# Dummy chart data
chart_data = {
    '_metadata': {
        'name': 'Test User',
        'gender': 'Male',
        'datetime': '2025-12-22 12:30',
        'location': 'New Delhi'
    },
    'sun': {'sign': 'Sagittarius', 'degree': 20},
    'moon': {'sign': 'Pisces', 'degree': 15},
    'ascendant': {'sign': 'Aries', 'degree': 10},
    # ... minimal data needed
    'jupiter': {'sign': 'Gemini', 'degree': 12}, 
}

print("\n--- Testing Standard Vedic Mode ---")
query = "What does my chart say about my career?"
print(f"Query: {query}")

# 1. Test Answer
print(">> Fetching Answer...")
answer = get_astrology_prediction(chart_data, query, api_key=api_key)
print(f"✅ AI Answer:\n{answer}\n")

# 2. Test Suggestions
print(">> Fetching Suggestions...")
suggestions = get_followup_questions(query, api_key=api_key)
print(f"✅ Suggestions: {suggestions}\n")


print("\n--- Testing KP Mode ---")
query = "Perform a KP analysis."
print(f"Query: {query}")

# 1. Test Answer
print(">> Fetching KP Answer...")
answer_kp = get_astrology_prediction(chart_data, query, api_key=api_key, is_kp_mode=True)
print(f"✅ KP Answer:\n{answer_kp}\n")

# 2. Test Suggestions
print(">> Fetching KP Suggestions...")
suggestions_kp = get_followup_questions(query, api_key=api_key, is_kp_mode=True)
print(f"✅ KP Suggestions: {suggestions_kp}\n")

