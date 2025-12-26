import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.ai import get_astrology_prediction

# Dummy chart data
chart_data = {
    '_metadata': {
        'name': 'Test User',
        'gender': 'Male',
        'datetime': '2025-12-22 12:30',
        'location': 'New Delhi'
    },
    'sun': {'sign': 'Sagittarius', 'degree': 20},
    'moon': {'sign': 'Pisces', 'degree': 15},
    'ascendant': {'sign': 'Aries', 'degree': 10},
    'mars': {'sign': 'Scorpio', 'degree': 5},
    'mercury': {'sign': 'Sagittarius', 'degree': 10},
    'jupiter': {'sign': 'Gemini', 'degree': 12},
    'venus': {'sign': 'Capricorn', 'degree': 8},
    'saturn': {'sign': 'Sagittarius', 'degree': 25},
    'rahu': {'sign': 'Capricorn', 'degree': 20},
    'ketu': {'sign': 'Cancer', 'degree': 20},
}

print("--- Testing Standard Vedic Mode ---")
query = "What does my chart say about my career?"
print(f"Query: {query}")
response = get_astrology_prediction(chart_data, query)
print(f"AI Response: {response}\n")

print("--- Testing KP Mode ---")
query = "Perform a KP analysis."
print(f"Query: {query}")
response = get_astrology_prediction(chart_data, query, is_kp_mode=True)
print(f"AI Response: {response}")
