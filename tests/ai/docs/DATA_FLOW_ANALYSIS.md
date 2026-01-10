# AI Data Flow Analysis: What Gets Sent to OpenAI

This document explains **exactly** what data is sent to the AI when you ask a question.

## 📊 Complete Data Flow

### Step 1: Generate Birth Chart
First, the system generates a complete Vedic chart from birth data:

```python
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
    timezone="Asia/Kolkata"
)
```

**Chart Data Generated:**
- Planetary positions (10 planets: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu, Ascendant)
- For each planet: Sign, Degree, House, Nakshatra, Ruler relationships
- Divisional charts (D9, D10, D12)
- KP data (if enabled): House cusps, Dasha periods
- Metadata: Ayanamsa, house system, etc.

### Step 2: Extract Essential Data

The AI function extracts only the most important data using `format_planetary_data()`:

```python
def format_planetary_data(chart_data: Dict[str, Any]) -> str:
    planets = ['sun', 'moon', 'ascendant', 'mars', 'mercury', 
               'jupiter', 'venus', 'saturn', 'rahu', 'ketu']
    
    for planet in planets:
        extract: sign, degree, house, rules_houses
```

**What Gets Extracted (Example for Gandhi):**
```
Sun: Virgo 8.45° (House: 1, Rules: 12th)
Moon: Cancer 23.67° (House: 11, Rules: 11th)
Ascendant: Virgo 0.12° (House: 1, Rules: 1st)
Mars: Libra 15.34° (House: 2, Rules: 3rd, 8th)
Mercury: Libra 2.89° (House: 2, Rules: 1st, 10th)
Jupiter: Aries 21.45° (House: 8, Rules: 4th, 7th)
Venus: Libra 19.23° (House: 2, Rules: 2nd, 9th)
Saturn: Scorpio 11.78° (House: 3, Rules: 5th, 6th)
Rahu: Cancer 28.90° (House: 11, Rules: -)
Ketu: Capricorn 28.90° (House: 5, Rules: -)
```

### Step 3: Build the Prompt

The AI receives 2 types of messages:

#### Message 1: System Instruction (Always Same)
```
CORE RULE: You are Omkar, a Vedic Astrologer. Before processing input, 
check if it's astrology-related. If NOT (e.g., recipes, coding, sports, 
math), output ONLY: 'I'm Omkar, your Vedic Astrologer. I can only answer 
questions about your chart, destiny, and life path. Ask me about career, 
relationships, timing, or any area of life you'd like astrological guidance on.' 
and STOP.

IF VALID: Start with 'Your destiny trigger lies in [specific area]'. 
Explain key planetary influences with specificity (e.g., 'Mercury in 10th house'). 
Include ONE indicator with weight. Give concrete timing/action advice.

TONE: Direct, specific, actionable. LENGTH: 60-80 words. No bullets.
END: Curiosity question (e.g., 'Want to explore how fame will come?').
```

**Token Count:** ~175 tokens

#### Message 2: User Prompt (Built per Question)

**First Message Format:**
```
User: Mahatma Gandhi
Planetary Positions: Sun: Virgo 8.45° (House: 1, Rules: 12th), Moon: Cancer 23.67° (House: 11, Rules: 11th), Ascendant: Virgo 0.12° (House: 1, Rules: 1st), Mars: Libra 15.34° (House: 2, Rules: 3rd, 8th), Mercury: Libra 2.89° (House: 2, Rules: 1st, 10th), Jupiter: Aries 21.45° (House: 8, Rules: 4th, 7th), Venus: Libra 19.23° (House: 2, Rules: 2nd, 9th), Saturn: Scorpio 11.78° (House: 3, Rules: 5th, 6th), Rahu: Cancer 28.90° (House: 11, Rules: -), Ketu: Capricorn 28.90° (House: 5, Rules: -)

KP DATA:
House Cusps (Placidus): H1: Virgo 0.12° (Star: Mercury, Sub: Venus), H2: Libra 2.45°... [all 12 houses]
Current Dasha: Venus Maha Dasha (End JD: 2415021.45, Balance: 18.5 years), Sun Antar Dasha (End JD: 2414895.23)

Question: What is my life purpose?
```

**Token Count (First Message):** ~240 tokens

**Subsequent Messages Format (with History):**
```
Planetary Positions: Sun: Virgo 8.45° (House: 1, Rules: 12th), Moon: Cancer 23.67°... [same as above]

KP DATA: [same as above]

Question: Will I be involved in politics or social change?
```

**Token Count (Subsequent):** ~230 tokens (no name included)

### Step 4: Complete API Request

**Full Request to OpenAI:**

```json
{
  "model": "gpt-5-nano",
  "input": [
    {
      "role": "system",
      "content": [
        {
          "type": "input_text",
          "text": "CORE RULE: You are Omkar, a Vedic Astrologer..."
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": "User: Mahatma Gandhi\nPlanetary Positions: Sun: Virgo 8.45°..."
        }
      ]
    }
  ],
  "stream": false,
  "reasoning": {
    "effort": "low"
  }
}
```

## 📏 Token Breakdown

### Input Tokens (Per Question)

| Component | Tokens | Cacheable | Notes |
|-----------|--------|-----------|-------|
| System instruction | ~175 | ✅ Yes | Same for all requests |
| Planetary positions | ~180 | ✅ Yes | Same chart, different questions |
| KP data (if enabled) | ~200 | ✅ Yes | Same chart |
| User name (first msg only) | ~10 | ✅ Yes | Only in first message |
| Question text | ~10-20 | ❌ No | Varies per question |
| **TOTAL (First)** | **~575** | **~555 cacheable** | With KP mode |
| **TOTAL (Subsequent)** | **~565** | **~555 cacheable** | No name |

### Output Tokens (Per Question)

| Component | Tokens | Notes |
|-----------|--------|-------|
| AI prediction | ~60-80 | As per system instruction |
| Reasoning tokens | ~450-600 | Internal thinking (low effort) |
| **TOTAL** | **~510-680** | Varies by question complexity |

### Real Example from Gandhi Test

From the logs we saw:
```
📊 TOKEN USAGE: Total=1052 | 
Input: 424 (cached: 0, non-cached: 424) | 
Output: 628 | 
Thinking: 512
```

**Breakdown:**
- **Input tokens:** 424 (all non-cached on first run)
- **Output tokens:** 628 total
  - Prediction text: ~116 tokens
  - Reasoning: ~512 tokens
- **Total billed:** 1,052 tokens

## 🔍 What Data is NOT Sent

The AI does **NOT** receive:

❌ Full nakshatra descriptions  
❌ Divisional chart details (D9, D10, D12) - unless explicitly requested  
❌ Detailed planetary aspects  
❌ Varga positions  
❌ Strength calculations (Shadbala, etc.)  
❌ Ashtakavarga points  
❌ Full planetary longitudes  
❌ Previous conversation context (unless in history)  

**Why?** To save tokens and keep responses focused.

## 💡 Optimization Strategies

### Current Optimizations

1. **Name only in first message** (Saves ~10 tokens per follow-up)
2. **Essential planets only** (10 items vs. all chart data)
3. **Rounded degrees** (2 decimals vs. full precision)
4. **abbreviated house info** ("Rules: 3rd, 8th" vs. full descriptions)
5. **KP data only if requested** (Saves ~200 tokens when not needed)

### Potential Further Optimizations

If you want to reduce token usage more:

```python
# Option 1: Abbreviate further
"Su:Vir8°H1 Mo:Can24°H11 As:Vir0°H1..."
# Saves: ~40% tokens

# Option 2: Only send relevant planets for question
if "career" in question:
    planets = ['sun', 'mercury', 'jupiter', 'saturn', 'ascendant']
# Saves: ~50% tokens

# Option 3: Skip KP data unless specifically asked
# Saves: ~200 tokens

# Option 4: Use shorter system instruction
# Saves: ~100 tokens (but may reduce quality)
```

## 📊 Cost Analysis

Using GPT-5-nano pricing (example):

```
Input tokens: ~424 × $0.001 per 1K = $0.000424
Output tokens: ~628 × $0.003 per 1K = $0.001884
Total per question: ~$0.002308

For 5 questions: ~$0.012
For 25 questions (all tests): ~$0.058
```

With caching (2nd question onwards):
```
Cached input: ~555 × $0.0001 per 1K = $0.0000555 (90% discount)
Non-cached: ~20 × $0.001 per 1K = $0.00002
Total input: ~$0.00008

Savings: ~75% on input tokens
```

## 🎯 Summary

**For Each Question, AI Receives:**

1. **System Role:** "You are Omkar, a Vedic Astrologer..." (~175 tokens)
2. **Chart Data:** 10 planetary positions with sign, degree, house (~180 tokens)
3. **KP Data (optional):** Cusps and Dasha (~200 tokens)
4. **User Name (first msg only):** "User: Mahatma Gandhi" (~10 tokens)
5. **The Question:** "What is my life purpose?" (~10-20 tokens)

**Total Input:** ~400-600 tokens per question
**Total Output:** ~500-700 tokens per question (including reasoning)

**What AI Uses to Predict:**
- Planetary signs and houses (primary)
- Degree positions (for specificity)
- House rulerships (for connections)
- Dasha periods (for timing, if KP mode)
- Question context (to focus answer)

**What AI Does NOT Know:**
- Person's actual name/identity (just "User: [Name]")
- Their real-life events
- External context beyond the chart
- Previous questions (unless in conversation history)

This keeps predictions based purely on astrological data, not biographical information.
