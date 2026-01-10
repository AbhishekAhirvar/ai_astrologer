# Token Usage Breakdown - How to Read Cache Stats

## What I Changed

Updated the token logging in `backend/ai.py` to show:
1. **Cached input tokens** - Tokens that were retrieved from cache (FREE on OpenAI)
2. **Non-cached input tokens** - New tokens that had to be processed
3. **Output tokens** - Tokens in the AI's response

## New Log Format

**Before**:
```
📊 TOKEN USAGE: Total=450, Prompt=350, Completion=100, Thinking=0
```

**After**:
```
📊 TOKEN USAGE: Total=450 | Input: 350 (cached: 300, non-cached: 50) | Output: 100 | Thinking: 0
```

## How It Works

The OpenAI API returns `usage.prompt_tokens_details.cached_tokens` which tells you how many input tokens were served from cache.

**Cache** happens when:
- System instruction is the same (OMKAR_SYSTEM_INSTRUCTION)
- Previous messages in the conversation are the same

**Example Conversation**:

### Message 1 (First in conversation):
```
Input: 350 (cached: 0, non-cached: 350) | Output: 100
```
- Nothing cached (first message)
- All 350 input tokens are fresh

### Message 2 (Follow-up):
```
Input: 450 (cached: 300, non-cached: 150) | Output: 95
```
- System instruction + previous messages = 300 tokens (CACHED - FREE!)
- Only the new query + planetary position context = 150 tokens (PAID)
- Output: 95 tokens (PAID)

## Cost Calculation (OpenAI GPT-5.2 - Example Rates)

Assuming:
- Input tokens: $0.50 / 1M tokens
- Cached input tokens: $0.10 / 1M tokens (5x cheaper)
- Output tokens: $2.00 / 1M tokens

**Message 2 Cost**:
- Cached: 300 × $0.10 / 1M = $0.00003
- Non-cached: 150 × $0.50 / 1M = $0.000075
- Output: 95 × $2.00 / 1M = $0.00019
- **Total**: ~$0.000295

**Without Cache** (all 450 tokens non-cached):
- Input: 450 × $0.50 / 1M = $0.000225
- Output: 95 × $2.00 / 1M = $0.00019
- **Total**: ~$0.000415

**Savings**: ~29% on this message

## Optimization Benefits

### 1. Name Only in First Message
- **Before**: "User Identity: John. " in every message (~5 tokens each)
- **After**: "User: John\n" only in first message
- **Benefit**: Fewer non-cached tokens in follow-ups

### 2. No Reasoning for Suggestions
- **Before**: Model generates reasoning tokens (hidden overhead)
- **After**: Direct response only
- **Benefit**: Lower thinking token usage

### 3. System Instruction Caching
- OMKAR_SYSTEM_INSTRUCTION is ~80 tokens
- Gets cached after first use
- **Benefit**: ~80 tokens cached per follow-up message

## How to Monitor

Check your logs for lines starting with `📊 TOKEN USAGE:` or `📊 STREAM TOKEN USAGE:`

The breakdown shows:
- **Total**: All tokens used
- **Input**: Prompt tokens (cached + non-cached)
  - **cached**: Retrieved from cache (cheaper)
  - **non-cached**: Processed fresh (full price)
- **Output**: AI response tokens
- **Thinking**: Reasoning tokens (if applicable)

## Pro Tip

For long conversations:
- Keep system instruction consistent (enables caching)
- Reuse chart data format (gets cached)
- Only vary the user query (minimal non-cached tokens)

This maximizes cache hits and minimizes costs.
