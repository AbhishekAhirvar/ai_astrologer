#!/usr/bin/env bash
# Run complete blind test workflow

set -e

echo "================================================================================"
echo "🔮 BLIND PREDICTION TEST - Complete Workflow"
echo "================================================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "test_data_generator.py" ]; then
    echo "❌ Error: Must run from tests/ai/blind_test/ directory"
    exit 1
fi

# Step 1: Generate test data
echo "Step 1: Generating anonymous test data..."
python test_data_generator.py

if [ ! -f "data/blind_test_dataset.json" ]; then
    echo "❌ Error: Dataset generation failed"
    exit 1
fi

echo "✅ Test data generated"
echo ""

# Step 2: Run predictions (quick or full)
echo "Step 2: Running predictions..."
echo ""
echo "Choose test mode:"
echo "  1) Quick test (2 subjects, ~10 predictions, ~$0.02)"
echo "  2) Full test (9 subjects, ~45 predictions, ~$0.09)"
echo ""
read -p "Enter choice (1 or 2): " choice

if [ "$choice" = "1" ]; then
    echo ""
    echo "Running QUICK test..."
    python blind_predictor.py quick
elif [ "$choice" = "2" ]; then
    echo ""
    echo "Running FULL test..."
    python blind_predictor.py
else
    echo "❌ Invalid choice"
    exit 1
fi

# Step 3: Evaluate results
echo ""
echo "Step 3: Evaluating results..."
echo ""

# Find latest predictions file
latest_pred=$(ls -t results/predictions_*.json 2>/dev/null | head -1)

if [ -z "$latest_pred" ]; then
    echo "❌ No prediction files found"
    exit 1
fi

echo "Evaluating: $latest_pred"
python evaluator.py "$latest_pred" data/ground_truth_mapping.json

echo ""
echo "================================================================================"
echo "✅ BLIND TEST COMPLETE"
echo "================================================================================"
echo ""
echo "📁 Files generated:"
echo "   Data: data/blind_test_dataset.json"
echo "   Predictions: $latest_pred"
echo "   Evaluation: results/evaluation_results.json"
echo ""
echo "📊 Review the evaluation results above!"
echo ""
