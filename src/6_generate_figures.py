"""
6_generate_figures.py - Phase 6: Figure Generation for DevPrompt Paper

Generates the 6 main figures for the research paper:
1. Intent Preservation by Condition
2. Tool F1 by Condition
3. Intent Preservation vs. Tool F1 Correlation
4. Tool Precision/Recall by Condition
5. Cross-model Performance
6. Token Efficiency by Condition

Outputs high-DPI images to the figures/ directory.
"""

import sqlite3
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as plt_sns
import numpy as np

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

def create_figures():
    if not os.path.exists(FIG_DIR):
        os.makedirs(FIG_DIR)
        
    conn = sqlite3.connect(DB_PATH)
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
        print("No scored results found.")
        return
        
    print(f"Loaded {len(df)} scored results. Generating figures...")
    setup_style()
    
    # 1. Intent Preservation by Condition
    plt.figure(figsize=(8, 6))
    ax = plt_sns.barplot(data=df, x='condition', y='intent_preservation', capsize=.1, errorbar=('ci', 95))
    ax.set_title('Intent Preservation Score by Prompt Condition')
    ax.set_xlabel('Condition (A=Raw, B=Clean, C=JSON)')
    ax.set_ylabel('Cosine Similarity to Gold Standard')
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

    # 9. Pareto Frontier (CPSTC explicitly plotted)
    cpstc_df = df.groupby('condition').agg(
        Total_Tokens=('total_tokens', 'sum'),
        Successful_Tasks=('min_req_met', 'sum'),
        Tool_F1=('tool_f1', 'mean')
    ).reset_index()
    cpstc_df['Avg_Tokens'] = cpstc_df['Total_Tokens'] / len(df['condition'].unique())  # approximate
    cpstc_df['CPSTC'] = cpstc_df['Total_Tokens'] / cpstc_df['Successful_Tasks']
    
    plt.figure(figsize=(8, 6))
    markers = ['o', 's', '^']
    for i, row in cpstc_df.iterrows():
        plt.scatter(row['CPSTC'], row['Tool_F1'], s=200, marker=markers[i], label=f"Cond {row['condition'].upper()}")
        plt.text(row['CPSTC'] + 50, row['Tool_F1'], f"Cond {row['condition'].upper()}", fontsize=12)
    plt.title('Cost-Performance Pareto Frontier (CPSTC)')
    plt.xlabel('CPSTC (Tokens per Successful Task)')
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

    # 11. Success Breakdown (First Call vs Eventual)
    succ_df = df.groupby('condition')[['first_call_correct', 'min_req_met']].mean().reset_index()
    # To plot as stacked, we need "Eventual only"
    succ_df['Eventual Only'] = succ_df['min_req_met'] - succ_df['first_call_correct']
    # Sometimes it can be negative if logic was weird, cap at 0
    succ_df['Eventual Only'] = succ_df['Eventual Only'].clip(lower=0)
    
    plt.figure(figsize=(8, 6))
    plt.bar(succ_df['condition'], succ_df['first_call_correct'], color='#2ca02c', label='First Call Correct')
    plt.bar(succ_df['condition'], succ_df['Eventual Only'], bottom=succ_df['first_call_correct'], color='#1f77b4', label='Eventual Success (Multiple Calls)')
    plt.title('Success Breakdown: Immediate vs Multi-Turn')
    plt.xlabel('Condition (A=Raw, B=Clean, C=JSON)')
    plt.ylabel('Success Rate')
    plt.legend()
    plt.savefig(os.path.join(FIG_DIR, 'fig11_success_breakdown.png'))
    plt.close()

    # 12. Intent Preservation by Model
    plt.figure(figsize=(10, 6))
    ax = plt_sns.barplot(data=df, x='model', y='intent_preservation', hue='condition', capsize=.05)
    ax.set_title('Intent Preservation Score by Model and Condition')
    ax.set_xlabel('LLM Model')
    ax.set_ylabel('Cosine Similarity (Intent)')
    plt.legend(title='Condition', loc='lower right')
    plt.savefig(os.path.join(FIG_DIR, 'fig12_intent_by_model.png'))
    plt.close()

    # 13. Input vs Output Token Breakdown
    tok_df = df.groupby('condition')[['input_tokens', 'output_tokens']].mean().reset_index()
    plt.figure(figsize=(8, 6))
    
    p1 = plt.bar(tok_df['condition'], tok_df['input_tokens'], color='lightblue', label='Input Tokens')
    p2 = plt.bar(tok_df['condition'], tok_df['output_tokens'], bottom=tok_df['input_tokens'], color='steelblue', label='Output Tokens')
    
    plt.title('Token Usage Breakdown: Input vs Output')
    plt.xlabel('Condition (A=Raw, B=Clean, C=JSON)')
    plt.ylabel('Average Tokens per Task')
    plt.legend()
    plt.savefig(os.path.join(FIG_DIR, 'fig13_token_breakdown.png'))
    plt.close()

    print(f"13 figures generated successfully in {FIG_DIR}")

if __name__ == '__main__':
    create_figures()
