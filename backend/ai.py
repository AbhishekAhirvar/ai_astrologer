import os
import google.generativeai as genai
from backend.logger import logger
from dotenv import load_dotenv

load_dotenv()

# Configure Google Gemini
GEMINI_MODEL = "gemini-3.0-flash"


def get_astrology_prediction(chart_data, user_query, api_key, is_kp_mode=False):
    """
    Sends essential chart data and query to Google Gemini 3.0 Flash API.
    """
    if not api_key:
        logger.error("API Key not provided to get_astrology_prediction")
        return "⚠️ Error: API Key missing. Please check configuration.", []
    
    try:
        # Configure Gemini API
        genai.configure(api_key=api_key)
        
        if "error" in chart_data:
            return f"Could not generate prediction due to chart error: {chart_data['error']}", []

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

        # 2. SYSTEM INSTRUCTION
        if is_kp_mode:
            system_instruction = (
                "You are an expert KP Astrologer (Krishnamurti Paddhati). Analyze using KP rules: Sub-lords, Custal significators, and Ruling Planets. "
                "GROUNDING RULES: "
                "1. Strictly answer only questions related to astrology, destiny, or life events via planetary analysis. "
                "2. If a question is slightly unrelated (e.g., 'how to be happy'), link it back to their planets (e.g., Moon/Jupiter positions). "
                "3. If a question is completely unrelated (e.g., 'how to bake a cake', 'coding help'), politely refuse and state you can only provide astrological guidance. "
                "4. Provide a concise response under 50 words. "
                "5. ALWAYS end by adding exactly 3 full-sentence, KP-specialized questions separated by ' || ' and preceded by the tag [SUGGESTIONS]."
            )
        else:
            system_instruction = (
                "You are an expert Vedic Astrologer. "
                "GROUNDING RULES: "
                "1. Strictly answer only questions related to astrology, destiny, or life events via planetary analysis. "
                "2. If a question is slightly unrelated, link it back to their planets or dashas. "
                "3. If a question is completely unrelated (e.g., 'cooking', 'technology', 'math'), politely refuse to answer. "
                "4. Provide a concise response under 50 words. "
                "5. ALWAYS end by adding exactly 3 full-sentence, real-life suggested questions separated by ' || ' and preceded by the tag [SUGGESTIONS]."
            )

        # 3. PROMPT
        prompt_content = f"{system_instruction}\n\nPositions: {planets_str}. User Question: {user_query}."

        # Initialize Gemini model
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 150,
            }
        )
        
        # Generate response
        response = model.generate_content(prompt_content)
        
        if response and response.text:
            logger.info(f"AI prediction successful for {user_query[:30]}...")
            return response.text.strip()
        else:
            logger.error("Empty response from Gemini API")
            return "⚠️ Error: Empty response from AI", []
            
    except Exception as e:
        logger.exception(f"Exception during AI prediction: {str(e)}")
        return f"⚠️ Connection Error: {str(e)}", []
