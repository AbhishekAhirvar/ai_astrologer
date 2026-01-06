import os
from google import genai
from google.genai import types
from backend.logger import logger
from dotenv import load_dotenv

load_dotenv()

# Configure Google Gemini
GEMINI_MODEL = "gemini-3-flash-preview"

# Log model info on startup
logger.info(f"🤖 AI Module initialized with Google Gemini model: {GEMINI_MODEL}")


def get_astrology_prediction(chart_data, user_query, api_key, is_kp_mode=False):
    """
    Sends essential chart data and query to Google Gemini 3 Flash Preview API.
    """
    if not api_key:
        logger.error("API Key not provided to get_astrology_prediction")
        return "⚠️ Error: API Key missing. Please check configuration."
    
    try:
        if "error" in chart_data:
            return f"Could not generate prediction due to chart error: {chart_data['error']}"

        # 1. OPTIMIZE DATA: Extract only essential info to save tokens
        planets = ['sun', 'moon', 'ascendant', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']
        essential_data = []
        
        # Handle Pydantic models or Dicts
        def get_p_data(source, key):
            if isinstance(source, dict):
                return source.get(key, {})
            # chart_data is likely ChartResponse pydantic model
            if hasattr(source, 'planets'):
                return getattr(source.planets, 'get', lambda k,d: d)(key, {})
            # Fallback
            return {}

        for p in planets:
            p_data = get_p_data(chart_data, p)
            if p_data:
                # Handle Pydantic model access or Dict access
                if isinstance(p_data, dict):
                    sign = p_data.get('sign', '?')
                    deg = p_data.get('degree', 0)
                else:
                    sign = getattr(p_data, 'sign', '?')
                    deg = getattr(p_data, 'degree', 0)
                    
                essential_data.append(f"{p.capitalize()}: {sign} {deg}°")
        
        planets_str = ", ".join(essential_data)

        # 2. SYSTEM INSTRUCTION - Focus on Answer ONLY
        if is_kp_mode:
            system_instruction = (
                "You are an expert KP Astrologer. Give an accurate prediction (approx 50 words) based on the planetary data and KP rules. "
                "Do NOT provide suggestions or questions."
            )
        else:
            system_instruction = (
                "You are an expert Vedic Astrologer. Give an accurate prediction (approx 50 words) based on the planetary data. "
                "Do NOT provide suggestions or questions."
            )

        # 3. PROMPT
        prompt_content = f"{system_instruction}\n\nPlanetary Positions: {planets_str}\n\nQuestion: {user_query}"

        # Initialize Gemini client with new API
        client = genai.Client(api_key=api_key)
        
        # Generate response
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt_content,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=1000,
            )
        )
        
        if response and response.text:
            return response.text.strip()
        else:
            return "⚠️ Error: Empty response from AI"
            
    except Exception as e:
        logger.exception(f"Exception during AI prediction: {str(e)}")
        return f"⚠️ Connection Error: {str(e)}"


def get_followup_questions(user_query, api_key, is_kp_mode=False):
    """
    Generates 3 follow-up questions based on the user's query.
    """
    if not api_key:
        return ["Error: API Key missing"] * 3
        
    try:
        # 1. SYSTEM INSTRUCTION - Focus on Questions ONLY
        if is_kp_mode:
            system_instruction = (
                "You are an expert KP Astrologer. "
                "Generate exactly 3 good, thoughtful follow-up questions based on real-life situations and the user's specific query. "
                "KP Context: Sub-lords, significators, ruling planets."
                "Format: Question 1 || Question 2 || Question 3"
            )
        else:
            system_instruction = (
                "You are an expert Vedic Astrologer. "
                "Generate exactly 3 good, thoughtful follow-up questions based on real-life situations and the user's specific query. "
                "Format: Question 1 || Question 2 || Question 3"
            )

        prompt_content = f"{system_instruction}\n\nUser Question: {user_query}\n\nOutput only the 3 questions separated by ||."

        client = genai.Client(api_key=api_key)
        
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt_content,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=100,
            )
        )
        
        if response and response.text:
            raw_text = response.text.strip()
            # Parse the || separated questions
            parts = raw_text.split("||")
            suggestions = []
            for p in parts:
                clean_q = p.strip().replace("**", "").replace("*", "")
                if clean_q:
                    if not clean_q.endswith('?'):
                        clean_q += '?'
                    suggestions.append(clean_q)
            
            # Ensure we have exactly 3
            while len(suggestions) < 3:
                suggestions.append("What else should I know?")
            
            return suggestions[:3]
            
        return ["What does this mean?", "Any remedies?", "Future outlook?"]

    except Exception as e:
        logger.exception(f"Exception during suggestions generation: {str(e)}")
        return ["Error generating suggestions"] * 3
