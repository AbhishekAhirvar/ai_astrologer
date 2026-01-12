"""
Combined Blind Test Report Generator

Merges multiple bot prediction JSONs into a single human-readable HTML report
with side-by-side comparison and evaluation metrics.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from tests.ai.blind_test.evaluator import (
    calculate_trait_overlap, 
    calculate_specificity_score, 
    evaluate_consistency,
    get_ai_semantic_score
)


def load_prediction_file(filepath: Path) -> Dict[str, Any]:
    """Load a prediction JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def generate_combined_html(prediction_files: List[Path], output_path: Path, ground_truth_path: Path = None):
    """
    Generate a single HTML report combining all bot predictions.
    """
    # Load all predictions
    all_predictions = []
    for filepath in prediction_files:
        data = load_prediction_file(filepath)
        all_predictions.append(data)
    
    # Load ground truth if available
    ground_truth = {}
    if ground_truth_path and ground_truth_path.exists():
        with open(ground_truth_path, 'r') as f:
            ground_truth = json.load(f)

    # --- METRICS CALCULATION ---
    bot_metrics = {}
    
    for bot_data in all_predictions:
        bot_name = bot_data['test_metadata']['bot_name']
        all_preds_text = []
        all_overlaps = []
        
        # Calculate bot-wide semantic score (average across subjects)
        bot_semantic_scores = []
        bot_data['_subject_semantic_cache'] = {}
        
        for subj in bot_data.get('predictions', []):
            sid = subj['subject_id']
            preds = [p['prediction'] for p in subj.get('predictions', [])]
            all_preds_text.extend(preds)
            
            # Semantic & Trait evaluation if ground truth exists
            if ground_truth and sid in ground_truth:
                facts_dict = ground_truth[sid].get('known_facts', {})
                facts = []
                for cat in facts_dict.values():
                    if isinstance(cat, list): facts.extend(cat)
                
                # Keywords overlap
                overlap = calculate_trait_overlap(preds, facts)
                all_overlaps.append(overlap)
                
                # AI Semantic Accuracy
                score, reasoning = get_ai_semantic_score(" ".join(preds), facts)
                bot_data['_subject_semantic_cache'][sid] = {"score": score, "reasoning": reasoning}
                bot_semantic_scores.append(score)
        
        spec_score = calculate_specificity_score(all_preds_text) if all_preds_text else 0
        avg_overlap = sum(all_overlaps) / len(all_overlaps) if all_overlaps else 0
        avg_semantic = sum(bot_semantic_scores) / len(bot_semantic_scores) if bot_semantic_scores else 0
        
        bot_metrics[bot_name] = {
            "overlap": avg_overlap,
            "specificity": spec_score,
            "semantic": avg_semantic,
            "consistency": 0 
        }

    # Cross-bot consistency
    for b1_name in bot_metrics:
        consistencies = []
        b1_data = next(b for b in all_predictions if b['test_metadata']['bot_name'] == b1_name)
        
        for b2_data in all_predictions:
            b2_name = b2_data['test_metadata']['bot_name']
            if b1_name == b2_name: continue
            
            pair_consistencies = []
            for s1 in b1_data.get('predictions', []):
                s2 = next((s for s in b2_data.get('predictions', []) if s['subject_id'] == s1['subject_id']), None)
                if s2:
                    p1 = [p['prediction'] for p in s1.get('predictions', [])]
                    p2 = [p['prediction'] for p in s2.get('predictions', [])]
                    pair_consistencies.append(evaluate_consistency(p1, p2))
            
            if pair_consistencies:
                consistencies.append(sum(pair_consistencies) / len(pair_consistencies))
        
        bot_metrics[b1_name]["consistency"] = sum(consistencies) / len(consistencies) if consistencies else 0

    avg_total_overlap = sum(m["overlap"] for m in bot_metrics.values()) / len(bot_metrics) if bot_metrics else 0
    avg_total_spec = sum(m["specificity"] for m in bot_metrics.values()) / len(bot_metrics) if bot_metrics else 0
    avg_total_semantic = sum(m["semantic"] for m in bot_metrics.values()) / len(bot_metrics) if bot_metrics else 0
    avg_total_consist = sum(m["consistency"] for m in bot_metrics.values()) / len(bot_metrics) if bot_metrics else 0

    # Start HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>4-Bot Blind Test Comparison Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px; line-height: 1.6; color: #212529;
        }}
        .container {{
            max-width: 1400px; margin: 0 auto; background: white;
            border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 30px; text-align: center;
        }}
        .metadata {{ background: #f8f9fa; padding: 20px 30px; border-bottom: 2px solid #e9ecef; }}
        .metadata-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
        .metadata-item {{ background: white; padding: 12px; border-radius: 6px; border-left: 4px solid #667eea; }}
        .performance-overview {{ padding: 30px; background: #fdfcfb; border-bottom: 2px solid #eee; }}
        .perf-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        .perf-table th, .perf-table td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }}
        .perf-table th {{ background: #f8f9fa; font-weight: 600; font-size: 0.85em; text-transform: uppercase; }}
        .score-pill {{ padding: 4px 10px; border-radius: 4px; font-weight: 600; font-size: 0.9em; }}
        .score-high {{ background: #e8f5e9; color: #2e7d32; }}
        .score-med {{ background: #fff3e0; color: #ef6c00; }}
        .score-low {{ background: #ffebee; color: #c62828; }}
        .bot-name {{ font-weight: 700; padding: 4px 8px; border-radius: 4px; display: inline-block; }}
        .bot-omkar-pro {{ background: #e3f2fd; color: #1976d2; }}
        .bot-omkar-lite {{ background: #f3e5f5; color: #7b1fa2; }}
        .bot-jyoti-pro {{ background: #e8f5e9; color: #388e3c; }}
        .bot-jyoti-lite {{ background: #fff3e0; color: #f57c00; }}
        .subject-section {{ padding: 30px; border-bottom: 3px solid #e9ecef; }}
        .subject-header {{
            background: linear-gradient(135deg, #1a2a6c 0%, #b21f1f 100%, #fdbb2d 100%);
            color: white; padding: 20px; border-radius: 8px; margin-bottom: 25px;
        }}
        .question-block {{ margin-bottom: 40px; background: #f8f9fa; border-radius: 8px; padding: 20px; }}
        .question-title {{ font-size: 1.25em; font-weight: 600; margin-bottom: 20px; border-bottom: 2px solid #dee2e6; padding-bottom: 10px; }}
        .bot-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }}
        .bot-card {{ background: white; padding: 18px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); position: relative; }}
        .ai-reasoning {{ 
            margin-top: 15px; padding: 12px; background: #fff9db; 
            border-left: 4px solid #fcc419; font-size: 0.85em; border-radius: 4px;
            display: none;
        }}
        .bot-card:hover .ai-reasoning {{ display: block; }}
        .reveal-section {{
            margin-top: 30px; padding: 25px; background: #f8f9fa;
            border: 3px solid #667eea; border-radius: 12px; text-align: center;
            cursor: pointer;
        }}
        .reveal-name {{
            font-size: 1.8em; font-weight: 800; filter: blur(12px); transition: all 0.4s ease;
        }}
        .reveal-section.revealed .reveal-name {{ filter: none; color: #667eea; }}
        .evaluation-section {{ background: #f8f9fa; padding: 30px; }}
        .eval-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
        .eval-card {{ background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .eval-value {{ font-size: 2.2em; font-weight: 700; color: #667eea; }}
        .footer {{ background: #212529; color: white; padding: 20px; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔮 Intelligence Test Report: Omkar & Jyoti</h1>
            <p>Blind performance analysis with AI-powered Semantic Audit</p>
        </div>
        
        <div class="metadata">
            <div class="metadata-grid">
                <div class="metadata-item">
                    <div style="font-size:0.8em; color:#6c757d;">TEST DATE</div>
                    <div style="font-weight:600;">{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
                </div>
            </div>
        </div>

        <div class="performance-overview">
            <h2>📊 Performance Summary</h2>
            <table class="perf-table">
                <thead>
                    <tr>
                        <th>Configuration</th>
                        <th>Semantic Accuracy</th>
                        <th>Consistency</th>
                        <th>Verdict</th>
                    </tr>
                </thead>
                <tbody>
"""
    for bot_name in ['OMKAR_PRO', 'OMKAR_LITE', 'JYOTI_PRO', 'JYOTI_LITE']:
        m = bot_metrics.get(bot_name, {"overlap":0, "specificity":0, "consistency":0, "semantic":0})
        ov_class = "score-high" if m["overlap"] > 40 else "score-med" if m["overlap"] > 20 else "score-low"
        spec_class = "score-high" if m["specificity"] > 1.5 else "score-med" if m["specificity"] > 1.0 else "score-low"
        cons_class = "score-high" if m["consistency"] > 60 else "score-med" if m["consistency"] > 40 else "score-low"
        sem_class = "score-high" if m["semantic"] > 70 else "score-med" if m["semantic"] > 40 else "score-low"
        
        bot_slug = bot_name.lower().replace('_', '-')
        verdict = "Optimized" if "PRO" in bot_name else "Efficient"
        verdict_color = "#667eea" if "PRO" in bot_name else "inherit"

        html += f"""
                    <tr>
                        <td><span class="bot-name bot-{bot_slug}">{bot_name}</span></td>
                        <td><span class="score-pill {sem_class}">{m["semantic"]:.1f}/100</span></td>
                        <td><span class="score-pill {cons_class}">{m["consistency"]:.1f}%</span></td>
                        <td><strong style="color: {verdict_color};">{verdict}</strong></td>
                    </tr>
"""
    html += """
                </tbody>
            </table>
        </div>
"""

    # Subjects Section
    max_subjects = max(len(b.get('predictions', [])) for b in all_predictions) if all_predictions else 0
    if max_subjects > 0:
        for subject_idx in range(max_subjects):
            # Use first bot's data as subject anchor
            primary_bot_subj = all_predictions[0]['predictions'][subject_idx]
            subject_id = primary_bot_subj['subject_id']
            test_type = primary_bot_subj.get('test_type', 'unknown')
            birth_data = primary_bot_subj.get('birth_data_used', {})
            
            real_name = ground_truth.get(subject_id, {}).get('identity', 'Unknown') if ground_truth else "Unknown"
            
            html += f"""
        <div class="subject-section">
            <div class="subject-header">
                <h2>Subject: {subject_id}</h2>
                <div style="font-size:0.9em; opacity:0.9;">
                    {test_type.replace('_', ' ').title()} | {birth_data.get('date', 'N/A')} | {birth_data.get('location', 'N/A')}
                </div>
            </div>
"""
            # Questions grid
            for q_idx in range(len(primary_bot_subj.get('predictions', []))):
                question = primary_bot_subj['predictions'][q_idx]['question']
                html += f"""
            <div class="question-block">
                <div class="question-title">Q{q_idx + 1}: {question}</div>
                <div class="bot-grid">
"""
                for bot_data in all_predictions:
                    b_name = bot_data['test_metadata']['bot_name']
                    b_class = f"bot-{b_name.lower().replace('_', '-')}"
                    
                    p_text = "⚠️ Missing"
                    if subject_idx < len(bot_data.get('predictions', [])):
                         subj_data = bot_data['predictions'][subject_idx]
                         if q_idx < len(subj_data.get('predictions', [])):
                             p_text = subj_data['predictions'][q_idx].get('prediction', 'No response')
                    
                    # Semantic audit for the whole subject (shown once per subject card)
                    # We'll just show the score in the header of the card for each bot
                    sem_audit = bot_data.get('_subject_semantic_cache', {}).get(subject_id, {"score":0, "reasoning": "N/A"})
                    
                    html += f"""
                    <div class="bot-card">
                        <div class="bot-name {b_class}">{b_name} <span style="float:right; font-size:0.7em;">{sem_audit['score']}/100</span></div>
                        <div style="margin-top:10px; font-size:0.95em;">{p_text}</div>
                        <div class="ai-reasoning">
                            <strong>AI Auditor:</strong> {sem_audit['reasoning']}
                        </div>
                    </div>
"""
                html += "</div></div>"

            html += f"""
            <div class="reveal-section" onclick="this.classList.toggle('revealed')">
                <div style="font-size:0.7em; color:#6c757d; margin-bottom:5px;">TAP TO REVEAL IDENTITY</div>
                <div class="reveal-name">{real_name}</div>
            </div>
        </div>
"""

    html += f"""
        <div class="evaluation-section">
            <h2>📈 Global Performance Averages</h2>
            <div class="eval-grid">
                <div class="eval-card"><div style="font-size:0.8em;">Semantic Accuracy</div><div class="eval-value">{avg_total_semantic:.1f}</div></div>
                <div class="eval-card"><div style="font-size:0.8em;">Bot Consistency</div><div class="eval-value">{avg_total_consist:.1f}%</div></div>
            </div>
        </div>
        <div class="footer">Generated by AI Astrologer Test Framework | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </div>
</body>
</html>
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ Combined HTML report generated: {output_path}")
    return output_path


if __name__ == '__main__':
    results_dir = Path(__file__).parent / 'results'
    prediction_files = []
    for bot_name in ['OMKAR_PRO', 'OMKAR_LITE', 'JYOTI_PRO', 'JYOTI_LITE']:
        files = list(results_dir.glob(f'predictions_{bot_name}_*.json'))
        if files:
            prediction_files.append(max(files, key=lambda p: p.stat().st_mtime))
    
    if prediction_files:
        dt_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = results_dir / f'combined_report_{dt_str}.html'
        gt = Path(__file__).parent / 'data' / 'ground_truth_mapping.json'
        generate_combined_html(prediction_files, out, gt)
