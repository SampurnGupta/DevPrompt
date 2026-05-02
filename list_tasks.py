import json
data = json.load(open('data/conditions_all.json', encoding='utf-8'))
# Show a sample: one from each intent group
samples = ['debug_003', 'generate_002', 'refactor_003', 'explain_004', 'scaffold_003', 'test_002', 'document_005', 'composite_001']
for tid in samples:
    t = next(x for x in data if x['task_id'] == tid)
    print(f"\n=== {tid} ===")
    print(f"A: {t['condition_a']}")
    print(f"B: {t['condition_b']}")
    c = t['condition_c']
    print(f"C: intent={c['intent']} | conf={c['confidence_score']}")
    print(f"   normalized={c['normalized']}")
    print(f"   entities={c['entities']}")
