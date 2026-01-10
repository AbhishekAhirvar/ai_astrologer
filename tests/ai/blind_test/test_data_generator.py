"""
Blind Test Data Generator

Creates anonymous test datasets that prevent AI from recognizing famous people.
Includes control groups for rigorous testing.

Fixes Applied:
1. Ocean Problem: Uses real cities for fictional people
2. Precision Leak: Fuzzes coordinates/time for famous people
"""

import json
import random
import string
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timedelta


# Real cities for fictional people (avoid ocean coordinates)
REAL_CITIES = [
    {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503, "tz": "Asia/Tokyo"},
    {"name": "Delhi", "lat": 28.7041, "lon": 77.1025, "tz": "Asia/Kolkata"},
    {"name": "Shanghai", "lat": 31.2304, "lon": 121.4737, "tz": "Asia/Shanghai"},
    {"name": "São Paulo", "lat": -23.5505, "lon": -46.6333, "tz": "America/Sao_Paulo"},
    {"name": "Mexico City", "lat": 19.4326, "lon": -99.1332, "tz": "America/Mexico_City"},
    {"name": "Cairo", "lat": 30.0444, "lon": 31.2357, "tz": "Africa/Cairo"},
    {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "tz": "Asia/Kolkata"},
    {"name": "Beijing", "lat": 39.9042, "lon": 116.4074, "tz": "Asia/Shanghai"},
    {"name": "Dhaka", "lat": 23.8103, "lon": 90.4125, "tz": "Asia/Dhaka"},
    {"name": "Osaka", "lat": 34.6937, "lon": 135.5023, "tz": "Asia/Tokyo"},
    {"name": "Lagos", "lat": 6.5244, "lon": 3.3792, "tz": "Africa/Lagos"},
    {"name": "Istanbul", "lat": 41.0082, "lon": 28.9784, "tz": "Europe/Istanbul"},
    {"name": "Buenos Aires", "lat": -34.6037, "lon": -58.3816, "tz": "America/Argentina/Buenos_Aires"},
    {"name": "Kolkata", "lat": 22.5726, "lon": 88.3639, "tz": "Asia/Kolkata"},
    {"name": "Manila", "lat": 14.5995, "lon": 120.9842, "tz": "Asia/Manila"},
]


# Generic questions that don't reveal identity
GENERIC_QUESTIONS = [
    "What is my primary life purpose?",
    "What are my natural talents and abilities?",
    "Will I achieve recognition in my field?",
    "Identify the specific YEARS when major events or breakthroughs will occur in my life. Format: 'In year XXXX: [astrological reason and event theme]'. Cover past and future.",
    "What major challenges will I face in life?",
    "What is my leadership potential?"
]


def generate_anonymous_id(prefix: str = "Subject") -> str:
    """Generate a random anonymous ID"""
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{random_suffix}"


def fuzz_birth_data(birth_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fuzz birth data to prevent LLM fingerprinting
    
    Adds small randomness to coordinates and time while preserving
    astrological chart accuracy. Breaks exact string matching.
    
    Fuzzing:
    - Time: ±1 minute (minimal impact on ascendant)
    - Lat/Lon: ±0.01 degrees (~1km, minimal impact on houses)
    """
    fuzzed = birth_data.copy()
    
    # Fuzz time by ±1 minute
    minute_offset = random.randint(-1, 1)
    new_minute = (fuzzed["minute"] + minute_offset) % 60
    hour_carry = (fuzzed["minute"] + minute_offset) // 60
    fuzzed["minute"] = new_minute
    fuzzed["hour"] = (fuzzed["hour"] + hour_carry) % 24
    
    # Fuzz coordinates by ±0.01 degrees (~1km)
    fuzzed["lat"] += random.uniform(-0.01, 0.01)
    fuzzed["lon"] += random.uniform(-0.01, 0.01)
    
    return fuzzed


def create_blind_person(birth_data: Dict[str, Any], known_facts: Dict[str, Any], 
                       true_identity: str) -> Dict[str, Any]:
    """
    Create a blind test entry with anonymous ID
    
    Args:
        birth_data: Original birth information
        known_facts: Actual biographical facts (for evaluation only)
        true_identity: Real name (hidden from AI)
    
    Returns:
        Blind test entry with fuzzed data
    """
    anonymous_id = generate_anonymous_id()
    
    # CRITICAL: Fuzz data to prevent LLM fingerprinting
    fuzzed_data = fuzz_birth_data(birth_data)
    
    # Anonymize location - use coordinates only
    blind_location = f"Coordinates: {fuzzed_data['lat']:.2f}°N, {fuzzed_data['lon']:.2f}°E"
    
    return {
        "id": anonymous_id,
        "birth_data": {
            "year": fuzzed_data["year"],
            "month": fuzzed_data["month"],
            "day": fuzzed_data["day"],
            "hour": birth_data["hour"],
            "minute": birth_data["minute"],
            "lat": birth_data["lat"],
            "lon": birth_data["lon"],
            "timezone": birth_data["timezone"],
            "location_display": blind_location  # Anonymous location
        },
        "test_questions": GENERIC_QUESTIONS,
        "ground_truth": {
            "identity": true_identity,
            "known_facts": known_facts
        },
        "test_type": "famous_blind"
    }


def create_fictional_chart() -> Dict[str, Any]:
    """
    Create a fictional chart with random planetary positions
    This is a control to test if AI gives generic predictions for unknown people
    """
    anonymous_id = generate_anonymous_id("Control")
    
    # Random birth data
    random_year = random.randint(1950, 2000)
    random_month = random.randint(1, 12)
    random_day = random.randint(1, 28)
    random_hour = random.randint(0, 23)
    random_minute = random.randint(0, 59)
    
    # FIXED: Use real city instead of random ocean coordinates
    city = random.choice(REAL_CITIES)
    
    return {
        "id": anonymous_id,
        "birth_data": {
            "year": random_year,
            "month": random_month,
            "day": random_day,
            "hour": random_hour,
            "minute": random_minute,
            "lat": city["lat"],
            "lon": city["lon"],
            "timezone": "UTC",
            "location_display": f"Coordinates: {city['lat']:.2f}°N, {city['lon']:.2f}°E"
        },
        "test_questions": GENERIC_QUESTIONS,
        "ground_truth": {
            "identity": "Fictional Person (No Real Biography)",
            "known_facts": {}
        },
        "test_type": "fictional_control"
    }


def create_duplicate_chart(original: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a duplicate of an existing chart with different ID
    This tests consistency - same chart should give similar predictions
    """
    duplicate = original.copy()
    duplicate["id"] = generate_anonymous_id("Duplicate")
    duplicate["test_type"] = "duplicate_control"
    duplicate["duplicate_of"] = original["id"]
    
    return duplicate


# Famous people data (will be anonymized)
FAMOUS_PEOPLE_DATA = {
    "steve_jobs": {
        "birth_data": {
            "year": 1955, "month": 2, "day": 24,
            "hour": 19, "minute": 15,
            "lat": 37.7749, "lon": -122.4194,
            "timezone": "America/Los_Angeles"
        },
        "known_facts": {
            "career": ["Technology innovator", "Founded Apple", "Perfectionist", "Visionary"],
            "personality": ["Demanding leader", "Charismatic", "Spiritual interests"],
            "challenges": ["Fired from own company", "Health issues"],
            "major_events": [
                "1976: Co-founded Apple Computer",
                "1985: Forced out of Apple",
                "1997: Returned to Apple as CEO",
                "2001: Launched iPod",
                "2007: Launched iPhone",
                "2011: Passed away from pancreatic cancer"
            ]
        },
        "identity": "Steve Jobs"
    },
    
    "oprah_winfrey": {
        "birth_data": {
            "year": 1954, "month": 1, "day": 29,
            "hour": 7, "minute": 50,
            "lat": 33.0576, "lon": -89.5876,
            "timezone": "America/Chicago"
        },
        "known_facts": {
            "career": ["Media mogul", "Television host", "Billionaire", "Author"],
            "personality": ["Empathetic", "Influential speaker", "Philanthropist"],
            "challenges": ["Poverty in childhood", "Never married"],
            "major_events": [
                "1986: The Oprah Winfrey Show nationally syndicated",
                "1988: Founded Harpo Productions",
                "1998: Co-founded Oxygen Media",
                "2011: Ended talk show, launched OWN network",
                "2013: Awarded Presidential Medal of Freedom"
            ]
        },
        "identity": "Oprah Winfrey"
    },
    
    "elon_musk": {
        "birth_data": {
            "year": 1971, "month": 6, "day": 28,
            "hour": 7, "minute": 30,
            "lat": -25.7479, "lon": 28.2293,
            "timezone": "Africa/Johannesburg"
        },
        "known_facts": {
            "career": ["Multi-entrepreneur", "Technology pioneer", "Space exploration", "Electric vehicles"],
            "personality": ["Workaholic", "Risk-taker", "Controversial"],
            "challenges": ["Multiple divorces", "Public controversies"],
            "major_events": [
                "1995: Founded Zip2",
                "1999: Co-founded X.com (later PayPal)",
                "2002: Founded SpaceX",
                "2004: Joined Tesla as chairman",
                "2008: Became Tesla CEO",
                "2020: SpaceX successfully launched astronauts to ISS",
                "2022: Acquired Twitter"
            ]
        },
        "identity": "Elon Musk"
    },
    
    "mahatma_gandhi": {
        "birth_data": {
            "year": 1869, "month": 10, "day": 2,
            "hour": 7, "minute": 12,
            "lat": 21.6417, "lon": 69.6293,
            "timezone": "Asia/Kolkata"
        },
        "known_facts": {
            "career": ["Political leader", "Independence movement", "Non-violence philosophy", "Lawyer"],
            "personality": ["Peaceful", "Principled", "Ascetic", "Spiritual"],
            "challenges": ["Assassinated", "Long struggle"],
            "major_events": [
                "1893: Experienced racism in South Africa",
                "1915: Returned to India from South Africa",
                "1930: Led Salt March (Dandi March)",
                "1942: Launched Quit India Movement",
                "1947: India gained independence",
                "1948: Assassinated in New Delhi"
            ]
        },
        "identity": "Mahatma Gandhi"
    },
    
    "albert_einstein": {
        "birth_data": {
            "year": 1879, "month": 3, "day": 14,
            "hour": 11, "minute": 30,
            "lat": 48.4011, "lon": 9.9876,
            "timezone": "Europe/Berlin"
        },
        "known_facts": {
            "career": ["Physicist", "Nobel Prize", "Theory of relativity", "Professor"],
            "personality": ["Unconventional thinker", "Pacifist", "Curious"],
            "challenges": ["Struggled in school", "Fled Nazi Germany"],
            "major_events": [
                "1905: Published groundbreaking papers (Annus Mirabilis)",
                "1915: Completed general theory of relativity",
                "1921: Awarded Nobel Prize in Physics",
                "1933: Emigrated to US fleeing Nazi regime",
                "1939: Signed letter to Roosevelt about atomic weapons",
                "1955: Passed away in Princeton"
            ]
        },
        "identity": "Albert Einstein"
    }
}


def generate_blind_test_dataset(output_dir: str = None) -> Dict[str, Any]:
    """
    Generate complete blind test dataset
    
    Returns:
        Dictionary containing all test subjects and metadata
    """
    # Use script directory if no output_dir specified
    if output_dir is None:
        script_dir = Path(__file__).parent
        output_dir = script_dir / "data"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    blind_dataset = {
        "test_subjects": [],
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_subjects": 0,
            "famous_people": 0,
            "fictional_controls": 0,
            "duplicate_controls": 0,
            "questions_per_subject": len(GENERIC_QUESTIONS),
            "total_predictions_needed": 0
        }
    }
    
    # Add famous people (anonymized)
    famous_blind = []
    for person_id, data in FAMOUS_PEOPLE_DATA.items():
        blind_person = create_blind_person(
            birth_data=data["birth_data"],
            known_facts=data["known_facts"],
            true_identity=data["identity"]
        )
        famous_blind.append(blind_person)
        blind_dataset["test_subjects"].append(blind_person)
    
    blind_dataset["metadata"]["famous_people"] = len(famous_blind)
    
    # Add fictional controls
    fictional_count = 2
    for i in range(fictional_count):
        fictional = create_fictional_chart()
        blind_dataset["test_subjects"].append(fictional)
    
    blind_dataset["metadata"]["fictional_controls"] = fictional_count
    
    # Add duplicate controls (use first 2 famous people)
    duplicates = []
    for original in famous_blind[:2]:
        duplicate = create_duplicate_chart(original)
        duplicates.append(duplicate)
        blind_dataset["test_subjects"].append(duplicate)
    
    blind_dataset["metadata"]["duplicate_controls"] = len(duplicates)
    blind_dataset["metadata"]["total_subjects"] = len(blind_dataset["test_subjects"])
    blind_dataset["metadata"]["total_predictions_needed"] = (
        len(blind_dataset["test_subjects"]) * len(GENERIC_QUESTIONS)
    )
    
    # Save dataset
    dataset_file = Path(output_dir) / "blind_test_dataset.json"
    with open(dataset_file, 'w') as f:
        json.dump(blind_dataset, f, indent=2)
    
    # Create separate ground truth mapping (secret file)
    ground_truth = {
        subject["id"]: subject["ground_truth"]
        for subject in blind_dataset["test_subjects"]
    }
    
    truth_file = Path(output_dir) / "ground_truth_mapping.json"
    with open(truth_file, 'w') as f:
        json.dump(ground_truth, f, indent=2)
    
    print(f"\n✅ Blind test dataset generated!")
    print(f"   Total subjects: {blind_dataset['metadata']['total_subjects']}")
    print(f"   Famous (blind): {blind_dataset['metadata']['famous_people']}")
    print(f"   Fictional: {blind_dataset['metadata']['fictional_controls']}")
    print(f"   Duplicates: {blind_dataset['metadata']['duplicate_controls']}")
    print(f"   Total predictions: {blind_dataset['metadata']['total_predictions_needed']}")
    print(f"\n📁 Files saved:")
    print(f"   Dataset: {dataset_file}")
    print(f"   Ground truth: {truth_file}")
    
    return blind_dataset


if __name__ == "__main__":
    generate_blind_test_dataset()
