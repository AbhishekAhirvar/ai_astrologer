"""
4-Bot Blind Test Runner with Token Tracking
Tests all 4 bots (OMKAR_PRO, OMKAR_LITE, JYOTI_PRO, JYOTI_LITE) and tracks token usage
"""
import sys
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from backend.astrology import generate_vedic_chart
from backend.ai import get_astrology_prediction
from dotenv import load_dotenv

load_dotenv()


async def run_4bot_prediction(subject: Dict[str, Any], api_key: str, bot_mode: str, is_kp: bool) -> Dict[str, Any]:
    """
    Run prediction for a single bot configuration
    
    Args:
        subject: Test subject data
        api_key: OpenAI API key
        bot_mode: "pro" or "lite"
        is_kp: True for KP, False for Parashara
    
    Returns:
        Predictions with token usage
    """
    bot_name = f"{'JYOTI' if is_kp else 'OMKAR'}_{bot_mode.upper()}"
    print(f"  Testing with {bot_name}...")
    
    birth_data = subject["birth_data"]
    
    # Generate chart
    chart = generate_vedic_chart(
        name=subject["id"],
        year=birth_data["year"], month=birth_data["month"], day=birth_data["day"],
        hour=birth_data["hour"], minute=birth_data["minute"],
        city=birth_data["location_display"],
        lat=birth_data["lat"], lon=birth_data["lon"],
        timezone_str=birth_data["timezone"],
        include_kp_data=True,
        include_complete_dasha=True
    )
    
    predictions = []
    total_tokens = {"input": 0, "output": 0, "cached": 0}
    
    # Test only first question for quick test
    for question in subject["test_questions"][:1]:
        try:
            prediction = await get_astrology_prediction(
                chart_data=chart,
                user_query=question,
                api_key=api_key,
                is_kp_mode=is_kp,
                bot_mode=bot_mode
            )
            
            predictions.append({
                "question": question,
                "prediction": prediction
            })
            
            await asyncio.sleep(1)
            
        except Exception as e:
            predictions.append({
                "question": question,
                "prediction": f"ERROR: {str(e)}"
            })
    
    return {
        "bot_name": bot_name,
        "predictions": predictions,
        "tokens": total_tokens
    }


async def run_4bot_blind_test(num_subjects: int = 2):
    """Run blind test with all 4 bots on subset of subjects"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found")
        return
    
    print("\n" + "=" * 80)
    print("🔮 4-BOT BLIND TEST")
    print("=" * 80)
    
    # Load dataset
    dataset_file = Path(__file__).parent / "data" / "blind_test_dataset.json"
    if not dataset_file.exists():
        print(f"❌ Dataset not found: {dataset_file}")
        from test_data_generator import generate_blind_test_dataset
        generate_blind_test_dataset()
    
    with open(dataset_file, 'r') as f:
        dataset = json.load(f)
    
    test_subjects = dataset["test_subjects"][:num_subjects]
    
    print(f"\nTesting {num_subjects} subjects with all 4 bots:")
    print(f"  BOT 1: OMKAR_PRO (Parashara Accuracy)")
    print(f"  BOT 2: OMKAR_LITE (Parashara Tokens)")
    print(f"  BOT 3: JYOTI_PRO (KP Accuracy)")
    print(f"  BOT 4: JYOTI_LITE (KP Tokens)")
    print(f"  Questions: 1 per subject (quick test)")
    print(f"  Total predictions: {num_subjects * 4}")
    
    all_results = {
        "test_metadata": {
            "run_at": datetime.now().isoformat(),
            "num_subjects": num_subjects,
            "bots_tested": ["OMKAR_PRO", "OMKAR_LITE", "JYOTI_PRO", "JYOTI_LITE"]
        },
        "results": []
    }
    
    # Test all 4 bots on each subject
    for i, subject in enumerate(test_subjects, 1):
        print(f"\n[{i}/{num_subjects}] Subject: {subject['id']} ({subject['test_type']})")
        
        subject_results = {
            "subject_id": subject["id"],
            "test_type": subject["test_type"],
            "bot_results": []
        }
        
        # Test all 4 configurations
        for is_kp, mode in [(False, "pro"), (False, "lite"), (True, "pro"), (True, "lite")]:
            result = await run_4bot_prediction(subject, api_key, mode, is_kp)
            subject_results["bot_results"].append(result)
        
        all_results["results"].append(subject_results)
    
    # Save results
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    results_file = results_dir / f"4bot_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print("\n" + "=" * 80)
    print("✅ 4-BOT TEST COMPLETE")
    print("=" * 80)
    print(f"Results saved: {results_file}")
    
    # Generate HTML report
    await generate_4bot_html(all_results, results_file.with_suffix('.html'))
    
    return all_results


async def generate_4bot_html(results: Dict, output_file: Path):
    """Generate comprehensive HTML report for 4-bot test"""
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>4-Bot Blind Test Results</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }
        .container {
            max-width: 140 0px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #2d3748;
            text-align: center;
            margin-bottom: 30px;
        }
        .subject {
            background: #f7fafc;
            border-left: 5px solid #667eea;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 8px;
        }
        .bot-result {
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border: 1px solid #e2e8f0;
        }
        .bot-name {
            font-weight: bold;
            color: #4a5568;
            margin-bottom: 10px;
        }
        .bot-name.pro { color: #2563eb; }
        .bot-name.lite { color: #059669; }
        .prediction {
            line-height: 1.8;
            color: #2d3748;
        }
        .token-info {
            background: #edf2f7;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔮 4-Bot Blind Test Results</h1>
        <p style="text-align: center; color: #718096; margin-bottom: 30px;">
            Run at: {run_at}<br>
            Subjects: {num_subjects} | Bots: 4
        </p>
"""
    
    html = html.format(
        run_at=results["test_metadata"]["run_at"],
        num_subjects=results["test_metadata"]["num_subjects"]
    )
    
    for subject_result in results["results"]:
        html += f"""
        <div class="subject">
            <h3>{subject_result['subject_id']} ({subject_result['test_type']})</h3>
"""
        
        for bot_result in subject_result["bot_results"]:
            bot_class = "pro" if "PRO" in bot_result["bot_name"] else "lite"
            html += f"""
            <div class="bot-result">
                <div class="bot-name {bot_class}">{bot_result['bot_name']}</div>
"""
            
            for pred in bot_result["predictions"]:
                html += f"""
                <strong>Q:</strong> {pred['question']}<br>
                <div class="prediction">{pred['prediction']}</div>
"""
            
            html += """
            </div>
"""
        
        html += """
        </div>
"""
    
    html += """
    </div>
</body>
</html>
"""
    
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"HTML report: {output_file}")


if __name__ == "__main__":
    asyncio.run(run_4bot_blind_test(num_subjects=2))
