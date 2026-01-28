import sys
import os
import asyncio
import pytest
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.ai import get_astrology_prediction_stream
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    pytest.skip("API Key not found", allow_module_level=True)

# Dummy chart
chart_data = {
    'sun': {'sign': 'Sagittarius', 'degree': 20, 'house': 9, 'rules_houses': '5th'},
    'moon': {'sign': 'Pisces', 'degree': 15, 'house': 12, 'rules_houses': '4th'},
    'ascendant': {'sign': 'Aries', 'degree': 10, 'house': 1, 'rules_houses': '1st'},
}

async def test_grounding():
    print("="*60)
    print("TEST 1: Slightly off-topic (should relate to astrology)")
    print("="*60)
    print("Query: How can I be more confident?\n")
    async for chunk in get_astrology_prediction_stream(chart_data, "How can I be more confident?", api_key):
        print(chunk, end="", flush=True)
    print("\n\n")
    
    print("="*60)
    print("TEST 2: Completely off-topic (should decline)")
    print("="*60)
    print("Query: What's the best pizza recipe?\n")
    async for chunk in get_astrology_prediction_stream(chart_data, "What's the best pizza recipe?", api_key):
        print(chunk, end="", flush=True)
    print("\n\n")
    
    print("="*60)
    print("TEST 3: On-topic astrology question (normal response)")
    print("="*60)
    print("Query: When will I find success?\n")
    async for chunk in get_astrology_prediction_stream(chart_data, "When will I find success?", api_key):
        print(chunk, end="", flush=True)
    print("\n")

if __name__ == "__main__":
    asyncio.run(test_grounding())
