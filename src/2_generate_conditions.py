"""
2_generate_conditions.py — Phase 2: Generate all 3 prompt conditions for 48 tasks.

Condition A: raw unstructured developer prompt (baseline)
Condition B: deterministic local cleaning (filler removal, contraction expansion, normalization)
Condition C: Groq Llama 3.3 70B → DevPrompt structured JSON

Output: data/conditions_all.json
Usage:  python src/2_generate_conditions.py
"""

import sys, os, json, re, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.utils.api_clients import generate_condition_c

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

# ---------------------------------------------------------------------------
# Condition B — deterministic local cleaning pipeline
# ---------------------------------------------------------------------------

# Filler words to strip (word-boundary anchored)
_FILLERS = re.compile(
    r'\b(um+|uh+|like|you know|basically|okay so|ok so|so like|so yeah|'
    r'so basically|you know what|i mean|kind of|kinda|sort of|right|alright|'
    r'well|yeah|yep|nope|hmm+|hm+)\b',
    flags=re.IGNORECASE
)

# Contractions → expanded forms
_CONTRACTIONS = {
    "don't": "do not", "doesn't": "does not", "didn't": "did not",
    "can't": "cannot", "couldn't": "could not", "shouldn't": "should not",
    "wouldn't": "would not", "won't": "will not", "isn't": "is not",
    "aren't": "are not", "wasn't": "was not", "weren't": "were not",
    "haven't": "have not", "hasn't": "has not", "hadn't": "had not",
    "i'm": "I am", "i've": "I have", "i'll": "I will", "i'd": "I would",
    "it's": "it is", "it'll": "it will", "that's": "that is",
    "there's": "there is", "they're": "they are", "they've": "they have",
    "they'll": "they will", "we're": "we are", "we've": "we have",
    "we'll": "we will", "you're": "you are", "you've": "you have",
    "you'll": "you will", "let's": "let us", "what's": "what is",
    "who's": "who is", "how's": "how is", "where's": "where is",
}
_CONTRACTION_RE = re.compile(
    r'\b(' + '|'.join(re.escape(k) for k in _CONTRACTIONS.keys()) + r')\b',
    flags=re.IGNORECASE
)


def clean_condition_b(raw: str) -> str:
    """
    Deterministic Condition B cleaning pipeline:
    1. Lowercase
    2. Expand contractions
    3. Remove filler words
    4. Collapse multiple spaces / strip
    5. Capitalize first letter, ensure ends with period
    """
    text = raw.lower()

    # Expand contractions (case-insensitive match, preserve expansion case)
    def replace_contraction(m):
        return _CONTRACTIONS.get(m.group(0).lower(), m.group(0))
    text = _CONTRACTION_RE.sub(replace_contraction, text)

    # Remove fillers
    text = _FILLERS.sub('', text)

    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Capitalize first letter
    if text:
        text = text[0].upper() + text[1:]

    # Ensure ends with period
    if text and text[-1] not in '.!?':
        text += '.'

    return text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Load tasks_master.json
    master_path = os.path.join(DATA_DIR, 'tasks_master.json')
    with open(master_path, encoding='utf-8') as f:
        tasks = json.load(f)
    print(f"Loaded {len(tasks)} tasks from tasks_master.json")

    output = []
    failed_c = []

    for i, task in enumerate(tasks):
        tid = task['task_id']
        raw = task['raw_utterance']
        print(f"\n[{i+1:02d}/48] {tid}")

        # --- Condition A: passthrough ---
        cond_a = raw
        print(f"  A: {cond_a[:80]}")

        # --- Condition B: cleaned plain text ---
        cond_b = clean_condition_b(raw)
        print(f"  B: {cond_b[:80]}")

        # --- Condition C: Groq structured JSON ---
        print(f"  C: calling Groq...", end='', flush=True)
        try:
            cond_c = generate_condition_c(raw)
            if '_parse_error' in cond_c:
                print(f" PARSE ERROR -> flagged")
                failed_c.append(tid)
            else:
                print(f" intent={cond_c.get('intent')} conf={cond_c.get('confidence_score')}")
        except Exception as e:
            print(f" FAILED: {e}")
            cond_c = {
                "raw_utterance": raw, "normalized": raw,
                "intent": "unknown", "confidence_score": 0.0,
                "entities": {"error_type": None, "component": None, "language": None, "framework": None},
                "_api_error": str(e)
            }
            failed_c.append(tid)

        output.append({
            "task_id": tid,
            "intent": task['intent'],
            "condition_a": cond_a,
            "condition_b": cond_b,
            "condition_c": cond_c,
        })

        # Rate-limit buffer between Groq calls (free tier)
        time.sleep(0.5)

    # Save
    out_path = os.path.join(DATA_DIR, 'conditions_all.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"PHASE 2 COMPLETE")
    print(f"  conditions_all.json : {len(output)} tasks")
    print(f"  Condition C errors  : {len(failed_c)}")
    if failed_c:
        print(f"  Failed tasks        : {failed_c}")
    print(f"  Saved -> {out_path}")
    print(f"{'='*60}")
    print(f"\nNEXT: python src/3_run_experiment.py")


if __name__ == '__main__':
    main()
