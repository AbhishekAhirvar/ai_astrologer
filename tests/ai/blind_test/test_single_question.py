"""
Quick single-question test to verify AI prediction works end-to-end
"""
import sys
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from backend.astrology import generate_vedic_chart
from backend.ai import get_astrology_prediction
from dotenv import load_dotenv

load_dotenv()

async def test_single_question():
    """Test with just one question to verify the fix"""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found")
        return
    
    print("\n🧪 Single Question Test - OMKAR_PRO\n")
    
    # Generate chart for Steve Jobs (Subject-6VUF87)
    print("📊 Generating chart...")
    chart = generate_vedic_chart(
        name="Test Subject",
        year=1955,
        month=2,
        day=24,
        hour=19,
        minute=15,
        city="San Francisco",
        lat=37.77,
        lon=-122.43,
        timezone_str="America/Los_Angeles",
        include_kp_data=True,
        include_complete_dasha=True
    )
    
    print("✅ Chart generated successfully\n")
    
    # Ask one question
    question = "What is my primary life purpose?"
    print(f"❓ Question: {question}")
    print("⏳ Waiting for AI response...\n")
    
    try:
        prediction = await get_astrology_prediction(
            chart_data=chart,
            user_query=question,
            api_key=api_key,
            is_kp_mode=False,  # Parashara mode
            bot_mode="pro"
        )
        
        print("="*80)
        print("✅ PREDICTION RECEIVED:")
        print("="*80)
        print(prediction)
        print("="*80)
        
        # Save result
        result = {
            "test_metadata": {
                "run_at": datetime.now().isoformat(),
                "test_type": "single_question_verification",
                "bot_name": "OMKAR_PRO"
            },
            "question": question,
            "prediction": prediction,
            "status": "SUCCESS" if "ERROR" not in prediction else "FAILED"
        }
        
        results_dir = Path(__file__).parent / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        results_file = results_dir / f"single_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(results_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n📁 Results saved: {results_file}")
        
        if "ERROR" in prediction:
            print("\n❌ Test FAILED - Error in prediction")
            return False
        else:
            print("\n✅ Test PASSED - Valid prediction received")
            return True
            
    except Exception as e:
        print(f"\n❌ Test FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_single_question())
    sys.exit(0 if success else 1)
