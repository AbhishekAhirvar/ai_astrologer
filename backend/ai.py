import os
import asyncio
from openai import OpenAI
from backend.logger import logger
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
from functools import lru_cache

load_dotenv()

# Configure OpenAI
OPENAI_MODEL = "gpt-5.2"

# Log model info on startup
logger.info(f"🤖 AI Module initialized with OpenAI model: {OPENAI_MODEL}")

@lru_cache(maxsize=100)
def get_planet_basic_meaning(planet, sign):
    """
    Example of a cached lookup for basic meanings.
    (This can be expanded with more astrological rules)
    """
    return f"{planet} in {sign}."

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def get_astrology_prediction_stream(chart_data, user_query, api_key, history=None, is_kp_mode=False):
    """
    Streams astrological prediction using OpenAI GPT-5.2.
    """
    if not api_key:
        yield "⚠️ Error: API Key missing."
        return

    try:
        # Prepare planetary data
        planets = ['sun', 'moon', 'ascendant', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']
        essential_data = []
        def get_p_data(source, key):
            if isinstance(source, dict): return source.get(key, {})
            if hasattr(source, 'planets'): return getattr(source.planets, 'get', lambda k,d: d)(key, {})
            return {}

        for p in planets:
            p_data = get_p_data(chart_data, p)
            if p_data:
                sign = p_data.get('sign', '?') if isinstance(p_data, dict) else getattr(p_data, 'sign', '?')
                deg = p_data.get('degree', 0) if isinstance(p_data, dict) else getattr(p_data, 'degree', 0)
                house = p_data.get('house', '?') if isinstance(p_data, dict) else getattr(p_data, 'house', '?')
                rules = p_data.get('rules_houses', '-') if isinstance(p_data, dict) else getattr(p_data, 'rules_houses', '-')
                essential_data.append(f"{p.capitalize()}: {sign} {deg}° (House: {house}, Rules: {rules})")
        
        planets_str = ", ".join(essential_data)
        system_instruction = (
            f"You are an expert {'KP' if is_kp_mode else 'Vedic'} Astrologer. "
            "Give an accurate prediction (approx 50 words) based on the planetary data. "
            "Maintain conversation continuity."
        )

        def format_msg(role, content):
            # 2026 Responses API: type tells content type, but field is always 'text'
            
            # If content is already a list (from history), extract the actual text
            if isinstance(content, list):
                # Extract text from content blocks like [{"text": "...", "type": "text"}]
                if len(content) > 0 and isinstance(content[0], dict) and 'text' in content[0]:
                    content = content[0]['text']
                else:
                    # Fallback: use as-is
                    return {"role": role, "content": content}
            
            # Now format with correct type
            content_type = "input_text" if role in ["user", "system"] else "output_text"
            return {"role": role, "content": [{"type": content_type, "text": content}]}

        messages = [format_msg("system", system_instruction)]
        
        # Add history - Gradio stores plain text in content
        if history:
            for msg in history[-10:]:
                # Skip if this is the current query (avoid duplication)
                if msg.get("role") == "user" and msg.get("content") == user_query:
                    continue
                messages.append(format_msg(msg["role"], msg["content"]))
        
        current_prompt = f"Planetary Positions: {planets_str}\n\nUser Question: {user_query}"
        messages.append(format_msg("user", current_prompt))

        logger.info(f"📤 API INPUT: {len(messages)} messages | History items: {len(history) if history else 0}")

        client = OpenAI(api_key=api_key)
        
        # Use OpenAI Responses API (2026)
        stream = client.responses.create(
            model=OPENAI_MODEL,
            input=messages,
            stream=True,
            reasoning={"effort": "low"}
        )
        
        for event in stream:
            logger.debug(f"AI Stream Event: {event}")
            chunk = ""
            
            # Robust parsing for 2026 SDK
            if hasattr(event, 'type'):
                if "delta" in event.type:
                    resp = getattr(event, 'response', None)
                    if resp:
                        chunk = getattr(resp, 'text', "") if hasattr(resp, 'text') else resp.get('text', "")
            elif isinstance(event, dict):
                if "delta" in event.get('type', ''):
                    chunk = event.get('response', {}).get('text', "")
            
            # Fallbacks
            if not chunk:
                if hasattr(event, 'output_text'): chunk = event.output_text
                elif hasattr(event, 'delta'): chunk = event.delta
                elif isinstance(event, dict): 
                    chunk = event.get('output_text', "") or event.get('delta', "")

            if chunk:
                logger.debug(f"AI Stream Chunk: {chunk}")
                yield chunk
            await asyncio.sleep(0.01)

    except Exception as e:
        logger.exception(f"Exception during AI streaming: {str(e)}")
        yield f"⚠️ Error: {str(e)}"

    except Exception as e:
        logger.exception(f"Exception during AI streaming: {str(e)}")
        yield f"⚠️ Error: {str(e)}"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def get_astrology_prediction(chart_data, user_query, api_key, history=None, is_kp_mode=False):
    """
    Sends essential chart data and query to OpenAI GPT-5.2 with history support.
    """
    if not api_key:
        logger.error("API Key not provided to get_astrology_prediction")
        return "⚠️ Error: API Key missing. Please check configuration."
    
    try:
        if isinstance(chart_data, dict) and "error" in chart_data:
            return f"Could not generate prediction due to chart error: {chart_data['error']}"

        # 1. OPTIMIZE DATA
        planets = ['sun', 'moon', 'ascendant', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']
        essential_data = []
        
        def get_p_data(source, key):
            if isinstance(source, dict): return source.get(key, {})
            if hasattr(source, 'planets'): return getattr(source.planets, 'get', lambda k,d: d)(key, {})
            return {}

        for p in planets:
            p_data = get_p_data(chart_data, p)
            if p_data:
                sign = p_data.get('sign', '?') if isinstance(p_data, dict) else getattr(p_data, 'sign', '?')
                deg = p_data.get('degree', 0) if isinstance(p_data, dict) else getattr(p_data, 'degree', 0)
                house = p_data.get('house', '?') if isinstance(p_data, dict) else getattr(p_data, 'house', '?')
                rules = p_data.get('rules_houses', '-') if isinstance(p_data, dict) else getattr(p_data, 'rules_houses', '-')
                essential_data.append(f"{p.capitalize()}: {sign} {deg}° (House: {house}, Rules: {rules})")
        
        planets_str = ", ".join(essential_data)

        # 2. SYSTEM INSTRUCTION
        system_instruction = (
            f"You are an expert {'KP' if is_kp_mode else 'Vedic'} Astrologer. "
            "Give an accurate prediction (approx 50 words) based on the planetary data. "
            "Maintain conversation continuity if history is provided."
        )

        def format_msg(role, content):
            # Extract text from pre-formatted content blocks
            if isinstance(content, list):
                if len(content) > 0 and isinstance(content[0], dict) and 'text' in content[0]:
                    content = content[0]['text']
                else:
                    return {"role": role, "content": content}
            
            content_type = "input_text" if role in ["user", "system"] else "output_text"
            return {"role": role, "content": [{"type": content_type, "text": content}]}

        # 3. PREPARE MESSAGES
        messages = [format_msg("system", system_instruction)]
        if history:
            for msg in history[-10:]:
                if msg.get("role") == "user" and msg.get("content") == user_query:
                    continue
                messages.append(format_msg(msg["role"], msg["content"]))

        current_prompt = f"Planetary Positions: {planets_str}\n\nUser Question: {user_query}"
        messages.append(format_msg("user", current_prompt))

        client = OpenAI(api_key=api_key)
        
        # 4. GENERATE CONTENT
        response = await asyncio.to_thread(
            client.responses.create,
            model=OPENAI_MODEL,
            input=messages,
            reasoning={"effort": "low"}
        )
        
        if response and hasattr(response, 'output_text'):
            return response.output_text.strip()
        return "⚠️ Error: Empty response from AI"
            
    except Exception as e:
        logger.exception(f"Exception during AI prediction: {str(e)}")
        raise e  # Tenacity needs this to retry


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def get_followup_questions(api_key, chart_data=None, is_kp_mode=False):
    """
    Generates 3 follow-up questions based on the chart data only (generic/context-aware).
    """
    if not api_key:
        return ["Error: API Key missing"] * 3
        
    try:
        system_instruction = (
            f"You are an expert {'KP' if is_kp_mode else 'Vedic'} Astrologer. "
            "Generate 3 VERY SHORT follow-up questions for the user. "
            "CRITICAL: Each question MUST be under 7 words. No preamble."
            "Format: Question 1 || Question 2 || Question 3"
        )
        
        planets_context = ""
        if chart_data:
            planets = ['sun', 'moon', 'ascendant', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']
            essential_data = []
            def get_p_data(source, key):
                if isinstance(source, dict): return source.get(key, {})
                if hasattr(source, 'planets'): return getattr(source.planets, 'get', lambda k,d: d)(key, {})
                return {}

            for p in planets:
                p_data = get_p_data(chart_data, p)
                if p_data:
                    sign = p_data.get('sign', '?') if isinstance(p_data, dict) else getattr(p_data, 'sign', '?')
                    deg = p_data.get('degree', 0) if isinstance(p_data, dict) else getattr(p_data, 'degree', 0)
                    house = p_data.get('house', '?') if isinstance(p_data, dict) else getattr(p_data, 'house', '?')
                    rules = p_data.get('rules_houses', '-') if isinstance(p_data, dict) else getattr(p_data, 'rules_houses', '-')
                    essential_data.append(f"{p.capitalize()}: {sign} {deg}° (House: {house}, Rules: {rules})")
            planets_context = f"Planetary Data: {', '.join(essential_data)}\n\n"

        def format_msg(role, content):
            # Extract text from pre-formatted content blocks
            if isinstance(content, list):
                if len(content) > 0 and isinstance(content[0], dict) and 'text' in content[0]:
                    content = content[0]['text']
                else:
                    return {"role": role, "content": content}
            
            content_type = "input_text" if role in ["user", "system"] else "output_text"
            return {"role": role, "content": [{"type": content_type, "text": content}]}

        prompt_text = (
            f"Planetary Context: {planets_context}\n"
            "Output exactly 3 VERY SHORT questions (MAX 7 WORDS EACH) separated by ||. No extra text."
        )
        
        messages = [format_msg("user", prompt_text)]

        client = OpenAI(api_key=api_key)
        
        response = await asyncio.to_thread(
            client.responses.create,
            model=OPENAI_MODEL,
            input=messages,
            reasoning={"effort": "low"}
        )
        
        raw_text = response.output_text.strip() if response and hasattr(response, 'output_text') else ""
        logger.info(f"Raw AI Suggestions response: {raw_text}")
        
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
