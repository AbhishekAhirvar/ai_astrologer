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


def load_prediction_file(filepath: Path) -> Dict[str, Any]:
    """Load a prediction JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def generate_combined_html(prediction_files: List[Path], output_path: Path, ground_truth_path: Path = None):
    """
    Generate a single HTML report combining all bot predictions.
    
    Args:
        prediction_files: List of paths to prediction JSON files
        output_path: Path to save the combined HTML report
        ground_truth_path: Optional path to ground truth mapping for evaluation
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
    
    # Start HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>4-Bot Blind Test Comparison Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header .subtitle {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .metadata {{
            background: #f8f9fa;
            padding: 20px 30px;
            border-bottom: 2px solid #e9ecef;
        }}
        
        .metadata-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        
        .metadata-item {{
            background: white;
            padding: 12px;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }}
        
        .metadata-label {{
            font-size: 0.85em;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .metadata-value {{
            font-size: 1.1em;
            font-weight: 600;
            color: #212529;
            margin-top: 4px;
        }}
        
        .subject-section {{
            padding: 30px;
            border-bottom: 3px solid #e9ecef;
        }}
        
        .subject-header {{
            background: linear-gradient(135deg, #1a2a6c 0%, #b21f1f 100%, #fdbb2d 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 25px;
        }}
        
        .subject-header h2 {{
            font-size: 1.8em;
            margin-bottom: 8px;
        }}
        
        .subject-info {{
            font-size: 0.95em;
            opacity: 0.95;
        }}
        
        .reveal-section {{
            margin-top: 30px;
            padding: 25px;
            background: #f8f9fa;
            border: 3px solid #667eea;
            border-radius: 12px;
            text-align: center;
            cursor: pointer;
            transition: background 0.3s;
        }}
        
        .reveal-section:hover {{
            background: #fff;
        }}
        
        .reveal-label {{
            font-size: 0.9em;
            color: #6c757d;
            text-transform: uppercase;
            font-weight: 700;
            margin-bottom: 10px;
            display: block;
        }}
        
        .reveal-name {{
            font-size: 1.8em;
            font-weight: 800;
            color: #212529;
            filter: blur(12px);
            transition: all 0.4s ease;
            user-select: none;
            cursor: pointer;
        }}
        
        .reveal-section.revealed .reveal-name,
        .reveal-section:active .reveal-name {{
            filter: none;
            user-select: text;
            color: #667eea;
        }}
        
        .performance-overview {{
            padding: 30px;
            background: #fdfcfb;
            border-bottom: 2px solid #eee;
        }}
        
        .perf-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        .perf-table th, .perf-table td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        
        .perf-table th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #495057;
            text-transform: uppercase;
            font-size: 0.85em;
        }}
        
        .score-pill {{
            padding: 4px 10px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 0.9em;
        }}
        
        .score-high {{ background: #e8f5e9; color: #2e7d32; }}
        .score-med {{ background: #fff3e0; color: #ef6c00; }}
        .score-low {{ background: #ffebee; color: #c62828; }}
        
        .question-block {{
            margin-bottom: 40px;
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
        }}
        
        .question-title {{
            font-size: 1.3em;
            font-weight: 600;
            color: #212529;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid #dee2e6;
        }}
        
        .bot-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }}
        
        .bot-card {{
            background: white;
            border-radius: 8px;
            padding: 18px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .bot-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .bot-name {{
            font-weight: 700;
            font-size: 1.1em;
            margin-bottom: 12px;
            padding: 8px 12px;
            border-radius: 6px;
            display: inline-block;
        }}
        
        .bot-omkar-pro {{ background: #e3f2fd; color: #1976d2; }}
        .bot-omkar-lite {{ background: #f3e5f5; color: #7b1fa2; }}
        .bot-jyoti-pro {{ background: #e8f5e9; color: #388e3c; }}
        .bot-jyoti-lite {{ background: #fff3e0; color: #f57c00; }}
        
        .prediction-text {{
            color: #495057;
            line-height: 1.8;
            font-size: 0.95em;
        }}
        
        .error-text {{
            color: #dc3545;
            font-style: italic;
            background: #f8d7da;
            padding: 12px;
            border-radius: 6px;
            border-left: 4px solid #dc3545;
        }}
        
        .evaluation-section {{
            background: #f8f9fa;
            padding: 30px;
        }}
        
        .eval-header {{
            font-size: 2em;
            color: #212529;
            margin-bottom: 25px;
            text-align: center;
        }}
        
        .eval-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .eval-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .eval-label {{
            font-size: 0.9em;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        
        .eval-value {{
            font-size: 2.5em;
            font-weight: 700;
            color: #667eea;
        }}
        
        .eval-description {{
            font-size: 0.85em;
            color: #6c757d;
            margin-top: 8px;
        }}
        
        .footer {{
            background: #212529;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 0.9em;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
            }}
            .bot-card {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔮 4-Bot Blind Test Comparison</h1>
            <div class="subtitle">Comprehensive Astrological AI Performance Analysis</div>
        </div>
        
        <div class="metadata">
            <div class="metadata-grid">
                <div class="metadata-item">
                    <div class="metadata-label">Test Date</div>
                    <div class="metadata-value">{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">System Performance</div>
                    <div class="metadata-value">4 Bots Active</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Analyzer Status</div>
                    <div class="metadata-value">Automated</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Blind Strength</div>
                    <div class="metadata-value">High</div>
                </div>
            </div>
        </div>

        <div class="performance-overview">
            <h2 style="font-size: 1.5em; color: #212529;">📊 Performance Analyzer Summary</h2>
            <table class="perf-table">
                <thead>
                    <tr>
                        <th>Bot Configuration</th>
                        <th>Trait Overlap</th>
                        <th>Specificity</th>
                        <th>Consistency</th>
                        <th>Verdict</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><span class="bot-name bot-omkar-pro" style="margin:0; font-size: 0.85em;">OMKAR_PRO</span></td>
                        <td><span class="score-pill score-high">--%</span></td>
                        <td><span class="score-pill score-high">--</span></td>
                        <td><span class="score-pill score-high">--%</span></td>
                        <td><strong style="color: #667eea;">Optimized</strong></td>
                    </tr>
                    <tr>
                        <td><span class="bot-name bot-omkar-lite" style="margin:0; font-size: 0.85em;">OMKAR_LITE</span></td>
                        <td><span class="score-pill score-med">--%</span></td>
                        <td><span class="score-pill score-med">--</span></td>
                        <td><span class="score-pill score-high">--%</span></td>
                        <td><strong>Token Efficient</strong></td>
                    </tr>
                    <tr>
                        <td><span class="bot-name bot-jyoti-pro" style="margin:0; font-size: 0.85em;">JYOTI_PRO</span></td>
                        <td><span class="score-pill score-high">--%</span></td>
                        <td><span class="score-pill score-high">--</span></td>
                        <td><span class="score-pill score-high">--%</span></td>
                        <td><strong style="color: #667eea;">Optimized</strong></td>
                    </tr>
                    <tr>
                        <td><span class="bot-name bot-jyoti-lite" style="margin:0; font-size: 0.85em;">JYOTI_LITE</span></td>
                        <td><span class="score-pill score-med">--%</span></td>
                        <td><span class="score-pill score-med">--</span></td>
                        <td><span class="score-pill score-high">--%</span></td>
                        <td><strong>Token Efficient</strong></td>
                    </tr>
                </tbody>
            </table>
        </div>
"""
    
    # Determine max subjects based on the most complete file
    max_subjects = 0
    primary_file_idx = 0
    
    if all_predictions:
        for idx, pred in enumerate(all_predictions):
            if 'predictions' in pred:
                count = len(pred['predictions'])
                if count > max_subjects:
                    max_subjects = count
                    primary_file_idx = idx
    
    # Group predictions by subject
    if max_subjects > 0:
        primary_predictions = all_predictions[primary_file_idx]['predictions']
        for subject_idx in range(max_subjects):
            # Use data from primary file for headers
            if subject_idx < len(primary_predictions):
                subject_data = primary_predictions[subject_idx]
            else:
                # Fallback if primary is weirdly inconsistent
                subject_data = {'subject_id': f'Unknown-{subject_idx}', 'birth_data_used': {}}
                
            subject_id = subject_data['subject_id']
            test_type = subject_data.get('test_type', 'unknown')
            birth_data = subject_data.get('birth_data_used', {})
            
            # Get real identity if available
            real_name = "Unknown"
            if ground_truth and subject_id in ground_truth:
                real_name = ground_truth[subject_id].get('real_name', 'Unknown')
            
            html += f"""
        <div class="subject-section">
            <div class="subject-header">
                <h2>Blind Subject: {subject_id}</h2>
                <div class="subject-info">
                    Test Type: {test_type} | ID: {subject_id}<br>
                    Data Used: {birth_data.get('date', 'N/A')} {birth_data.get('time', 'N/A')} | {birth_data.get('location', 'N/A')}
                </div>
            </div>
"""
            
            # Get questions from first bot
            questions = subject_data['predictions']
            
            # For each question, show all bot responses side by side
            for q_idx, question_data in enumerate(questions):
                question = question_data['question']
                
                html += f"""
            <div class="question-block">
                <div class="question-title">Q{q_idx + 1}: {question}</div>
                <div class="bot-grid">
"""
                
                # Collect responses from all bots for this question
                for bot_data in all_predictions:
                    bot_name = bot_data['test_metadata']['bot_name']
                    if subject_idx < len(bot_data.get('predictions', [])):
                        bot_subject = bot_data['predictions'][subject_idx]
                        if q_idx < len(bot_subject.get('predictions', [])):
                             bot_prediction = bot_subject['predictions'][q_idx]
                             prediction_text = bot_prediction.get('prediction', 'N/A')
                        else:
                             prediction_text = "⚠️ No response generated"
                             is_error = True
                    else:
                        prediction_text = "⚠️ Subject data missing (Bot run incomplete)"
                        is_error = True
                    is_error = prediction_text.startswith('ERROR')
                    
                    bot_class = f"bot-{bot_name.lower().replace('_', '-')}"
                    
                    html += f"""
                    <div class="bot-card">
                        <div class="bot-name {bot_class}">{bot_name}</div>
                        <div class="{'error-text' if is_error else 'prediction-text'}">
                            {prediction_text}
                        </div>
                    </div>
"""
                
                html += """
                </div>
            </div>
"""
            
            html += f"""
            <div class="reveal-section" onclick="this.classList.toggle('revealed')">
                <span class="reveal-label">Tap to Reveal Identity</span>
                <div class="reveal-name">{real_name}</div>
            </div>
        </div>
"""
    
    # Add evaluation section if ground truth available
    if ground_truth:
        html += """
        <div class="evaluation-section">
            <h2 class="eval-header">📊 Evaluation Metrics</h2>
            <div class="eval-grid">
                <div class="eval-card">
                    <div class="eval-label">Avg Trait Overlap</div>
                    <div class="eval-value">--%</div>
                    <div class="eval-description">Across all bots</div>
                </div>
                <div class="eval-card">
                    <div class="eval-label">Event Accuracy</div>
                    <div class="eval-value">--%</div>
                    <div class="eval-description">Timeline predictions</div>
                </div>
                <div class="eval-card">
                    <div class="eval-label">Specificity Score</div>
                    <div class="eval-value">--</div>
                    <div class="eval-description">Detail level</div>
                </div>
                <div class="eval-card">
                    <div class="eval-label">Consistency</div>
                    <div class="eval-value">--%</div>
                    <div class="eval-description">Between bots</div>
                </div>
            </div>
        </div>
"""
    
    html += f"""
        <div class="footer">
            Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')} | AI Astrologer Blind Test Framework
        </div>
    </div>
</body>
</html>
"""
    
    # Write HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Combined HTML report generated: {output_path}")
    return output_path


if __name__ == '__main__':
    # Example usage
    results_dir = Path(__file__).parent / 'results'
    
    # Find the most recent prediction files for each bot
    prediction_files = []
    for bot_name in ['OMKAR_PRO', 'OMKAR_LITE', 'JYOTI_PRO', 'JYOTI_LITE']:
        files = list(results_dir.glob(f'predictions_{bot_name}_*.json'))
        if files:
            latest = max(files, key=lambda p: p.stat().st_mtime)
            prediction_files.append(latest)
            print(f"Found {bot_name}: {latest.name}")
    
    if prediction_files:
        script_dir = Path(__file__).parent
        output_path = results_dir / f'combined_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        ground_truth_path = script_dir / 'data' / 'ground_truth_mapping.json'
        
        generate_combined_html(prediction_files, output_path, ground_truth_path)
    else:
        print("❌ No prediction files found!")
