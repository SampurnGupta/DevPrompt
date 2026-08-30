"""
5_analyze_results.py - Phase 5: Statistical Analysis for DevPrompt Paper

Generates the final tables and figures for the research paper:
1. Overall Performance by Condition (A vs B vs C)
2. Model Performance by Condition (A vs B vs C across Gemini, Groq, Cerebras)
3. Performance by Intent Category
4. Paired t-tests, Cohen's d, Bonferroni correction, and CIs
5. One-way ANOVA per intent, McNemar's test, K-Means silhouette scores
"""

import sqlite3
import pandas as pd
import os
import sys
import json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scipy import stats
from src.utils.metrics import cohens_d, confidence_interval_95

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DB_PATH  = os.path.join(DATA_DIR, 'results.db')

def calc_tool_halluc_rate(tool_calls_json):
    try:
        calls = json.loads(tool_calls_json)
        if not calls:
            return 0.0
        invalid = sum(1 for c in calls if not c.get('valid', True))
        return invalid / len(calls)
    except:
        return 0.0

def load_tasks_map():
    master_path = os.path.join(DATA_DIR, 'tasks_master.json')
    if not os.path.exists(master_path):
        return {}
    with open(master_path, encoding='utf-8') as f:
        data = json.load(f)
    return {t['task_id']: t for t in data}

def compute_row_kendall_tau(row, tasks_map):
    task_id = row['task_id']
    task = tasks_map.get(task_id)
    if not task:
        return None
    expected_tools = task['gold_standard']['expected_tools']
    try:
        calls = json.loads(row['tool_calls_json'])
        actual_tools = [c['tool'] for c in calls if c.get('valid', True)]
    except:
        actual_tools = []
    
    if len(actual_tools) < 2:
        return None
        
    expected_ranks = {tool: idx for idx, tool in enumerate(expected_tools)}
    actual_ranks = [expected_ranks.get(tool, len(expected_tools)) for tool in actual_tools]
    
    tau, _ = stats.kendalltau(actual_ranks, sorted(actual_ranks))
    if pd.isna(tau):
        return 0.0
    return tau

def bootstrap_cpstc(sub_df, n_iterations=1000):
    cpstc_values = []
    n = len(sub_df)
    if n == 0:
        return (np.nan, np.nan)
    np.random.seed(42)
    for _ in range(n_iterations):
        sample = sub_df.sample(n=n, replace=True)
        successes = sample['min_req_met'].sum()
        tokens = sample['total_tokens'].sum()
        if successes > 0:
            cpstc_values.append(tokens / successes)
    if not cpstc_values:
        return (np.nan, np.nan)
    lower = np.percentile(cpstc_values, 2.5)
    upper = np.percentile(cpstc_values, 97.5)
    return (lower, upper)

def compute_silhouette_scores():
    print("=== K-Means Silhouette Scores (k=6) ===")
    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics import silhouette_score
        from sklearn.cluster import KMeans
        
        dataset_path = os.path.join(os.path.dirname(DATA_DIR), 'devflow_dataset.csv')
        if not os.path.exists(dataset_path):
            print("  devflow_dataset.csv not found, skipping silhouette.")
            return
            
        raw_df = pd.read_csv(dataset_path)
        raw_df.columns = [c.strip().lower() for c in raw_df.columns]
        
        # Keep only unique non-empty columns
        import re as _re
        clean_cols = [c for c in raw_df.columns if not _re.search(r'\.\d+$', c)]
        raw_df = raw_df[clean_cols]
        
        model = SentenceTransformer('all-MiniLM-L6-v2')
        intents = ['debug', 'generate', 'refactor', 'explain', 'scaffold', 'test', 'document']
        
        for intent in intents:
            sub = raw_df[raw_df['intent'] == intent].reset_index(drop=True)
            if len(sub) < 12: continue
            
            embs = model.encode(sub['utterance'].tolist())
            km = KMeans(n_clusters=6, random_state=42, n_init=10)
            labels = km.fit_predict(embs)
            score = silhouette_score(embs, labels)
            print(f"  Intent '{intent:<12}': Silhouette Score = {score:.4f}")
    except Exception as e:
        print(f"  Silhouette error: {e}")
    print()

def run_per_intent_anova(df):
    print("=== Table 4: One-way ANOVA per Intent Category ===")
    print(f"{'Intent':<12} | {'F-Statistic':<12} | {'p-value':<12}")
    print("-" * 42)
    for intent in df['intent'].unique():
        sub = df[df['intent'] == intent]
        grp_a = sub[sub['condition'] == 'a']['tool_f1']
        grp_b = sub[sub['condition'] == 'b']['tool_f1']
        grp_c = sub[sub['condition'] == 'c']['tool_f1']
        
        if len(grp_a) > 2 and len(grp_b) > 2 and len(grp_c) > 2:
            f_stat, p_val = stats.f_oneway(grp_a, grp_b, grp_c)
            print(f"{intent:<12} | {f_stat:<12.4f} | {p_val:<12.4g}")
        else:
            print(f"{intent:<12} | Insufficient data")
    print()

def run_mcnemars_test(df):
    print("=== McNemar's Test (Binary Success: Cond C vs Cond A) ===")
    try:
        pivot = df.pivot_table(index=['task_id', 'model'], columns='condition', values='min_req_met')
        a_succ = pivot['a'].dropna()
        c_succ = pivot['c'].dropna()
        common = a_succ.index.intersection(c_succ.index)
        a_val = a_succ.loc[common]
        c_val = c_succ.loc[common]
        
        yy = sum((a_val == 1) & (c_val == 1))
        yn = sum((a_val == 1) & (c_val == 0))
        ny = sum((a_val == 0) & (c_val == 1))
        nn = sum((a_val == 0) & (c_val == 0))
        
        table = [[yy, yn], [ny, nn]]
        
        from statsmodels.stats.contingency_tables import mcnemar
        res = mcnemar(table, exact=True)
        print(f"  Contingency Table (YY, YN, NY, NN): {table}")
        print(f"  McNemar exact p-value: {res.pvalue:.4g}")
    except Exception as e:
        print(f"  McNemar error: {e}")
    print()

def analyze_condition_b_hallucinations(df):
    print("=== Condition B Hallucination Advantage Deep-Dive ===")
    model_cond = df.pivot_table(index='model', columns='condition', values='hallucination_score', aggfunc='mean')
    print(model_cond)
    print("\n  Observed Deltas:")
    for model in model_cond.index:
        mean_a = model_cond.loc[model, 'a']
        mean_b = model_cond.loc[model, 'b']
        mean_c = model_cond.loc[model, 'c']
        print(f"    {model:<15} : A->B delta = {mean_b - mean_a:+.4f} | B->C delta = {mean_c - mean_b:+.4f}")
    print()

def analyze():
    if not os.path.exists(DB_PATH):
        print(f"Database not found: {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    
    query = """
        SELECT 
            r.run_id, r.task_id, r.intent, r.condition, r.model,
            s.intent_preservation, s.tool_precision, s.tool_recall, s.tool_f1,
            s.total_tool_calls, s.redundant_calls, s.first_call_correct, s.min_req_met, s.hallucination_score,
            s.intent_fidelity_score, s.functional_correct,
            r.input_tokens, r.output_tokens, r.total_tokens, r.execution_time_sec, r.tool_calls_json
        FROM results r
        JOIN scores s ON r.run_id = s.run_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if len(df) == 0:
        print("No scored results found in the database. Run 4_score_results.py first.")
        return
        
    print(f"Loaded {len(df)} scored results for analysis.\n")
    
    # Compute derived diagnostic metrics
    df['format_compliance'] = (df['total_tool_calls'] > 0).astype(float)
    df['tool_halluc_rate'] = df['tool_calls_json'].apply(calc_tool_halluc_rate)
    
    tasks_map = load_tasks_map()
    df['kendall_tau'] = df.apply(lambda r: compute_row_kendall_tau(r, tasks_map), axis=1)
    
    # 1. Overall Performance by Condition
    print("=== Table 1: Overall Performance by Condition ===")
    
    cond_stats = df.groupby('condition').agg(
        Intent_Fidelity=('intent_fidelity_score', 'mean'),
        Tool_F1=('tool_f1', 'mean'),
        Hallucination_Rate=('hallucination_score', 'mean'),
        First_Call_Acc=('first_call_correct', 'mean'),
        Min_Req_Met=('min_req_met', 'mean'),
        Format_Compliance=('format_compliance', 'mean'),
        Tool_Halluc_Rate=('tool_halluc_rate', 'mean'),
        Func_Correct_Rate=('functional_correct', 'mean'),
        Redundancy=('redundant_calls', 'mean'),
        Kendall_Tau=('kendall_tau', 'mean'),
        Avg_Tokens=('total_tokens', 'mean'),
        Avg_Output_Tokens=('output_tokens', 'mean'),
        Avg_Latency=('execution_time_sec', 'mean'),
        Total_Tokens_Sum=('total_tokens', 'sum'),
        Successful_Tasks=('min_req_met', 'sum')
    )
    cond_stats['CPSTC'] = cond_stats['Total_Tokens_Sum'] / cond_stats['Successful_Tasks']
    
    # Add Bootstrap CIs for CPSTC
    for cond in ['a', 'b', 'c']:
        sub = df[df['condition'] == cond]
        ci_lower, ci_upper = bootstrap_cpstc(sub)
        cond_stats.loc[cond, 'CPSTC_CI_lower'] = ci_lower
        cond_stats.loc[cond, 'CPSTC_CI_upper'] = ci_upper
        
    # Drop temp sum columns
    cond_stats = cond_stats.drop(columns=['Total_Tokens_Sum', 'Successful_Tasks']).round(4)
    print(cond_stats)
    cond_stats.to_csv(os.path.join(DATA_DIR, 'table1_condition_overall.csv'))
    print("\n")
    
    # Model-Stratified Table 1 (Task 4.9)
    print("=== Table 1 Variant: Overall Performance Grouped by Model & Condition ===")
    model_stratified = df.groupby(['model', 'condition']).agg(
        Intent_Fidelity=('intent_fidelity_score', 'mean'),
        Tool_F1=('tool_f1', 'mean'),
        Hallucination_Rate=('hallucination_score', 'mean'),
        First_Call_Acc=('first_call_correct', 'mean'),
        Min_Req_Met=('min_req_met', 'mean'),
        Format_Compliance=('format_compliance', 'mean'),
        Func_Correct_Rate=('functional_correct', 'mean'),
        Avg_Tokens=('total_tokens', 'mean')
    ).round(4)
    print(model_stratified)
    model_stratified.to_csv(os.path.join(DATA_DIR, 'table1_model_stratified.csv'))
    print("\n")
    
    # 2. Performance by Model and Condition
    print("=== Table 2: Performance by Model and Condition ===")
    model_cond_stats = df.pivot_table(
        index='model', 
        columns='condition', 
        values=['tool_f1', 'intent_fidelity_score', 'hallucination_score', 'functional_correct'],
        aggfunc='mean'
    ).round(4)
    print(model_cond_stats)
    model_cond_stats.to_csv(os.path.join(DATA_DIR, 'table2_model_condition.csv'))
    print("\n")
    
    # 3. Performance by Intent Category
    print("=== Table 3: Performance by Intent Category (Tool F1) ===")
    intent_stats = df.pivot_table(
        index='intent',
        columns='condition',
        values='tool_f1',
        aggfunc='mean'
    ).round(4)
    print(intent_stats)
    intent_stats.to_csv(os.path.join(DATA_DIR, 'table3_intent_category.csv'))
    print("\n")
    
    # 4. Statistical significance (Within-Subjects Paired t-tests)
    print("=== Statistical Analysis (Within-Subjects Paired t-tests) ===")
    pivot = df.pivot_table(index=['task_id', 'model'], columns='condition', values='tool_f1')
    
    pairs = [('a', 'c'), ('a', 'b'), ('b', 'c')]
    bonferroni_alpha = 0.05 / 12  # 3 pairs x 4 primary metrics
    
    for c1, c2 in pairs:
        grp1 = pivot[c1].dropna()
        grp2 = pivot[c2].dropna()
        common_idx = grp1.index.intersection(grp2.index)
        val1 = grp1.loc[common_idx]
        val2 = grp2.loc[common_idx]
        
        t_stat, p_val = stats.ttest_rel(val2, val1)
        d = cohens_d(val2.tolist(), val1.tolist())
        
        # 95% CIs on the means
        ci1 = confidence_interval_95(val1.tolist())
        ci2 = confidence_interval_95(val2.tolist())
        
        print(f"Comparison: Condition {c2.upper()} vs Condition {c1.upper()}")
        print(f"  Mean {c2.upper()}: {val2.mean():.4f} (95% CI: [{ci2[0]:.4f}, {ci2[1]:.4f}])")
        print(f"  Mean {c1.upper()}: {val1.mean():.4f} (95% CI: [{ci1[0]:.4f}, {ci1[1]:.4f}])")
        print(f"  Paired t-statistic: {t_stat:.4f} | p-value: {p_val:.4g}")
        print(f"  Cohen's d (pooled): {d:.4f}")
        
        sig_str = "SIGNIFICANT" if p_val < bonferroni_alpha else "NOT SIGNIFICANT"
        print(f"  Significance (Bonferroni corrected alpha={bonferroni_alpha:.4f}): {sig_str}")
        print()
        
    # Additional diagnostic tests
    run_per_intent_anova(df)
    run_mcnemars_test(df)
    analyze_condition_b_hallucinations(df)
    compute_silhouette_scores()
    
    print("\nAnalysis complete. CSV tables saved to data/ directory.")

if __name__ == "__main__":
    analyze()
