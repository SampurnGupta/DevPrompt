# DevPrompt — Gold Standard Audit & Planned Changes

> **Purpose:** Complete audit of all 48 gold standard definitions.
> What is currently defined, what is wrong with it, and exactly what to change.
> Changes must be applied in `src/gold_standards_part1/2/3.py` then rebuilt via `build_tasks_master.py`.

---

## 1. Current Gold Standard Structure (Per Task)

Each task in `tasks_master.json` has:

| Field | Type | Purpose |
|-------|------|---------|
| `functional_output_description` | string | 2-3 sentences: what a correct solution looks like |
| `intent_preservation_reference` | string | Short gold paraphrase (10-15 words) used for intent scoring |
| `expected_tools` | list[str] | Ordered list of tools the ideal response uses |
| `minimum_required_tools` | list[str] | Bare minimum tools — if called, task is considered "attempted" |
| `entities` | dict | error_type, component, language, framework |
| `has_unit_test` | bool | Whether a pytest file is planned |
| `unit_test_path` | str\|None | Path to the test file |

**Two derived fields added by `build_tasks_master.py`:**
- `intent_preservation_embedding` — `all-MiniLM-L6-v2` vector of the reference paraphrase
- `gold_standard` — wrapper dict containing all the above

---

## 2. Identified Problems Across All Gold Standards

### Problem A — `expected_tools` is a single sequence; multiple valid sequences exist

The metric computes Tool F1 as set intersection of called tools vs. `expected_tools`. This means:
- A model that calls `[read_file, search_codebase, write_file]` vs expected `[search_codebase, read_file, write_file]` gets F1=1.0 ✅ (set match)
- A model that calls `[read_file, write_file]` vs expected `[search_codebase, read_file, write_file]` gets Recall=0.67 ❌ even though this may be perfectly valid

**Fix:** Add `alternative_tool_sequences` field (list of lists) with 1-2 additional valid sequences per task. Score against the best-matching sequence across all alternatives.

### Problem B — `minimum_required_tools` is too permissive for debug tasks

Every debug task has `minimum_required_tools = ["read_file", "write_file"]`. This means calling those two tools — even with completely wrong content — counts as a success (`min_req_met = True`). For diagnostic tasks, you must also search or inspect; for fix tasks, you must at minimum run or verify.

**Fix:** Strengthen minimum required tools for debug tasks to include at least one diagnostic tool (`search_codebase` or `execute_shell`).

### Problem C — `intent_preservation_reference` is too short (10-15 words)

The reference paraphrase is used to compute cosine similarity with the full LLM response (200-800 words). A 12-word sentence embedded in 384 dimensions will always have low similarity to a long paragraph — **this is a length artifact, not a semantic one**. This is the root cause of Condition C's paradoxical low intent preservation score.

**Fix (already planned):** Replace cosine similarity metric with LLM-as-judge. However, the reference should also be **extended** to include the `functional_output_description` content so the judge has a richer target to evaluate against.

### Problem D — `expected_tools` for `explain` tasks only lists 1-2 tools — acceptable

For explain tasks, a model that produces a thorough explanation using only `fetch_docs` (and no file tools) is perfectly valid. The current gold standards correctly reflect this.

### Problem E — `minimum_required_tools` for `test` tasks includes `run_tests` — potentially unfair

Tasks like `test_001` through `test_003` require `run_tests` as a minimum required tool. But in a declarative (non-executable) evaluation where tools are not actually run, requiring `run_tests` penalizes a model that writes perfect test code but doesn't declare `run_tests`. This inflates failure rates for test tasks artificially.

**Fix:** Remove `run_tests` from `minimum_required_tools` for pure test-writing tasks. Keep it in `expected_tools` (the ideal sequence still includes it).

### Problem F — Scaffold tasks have `minimum_required_tools = ["write_file"]` only — too weak

A scaffold task that calls only `write_file` without any structure (`execute_shell` for npm init, `fetch_docs` for dependency lookup) gets counted as a minimum success. This doesn't reflect real scaffold quality.

**Fix:** Add `execute_shell` or `fetch_docs` to `minimum_required_tools` for scaffold tasks where project setup is clearly the goal.

---

## 3. Task-by-Task Planned Changes

### 3.1 DEBUG Tasks (debug_001 to debug_006)

| Task | Current min tools | Problem | Fix |
|------|------------------|---------|-----|
| debug_001 | `[read_file, write_file]` | Can "succeed" without ever searching for the bug | Add `search_codebase` to minimum |
| debug_002 | `[read_file, write_file]` | Same as above | Add `search_codebase` to minimum |
| debug_003 | `[read_file, write_file]` | Same | Add `search_codebase` to minimum |
| debug_004 | `[read_file, write_file]` | Docker OOM — should at minimum run a shell command to inspect | Add `execute_shell` to minimum |
| debug_005 | `[read_file, write_file]` | Android OOM crash — should search for the crash site | Add `search_codebase` to minimum |
| debug_006 | `[read_file, write_file]` | Memory leak — must search to locate it | Add `search_codebase` to minimum |

**Alternative tool sequences to add** (examples):
```python
# debug_001 — alternative: read before search
"alternative_tool_sequences": [
    ["read_file", "search_codebase", "write_file", "run_tests"],  # read first, then search
    ["search_codebase", "read_file", "write_file"]               # skip tests
]
```

### 3.2 GENERATE Tasks (generate_001 to generate_006)

| Task | Current min tools | Problem | Fix |
|------|------------------|---------|-----|
| generate_001 | `[write_file]` | React component without ever fetching docs — marginally acceptable | Keep as-is |
| generate_002 | `[write_file]` | Django JWT middleware without docs is risky — under-specified | Add `fetch_docs` to minimum |
| generate_003 | `[write_file]` | Pandas script — write_file alone is sufficient | Keep as-is |
| generate_004 | `[write_file]` | Express endpoint with bcrypt/JWT — should at minimum fetch docs | Add `fetch_docs` to minimum |
| generate_005 | `[write_file]` | Bash backup script — write_file alone is reasonable | Keep as-is |
| generate_006 | `[write_file]` | SQL query — write_file alone is reasonable | Keep as-is |

**Alternative tool sequences to add** (examples):
```python
# generate_001 — alternative: fetch docs first is optional
"alternative_tool_sequences": [
    ["write_file"],           # model generates from memory, no docs needed
    ["write_file", "lint_code"]  # model also lints
]
```

### 3.3 REFACTOR Tasks (refactor_001 to refactor_006)

| Task | Current min tools | Problem | Fix |
|------|------------------|---------|-----|
| refactor_001 | `[read_file, write_file]` | Microservice extraction — must search to understand structure | Add `search_codebase` to minimum |
| refactor_002 | `[read_file, write_file]` | Renaming — read + write is sufficient | Keep as-is |
| refactor_003 | `[read_file, write_file]` | Strategy pattern — read + write is sufficient | Keep as-is |
| refactor_004 | `[read_file, write_file]` | async/await conversion — lint after is valuable | Keep as-is; add `lint_code` to alternatives |
| refactor_005 | `[read_file, write_file]` | Extract validation — must search imports | Add `search_codebase` to minimum |
| refactor_006 | `[read_file, write_file]` | Simplify payment logic — read + write sufficient | Keep as-is |

### 3.4 EXPLAIN Tasks (explain_001 to explain_006)

All explain tasks have `minimum_required_tools = ["read_file"]` or `["fetch_docs"]`. These are reasonable for explanation-focused tasks. **No minimum tool changes needed.**

However, `expected_tools` for `explain_003` lists `execute_shell` to test a regex pattern — this is insightful but may be too specific. Add an alternative without `execute_shell`.

### 3.5 SCAFFOLD Tasks (scaffold_001 to scaffold_006)

| Task | Current min tools | Problem | Fix |
|------|------------------|---------|-----|
| scaffold_001 | `[write_file]` | Node.js/TS/Next.js scaffold without running any shell command is underspecified | Add `execute_shell` to minimum |
| scaffold_002 | `[write_file]` | Flutter/Firebase — write_file alone is marginal | Add `fetch_docs` to minimum |
| scaffold_003 | `[write_file]` | Django project — shell for django-admin startproject makes sense | Add `execute_shell` to minimum |
| scaffold_004 | `[write_file]` | Terraform — write_file alone for infrastructure is ok | Keep as-is |
| scaffold_005 | `[write_file]` | Monorepo — `execute_shell` for npm init is essential | Add `execute_shell` to minimum |
| scaffold_006 | `[write_file]` | Data science project — write_file alone reasonable | Keep as-is |

### 3.6 TEST Tasks (test_001 to test_006)

| Task | Current min tools | Problem | Fix |
|------|------------------|---------|-----|
| test_001 | `[write_file, run_tests]` | Requiring `run_tests` penalizes models that write perfect tests but don't declare run | Remove `run_tests` from minimum; keep in expected |
| test_002 | `[write_file, run_tests]` | Same | Remove `run_tests` from minimum |
| test_003 | `[write_file, run_tests]` | Same | Remove `run_tests` from minimum |
| test_004 | `[write_file]` | Locust load tests — write_file alone is ok | Keep as-is |
| test_005 | `[write_file, run_tests]` | Same issue as above | Remove `run_tests` from minimum |
| test_006 | `[write_file]` | Fixture only — write_file alone is ok | Keep as-is |

> **Why:** In our declarative evaluation, `run_tests` is never actually executed. Requiring it as a minimum means a model is penalized for not *declaring* a tool call, not for failing to test. This inflates the failure rate for test tasks specifically and is one reason `test` intent has the lowest Tool F1 under all conditions.

### 3.7 DOCUMENT Tasks (document_001 to document_006)

All document tasks have `minimum_required_tools = ["read_file", "write_file"]`. These are reasonable. **No changes needed.**

Exception: `document_004` (CHANGELOG) lists `git_diff` in expected tools — valid since changelog writing requires reviewing what changed. But `minimum_required_tools` only has `write_file`. Add `git_diff` to minimum for this task.

### 3.8 COMPOSITE Tasks (composite_001 to composite_006)

Composite tasks combine two intents. Their minimum required tools should reflect both sub-intents.

| Task | Sub-intents | Current min | Issue | Fix |
|------|------------|-------------|-------|-----|
| composite_001 | debug + test | `[read_file, write_file, run_tests]` | Good — covers both sub-tasks | Keep |
| composite_002 | refactor + document | `[read_file, write_file]` | No document-specific tool (git_diff for diff) | Add `git_diff` to minimum |
| composite_003 | explain + generate | `[read_file, write_file]` | `fetch_docs` missing for explain part | Add `fetch_docs` to minimum |
| composite_004 | scaffold + test | `[write_file, run_tests]` | Missing `execute_shell` for scaffold | Add `execute_shell` to minimum |
| composite_005 | debug + document | `[read_file, write_file]` | Missing diagnostic tool for debug | Add `search_codebase` to minimum |
| composite_006 | generate + explain | `[write_file]` | Missing `read_file` for explain part | Add `read_file` to minimum |

---

## 4. New Field to Add: `alternative_tool_sequences`

Add this field to every gold standard definition. It contains 1-2 additional valid tool orderings or subsets.

**Format:**
```python
"alternative_tool_sequences": [
    ["tool_a", "tool_b", "tool_c"],   # alternative 1
    ["tool_a", "tool_c"]              # alternative 2 (minimal but valid)
]
```

**Scoring change in `src/utils/metrics.py`:**
- Compute Tool F1 against `expected_tools` AND each `alternative_tool_sequences` entry
- Use the **best** (highest) F1 score as the task's Tool F1
- This prevents penalizing correct but differently-ordered responses

**Code change in `compute_agentic_metrics()`:**
```python
all_sequences = [gold['expected_tools']] + gold.get('alternative_tool_sequences', [])
best_f1 = 0.0
for seq in all_sequences:
    expected_set = set(seq)
    correct = actual_set & expected_set
    p = len(correct) / len(actual_set) if actual_set else 0.0
    r = len(correct) / len(expected_set) if expected_set else 0.0
    f1 = 2*p*r/(p+r) if (p+r) > 0 else 0.0
    if f1 > best_f1:
        best_f1 = f1
        best_precision, best_recall = p, r
```

---

## 5. `intent_preservation_reference` — What to Change

Currently: short paraphrase (10-15 words) used for cosine similarity → being replaced by LLM-as-judge.

**For the LLM judge, the reference should be richer.** Update each task's reference to combine the short paraphrase with 1-2 key acceptance criteria from `functional_output_description`.

**Example (debug_001):**
```
Current: "Fix the database connection timeout that causes an infinite loop."

Improved: "Fix the database connection timeout that causes an infinite retry loop.
           Solution must implement exponential backoff or a max-retry limit with proper exception handling."
```

This gives the judge enough context to distinguish "the model acknowledged the timeout" from "the model actually proposed a correct fix strategy."

**Apply this improvement** to all 48 tasks when updating the gold standard files.

---

## 6. Summary of All Changes

| Change | Affects | Tasks | Effort |
|--------|---------|-------|--------|
| Add `alternative_tool_sequences` | `gold_standards_part*.py` + `metrics.py` | All 48 | High — 1-2 per task |
| Strengthen debug `minimum_required_tools` | `gold_standards_part1.py` | debug_001-006 | Low — 6 lines |
| Add `fetch_docs` to generate minimum | `gold_standards_part1.py` | generate_002, 004 | Low — 2 lines |
| Add search/shell to scaffold minimum | `gold_standards_part3.py` | scaffold_001, 002, 003, 005 | Low — 4 lines |
| Remove `run_tests` from test minimum | `gold_standards_part3.py` | test_001, 002, 003, 005 | Low — 4 lines |
| Add composite sub-intent tools to minimum | `gold_standards_part3.py` | composite_002-006 | Low — 5 lines |
| Extend `intent_preservation_reference` | `gold_standards_part*.py` | All 48 | Medium — 48 edits |
| Update `compute_agentic_metrics()` for best-F1 | `src/utils/metrics.py` | All tasks (scoring logic) | Medium — 15 lines |
| Rebuild `tasks_master.json` | `src/build_tasks_master.py` | Triggered automatically | Low — run script |
| Re-run scoring on updated gold standards | `src/4_score_results.py` | All 432 rows | High — API calls not needed; re-score from stored responses |

---

## 7. Impact on Results After These Changes

| Metric | Expected direction | Reason |
|--------|-------------------|--------|
| Tool F1 (overall) | ↑ Higher | Best-sequence scoring stops penalizing valid alternatives |
| Min Req Met rate | ↑ Higher for debug, scaffold; ↓ slightly for test | Removing `run_tests` from test minimum; adding diagnostic tools to debug minimum but those tools may now be called more often under C |
| CPSTC | Changes alongside Min Req Met | More successes → lower CPSTC |
| Condition B Tool F1 | ↑ May improve relatively | B's lower F1 is partly because models choose valid-but-different sequences |
| Test intent Tool F1 | ↑ Noticeably | Removing `run_tests` from minimum eliminates a major false-negative source |

> ⚠️ **Important:** These gold standard changes will produce different result numbers than the current tables. Both sets of results should be preserved — the current results are based on the original gold standards, and the revised results on the improved gold standards. The paper should describe the revision as a methodology improvement and report both if needed, or clearly state which gold standard version was used.

---

## 8. Files to Modify

| File | Change |
|------|--------|
| `src/gold_standards_part1.py` | Add `alternative_tool_sequences`; extend `intent_preservation_reference`; fix debug + generate minimums |
| `src/gold_standards_part2.py` | Add `alternative_tool_sequences`; extend `intent_preservation_reference`; fix explain alternatives |
| `src/gold_standards_part3.py` | Add `alternative_tool_sequences`; extend `intent_preservation_reference`; fix scaffold/test/composite minimums |
| `src/utils/metrics.py` | Update `compute_agentic_metrics()` to score against best-matching sequence |
| `src/build_tasks_master.py` | Re-run after any gold standard change → rebuilds `data/tasks_master.json` |
| `src/4_score_results.py` | Re-run in rescore mode to apply updated gold standards to stored responses |
