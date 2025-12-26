import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Configure Hugging Face (using the token stored in GEMINI_API_KEY as per user environment)
api_key = os.getenv("GEMINI_API_KEY")
HF_MODEL = "Qwen/Qwen2.5-72B-Instruct"

def get_astrology_prediction(chart_data, user_query, is_kp_mode=False):
    """
    Sends essential chart data and query to Hugging Face Inference API.
    """
    if not api_key:
        return "Error: Hugging Face API Token (GEMINI_API_KEY) is missing. Please set it in the .env file."
    
    try:
        if "error" in chart_data:
            return f"Could not generate prediction due to chart error: {chart_data['error']}"

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
                "1. Provide a concise response under 50 words. "
                "2. ALWAYS end by adding exactly 3 full-sentence, KP-specialized questions (e.g., 'Who is the sub-lord of my 10th house?, Which planets are significators for my career?, What are my ruling planets right now?') separated by COMMAS and preceded by the tag [SUGGESTIONS]."
            )
        else:
            system_instruction = (
                "You are an expert Vedic Astrologer. "
                "1. Provide a concise response under 50 words. "
                "2. ALWAYS end by adding exactly 3 full-sentence, real-life suggested questions (e.g., 'What are the main obstacles in my career right now?, When can I expect significant financial growth?, Is there a possibility of foreign travel in my chart?') separated by COMMAS and preceded by the tag [SUGGESTIONS]."
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
        
        if response.status_code != 200:
            return f"Error from Hugging Face: {response.text}"
            
        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            text = result['choices'][0].get('message', {}).get('content', '').strip()
        else:
            text = str(result)
            
        return text
    except Exception as e:
        return f"Error communicating with AI: {str(e)}"

