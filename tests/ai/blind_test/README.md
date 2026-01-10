# Blind Prediction Test - MVP

## 🎯 Purpose

This is a **rigorous blind testing system** that prevents AI from "cheating" by recognizing famous people's names. It tests whether predictions are based on astrological charts or the AI's training data.

## 🚨 Problem Solved

**Original flaw**: Sending "User: Mahatma Gandhi" to AI meant it could use biographical knowledge instead of chart data.

**Solution**: Anonymous IDs like "Subject-X7B2K9" ensure AI has no idea who the person is.

## 📊 Test Design

### Test Groups

1. **Famous People (Blind)** - 5 people with anonymous IDs
2. **Fictional Controls** - 2 random charts (should get generic predictions)
3. **Duplicate Controls** - 2 duplicate charts with different IDs (should get similar predictions)

### Evaluation Metrics

- **Trait Overlap**: Do predictions match known traits?
- **Specificity Score**: Are predictions specific or generic?
- **Consistency**: Do duplicate charts get similar predictions?

### Timezone Handling ✅

**Critical Feature:** System correctly handles multiple timezones!

- Backend accepts `timezone_str` parameter (defaults to IST but can be overridden)
- Each subject includes proper timezone in test data
- Famous people use their actual timezones (LA, Chicago, Johannesburg, Kolkata, Berlin)
- Fictional people use real city timezones (Tokyo, Delhi, Cairo, etc.)
- Blind predictor passes: `timezone_str=birth_data["timezone"]`

**Verified:** No hardcoded IST issues ✅

## 🚀 Quick Start

### Step 1: Generate Test Data

```bash
cd tests/ai/blind_test
python test_data_generator.py
```

This creates:
- `data/blind_test_dataset.json` - Anonymous test subjects
- `data/ground_truth_mapping.json` - Secret mapping (for evaluation only)

### Step 2: Run Quick Test (2 subjects)

```bash
python blind_predictor.py quick
```

This tests 2 subjects with 5 questions each = 10 predictions (~$0.02)

### Step 3: Run Full Test (All subjects)

```bash
python blind_predictor.py
```

This tests all 9 subjects = 45 predictions (~$0.09)

### Step 4: Evaluate Results

```bash
python evaluator.py results/predictions_XXXXXX.json data/ground_truth_mapping.json
```

## 📁 File Structure

```
blind_test/
├── __init__.py
├── test_data_generator.py  # Creates anonymous datasets
├── blind_predictor.py      # Runs predictions with anonymous IDs
├── evaluator.py            # Evaluates using semantic analysis
├── data/
│   ├── blind_test_dataset.json      # Test subjects (anonymous)
│   └── ground_truth_mapping.json    # Secret mappings
└── results/
    ├── predictions_XXXXX.json       # Raw predictions
    └── evaluation_results.json      # Evaluation scores
```

## 🔍 What Gets Tested

### For Each Subject:
- 5 generic questions (no identity hints)
- AI receives anonymous ID only
- Location shown as coordinates only
- No real names anywhere

### Example Input to AI:
```
User: Subject-X7B2K9
Location: Coordinates: 37.77°N, 122.42°W
Question: What is my primary life purpose?
```

AI has NO idea this is Steve Jobs!

## 📊 Evaluation

### Three Key Checks:

1. **Specificity Test**
   - Do famous people get more specific predictions than fictional charts?
   - If yes: AI might be using chart data effectively
   - If no: AI might be too generic

2. **Consistency Test**
   - Do duplicate charts (same person, different IDs) get similar predictions?
   - If yes: AI is using chart data consistently
   - If no: Predictions are random/unreliable

3. **Trait Overlap Test**
   - Do predictions mention traits that match known facts?
   - High overlap: Predictions align with reality
   - Low overlap: Predictions don't match

## ⚠️ What This Test Shows

### Can Show:
✅ Whether AI makes specific vs. generic predictions  
✅ Whether predictions are consistent (duplicate test)  
✅ Whether AI might be using external knowledge  
✅ Relative performance vs. baseline  

### Cannot Show:
❌ That astrology is "scientifically valid"  
❌ That future predictions will be accurate  
❌ Causation (only correlation)  
❌ Proof of astrological mechanisms  

## 🎓 Expected Results

### If AI Uses Chart Data:
- Famous & fictional both get specific predictions
- Duplicates get very similar predictions (>80%)
- Trait overlap is moderate (30-50%)

### If AI Uses Name Recognition:
- Famous get accurate predictions
- Fictional get generic predictions
- Duplicates with different IDs don't match

### If AI is Generic:
- All predictions are vague
- No difference between famous & fictional
- Low consistency for duplicates

## 💰 Cost Estimate

- Quick test (2 subjects): ~$0.02
- Full test (9 subjects): ~$0.09
- With caching: ~70% cheaper

## 🔬 Future Improvements

- [ ] Add semantic similarity with embeddings
- [ ] Add more control groups
- [ ] Test with date obfuscation
- [ ] Compare multiple AI models
- [ ] Expert astrologer benchmark

## 📝 Notes

- This is for **software validation** only
- Not for proving/disproving astrology
- Results are for development purposes
- No medical/financial/legal advice implied

---

**Created**: 2026-01-09  
**Version**: MVP 1.0  
**Status**: Ready for testing
