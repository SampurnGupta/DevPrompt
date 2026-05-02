"""
1_select_tasks.py — Phase 1.1 + 1.2: Dataset sampling and task selection.

Process:
  1. Load devflow_dataset.csv
  2. Embed all utterances with all-MiniLM-L6-v2
  3. K-Means clustering (k=6) within each intent class
  4. Select utterance nearest to each cluster centroid
  5. Tiebreak: utterance with most non-null entities
  6. Output: data/selected_tasks_base.csv (42 tasks)
  7. Append 6 manually-authored composite tasks → data/tasks_raw.json (48 tasks total)

Usage:
    python src/1_select_tasks.py
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'devflow_dataset.csv')
OUTPUT_CSV = os.path.join(DATA_DIR, 'selected_tasks_base.csv')
OUTPUT_JSON = os.path.join(DATA_DIR, 'tasks_raw.json')

VALID_INTENTS = ['debug', 'generate', 'refactor', 'explain', 'scaffold', 'test', 'document']
CLUSTERS_PER_CLASS = 6  # → 7 × 6 = 42 single-intent tasks
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'


# ---------------------------------------------------------------------------
# 6 manually-authored composite tasks
# ---------------------------------------------------------------------------

COMPOSITE_TASKS = [
    {
        "task_id": "composite_001",
        "intent": "composite",
        "sub_intents": ["debug", "test"],
        "raw_utterance": "um debug the null pointer exception in the user service then write unit tests for it so we don't regress"
    },
    {
        "task_id": "composite_002",
        "intent": "composite",
        "sub_intents": ["refactor", "document"],
        "raw_utterance": "refactor the payment service to separate concerns and uh document the changes with proper inline comments"
    },
    {
        "task_id": "composite_003",
        "intent": "composite",
        "sub_intents": ["explain", "generate"],
        "raw_utterance": "explain why the kafka consumer is lagging and like generate a fix using async processing"
    },
    {
        "task_id": "composite_004",
        "intent": "composite",
        "sub_intents": ["scaffold", "test"],
        "raw_utterance": "scaffold a new microservice for order management and basically add integration tests for the main endpoints"
    },
    {
        "task_id": "composite_005",
        "intent": "composite",
        "sub_intents": ["debug", "document"],
        "raw_utterance": "um fix the memory leak in the connection pool and write documentation about what was causing it and how you fixed it"
    },
    {
        "task_id": "composite_006",
        "intent": "composite",
        "sub_intents": ["generate", "explain"],
        "raw_utterance": "generate a new REST API endpoint for user profile updates and explain how it integrates with the existing auth middleware"
    }
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def count_entities(row: pd.Series) -> int:
    """Count non-null entity fields (language, framework, error_type) in a dataset row."""
    cols = ['language', 'framework', 'error_type']
    return sum(1 for c in cols if c in row.index and pd.notna(row[c]) and str(row[c]).strip() not in ('', 'nan'))


def embed_utterances(utterances: list, model: SentenceTransformer, batch_size: int = 64) -> np.ndarray:
    """Embed utterances in batches with progress bar."""
    print(f"  Embedding {len(utterances)} utterances...")
    embeddings = model.encode(
        utterances,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True
    )
    return embeddings


def select_tasks_for_class(
    class_df: pd.DataFrame,
    embeddings: np.ndarray,
    intent: str,
    n_clusters: int = 6
) -> pd.DataFrame:
    """
    Apply K-Means to utterances of one intent class, select one utterance per cluster.

    Selection rule:
        1. Find utterance closest to cluster centroid (minimum L2 distance)
        2. Tiebreak: highest entity count
    """
    n = len(class_df)
    k = min(n_clusters, n)  # can't have more clusters than samples

    if k < 2:
        # Edge case: return what we have
        selected = class_df.copy()
        selected['cluster'] = 0
        selected['task_id'] = [f"{intent}_{str(i+1).zfill(3)}" for i in range(len(selected))]
        return selected.head(k)

    print(f"  [{intent}] K-Means with k={k} on {n} utterances...")
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(embeddings)
    centroids = km.cluster_centers_

    selected_indices = []
    for cluster_id in range(k):
        cluster_mask = labels == cluster_id
        cluster_indices = np.where(cluster_mask)[0]
        cluster_embeddings = embeddings[cluster_mask]

        # Distance to centroid
        centroid = centroids[cluster_id]
        distances = np.linalg.norm(cluster_embeddings - centroid, axis=1)
        min_dist = distances.min()

        # All indices tied at minimum distance (or within floating point tolerance)
        tied_positions = np.where(np.isclose(distances, min_dist, atol=1e-6))[0]
        tied_global_indices = cluster_indices[tied_positions]

        if len(tied_global_indices) == 1:
            selected_indices.append(int(tied_global_indices[0]))
        else:
            # Tiebreak: entity richness
            entity_counts = class_df.iloc[tied_global_indices].apply(count_entities, axis=1).values
            best_tied_pos = np.argmax(entity_counts)
            selected_indices.append(int(tied_global_indices[best_tied_pos]))

    selected = class_df.iloc[selected_indices].copy()
    selected['cluster'] = [labels[i] for i in selected_indices]
    return selected


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    # 1. Load dataset
    print("Loading dataset...")
    df = pd.read_csv(DATASET_PATH)
    print(f"  Loaded {len(df)} rows, columns: {list(df.columns)}")

    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]

    # Drop duplicate entity columns (e.g., language.1, framework.2, error_type.3, etc.)
    # Keep only columns without a numeric dot-suffix (dataset profile note)
    import re as _re
    clean_cols = [c for c in df.columns if not _re.search(r'\.\d+$', c)]
    df = df[clean_cols]

    print(f"  Cleaned columns: {list(df.columns)}")
    print(f"  Intent distribution:\n{df['intent'].value_counts()}")

    # 2. Load embedding model
    print(f"\nLoading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    # 3. Embed ALL utterances (do once, slice by class)
    print("\nEmbedding all utterances...")
    all_embeddings = embed_utterances(df['utterance'].tolist(), model)

    # 4. K-Means sampling per intent class
    print("\nSampling tasks per intent class...")
    all_selected = []
    task_counter = {}

    for intent in VALID_INTENTS:
        class_mask = df['intent'] == intent
        class_df = df[class_mask].reset_index(drop=True)
        class_embeddings = all_embeddings[class_mask.values]

        selected = select_tasks_for_class(class_df, class_embeddings, intent, CLUSTERS_PER_CLASS)

        # Assign task IDs
        if intent not in task_counter:
            task_counter[intent] = 0
        task_ids = []
        for _ in range(len(selected)):
            task_counter[intent] += 1
            task_ids.append(f"{intent}_{str(task_counter[intent]).zfill(3)}")
        selected['task_id'] = task_ids

        print(f"  [{intent}] Selected {len(selected)} tasks")
        all_selected.append(selected)

    selected_df = pd.concat(all_selected, ignore_index=True)

    # 5. Validation
    assert len(selected_df) == CLUSTERS_PER_CLASS * len(VALID_INTENTS), \
        f"Expected {CLUSTERS_PER_CLASS * len(VALID_INTENTS)} tasks, got {len(selected_df)}"
    assert selected_df['task_id'].nunique() == len(selected_df), "Duplicate task IDs!"
    assert selected_df['utterance'].nunique() == len(selected_df), "Duplicate utterances!"

    print(f"\n[OK] Selected {len(selected_df)} single-intent tasks")
    print(f"   Intent breakdown: {selected_df['intent'].value_counts().to_dict()}")

    # 6. Save CSV
    selected_df.to_csv(OUTPUT_CSV, index=False)
    print(f"   Saved -> {OUTPUT_CSV}")

    # 7. Build tasks_raw.json
    tasks_raw = []

    for _, row in selected_df.iterrows():
        task = {
            "task_id": row['task_id'],
            "intent": row['intent'],
            "raw_utterance": row['utterance'],
            "source": "dataset_sampled",
            "cluster": int(row.get('cluster', 0)),
            "entities_in_source": {
                "language": row.get('language', None) if pd.notna(row.get('language', None)) else None,
                "framework": row.get('framework', None) if pd.notna(row.get('framework', None)) else None,
                "error_type": row.get('error_type', None) if pd.notna(row.get('error_type', None)) else None
            }
        }
        # Clean null values
        for k, v in task['entities_in_source'].items():
            if isinstance(v, float) and np.isnan(v):
                task['entities_in_source'][k] = None
        tasks_raw.append(task)

    # Append composite tasks
    for ct in COMPOSITE_TASKS:
        tasks_raw.append({
            "task_id": ct["task_id"],
            "intent": ct["intent"],
            "sub_intents": ct["sub_intents"],
            "raw_utterance": ct["raw_utterance"],
            "source": "manually_authored",
            "cluster": None,
            "entities_in_source": {}
        })

    # Final validation
    all_ids = [t['task_id'] for t in tasks_raw]
    assert len(all_ids) == 48, f"Expected 48 tasks total, got {len(all_ids)}"
    assert len(set(all_ids)) == 48, "Duplicate task IDs in tasks_raw!"

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(tasks_raw, f, indent=2, ensure_ascii=False)
    print(f"   Saved -> {OUTPUT_JSON} ({len(tasks_raw)} total tasks: 42 sampled + 6 composite)")

    # 8. Summary
    print("\n" + "="*60)
    print("PHASE 1.1 + 1.2 COMPLETE")
    print(f"  selected_tasks_base.csv : {len(selected_df)} tasks")
    print(f"  tasks_raw.json          : {len(tasks_raw)} tasks (42 + 6 composite)")
    print("="*60)
    print("\nNEXT STEP: Run the gold standard definition process.")
    print("  -> See data/tasks_raw.json for the full task list.")
    print("  -> Manually add gold standards to produce data/tasks_master.json")
    print("    OR run: python src/2_generate_conditions.py --gold-standard-mode")


if __name__ == '__main__':
    main()
