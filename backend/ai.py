import os
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from datetime import datetime
from openai import OpenAI
from backend.schemas import ChartResponse
from backend.logger import logger
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
from functools import lru_cache

load_dotenv()

# Configure OpenAI
OPENAI_MODEL = "gpt-5-nano"

# Security: Mute third-party loggers to prevent leaking request details
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

# Log model info on startup
logger.info(f"🤖 AI Module initialized with OpenAI model: {OPENAI_MODEL}")

# @lru_cache(maxsize=1)  # Commented out - not using cache to avoid token overhead
def get_openai_client(api_key: str) -> OpenAI:
    """
    Returns an OpenAI client for the given API key.
    This reuses the internal connection pool (httpx client) across requests.
    """
    return OpenAI(api_key=api_key)

def jd_to_date(jd):
    """Convert Julian Day to date string."""
    import swisseph as swe
    y, m, d, h = swe.revjul(jd)
    return f"{y}-{m:02d}-{d:02d}"

def _ensure_chart_object(chart_data: Any) -> Any:
    """
    Ensures chart_data is a proper object (ChartResponse or similar) with attribute access.
    If it's a dict, attempts to convert it to ChartResponse.
    """
    if isinstance(chart_data, dict):
        try:
            # Check if it looks like a chart dict
            if 'planets' in chart_data and 'metadata' in chart_data:
                 return ChartResponse(**chart_data)
            # Legacy or unexpected dict structure handling could be added here if needed
            # For now return as is if conversion fails, but log warning
            logger.warning("Received dict chart_data that doesn't fully match ChartResponse schema. Proceeding with dict.")
            return chart_data
        except Exception as e:
            logger.error(f"Failed to convert dict to ChartResponse: {e}")
            return chart_data
            
    return chart_data

def _extract_user_name(chart_data: Any) -> str:
    """Safely extract user name from chart data object or dict."""
    if isinstance(chart_data, dict):
        # Handle dict input (e.g. detailed payload)
        if "meta" in chart_data and "name" in chart_data["meta"]:
            return chart_data["meta"]["name"]
        return chart_data.get("name", "User")
        
    # Handle Pydantic model
    if hasattr(chart_data, 'name'):
        return chart_data.name
    # Handle legacy schema
    if hasattr(chart_data, 'subject_name'):
        return chart_data.subject_name
        
    return "User"

def format_planetary_data(chart_data: Dict[str, Any]) -> str:
    """
    Extracts and formats planetary data including Nakshatra, Retrograde, and Navamsa.
    """
    planets = ['sun', 'moon', 'ascendant', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']
    essential_data = []

    # Handle nested structure from full serializable dump
    p_source = chart_data.get('planets', chart_data)
    vargas = chart_data.get('vargas', {})
    navamsa = vargas.get('d9_chart', {})

    for p in planets:
        p_data = p_source.get(p, {})
        if p_data:
            sign = p_data.get('sign', '?')
            deg = p_data.get('degree', 0)
            house = p_data.get('house', '?')
            
            # Retrograde Status
            retro = " (R)" if p_data.get('is_retrograde') else ""
            
            # Nakshatra
            nak = "?"
            if 'nakshatra' in p_data and isinstance(p_data['nakshatra'], dict):
                nak = f"{p_data['nakshatra'].get('nakshatra', '?')} ({p_data['nakshatra'].get('pada', 1)})"
            
            # Navamsa Position
            d9_sign = "?"
            if p in navamsa:
                d9_sign = navamsa[p].get('sign', '?')
                
            essential_data.append(f"{p.capitalize()}{retro}: {sign} {deg}° in {nak} | D9: {d9_sign} | House: {house}")
    
    return "\n".join(essential_data)

def _get_serializable_chart_data(chart_data: Any) -> Dict[str, Any]:
    """Helper to convert chart data to a simple dict format."""
    if isinstance(chart_data, dict):
        return {k: v for k, v in chart_data.items() if not k.startswith('_')}
    
    # Use Pydantic dump if available to get FULL chart (including Vargas)
    if hasattr(chart_data, 'model_dump'):
        return chart_data.model_dump()
    elif hasattr(chart_data, 'dict'):
        return chart_data.dict()
        
    # Validation fallback
    if hasattr(chart_data, 'planets'):
        # ... logic as fallback ...
        return getattr(chart_data, 'planets', {})
    
    return {}

def _format_openai_message(role: str, content: Any) -> Dict[str, Any]:
    """
    Formats a message for the OpenAI Responses API (2026).
    Handles both string content and pre-formatted content lists.
    """
    # If content is already a list (from history), extract the actual text
    if isinstance(content, list):
        # Extract text from content blocks like [{"text": "...", "type": "text"}]
        if len(content) > 0 and isinstance(content[0], dict) and 'text' in content[0]:
            content = content[0]['text']
        else:
            # Fallback: use as-is if we can't parse it
            return {"role": role, "content": content}
    
    # Text-only input mode for 2026 API
    content_type = "input_text" if role in ["user", "system"] else "output_text"
    return {"role": role, "content": [{"type": content_type, "text": str(content)}]}

# Import significator engine
from backend.kp_significators import (
    build_optimized_planet_payload,
    build_optimized_house_payload,
    PLANET_CODES
)
import swisseph as swe
import json

def jd_to_date(jd: float) -> str:
    """Converts Julian Day to YYYY-MM-DD format."""
    try:
        year, month, day, hour = swe.revjul(jd)
        return f"{int(year)}-{int(month):02d}-{int(day):02d}"
    except Exception:
        return "?"

OMKAR_SYSTEM_INSTRUCTION_V2 = (
    "ROLE: You are Omkar, a legendary Vedic Astrologer using KP System. "
    "I will provide a JSON object with the user's birth chart data. "
    "KEY DEFINITIONS: "
    "'pl': Planets. Format [Sign, Star, Sub, Strength, [Significators]]. "
    "The [Significators] list contains house numbers this planet signifies - use these for predictions. "
    "'h': House cusps. Format [Sign, Sub_Lord]. Sub determines house quality. "
    "'dasha': Current timing. 'curr': [Maha, Antar, Pratyantar]. 'ends_in': Time remaining. "
    "RULES: Do NOT recalculate positions. Trust the [Significators] provided. "
    "Focus on WHAT and WHEN. Give concrete timing. "
    "TONE: Sacred, profound, absolute. Speak as a Sage who KNOWS. Never use 'may', 'can', 'could', or 'might'. "
    "be compassionate. "
    "GREETING: You are speaking to {user_name}. Address them by name in the first sentence. "
    "LENGTH: 50-70 words. No bullets. "
    "END: One curiosity-sparking question related to their destiny."
)

# Parashara/Vedic instruction for non-KP mode
OMKAR_SYSTEM_INSTRUCTION = (
    "ROLE: You are Omkar, a legendary Vedic Astrologer. "
    "GROUNDING: If the user query is COMPLETELY unrelated to astrology, life path, or personal destiny (e.g., coding, recipes, math, sports), politely refuse as Omkar. "
    "If it is SLIGHTLY related or can be linked to their journey (e.g., life challenges, general advice), guide them back to their stars and answer from an astrological perspective. "
    "IF VALID: Answer directly with wisdom. Mention 1-2 key planets maximum ONLY if critical to the answer. "
    "Focus on what user asked why he is asking, to give information he needed not just what he asked, not technical details. "
    "Give concrete timing and actionable advice. "
    "TONE: Sacred, profound, absolute. Speak as a Sage who KNOWS."
    "Be wise, and compassionate."
    "GREETING: You are speaking to {user_name}. Address them by name in the first sentence. "
    "LENGTH: 50-70 words. No bullets. "
    "END: One curiosity-sparking question related to their destiny."
)

# ==========================================
# 4-BOT SYSTEM PROMPTS
# ==========================================

# Bot 1: OMKAR_PRO - Parashara Accuracy Optimized
OMKAR_PRO_SYSTEM = """You are Omkar, a profound, helpful, and compassionate Vedic Sage. 

RULES:
1. GROUNDED WISDOM: The data provided is precise astrological information. Translate it into clear, helpful life guidance.
2. DESCRIBE TRAITS: Focus on describing the user's query,and tell him natural tendencies, and life patterns according to astrology in simple language.
3. MINIMAL JARGON: You may mention planet names (e.g., Saturn, Jupiter) if helpful, but limit to at most 2 mentions. Do NOT mention zodiac signs or house numbers unless explicitly asked.
4. SACRED TONE: Speak as a helpful and compassionate Sage. Use clear, warm language that feels both wise and practical.
5. LENGTH: 100 words or less.
6. Crucial: End with a curiosity-sparking, thoughtful follow-up question.

PAYLOAD:
- "meta": User identity (contains 'dob' for age calculation) and system type.
- "dasha": Current time cycle (lord, sub-lords, balance).
- "planets": Detailed data for Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn.

FORMAT:
1. "Om Tat Sat, {user_name}."
2. Clear, specific destiny prediction as user asked (No jargon unless requested).
3. ONE curiosity-sparking, thoughtful follow-up question.

Tone: Sacred, Warm, wise, practical, compassionate, helpful.
"""

# Bot 2: OMKAR_LITE - Parashara Token Optimized
OMKAR_LITE_SYSTEM = """You are Omkar, a wise, helpful, and compassionate Vedic Sage. 

RULES:
1. DESCRIBE TRAITS: Focus on describing the user's personality traits, destiny, natural tendencies, and life patterns according to astrology.
2. MINIMAL JARGON: You may mention planet names if helpful (max 2 mentions). Do NOT mention zodiac signs or house numbers unless asked.
3. SACRED VOICE: Speak as a helpful and compassionate Sage in simple but profound language.
4. LENGTH: 100 words or less.
5. Crucial: End with a curiosity-sparking, thoughtful follow-up question.

PAYLOAD LEGEND:
- "meta": Contains Name, DOB, and Current Date. Use DOB for calculations.
- "D:A>B>C/XyYm": Dasha hierarchy (Maha>Antar>Pratyantar) / years and months remaining.
- "Pl:SignDeg°retroHHouse": Planet position (e.g., "Ma:Sag10°RH7" is Mars in Sag at 10°, Retrograde, 7th House).
- "SB:Pl:Score": Shadbala (strength) score.

FORMAT:
Om Tat Sat, {user_name}. [Profound prediction]. [Curiosity-sparking question].

Tone: Sacred, Warm, wise, profound, compassionate.
"""

# Bot 3: JYOTI_PRO - KP Accuracy Optimized  
JYOTI_PRO_SYSTEM = """You are Omkar, a profound, helpful, and compassionate Sage of precision.

RULES:
1. GROUNDED PRECISION: The data is precise astrological information. Translate it into clear, specific life guidance.
2. DESCRIBE TRAITS: Focus on describing the user's personality traits and life patterns with precision.
3. MINIMAL JARGON: You may mention planet names if helpful (max 2 mentions). Do NOT mention zodiac signs or house numbers unless asked.
4. SACRED TONE: Speak as a helpful and compassionate Sage. Use clear, warm language that feels both wise and practical.
5. LENGTH: 100 words or less.
6. Crucial: End with a curiosity-sparking, thoughtful follow-up question.
7. DATA AVAILABILITY: You HAVE the user's Date of Birth (dob) in the 'meta' section. DO NOT ask for it.

PAYLOAD LEGEND:
- "meta": User identity (contains 'dob') and system info.
- "pl": Planet data including sign, star, sub, and strength (str).
- "h": House cusps data including sign, sub, and verdict.
- "sig": Planetary significators for events.

FORMAT:
1. "Om Tat Sat, {user_name}."
2. Clear, specific prediction as user asked (No jargon unless requested).
3. ONE curiosity-sparking, thoughtful follow-up question.

Tone: Sacred, Precise, wise, practical, helpful, compassionate.
"""

# Bot 4: JYOTI_LITE - KP Token Optimized
JYOTI_LITE_SYSTEM = """You are Omkar, a wise, helpful, and compassionate Sage of precision.

RULES:
1. DESCRIBE TRAITS: Focus on describing the user's personality traits, destiny, natural tendencies, and life patterns clearly.
2. MINIMAL JARGON: You may mention planet names if helpful (max 2 mentions). Do NOT mention zodiac signs or house numbers unless asked.
3. Speak as a helpful and compassionate Sage. Be precise with exact timing and life traits.
4. LENGTH: 100 words or less.
5. Crucial: End with a curiosity-sparking, thoughtful follow-up question.
6. DATA AVAILABILITY: You HAVE the user's Date of Birth (dob) in the 'meta' section. DO NOT ask for it.

PAYLOAD LEGEND:
- "meta": Contains Name, DOB, and Current Date.
- "pl": Planet data including sign, star, sub, and significators.
- "h": House data (sign, sub).
- "dasha": Current time periods and balance.

FORMAT:
Om Tat Sat, {user_name}. [Precise profound prediction]. [Curiosity-sparking question].

Tone: Sacred, Warm, wise, profound, helpful, compassionate.
"""


def _build_optimized_json_context(chart_data: Any) -> str:
    """
    Builds the token-optimized JSON payload for AI context.
    
    Returns a compact JSON string with pre-computed significators.
    Zero-Math Protocol: No DOB, no Julian Days. Only human-readable context.
    """
    payload = {}
    
    # Meta information
    if hasattr(chart_data, 'metadata'):
        payload["meta"] = {
            "sys": "KP" if hasattr(chart_data, 'kp_data') and chart_data.kp_data else "Vedic",
            "name": _extract_user_name(chart_data),
            "dob": _extract_dob(chart_data), # Extract YYYY-MM-DD
            "current_date": datetime.now().strftime('%Y-%m-%d')  # FIX: Temporal awareness
        }
    
    # Dasha information (human-readable delta instead of Julian)
    if hasattr(chart_data, 'complete_dasha') and chart_data.complete_dasha:
        cd = chart_data.complete_dasha
        curr = cd.current_state
        
        hierarchy = []
        ends_in = "?"
        
        if curr.maha_dasha:
            hierarchy.append(PLANET_CODES.get(curr.maha_dasha.lord, curr.maha_dasha.lord[:2]))
            # Calculate human-readable delta
            now = datetime.now()
            current_jd = swe.julday(now.year, now.month, now.day, 12.0)  # Dynamic current date
            delta_days = curr.maha_dasha.end_jd - current_jd
            if delta_days > 0:
                years = int(delta_days / 365.25)
                months = int((delta_days % 365.25) / 30.44)
                ends_in = f"{years}y {months}m"
            else:
                ends_in = "ended"
        if curr.antar_dasha:
            hierarchy.append(PLANET_CODES.get(curr.antar_dasha.lord, curr.antar_dasha.lord[:2]))
        if curr.pratyantar_dasha:
            hierarchy.append(PLANET_CODES.get(curr.pratyantar_dasha.lord, curr.pratyantar_dasha.lord[:2]))
        
        payload["dasha"] = {
            "curr": hierarchy,
            "ends_in": ends_in
        }
    
    # Planets with significators
    if hasattr(chart_data, 'kp_data') and chart_data.kp_data:
        payload["pl"] = build_optimized_planet_payload(chart_data)
    
    # House cusps
    if hasattr(chart_data, 'kp_data') and chart_data.kp_data:
        payload["h"] = build_optimized_house_payload(chart_data)
    
    return json.dumps(payload, separators=(',', ':'))

def _extract_user_name(chart_data: Any) -> str:
    """Centralized helper to extract user name from chart data."""
    if hasattr(chart_data, 'metadata'):
        return getattr(chart_data.metadata, 'name', 'User')
    elif isinstance(chart_data, dict):
        # Try both 'metadata' (Pydantic dump) and '_metadata' (Legacy)
        meta = chart_data.get('metadata') or chart_data.get('_metadata', {})
        if isinstance(meta, dict):
            return meta.get('name', 'User')
        # Direct key access fallback
        return chart_data.get('name', 'User')
    return 'User'

def _extract_dob(chart_data: Any) -> str:
    """Centralized helper to extract DOB from chart data."""
    dob = "Unknown"
    
    # helper to clean date
    def clean_date(d):
        return str(d).split(' ')[0] if d else "Unknown"

    if hasattr(chart_data, 'metadata'):
        dob = getattr(chart_data.metadata, 'datetime', 'Unknown')
    elif isinstance(chart_data, dict):
        meta = chart_data.get('metadata') or chart_data.get('_metadata', {})
        if isinstance(meta, dict):
            dob = meta.get('datetime', 'Unknown')
        else:
             # direct access fallback
            dob = chart_data.get('dob', 'Unknown')
            
    return clean_date(dob)

def _build_user_prompt(user_name: str, planets_str: str, full_context_str: str, user_query: str, is_first_message: bool) -> str:
    """Standardized prompt builder to fix prompt drift."""
    # Add name ONLY in first message for token efficiency
    identity_prefix = f"User: {user_name}\n" if is_first_message and user_name != 'User' else ""
    return f"{identity_prefix}Planetary Positions: {planets_str}{full_context_str}\n\nQuestion: {user_query}"

def _build_optimized_user_prompt(json_context: str, user_query: str) -> str:
    """Builds user prompt for optimized JSON mode."""
    return f"CHART_DATA: {json_context}\n\nQuestion: {user_query}"

# Helper functions for 4-bot system
def detect_question_type(query: str) -> str:
    """Detect the type of question to provide focus routing."""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['marriage', 'marry', 'spouse', 'wife', 'husband', 'partner', 'wedding']):
        return 'marriage'
    elif any(word in query_lower for word in ['career', 'job', 'work', 'profession', 'business', 'employment']):
        return 'career'
    elif any(word in query_lower for word in ['money', 'wealth', 'rich', 'income', 'finance', 'millionaire', 'property']):
        return 'wealth'
    elif any(word in query_lower for word in ['health', 'disease', 'illness', 'body', 'medical']):
        return 'health'
    else:
        return 'general'

def get_focus_houses(question_type: str) -> list:
    """Get relevant house numbers based on question type (KP standard)."""
    focus_map = {
        'career': [2, 6, 10, 11],
        'marriage': [2, 7, 11],
        'wealth': [2, 6, 11],
        'health': [1, 5, 11],  # Recovery houses
        'general': []
    }
    return focus_map.get(question_type, [])

def get_strength_verdict(shadbala: float) -> str:
    """Convert Shadbala score to human-readable verdict."""
    if shadbala >= 450:
        return "Strong"
    elif shadbala >= 350:
        return "Moderate"
    else:
        return "Weak"


def normalize_shadbala_ratio(shadbala: float) -> float:
    """
    Normalize Shadbala score to a ratio where 1.0 is average.
    Average Shadbala is ~350, so we divide by 350.
    Returns a float like 1.32 (strong) or 0.93 (weak).
    """
    AVERAGE_SHADBALA = 350.0
    if shadbala == 0:
        return 0.0
    return round(shadbala / AVERAGE_SHADBALA, 2)


def expand_relationship(rel_abbrev: str) -> str:
    """
    Expand relationship abbreviation to full word to prevent AI hallucination.
    Examples: 'Gre' -> 'GreatFriend', 'Fri' -> 'Friend', 'Ene' -> 'Enemy'
    """
    relationship_map = {
        'Gre': 'GreatFriend',
        'Fri': 'Friend',
        'Neu': 'Neutral',
        'Ene': 'Enemy',
        'Bit': 'BitterEnemy'
    }
    return relationship_map.get(rel_abbrev, rel_abbrev)


def parse_house_rules(rules_str: str) -> list:
    """
    Parse house rules string to integer array.
    Examples: '2nd, 11th' -> [2, 11], '5th' -> [5], '' -> []
    """
    if not rules_str or rules_str == '-':
        return []
    
    # Remove 'st', 'nd', 'rd', 'th' suffixes and split by comma
    import re
    cleaned = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', rules_str)
    parts = [p.strip() for p in cleaned.split(',')]
    
    result = []
    for part in parts:
        try:
            result.append(int(part))
        except ValueError:
            continue
    
    return result


def _calculate_dasha_balance(complete_dasha) -> str:
    """Calculate dasha balance in years/months from end_jd."""
    try:
        if not complete_dasha or not complete_dasha.current_state or not complete_dasha.current_state.maha_dasha:
            return "N/A"
        
        maha = complete_dasha.current_state.maha_dasha
        if not hasattr(maha, 'end_jd') or maha.end_jd is None:
            return "N/A"
        
        import swisseph as swe
        from datetime import datetime
        now = datetime.now()
        current_jd = swe.julday(now.year, now.month, now.day, 12.0)
        
        delta_days = float(maha.end_jd) - float(current_jd)
        
        if delta_days > 0:
            years = int(delta_days / 365.25)
            months = int((delta_days % 365.25) / 30.44)
            return f"{years}y {months}m"
        else:
            return "ended"
    except Exception:
        return "N/A"
    except Exception:
        return "N/A"


# Payload builders for 4-bot system
def _build_kp_lite_payload(chart_data: Any) -> str:
    """Build compact KP payload for JYOTI_LITE (token-optimized)."""
    return _build_optimized_json_context(chart_data)


def _build_kp_pro_payload(chart_data: Any, user_query: str = "") -> str:
    """Build enriched KP payload for JYOTI_PRO (accuracy-optimized)."""
    from datetime import datetime
    from backend.kp_significators import build_optimized_planet_payload, build_optimized_house_payload
    
    question_type = detect_question_type(user_query)
    focus_houses = get_focus_houses(question_type)
    
    # Build enriched payload
    pl_payload = build_optimized_planet_payload(chart_data)
    h_payload = build_optimized_house_payload(chart_data)
    
    # Add verdicts and extra data for planets
    for code, data in pl_payload.items():
        # Find original planet name from code
        p_name = next((name for name, c in PLANET_CODES.items() if c == code), None)
        planet_obj = None
        if p_name:
            planet_obj = chart_data.planets.get(p_name.lower()) or chart_data.planets.get(p_name)
            
        if len(data) >= 4 and data[3] is not None:  # Has Shadbala
            pl_payload[code] = {
                "sign": data[0],
                "star": data[1],
                "sub": data[2],
                "str": normalize_shadbala_ratio(data[3]),
                "sig": data[4],
                "rel": expand_relationship(getattr(planet_obj, 'relationship', '')[:3]) if planet_obj else "",
                "rules": parse_house_rules(getattr(planet_obj, 'rules_houses', '')) if planet_obj else [],
                "retro": "R" if getattr(planet_obj, 'is_retrograde', False) else ""
            }
    
    # Format houses
    for num, data in h_payload.items():
        h_payload[num] = {
            "sign": data[0],
            "sub": data[1]
        }
    
    meta = {
        "sys": "KP", 
        "name": _extract_user_name(chart_data),
        "dob": _extract_dob(chart_data),
        "current_date": datetime.now().strftime('%Y-%m-%d')  # FIX: Temporal awareness
    }
    dasha_info = {
        "lord": chart_data.complete_dasha.current_state.maha_dasha.lord if (hasattr(chart_data, 'complete_dasha') and chart_data.complete_dasha and chart_data.complete_dasha.current_state.maha_dasha) else "Unknown",
        "curr": [chart_data.complete_dasha.current_state.maha_dasha.lord[:2] if (hasattr(chart_data, 'complete_dasha') and chart_data.complete_dasha and chart_data.complete_dasha.current_state.maha_dasha) else "?",
                 chart_data.complete_dasha.current_state.antar_dasha.lord[:2] if (hasattr(chart_data, 'complete_dasha') and chart_data.complete_dasha and chart_data.complete_dasha.current_state.antar_dasha) else "?",
                 chart_data.complete_dasha.current_state.pratyantar_dasha.lord[:2] if (hasattr(chart_data, 'complete_dasha') and chart_data.complete_dasha and chart_data.complete_dasha.current_state.pratyantar_dasha) else "?"],
        "ends": _calculate_dasha_balance(chart_data.complete_dasha) if (hasattr(chart_data, 'complete_dasha') and chart_data.complete_dasha and chart_data.complete_dasha.current_state.maha_dasha) else "N/A"
    }
    
    payload = {"meta": meta, "dasha": dasha_info, "pl": pl_payload, "h": h_payload}
    
    # Add focus routing if specific question
    if question_type != 'general':
        payload["focus"] = {"topic": question_type, "houses": focus_houses}
    
    return json.dumps(payload, separators=(',', ':'))


def _build_parashara_lite_payload(chart_data: Any) -> str:
    """Build compact Parashara payload for OMKAR_LITE (token-optimized)."""
    dasha_str = ""
    if hasattr(chart_data, 'complete_dasha') and chart_data.complete_dasha:
        cd = chart_data.complete_dasha
        curr = cd.current_state
        maha_lord = curr.maha_dasha.lord if curr.maha_dasha else "?"
        antar_lord = curr.antar_dasha.lord if curr.antar_dasha else "?"
        pratyantar_lord = curr.pratyantar_dasha.lord if curr.pratyantar_dasha else "?"
        
        # Calculate balance from end_jd
        years, months = 0, 0
        if curr.maha_dasha and hasattr(curr.maha_dasha, 'end_jd'):
            import swisseph as swe
            current_jd = swe.julday(2026, 1, 10, 12.0)
            delta_days = curr.maha_dasha.end_jd - current_jd
            if delta_days > 0:
                years = int(delta_days / 365.25)
                months = int((delta_days % 365.25) / 30.44)
        
        dasha_str = f"D:{maha_lord[:2]}>{antar_lord[:2]}>{pratyantar_lord[:2]}/{years}y{months}m"
    
    # Compact planet positions
    planets_compact = []
    if hasattr(chart_data, 'planets'):
        relevant_planets = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu', 'ascendant']
        for name, data in chart_data.planets.items():
            if name.lower() in relevant_planets:
                deg = int(data.degree) if hasattr(data, 'degree') else int(getattr(data, 'longitude', 0) % 30)
                retro = "R" if getattr(data, 'is_retrograde', False) else ""
                house = getattr(data, 'house', '?')
                planets_compact.append(f"{name[:2]}:{data.sign[:3]}{deg}°{retro}H{house}")
    
    # Shadbala scores (top 4 only) - normalize case for lookup
    shadbala_str = ""
    if hasattr(chart_data, 'shadbala') and chart_data.shadbala and chart_data.shadbala.total_shadbala:
        # Normalize keys to lowercase for consistent lookup
        normalized_shadbala = {k.lower(): v for k, v in chart_data.shadbala.total_shadbala.items()}
        top_planets = sorted(normalized_shadbala.items(), 
                            key=lambda x: x[1], 
                            reverse=True)[:4]
        shadbala_parts = [f"{name[:2]}:{int(score)}" for name, score in top_planets]
        shadbala_str = f" SB:{','.join(shadbala_parts)}"
    
    # FIX: Add Metadata for Temporal Awareness
    name = _extract_user_name(chart_data)
    dob = _extract_dob(chart_data)
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    meta_str = f"Name:{name} DOB:{dob} Now:{current_date}"
    
    return f"{meta_str} {dasha_str} {' '.join(planets_compact)}{shadbala_str}"


def _build_parashara_pro_payload(chart_data: Any, user_query: str = "") -> str:
    """Build enriched Parashara payload for OMKAR_PRO (accuracy-optimized)."""
    from datetime import datetime
    question_type = detect_question_type(user_query)
    
    # Meta
    meta = {
        "name": _extract_user_name(chart_data),
        "dob": _extract_dob(chart_data),
        "current_date": datetime.now().strftime('%Y-%m-%d')  # FIX: Temporal awareness
    }
    
    # Dasha
    dasha_info = {}
    if hasattr(chart_data, 'complete_dasha') and chart_data.complete_dasha:
        cd = chart_data.complete_dasha
        dasha_info = {
            "lord": cd.current_state.maha_dasha.lord if cd.current_state.maha_dasha else "Unknown",
            "sub": [
                cd.current_state.antar_dasha.lord if cd.current_state.antar_dasha else "Unknown",
                cd.current_state.pratyantar_dasha.lord if cd.current_state.pratyantar_dasha else "Unknown"
            ],
            "ends": _calculate_dasha_balance(cd) if cd.current_state.maha_dasha else "N/A"
        }
    
    # Planets with verdicts
    planets_data = {}
    if hasattr(chart_data, 'planets'):
        relevant_planets = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu', 'ascendant']
        
        # Normalize shadbala dict for consistent lookup
        normalized_shadbala = {}
        if hasattr(chart_data, 'shadbala') and chart_data.shadbala and chart_data.shadbala.total_shadbala:
            normalized_shadbala = {k.lower(): v for k, v in chart_data.shadbala.total_shadbala.items()}
        
        for name, data in chart_data.planets.items():
            if name.lower() in relevant_planets:
                nakshatra = getattr(data, 'nakshatra', {})
                nak_short = getattr(nakshatra, 'nakshatra', 'N/A')[:7] if hasattr(nakshatra, 'nakshatra') else 'N/A'
                
                # Get Shadbala with normalized lookup
                shadbala = int(normalized_shadbala.get(name.lower(), 0))
                
                # Get karaka from planet data
                karaka = getattr(data, 'karaka', '')
                if not karaka or karaka == '-':
                    karaka = ""
                
                # Get relationship and houses_ruled
                relationship = getattr(data, 'relationship', '')
                houses_ruled = getattr(data, 'rules_houses', '')
                
                planets_data[name] = {
                    "sign": data.sign,
                    "house": getattr(data, 'house', '?'),
                    "nak": nak_short,
                    "karaka": karaka,
                    "str": normalize_shadbala_ratio(shadbala),
                    "rel": expand_relationship(relationship[:3]) if relationship else "",
                    "rules": parse_house_rules(houses_ruled) if houses_ruled else [],
                    "retro": "R" if getattr(data, 'is_retrograde', False) else ""
                }
    
    payload = {"meta": meta, "dasha": dasha_info, "planets": planets_data}
    
    # Add focus if specific question
    if question_type != 'general':
        payload["focus"] = question_type
    
    return json.dumps(payload, separators=(',', ':'))


# Bot router
def get_bot_config(is_kp_mode: bool, bot_mode: str = "pro"):
    """
    Get the appropriate bot configuration (system prompt + payload builder).
    
    Args:
        is_kp_mode: True for KP (JYOTI), False for Parashara (OMKAR)
        bot_mode: "pro" for accuracy, "lite" for tokens, "legacy" for old behavior
    
    Returns:
        Tuple of (system_prompt,  payload_builder_function)
    """
    if bot_mode == "legacy":
        # Return None to signal legacy mode (caller will handle)
        return None, None
    
    if is_kp_mode:
        if bot_mode == "lite":
            return JYOTI_LITE_SYSTEM, _build_kp_lite_payload
        else:  # pro
            return JYOTI_PRO_SYSTEM, _build_kp_pro_payload
    else:
        if bot_mode == "lite":
            return OMKAR_LITE_SYSTEM, _build_parashara_lite_payload
        else:  # pro
            return OMKAR_PRO_SYSTEM, _build_parashara_pro_payload



@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def get_astrology_prediction_stream(chart_data, user_query, api_key, history=None, is_kp_mode=False, system_instruction=None, bot_mode="pro", model=None):
    """
    Streams astrological prediction using OpenAI GPT-5 nano.
    Grounding logic is handled by the system instruction.
    """
    if not api_key:
        yield "⚠️ Error: API Key missing."
        return

    sys_instr = system_instruction or OMKAR_SYSTEM_INSTRUCTION
    
    # Ensure chart_data is an object to prevent AttributeErrors
    chart_data = _ensure_chart_object(chart_data)
    
    # Extract name early for dynamic prompting
    user_name = _extract_user_name(chart_data)

    try:
        # Use bot router if not legacy mode
        if system_instruction is None and bot_mode != "legacy":
            sys_prompt, payload_builder = get_bot_config(is_kp_mode, bot_mode)
            
            if sys_prompt and payload_builder:
                # Build payload using bot-specific builder  
                try:
                    payload = payload_builder(chart_data, user_query) if bot_mode == "pro" else payload_builder(chart_data)
                except TypeError:
                    # Lite builders don't take user_query
                    payload = payload_builder(chart_data)
               
                # Format system prompt with user name
                sys_instr = sys_prompt.format(user_name=user_name) if "{user_name}" in sys_prompt else sys_prompt
                
                messages = [_format_openai_message("system", sys_instr)]
                
                # Add history
                if history:
                    for msg in history[-10:]:
                        if msg.get("role") == "user" and msg.get("content") == user_query:
                            continue
                        messages.append(_format_openai_message(msg["role"], msg["content"]))
                
                # Add user query with payload
                if is_kp_mode:
                    user_prompt = _build_optimized_user_prompt(payload, user_query)
                else:
                    user_prompt = f"CHART_DATA: {payload}\n\nQuestion: {user_query}"
                
                messages.append(_format_openai_message("user", user_prompt))
                
                logger.debug(f"📤 {bot_mode.upper()} MODE: {len(payload)} chars payload")
                
                # Skip to streaming section
                skip_legacy = True
            else:
                skip_legacy = False
        else:
            skip_legacy = False
        
        # Legacy mode (original behavior)
        if not skip_legacy:
            sys_instr = system_instruction or (OMKAR_SYSTEM_INSTRUCTION_V2 if is_kp_mode else OMKAR_SYSTEM_INSTRUCTION)
            
            # === OPTIMIZED JSON MODE (KP) ===
            if is_kp_mode and hasattr(chart_data, 'kp_data') and chart_data.kp_data:
                # Dynamic system prompt with user name
                sys_instr = sys_instr.format(user_name=user_name) if "{user_name}" in sys_instr else sys_instr
                json_context = _build_optimized_json_context(chart_data)
            
            messages = [_format_openai_message("system", sys_instr)]
            
            # Add history
            if history:
                for msg in history[-10:]:
                    if msg.get("role") == "user" and msg.get("content") == user_query:
                        continue
                    messages.append(_format_openai_message(msg["role"], msg["content"]))
            
            # Optimized prompt
            current_prompt = _build_optimized_user_prompt(json_context, user_query)
            messages.append(_format_openai_message("user", current_prompt))
            
            logger.debug(f"📤 OPTIMIZED MODE: {len(json_context)} chars JSON payload")
        
        # === PARASHARA MODE (Classic Vedic) ===
        else:
            # Prepare planetary data
            chart_dict = _get_serializable_chart_data(chart_data)
            planets_str = format_planetary_data(chart_dict)
            
            # Add Enhanced Dasha Data
            dasha_str = ""
            if hasattr(chart_data, 'complete_dasha') and chart_data.complete_dasha:
                cd = chart_data.complete_dasha
                curr = cd.current_state
                
                hierarchy = []
                if curr.maha_dasha: hierarchy.append(f"Maha: {curr.maha_dasha.lord} (End: {jd_to_date(curr.maha_dasha.end_jd)})")
                if curr.antar_dasha: hierarchy.append(f"Antar: {curr.antar_dasha.lord}")
                if curr.pratyantar_dasha: hierarchy.append(f"Prat: {curr.pratyantar_dasha.lord}")
                
                dasha_str = f"\n\nDASHA (Current): {' > '.join(hierarchy)}"
                
            # Add Shadbala Data
            shadbala_str = ""
            if hasattr(chart_data, 'shadbala') and chart_data.shadbala:
                sb = chart_data.shadbala.total_shadbala
                sb_list = [f"{k}: {v:.1f}" for k, v in sb.items()]
                shadbala_str = f"\n\nSHADBALA: {', '.join(sb_list)}"

            # Add Metadata (DOB)
            meta_str = ""
            dob_val = _extract_dob(chart_data)
            if dob_val != "Unknown":
                meta_str = f"\n\nMETADATA: DOB: {dob_val}"
            
            full_context_str = f"{meta_str}{dasha_str}{shadbala_str}"
            
            # Dynamic system prompt with user name for Legacy Mode
            formatted_instr = sys_instr.format(user_name=user_name) if "{user_name}" in sys_instr else sys_instr
            messages = [_format_openai_message("system", formatted_instr)]
            
            is_first_message = not history or len(history) == 0
            if history:
                for msg in history[-10:]:
                    if msg.get("role") == "user" and msg.get("content") == user_query:
                        continue
                    messages.append(_format_openai_message(msg["role"], msg["content"]))
            
            current_prompt = _build_user_prompt(user_name, planets_str, full_context_str, user_query, is_first_message)
            messages.append(_format_openai_message("user", current_prompt))

        # Security: Log at DEBUG, not INFO
        logger.debug(f"📤 API INPUT: {len(messages)} messages | History items: {len(history) if history else 0}")

        client = get_openai_client(api_key)
        
        # Set reasoning effort based on model
        # gpt-5-nano: low reasoning, gpt-5-mini: minimal reasoning
        reasoning_effort = "low" if model == "gpt-5-nano" or not model else "minimal"
        
        stream = await asyncio.to_thread(
            client.responses.create,
            model=model or OPENAI_MODEL,
            input=messages,
            stream=True,
            reasoning={"effort": reasoning_effort}
        )
        
        for event in stream:
            chunk = ""
            
            # Robust parsing for 2026 SDK
            if hasattr(event, 'type') and "delta" in event.type:
                resp = getattr(event, 'response', None)
                if resp:
                    chunk = getattr(resp, 'text', "") if hasattr(resp, 'text') else resp.get('text', "")
            elif isinstance(event, dict) and "delta" in event.get('type', ''):
                chunk = event.get('response', {}).get('text', "")
            
            # Fallbacks
            if not chunk:
                if hasattr(event, 'output_text'): chunk = event.output_text
                elif hasattr(event, 'delta'): chunk = event.delta
                elif isinstance(event, dict): 
                    chunk = event.get('output_text', "") or event.get('delta', "")

            if chunk:
                yield chunk
            
            # Capture usage from final event
            if hasattr(event, 'usage'):
                u = event.usage
                
                # Extract token details (OpenAI Responses API format)
                input_tokens = getattr(u, 'input_tokens', 0)
                output_tokens = getattr(u, 'output_tokens', 0)
                total_tokens = getattr(u, 'total_tokens', 0)
                
                # Cache breakdown
                input_details = getattr(u, 'input_tokens_details', None)
                cached_input = getattr(input_details, 'cached_tokens', 0) if input_details else 0
                non_cached_input = input_tokens - cached_input
                
                # Reasoning tokens
                output_details = getattr(u, 'output_tokens_details', None)
                reasoning = getattr(output_details, 'reasoning_tokens', 0) if output_details else 0
                
                logger.info(
                    f"📊 STREAM TOKEN USAGE: Total={total_tokens} | "
                    f"Input: {input_tokens} (cached: {cached_input}, non-cached: {non_cached_input}) | "
                    f"Output: {output_tokens} | Thinking: {reasoning}"
                )
                
            await asyncio.sleep(0.01)

    except Exception as e:
        logger.exception(f"Exception during AI streaming: {str(e)}")
        yield f"⚠️ Error: {str(e)}"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def get_astrology_prediction(chart_data, user_query, api_key, history=None, is_kp_mode=False, system_instruction=None, bot_mode="pro", return_debug_info=False):
    """
    Sends essential chart data and query to OpenAI GPT-5 nano with history support.
    Grounding logic is handled by the system instruction.
    """
    if not api_key:
        logger.error("API Key not provided to get_astrology_prediction")
        return "⚠️ Error: API Key missing. Please check configuration."
    
    sys_instr = system_instruction or OMKAR_SYSTEM_INSTRUCTION
    
    # Extract name early for dynamic prompting
    user_name = _extract_user_name(chart_data)
    
    try:
        # Generate response
        if isinstance(chart_data, dict) and "error" in chart_data:
            return f"Could not generate prediction due to chart error: {chart_data['error']}"

        # Use bot router if not legacy mode
        if system_instruction is None and bot_mode != "legacy":
            sys_prompt, payload_builder = get_bot_config(is_kp_mode, bot_mode)
            
            if sys_prompt and payload_builder:
                # Build payload using bot-specific builder  
                try:
                    payload = payload_builder(chart_data, user_query) if bot_mode == "pro" else payload_builder(chart_data)
                except TypeError:
                    # Lite builders don't take user_query
                    payload = payload_builder(chart_data)
               
                # Format system prompt with user name
                sys_instr = sys_prompt.format(user_name=user_name) if "{user_name}" in sys_prompt else sys_prompt
                
                messages = [_format_openai_message("system", sys_instr)]
                
                # Add history
                if history:
                    for msg in history[-10:]:
                        if msg.get("role") == "user" and msg.get("content") == user_query:
                            continue
                        messages.append(_format_openai_message(msg["role"], msg["content"]))
                
                # Add user query with payload
                if is_kp_mode:
                    user_prompt = _build_optimized_user_prompt(payload, user_query)
                else:
                    user_prompt = f"CHART_DATA: {payload}\n\nQuestion: {user_query}"
                
                messages.append(_format_openai_message("user", user_prompt))
                
                # Debug info capture
                debug_payload = user_prompt
                
                logger.info(f"📤 {bot_mode.upper()} PAYLOAD (first 400 chars): {user_prompt[:400]}...")
        
        # === LEGACY/FALLBACK MODE ===
        else:
            # === OPTIMIZED JSON MODE (KP) ===
            if is_kp_mode and hasattr(chart_data, 'kp_data') and chart_data.kp_data:
                # Dynamic system prompt with user name
                sys_instr = OMKAR_SYSTEM_INSTRUCTION_V2.format(user_name=user_name)
                json_context = _build_optimized_json_context(chart_data)
                
                messages = [_format_openai_message("system", sys_instr)]
                
                if history:
                    for msg in history[-10:]:
                        if msg.get("role") == "user" and msg.get("content") == user_query:
                            continue
                        messages.append(_format_openai_message(msg["role"], msg["content"]))
                
                current_prompt = _build_optimized_user_prompt(json_context, user_query)
                messages.append(_format_openai_message("user", current_prompt))
            
            # === PARASHARA MODE (Classic Vedic) ===
            else:
                chart_dict = _get_serializable_chart_data(chart_data)
                planets_str = format_planetary_data(chart_dict)
                
                # Add Dasha Data
                dasha_str = ""
                if hasattr(chart_data, 'complete_dasha') and chart_data.complete_dasha:
                    cd = chart_data.complete_dasha
                    curr = cd.current_state
                    
                    hierarchy = []
                    if curr.maha_dasha: hierarchy.append(f"Maha: {curr.maha_dasha.lord} (End: {jd_to_date(curr.maha_dasha.end_jd)})")
                    if curr.antar_dasha: hierarchy.append(f"Antar: {curr.antar_dasha.lord}")
                    if curr.pratyantar_dasha: hierarchy.append(f"Prat: {curr.pratyantar_dasha.lord}")
                    
                    dasha_str = f"\n\nDASHA (Current): {' > '.join(hierarchy)}"

                # Add Shadbala Data
                shadbala_str = ""
                if hasattr(chart_data, 'shadbala') and chart_data.shadbala:
                    sb = chart_data.shadbala.total_shadbala
                    sb_list = [f"{k}: {v:.1f}" for k, v in sb.items()]
                    shadbala_str = f"\n\nSHADBALA: {', '.join(sb_list)}"

                full_context_str = f"{dasha_str}{shadbala_str}"
                
                # Dynamic system prompt with user name for Parashara Mode
                formatted_instr = sys_instr.format(user_name=user_name) if "{user_name}" in sys_instr else sys_instr
                messages = [_format_openai_message("system", formatted_instr)]
                
                is_first_message = not history or len(history) == 0
                if history:
                    for msg in history[-10:]:
                        if msg.get("role") == "user" and msg.get("content") == user_query:
                            continue
                        messages.append(_format_openai_message(msg["role"], msg["content"]))
                
                current_prompt = _build_user_prompt(user_name, planets_str, full_context_str, user_query, is_first_message)
                messages.append(_format_openai_message("user", current_prompt))

        client = get_openai_client(api_key)
        
        response = await asyncio.to_thread(
            client.responses.create,
            model=OPENAI_MODEL,
            input=messages,
            reasoning={"effort": "medium"}
        )
        
        if response and hasattr(response, 'output_text'):
            if hasattr(response, 'usage'):
                u = response.usage
                
                # Extract token details
                input_tokens = getattr(u, 'input_tokens', 0)
                output_tokens = getattr(u, 'output_tokens', 0)
                total_tokens = getattr(u, 'total_tokens', 0)
                
                # Cache breakdown
                input_details = getattr(u, 'input_tokens_details', None)
                cached_input = getattr(input_details, 'cached_tokens', 0) if input_details else 0
                non_cached_input = input_tokens - cached_input
                
                # Reasoning tokens
                output_details = getattr(u, 'output_tokens_details', None)
                reasoning_count = getattr(output_details, 'reasoning_tokens', 0) if output_details else 0
                
                logger.info(
                    f"📊 TOKEN USAGE: Total={total_tokens} | "
                    f"Input: {input_tokens} (cached: {cached_input}, non-cached: {non_cached_input}) | "
                    f"Output: {output_tokens} | Thinking: {reasoning_count}"
                )
                logger.info(f"DEBUG: Response attributes: {dir(response)}")
                
                # Deep inspection of output object
                if hasattr(response, 'output'):
                    logger.info(f"DEBUG: Output object: {response.output}")
                    logger.info(f"DEBUG: Output type: {type(response.output)}")
                    if response.output:
                        logger.info(f"DEBUG: Output dir: {dir(response.output)}")
                        # Try to get text or content from output
                        for attr in ['text', 'content', 'reasoning', 'thinking']:
                            if hasattr(response.output, attr):
                                val = getattr(response.output, attr)
                                logger.info(f"DEBUG: output.{attr} = {val}")

                # Extract reasoning summary from output list
                if hasattr(response, 'output') and isinstance(response.output, list):
                    for item in response.output:
                        if hasattr(item, 'type') and item.type == 'reasoning':
                            logger.info(f"🧠 REASONING ITEM FOUND: {item}")
                            # Check for summary field
                            if hasattr(item, 'summary') and item.summary:
                                logger.info(f"🧠 AI INTERNAL DIALOGUE (THINKING SUMMARY):\n{item.summary}")
                            break

            content = response.output_text.strip()
            
            if return_debug_info:
                return {
                    "prediction": content,
                    "payload": debug_payload if 'debug_payload' in locals() else str(messages),
                    "usage": {
                        "input_tokens": input_tokens if 'input_tokens' in locals() else 0,
                        "output_tokens": output_tokens if 'output_tokens' in locals() else 0,
                        "total_tokens": total_tokens if 'total_tokens' in locals() else 0
                    }
                }
            
            return content
        return "⚠️ Error: Empty response from AI"
            
    except Exception as e:
        logger.exception(f"Exception during AI prediction: {str(e)}")
        raise e  # Tenacity needs this to retry


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def get_followup_questions(api_key: str, chart_data: Any = None, is_kp_mode: bool = False, history: List[Dict[str, str]] = None):
    """
    Generates 3 follow-up questions based on the chart data and conversation context.
    """
    if not api_key:
        return ["What does this mean?", "Any remedies?", "Future outlook?"]
        
    try:
        # standardizing chart data
        chart_data = _ensure_chart_object(chart_data)

        # Standardized user name extraction
        user_name = _extract_user_name(chart_data)

        system_instruction = (
            f"You are the legendary Astrologer 'Omkar' talking to {user_name}. "
            "Generate 3 VERY SHORT 'Destiny Hook' questions for the user in FIRST PERSON (use 'I', 'my', 'me'). "
            "These should feel like triggers or invitations to uncover secrets. "
            "CRITICAL: Each question MUST be under 7 words. No preamble. "
            "Format: Question 1 || Question 2 || Question 3"
        )
        
        context_str = ""
        if history:
            last_msgs = [m["content"] for m in history[-3:] if isinstance(m["content"], str)]
            context_str = f"Context of conversation: {' | '.join(last_msgs)}\n\n"

        planets_context = ""
        if chart_data:
            chart_dict = _get_serializable_chart_data(chart_data)
            planets_context = f"Birth Chart Data: {format_planetary_data(chart_dict)}\n\n"

        user_prompt = (
            f"{planets_context}"
            f"{context_str}"
            "Generate exactly 3 SHORT follow-up questions (MAX 7 WORDS EACH) separated by ||."
        )
        
        # Fix: Use proper system/user message separation
        messages = [
            _format_openai_message("system", system_instruction),
            _format_openai_message("user", user_prompt)
        ]

        client = get_openai_client(api_key)
        
        # Disable reasoning for suggestions to save tokens
        response = await asyncio.to_thread(
            client.responses.create,
            model=OPENAI_MODEL,
            input=messages
        )
        
        raw_text = response.output_text.strip() if response and hasattr(response, 'output_text') else ""
        logger.info(f"AI Suggestions: {raw_text}")
        
        if raw_text:
            parts = raw_text.split("||")
            suggestions = [p.strip().replace("**", "").replace("*", "") for p in parts if p.strip()]
            suggestions = [(s if s.endswith('?') else s + '?') for s in suggestions]
            
            while len(suggestions) < 3:
                suggestions.append("What else should I know?")
            return suggestions[:3]
            
        return ["What does this mean?", "Any remedies?", "Future outlook?"]

    except Exception as e:
        logger.exception(f"Exception during suggestions generation: {str(e)}")
        raise e
