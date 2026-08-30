"""
6_generate_figures.py - Phase 6: Figure Generation for DevPrompt Paper

Generates the main figures for the research paper:
1. Intent Fidelity by Condition
2. Tool F1 by Condition
3. Precision vs Recall by Condition
4. Cross-Model Performance
5. Intent Class Breakdown
6. Token Efficiency Scatter
7. Redundancy vs Success (Productive Flailing)
8. Hallucination Heatmap
9. Cost-Performance Pareto Frontier (CPSTC)
10. Execution Time (Latency)
11. Success Breakdown (First Call vs Eventual)
12. Intent Fidelity by Model
13. Input vs Output Token Breakdown
14. Format Compliance by Model and Condition
15. Kendall's Tau Score by Condition

Outputs high-DPI images to the figures/ directory.
"""

import sqlite3
import pandas as pd
import os
import json
import matplotlib.pyplot as plt
import seaborn as plt_sns
import numpy as np
from scipy import stats

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DB_PATH  = os.path.join(DATA_DIR, 'results.db')
FIG_DIR  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'figures')

def setup_style():
    """Configure seaborn and matplotlib styles for publication-quality figures."""
    plt_sns.set_theme(style="whitegrid", palette="colorblind")
    plt.rcParams.update({
        'font.size': 12,
        'axes.labelsize': 14,
        'axes.titlesize': 16,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'legend.fontsize': 12,
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight'
    })

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

def bootstrap_cpstc_local(sub_df, n_iterations=1000):
    cpstc_values = []
    n = len(sub_df)
    if n == 0:
        return (0, 0)
    np.random.seed(42)
    for _ in range(n_iterations):
        sample = sub_df.sample(n=n, replace=True)
        successes = sample['min_req_met'].sum()
        tokens = sample['total_tokens'].sum()
        if successes > 0:
            cpstc_values.append(tokens / successes)
    if not cpstc_values:
        return (0, 0)
    return (np.percentile(cpstc_values, 2.5), np.percentile(cpstc_values, 97.5))

def create_figures():
    if not os.path.exists(FIG_DIR):
        os.makedirs(FIG_DIR)
        
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT 
            r.run_id, r.task_id, r.intent, r.condition, r.model,
            s.intent_fidelity_score, s.tool_precision, s.tool_recall, s.tool_f1,
            s.total_tool_calls, s.redundant_calls, s.first_call_correct, s.min_req_met, s.hallucination_score,
            r.input_tokens, r.output_tokens, r.total_tokens, r.execution_time_sec, r.tool_calls_json
        FROM results r
        JOIN scores s ON r.run_id = s.run_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if len(df) == 0:
        print("No scored results found.")
        return
        
    print(f"Loaded {len(df)} scored results. Generating figures...")
    setup_style()
    tasks_map = load_tasks_map()
    
    # 1. Intent Fidelity by Condition
    plt.figure(figsize=(8, 6))
    ax = plt_sns.barplot(data=df, x='condition', y='intent_fidelity_score', capsize=.1, errorbar=('ci', 95))
    ax.set_title('Intent Fidelity Score by Prompt Condition')
    ax.set_xlabel('Condition (A=Raw, B=Clean, C=JSON)')
    ax.set_ylabel('Intent Fidelity Score (0-3)')
    plt.savefig(os.path.join(FIG_DIR, 'fig1_intent_preservation.png'))
    plt.close()
    
    # 2. Tool F1 by Condition
    plt.figure(figsize=(8, 6))
    ax = plt_sns.barplot(data=df, x='condition', y='tool_f1', capsize=.1, errorbar=('ci', 95))
    ax.set_title('Tool Selection F1-Score by Prompt Condition')
    ax.set_xlabel('Condition (A=Raw, B=Clean, C=JSON)')
    ax.set_ylabel('Tool F1-Score')
    plt.savefig(os.path.join(FIG_DIR, 'fig2_tool_f1.png'))
    plt.close()

    # 3. Precision vs Recall by Condition (Scatter/Line)
    cond_stats = df.groupby('condition')[['tool_precision', 'tool_recall']].mean().reset_index()
    plt.figure(figsize=(8, 6))
    markers = ['o', 's', '^']
    colors = plt_sns.color_palette("colorblind", 3)
    for i, row in cond_stats.iterrows():
        plt.scatter(row['tool_precision'], row['tool_recall'], 
                    label=f"Condition {row['condition'].upper()}",
                    marker=markers[i], color=colors[i], s=150)
    plt.plot([0, 1], [0, 1], 'k--', alpha=0.3, label='Precision = Recall')
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.title('Agentic Tool Use: Precision vs. Recall')
    plt.xlabel('Mean Tool Precision')
    plt.ylabel('Mean Tool Recall')
    plt.legend()
    plt.savefig(os.path.join(FIG_DIR, 'fig3_precision_vs_recall.png'))
    plt.close()

    # 4. Cross-Model Performance
    plt.figure(figsize=(10, 6))
    ax = plt_sns.barplot(data=df, x='model', y='tool_f1', hue='condition', capsize=.05, errorbar=('ci', 95))
    ax.set_title('Tool F1-Score by Model and Condition')
    ax.set_xlabel('LLM Model')
    ax.set_ylabel('Tool F1-Score')
    plt.legend(title='Condition')
    plt.savefig(os.path.join(FIG_DIR, 'fig4_cross_model_f1.png'))
    plt.close()

    # 5. Intent Class Breakdown (Tool F1)
    plt.figure(figsize=(12, 6))
    ax = plt_sns.barplot(data=df, x='intent', y='tool_f1', hue='condition', errorbar=None)
    ax.set_title('Tool F1-Score across Task Intents')
    ax.set_xlabel('Task Intent')
    ax.set_ylabel('Mean Tool F1-Score')
    plt.xticks(rotation=45)
    plt.legend(title='Condition', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'fig5_intent_class_f1.png'))
    plt.close()

    # 6. Token Efficiency (Total Tokens vs Tool F1)
    plt.figure(figsize=(8, 6))
    ax = plt_sns.scatterplot(data=df, x='total_tokens', y='tool_f1', hue='condition', alpha=0.6)
    ax.set_title('Token Efficiency: Performance vs. Token Cost')
    ax.set_xlabel('Total Tokens (Input + Output)')
    ax.set_ylabel('Tool F1-Score')
    plt.savefig(os.path.join(FIG_DIR, 'fig6_token_efficiency.png'))
    plt.close()

    # 7. Redundancy vs Success (Productive Flailing)
    red_df = df.groupby('condition')[['redundant_calls', 'min_req_met']].mean().reset_index()
    fig, ax1 = plt.subplots(figsize=(8, 6))
    ax2 = ax1.twinx()
    width = 0.35
    x = np.arange(len(red_df))
    ax1.bar(x - width/2, red_df['redundant_calls'], width, color='skyblue', label='Redundant Calls')
    ax2.bar(x + width/2, red_df['min_req_met'], width, color='salmon', label='Success Rate (Min Req)')
    ax1.set_xlabel('Condition (A=Raw, B=Clean, C=JSON)')
    ax1.set_ylabel('Avg Redundant Tool Calls', color='skyblue')
    ax2.set_ylabel('Success Rate', color='salmon')
    ax1.set_xticks(x)
    ax1.set_xticklabels(['A', 'B', 'C'])
    plt.title('Productive Flailing: Redundancy vs Success')
    fig.legend(loc='upper left', bbox_to_anchor=(0.15, 0.85))
    plt.savefig(os.path.join(FIG_DIR, 'fig7_redundancy_vs_success.png'))
    plt.close()

    # 8. Hallucination Heatmap (Model x Condition)
    hall_df = df.pivot_table(values='hallucination_score', index='model', columns='condition', aggfunc='mean')
    plt.figure(figsize=(8, 6))
    ax = plt_sns.heatmap(hall_df, annot=True, cmap='YlOrRd', fmt='.3f', cbar_kws={'label': 'Avg Hallucination Score (0-2)'})
    ax.set_title('Hallucination Severity by Model and Condition')
    ax.set_xlabel('Condition (A=Raw, B=Clean, C=JSON)')
    ax.set_ylabel('Model')
    plt.savefig(os.path.join(FIG_DIR, 'fig8_hallucination_heatmap.png'))
    plt.close()

    # 9. Pareto Frontier (CPSTC explicitly plotted with Bootstrap CIs)
    cpstc_df = df.groupby('condition').agg(
        Total_Tokens=('total_tokens', 'sum'),
        Successful_Tasks=('min_req_met', 'sum'),
        Tool_F1=('tool_f1', 'mean')
    ).reset_index()
    cpstc_df['CPSTC'] = cpstc_df['Total_Tokens'] / cpstc_df['Successful_Tasks']
    
    plt.figure(figsize=(8, 6))
    colors = plt_sns.color_palette("colorblind", 3)
    for i, row in cpstc_df.iterrows():
        cond = row['condition']
        sub_cond = df[df['condition'] == cond]
        ci_low, ci_high = bootstrap_cpstc_local(sub_cond)
        xerr_low = row['CPSTC'] - ci_low
        xerr_high = ci_high - row['CPSTC']
        
        plt.errorbar(row['CPSTC'], row['Tool_F1'], xerr=[[xerr_low], [xerr_high]], 
                     fmt=markers[i], color=colors[i], markersize=12, capsize=5, label=f"Cond {cond.upper()}")
        plt.text(row['CPSTC'] + 80, row['Tool_F1'], f"Cond {cond.upper()}", fontsize=12)
        
    plt.title('Cost-Performance Pareto Frontier (CPSTC)')
    plt.xlabel('CPSTC (Tokens per Successful Task, with 95% Bootstrap CIs)')
    plt.ylabel('Mean Tool F1-Score')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig(os.path.join(FIG_DIR, 'fig9_pareto_frontier.png'))
    plt.close()

    # 10. Execution Time (Latency)
    plt.figure(figsize=(10, 6))
    ax = plt_sns.barplot(data=df, x='model', y='execution_time_sec', hue='condition', capsize=.05)
    ax.set_title('API Execution Latency by Model and Condition')
    ax.set_xlabel('LLM Model')
    ax.set_ylabel('Execution Time (Seconds)')
    plt.legend(title='Condition')
    plt.savefig(os.path.join(FIG_DIR, 'fig10_execution_latency.png'))
    plt.close()

    # 11. Success Breakdown Grouped Bars (Fix 5.2)
    succ_df = df.groupby('condition')[['first_call_correct', 'min_req_met']].mean().reset_index()
    x = np.arange(len(succ_df))
    width = 0.35
    plt.figure(figsize=(8, 6))
    plt.bar(x - width/2, succ_df['first_call_correct'], width, label='First Call Correct', color='#2ca02c')
    plt.bar(x + width/2, succ_df['min_req_met'], width, label='Eventual Success (Min Req)', color='#1f77b4')
    plt.title('Success Rate comparison: Immediate vs Multi-Turn')
    plt.xlabel('Condition (A=Raw, B=Clean, C=JSON)')
    plt.ylabel('Success Rate')
    plt.xticks(x, ['A', 'B', 'C'])
    plt.legend()
    plt.savefig(os.path.join(FIG_DIR, 'fig11_success_breakdown.png'))
    plt.close()

    # 12. Intent Fidelity by Model
    plt.figure(figsize=(10, 6))
    ax = plt_sns.barplot(data=df, x='model', y='intent_fidelity_score', hue='condition', capsize=.05)
    ax.set_title('Intent Fidelity Score by Model and Condition')
    ax.set_xlabel('LLM Model')
    ax.set_ylabel('Intent Fidelity Score (0-3)')
    plt.legend(title='Condition', loc='lower right')
    plt.savefig(os.path.join(FIG_DIR, 'fig12_intent_by_model.png'))
    plt.close()

    # 13. Input vs Output Token Breakdown
    tok_df = df.groupby('condition')[['input_tokens', 'output_tokens']].mean().reset_index()
    plt.figure(figsize=(8, 6))
    plt.bar(tok_df['condition'], tok_df['input_tokens'], color='lightblue', label='Input Tokens')
    plt.bar(tok_df['condition'], tok_df['output_tokens'], bottom=tok_df['input_tokens'], color='steelblue', label='Output Tokens')
    plt.title('Token Usage Breakdown: Input vs Output')
    plt.xlabel('Condition (A=Raw, B=Clean, C=JSON)')
    plt.ylabel('Average Tokens per Task')
    plt.legend()
    plt.savefig(os.path.join(FIG_DIR, 'fig13_token_breakdown.png'))
    plt.close()

    # 14. Format Compliance by Model and Condition (New)
    df['format_compliance'] = (df['total_tool_calls'] > 0).astype(float)
    plt.figure(figsize=(10, 6))
    ax = plt_sns.barplot(data=df, x='model', y='format_compliance', hue='condition', capsize=.05)
    ax.set_title('Format Compliance Rate by Model and Condition')
    ax.set_xlabel('LLM Model')
    ax.set_ylabel('Format Compliance Rate (% runs returning valid TOOL_CALL)')
    plt.legend(title='Condition')
    plt.savefig(os.path.join(FIG_DIR, 'fig14_format_compliance.png'))
    plt.close()

    # 15. Kendall's Tau Tool Ordering Score by Condition (New)
    df['kendall_tau'] = df.apply(lambda r: compute_row_kendall_tau(r, tasks_map), axis=1)
    tau_df = df.dropna(subset=['kendall_tau'])
    plt.figure(figsize=(8, 6))
    ax = plt_sns.barplot(data=tau_df, x='condition', y='kendall_tau', capsize=.1, errorbar=('ci', 95))
    ax.set_title('Tool Ordering Correctness (Kendall\'s Tau) by Prompt Condition')
    ax.set_xlabel('Condition (A=Raw, B=Clean, C=JSON)')
    ax.set_ylabel('Mean Kendall\'s Tau Score')
    plt.savefig(os.path.join(FIG_DIR, 'fig15_kendall_tau.png'))
    plt.close()

    print(f"15 figures generated successfully in {FIG_DIR}")

if __name__ == '__main__':
    create_figures()
