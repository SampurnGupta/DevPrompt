"""
build_tasks_master.py — Assemble tasks_master.json from tasks_raw.json + gold standards.

Merges:
  - data/tasks_raw.json          (48 tasks with raw utterances)
  - gold_standards_part1.py      (debug + generate)
  - gold_standards_part2.py      (refactor + explain)
  - gold_standards_part3.py      (scaffold + test + document + composite)

Then pre-computes intent_preservation_embedding for each task using all-MiniLM-L6-v2.
Output: data/tasks_master.json

Usage:
    python src/build_tasks_master.py
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gold_standards_part1 import DEBUG_GENERATE
from gold_standards_part2 import REFACTOR_EXPLAIN
from gold_standards_part3 import SCAFFOLD_TEST_DOCUMENT_COMPOSITE

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

def main():
    # 1. Merge all gold standard dicts
    all_gold = {}
    all_gold.update(DEBUG_GENERATE)
    all_gold.update(REFACTOR_EXPLAIN)
    all_gold.update(SCAFFOLD_TEST_DOCUMENT_COMPOSITE)
    print(f"Loaded {len(all_gold)} gold standard definitions")

    # 2. Load tasks_raw.json
    tasks_raw_path = os.path.join(DATA_DIR, 'tasks_raw.json')
    with open(tasks_raw_path, encoding='utf-8') as f:
        tasks_raw = json.load(f)
    print(f"Loaded {len(tasks_raw)} raw tasks")

    # 3. Load embedding model
    print("Loading all-MiniLM-L6-v2 for embedding pre-computation...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # 4. Merge and compute embeddings
    tasks_master = []
    missing_gold = []

    for task in tasks_raw:
        tid = task['task_id']
        if tid not in all_gold:
            missing_gold.append(tid)
            continue

        gold = all_gold[tid]
        ref = gold['intent_preservation_reference']
        print(f"  Embedding [{tid}]: {ref[:60]}...")
        embedding = model.encode(ref).tolist()

        master_task = {
            "task_id": tid,
            "intent": task['intent'],
            "raw_utterance": task['raw_utterance'],
            "source": task.get('source', 'dataset_sampled'),
            "gold_standard": {
                "functional_output_description": gold['functional_output_description'],
                "intent_preservation_reference": ref,
                "intent_preservation_embedding": embedding,
                "expected_tools": gold['expected_tools'],
                "minimum_required_tools": gold['minimum_required_tools'],
                "alternative_tool_sequences": gold.get('alternative_tool_sequences', []),
                "entities": gold['entities']
            },
            "has_unit_test": gold['has_unit_test'],
            "unit_test_path": gold['unit_test_path']
        }
        if 'sub_intents' in task:
            master_task['sub_intents'] = task['sub_intents']

        tasks_master.append(master_task)

    if missing_gold:
        print(f"WARNING: No gold standard found for: {missing_gold}")

    # 5. Validate
    assert len(tasks_master) == 48, f"Expected 48, got {len(tasks_master)}"
    ids = [t['task_id'] for t in tasks_master]
    assert len(set(ids)) == 48, "Duplicate task IDs!"
    for t in tasks_master:
        assert t['gold_standard']['intent_preservation_embedding'], f"Missing embedding: {t['task_id']}"
        assert t['gold_standard']['expected_tools'], f"Empty expected_tools: {t['task_id']}"

    # 6. Save
    out_path = os.path.join(DATA_DIR, 'tasks_master.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(tasks_master, f, indent=2, ensure_ascii=False)

    unit_test_count = sum(1 for t in tasks_master if t['has_unit_test'])
    print(f"\n[DONE] tasks_master.json saved -> {out_path}")
    print(f"  Total tasks      : {len(tasks_master)}")
    print(f"  With unit tests  : {unit_test_count}")
    print(f"  Without          : {len(tasks_master) - unit_test_count}")
    print(f"\nNEXT: python src/2_generate_conditions.py")

if __name__ == '__main__':
    main()
