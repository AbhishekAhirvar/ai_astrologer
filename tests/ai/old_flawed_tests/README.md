# Old Prediction Accuracy Tests (FLAWED - Do Not Use)

## ⚠️ Warning: These Tests Have a Critical Flaw

These tests were **archived** because they have a fundamental design flaw:

### The Problem

```python
# What was sent to AI:
User: Mahatma Gandhi
Question: What is my life purpose?
```

**Issue:** AI recognizes "Mahatma Gandhi" from training data and can use biographical knowledge instead of astrological chart analysis.

**Result:** Test results are **meaningless** - we can't tell if AI is using:
- ✅ Chart data (what we want)
- ❌ Biographical knowledge from training (cheating)

## ✅ Use the New Blind Test Instead

The new **blind test system** in `/tests/ai/blind_test/` fixes this:
- Uses anonymous IDs: `Subject-X7B2K9` instead of `Mahatma Gandhi`
- Generic questions only (no identity hints)
- Control groups (fictional + duplicate charts)
- Prevents name recognition completely

## 📁 Files in This Archive

- `test_prediction_accuracy.py` - Original flawed test
- `quick_accuracy_demo.py` - Demo of flawed test
- `README_ACCURACY_TESTS.md` - Original documentation
- `PREDICTION_TESTING_SUMMARY.md` - Original summary

## 🎓 Why Keep These?

Educational purposes - to show the evolution of the testing methodology and why rigorous blind testing is necessary.

---

**Created:** 2026-01-09  
**Archived:** 2026-01-09  
**Reason:** Name recognition flaw  
**Replacement:** `/tests/ai/blind_test/`
