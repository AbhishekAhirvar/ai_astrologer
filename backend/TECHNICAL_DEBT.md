# Technical Debt - backend/ai.py

## Critical Issues (Documented, Not Fixed)

### 1. Streaming + Retry Footgun ⚠️
**Location**: `get_astrology_prediction_stream` with `@retry` decorator

**Problem**:
- Generator yields partial output
- If failure happens mid-stream, retry restarts from scratch
- Caller may have already consumed partial chunks
- Result: Output duplication or inconsistent state

**Impact**: Acceptable for internal testing, **must be fixed before external release**

**Solution** (when needed):
```python
# Option A: Remove @retry from streaming function
# Option B: Implement stateful retry with chunk tracking
# Option C: Wrap at caller level with idempotency tokens
```

---

### 2. Stream Event Parsing is Brittle
**Location**: Lines 169-181 in `get_astrology_prediction_stream`

**Problem**:
- Defensive parsing for multiple SDK shapes (object/dict/evolving formats)
- Behavior may change on SDK upgrades
- Bugs will be "soft" (missing/duplicated tokens, not crashes)

**Impact**: Functional but fragile. Acceptable for now.

**Mitigation**: Pin OpenAI SDK version, test on upgrades

---

### 3. Prompt Consistency Drift
**Location**: Multiple functions inject user identity differently

**Examples**:
- `get_astrology_prediction_stream`: `f"User Identity: {user_name}. "`
- `get_astrology_prediction`: Same pattern
- `get_followup_questions`: Embedded in system instruction

**Impact**: Increases prompt entropy and behavioral variance

**Fix** (later): Create standardized `_build_user_context(user_name, ...)` helper

---

## Fixed Issues ✅

### 3. Follow-up Questions System Role (FIXED)
Changed `get_followup_questions` to use proper system/user message separation instead of embedding everything in user content.

### 5. Silent Assumptions (FIXED)
Added defensive checks in `_get_serializable_chart_data`:
- Validate `.planets` exists and is not None
- Wrap serialization in try/except to skip unserializable planets
