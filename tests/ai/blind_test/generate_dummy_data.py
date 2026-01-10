"""
Dummy Data Generator for HTML Report Verification
"""
import json
from pathlib import Path
from datetime import datetime

def generate_dummy_results():
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    bots = ["OMKAR_PRO", "OMKAR_LITE", "JYOTI_PRO", "JYOTI_LITE"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for bot in bots:
        dummy_data = {
            "test_metadata": {
                "run_at": datetime.now().isoformat(),
                "test_type": "dummy_test",
                "num_subjects": 1,
                "bot_name": bot,
                "is_kp_mode": "JYOTI" in bot,
                "bot_mode": "pro" if "PRO" in bot else "lite"
            },
            "predictions": [
                {
                    "subject_id": "Subject-6VUF87",
                    "test_type": "famous_blind",
                    "bot_name": bot,
                    "predictions": [
                        {
                            "question": "What is my primary life purpose?",
                            "prediction": f"Om Tat Sat. This is a dummy prediction from {bot} about your life purpose. You are destined for great things.",
                            "timestamp": datetime.now().isoformat()
                        },
                        {
                            "question": "What are my natural talents?",
                            "prediction": f"According to {bot}, your natural talents include precision and wisdom. Also, Jupiter is strong in your chart.",
                            "timestamp": datetime.now().isoformat()
                        }
                    ],
                    "birth_data_used": {
                        "date": "1990-01-01",
                        "time": "12:00",
                        "location": "Coordinates: 0°N, 0°E"
                    }
                }
            ]
        }
        
        filename = f"predictions_{bot}_{timestamp}_DUMMY.json"
        with open(results_dir / filename, "w") as f:
            json.dump(dummy_data, f, indent=2)
            
    print(f"✅ Generated dummy JSONs for {len(bots)} bots.")

if __name__ == "__main__":
    generate_dummy_results()
