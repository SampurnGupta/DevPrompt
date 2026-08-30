"""
4_score_results.py — Phase 4: Scoring experimental results.

Calculates:
1. Intent Preservation Score (Cosine Similarity)
2. Agentic Metrics (Tool F1, Precision, Recall, Redundancy, etc. using best-matching sequence)
3. Token Efficiency (Tokens per call)
4. LLM-as-judge Intent Fidelity Score (0-3 scale)
5. Functional Correctness (Pass@1 via pytest execution)

Results are stored in a 'scores' table in results.db.
"""

import sys, os, json, sqlite3, re, subprocess, argparse
import numpy as np
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('.env')

_openai_client = None
def get_openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in env")
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client

def judge_hallucination(task, response):
    try:
        client = get_openai_client()
        judge_prompt = f"""
You are evaluating an LLM response for hallucinations.
TASK: {task['gold_standard']['functional_output_description']}
RESPONSE: {response}

Rubric:
- Score 0: No hallucination — all claims verifiable, uncertainties stated
- Score 1: Minor — 1-2 unverifiable minor details, doesn't affect correctness
- Score 2: Major — invented APIs/methods, confidently wrong facts, would break code

Output ONLY valid JSON: {{"score": 0, "reasoning": "...", "hallucinated_claims": []}}
"""
        result = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": judge_prompt}],
            temperature=0.1, max_tokens=300
        )
        content = result.choices[0].message.content
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            return int(json.loads(match.group(0)).get('score', 0))
        return 0
    except Exception as e:
        print(f"Hallucination API error: {e}")
        return 0

def judge_intent_fidelity(task, response):
    try:
        client = get_openai_client()
        ref = task['gold_standard']['intent_preservation_reference']
        judge_prompt = f"""
You are evaluating an LLM response for developer intent fidelity.
A developer asked: "{ref}"
The AI responded: "{response[:1500]}"

Rubric:
Does the response address the developer's request?
- Score 0: Not at all — completely misses the point, ignores the core request
- Score 1: Partially — attempts the request but misses key constraints or is incomplete
- Score 2: Mostly — addresses the core request and satisfies most constraints
- Score 3: Fully — completely and correctly satisfies the request and all constraints

Output ONLY valid JSON: {{"score": X, "reasoning": "..."}}
"""
        result = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": judge_prompt}],
            temperature=0.1, max_tokens=300
        )
        content = result.choices[0].message.content
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            return int(json.loads(match.group(0)).get('score', 0))
        return 0
    except Exception as e:
        print(f"Intent Fidelity judge API error: {e}")
        return 0

def extract_first_code_block(text: str) -> str:
    if not text:
        return ""
    match = re.search(r'```(?:python|javascript|js|bash|sh|sql)?\n(.*?)```', text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()

def run_functional_test(task_id: str, run_id: str, response: str) -> Optional[bool]:
    scratch_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scratch')
    os.makedirs(scratch_dir, exist_ok=True)
    
    code = extract_first_code_block(response)
    solution_path = os.path.join(scratch_dir, f"{run_id}_solution.py")
    with open(solution_path, 'w', encoding='utf-8') as f:
        f.write(code)
        
    test_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests', f"{task_id}_test.py")
    if not os.path.exists(test_file):
        return None
        
    env = os.environ.copy()
    env['CURRENT_RUN_ID'] = run_id
    env['CURRENT_SOLUTION_PATH'] = solution_path
    
    try:
        res = subprocess.run(
            [sys.executable, '-m', 'pytest', test_file, '-q', '--tb=no'],
            capture_output=True, text=True, timeout=10, env=env
        )
        return res.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"Timeout running test for {run_id}")
        return False
    except Exception as e:
        print(f"Error running test for {run_id}: {e}")
        return False

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.metrics import (
    compute_intent_preservation,
    compute_agentic_metrics,
    describe
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DB_PATH  = os.path.join(DATA_DIR, 'results.db')
MASTER_PATH = os.path.join(DATA_DIR, 'tasks_master.json')

SCHEMA_SCORES = """
CREATE TABLE IF NOT EXISTS scores (
    run_id              TEXT PRIMARY KEY,
    intent_preservation REAL,
    tool_precision      REAL,
    tool_recall         REAL,
    tool_f1             REAL,
    total_tool_calls    INTEGER,
    redundant_calls     INTEGER,
    first_call_correct  INTEGER,
    min_req_met         INTEGER,
    hallucination_score INTEGER,
    intent_fidelity_score INTEGER DEFAULT NULL,
    functional_correct  BOOLEAN DEFAULT NULL,
    FOREIGN KEY(run_id) REFERENCES results(run_id)
);
"""

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(SCHEMA_SCORES)
    # Validate / alter schema dynamic check
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(scores)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'intent_fidelity_score' not in columns:
        conn.execute("ALTER TABLE scores ADD COLUMN intent_fidelity_score INTEGER DEFAULT NULL")
    if 'functional_correct' not in columns:
        conn.execute("ALTER TABLE scores ADD COLUMN functional_correct BOOLEAN DEFAULT NULL")
    conn.commit()
    return conn

def load_tasks_master():
    with open(MASTER_PATH, encoding='utf-8') as f:
        data = json.load(f)
    return {t['task_id']: t for t in data}

def score_results(rescore_tools: bool = False, rescore_intent: bool = False, rescore_functional: bool = False, filter_model: str = None):
    conn = get_db()
    tasks_map = load_tasks_master()
    
    if rescore_tools or rescore_intent or rescore_functional:
        query = """
            SELECT r.run_id, r.task_id, r.response, r.tool_calls_json
            FROM results r
            WHERE r.error IS NULL AND r.response IS NOT NULL
        """
        if filter_model:
            query += f" AND r.model = '{filter_model}'"
        print(f"Rescore mode active (tools={rescore_tools}, intent={rescore_intent}, functional={rescore_functional}, model={filter_model})")
    else:
        # Standard run: skip already scored runs (Fix 1.5)
        query = """
            SELECT r.run_id, r.task_id, r.response, r.tool_calls_json
            FROM results r
            LEFT JOIN scores s ON r.run_id = s.run_id
            WHERE r.error IS NULL AND r.response IS NOT NULL AND s.run_id IS NULL
        """
        print("Standard scoring mode active (skipping already scored runs)")
        
    results = conn.execute(query).fetchall()
    print(f"Found {len(results)} rows to process.")
    
    if not results:
        conn.close()
        print("No new results to score.")
        return

    # Backup logic for rescore mode
    if rescore_tools or rescore_intent or rescore_functional:
        print("Creating backup table scores_original if not exists...")
        try:
            # Check if scores_original exists
            exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scores_original'").fetchone()
            if not exists:
                conn.execute("CREATE TABLE scores_original AS SELECT * FROM scores")
                conn.commit()
                print("Backup successful.")
            else:
                print("scores_original backup already exists, skipping backup.")
        except Exception as e:
            print(f"Backup warning: {e}")

    # Ensure all run_ids exist in scores table before we run UPDATEs
    for run_id, _, _, _ in results:
        exists = conn.execute("SELECT 1 FROM scores WHERE run_id = ?", (run_id,)).fetchone()
        if not exists:
            conn.execute("INSERT INTO scores (run_id) VALUES (?)", (run_id,))
    conn.commit()

    if rescore_tools:
        print("Recalculating agentic tool metrics for all matching runs...")
        for run_id, task_id, response, tool_calls_json in results:
            task = tasks_map.get(task_id)
            if not task: continue
            tool_calls = json.loads(tool_calls_json)
            extracted_tool_names = [tc['tool'] for tc in tool_calls if 'tool' in tc]
            agentic = compute_agentic_metrics(task, extracted_tool_names)
            
            conn.execute("""
                UPDATE scores SET
                    tool_precision = ?,
                    tool_recall = ?,
                    tool_f1 = ?,
                    total_tool_calls = ?,
                    redundant_calls = ?,
                    first_call_correct = ?,
                    min_req_met = ?
                WHERE run_id = ?
            """, (
                agentic['tool_precision'], agentic['tool_recall'], agentic['tool_f1'],
                agentic['total_tool_calls'], agentic['redundant_calls'],
                1 if agentic['first_call_correct'] else 0,
                1 if agentic['minimum_requirements_met'] else 0,
                run_id
            ))
        conn.commit()
        print("Agentic tool metrics update complete.")

    if rescore_functional:
        print("Running Pass@1 functional tests for applicable tasks...")
        for run_id, task_id, response, _ in results:
            task = tasks_map.get(task_id)
            if not task or not task.get('has_unit_test', False):
                continue
            
            passed = run_functional_test(task_id, run_id, response)
            conn.execute("""
                UPDATE scores SET functional_correct = ? WHERE run_id = ?
            """, (passed, run_id))
        conn.commit()
        print("Functional correctness update complete.")

    if rescore_intent:
        print("Running LLM intent fidelity judge for all results...")
        from concurrent.futures import ThreadPoolExecutor, as_completed
        scored_data = []
        for run_id, task_id, response, _ in results:
            task = tasks_map.get(task_id)
            if not task: continue
            scored_data.append((run_id, task, response))
            
        with ThreadPoolExecutor(max_workers=15) as executor:
            future_to_run = {
                executor.submit(judge_intent_fidelity, item[1], item[2]): item[0]
                for item in scored_data
            }
            count = 0
            for future in as_completed(future_to_run):
                run_id = future_to_run[future]
                score = future.result()
                conn.execute("UPDATE scores SET intent_fidelity_score = ? WHERE run_id = ?", (score, run_id))
                count += 1
                if count % 50 == 0:
                    print(f"  Processed {count}/{len(scored_data)} intent fidelity scores...")
        conn.commit()
        print("Intent fidelity update complete.")

    # Standard run scoring logic
    if not (rescore_tools or rescore_intent or rescore_functional):
        scored_data = []
        for run_id, task_id, response, tool_calls_json in results:
            task = tasks_map.get(task_id)
            if not task: continue
                
            gold_embedding = task['gold_standard']['intent_preservation_embedding']
            intent_score = compute_intent_preservation(gold_embedding, response)
            
            tool_calls = json.loads(tool_calls_json)
            extracted_tool_names = [tc['tool'] for tc in tool_calls if 'tool' in tc]
            agentic = compute_agentic_metrics(task, extracted_tool_names)
            
            scored_data.append((run_id, task, response, intent_score, agentic))
            
        print(f"Pre-calculated metrics for {len(scored_data)} new items. Running judges via ThreadPoolExecutor...")
        
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        final_rows = []
        with ThreadPoolExecutor(max_workers=15) as executor:
            # We run both hallucination and intent fidelity judges
            future_to_data = {
                executor.submit(lambda t=item[1], r=item[2]: (judge_hallucination(t, r), judge_intent_fidelity(t, r))): item 
                for item in scored_data
            }
            
            count = 0
            for future in as_completed(future_to_data):
                item = future_to_data[future]
                run_id, task, response, intent_score, agentic = item
                hallucination_score, intent_fidelity = future.result()
                
                # Check functional test if applicable
                passed = None
                if task.get('has_unit_test', False):
                    passed = run_functional_test(task['task_id'], run_id, response)
                
                conn.execute("""
                    UPDATE scores SET
                        intent_preservation = ?,
                        tool_precision = ?,
                        tool_recall = ?,
                        tool_f1 = ?,
                        total_tool_calls = ?,
                        redundant_calls = ?,
                        first_call_correct = ?,
                        min_req_met = ?,
                        hallucination_score = ?,
                        intent_fidelity_score = ?,
                        functional_correct = ?
                    WHERE run_id = ?
                """, (
                    intent_score,
                    agentic['tool_precision'], agentic['tool_recall'], agentic['tool_f1'],
                    agentic['total_tool_calls'], agentic['redundant_calls'],
                    1 if agentic['first_call_correct'] else 0,
                    1 if agentic['minimum_requirements_met'] else 0,
                    hallucination_score,
                    intent_fidelity,
                    passed,
                    run_id
                ))
                
                count += 1
                if count % 50 == 0:
                    print(f"  Processed {count}/{len(scored_data)} judges...")
        conn.commit()
        print("Standard scoring complete.")
    
    # Generate a quick summary
    print("\n=== PRELIMINARY SUMMARY BY CONDITION ===")
    summary_query = """
        SELECT r.condition, 
               AVG(s.intent_fidelity_score) as avg_intent_fidelity,
               AVG(s.tool_f1) as avg_f1,
               AVG(s.hallucination_score) as avg_hallucination,
               AVG(r.total_tokens) as avg_tokens
        FROM results r
        JOIN scores s ON r.run_id = s.run_id
        GROUP BY r.condition
    """
    summary = conn.execute(summary_query).fetchall()
    print(f"{'Cond':<6} | {'Fidelity':<8} | {'Tool F1':<8} | {'Halluc':<6} | {'Tokens':<8}")
    print("-" * 50)
    for cond, fidelity, f1, halluc, tokens in summary:
        print(f"{cond:<6} | {fidelity or 0:.4f} | {f1 or 0:.4f} | {halluc or 0:.4f} | {tokens or 0:.1f}")
        
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--rescore-tools', action='store_true', help="Recompute agentic tool metrics from results table without API calls")
    parser.add_argument('--rescore-intent', action='store_true', help="Re-run LLM intent fidelity judge for all results")
    parser.add_argument('--rescore-functional', action='store_true', help="Re-run Pass@1 pytest execution on extracted code blocks")
    parser.add_argument('--model', type=str, default=None, choices=['gemini', 'groq', 'cerebras'], help="Filter to specific model")
    args = parser.parse_args()
    
    score_results(
        rescore_tools=args.rescore_tools,
        rescore_intent=args.rescore_intent,
        rescore_functional=args.rescore_functional,
        filter_model=args.model
    )
