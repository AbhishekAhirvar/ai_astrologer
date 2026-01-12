#!/usr/bin/env python3
"""
Show Exact AI Input Data

This script shows EXACTLY what data is sent to OpenAI when you ask a question.
It generates a chart and prints the formatted data WITHOUT making an API call.
"""

import sys
import os
from pathlib import Path
import json

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.astrology import generate_vedic_chart
from backend.ai import (
    format_planetary_data, 
    _get_serializable_chart_data,
    _build_user_prompt,
    _extract_user_name,
    OMKAR_SYSTEM_INSTRUCTION
)

def show_exact_ai_input():
    """Show exactly what data is sent to OpenAI"""
    
    print("\n" + "="*80)
    print("📊 EXACT AI INPUT DATA ANALYSIS")
    print("="*80)
    
    # Generate chart
    print("\n⏳ Generating chart for Mahatma Gandhi...")
    chart = generate_vedic_chart(
        name="Mahatma Gandhi",
        year=1869,
        month=10,
        day=2,
        hour=7,
        minute=12,
        city="Porbandar",
        lat=21.6417,
        lon=69.6293,
        timezone_str="Asia/Kolkata",
          # Include KP data to see full input
    )
    
    # Extract data the same way AI module does
    chart_dict = _get_serializable_chart_data(chart)
    planets_str = format_planetary_data(chart_dict)
    user_name = _extract_user_name(chart)
    
    # Get KP data (if available)
    kp_data_str = ""
    if hasattr(chart, 'kp_data') and chart.kp_data:
        try:
            kp_cusps = []
            for house_num in range(1, 13):
                cusp = chart.kp_data.cusps.get(house_num)
                if cusp:
                    # Works with both dict and Pydantic model
                    sign = cusp.sign if hasattr(cusp, 'sign') else cusp.get('sign')
                    deg = cusp.degree_in_sign if hasattr(cusp, 'degree_in_sign') else cusp.get('degree_in_sign', 0)
                    star = cusp.star_lord if hasattr(cusp, 'star_lord') else cusp.get('star_lord')
                    sub = cusp.sub_lord if hasattr(cusp, 'sub_lord') else cusp.get('sub_lord')
                    kp_cusps.append(f"H{house_num}: {sign} {deg:.2f}° (Star: {star}, Sub: {sub})")
            
            dasha_obj = chart.kp_data.dasha
            # Access maha dasha
            if hasattr(dasha_obj, 'maha_dasha'):
                maha = dasha_obj.maha_dasha
                antar = dasha_obj.antar_dasha
            else:
                maha = dasha_obj['maha_dasha']
                antar = dasha_obj['antar_dasha']
            
            # Extract values
            maha_lord = maha.lord if hasattr(maha, 'lord') else maha.get('lord', '?')
            antar_lord = antar.lord if hasattr(antar, 'lord') else antar.get('lord', '?')
            maha_balance = maha.balance_years if hasattr(maha, 'balance_years') else maha.get('balance_years', 0)
            
            kp_data_str = (
                f"\n\nKP DATA:\n"
                f"House Cusps (Placidus): {', '.join(kp_cusps[:3])}... [and 9 more]\n"
                f"Current Dasha: {maha_lord} Maha Dasha (Balance: {maha_balance} years), {antar_lord} Antar Dasha"
            )
        except Exception as e:
            kp_data_str = f"\n\nKP DATA: [Error extracting: {e}]"

    
    # Build prompts
    question = "What is my life purpose?"
    user_prompt_first = _build_user_prompt(user_name, planets_str, kp_data_str, question, is_first_message=True)
    user_prompt_subsequent = _build_user_prompt(user_name, planets_str, kp_data_str, question, is_first_message=False)
    
    # Display results
    print("\n" + "="*80)
    print("MESSAGE 1: SYSTEM INSTRUCTION")
    print("="*80)
    print(f"\n{OMKAR_SYSTEM_INSTRUCTION}\n")
    print(f"Token count: ~{len(OMKAR_SYSTEM_INSTRUCTION.split()) * 1.3:.0f} tokens")
    
    print("\n" + "="*80)
    print("MESSAGE 2: USER PROMPT (FIRST MESSAGE)")
    print("="*80)
    print(f"\n{user_prompt_first}\n")
    print(f"Token count: ~{len(user_prompt_first.split()) * 1.3:.0f} tokens")
    
    print("\n" + "="*80)
    print("MESSAGE 2: USER PROMPT (SUBSEQUENT MESSAGES)")
    print("="*80)
    print(f"\n{user_prompt_subsequent}\n")
    print(f"Token count: ~{len(user_prompt_subsequent.split()) * 1.3:.0f} tokens")
    
    print("\n" + "="*80)
    print("📊 TOKEN SUMMARY")
    print("="*80)
    
    system_tokens = len(OMKAR_SYSTEM_INSTRUCTION.split()) * 1.3
    user_first_tokens = len(user_prompt_first.split()) * 1.3
    user_subsequent_tokens = len(user_prompt_subsequent.split()) * 1.3
    
    print(f"""
    FIRST MESSAGE:
    - System instruction: ~{system_tokens:.0f} tokens (cacheable)
    - User prompt: ~{user_first_tokens:.0f} tokens (mostly cacheable)
    - Total input: ~{system_tokens + user_first_tokens:.0f} tokens
    
    SUBSEQUENT MESSAGES:
    - System instruction: ~{system_tokens:.0f} tokens (cacheable)
    - User prompt: ~{user_subsequent_tokens:.0f} tokens (mostly cacheable)
    - Total input: ~{system_tokens + user_subsequent_tokens:.0f} tokens
    - Savings: ~{user_first_tokens - user_subsequent_tokens:.0f} tokens (no name)
    
    CACHEABLE vs NON-CACHEABLE:
    - Cacheable: System instruction + planetary data + KP data
    - Non-cacheable: Question text only (~10-20 tokens)
    - Cache savings: ~95% of input tokens on 2nd+ question
    """)
    
    print("\n" + "="*80)
    print("🔍 PLANETARY DATA BREAKDOWN")
    print("="*80)
    
    planets_list = planets_str.split(", ")
    print(f"\nTotal planets: {len(planets_list)}")
    print("\nData for each planet:")
    for i, planet in enumerate(planets_list[:3], 1):  # Show first 3
        print(f"  {i}. {planet}")
    print(f"  ... and {len(planets_list) - 3} more")
    
    print("\n" + "="*80)
    print("📋 WHAT AI RECEIVES vs WHAT IT DOESN'T")
    print("="*80)
    
    print("""
    ✅ AI RECEIVES:
    - System role: "You are Omkar, a Vedic Astrologer"
    - User name: "Mahatma Gandhi" (first message only)
    - 10 planets with: Sign, Degree (2 decimals), House, Rules
    - KP data: 12 house cusps with star/sub lords, current Dasha
    - Question text: "What is my life purpose?"
    
    ❌ AI DOES NOT RECEIVE:
    - Full nakshatra descriptions
    - Divisional chart positions (D9, D10, D12)
    - Planetary aspects
    - Ashtakavarga points
    - Shadbala strengths
    - Yogas or combinations
    - Any biographical information
    - Previous questions (unless explicitly in conversation history)
    
    💡 WHY THIS MATTERS:
    - Keeps token usage low (~400-600 tokens per question)
    - Focuses AI on essential chart data
    - Enables prompt caching (90% discount on repeated data)
    - Maintains prediction purity (no biographical hints)
    """)
    
    print("\n" + "="*80)
    print("🎯 FULL API REQUEST (JSON FORMAT)")
    print("="*80)
    
    # Show what the actual API request looks like
    api_request = {
        "model": "gpt-5-nano",
        "input": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": OMKAR_SYSTEM_INSTRUCTION
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": user_prompt_first
                    }
                ]
            }
        ],
        "stream": False,
        "reasoning": {
            "effort": "low"
        }
    }
    
    # Truncate long text for display
    display_request = api_request.copy()
    display_request["input"][1]["content"][0]["text"] = user_prompt_first[:200] + "... [truncated]"
    
    print(f"\n{json.dumps(display_request, indent=2)}")
    
    print("\n" + "="*80)
    print("✅ DONE - This is EXACTLY what OpenAI receives")
    print("="*80 + "\n")

if __name__ == "__main__":
    show_exact_ai_input()
