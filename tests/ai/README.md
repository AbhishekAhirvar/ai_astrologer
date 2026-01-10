# Tests / AI

This directory contains AI prediction testing systems.

## 📁 Current Structure

### `blind_test/` - **Rigorous Blind Test System** ✅
The main test system that eliminates AI cheating through anonymization.

**Key Features:**
- Anonymous IDs (no name recognition)
- Generic questions (no context leakage) 
- Control groups (fictional + duplicate charts)
- Automated evaluation

**Quick Start:**
```bash
cd blind_test
python blind_predictor.py quick  # Quick test (2 subjects)
```

See [`blind_test/README.md`](blind_test/README.md) for full documentation.

---

### `docs/` - Documentation
- `AI_INPUT_SUMMARY.md` - What data AI receives
- `DATA_FLOW_ANALYSIS.md` - Technical data flow details
- `show_ai_input.py` - Demo script showing AI input

### `old_flawed_tests/` - Archived
Old prediction tests that had the **name recognition flaw**:
- AI could recognize "Mahatma Gandhi" and use training data
- Tests were not truly blind
- Kept for reference only

**Do not use these for validation!**

---

## 🚀 Recommended Test

**Use `blind_test/` for all prediction validation.**

It's the only system that prevents AI from cheating through name recognition.

---

## 📝 Other Test Files

- `test_ai.py` - Basic AI functionality tests
- `test_cache_verification.py` - Prompt caching tests
- `test_grounding.py` - Grounding behavior tests

These are for basic functionality, not accuracy validation.
