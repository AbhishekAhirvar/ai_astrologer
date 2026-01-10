"""
Test Prediction Accuracy Against Famous People's Life Events

This test file validates astrological predictions by comparing them against
documented life events of famous personalities. Each test case includes:
- Birth data (date, time, location)
- Known life events and characteristics
- AI predictions
- Accuracy assessment

Data sources: Public birth records and documented biographies
"""

import sys
import os
import asyncio
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.astrology import generate_vedic_chart
from backend.ai import get_astrology_prediction
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


# ============================================================================
# FAMOUS PEOPLE DATABASE
# ============================================================================

FAMOUS_PEOPLE = {
    "steve_jobs": {
        "name": "Steve Jobs",
        "birth_data": {
            "year": 1955,
            "month": 2,
            "day": 24,
            "hour": 19,
            "minute": 15,
            "city": "San Francisco",
            "lat": 37.7749,
            "lon": -122.4194,
            "timezone": "America/Los_Angeles"
        },
        "known_facts": {
            "career": [
                "Founded Apple Computer at age 21",
                "Revolutionized personal computing industry",
                "Known for innovation and design aesthetics",
                "Fired from Apple in 1985, returned in 1997",
                "Created multiple billion-dollar companies (Apple, Pixar, NeXT)"
            ],
            "personality": [
                "Perfectionist and demanding leader",
                "Charismatic public speaker",
                "Visionary and unconventional thinker",
                "Spiritual interest in Buddhism and Eastern philosophy"
            ],
            "life_events": [
                "Adopted at birth",
                "Dropped out of college but continued auditing classes",
                "Married Laurene Powell in 1991",
                "Battled pancreatic cancer (diagnosed 2003)",
                "Passed away in 2011"
            ],
            "timing": {
                "major_success": "1984 (Macintosh launch)",
                "crisis": "1985 (ousted from Apple)",
                "comeback": "1997 (returned to Apple)",
                "peak": "2007 (iPhone launch)"
            }
        },
        "test_questions": [
            "What is my career path and potential?",
            "Will I face setbacks in my work?",
            "What are my leadership qualities?",
            "Will I achieve fame and recognition?",
            "What health issues should I watch for?"
        ]
    },
    
    "oprah_winfrey": {
        "name": "Oprah Winfrey",
        "birth_data": {
            "year": 1954,
            "month": 1,
            "day": 29,
            "hour": 7,
            "minute": 50,
            "city": "Kosciusko",
            "lat": 33.0576,
            "lon": -89.5876,
            "timezone": "America/Chicago"
        },
        "known_facts": {
            "career": [
                "Media mogul and billionaire",
                "Hosted The Oprah Winfrey Show for 25 years",
                "Founded OWN (Oprah Winfrey Network)",
                "Influential book club creator",
                "Actress and producer"
            ],
            "personality": [
                "Empathetic and compassionate",
                "Influential public speaker",
                "Philanthropist and humanitarian",
                "Overcame poverty and abuse"
            ],
            "life_events": [
                "Born into poverty in rural Mississippi",
                "Started broadcasting career at age 19",
                "Became first Black female billionaire",
                "Never married, long-term partner Stedman Graham"
            ],
            "timing": {
                "breakthrough": "1986 (nationally syndicated show)",
                "peak_influence": "1990s-2000s",
                "network_launch": "2011 (OWN)"
            }
        },
        "test_questions": [
            "What is my relationship with public speaking?",
            "Will I have success in media?",
            "What are my money prospects?",
            "Will I get married?",
            "What is my life purpose?"
        ]
    },
    
    "elon_musk": {
        "name": "Elon Musk",
        "birth_data": {
            "year": 1971,
            "month": 6,
            "day": 28,
            "hour": 7,
            "minute": 30,
            "city": "Pretoria",
            "lat": -25.7479,
            "lon": 28.2293,
            "timezone": "Africa/Johannesburg"
        },
        "known_facts": {
            "career": [
                "Founded/co-founded: PayPal, Tesla, SpaceX, Neuralink, The Boring Company",
                "Richest person in the world (at various times)",
                "Pioneered electric vehicles and private space exploration",
                "Acquired Twitter (X) in 2022"
            ],
            "personality": [
                "Workaholic (80-100 hour weeks)",
                "Risk-taker and visionary",
                "Controversial on social media",
                "Interest in Mars colonization and AI"
            ],
            "life_events": [
                "Parents divorced when he was 10",
                "Moved to Canada at 17, then USA",
                "Multiple marriages and divorces",
                "Father of 11 children"
            ],
            "timing": {
                "paypal_sale": "2002 ($165 million)",
                "spacex_founding": "2002",
                "tesla_success": "2008 onwards",
                "twitter_acquisition": "2022"
            }
        },
        "test_questions": [
            "Will I be involved in technology?",
            "What are my entrepreneurial prospects?",
            "Will I take big risks?",
            "How is my relationship life?",
            "Will I achieve worldwide fame?"
        ]
    },
    
    "mahatma_gandhi": {
        "name": "Mahatma Gandhi",
        "birth_data": {
            "year": 1869,
            "month": 10,
            "day": 2,
            "hour": 7,
            "minute": 12,
            "city": "Porbandar",
            "lat": 21.6417,
            "lon": 69.6293,
            "timezone": "Asia/Kolkata"
        },
        "known_facts": {
            "career": [
                "Leader of Indian independence movement",
                "Developed philosophy of non-violent resistance (Satyagraha)",
                "Lawyer by training",
                "International symbol of peace"
            ],
            "personality": [
                "Simple lifestyle, ascetic",
                "Principled and morally driven",
                "Patient and peaceful",
                "Deeply spiritual (Hindu philosophy)"
            ],
            "life_events": [
                "Married at age 13 (arranged marriage)",
                "Studied law in London",
                "Spent 21 years in South Africa fighting discrimination",
                "Led India to independence in 1947",
                "Assassinated in 1948"
            ],
            "timing": {
                "south_africa": "1893-1914",
                "return_to_india": "1915",
                "salt_march": "1930",
                "independence": "1947",
                "assassination": "1948"
            }
        },
        "test_questions": [
            "What is my life purpose?",
            "Will I be involved in politics or social change?",
            "What are my spiritual inclinations?",
            "Will I face violence or danger?",
            "Will I influence many people?"
        ]
    },
    
    "albert_einstein": {
        "name": "Albert Einstein",
        "birth_data": {
            "year": 1879,
            "month": 3,
            "day": 14,
            "hour": 11,
            "minute": 30,
            "city": "Ulm",
            "lat": 48.4011,
            "lon": 9.9876,
            "timezone": "Europe/Berlin"
        },
        "known_facts": {
            "career": [
                "Theoretical physicist",
                "Developed theory of relativity",
                "Nobel Prize in Physics (1921)",
                "Most influential physicist of 20th century"
            ],
            "personality": [
                "Unconventional thinker",
                "Pacifist and humanitarian",
                "Curious and imaginative from childhood",
                "Struggled with authority and formal education"
            ],
            "life_events": [
                "Late talker as child (parents worried)",
                "Failed entrance exam to Swiss polytechnic (first attempt)",
                "Married twice, divorced once",
                "Left Germany due to Nazi persecution",
                "Settled in USA in 1933"
            ],
            "timing": {
                "annus_mirabilis": "1905 (published 4 groundbreaking papers)",
                "general_relativity": "1915",
                "nobel_prize": "1921",
                "emigration": "1933"
            }
        },
        "test_questions": [
            "What is my intellectual potential?",
            "Will I make groundbreaking discoveries?",
            "What challenges will I face in education?",
            "Will I travel or relocate?",
            "What is my legacy?"
        ]
    }
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_accuracy_score(prediction: str, known_facts: Dict[str, Any], question: str) -> Dict[str, Any]:
    """
    Calculate how well the prediction aligns with known facts.
    
    Returns:
        Dict with score, matches, and analysis
    """
    prediction_lower = prediction.lower()
    
    matches = []
    keywords_found = 0
    total_keywords = 0
    
    # Check for career-related keywords
    if "career" in question.lower():
        career_keywords = [
            ("success", "fame", "recognition", "achievement"),
            ("leadership", "leader", "pioneer", "innovator"),
            ("business", "entrepreneur", "company", "founder"),
            ("technology", "science", "innovation", "invention")
        ]
        
        for fact in known_facts.get("career", []):
            fact_lower = fact.lower()
            for keyword_group in career_keywords:
                for keyword in keyword_group:
                    total_keywords += 1
                    if keyword in fact_lower and keyword in prediction_lower:
                        keywords_found += 1
                        matches.append(f"✓ Predicted '{keyword}' - Actual: {fact}")
    
    # Check for personality traits
    if "personality" in question.lower() or "qualities" in question.lower():
        for trait in known_facts.get("personality", []):
            trait_words = trait.lower().split()
            for word in trait_words:
                if len(word) > 5:  # Only meaningful words
                    total_keywords += 1
                    if word in prediction_lower:
                        keywords_found += 1
                        matches.append(f"✓ Predicted trait found: {word}")
    
    # Calculate score
    score = (keywords_found / total_keywords * 100) if total_keywords > 0 else 0
    
    return {
        "score": round(score, 2),
        "matches": matches,
        "keywords_found": keywords_found,
        "total_keywords": total_keywords,
        "prediction": prediction,
        "question": question
    }


def print_test_result(person_name: str, result: Dict[str, Any], known_facts: Dict[str, Any]):
    """Pretty print test results"""
    print("\n" + "="*80)
    print(f"🔮 TESTING: {person_name}")
    print("="*80)
    
    print(f"\n📋 Question: {result['question']}")
    print(f"\n🤖 AI Prediction:")
    print(f"   {result['prediction']}")
    
    print(f"\n📊 Accuracy Analysis:")
    print(f"   Score: {result['score']}%")
    print(f"   Keywords Found: {result['keywords_found']}/{result['total_keywords']}")
    
    if result['matches']:
        print(f"\n✅ Matches with Known Facts:")
        for match in result['matches'][:5]:  # Show top 5 matches
            print(f"   {match}")
    
    print(f"\n📚 Known Facts (Reference):")
    for category, facts in known_facts.items():
        if category != "timing" and facts:
            print(f"\n   {category.upper()}:")
            for fact in facts[:3]:  # Show first 3 facts per category
                print(f"   • {fact}")


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

async def test_single_person(person_id: str, verbose: bool = True) -> Dict[str, Any]:
    """Test predictions for a single famous person"""
    person = FAMOUS_PEOPLE[person_id]
    birth_data = person["birth_data"]
    
    # Generate vedic chart
    print(f"\n🔄 Generating chart for {person['name']}...")
    chart = generate_vedic_chart(
        name=person["name"],
        year=birth_data["year"],
        month=birth_data["month"],
        day=birth_data["day"],
        hour=birth_data["hour"],
        minute=birth_data["minute"],
        city=birth_data["city"],
        lat=birth_data["lat"],
        lon=birth_data["lon"],
        timezone_str=birth_data["timezone"]
    )
    
    results = []
    total_score = 0
    
    # Test each question
    for question in person["test_questions"]:
        print(f"\n⏳ Testing question: {question}")
        
        # Get AI prediction
        prediction = await get_astrology_prediction(
            chart_data=chart,
            user_query=question,
            api_key=api_key
        )
        
        # Calculate accuracy
        accuracy = calculate_accuracy_score(
            prediction=prediction,
            known_facts=person["known_facts"],
            question=question
        )
        
        results.append(accuracy)
        total_score += accuracy["score"]
        
        if verbose:
            print_test_result(person["name"], accuracy, person["known_facts"])
        
        # Rate limiting
        await asyncio.sleep(2)
    
    average_score = total_score / len(person["test_questions"]) if person["test_questions"] else 0
    
    return {
        "person": person["name"],
        "results": results,
        "average_score": round(average_score, 2),
        "total_questions": len(person["test_questions"])
    }


async def test_all_famous_people(verbose: bool = True) -> Dict[str, Any]:
    """Test predictions for all famous people"""
    print("\n" + "="*80)
    print("🌟 TESTING PREDICTION ACCURACY - FAMOUS PEOPLE")
    print("="*80)
    
    all_results = {}
    overall_scores = []
    
    for person_id in FAMOUS_PEOPLE.keys():
        result = await test_single_person(person_id, verbose=verbose)
        all_results[person_id] = result
        overall_scores.append(result["average_score"])
    
    # Summary
    overall_average = sum(overall_scores) / len(overall_scores) if overall_scores else 0
    
    print("\n" + "="*80)
    print("📊 OVERALL SUMMARY")
    print("="*80)
    
    for person_id, result in all_results.items():
        print(f"\n{result['person']}: {result['average_score']}% average accuracy")
        print(f"   Questions tested: {result['total_questions']}")
    
    print(f"\n🎯 Overall Average Accuracy: {overall_average:.2f}%")
    print("="*80)
    
    return {
        "all_results": all_results,
        "overall_average": round(overall_average, 2),
        "total_people_tested": len(FAMOUS_PEOPLE),
        "total_predictions": sum(r["total_questions"] for r in all_results.values())
    }


async def test_specific_person(person_name: str) -> None:
    """Test a specific famous person by name"""
    person_id = None
    
    # Find person by name
    for pid, data in FAMOUS_PEOPLE.items():
        if person_name.lower() in data["name"].lower():
            person_id = pid
            break
    
    if not person_id:
        print(f"❌ Person '{person_name}' not found in database")
        print(f"Available people: {', '.join([p['name'] for p in FAMOUS_PEOPLE.values()])}")
        return
    
    await test_single_person(person_id, verbose=True)


# ============================================================================
# PYTEST TEST FUNCTIONS
# ============================================================================

async def test_steve_jobs_accuracy():
    """Test prediction accuracy for Steve Jobs"""
    result = await test_single_person("steve_jobs", verbose=False)
    assert result["average_score"] > 0, "Predictions should have some accuracy"
    print(f"\nSteve Jobs Average Accuracy: {result['average_score']}%")


async def test_oprah_winfrey_accuracy():
    """Test prediction accuracy for Oprah Winfrey"""
    result = await test_single_person("oprah_winfrey", verbose=False)
    assert result["average_score"] > 0, "Predictions should have some accuracy"
    print(f"\nOprah Winfrey Average Accuracy: {result['average_score']}%")


async def test_elon_musk_accuracy():
    """Test prediction accuracy for Elon Musk"""
    result = await test_single_person("elon_musk", verbose=False)
    assert result["average_score"] > 0, "Predictions should have some accuracy"
    print(f"\nElon Musk Average Accuracy: {result['average_score']}%")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in .env file")
        sys.exit(1)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        person_name = " ".join(sys.argv[1:])
        asyncio.run(test_specific_person(person_name))
    else:
        # Test all people
        asyncio.run(test_all_famous_people(verbose=True))
