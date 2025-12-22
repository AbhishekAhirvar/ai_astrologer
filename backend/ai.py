import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Warning: GEMINI_API_KEY not found in environment variables.")

def get_astrology_prediction(chart_data, user_query):
    """
    Sends chart data and query to Gemini.
    """
    if not api_key:
        return "Error: API Key is missing. Please set GEMINI_API_KEY."
    
    try:
        genai.configure(api_key=api_key)
        
        # Use system instruction for better behavioral control
        system_instruction = (
            "You are an expert Vedic Astrologer. You provide detailed, insightful, and empathetic analyses based on "
            "Sidereal/Lahiri birth chart data. Your responses should be comprehensive, well-structured, and "
            "approximately 250 words long. Never provide short or truncated answers."
        )
        
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction=system_instruction
        )

        if "error" in chart_data:
            return f"Could not generate prediction due to chart error: {chart_data['error']}"

        # Construct Prompt
        metadata = chart_data.get('_metadata', {})
        gender = metadata.get('gender', 'Unknown')
        
        prompt = f"""
        User Birth Details: {metadata.get('name', 'Unknown')} ({gender}) - {metadata.get('datetime', 'N/A')} at {metadata.get('location', 'Unknown')}
        
        Planetary Positions:
        - Sun: {chart_data.get('sun', {})}
        - Moon: {chart_data.get('moon', {})}
        - Ascendant (Lagna): {chart_data.get('ascendant', {})}
        - Mercury: {chart_data.get('mercury', {})}
        - Venus: {chart_data.get('venus', {})}
        - Mars: {chart_data.get('mars', {})}
        - Jupiter: {chart_data.get('jupiter', {})}
        - Saturn: {chart_data.get('saturn', {})}
        - Rahu: {chart_data.get('rahu', {})}
        - Ketu: {chart_data.get('ketu', {})}
        
        User Question: {user_query}
        
        Analyze the chart data in relation to the user's question and provide a detailed response of 200-250 words.
        Ensure the response is complete and concludes naturally.
        """
        
        response = model.generate_content(
            prompt,
            generation_config={
                'max_output_tokens': 2000, # Increased significantly
                'temperature': 0.7,
            }
        )
        return response.text
    except Exception as e:
        return f"Error communicating with AI: {str(e)}"
