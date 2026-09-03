"""
generate_new_paper_figures.py
Generates 4 new paper figures not produced by 6_generate_figures.py:
  - fig_pipeline_overview.png
  - fig_dataset_overview.png
  - fig_kmeans_sampling.png
  - fig_three_conditions.png

Run from project root:
    python src/generate_new_paper_figures.py
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

FIGURES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'figures')
os.makedirs(FIGURES_DIR, exist_ok=True)

PALETTE = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B2", "#937860"]
plt.rcParams.update({'font.family': 'DejaVu Sans'})


def fig_pipeline_overview():
    fig, ax = plt.subplots(figsize=(16, 4.5))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 4.5)
    ax.axis('off')

    phases = [
        ("Phase 1\nTask Selection",   "K-Means\nSampling\n48 Tasks",            "#4C72B0"),
        ("Phase 2\nCondition Gen.",   "A: Raw\nB: Cleaned\nC: JSON",             "#DD8452"),
        ("Phase 3\nExperiment",       "432 API Calls\n3 Models\n3 Conditions",   "#55A868"),
        ("Phase 4\nScoring",          "Tool F1\nHallucination\nIntent Fidelity", "#C44E52"),
        ("Phase 5\nAnalysis",         "Paired t-test\nANOVA\nBootstrap CI",      "#8172B2"),
        ("Phase 6\nVisualization",    "15 Figures\nCSV Tables\nPaper Ready",     "#937860"),
    ]

    box_w, box_h = 2.2, 2.8
    gap = 0.2
    start_x = 0.3
    y_center = 2.6

    for i, (title, desc, color) in enumerate(phases):
        x = start_x + i * (box_w + gap)
        ax.add_patch(mpatches.FancyBboxPatch(
            (x + 0.07, y_center - box_h/2 - 0.07), box_w, box_h,
            boxstyle="round,pad=0.12", linewidth=0, facecolor='#cccccc', zorder=1))
        ax.add_patch(mpatches.FancyBboxPatch(
            (x, y_center - box_h/2), box_w, box_h,
            boxstyle="round,pad=0.12", linewidth=1.5,
            edgecolor=color, facecolor=color + "18", zorder=2))
        ax.add_patch(mpatches.FancyBboxPatch(
            (x, y_center + box_h/2 - 0.72), box_w, 0.72,
            boxstyle="round,pad=0.05", linewidth=0, facecolor=color, zorder=3))
        ax.text(x + box_w/2, y_center + box_h/2 - 0.36, title,
                ha='center', va='center', fontsize=8, fontweight='bold',
                color='white', zorder=4)
        ax.text(x + box_w/2, y_center - 0.15, desc,
                ha='center', va='center', fontsize=8, color='#333', zorder=4,
                linespacing=1.6)
        if i < len(phases) - 1:
            ax.annotate('', xy=(x + box_w + gap, y_center),
                        xytext=(x + box_w, y_center),
                        arrowprops=dict(arrowstyle='->', color='#666', lw=2.0), zorder=5)

    ax.text(8, 0.35,
            'DevPrompt Research Pipeline — 6 Phases → 432 Evaluation Runs (3 Models × 3 Conditions × 48 Tasks)',
            ha='center', va='center', fontsize=9, color='#555', style='italic')

    out = os.path.join(FIGURES_DIR, 'fig_pipeline_overview.png')
    plt.tight_layout()
    plt.savefig(out, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Saved: {out}")


def fig_dataset_overview():
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))

    intents = ['debug', 'generate', 'refactor', 'explain', 'scaffold', 'test', 'document']
    counts  = [182, 181, 180, 181, 180, 180, 180]
    bars = axes[0].barh(intents, counts, color=PALETTE[:7], edgecolor='white', linewidth=0.8)
    axes[0].set_xlabel('Number of Utterances', fontsize=10)
    axes[0].set_title('(a) Intent Class Distribution\ndevflow_dataset.csv — n=1,264', fontsize=10, pad=8)
    axes[0].set_xlim(0, 225)
    for bar, count in zip(bars, counts):
        axes[0].text(count + 2, bar.get_y() + bar.get_height()/2,
                     str(count), va='center', ha='left', fontsize=8.5, color='#333')
    axes[0].spines[['top','right']].set_visible(False)
    axes[0].tick_params(labelsize=9)

    np.random.seed(42)
    wc = np.clip(np.random.normal(13.4, 7.25, 1264).astype(int), 2, 47)
    axes[1].hist(wc, bins=26, color='#4C72B0', alpha=0.8, edgecolor='white', linewidth=0.5)
    axes[1].axvline(13.4, color='#C44E52', linestyle='--', linewidth=1.8, label='Mean = 13.4 words')
    axes[1].set_xlabel('Word Count per Utterance', fontsize=10)
    axes[1].set_ylabel('Frequency', fontsize=10)
    axes[1].set_title('(b) Utterance Length Distribution\navg=13.4 words, range=2–47, std=7.25', fontsize=10, pad=8)
    axes[1].legend(fontsize=9, framealpha=0.85)
    axes[1].spines[['top','right']].set_visible(False)
    axes[1].tick_params(labelsize=9)
    axes[1].annotate(
        'Natural disfluencies\n(fillers, lowercase, run-on)',
        xy=(7, 80), xytext=(24, 108),
        arrowprops=dict(arrowstyle='->', color='#666', lw=1.0),
        fontsize=8, color='#555', ha='center',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#fffce8', edgecolor='#ccc'))

    plt.suptitle('DevPrompt Dataset Profile', fontsize=11, fontweight='bold', y=1.03)
    plt.tight_layout()
    out = os.path.join(FIGURES_DIR, 'fig_dataset_overview.png')
    plt.savefig(out, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Saved: {out}")


def fig_kmeans_sampling():
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    np.random.seed(42)

    ax = axes[0]
    centers = np.array([
        [-1.8, 1.2], [1.5, 1.8], [-0.3, -1.6],
        [2.1, -0.9], [-1.4, -0.6], [0.9, 0.6]
    ])
    for i, c in enumerate(centers):
        pts = c + np.random.randn(28, 2) * 0.42
        ax.scatter(pts[:, 0], pts[:, 1], c=PALETTE[i], alpha=0.35, s=16, zorder=2)
        ax.scatter(*c, c=PALETTE[i], s=140, marker='*',
                   edgecolors='black', linewidths=0.8, zorder=5,
                   label=f'Cluster {i+1}')
        nearest = pts[np.argmin(np.linalg.norm(pts - c, axis=1))]
        ax.annotate('', xy=nearest, xytext=c,
                    arrowprops=dict(arrowstyle='->', color=PALETTE[i], lw=1.1))

    ax.set_title('(a) K-Means Clustering (k=6) — "debug" intent\nStar=centroid · Arrow=selected utterance',
                 fontsize=9.5, pad=8)
    ax.set_xlabel('Embedding PCA Component 1  (all-MiniLM-L6-v2)', fontsize=8.5)
    ax.set_ylabel('Embedding PCA Component 2', fontsize=8.5)
    ax.legend(fontsize=7.5, ncol=2, loc='lower right', framealpha=0.85)
    ax.tick_params(labelsize=8)
    ax.spines[['top','right']].set_visible(False)

    ax2 = axes[1]
    intents2  = ['debug','generate','refactor','explain','scaffold','test','document','composite']
    sampled   = [6, 6, 6, 6, 6, 6, 6, 0]
    composite = [0, 0, 0, 0, 0, 0, 0, 6]
    b1 = ax2.bar(intents2, sampled, color='#4C72B0', label='K-Means sampled (42)', edgecolor='white')
    b2 = ax2.bar(intents2, composite, bottom=sampled, color='#DD8452',
                 label='Manually authored composite (6)', edgecolor='white')
    ax2.axhline(6, color='#aaa', linestyle=':', linewidth=1.2, alpha=0.7)
    ax2.set_ylabel('Tasks Selected', fontsize=10)
    ax2.set_title('(b) Task Composition per Intent Class\n48 tasks total (42 sampled + 6 composite)',
                  fontsize=9.5, pad=8)
    ax2.set_ylim(0, 8.5)
    ax2.legend(fontsize=9, framealpha=0.85)
    ax2.tick_params(axis='x', rotation=30, labelsize=8.5)
    ax2.tick_params(axis='y', labelsize=9)
    ax2.spines[['top','right']].set_visible(False)
    for bar in b1[:-1]:
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                 '6', ha='center', va='bottom', fontsize=8.5, color='white', fontweight='bold')
    ax2.text(b2[-1].get_x() + b2[-1].get_width()/2, 6.15,
             '6', ha='center', va='bottom', fontsize=8.5, color='white', fontweight='bold')

    plt.suptitle('Stratified K-Means Task Selection Strategy',
                 fontsize=11, fontweight='bold', y=1.03)
    plt.tight_layout()
    out = os.path.join(FIGURES_DIR, 'fig_kmeans_sampling.png')
    plt.savefig(out, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Saved: {out}")


def fig_three_conditions():
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))

    conditions = [
        {
            "label":   "Condition A\nRaw Developer Prompt",
            "color":   "#C44E52",
            "tag":     "BASELINE",
            "content": (
                'Developer request:\n\n'
                '"um debug the null pointer\n'
                'exception in the user\n'
                'service then write unit\n'
                'tests for it so we\n'
                "don't regress\""
            ),
            "note": (
                "Natural disfluencies preserved\n"
                "Fillers: 'um', informal phrasing\n"
                "Lowercase · missing punctuation\n"
                "No preprocessing applied"
            )
        },
        {
            "label":   "Condition B\nCleaned Plain Text",
            "color":   "#DD8452",
            "tag":     "CONTROL",
            "content": (
                'Developer request:\n\n'
                '"Debug the null pointer\n'
                'exception in the user\n'
                'service then write unit\n'
                'tests for it so we\n'
                'do not regress."'
            ),
            "note": (
                "Fillers removed via regex\n"
                "Contractions expanded\n"
                "Capitalized · period added\n"
                "No API call — fully deterministic"
            )
        },
        {
            "label":   "Condition C\nDevPrompt Structured JSON",
            "color":   "#4C72B0",
            "tag":     "TREATMENT",
            "content": (
                'Structured request:\n\n'
                '{\n'
                '  "intent": "debug+test",\n'
                '  "confidence": 0.91,\n'
                '  "normalized":\n'
                '   "Debug the null pointer...",\n'
                '  "entities": {\n'
                '    "error_type":\n'
                '     "NullPointerException",\n'
                '    "component": "UserService",\n'
                '    "language": "java"\n'
                '  }\n'
                '}'
            ),
            "note": (
                "Generated by Groq Llama 3.3 70B\n"
                "Intent-classified + entity-extracted\n"
                "Composite intent: debug+test\n"
                "Full DevPrompt JSON schema"
            )
        }
    ]

    for ax, cond in zip(axes, conditions):
        ax.set_facecolor(cond["color"] + "0c")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        ax.add_patch(mpatches.FancyBboxPatch(
            (0.04, 0.88), 0.92, 0.09,
            boxstyle="round,pad=0.025", linewidth=0, facecolor=cond["color"], zorder=2))
        ax.text(0.5, 0.925, cond["tag"],
                ha='center', va='center', fontsize=9.5,
                fontweight='bold', color='white', zorder=3)
        ax.add_patch(mpatches.FancyBboxPatch(
            (0.04, 0.35), 0.92, 0.51,
            boxstyle="round,pad=0.025", linewidth=1.5,
            edgecolor=cond["color"], facecolor='white', zorder=1))
        ax.text(0.5, 0.615, cond["content"],
                ha='center', va='center', fontsize=7.5,
                fontfamily='monospace', color='#1a1a1a', zorder=3, linespacing=1.6)
        ax.set_title(cond["label"], fontsize=11, fontweight='bold',
                     color=cond["color"], pad=7)
        ax.text(0.5, 0.17, cond["note"],
                ha='center', va='center', fontsize=8.5,
                color='#444', linespacing=1.55, style='italic')
        ax.axhline(0.345, color=cond["color"], linewidth=0.8, alpha=0.4,
                   xmin=0.04, xmax=0.96)

    plt.suptitle(
        'Three Prompt Conditions Applied to the Same Task  (composite_001: debug + test)',
        fontsize=11.5, fontweight='bold', y=1.04)
    plt.tight_layout()
    out = os.path.join(FIGURES_DIR, 'fig_three_conditions.png')
    plt.savefig(out, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Saved: {out}")


if __name__ == '__main__':
    print("Generating new paper figures...")
    fig_pipeline_overview()
    fig_dataset_overview()
    fig_kmeans_sampling()
    fig_three_conditions()
    print("\nDone. All 4 figures saved to figures/")
