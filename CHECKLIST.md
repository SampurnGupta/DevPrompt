# DevPrompt — Execution Checklist

> Execute tasks **within each group in order**. Groups 2–6 can run in parallel once Groups 0 + 1 are done.
> See `METHODOLOGY_AND_FLOW.md` for full context, code snippets, and rationale.
> See `GOLD_STANDARD_AUDIT.md` for task-by-task gold standard audit and all planned changes.
> **Data re-collection NOT required.** All 432 API results are stored in `data/results.db`.

---

## ⚫ Group 0 — Gold Standard Improvements (Do First)

These change the evaluation criteria. After any change here: rebuild `tasks_master.json` → re-score tool metrics (no new API calls needed).

- [x] **0.1 — Strengthen `minimum_required_tools` for debug tasks**
  - **File:** `src/gold_standards_part1.py`
  - Add `search_codebase` to minimum for debug_001, 002, 003, 005, 006
  - Add `execute_shell` for debug_004 (Docker OOM — shell needed to inspect)
  - **Why:** `[read_file, write_file]` only — a model can read + write hallucinated content and count as a success

- [x] **0.2 — Remove `run_tests` from `minimum_required_tools` for test-writing tasks**
  - **File:** `src/gold_standards_part3.py`
  - Remove `run_tests` from minimum for test_001, test_002, test_003, test_005
  - Keep `run_tests` in `expected_tools` (ideal sequence still includes it)
  - **Why:** Declarative evaluation — `run_tests` is never executed. Requiring it as minimum inflates false-failure rate for the `test` intent

- [x] **0.3 — Strengthen `minimum_required_tools` for scaffold tasks**
  - **File:** `src/gold_standards_part3.py`
  - Add `execute_shell` to minimum for scaffold_001, scaffold_003, scaffold_005
  - Add `fetch_docs` for scaffold_002
  - **Why:** `write_file` alone cannot realistically scaffold a project — no init, no dependency lookup

- [x] **0.4 — Strengthen `minimum_required_tools` for composite tasks**
  - **File:** `src/gold_standards_part3.py`
  - composite_002: add `git_diff` | composite_003: add `fetch_docs` | composite_004: add `execute_shell` | composite_005: add `search_codebase` | composite_006: add `read_file`
  - **Why:** Composite tasks span two intents — minimums must require at least one tool per sub-intent

- [x] **0.5 — Add `alternative_tool_sequences` to all 48 tasks** *(most impactful)*
  - **Files:** All three `gold_standards_part*.py`
  - Add `"alternative_tool_sequences": [[...], [...]]` — 1-2 valid alternatives per task
  - **Why:** Single gold sequence penalizes valid differently-ordered responses. E.g., `[read_file, search_codebase, write_file]` is as correct as `[search_codebase, read_file, write_file]` for a debug task
  - See `GOLD_STANDARD_AUDIT.md` Section 3 for task-by-task alternatives
  - Priority order: debug → generate → composite → refactor → scaffold → test → explain → document

- [x] **0.6 — Extend `intent_preservation_reference` for all 48 tasks**
  - **Files:** All three `gold_standards_part*.py`
  - Extend each 10-15 word paraphrase to include 1-2 key acceptance criteria from `functional_output_description`
  - **Why:** Short paraphrases give the LLM-as-judge insufficient context to evaluate intent fidelity quality
  - Example: `"Fix the database connection timeout."` → `"Fix the database connection timeout causing an infinite retry loop. Solution must implement exponential backoff or a max-retry limit with proper exception handling."`

- [x] **0.7 — Update `compute_agentic_metrics()` to score against best-matching sequence**
  - **File:** `src/utils/metrics.py` lines 84-118
  - Loop over `expected_tools` + `alternative_tool_sequences`; take highest F1
  - **Code:**
    ```python
    all_sequences = [gold['expected_tools']] + gold.get('alternative_tool_sequences', [])
    best_f1, best_p, best_r = 0.0, 0.0, 0.0
    for seq in all_sequences:
        expected_set = set(seq)
        correct = actual_set & expected_set
        p = len(correct)/len(actual_set) if actual_set else 0.0
        r = len(correct)/len(expected_set) if expected_set else 0.0
        f1 = 2*p*r/(p+r) if (p+r) > 0 else 0.0
        if f1 > best_f1:
            best_f1, best_p, best_r = f1, p, r
    ```
  - **Why:** Without this change, `alternative_tool_sequences` has no effect on scoring

- [x] **0.8 — Update `build_tasks_master.py` to propagate `alternative_tool_sequences`**
  - **File:** `src/build_tasks_master.py` line 65-74 (`gold_standard` dict assembly)
  - Add `"alternative_tool_sequences": gold.get('alternative_tool_sequences', [])` to the dict
  - **Why:** Currently the script does not include this field in the output `tasks_master.json`, so the scorer would never see it

- [x] **0.9 — Rebuild `tasks_master.json` and re-score tool metrics**
  - Run: `python src/build_tasks_master.py`
  - Add `--rescore-tools` mode to `4_score_results.py` (re-read stored responses from `results` table; re-run `compute_agentic_metrics()`; update tool metric columns in `scores` table — **no new API calls**)
  - Backup original: `CREATE TABLE scores_original AS SELECT * FROM scores` before overwriting
  - Run: `python src/4_score_results.py --rescore-tools`

---

## 🔴 Group 1 — Critical Code Fixes (Do Before Any Re-Analysis)

- [x] **1.1 — Fix statistical test: `ttest_ind` → `ttest_rel`**
  - **File:** `src/5_analyze_results.py` line 112
  - **Bug:** `stats.ttest_ind(cond_c_f1, cond_a_f1)` — independent test on within-subjects data; inflates df from 48 to 144
  - **Fix:** Pivot by `(task_id, model)` → run `ttest_rel` for all three pairs (A vs C, A vs B, B vs C):
    ```python
    pivot = df.pivot_table(index=['task_id','model'], columns='condition', values='tool_f1')
    t_ac, p_ac = stats.ttest_rel(pivot['c'].dropna(), pivot['a'].dropna())
    t_ab, p_ab = stats.ttest_rel(pivot['b'].dropna(), pivot['a'].dropna())
    t_bc, p_bc = stats.ttest_rel(pivot['c'].dropna(), pivot['b'].dropna())
    ```

- [x] **1.2 — Consolidate Cohen's d to one implementation**
  - **File:** `src/5_analyze_results.py` lines 99-105
  - **Bug:** Inline formula uses biased `.std()` (`ddof=0`); correct version in `src/utils/metrics.py`
  - **Fix:** Delete lines 99-105; `from src.utils.metrics import cohens_d`; call for all three pairs

- [x] **1.3 — Add Bonferroni correction and corrected α**
  - **File:** `src/5_analyze_results.py`
  - **Bug:** Single α=0.05 used; 3 pairs × 4 primary metrics = 12 comparisons → α should be ≈ 0.004
  - **Fix:** Compute `corrected_alpha = 0.05 / 12`; report alongside each p-value; mark significance at corrected threshold

- [x] **1.4 — Add 95% CIs to all reported means**
  - **File:** `src/5_analyze_results.py`
  - **Bug:** `confidence_interval_95()` exists in `metrics.py` but is never called from the analysis script
  - **Fix:** Apply `confidence_interval_95()` to all per-condition, per-model means in Table 1 and Table 2

- [x] **1.5 — Fix "skip already scored" bug in `4_score_results.py`**
  - **File:** `src/4_score_results.py` line 104-110
  - **Bug:** Query does not filter already-scored runs — running the script twice rescores all 432 rows and wastes API calls
  - **Fix:** Add `AND s.run_id IS NULL` to the WHERE clause to skip rows that already have a score entry

- [x] **1.6 — Add rescore modes to `4_score_results.py`**
  - **File:** `src/4_score_results.py`
  - **Bug:** No way to rescore only tool metrics (from updated gold standards) without re-running all API calls
  - **Fix:** Add `--rescore-tools` (re-compute tool metrics from stored `tool_calls_json`), `--rescore-intent` (re-run intent fidelity judge), `--rescore-functional` (re-run Pass@1 pytest)

- [x] **1.7 — Fix Condition A label in `3_run_experiment.py`**
  - **File:** `src/3_run_experiment.py` line 89
  - **Bug:** `"Voice transcription (may contain filler words and informal speech):"` — inconsistent with new research framing
  - **Fix:** `"Developer request:"`
  - Note: This affects future runs only. The 432 stored prompts already contain the old label but it is metadata and does not affect scoring.

- [x] **1.8 — Fix `api_clients.py` header comment**
  - **File:** `src/utils/api_clients.py` line 15
  - **Bug:** References `qwen-3-235b-a22b-instruct-2507` (original planned model); actual model is `llama3.1-8b`
  - **Fix:** Update to `"Cerebras: llama3.1-8b"`

- [x] **1.9 — Fix figure docstring in `6_generate_figures.py`**
  - **File:** `src/6_generate_figures.py` lines 3-12
  - **Bug:** Docstring says "6 main figures" and lists only 6 — actual output is 15 figures
  - **Fix:** Update docstring to list all 15 figures correctly

---

## 🟠 Group 2 — Database Schema Additions (Before Re-Scoring)

Run these SQL statements against `data/results.db` before running any new scoring:

- [x] **2.1 — Add `intent_fidelity_score` column**
  ```sql
  ALTER TABLE scores ADD COLUMN intent_fidelity_score INTEGER DEFAULT NULL;
  ```

- [x] **2.2 — Add `functional_correct` column**
  ```sql
  ALTER TABLE scores ADD COLUMN functional_correct BOOLEAN DEFAULT NULL;
  ```

- [x] **2.3 — Verify schema and row count**
  ```sql
  SELECT COUNT(*) FROM scores;                                          -- expect 432
  PRAGMA table_info(scores);                                            -- confirm new columns exist
  SELECT COUNT(*) FROM scores WHERE intent_fidelity_score IS NOT NULL; -- expect 0 before rescoring
  ```

---

## 🟠 Group 3 — Scoring Additions (Run After Groups 0 + 2)

- [x] **3.1 — Add few-shot TOOL_CALL examples to `TOOL_SYSTEM_PROMPT`**
  - **File:** `src/utils/tool_extraction.py` — append after line 131
  - Add 2-3 concrete `TOOL_CALL:` examples covering debug, generate, explain tasks
  - **Why:** Raises format compliance rate; Gemini ignores the format entirely in zero-shot setting
  - ⚠️ Note: Document in paper that reported results are from the zero-shot prompt; few-shot is an ablation

- [x] **3.2 — Implement `judge_intent_fidelity()` in `4_score_results.py`**
  - Add a second GPT-4o-mini call inside the existing `ThreadPoolExecutor` batch
  - Prompt: "Does the response address the developer's stated task? [0=Not at all / 1=Partially / 2=Mostly / 3=Fully]. JSON: `{\"score\": X}`"
  - Use extended `intent_preservation_reference` as the intent description
  - Store in `scores.intent_fidelity_score`
  - Run: `python src/4_score_results.py --rescore-intent`

- [x] **3.3 — Write unit test files for applicable tasks (~20 files)**
  - Directory: `tests/`
  - Applicable: all tasks where `has_unit_test: True` in `tasks_master.json`
  - Intents: debug (4 tasks: 001,002,003,006), generate (4 tasks: 001,002,003,004), refactor (all 6), test (all 6), composite (all 6)
  - Pattern: each test imports/reads the LLM-generated code block as a fixture and asserts it meets functional acceptance criteria
  - Start with: debug_001, debug_002, generate_001, generate_003 (simplest to verify)

- [x] **3.4 — Implement Pass@1 scoring in `4_score_results.py`**
  - Only for runs where `task.has_unit_test = True`
  - Extract first fenced code block from `response` text using regex
  - Write to `scratch/{run_id}_solution.py`
  - Run: `subprocess.run(['python', '-m', 'pytest', f'tests/{task_id}_test.py', '--tb=no', '-q'], capture_output=True, timeout=10)`
  - Parse exit code 0 = `True`, else `False` → store in `scores.functional_correct`
  - Run: `python src/4_score_results.py --rescore-functional`

- [x] **3.5 — Add Bootstrap CI on CPSTC to `5_analyze_results.py`**
  - Resample `(total_tokens, min_req_met)` pairs 1,000× per condition
  - Compute CPSTC for each resample → report as `2,906 (95% CI: [X, X])`
  - **Why:** Success denominators are 25-32 (out of 144) — single-count swings CPSTC by ~140 tokens

---

## 🟡 Group 4 — Analysis Updates (Run After Groups 0 + 1 + 3)

- [x] **4.1 — Compute Format Compliance Rate from existing data**
  - `SELECT condition, AVG(CASE WHEN total_tool_calls > 0 THEN 1 ELSE 0 END) FROM results GROUP BY condition`
  - Add as `format_compliance_rate` column in Table 1 output
  - **Why:** Separates "wrong tools called" from "no tool declarations made at all"

- [x] **4.2 — Compute Tool Hallucination Rate from existing data**
  - Parse `tool_calls_json` per row; count `valid=False` entries; compute `invalid/total` per condition
  - Add as `tool_hallucination_rate` column in Table 1 or a new Table 4
  - **Why:** Shows whether conditions differ in hallucinated tool name generation

- [x] **4.3 — Add `output_tokens` distribution to Table 1**
  - Already stored in `results.output_tokens`; just add `mean_output_tokens` to `cond_stats` aggregation
  - **Why:** Important context for understanding CPSTC differences and the cosine similarity length bias

- [x] **4.4 — Add Kendall's τ for tool sequence ordering**
  - For runs where `len(actual_tools) >= 2`, compute `scipy.stats.kendalltau(actual_rank, expected_rank)`
  - Report mean τ per condition
  - **Why:** Set-based F1 completely ignores ordering — `read_file → write_file` vs `write_file → read_file` get the same F1 but only one is a sensible workflow

- [x] **4.5 — Add per-intent one-way ANOVA**
  - For each intent class: `scipy.stats.f_oneway(a_scores, b_scores, c_scores)` on Tool F1
  - Report F-statistic and p-value per intent in a new Table 4
  - **Why:** H4 — formally tests whether condition effect varies by intent. Table 3 shows `test` and `refactor` regress under C; ANOVA makes this statistically rigorous

- [x] **4.6 — Add Condition B hallucination deep-dive**
  - Compute per-model B vs A and B vs C hallucination delta
  - Add analysis block: "Text normalization reduces hallucination even without structural improvement to tool selection"
  - Expected: Groq A→B: 0.125→0.083; Cerebras A→B: 0.167→0.083
  - **Why:** Condition B's hallucination rate (0.069) is the best result in the entire study and should not be buried

- [x] **4.7 — Add silhouette score computation**
  - Load embeddings and cluster labels from the task selection step
  - Compute `sklearn.metrics.silhouette_score(class_embeddings, kmeans_labels)` per intent class
  - Report 7 scores in paper methodology section
  - **Why:** Validates that k=6 clusters are semantically meaningful, not random splits

- [x] **4.8 — Add McNemar's test for binary success comparison**
  - Compare `min_req_met` (binary) between conditions A vs C using `statsmodels.stats.contingency_tables.mcnemar`
  - **Why:** More appropriate than t-test for binary success/failure outcomes; complements the paired t-test on continuous Tool F1

- [x] **4.9 — Stratify all results by model in Tables 1 and 2**
  - Currently Table 1 aggregates across all 3 models — Gemini's near-zero F1 distorts the average
  - Add a stratified version of Table 1 showing per-model means alongside the overall aggregate
  - **Why:** Without model stratification, the Gemini format-compliance failure artificially deflates all condition means

- [x] **4.10 — Re-run `5_analyze_results.py` and regenerate all CSVs**
  - Confirm: new p-values, d, CIs, ANOVA, all new columns present in output
  - Save updated tables to `data/`

---

## 🟡 Group 5 — Figure Updates (Run After Group 4)

- [x] **5.1 — Fix Fig 9 (Pareto Frontier) — `Avg_Tokens` computation bug**
  - **File:** `src/6_generate_figures.py` line 167
  - **Bug:** `/ len(df['condition'].unique())` (= /3) — divides total tokens by 3 conditions, not by actual runs
  - **Fix:** `/ (48 * 3)` (= /144, runs per condition) for correct per-run average

- [x] **5.2 — Fix Fig 11 (Success Breakdown) — misleading stacked bars**
  - **File:** `src/6_generate_figures.py` lines 196-208
  - **Bug:** `Eventual Only = min_req_met - first_call_correct` is logically wrong — the two metrics are not mutually exclusive additive quantities. Stacked bar implies they sum to total success, which is false.
  - **Fix:** Replace with grouped bars showing `first_call_correct` and `min_req_met` as independent bars side by side per condition

- [x] **5.3 — Update Fig 1 and Fig 12 after metric replacement**
  - Fig 1: rename y-axis from "Cosine Similarity to Gold Standard" → "Intent Fidelity Score (0–3)"
  - Fig 12: rename y-axis from "Cosine Similarity (Intent)" → "Intent Fidelity Score (0–3)"
  - Update titles accordingly

- [x] **5.4 — Add Fig: Format Compliance Rate by Condition and Model** *(new)*
  - Grouped barplot of `format_compliance_rate` by (condition, model)
  - **Why:** Shows format compliance failure (Gemini ≈ 0%) clearly; explains why aggregate F1 is low

- [x] **5.5 — Add Fig: Kendall's τ Tool Ordering Score by Condition** *(new)*
  - Barplot of mean τ ± 95% CI per condition
  - **Why:** Adds the ordering dimension missing from set-based F1

- [x] **5.6 — Re-run `6_generate_figures.py`** and verify all 15 figures look correct

---

## 🔵 Group 6 — Documentation Cleanup (Can Run Anytime)

- [x] **6.1 — Fix Cerebras model name across all documents**
  - Search all `.md` files for "Llama 3.3 70B (Cerebras)" → replace with "Llama 3.1 8B (Cerebras)"
  - Files: `devprompt_research_context.md`, `walkthrough.md`, `DevPrompt_Project_Summary.md`

- [x] **6.2 — Remove voice transcription framing from research documents**
  - In `devprompt_research_context.md`: update problem statement to "prompt formulation sensitivity"
  - Update hypothesis statements to H1/H2/H3/H4 from `METHODOLOGY_AND_FLOW.md`

- [x] **6.3 — Fix `walkthrough.md` self-contradiction**
  - Remove the "Wait, looking at the heatmap data..." block
  - Replace with resolved statement: "Cerebras showed the strongest hallucination reduction under Condition B (8.3%)"
  - Update metric numbers once Groups 3–5 are complete

- [x] **6.4 — Standardize figure count across all documents**
  - Search for "8 figures", "9 figures", "12 figures" → update to actual count

- [x] **6.5 — Create `requirements.txt`**
  - Run inside `venv`: `pip freeze > requirements.txt`
  - Pin all library versions

- [x] **6.6 — Write dataset provenance paragraph for paper**
  - Must address: source, collection method, label assignment, IRB considerations
  - Without this, no peer reviewer will accept the paper

---

## ✅ Completion Criteria

The project is ready for paper writing when:

- [x] Paired t-test p-values (all 3 pairs) computed and verified
- [x] Cohen's d with 95% CIs computed from `metrics.py` (not inline formula)
- [x] All 432 rows in `scores` have non-null `intent_fidelity_score`
- [x] All applicable rows (~180) have non-null `functional_correct`
- [x] `table1_condition_overall.csv` has ≥10 columns including `format_compliance_rate`, `tool_hallucination_rate`, `intent_fidelity_mean`, `functional_correct_rate`, `mean_output_tokens`, `CPSTC_CI_lower`, `CPSTC_CI_upper`
- [x] Bootstrap CPSTC CIs computed and documented
- [x] Per-intent ANOVA table generated (Table 4)
- [x] Model-stratified Table 1 variant generated
- [x] All figure bugs fixed; 2 new figures generated
- [x] `requirements.txt` exists
- [x] No Cerebras model name inconsistencies remain in any document
- [x] No voice transcription framing remains in research documents
- [x] Dataset provenance paragraph written

---

*Reference: `METHODOLOGY_AND_FLOW.md` — full explanations, code snippets, design rationale.*
*Reference: `GOLD_STANDARD_AUDIT.md` — task-by-task gold standard audit and impact analysis.*
