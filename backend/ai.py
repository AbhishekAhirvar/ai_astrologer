import os
import requests
from backend.logger import logger
from dotenv import load_dotenv

load_dotenv()

# Configure Hugging Face (using the token stored in KEY as per user environment)
api_key = os.getenv("KEY")
HF_MODEL = "Qwen/Qwen2.5-72B-Instruct"

def get_astrology_prediction(chart_data, user_query, is_kp_mode=False):
    """
    Sends essential chart data and query to Hugging Face Inference API.
    """
    if not api_key:
        logger.error("Hugging Face API Key (KEY) not found in environment variables!")
        return "⚠️ Error: API Key missing. Please check Space secrets.", []
    
    try:
        if "error" in chart_data:
            return f"Could not generate prediction due to chart error: {chart_data['error']}", []

        # 1. OPTIMIZE DATA: Extract only essential info to save tokens
        planets = ['sun', 'moon', 'ascendant', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']
        essential_data = []
        
        for p in planets:
            p_data = chart_data.get(p, {})
            if p_data:
                sign = p_data.get('sign', '?')
                deg = p_data.get('degree', 0)
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
        prompt_content = f"Positions: {planets_str}. User Ques: {user_query}."

        API_URL = "https://router.huggingface.co/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        payload = {
            "model": HF_MODEL,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt_content}
            ],
            "max_tokens": 150, # Increased slightly to allow for suggestions
            "temperature": 0.7
        }

        response = requests.post(API_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            logger.info(f"AI prediction successful for {user_query[:30]}...")
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                text = result['choices'][0].get('message', {}).get('content', '').strip()
            else:
                text = str(result) # Fallback if 'choices' not as expected
            return text
        else:
            error_data = response.text
            logger.error(f"AI API Error ({response.status_code}): {error_data}")
            return f"⚠️ API Error: {response.status_code}", []
    except Exception as e:
        logger.exception(f"Exception during AI prediction: {str(e)}")
        return f"⚠️ Connection Error: {str(e)}", []
