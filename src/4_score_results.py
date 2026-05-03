"""
4_score_results.py — Phase 4: Scoring experimental results.

Calculates:
1. Intent Preservation Score (Cosine Similarity)
2. Agentic Metrics (Tool F1, Precision, Recall, Redundancy)
3. Token Efficiency (Tokens per call)

Results are stored in a 'scores' table in results.db.
"""

import sys, os, json, sqlite3, re
import numpy as np
from typing import List, Dict, Any
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
    FOREIGN KEY(run_id) REFERENCES results(run_id)
);
"""

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(SCHEMA_SCORES)
    conn.commit()
    return conn

def load_tasks_master():
    with open(MASTER_PATH, encoding='utf-8') as f:
        data = json.load(f)
    return {t['task_id']: t for t in data}

def score_results():
    conn = get_db()
    tasks_map = load_tasks_master()
    
    query = """
        SELECT r.run_id, r.task_id, r.response, r.tool_calls_json
        FROM results r
        LEFT JOIN scores s ON r.run_id = s.run_id
        WHERE r.error IS NULL AND r.response IS NOT NULL
    """
    results = conn.execute(query).fetchall()
    print(f"Scoring {len(results)} results...")
    
    # Pre-calculate Intent and Agentic metrics synchronously
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
        
    print(f"Pre-calculated intent & agentic metrics for {len(scored_data)} items. Now fetching Hallucination via OpenAI...")
    
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    final_rows = []
    with ThreadPoolExecutor(max_workers=15) as executor:
        future_to_data = {
            executor.submit(judge_hallucination, item[1], item[2]): item 
            for item in scored_data
        }
        
        count = 0
        for future in as_completed(future_to_data):
            item = future_to_data[future]
            run_id, task, response, intent_score, agentic = item
            hallucination_score = future.result()
            
            final_rows.append((
                run_id, intent_score,
                agentic['tool_precision'], agentic['tool_recall'], agentic['tool_f1'],
                agentic['total_tool_calls'], agentic['redundant_calls'],
                1 if agentic['first_call_correct'] else 0,
                1 if agentic['minimum_requirements_met'] else 0,
                hallucination_score
            ))
            
            count += 1
            if count % 50 == 0:
                print(f"  Processed {count}/{len(scored_data)} hallucination scores...")

    # Batch Insert
    conn.executemany("""
        INSERT OR REPLACE INTO scores (
            run_id, intent_preservation, tool_precision, tool_recall, tool_f1,
            total_tool_calls, redundant_calls, first_call_correct, min_req_met, hallucination_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, final_rows)
    
    conn.commit()
    print(f"Finished scoring {len(final_rows)} results.")
    
    # Generate a quick summary
    print("\n=== PRELIMINARY SUMMARY BY CONDITION ===")
    summary_query = """
        SELECT r.condition, 
               AVG(s.intent_preservation) as avg_intent,
               AVG(s.tool_f1) as avg_f1,
               AVG(s.hallucination_score) as avg_hallucination,
               AVG(r.total_tokens) as avg_tokens
        FROM results r
        JOIN scores s ON r.run_id = s.run_id
        GROUP BY r.condition
    """
    summary = conn.execute(summary_query).fetchall()
    print(f"{'Cond':<6} | {'Intent':<8} | {'Tool F1':<8} | {'Halluc':<6} | {'Tokens':<8}")
    print("-" * 50)
    for cond, intent, f1, halluc, tokens in summary:
        print(f"{cond:<6} | {intent or 0:.4f} | {f1 or 0:.4f} | {halluc or 0:.4f} | {tokens or 0:.1f}")
        
    print("\n=== PRELIMINARY SUMMARY BY MODEL ===")
    model_query = """
        SELECT r.model, 
               AVG(s.intent_preservation) as avg_intent,
               AVG(s.tool_f1) as avg_f1
        FROM results r
        JOIN scores s ON r.run_id = s.run_id
        GROUP BY r.model
    """
    model_summary = conn.execute(model_query).fetchall()
    print(f"{'Model':<25} | {'Intent':<8} | {'Tool F1':<8}")
    print("-" * 50)
    for model, intent, f1 in model_summary:
        print(f"{model:<25} | {intent or 0:.4f} | {f1 or 0:.4f}")

    conn.close()

if __name__ == "__main__":
    score_results()
