#!/usr/bin/env python3
"""
Quick Demo: Test Prediction Accuracy (Single Question)

This is a lightweight demo that tests just ONE question for ONE person
to show how the accuracy testing works without consuming many API credits.
"""

import sys
import os
import asyncio
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.astrology import generate_vedic_chart
from backend.ai import get_astrology_prediction
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


async def quick_demo():
    """Quick demo with Steve Jobs - single question"""
    
    print("\n" + "="*80)
    print("🚀 QUICK DEMO: Prediction Accuracy Test")
    print("="*80)
    print("\nTesting: Steve Jobs")
    print("Question: What is my career path and potential?")
    print("\n" + "-"*80)
    
    # Generate chart
    print("\n⏳ Generating birth chart...")
    chart = generate_vedic_chart(
        name="Steve Jobs",
        year=1955,
        month=2,
        day=24,
        hour=19,
        minute=15,
        city="San Francisco",
        lat=37.7749,
        lon=-122.4194,
        timezone_str="America/Los_Angeles"
    )
    
    # Get prediction
    print("⏳ Getting AI prediction...")
    prediction = await get_astrology_prediction(
        chart_data=chart,
        user_query="What is my career path and potential?",
        api_key=api_key
    )
    
    # Display results
    print("\n" + "="*80)
    print("🤖 AI PREDICTION:")
    print("="*80)
    print(f"\n{prediction}\n")
    
    print("="*80)
    print("📚 KNOWN FACTS ABOUT STEVE JOBS:")
    print("="*80)
    
    known_facts = [
        "✓ Founded Apple Computer at age 21",
        "✓ Revolutionized personal computing industry",
        "✓ Known for innovation and design aesthetics",
        "✓ Fired from Apple in 1985, returned in 1997",
        "✓ Created multiple billion-dollar companies (Apple, Pixar, NeXT)",
        "✓ Perfectionist and demanding leader",
        "✓ Charismatic public speaker and visionary"
    ]
    
    for fact in known_facts:
        print(f"\n{fact}")
    
    print("\n" + "="*80)
    print("🎯 ANALYSIS:")
    print("="*80)
    
    # Simple keyword matching
    keywords_to_check = [
        ("innovation", "innovate", "innovator"),
        ("success", "successful", "achieve"),
        ("leader", "leadership"),
        ("technology", "computer", "computing"),
        ("business", "company", "entrepreneur"),
        ("creative", "creativity", "design"),
        ("visionary", "vision")
    ]
    
    matches = []
    prediction_lower = prediction.lower()
    
    for keyword_group in keywords_to_check:
        for keyword in keyword_group:
            if keyword in prediction_lower:
                matches.append(f"✅ Found: '{keyword}'")
                break
    
    if matches:
        print(f"\n🎉 Prediction contained {len(matches)}/{len(keywords_to_check)} relevant career keywords:\n")
        for match in matches:
            print(f"   {match}")
    else:
        print("\n⚠️  No matching keywords found")
    
    accuracy = (len(matches) / len(keywords_to_check)) * 100
    print(f"\n📊 Simple Accuracy Score: {accuracy:.1f}%")
    
    print("\n" + "="*80)
    print("💡 INTERPRETATION:")
    print("="*80)
    print("""
This is a very basic keyword-matching approach to show how the test works.

Real astrological validation would require:
- Expert astrologer review
- Timing predictions (when events occurred)
- Blind tests (astrologer doesn't know the person)
- Larger sample sizes
- Peer review

This test is useful for:
✓ Checking the AI isn't giving generic responses
✓ Validating chart calculations work correctly
✓ Testing prediction consistency
✓ Development and debugging

NOT useful for:
✗ Claiming scientific validity
✗ Production accuracy metrics
✗ Marketing claims
    """)
    
    print("="*80 + "\n")


if __name__ == "__main__":
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found")
        print("Please add it to your .env file")
        sys.exit(1)
    
    asyncio.run(quick_demo())
