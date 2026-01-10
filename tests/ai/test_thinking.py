
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.ai import get_astrology_prediction
from backend.astrology import generate_vedic_chart

async def test_thinking():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found")
        return

    print("Generating Chart...")
    chart = generate_vedic_chart(
        name="Tester",
        year=1990, month=1, day=1,
        hour=12, minute=0,
        city="London", lat=51.5, lon=0.0,
        timezone_str="Europe/London"
    )

    print("\nRequesting Prediction with High Reasoning Effort...")
    # I'll call it. I might need to modify ai.py first to ensure it's captured.
    # For now, let's just see if it's in the logs if I modify ai.py.
    
    # We will modify ai.py to return a tuple or log the thinking.
    
    # Actually, I'll just run a prediction and check the logs after I modify ai.py.
    prediction = await get_astrology_prediction(
        chart_data=chart,
        user_query="What is my primary life purpose?",
        api_key=api_key,
        is_kp_mode=False
    )
    
    print("\n--- AI OUTPUT ---")
    print(prediction)
    print("\n--- END ---")

if __name__ == "__main__":
    asyncio.run(test_thinking())
