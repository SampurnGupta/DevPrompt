"""
3_run_experiment.py - Phase 3: Main experiment loop.

Runs 48 tasks x 3 conditions x 3 models = 432 API calls.
Stores every result to SQLite data/results.db with checkpointing.
Loop order: model -> task -> condition (one model finishes before next starts).

Models & Rate Limits (free tier):
  gemini   : gemini-2.0-flash        15 RPM / 1500 RPD  -> 4s delay
  groq     : llama-3.3-70b-versatile 30 RPM / 100K TPD  -> 2s delay
  cerebras : gpt-oss-120b            30 RPM / 1M  TPD   -> 2s delay

Usage:
    python src/3_run_experiment.py                       # full run, all models
    python src/3_run_experiment.py --pilot               # 5 tasks x Groq only
    python src/3_run_experiment.py --resume              # skip already-completed run_ids
    python src/3_run_experiment.py --model groq          # one model only
    python src/3_run_experiment.py --model cerebras --resume
"""

import sys, os, json, time, sqlite3, argparse, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.utils.api_clients import MODEL_REGISTRY
from src.utils.tool_extraction import extract_tool_calls, validate_tool_calls, TOOL_SYSTEM_PROMPT

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DB_PATH  = os.path.join(DATA_DIR, 'results.db')

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS results (
    run_id              TEXT PRIMARY KEY,
    task_id             TEXT NOT NULL,
    intent              TEXT NOT NULL,
    condition           TEXT NOT NULL,
    model               TEXT NOT NULL,
    timestamp           TEXT NOT NULL,
    prompt              TEXT,
    response            TEXT,
    input_tokens        INTEGER,
    output_tokens       INTEGER,
    total_tokens        INTEGER,
    tool_calls_json     TEXT,
    tool_sequence       TEXT,
    total_tool_calls    INTEGER,
    execution_time_sec  REAL,
    error               TEXT
);
"""

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(SCHEMA)
    conn.commit()
    return conn

def get_completed_run_ids(conn):
    rows = conn.execute("SELECT run_id FROM results WHERE error IS NULL").fetchall()
    return {r[0] for r in rows}

def insert_result(conn, row: dict):
    conn.execute("""
        INSERT OR REPLACE INTO results
        (run_id, task_id, intent, condition, model, timestamp, prompt, response,
         input_tokens, output_tokens, total_tokens, tool_calls_json, tool_sequence,
         total_tool_calls, execution_time_sec, error)
        VALUES
        (:run_id, :task_id, :intent, :condition, :model, :timestamp, :prompt, :response,
         :input_tokens, :output_tokens, :total_tokens, :tool_calls_json, :tool_sequence,
         :total_tool_calls, :execution_time_sec, :error)
    """, row)
    conn.commit()

# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def build_prompt(task: dict, condition: str, conditions_data: dict) -> str:
    cdata = conditions_data[task['task_id']]
    if condition == 'a':
        user_input = cdata['condition_a']
        label = "Developer request:"
    elif condition == 'b':
        user_input = cdata['condition_b']
        label = "Developer request:"
    else:
        user_input = json.dumps(cdata['condition_c'], indent=2)
        label = "Structured developer request (JSON):"
    return f"{label}\n\n{user_input}"

# ---------------------------------------------------------------------------
# Rate-limit delays
# ---------------------------------------------------------------------------

RATE_DELAYS = {
    'gemini':   1.5,   # OpenRouter free tier — generous RPM, no daily limit
    'groq':     2.1,   # 30 RPM free tier (conservative after TPD hit)
    'cerebras': 2.1,   # 30 RPM free tier
}

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run_experiment(pilot: bool = False, resume: bool = False, only_model: str = None):
    conditions_path = os.path.join(DATA_DIR, 'conditions_all.json')
    master_path     = os.path.join(DATA_DIR, 'tasks_master.json')

    with open(conditions_path, encoding='utf-8') as f:
        conditions_list = json.load(f)
    with open(master_path, encoding='utf-8') as f:
        tasks_master = json.load(f)

    conditions_data = {c['task_id']: c for c in conditions_list}

    conn = get_db()
    completed = get_completed_run_ids(conn) if resume else set()
    if resume:
        print(f"[Resume] {len(completed)} runs already done, skipping.")

    tasks      = tasks_master[:5] if pilot else tasks_master
    conditions = ['a', 'b', 'c']

    if only_model:
        models = [only_model]
    elif pilot:
        models = ['groq']
    else:
        models = list(MODEL_REGISTRY.keys())

    total = len(tasks) * len(conditions) * len(models)
    mode  = "PILOT" if pilot else f"MODEL={only_model}" if only_model else "FULL"
    print(f"[{mode}] {len(tasks)} tasks x {len(conditions)} conds x {len(models)} models = {total} calls")

    call_num  = 0
    errors    = 0
    start_all = time.time()

    # Model-first loop: finish one model entirely before moving to next
    for model_name in models:
        model_fn = MODEL_REGISTRY[model_name]
        delay    = RATE_DELAYS.get(model_name, 1.0)
        print(f"\n--- {model_name.upper()} (delay={delay}s) ---")

        for task in tasks:
            tid = task['task_id']
            for condition in conditions:
                call_num += 1
                run_id = f"{tid}_cond{condition}_{model_name}"

                if run_id in completed:
                    print(f"  [{call_num:03d}] SKIP {run_id}")
                    continue

                prompt = build_prompt(task, condition, conditions_data)
                print(f"  [{call_num:03d}] {run_id} ... ", end='', flush=True)
                t0 = time.time()

                try:
                    result  = model_fn(prompt, system_prompt=TOOL_SYSTEM_PROMPT,
                                       temperature=0.3, max_tokens=2048)
                    elapsed = time.time() - t0
                    ext     = extract_tool_calls(result['response'])
                    val     = validate_tool_calls(ext)

                    insert_result(conn, {
                        'run_id': run_id, 'task_id': tid, 'intent': task['intent'],
                        'condition': condition, 'model': model_name,
                        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                        'prompt': prompt, 'response': result['response'],
                        'input_tokens': result['input_tokens'],
                        'output_tokens': result['output_tokens'],
                        'total_tokens': result['input_tokens'] + result['output_tokens'],
                        'tool_calls_json': json.dumps(ext),
                        'tool_sequence': json.dumps(val['tool_sequence']),
                        'total_tool_calls': val['total_calls'],
                        'execution_time_sec': round(elapsed, 3),
                        'error': None,
                    })
                    print(f"OK ({elapsed:.1f}s | {result['input_tokens']}+{result['output_tokens']}tok | tools={val['tool_sequence']})")

                except Exception as e:
                    elapsed = time.time() - t0
                    errors += 1
                    err_msg = str(e)[:500]
                    insert_result(conn, {
                        'run_id': run_id, 'task_id': tid, 'intent': task['intent'],
                        'condition': condition, 'model': model_name,
                        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                        'prompt': prompt, 'response': None,
                        'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0,
                        'tool_calls_json': '[]', 'tool_sequence': '[]',
                        'total_tool_calls': 0,
                        'execution_time_sec': round(elapsed, 3),
                        'error': err_msg,
                    })
                    print(f"ERROR: {err_msg[:80]}")

                time.sleep(delay)

    conn.close()
    elapsed_total = time.time() - start_all
    print(f"\n{'='*60}")
    print(f"DONE | calls={call_num} | errors={errors} | time={elapsed_total/60:.1f}min")
    print(f"{'='*60}")

    # Summary from DB
    conn2 = sqlite3.connect(DB_PATH)
    total_ok  = conn2.execute("SELECT COUNT(*) FROM results WHERE error IS NULL").fetchone()[0]
    total_err = conn2.execute("SELECT COUNT(*) FROM results WHERE error IS NOT NULL").fetchone()[0]
    conn2.close()
    print(f"DB totals: {total_ok} success, {total_err} errors")
    print(f"\nNEXT: python src/4_score_results.py")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pilot',  action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--model',  type=str, default=None, choices=['gemini','groq','cerebras'])
    args = parser.parse_args()
    run_experiment(pilot=args.pilot, resume=args.resume, only_model=args.model)
