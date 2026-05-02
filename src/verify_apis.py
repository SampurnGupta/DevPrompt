"""
verify_apis.py — Quick smoke test for all 4 API connections.
Run: python src/verify_apis.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

SYSTEM = "You are a helpful assistant."
PING = "Reply with exactly: OK"

results = {}

# --- Gemini ---
try:
    from src.utils.api_clients import call_gemini
    r = call_gemini(PING, system_prompt=SYSTEM, max_tokens=10)
    results['gemini'] = ('PASS', r['response'].strip()[:30], r['input_tokens'], r['output_tokens'])
except Exception as e:
    results['gemini'] = ('FAIL', str(e)[:80])

# --- Groq ---
try:
    from src.utils.api_clients import call_groq
    r = call_groq(PING, system_prompt=SYSTEM, max_tokens=10)
    results['groq'] = ('PASS', r['response'].strip()[:30], r['input_tokens'], r['output_tokens'])
except Exception as e:
    results['groq'] = ('FAIL', str(e)[:80])

# --- Cerebras ---
try:
    from src.utils.api_clients import call_cerebras
    r = call_cerebras(PING, system_prompt=SYSTEM, max_tokens=10)
    results['cerebras'] = ('PASS', r['response'].strip()[:30], r['input_tokens'], r['output_tokens'])
except Exception as e:
    results['cerebras'] = ('FAIL', str(e)[:80])

# --- OpenAI Judge ---
try:
    from src.utils.api_clients import call_openai_judge
    r = call_openai_judge(PING, max_tokens=10)
    results['openai'] = ('PASS', r['response'].strip()[:30], r['input_tokens'], r['output_tokens'])
except Exception as e:
    results['openai'] = ('FAIL', str(e)[:80])

print("\n=== API Verification Results ===")
for name, res in results.items():
    status = res[0]
    detail = res[1]
    if status == 'PASS':
        print(f"  [{status}] {name:10s} -> '{detail}' | in={res[2]} out={res[3]}")
    else:
        print(f"  [{status}] {name:10s} -> {detail}")
