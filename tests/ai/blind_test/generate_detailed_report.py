
import json
import sys
from pathlib import Path
from datetime import datetime

def generate_html_report(json_file_path: str):
    path = Path(json_file_path)
    if not path.exists():
        print(f"File not found: {path}")
        return

    with open(path, 'r') as f:
        data = json.load(f)

    # Basic HTML structure
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Comprehensive AI Astrology Report</title>
        <style>
            body { font-family: sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px; }
            .bot-section { margin-bottom: 40px; border: 1px solid #ddd; border-radius: 5px; overflow: hidden; }
            .bot-header { background: #2c3e50; color: white; padding: 10px 15px; font-weight: bold; font-size: 1.2em; display: flex; justify-content: space-between; }
            .qa-block { padding: 15px; border-bottom: 1px solid #eee; }
            .qa-block:last-child { border-bottom: none; }
            .question { font-weight: bold; color: #d35400; margin-bottom: 5px; }
            .answer { line-height: 1.5; color: #333; margin-bottom: 10px; }
            .meta { font-size: 0.9em; color: #7f8c8d; background: #f9f9f9; padding: 8px; border-radius: 4px; border: 1px solid #eee; }
            details { margin-top: 10px; }
            summary { cursor: pointer; color: #2980b9; font-weight: bold; }
            pre { background: #2c3e50; color: #ecf0f1; padding: 10px; border-radius: 4px; overflow-x: auto; white-space: pre-wrap; font-size: 0.85em; }
            .token-stats { font-weight: bold; color: #27ae60; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Comprehensive Blind Test Report: Michael Peterson</h1>
            <p>Generated: """ + datetime.now().strftime('%Y-%m-%d %H:%M') + """</p>
    """

    for bot_result in data:
        bot_name = bot_result['bot']
        preds = bot_result['preds']
        
        # Calculate total tokens for this bot
        total_input = sum(p.get('usage', {}).get('input_tokens', 0) for p in preds)
        total_output = sum(p.get('usage', {}).get('output_tokens', 0) for p in preds)
        total_cost_est = (total_input * 0.15 / 1000000) + (total_output * 0.60 / 1000000) # GPT-5-nano approx pricing
        
        html += f"""
            <div class="bot-section">
                <div class="bot-header">
                    <span>🤖 {bot_name}</span>
                    <span style="font-size: 0.8em; opacity: 0.9;">Total Tokens: {total_input+total_output} (~${total_cost_est:.6f})</span>
                </div>
        """
        
        for p in preds:
            usage = p.get('usage', {})
            payload = p.get('payload', 'N/A')
            
            # Format payload for better reading
            try:
                # If payload has "CHART_DATA:", try to format the JSON part
                if "CHART_DATA:" in payload:
                    parts = payload.split("CHART_DATA:", 1)
                    preamble = parts[0]
                    json_part = parts[1].split("\n\nQuestion:", 1)[0]
                    rest = parts[1].split("\n\nQuestion:", 1)[1] if "\n\nQuestion:" in parts[1] else ""
                    
                    parsed_json = json.loads(json_part.strip())
                    formatted_json = json.dumps(parsed_json, indent=2)
                    
                    display_payload = f"{preamble}CHART_DATA: {formatted_json}\n\nQuestion:{rest}"
                else:
                    display_payload = payload
            except:
                display_payload = payload

            html += f"""
                <div class="qa-block">
                    <div class="question">Q: {p['q']}</div>
                    <div class="answer">{p['a'].replace(chr(10), '<br>')}</div>
                    
                    <div class="meta">
                        <span class="token-stats">🎫 Usage: In: {usage.get('input_tokens',0)} | Out: {usage.get('output_tokens',0)} | Total: {usage.get('total_tokens',0)}</span>
                        
                        <details>
                            <summary>🔍 View Prompt Payload</summary>
                            <pre>{display_payload}</pre>
                        </details>
                    </div>
                </div>
            """
        
        html += "</div>"

    html += """
        </div>
    </body>
    </html>
    """
    
    output_path = path.with_suffix('.html')
    with open(output_path, 'w') as f:
        f.write(html)
        
    print(f"✅ HTML Report generated: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        generate_html_report(sys.argv[1])
    else:
        print("Usage: python generate_detailed_report.py <json_file>")
