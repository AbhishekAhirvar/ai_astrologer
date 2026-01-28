
import json
import sys

# Rates per 1M tokens
# Nano
NANO_IN = 0.05
NANO_IN_CACHE = 0.005
NANO_OUT = 0.40

# GPT-5.2
GPT52_IN = 1.75
GPT52_IN_CACHE = 0.175
GPT52_OUT = 14.00

def calculate_costs(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    total_input = 0
    total_output = 0
    # Note: The current JSON schema might not split cached/non-cached explicitly in the 'usage' dict unless I look closer.
    # backend/ai.py returns: "usage": { "input_tokens": ..., "output_tokens": ..., "total_tokens": ... }
    # It does NOT properly pass through cached_tokens in the simplified usage dict.
    # I'll check if I can assume a cache hit rate or if I need to treat all as non-cached for a conservative estimate.
    # Given the user prompt mentioned "pehla input dusra cashed", they know cache exists.
    # But since my backend/ai.py debug info (which I edited in step 1165) only passes input/output/total in the dictionary,
    # I will have to calculate cost assuming 0% cache for a "worst case" or try to find if cache info is hidden elsewhere.
    # Looking at step 1165 replace_content, I only put input/output/total in the return dict.
    # So I will use the base Input rate for all input tokens.
    
    print(f"Reading: {json_file}")
    
    for bot in data:
        bot_in = 0
        bot_out = 0
        for p in bot['preds']:
            u = p.get('usage', {})
            bot_in += u.get('input_tokens', 0)
            bot_out += u.get('output_tokens', 0)
        
        total_input += bot_in
        total_output += bot_out
        
        # Per bot calc
        nano_cost = (bot_in * NANO_IN / 1e6) + (bot_out * NANO_OUT / 1e6)
        gpt52_cost = (bot_in * GPT52_IN / 1e6) + (bot_out * GPT52_OUT / 1e6)
        
        print(f"\nBot: {bot['bot']}")
        print(f"  Tokens: {bot_in} In, {bot_out} Out")
        print(f"  Nano Cost: ${nano_cost:.6f}")
        print(f"  5.2 Cost:  ${gpt52_cost:.6f}")

    # Grand Total
    grand_nano = (total_input * NANO_IN / 1e6) + (total_output * NANO_OUT / 1e6)
    grand_52 = (total_input * GPT52_IN / 1e6) + (total_output * GPT52_OUT / 1e6)
    
    print("\n" + "="*40)
    print(f"GRAND TOTAL (16 Predictions)")
    print(f"Total Input: {total_input}")
    print(f"Total Output: {total_output}")
    print(f"GPT-5-Nano Total: ${grand_nano:.6f}")
    print(f"GPT-5.2 Total:    ${grand_52:.6f}")
    print(f"Ratio: GPT-5.2 is {grand_52/grand_nano:.1f}x more expensive")
    print("="*40)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        calculate_costs(sys.argv[1])
