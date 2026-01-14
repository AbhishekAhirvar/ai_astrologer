"""
Blind Prediction Runner

Runs astrological predictions without revealing subject identity to AI.
Uses anonymous IDs to prevent AI from using training data about famous people.
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import pytz
import swisseph as swe

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from backend.astrology import generate_vedic_chart, calculate_julian_day
from backend.ai import get_astrology_prediction
from backend.shadbala import calculate_shadbala_for_chart
from backend.dasha_system import VimshottariDashaSystem
from backend.kp_calculations import generate_kp_data
from backend.schemas import KPData, ShadbalaData
from dotenv import load_dotenv
from evaluator import evaluate_blind_test_results

load_dotenv()


# Custom system instruction for blind test to ensure historical scan
BLIND_TEST_SYSTEM_INSTRUCTION = (
    "ROLE: You are Omkar, a legendary Vedic Astrologer. "
    "TEST FOCUS: You are currently performing a blind test. You have been provided with the COMPLETE planetary chart and Dasha (timing) data for a subject. "
    "CRITICAL FOR TIMELINE QUESTIONS: If asked about 'entire life journey', 'major years', or 'past events', you MUST: "
    "(1) Calculate the subject's birth year from the chart metadata, "
    "(2) Map each Mahadasha/Antardasha period to SPECIFIC CALENDAR YEARS (e.g., 1976, 1985, 2001), "
    "(3) Identify breakthrough years by analyzing Dasha transitions and planetary periods, "
    "(4) Output EXACT YEARS with events, NOT vague 'late 20s' or 'midlife'. "
    "FORMAT REQUIRED: '1985: Major career shift (Sun Mahadasha began, 10th house activation)' "
    "Do NOT ask for birth details; you already have the chart. "
    "IF VALID: Answer directly with wisdom. Mention 1-2 key planets maximum ONLY if critical. "
    "TONE: Sage-like, sacred, human, direct. LENGTH: 100-150 words."
)


async def run_blind_prediction(subject: Dict[str, Any], api_key: str, is_kp_mode: bool = True, bot_mode: str = "pro", num_questions: int = None, target_question_idx: int = None) -> Dict[str, Any]:
    """
    Run predictions for a single subject WITHOUT revealing their identity
    
    Args:
        subject: Blind test subject data
        api_key: OpenAI API key
        is_kp_mode: True for KP system, False for Parashara (default: True)
        bot_mode: "pro" for accuracy, "lite" for tokens (default: "pro")
        num_questions: Max number of questions to ask
        target_question_idx: If provided, only ask this specific question (0-indexed)
    
    Returns:
        Predictions with anonymous ID
    """
    bot_name = f"{'JYOTI' if is_kp_mode else 'OMKAR'}_{bot_mode.upper()}"
    print(f"\n🔄 Testing {subject['id']} with {bot_name} ({subject['test_type']})...")
    
    birth_data = subject["birth_data"]
    
    # Generate chart with ANONYMOUS name
    # AI only sees the anonymous ID, not real name
    chart = generate_vedic_chart(
        name=subject["id"],  # Anonymous ID instead of real name
        year=birth_data["year"],
        month=birth_data["month"],
        day=birth_data["day"],
        hour=birth_data["hour"],
        minute=birth_data["minute"],
        city=birth_data["location_display"],  # Anonymous coordinates
        lat=birth_data["lat"],
        lon=birth_data["lon"],
        timezone_str=birth_data["timezone"]
    )
    
    # 2. Enrich chart data (Architecture change: calculations are now separate)
    # Calculate Shadbala
    chart.shadbala = ShadbalaData(total_shadbala=calculate_shadbala_for_chart(chart))
    
    # Calculate Complete Dasha
    dasha_sys = VimshottariDashaSystem()
    now_utc = datetime.now(pytz.UTC)
    cur_jd = calculate_julian_day(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, "UTC")
    birth_jd = calculate_julian_day(birth_data["year"], birth_data["month"], birth_data["day"], 
                                   birth_data["hour"], birth_data["minute"], birth_data["timezone"])
    moon_pos = chart.planets['moon'].abs_pos
    chart.complete_dasha = dasha_sys.calculate_complete_dasha(moon_pos, birth_jd, cur_jd)
    
    # Calculate KP Data if needed
    if is_kp_mode:
        # Extract planetary positions for KP (needs 'longitude' key)
        pp_positions = {p: {"longitude": pos.abs_pos} for p, pos in chart.planets.items()}
        
        # Add Ascendant to positions for KP if present
        if hasattr(chart, 'metadata') and hasattr(chart, 'planets'):
            # In our current schema, ascendant might be a float on chart or in planets
            if 'ascendant' not in pp_positions and hasattr(chart, 'ascendant') and chart.ascendant:
                pp_positions['ascendant'] = {"longitude": chart.ascendant}
        
        chart.kp_data = KPData(**generate_kp_data(
            jd=birth_jd,
            lat=birth_data["lat"],
            lon=birth_data["lon"],
            planetary_positions=pp_positions,
            moon_lon=moon_pos
        ))
    predictions = []
    
    # Ask generic questions (limit if requested)
    test_questions = subject["test_questions"]
    
    # If target_question_idx is provided, we only want THAT one
    if target_question_idx is not None:
        if target_question_idx < len(test_questions):
            test_questions = [test_questions[target_question_idx]]
        else:
            test_questions = []
    elif num_questions:
        test_questions = test_questions[:num_questions]
        
    for i, question in enumerate(test_questions, 1):
        print(f"   Question {i}/{len(subject['test_questions'])}: {question[:50]}...")
        
        try:
            # Use NEW 4-bot system (no custom system instruction to preserve bot behavior)
            prediction = await get_astrology_prediction(
                chart_data=chart,
                user_query=question,
                api_key=api_key,
                is_kp_mode=is_kp_mode,
                bot_mode=bot_mode  # NEW: Select bot
            )
            
            predictions.append({
                "question": question,
                "prediction": prediction,
                "timestamp": datetime.now().isoformat()
            })
            
            # Rate limiting
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
            predictions.append({
                "question": question,
                "prediction": f"ERROR: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
    
    return {
        "subject_id": subject["id"],
        "test_type": subject["test_type"],
        "bot_name": bot_name,  # NEW: Track which bot was used
        "predictions": predictions,
        "birth_data_used": {
            "date": f"{birth_data['year']}-{birth_data['month']}-{birth_data['day']}",
            "time": f"{birth_data['hour']}:{birth_data['minute']}",
            "location": birth_data["location_display"]
        }
    }


async def run_all_blind_predictions(dataset_file: str, api_key: str, 
                                    output_dir: str = None) -> Dict[str, Any]:
    """
    Run predictions for all subjects in blind test dataset
    
    Args:
        dataset_file: Path to blind test dataset JSON
        api_key: OpenAI API key
        output_dir: Directory to save results (default: script_dir/results)
    
    Returns:
        All predictions
    """
    # Use script directory if no output_dir specified
    if output_dir is None:
        script_dir = Path(__file__).parent
        output_dir = script_dir / "results"
    else:
        output_dir = Path(output_dir)
    
    print("\n" + "="*80)
    print("🔮 BLIND PREDICTION TEST - MVP")
    print("="*80)
    print("\n⚠️  CRITICAL: AI receives ANONYMOUS IDs only, no real names!")
    print("   This prevents AI from using training data about famous people.\n")
    
    # Load dataset
    with open(dataset_file, 'r') as f:
        dataset = json.load(f)
    
    total_subjects = len(dataset["test_subjects"])
    total_predictions = dataset["metadata"]["total_predictions_needed"]
    
    print(f"📊 Test Overview:")
    print(f"   Subjects: {total_subjects}")
    print(f"   Questions per subject: {dataset['metadata']['questions_per_subject']}")
    print(f"   Total predictions: {total_predictions}")
    print(f"   Famous (blind): {dataset['metadata']['famous_people']}")
    print(f"   Fictional controls: {dataset['metadata']['fictional_controls']}")
    print(f"   Duplicate controls: {dataset['metadata']['duplicate_controls']}")
    
    # Confirm
    print(f"\n⚠️  This will make {total_predictions} API calls")
    print(f"   Estimated cost: ~${total_predictions * 0.002:.2f} (with GPT-5-nano)")
    print(f"   Estimated time: ~{total_predictions * 3 / 60:.1f} minutes")
    
    # Run predictions
    all_results = {
        "test_metadata": {
            "run_at": datetime.now().isoformat(),
            "total_subjects": total_subjects,
            "total_predictions": total_predictions,
            "dataset_file": str(dataset_file)
        },
        "predictions": []
    }
    
    for i, subject in enumerate(dataset["test_subjects"], 1):
        print(f"\n[{i}/{total_subjects}] Processing {subject['id']}...")
        
        result = await run_blind_prediction(subject, api_key)
        all_results["predictions"].append(result)
    
    # Save results
    output_dir.mkdir(parents=True, exist_ok=True)
    results_file = output_dir / f"predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print("\n" + "="*80)
    print("✅ BLIND PREDICTIONS COMPLETE")
    print("="*80)
    print(f"\n📁 Results saved: {results_file}")
    print(f"   Total predictions: {len(all_results['predictions'])} subjects")
    
    # Run evaluation automatically
    ground_truth_file = Path(__file__).parent / "data" / "ground_truth_mapping.json"
    if ground_truth_file.exists():
        print("\n📊 Automatically running evaluation...")
        evaluate_blind_test_results(str(results_file), str(ground_truth_file))
    
    return all_results


async def quick_blind_test(api_key: str, num_subjects: int = 2, is_kp_mode: bool = True, bot_mode: str = "pro", num_questions: int = None, target_question_idx: int = None):
    """
    Quick test with just a few subjects to verify system works
    
    Args:
        api_key: OpenAI API key
        num_subjects: Number of subjects to test (default: 2)
        is_kp_mode: True for KP, False for Parashara (default: True)
        bot_mode: "pro" for accuracy, "lite" for tokens (default: "pro")
    """
    bot_name = f"{'JYOTI' if is_kp_mode else 'OMKAR'}_{bot_mode.upper()}"
    print("\n" + "="*80)
    print(f"🚀 QUICK BLIND TEST with {bot_name}")
    print("="*80)
    
    # Load dataset
    dataset_file = Path(__file__).parent / "data" / "blind_test_dataset.json"
    
    if not dataset_file.exists():
        print(f"\n❌ Dataset not found: {dataset_file}")
        print("   Run test_data_generator.py first!")
        return
    
    # test_subjects = dataset["test_subjects"][:num_subjects]
    test_subjects = [
        {
            "id": "Subject-1LV76F",  # Albert Einstein
            "test_type": "famous_blind",
            "birth_data": {
                "year": 1879, "month": 3, "day": 14,
                "hour": 11, "minute": 30,
                "location_display": "Ulm, Germany",
                "lat": 48.4011, "lon": 9.9876,
                "timezone": "Europe/Berlin"
            },
            "test_questions": [
                "What is my primary life purpose?",
                "What are my natural talents and abilities?",
                "Will I achieve recognition in my field?",
                "Looking at my entire life journey from birth to present, identify all major years where my path shifted significantly or I had massive breakthroughs. For each, explain the astrological reason and the theme of the event.",
                "What major challenges will I face in life?",
                "What is my leadership potential?"
            ]
        }
    ]
    
    print(f"\n📊 Testing {num_subjects} subjects with {bot_name}:")
    for subject in test_subjects:
        print(f"   - {subject['id']} ({subject['test_type']})")
    
    results = []
    for subject in test_subjects:
        result = await run_blind_prediction(subject, api_key, is_kp_mode, bot_mode, num_questions=num_questions, target_question_idx=target_question_idx)
        results.append(result)
    
    # Save results
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    results_file = results_dir / f"predictions_{bot_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    save_data = {
        "test_metadata": {
            "run_at": datetime.now().isoformat(),
            "test_type": "quick_test",
            "num_subjects": num_subjects,
            "bot_name": bot_name,
            "is_kp_mode": is_kp_mode,
            "bot_mode": bot_mode
        },
        "predictions": results
    }
    
    with open(results_file, 'w') as f:
        json.dump(save_data, f, indent=2)
    
    print("\n✅ Quick test complete!")
    print(f"   Bot: {bot_name}")
    print(f"   Tested: {len(results)} subjects")
    print(f"   Results saved: {results_file}")
    
    # Run evaluation automatically for quick test too
    ground_truth_file = Path(__file__).parent / "data" / "ground_truth_mapping.json"
    if ground_truth_file.exists():
        print("\n📊 Automatically running evaluation...")
        evaluate_blind_test_results(str(results_file), str(ground_truth_file))
    
    return results

async def run_comprehensive_test(api_key: str):
    """
    Run comprehensive blind test on Michael Peterson with all 4 bots.
    Captures full payload and token usage.
    """
    print("\n" + "="*80)
    print("🚀 COMPREHENSIVE BLIND TEST (Michael Peterson - AA Rated)")
    print("="*80)
    
    # Custom Test for Abhishek
    subject = {
        "id": "Subject-Abhishek-1992", 
        "test_type": "user_blind_test",
        "birth_data": {
            "year": 1992, "month": 1, "day": 2,
            "hour": 6, "minute": 40,
            "location_display": "Delhi, India",
            "lat": 28.6139, "lon": 77.2090,
            "timezone": "Asia/Kolkata"
        },
        "test_questions": [
            "What is my life purpose?",
            "What are my key personality traits?",
            "Which career is most suitable for me?",
            "What does my upcoming life look like?"
        ]
    }
    
    # 4 Configurations
    configs = [
        {"name": "OMKAR_PRO", "is_kp": False, "mode": "pro"},
        {"name": "OMKAR_LITE", "is_kp": False, "mode": "lite"},
        {"name": "JYOTI_PRO", "is_kp": True, "mode": "pro"},
        {"name": "JYOTI_LITE", "is_kp": True, "mode": "lite"},
    ]
    
    results = []
    
    # Generate common chart once (optimization)
    print(f"\n📊 Subject: {subject['id']} (Born {subject['birth_data']['year']})")
    
    for cfg in configs:
        print(f"\n🤖 Running Bot: {cfg['name']}...")
        
        # We need to manually call get_astrology_prediction here to pass return_debug_info
        # OR we modify run_blind_prediction. 
        # Modifying run_blind_prediction is cleaner but requires signature change.
        # Let's just do it inline here to be safe and explicit.
        
        # 1. Generate Chart (Anonymous)
        bd = subject["birth_data"]
        chart = generate_vedic_chart(subject["id"], bd["year"], bd["month"], bd["day"], bd["hour"], bd["minute"], bd["location_display"], bd["lat"], bd["lon"], bd["timezone"])
        chart.shadbala = ShadbalaData(total_shadbala=calculate_shadbala_for_chart(chart))
        
        dasha_sys = VimshottariDashaSystem()
        from datetime import datetime
        now_utc = datetime.now(pytz.UTC)
        cur_jd = calculate_julian_day(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, "UTC")
        birth_jd = calculate_julian_day(bd["year"], bd["month"], bd["day"], bd["hour"], bd["minute"], bd["timezone"])
        chart.complete_dasha = dasha_sys.calculate_complete_dasha(chart.planets['moon'].abs_pos, birth_jd, cur_jd)
        
        if cfg["is_kp"]:
             pp_positions = {p: {"longitude": pos.abs_pos} for p, pos in chart.planets.items()}
             if hasattr(chart, 'ascendant') and chart.ascendant:
                 pp_positions['ascendant'] = {"longitude": chart.ascendant}
             chart.kp_data = KPData(**generate_kp_data(birth_jd, bd["lat"], bd["lon"], pp_positions, chart.planets['moon'].abs_pos))
             
        bot_predictions = []
        for q in subject["test_questions"]:
            print(f"   - asking: {q[:30]}...")
            response = await get_astrology_prediction(
                chart_data=chart,
                user_query=q,
                api_key=api_key,
                is_kp_mode=cfg["is_kp"],
                bot_mode=cfg["mode"],
                return_debug_info=True # CAPTURE PAYLOAD
            )
            
            # Handle potential error if response is string (legacy fallback)
            if isinstance(response, str):
                bot_predictions.append({"q": q, "a": response, "usage": {}, "payload": "N/A"})
            else:
               bot_predictions.append({
                   "q": q, 
                   "a": response["prediction"], 
                   "usage": response["usage"], 
                   "payload": response["payload"]
               })
            await asyncio.sleep(1)

        results.append({
            "bot": cfg["name"],
            "preds": bot_predictions
        })

    # Save detailed comprehensive results
    out_file = Path(__file__).parent / "results" / f"comprehensive_MP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_file, 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"\n✅ Comprehensive Test Complete!")
    print(f"📁 Saved raw JSON: {out_file}")
    
    # Call report generator (we will create this next)
    # from generate_detailed_report import generate_html_report
    # generate_html_report(out_file)
    print("ℹ️  Run generate_detailed_report.py to see HTML.")
    return out_file


if __name__ == "__main__":
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in .env")
        sys.exit(1)
    
    # Check if dataset exists
    dataset_file = Path(__file__).parent / "data" / "blind_test_dataset.json"
    
    if not dataset_file.exists():
        print("❌ Dataset not found! Generating now...\n")
        from test_data_generator import generate_blind_test_dataset
        generate_blind_test_dataset()
        print("\n✅ Dataset generated. Run this script again to execute predictions.\n")
        sys.exit(0)
    
    # Parse command line args
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        # Quick test mode
        asyncio.run(quick_blind_test(api_key, num_subjects=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "comprehensive":
        # Comprehensive test mode
        asyncio.run(run_comprehensive_test(api_key))
    else:
        # Full test mode
        print("\n⚠️  About to run FULL blind test (all subjects)")
        response = input("   Continue? (yes/no): ")
        
        if response.lower() in ['yes', 'y']:
            asyncio.run(run_all_blind_predictions(str(dataset_file), api_key))
        else:
            print("\n❌ Cancelled. Use 'python blind_predictor.py quick' for quick test.")
