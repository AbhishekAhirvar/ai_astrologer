import sys
import os
import asyncio
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.ai import get_astrology_prediction
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

chart_data = {
    'sun': {'sign': 'Sagittarius', 'degree': 20, 'house': 9, 'rules_houses': '5th'},
    'moon': {'sign': 'Pisces', 'degree': 15, 'house': 12, 'rules_houses': '4th'},
    'ascendant': {'sign': 'Aries', 'degree': 10, 'house': 1, 'rules_houses': '1st'},
}

async def test_caching():
    print("="*70)
    print("CACHE VERIFICATION TEST")
    print("="*70)
    print("\n📌 Message 1: First call (nothing should be cached)")
    print("-"*70)
    
    response1 = await get_astrology_prediction(
        chart_data, 
        "What are my career prospects?", 
        api_key
    )
    print(f"Response: {response1[:100]}...")
    print("\n⏳ Wait 2 seconds...\n")
    await asyncio.sleep(2)
    
    print("="*70)
    print("📌 Message 2: Follow-up with history (system + previous should be cached)")
    print("-"*70)
    
    history = [
        {"role": "user", "content": "What are my career prospects?"},
        {"role": "assistant", "content": response1}
    ]
    
    response2 = await get_astrology_prediction(
        chart_data,
        "When will this happen?",
        api_key,
        history=history
    )
    print(f"Response: {response2[:100]}...")
    
    print("\n" + "="*70)
    print("✅ Check logs above for token breakdown:")
    print("   - Message 1 should show: cached: 0")
    print("   - Message 2 should show: cached: >0 (system + history cached)")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_caching())
