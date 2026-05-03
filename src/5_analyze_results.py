"""
5_analyze_results.py - Phase 5: Statistical Analysis for DevPrompt Paper

Generates the final tables and figures for the research paper:
1. Overall Performance by Condition (A vs B vs C)
2. Model Performance by Condition (A vs B vs C across Gemini, Groq, Cerebras)
3. Intent Preservation vs. Tool F1 Correlation
4. Token Efficiency metrics

Outputs tables to the console and saves them as CSV in data/
"""

import sqlite3
import pandas as pd
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DB_PATH  = os.path.join(DATA_DIR, 'results.db')

def analyze():
    if not os.path.exists(DB_PATH):
        print(f"Database not found: {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    
    # Load all scored data into a pandas DataFrame
    query = """
        SELECT 
            r.run_id, r.task_id, r.intent, r.condition, r.model,
            s.intent_preservation, s.tool_precision, s.tool_recall, s.tool_f1,
            s.total_tool_calls, s.redundant_calls, s.first_call_correct, s.min_req_met, s.hallucination_score,
            r.input_tokens, r.output_tokens, r.total_tokens, r.execution_time_sec
        FROM results r
        JOIN scores s ON r.run_id = s.run_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if len(df) == 0:
        print("No scored results found in the database. Run 4_score_results.py first.")
        return
        
    print(f"Loaded {len(df)} scored results for analysis.\n")
    
    # 1. Overall Performance by Condition
    print("=== Table 1: Overall Performance by Condition ===")
    
    # Calculate CPSTC manually
    cond_stats = df.groupby('condition').agg(
        Intent_Preservation=('intent_preservation', 'mean'),
        Tool_F1=('tool_f1', 'mean'),
        Hallucination_Rate=('hallucination_score', 'mean'),
        First_Call_Acc=('first_call_correct', 'mean'),
        Min_Req_Met=('min_req_met', 'mean'),
        Redundancy=('redundant_calls', 'mean'),
        Avg_Tokens=('total_tokens', 'mean'),
        Total_Tokens_Sum=('total_tokens', 'sum'),
        Successful_Tasks=('min_req_met', 'sum')
    )
    cond_stats['CPSTC'] = cond_stats['Total_Tokens_Sum'] / cond_stats['Successful_Tasks']
    cond_stats = cond_stats.drop(columns=['Total_Tokens_Sum', 'Successful_Tasks']).round(4)
    print(cond_stats)
    cond_stats.to_csv(os.path.join(DATA_DIR, 'table1_condition_overall.csv'))
    print("\n")
    
    # 2. Performance by Model and Condition
    print("=== Table 2: Performance by Model and Condition ===")
    model_cond_stats = df.pivot_table(
        index='model', 
        columns='condition', 
        values=['tool_f1', 'intent_preservation', 'hallucination_score'],
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
    
    # 4. Statistical significance (simplified Cohen's d approximation for C vs A)
    # Using the overall tool_f1 scores
    cond_A = df[df['condition'] == 'a']['tool_f1']
    cond_C = df[df['condition'] == 'c']['tool_f1']
    
    mean_A = cond_A.mean()
    mean_C = cond_C.mean()
    std_pooled = ((cond_A.std() ** 2 + cond_C.std() ** 2) / 2) ** 0.5
    
    if std_pooled > 0:
        cohens_d = (mean_C - mean_A) / std_pooled
    else:
        cohens_d = 0.0
        
    print("=== Statistical Analysis ===")
    print(f"Cohen's d (Condition C vs Condition A) for Tool F1: {cohens_d:.4f}")
    if cohens_d > 0.8:
        print("Interpretation: Large effect size. Condition C significantly improves Tool F1.")
    elif cohens_d > 0.5:
        print("Interpretation: Medium effect size. Condition C moderately improves Tool F1.")
    elif cohens_d > 0.2:
        print("Interpretation: Small effect size. Condition C slightly improves Tool F1.")
    else:
        print("Interpretation: Negligible effect size.")
        
    print("\nAnalysis complete. CSV tables saved to data/ directory.")

if __name__ == '__main__':
    analyze()
