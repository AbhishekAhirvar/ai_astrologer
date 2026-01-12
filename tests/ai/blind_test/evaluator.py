"""
Blind Test Evaluator

Evaluates predictions using semantic similarity and statistical analysis.
No human bias - uses automated matching.
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import re
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def extract_traits_from_text(text: str) -> List[str]:
    """
    Extract key traits/keywords from prediction text
    Simple keyword extraction
    """
    # Common astrological/personality keywords
    trait_keywords = [
        'leadership', 'creative', 'innovative', 'spiritual', 'analytical',
        'emotional', 'practical', 'communication', 'ambitious', 'patient',
        'aggressive', 'peaceful', 'generous', 'disciplined', 'rebellious',
        'traditional', 'unconventional', 'social', 'introvert', 'extrovert',
        'success', 'fame', 'wealth', 'power', 'knowledge', 'wisdom',
        'technology', 'science', 'art', 'politics', 'business', 'education',
        'travel', 'foreign', 'domestic', 'family', 'career', 'health'
    ]
    
    text_lower = text.lower()
    found_traits = []
    
    for trait in trait_keywords:
        if trait in text_lower:
            found_traits.append(trait)
    
    return found_traits


def calculate_trait_overlap(predictions: List[str], known_facts: List[str]) -> float:
    """
    Calculate overlap between predicted traits and known facts
    Returns overlap percentage
    """
    pred_text = " ".join(predictions).lower()
    fact_text = " ".join(known_facts).lower()
    
    pred_traits = set(extract_traits_from_text(pred_text))
    fact_traits = set(extract_traits_from_text(fact_text))
    
    if not fact_traits:
        return 0.0
    
    overlap = len(pred_traits & fact_traits)
    total_fact_traits = len(fact_traits)
    
    return (overlap / total_fact_traits) * 100 if total_fact_traits > 0 else 0.0


def calculate_specificity_score(predictions: List[str]) -> float:
    """
    Calculate how specific vs. generic predictions are
    Higher score = more specific details
    """
    all_text = " ".join(predictions)
    
    # Specific indicators
    specific_markers = [
        r'\d+th house',  # "10th house"
        r'\d+°',  # Degree mentions
        r'[A-Z][a-z]+ in [A-Z][a-z]+',  # "Mars in Aries"
        r'dasha',
        r'transit',
        r'lord of',
        r'ruler of'
    ]
    
    specificity_count = 0
    for marker in specific_markers:
        specificity_count += len(re.findall(marker, all_text))
    
    # Normalize by number of predictions
    return specificity_count / len(predictions) if predictions else 0


def evaluate_consistency(predictions1: List[str], predictions2: List[str]) -> float:
    """
    Evaluate consistency between two sets of predictions for same chart
    Uses simple word overlap
    """
    text1 = " ".join(predictions1).lower()
    text2 = " ".join(predictions2).lower()
    
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    # Remove common words
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'your', 'you', 'this', 'that', 'these', 'those'}
    
    words1 = words1 - common_words
    words2 = words2 - common_words
    
    if not words1 or not words2:
        return 0.0
    
    overlap = len(words1 & words2)
    total = len(words1 | words2)
    
    return (overlap / total) * 100 if total > 0 else 0.0


def calculate_event_accuracy(predictions: List[str], major_events: List[str]) -> Dict[str, Any]:
    """
    Calculate accuracy of predicted years vs actual life events.
    Returns details and a score.
    """
    if not major_events:
        return {"score": 0.0, "hits": [], "misses": []}

    # Extract years from text (1900-2099)
    pred_text = " ".join(predictions)
    pred_years = set(re.findall(r'\b(19|20)\d{2}\b', pred_text))
    
    # Extract years from ground truth
    truth_years = set()
    for event in major_events:
        years = re.findall(r'\b(19|20)\d{2}\b', event)
        truth_years.update(years)
    
    if not truth_years:
        return {"score": 0.0, "hits": [], "misses": []}

    # Calculate hits (exact matches)
    hits = pred_years & truth_years
    misses = truth_years - pred_years
    
    # Simple recall score: What % of major event years did AI mention?
    score = (len(hits) / len(truth_years)) * 100
    
    return {
        "score": round(score, 1),
        "hits": sorted(list(hits)),
        "misses": sorted(list(misses)),
        "total_events": len(truth_years)
    }


def get_ai_semantic_score(prediction_text: str, known_facts: List[str]) -> Tuple[float, str]:
    """
    Use AI to evaluate how well a prediction matches known facts.
    Returns (score 0-100, reasoning)
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return 0.0, "API key missing"

    client = OpenAI(api_key=api_key)
    facts_str = "\n".join([f"- {f}" for f in known_facts])
    
    prompt = f"""
        You are an expert impartial auditor of astrological predictions.
        
        GROUND TRUTH FACTS for the subject:
        {facts_str}
        
        AI PREDICTION to evaluate:
        "{prediction_text}"
        
        TASK:
        Evaluate how accurately the prediction captures the essence of the person's life and traits.
        Ignore astrological jargon (like "Mars in 7th") and focus on the ACTUAL traits and life patterns described.
        
        SCORING CRITERIA:
        0: Complete mismatch or contradictory.
        1-33: Vague or low-level match (barnum effect).
        34-66: Good match - identifies specific correct traits (e.g. leadership for a CEO).
        67-90: High accuracy - matches specific life events or unique personality quirks.
        91-100: Exceptional - captures nuances that are highly specific to this individual.
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "score": <0-100>,
            "reasoning": "<1-2 sentence explanation>"
        }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": [{"text": "You are a precise evaluation bot. Output JSON only.", "type": "text"}]},
                {"role": "user", "content": [{"text": prompt, "type": "text"}]}
            ],
            response_format={"type": "json_object"}
        )
        
        # Access content safely given the 2026 API structure seen in backend/ai.py
        result_text = response.choices[0].message.content
        if isinstance(result_text, list):
            result_text = result_text[0].get('text', '{}')
            
        result = json.loads(result_text)
        return float(result.get("score", 0)), result.get("reasoning", "")
    except Exception as e:
        print(f"⚠️ AI Evaluation Error: {e}")
        return 0.0, f"Error: {str(e)}"


def create_html_output(predictions_data: Dict[str, Any], ground_truth: Dict[str, Any], 
                       output_file: str) -> None:
    """
    Create a beautiful HTML file with human-readable Q&A results.
    Shows real identities, questions, and AI responses.
    
    Args:
        predictions_data: Raw predictions JSON data
        ground_truth: Ground truth mapping with real identities
        output_file: Path to save HTML file
    """
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blind Test Results - Human Readable</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #2d3748;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        .subtitle {{
            text-align: center;
            color: #718096;
            margin-bottom: 40px;
            font-size: 1.1em;
        }}
        .subject {{
            background: #f7fafc;
            border-left: 5px solid #667eea;
            padding: 30px;
            margin-bottom: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .subject-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e2e8f0;
        }}
        .identity {{
            font-size: 1.8em;
            font-weight: bold;
            color: #2d3748;
        }}
        .test-type {{
            padding: 8px 16px;
            background: #667eea;
            color: white;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
        }}
        .test-type.fictional {{
            background: #ed8936;
        }}
        .test-type.duplicate {{
            background: #48bb78;
        }}
        .qa-pair {{
            margin-bottom: 25px;
            padding: 20px;
            background: white;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }}
        .question {{
            font-size: 1.1em;
            font-weight: 600;
            color: #4a5568;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
        }}
        .question::before {{
            content: "Q:";
            background: #667eea;
            color: white;
            padding: 4px 10px;
            border-radius: 5px;
            margin-right: 10px;
            font-weight: bold;
            font-size: 0.9em;
        }}
        .answer {{
            color: #2d3748;
            line-height: 1.8;
            padding-left: 10px;
            border-left: 3px solid #cbd5e0;
            margin-left: 35px;
        }}
        .error {{
            color: #e53e3e;
            font-style: italic;
        }}
        .metadata {{
            background: #edf2f7;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            font-size: 0.95em;
            color: #4a5568;
        }}
        .metadata strong {{
            color: #2d3748;
        }}
        .actual-events {{
            background: #fff5e6;
            border: 2px solid #f59e0b;
            padding: 20px;
            margin-top: 20px;
            border-radius: 8px;
        }}
        .actual-events h3 {{
            color: #d97706;
            margin-bottom: 15px;
            font-size: 1.2em;
            display: flex;
            align-items: center;
        }}
        .actual-events h3::before {{
            content: "📅";
            margin-right: 8px;
        }}
        .actual-events ul {{
            list-style: none;
            padding: 0;
        }}
        .actual-events li {{
            padding: 8px 0;
            color: #78350f;
            font-weight: 500;
            border-bottom: 1px solid #fde68a;
        }}
        .actual-events li:last-child {{
            border-bottom: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔮 Blind Test Results</h1>
        <p class="subtitle">Human-Readable Format with Real Identities</p>
        
        <div class="metadata">
            <strong>Test Run:</strong> {test_timestamp}<br>
            <strong>Total Subjects:</strong> {total_subjects}<br>
            <strong>Total Predictions:</strong> {total_predictions}
        </div>
"""
    
    # Add metadata
    test_meta = predictions_data.get("test_metadata", {})
    html_content = html_content.format(
        test_timestamp=test_meta.get("run_at", "Unknown"),
        total_subjects=test_meta.get("total_subjects", 0),
        total_predictions=test_meta.get("total_predictions", 0)
    )
    
    # Add each subject's results
    for pred in predictions_data.get("predictions", []):
        subject_id = pred.get("subject_id", "Unknown")
        test_type = pred.get("test_type", "unknown")
        
        # Get real identity
        gt = ground_truth.get(subject_id, {})
        real_identity = gt.get("identity", "Unknown")
        
        # Determine test type class
        type_class = ""
        if test_type == "fictional_control":
            type_class = " fictional"
        elif test_type == "duplicate_control":
            type_class = " duplicate"
        
        html_content += f"""
        <div class="subject">
            <div class="subject-header">
                <div class="identity">{real_identity}</div>
                <div class="test-type{type_class}">{test_type.replace('_', ' ').title()}</div>
            </div>
"""
        
        # Add Q&A pairs
        for qa in pred.get("predictions", []):
            question = qa.get("question", "Unknown question")
            answer = qa.get("prediction", "No response")
            
            # Check for errors
            answer_class = ' class="error"' if answer.startswith("ERROR:") else ""
            
            html_content += f"""
            <div class="qa-pair">
                <div class="question">{question}</div>
                <div class="answer"{answer_class}>{answer}</div>
            </div>
"""
        
        # Add actual major events section if available (for famous people)
        major_events = gt.get("known_facts", {}).get("major_events", [])
        if major_events:
            html_content += """
            <div class="actual-events">
                <h3>Actual Major Life Events</h3>
                <ul>
"""
            for event in major_events:
                html_content += f"                    <li>{event}</li>\n"
            
            html_content += """                </ul>
            </div>
"""
        
        html_content += """
        </div>
"""
    
    # Close HTML
    html_content += """
    </div>
</body>
</html>
"""
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ Human-readable HTML output saved: {output_file}")


def evaluate_blind_test_results(predictions_file: str, ground_truth_file: str) -> Dict[str, Any]:
    """
    Evaluate blind test results
    
    Args:
        predictions_file: Path to predictions JSON
        ground_truth_file: Path to ground truth mapping
    
    Returns:
        Evaluation results with scores and analysis
    """
    print("\n" + "="*80)
    print("📊 BLIND TEST EVALUATION")
    print("="*80)
    
    # Load data
    with open(predictions_file, 'r') as f:
        predictions_data = json.load(f)
    
    with open(ground_truth_file, 'r') as f:
        ground_truth = json.load(f)
    
    results = {
        "evaluation_summary": {},
        "by_type": {
            "famous_blind": [],
            "fictional_control": [],
            "duplicate_control": []
        },
        "statistical_tests": {}
    }
    
    # Group predictions by type
    predictions_by_type = defaultdict(list)
    predictions_by_id = {}
    
    for pred in predictions_data["predictions"]:
        subject_id = pred["subject_id"]
        test_type = pred["test_type"]
        
        pred_texts = [p["prediction"] for p in pred["predictions"]]
        predictions_by_type[test_type].append({
            "id": subject_id,
            "predictions": pred_texts,
            "ground_truth": ground_truth.get(subject_id, {})
        })
        predictions_by_id[subject_id] = pred_texts
    
    # Analyze famous people (blind)
    print("\n📌 Analyzing Famous People (Blind Test)...")
    famous_scores = []
    
    for item in predictions_by_type["famous_blind"]:
        identity = item["ground_truth"].get("identity", "Unknown")
        subject_id = item["id"]
        known_facts_dict = item["ground_truth"].get("known_facts", {})
        known_facts = []
        
        for category, facts in known_facts_dict.items():
            known_facts.extend(facts)
        
        # Calculate scores
        trait_overlap = calculate_trait_overlap(item["predictions"], known_facts)
        specificity = calculate_specificity_score(item["predictions"])
        
        # Calculate Event Accuracy (New)
        major_events = item["ground_truth"].get("known_facts", {}).get("major_events", [])
        event_eval = calculate_event_accuracy(item["predictions"], major_events)
        
        # Semantic Score (Phase 2 Upgrade)
        all_pred_text = " ".join(item["predictions"])
        all_known_facts = []
        for cat, facts in known_facts_dict.items():
            all_known_facts.extend(facts)
            
        semantic_score, reasoning = get_ai_semantic_score(all_pred_text, all_known_facts) if all_known_facts else (0.0, "No facts")
        
        famous_scores.append({
            "id": subject_id,
            "identity": identity,
            "trait_overlap": trait_overlap,
            "semantic_score": semantic_score,
            "semantic_reasoning": reasoning,
            "specificity": specificity,
            "event_accuracy": event_eval,
            "predictions": item["predictions"]
        })
        
        print(f"\n   {subject_id} → Real Identity: {identity}")
        print(f"      Trait overlap: {trait_overlap:.1f}%")
        print(f"      Semantic Score: {semantic_score:.1f}/100")
        print(f"      AI Reasoning: {reasoning}")
        print(f"      Event Accuracy: {event_eval['score']}% ({len(event_eval['hits'])}/{event_eval['total_events']} years)")
        print(f"      Specificity: {specificity:.2f}")

    
    results["by_type"]["famous_blind"] = famous_scores
    
    # Analyze fictional controls
    print("\n📌 Analyzing Fictional Controls...")
    fictional_scores = []
    
    for item in predictions_by_type["fictional_control"]:
        specificity = calculate_specificity_score(item["predictions"])
        
        fictional_scores.append({
            "id": item["id"],
            "specificity": specificity
        })
        
        print(f"   {item['id']}: Specificity = {specificity:.2f}")
    
    results["by_type"]["fictional_control"] = fictional_scores
    
    # Analyze duplicate controls (consistency check)
    print("\n📌 Analyzing Duplicate Controls (Consistency Check)...")
    duplicate_scores = []
    
    # Find duplicate pairs
    duplicate_pairs = []
    for pred in predictions_data["predictions"]:
        if pred["test_type"] == "duplicate_control":
            original_id = pred.get("duplicate_of")
            if original_id and original_id in predictions_by_id:
                duplicate_pairs.append({
                    "original_id": original_id,
                    "duplicate_id": pred["subject_id"],
                    "original_preds": predictions_by_id[original_id],
                    "duplicate_preds": predictions_by_id[pred["subject_id"]]
                })
    
    for pair in duplicate_pairs:
        consistency = evaluate_consistency(pair["original_preds"], pair["duplicate_preds"])
        
        duplicate_scores.append({
            "original_id": pair["original_id"],
            "duplicate_id": pair["duplicate_id"],
            "consistency": consistency
        })
        
        print(f"   {pair['original_id']} vs {pair['duplicate_id']}: {consistency:.1f}% consistent")
    
    results["by_type"]["duplicate_control"] = duplicate_scores
    
    # Statistical summary
    print("\n" + "="*80)
    print("📈 STATISTICAL SUMMARY")
    print("="*80)
    
    # Average scores
    # Average scores
    avg_famous_overlap = np.mean([s["trait_overlap"] for s in famous_scores]) if famous_scores else 0
    avg_famous_specificity = np.mean([s["specificity"] for s in famous_scores]) if famous_scores else 0
    avg_event_accuracy = np.mean([s["event_accuracy"]["score"] for s in famous_scores]) if famous_scores else 0
    avg_fictional_specificity = np.mean([s["specificity"] for s in fictional_scores]) if fictional_scores else 0
    avg_consistency = np.mean([s["consistency"] for s in duplicate_scores]) if duplicate_scores else 0
    
    results["evaluation_summary"] = {
        "famous_people": {
            "count": len(famous_scores),
            "avg_trait_overlap": round(avg_famous_overlap, 2),
            "avg_specificity": round(avg_famous_specificity, 2)
        },
        "fictional_controls": {
            "count": len(fictional_scores),
            "avg_specificity": round(avg_fictional_specificity, 2)
        },
        "duplicate_controls": {
            "count": len(duplicate_scores),
            "avg_consistency": round(avg_consistency, 2)
        }
    }
    
    print(f"\n✅ Famous People (Blind):")
    print(f"   Count: {len(famous_scores)}")
    print(f"   Avg trait overlap: {avg_famous_overlap:.2f}%")
    print(f"   Avg event accuracy: {avg_event_accuracy:.2f}%")
    print(f"   Avg specificity: {avg_famous_specificity:.2f}")
    
    print(f"\n✅ Fictional Controls:")
    print(f"   Count: {len(fictional_scores)}")
    print(f"   Avg specificity: {avg_fictional_specificity:.2f}")
    
    print(f"\n✅ Duplicate Controls (Consistency):")
    print(f"   Count: {len(duplicate_scores)}")
    print(f"   Avg consistency: {avg_consistency:.2f}%")
    
    # Interpretation
    print("\n" + "="*80)
    print("🎯 INTERPRETATION")
    print("="*80)
    
    if avg_famous_specificity > avg_fictional_specificity * 1.2:
        print("\n✅ POSITIVE: Famous people got MORE specific predictions than fictional")
        print("   This suggests AI might be using chart data effectively")
    else:
        print("\n⚠️  CONCERN: Fictional charts got similar specificity to famous people")
        print("   Predictions might be too generic")
    
    if avg_consistency > 70:
        print("\n✅ POSITIVE: High consistency for duplicate charts")
        print("   AI is using chart data consistently")
    elif avg_consistency > 50:
        print("\n⚠️  MODERATE: Moderate consistency for duplicates")
        print("   Some variability in predictions for same chart")
    else:
        print("\n❌ CONCERN: Low consistency for duplicate charts")
        print("   Predictions vary significantly for same chart")
    
    if avg_famous_overlap > 30:
        print(f"\n✅ POSITIVE: {avg_famous_overlap:.0f}% trait overlap with known facts")
        print("   Predictions align reasonably with reality")
    elif avg_famous_overlap > 15:
        print(f"\n⚠️  MODERATE: {avg_famous_overlap:.0f}% trait overlap")
        print("   Some alignment but room for improvement")
    else:
        print(f"\n❌ CONCERN: Only {avg_famous_overlap:.0f}% trait overlap")
        print("   Predictions don't match known personalities well")
    
    print("\n" + "="*80)
    
    # Generate human-readable HTML output
    # Generate human-readable HTML output
    # Use same basename as JSON to prevent overwriting old reports
    html_file = Path(predictions_file).with_suffix('.html')
    if html_file.name.startswith("predictions_"):
        html_file = html_file.with_name(html_file.name.replace("predictions_", "report_"))
        
    create_html_output(predictions_data, ground_truth, str(html_file))
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python evaluator.py <predictions_file> <ground_truth_file>")
        print("\nExample:")
        print("  python evaluator.py results/predictions_20260109.json data/ground_truth_mapping.json")
        sys.exit(1)
    
    predictions_file = sys.argv[1]
    ground_truth_file = sys.argv[2]
    
    results = evaluate_blind_test_results(predictions_file, ground_truth_file)
    
    # Save evaluation results
    output_file = Path(predictions_file).parent / "evaluation_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Evaluation saved: {output_file}\n")
