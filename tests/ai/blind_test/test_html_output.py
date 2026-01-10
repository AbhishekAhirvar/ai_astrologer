#!/usr/bin/env python3
"""
Test HTML Output Generation with Dummy Data
No API calls - just verifies HTML file creation works correctly
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from tests.ai.blind_test.evaluator import create_html_output

def create_dummy_predictions():
    """Create dummy prediction data for testing HTML output"""
    return {
        "test_metadata": {
            "run_at": datetime.now().isoformat(),
            "total_subjects": 2,
            "total_predictions": 12
        },
        "predictions": [
            {
                "subject_id": "Subject-TEST01",
                "test_type": "famous_blind",
                "predictions": [
                    {
                        "question": "What is my primary life purpose?",
                        "prediction": "Your chart shows a powerful combination of Sun in the 10th house and Moon in Gemini, indicating a life purpose centered around innovation and communication. You are meant to transform how people interact with technology.",
                        "timestamp": datetime.now().isoformat()
                    },
                    {
                        "question": "When are the major events in my life?",
                        "prediction": "Major events will occur during Jupiter transits. Expect significant breakthroughs around ages 21, 33, and 45. The period between 1995-2005 shows exceptional achievement potential with multiple planetary dashas aligning.",
                        "timestamp": datetime.now().isoformat()
                    },
                    {
                        "question": "What are my natural talents?",
                        "prediction": "Mercury in the 1st house gives exceptional analytical abilities. Your chart indicates natural talent in technology, design thinking, and persuasive communication.",
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            },
            {
                "subject_id": "Control-TEST02",
                "test_type": "fictional_control",
                "predictions": [
                    {
                        "question": "What is my primary life purpose?",
                        "prediction": "Your ascendant lord suggests a purpose involving service and healing. Saturn's placement indicates steady progress through disciplined effort.",
                        "timestamp": datetime.now().isoformat()
                    },
                    {
                        "question": "When are the major events in my life?",
                        "prediction": "Saturn return at age 29-30 will be transformative. Venus dasha periods show romantic and creative milestones.",
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            }
        ]
    }

def create_dummy_ground_truth():
    """Create dummy ground truth with actual events"""
    return {
        "Subject-TEST01": {
            "identity": "Steve Jobs",
            "known_facts": {
                "career": ["Technology innovator", "Founded Apple"],
                "major_events": [
                    "1976: Co-founded Apple Computer",
                    "1985: Forced out of Apple",
                    "1997: Returned to Apple as CEO",
                    "2001: Launched iPod",
                    "2007: Launched iPhone",
                    "2011: Passed away from pancreatic cancer"
                ]
            }
        },
        "Control-TEST02": {
            "identity": "Fictional Person (No Real Biography)",
            "known_facts": {}
        }
    }

def main():
    print("\n" + "="*80)
    print("🧪 TESTING HTML OUTPUT GENERATION (No API Calls)")
    print("="*80)
    
    # Create test directory
    test_dir = Path(__file__).parent / "results" / "test"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n📝 Creating dummy prediction data...")
    predictions = create_dummy_predictions()
    ground_truth = create_dummy_ground_truth()
    
    print(f"   ✅ Created {len(predictions['predictions'])} test subjects")
    print(f"   ✅ Generated {sum(len(p['predictions']) for p in predictions['predictions'])} dummy predictions")
    
    # Save dummy JSON files
    predictions_file = test_dir / "dummy_predictions.json"
    ground_truth_file = test_dir / "dummy_ground_truth.json"
    
    with open(predictions_file, 'w') as f:
        json.dump(predictions, f, indent=2)
    
    with open(ground_truth_file, 'w') as f:
        json.dump(ground_truth, f, indent=2)
    
    print(f"\n💾 Saved test data:")
    print(f"   {predictions_file}")
    print(f"   {ground_truth_file}")
    
    # Generate HTML output
    print("\n🎨 Generating HTML output...")
    html_file = test_dir / "test_output.html"
    
    try:
        create_html_output(predictions, ground_truth, str(html_file))
        
        # Verify file was created
        if html_file.exists():
            file_size = html_file.stat().st_size
            print(f"\n✅ SUCCESS! HTML file created:")
            print(f"   📄 {html_file}")
            print(f"   📊 Size: {file_size:,} bytes")
            
            # Quick content verification
            with open(html_file, 'r') as f:
                content = f.read()
                
            checks = {
                "Contains Steve Jobs": "Steve Jobs" in content,
                "Contains actual events": "1976: Co-founded Apple" in content,
                "Contains predictions": "innovation and communication" in content,
                "Contains styling": "background: linear-gradient" in content,
                "Contains fictional control": "Fictional Person" in content
            }
            
            print("\n🔍 Content Verification:")
            all_passed = True
            for check_name, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"   {status} {check_name}")
                if not passed:
                    all_passed = False
            
            if all_passed:
                print("\n🎉 All checks passed! HTML output is working correctly.")
                print(f"\n💡 Open in browser: file://{html_file.absolute()}")
                return 0
            else:
                print("\n⚠️  Some checks failed. Review the HTML file.")
                return 1
                
        else:
            print("\n❌ ERROR: HTML file was not created!")
            return 1
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
