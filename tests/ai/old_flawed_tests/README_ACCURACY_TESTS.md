# Prediction Accuracy Testing

This test suite validates the accuracy of astrological predictions by comparing them against documented life events of famous personalities.

## Test Database

The test includes birth data and documented facts for:

1. **Steve Jobs** - Technology innovator, Apple founder
2. **Oprah Winfrey** - Media mogul, philanthropist
3. **Elon Musk** - Multi-company entrepreneur
4. **Mahatma Gandhi** - Indian independence leader
5. **Albert Einstein** - Theoretical physicist

## How It Works

For each person, the test:
1. Generates a Vedic astrological chart from their birth data
2. Asks specific questions about career, personality, life events
3. Gets AI predictions
4. Compares predictions against documented facts
5. Calculates accuracy score based on keyword matching

## Running Tests

### Test All Famous People
```bash
# Activate venv
source venv/bin/activate

# Run comprehensive test (this will use API credits)
python tests/ai/test_prediction_accuracy.py
```

### Test Specific Person
```bash
python tests/ai/test_prediction_accuracy.py "Steve Jobs"
python tests/ai/test_prediction_accuracy.py "Oprah"
python tests/ai/test_prediction_accuracy.py "Einstein"
```

### Run as Pytest
```bash
pytest tests/ai/test_prediction_accuracy.py -v -s
```

## Output Format

The test provides:

```
🔮 TESTING: Steve Jobs
================================================================================

📋 Question: What is my career path and potential?

🤖 AI Prediction:
   [AI's response about career]

📊 Accuracy Analysis:
   Score: 45.5%
   Keywords Found: 5/11

✅ Matches with Known Facts:
   ✓ Predicted 'innovation' - Actual: Revolutionized personal computing industry
   ✓ Predicted 'leadership' - Actual: Known for innovation and design aesthetics

📚 Known Facts (Reference):
   CAREER:
   • Founded Apple Computer at age 21
   • Revolutionized personal computing industry
   • Created multiple billion-dollar companies
```

## Accuracy Scoring

The accuracy score is calculated by:
1. Extracting keywords from known facts
2. Checking if those keywords appear in AI predictions
3. Score = (matched keywords / total keywords) × 100

**Note:** This is a basic keyword-matching approach. Real astrological accuracy would require:
- Expert astrologer review
- Timing prediction validation
- Blind tests
- Larger sample size

## Customization

### Add New People

Edit `FAMOUS_PEOPLE` dictionary in the test file:

```python
"person_id": {
    "name": "Person Name",
    "birth_data": {
        "year": 1980,
        "month": 1,
        "day": 15,
        "hour": 14,
        "minute": 30,
        "city": "City Name",
        "lat": 40.7128,
        "lon": -74.0060,
        "timezone": "America/New_York"
    },
    "known_facts": {
        "career": ["fact 1", "fact 2"],
        "personality": ["trait 1", "trait 2"],
        # ...
    },
    "test_questions": [
        "What is my career potential?",
        # ...
    ]
}
```

### Modify Questions

Change the `test_questions` array for each person to test different aspects.

## Limitations

⚠️ **Important Notes:**

1. **This is NOT a scientific validation** - Astrology predictions are subjective
2. **API Costs** - Each test makes OpenAI API calls (costs money)
3. **Keyword Matching** - Simple matching may not capture nuanced predictions
4. **Data Quality** - Birth times for famous people may not be 100% accurate
5. **Interpretation** - Astrological predictions require expert interpretation

## Use Cases

This test is useful for:
- ✅ Checking if AI avoids generic responses
- ✅ Validating chart calculations are reasonable
- ✅ Testing consistency of predictions
- ✅ Identifying prediction patterns
- ❌ NOT for claiming scientific validity of astrology
- ❌ NOT for production accuracy metrics

## Contributing

To add more famous people:
1. Find publicly available birth data (time, date, location)
2. Document verified life events from reliable sources
3. Add to `FAMOUS_PEOPLE` dictionary
4. Run test to validate

## Legal & Ethical

- Birth data is from public records and biographies
- Used for educational/testing purposes only
- No medical, financial, or life advice is given
- Results are for software testing, not astrological consultation
