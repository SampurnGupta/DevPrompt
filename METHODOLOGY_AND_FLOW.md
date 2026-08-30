# DevPrompt — Master Methodology & Flow Document

> **Purpose:** Single source of truth for any person or LLM continuing this research.
> **Last updated:** 2026-08-30
> **Data collection:** ✅ Complete (432 API calls done, scored, stored in `data/results.db`)
> **Current phase:** Gold standard revision → re-scoring → analysis fixes → new metrics

---

## 1. Research Goal

**Research question:**
> How sensitive is LLM agentic performance to the *formulation* of a developer prompt?
> Does expressing a task as an **Intent-Classified Structured JSON** improve LLM tool-selection, output quality, and token efficiency compared to a **plain text** developer request?

**Dropped framing:** Voice transcription pipeline and ASR post-processing — removed as the primary motivation. Voice-like disfluencies in the dataset (um, uh, like) are an incidental property of the utterance style used for Condition A, not the research subject.

---

## 2. Three Conditions (All Retained)

| Condition | Name | Description | Role |
|-----------|------|-------------|------|
| **A** | Simple Prompt | Raw developer task description — natural, unstructured, may contain informal phrasing | **Primary baseline** |
| **B** | Cleaned Prompt | Same text after regex normalization (fillers removed, contractions expanded, capitalized) | **Middle-ground control** |
| **C** | Structured Prompt | Intent-classified JSON: intent label, entities, confidence, normalized utterance | **Primary treatment** |

**Why Condition B must be retained as a full comparison arm:**
- Answers whether *cleaning alone* helps (vs. *structuring* helping)
- Has the best hallucination rate (0.069) — a real finding distinct from tool selection
- Helps isolate whether Condition C's benefit comes from removing noise or from adding structure

**Condition C generation:** Groq Llama 3.3 70B generates the JSON. This is an implementation detail — the research question is whether *receiving* a structured JSON helps the evaluation LLMs, not whether generating it is novel.

**Three pairwise comparisons to report:**
- **A vs C** — primary: does structured prompting improve over simple prompting?
- **A vs B** — does text cleaning alone improve performance?
- **B vs C** — does adding intent structure on top of cleaned text add further value?

---

## 3. Formal Hypotheses

- **H1:** Condition C achieves significantly higher Tool F1 than Condition A (paired within-subjects test, α=0.004 after Bonferroni)
- **H2:** Condition C achieves lower CPSTC than Condition A
- **H3:** Condition B achieves lower hallucination rate than A and C (Condition B's strongest result)
- **H4 (Exploratory):** The Tool F1 benefit of Condition C over A varies significantly across intent categories

---

## 4. Dataset

- **File:** `devflow_dataset.csv`
- **Size:** 1,264 developer task descriptions, 7 intent classes, ~180 per class
- **Classes:** debug, generate, refactor, explain, scaffold, test, document
- **Content:** Natural developer task descriptions (informal phrasing preserved for Condition A)
- **Balance:** Near-perfect; class size std/mean ≈ 0.004
- **Provenance:** ⚠️ Source not documented — must add a paragraph to the paper

---

## 5. Task Selection — K-Means k=6

- **Embedding model:** `all-MiniLM-L6-v2` (384-dim, local, free)
- **Clustering:** K-Means (k=6, `random_state=42`, `n_init=10`) per intent class
- **Selection rule:** Utterance nearest to cluster centroid; tiebreak by entity richness (count of non-null language/framework/error_type fields)
- **Result:** 7 classes × 6 clusters = **42 sampled tasks** + **6 manually-authored composite tasks** = **48 total**

**Why k=6:**
- Balances semantic diversity (k=6 covers 6 distinct phrasings per intent) vs. scale (48×3×3 = 432 calls within free-tier limits)
- k=3 → 21 tasks (too small; misses entity/language diversity)
- k=9 → 63 tasks → 567 calls (exceeds Groq/Gemini daily limits reliably)
- **Validation needed:** Run `sklearn.metrics.silhouette_score` at k=6 per intent class to confirm clusters are meaningful

**Composite tasks:** Manually authored, NOT K-Means sampled. Analyzed separately from the 42 K-Means tasks in per-intent breakdowns.

---

## 6. Gold Standards — Current State & Planned Changes

Each of the 48 tasks has:
`functional_output_description` | `intent_preservation_reference` | `expected_tools` | `minimum_required_tools` | `entities` | `has_unit_test` | `unit_test_path`

Plus two derived fields added by `build_tasks_master.py`: `intent_preservation_embedding`, wrapped in `gold_standard` dict.

### 6.1 Problems Found

| # | Problem | Scope | Impact |
|---|---------|-------|--------|
| A | `expected_tools` is one sequence; valid alternatives are penalized | All 48 | Artificially lowers Tool F1 — valid differently-ordered responses score poorly |
| B | Debug `minimum_required_tools = [read_file, write_file]` too permissive | debug_001–006 | Models can "succeed" by reading + writing hallucinated content |
| C | `run_tests` in test task minimums — unfair in declarative evaluation | test_001/002/003/005 | Inflates false-failure rate for test intent |
| D | Scaffold `minimum_required_tools = [write_file]` too weak | scaffold_001/002/003/005 | A scaffold with no shell/docs counted as success |
| E | Composite minimum tools don't cover both sub-intents | composite_002–006 | One half of each composite task effectively un-evaluated |
| F | `intent_preservation_reference` is 10-15 words vs. 200-800 word responses | All 48 | Root cause of Condition C's paradoxically low intent preservation score |

### 6.2 Planned Changes (Full Detail in `GOLD_STANDARD_AUDIT.md`)

| Change | Files | Tasks | Effect |
|--------|-------|-------|--------|
| Add `alternative_tool_sequences` (1-2 per task) | `gold_standards_part*.py` + `metrics.py` | All 48 | ↑ Tool F1 across all conditions |
| Strengthen debug minimums (add `search_codebase` or `execute_shell`) | `part1.py` | debug_001–006 | ↑ Min Req Met precision for debug intent |
| Remove `run_tests` from test minimums | `part3.py` | test_001/002/003/005 | ↑ Tool F1 for test intent |
| Add `execute_shell`/`fetch_docs` to scaffold minimums | `part3.py` | scaffold_001/002/003/005 | ↑ Min Req Met precision for scaffold |
| Add missing sub-intent tools to composite minimums | `part3.py` | composite_002–006 | ↑ Composite intent coverage |
| Extend `intent_preservation_reference` (add acceptance criteria) | `part*.py` | All 48 | Richer context for LLM-as-judge intent fidelity |
| Update `compute_agentic_metrics()` to score vs. best-matching sequence | `src/utils/metrics.py` | Scoring logic | Implements alternative sequence scoring |
| Rebuild `tasks_master.json` | `build_tasks_master.py` | — | Propagates all gold standard changes |
| Re-score tool metrics from stored responses (no new API calls) | `4_score_results.py` | All 432 rows | Updates results.db with revised scores |

### 6.3 `build_tasks_master.py` — Bug Found

The `build_tasks_master.py` script does NOT propagate `alternative_tool_sequences` to `tasks_master.json`. When this field is added to the gold standard files, the script must be updated to include it in the `gold_standard` dict written to `tasks_master.json`.

---

## 7. What Has Been Implemented ✅

### Phase 1 — Task Selection (`src/1_select_tasks.py`)
- K-Means (k=6) per intent class on `all-MiniLM-L6-v2` embeddings
- Centroid-nearest selection with entity-richness tiebreak
- 6 composite tasks appended
- Output: `data/tasks_raw.json` (48 tasks)

### Phase 1b — Gold Standards (`src/gold_standards_part*.py` + `build_tasks_master.py`)
- 48 gold standards manually defined; embeddings pre-computed
- Output: `data/tasks_master.json`
- ⚠️ See Section 6 for planned changes

### Phase 2 — Condition Generation (`src/2_generate_conditions.py`)
- Condition A: raw utterance as-is
- Condition B: regex cleaning
- Condition C: Groq Llama 3.3 70B structured JSON
- Output: `data/conditions_all.json`

### Phase 3 — Experiment Runner (`src/3_run_experiment.py`)
- 432 API calls across 3 models × 3 conditions × 48 tasks
- Checkpointed via SQLite `--resume`
- Output: `data/results.db` — 432-row `results` table

### Phase 4 — Scoring (`src/4_score_results.py`)
- Tool metrics, hallucination judge, intent preservation (cosine sim)
- Output: `data/results.db` — 432-row `scores` table

### Phase 5 — Analysis (`src/5_analyze_results.py`)
- Tables 1, 2, 3 by condition / model / intent
- ❌ Wrong statistical test (see Section 8, Fix 1)

### Phase 6 — Figures (`src/6_generate_figures.py`)
- 13 publication-ready figures
- ❌ Two known bugs (see Section 8, Fix 6)

### Current Results (Table 1 — Condition Overall)

| Condition | Tool F1 | Min Req Met | CPSTC | Hallucination | First-Call Acc |
|-----------|---------|-------------|-------|---------------|----------------|
| A (Simple) | 0.3222 | 17.36% | 3,670 | 0.1111 | 25.00% |
| B (Cleaned) | 0.2750 | 14.58% | 4,523 | **0.0694** ← best | 17.36% |
| C (Structured JSON) | **0.3978** | **22.22%** | **2,906** | 0.0833 | **31.25%** |

**Key per-intent patterns (Tool F1) worth noting:**

| Intent | A | B | C | Insight |
|--------|---|---|---|---------|
| scaffold | 0.3482 | 0.2000 | **0.6074** | C +75% vs A |
| composite | 0.2370 | 0.1632 | **0.4048** | C +71% vs A |
| explain | 0.2907 | 0.3466 | **0.4741** | B > A (cleaning helps here) |
| refactor | 0.3021 | **0.3959** | 0.3687 | B wins — structure hurts |
| test | **0.3378** | 0.2783 | 0.2509 | A wins — C is worst |
| debug | **0.3598** | 0.3138 | 0.3281 | Minimal condition effect |

---

## 8. What Needs To Be Done 🔧

### Fix 1 — Correct the Statistical Test *(CRITICAL)*
- **File:** `src/5_analyze_results.py` line 112
- **Bug:** `stats.ttest_ind(cond_c_f1, cond_a_f1)` — independent test on within-subjects data
- **Why wrong:** The same 48 tasks × 3 models appear in every condition. `ttest_ind` inflates df from 48 to 144.
- **Fix:** Pivot by `(task_id, model)` → `stats.ttest_rel` for all 3 pairwise comparisons

### Fix 2 — Consolidate Cohen's d *(CRITICAL)*
- **File:** `src/5_analyze_results.py` lines 99-105
- **Bug:** Inline formula uses `.std()` (biased, `ddof=0`); `metrics.py` has correct pooled SD version
- **Fix:** Delete inline block; `from src.utils.metrics import cohens_d`

### Fix 3 — Replace Intent Preservation Metric *(CRITICAL)*
- **File:** `src/4_score_results.py`
- **Bug:** `compute_intent_preservation()` computes cosine similarity of full LLM response vs. 12-word paraphrase → measures verbosity not fidelity
- **Fix:** Add `judge_intent_fidelity()` using GPT-4o-mini (0-3 rubric) inside existing `ThreadPoolExecutor`
- **DB:** `ALTER TABLE scores ADD COLUMN intent_fidelity_score INTEGER DEFAULT NULL`

### Fix 4 — Implement Functional Correctness / Pass@1 *(CRITICAL)*
- **Files:** `tests/` (write ~20 test files), `src/4_score_results.py` (add pytest execution)
- **Bug:** `tests/` directory empty; `aggregate_token_stats()` in `metrics.py` already references `functional_correct` but it's never computed
- **Fix:** Write unit tests; add `subprocess.run(['python', '-m', 'pytest', ...])` in `4_score_results.py`
- **DB:** `ALTER TABLE scores ADD COLUMN functional_correct BOOLEAN DEFAULT NULL`

### Fix 5 — Address Success Rate Floor *(IMPORTANT)*
- **File:** `src/utils/tool_extraction.py` — `TOOL_SYSTEM_PROMPT` (line 116)
- **Bug:** System prompt has zero examples of `TOOL_CALL:` usage; Gemini ignores the format entirely
- **Fix:** Add 2-3 few-shot `TOOL_CALL:` examples to `TOOL_SYSTEM_PROMPT`
- **Additional:** Add Format Compliance Rate and Tool Hallucination Rate to analysis (computable from existing data)

### Fix 6 — Figure Bugs
- **Fig 9 (line 167):** `/ len(df['condition'].unique())` (=3) → should be `/ (48 * 3)` (=144) for per-run avg tokens
- **Fig 11 (lines 196-207):** `min_req_met - first_call_correct` can be negative; stacked bars are logically wrong — replace with grouped bars showing each metric independently
- **Fig 1 (line 67):** Title references "Cosine Similarity" — rename to "Intent Fidelity Score" after metric replacement
- **Fig 12 (line 213):** Same issue — references intent preservation (cosine sim)

### Fix 7 — `build_tasks_master.py` — Missing Field Propagation
- **File:** `src/build_tasks_master.py` line 65-74
- **Bug:** The `gold_standard` dict assembled does NOT include `alternative_tool_sequences` (not yet added) — must be explicitly added when populating `master_task`
- **Fix:** Add `"alternative_tool_sequences": gold.get('alternative_tool_sequences', [])` in the dict

### Fix 8 — `4_score_results.py` — No Rescore Mode
- **Bug:** The script runs `INSERT OR REPLACE` which would overwrite all scores. There is no mode to rescore only specific columns (e.g., only tool metrics after gold standard update)
- **Fix:** Add `--rescore-tools` flag (recompute tool metrics from stored responses, no new API calls) and `--rescore-intent` flag (run intent fidelity judge only)

### Fix 9 — `4_score_results.py` — No Filter for Already-Scored Runs
- **File:** `src/4_score_results.py` line 104-110
- **Bug:** The query `LEFT JOIN scores s ON r.run_id = s.run_id WHERE r.error IS NULL` does NOT filter out already-scored runs. Running the script twice will double-score everything (overwritten by `INSERT OR REPLACE`, but wastes API calls)
- **Fix:** Add `AND s.run_id IS NULL` to the WHERE clause to skip already-scored rows

### Fix 10 — `5_analyze_results.py` — Bonferroni Correction Missing
- **Bug:** Single α=0.05 used; with 3 pairs × 4 primary metrics = 12 tests → should use α≈0.004
- **Fix:** Report corrected α alongside each p-value; flag significance at corrected threshold

### Fix 11 — `5_analyze_results.py` — No 95% CIs on Reported Means
- **Bug:** All means reported as point estimates; `confidence_interval_95()` exists in `metrics.py` but never called from the analysis script
- **Fix:** Apply `confidence_interval_95()` to all per-condition means; include in Table 1 output

### Fix 12 — `5_analyze_results.py` — CPSTC bootstrap CI Missing
- **Bug:** CPSTC computed once from totals; with success denominators of 25-32 (out of 144), single-count changes swing CPSTC by ~140 tokens
- **Fix:** Bootstrap 1,000 resample iterations to report `CPSTC (95% CI: [X, X])`

### Fix 13 — Label Inconsistency in Experiment Runner
- **File:** `src/3_run_experiment.py` line 89
- **Bug:** `"Voice transcription (may contain filler words and informal speech):"` — stored in the `prompt` column of `results` table; inconsistent with new research framing
- **Fix:** Change to `"Developer request:"`
- **Note:** This only affects future runs. The 432 stored prompts already contain this label but it's metadata only; it does not affect scoring.

### Fix 14 — `api_clients.py` Header Comment
- **File:** `src/utils/api_clients.py` line 15
- **Bug:** Comments refer to `qwen-3-235b-a22b-instruct-2507` (the originally planned Cerebras model); actual model is `llama3.1-8b`
- **Fix:** Update the comment

---

## 9. New Metrics To Add

| Metric | Why | How | Where |
|--------|-----|-----|-------|
| **Format Compliance Rate** | Separates "wrong tools" from "no tools declared" | `AVG(total_tool_calls > 0)` per condition from existing `results` table | `5_analyze_results.py` — no new data needed |
| **Tool Hallucination Rate** | % of tool calls using invalid (non-whitelisted) names | Parse `tool_calls_json`, count `valid=False` calls | `5_analyze_results.py` — no new data needed; data already in `validate_tool_calls()` output stored in `results.tool_calls_json` |
| **Intent Fidelity Score (0-3)** | Valid replacement for cosine similarity | GPT-4o-mini judge (see Fix 3) | New `scores.intent_fidelity_score` column |
| **Functional Correctness (Pass@1)** | Whether extracted code actually works | pytest execution (see Fix 4) | New `scores.functional_correct` column |
| **Kendall's τ (tool ordering)** | Ordered correctness of tool sequences | `scipy.stats.kendalltau` on sequence rank arrays, runs with ≥2 tools | `5_analyze_results.py` |
| **Response Length (output_tokens)** | Confound for intent preservation + CPSTC context | Already stored as `output_tokens`; just add to Table 1 | `5_analyze_results.py` |
| **API Latency per condition** | Cost of longer Condition C prompts | Already stored as `execution_time_sec`; boxplot by (model, condition) | `6_generate_figures.py` — Fig 10 already exists but not in Table 1 |
| **Silhouette score at k=6** | Validates K-Means clustering meaningfulness | `sklearn.metrics.silhouette_score` per intent class | Report in paper methodology section |
| **Per-intent ANOVA** | Tests H4: does condition effect vary by intent? | `scipy.stats.f_oneway(a_f1, b_f1, c_f1)` per intent class | `5_analyze_results.py` |
| **Condition B hallucination analysis** | B's hallucination advantage is a real finding | Per-model B vs A delta; short analysis block | `5_analyze_results.py` |

---

## 10. Statistical Plan (Revised)

| Test | H | Purpose | Implementation |
|------|---|---------|----------------|
| Paired t-test (`ttest_rel`) | H1 | A vs C, A vs B, B vs C on Tool F1 | Pivot by `(task_id, model)` |
| Cohen's d | H1 | Effect size for each comparison | `src/utils/metrics.cohens_d()` |
| Bonferroni correction | All | 3 pairs × 4 metrics = 12 tests | α ≈ 0.004 |
| 95% CI on all means | All | Honest uncertainty | `src/utils/metrics.confidence_interval_95()` |
| Bootstrap CI on CPSTC | H2 | Stability of token efficiency ranking | 1,000 resamples from success subset |
| One-way ANOVA per intent | H4 | Does condition effect vary by intent? | `scipy.stats.f_oneway` per class |
| McNemar's test on `min_req_met` | H1 | Binary success rate comparison | `statsmodels.stats.contingency_tables.mcnemar` |
| Silhouette score | — | Validates k=6 cluster quality | `sklearn.metrics.silhouette_score` |

---

## 11. Models

| Model | Provider | Size | Rate Limit | Role |
|-------|----------|------|-----------|------|
| `gemini-2.5-flash` | OpenRouter | Proprietary | No daily limit | Evaluatee |
| `llama-3.3-70b-versatile` | Groq | 70B | 100K TPD | Evaluatee + Condition C generator |
| `llama3.1-8b` | Cerebras | 8B | 1M TPD | Evaluatee |
| `gpt-4o-mini` | OpenAI | Proprietary | Paid | Judge only |

**Model non-equivalence:** 8B vs 70B vs Flash. Reframed as cross-scale evaluation feature. Gemini's near-zero Tool F1 (≈0.15) is a format-compliance failure, not capability failure — all per-model results must be stratified in figures.

---

## 12. Known Shortcomings (Documented for Paper)

| Shortcoming | Severity | Mitigation |
|------------|---------|------------|
| Single run per cell (n=1) — no within-cell variance | High | Report means with CIs. All runs used temperature=0.3; temperature sensitivity is left for future work. |
| Unknown dataset provenance | High | Must add provenance paragraph before submission |
| Single-rater gold standards (no inter-rater reliability) | Medium | Document as limitation; add `alternative_tool_sequences` as partial fix |
| Declarative evaluation (tools not executed) | Medium | Functional correctness (Pass@1) partially addresses this |
| Groq used for both Condition C generation AND as evaluatee | Medium | Acknowledge as limitation — potential self-reinforcement for Groq×C |
| Non-equivalent model sizes | Medium | Reframed as cross-scale evaluation; all claims stratified by model |
| 48 tasks — limited generalizability | Medium | Frame as controlled study, not large-scale survey |
| Zero-shot evaluation only | Low | Future work: few-shot comparison |
| Single temperature (0.3) | Low | Future work: temperature sensitivity analysis |
| No condition-D (structured markdown baseline) | Low | Future work: isolates JSON-specific vs. structure-general benefit |

---

## 13. File Map

```
DevPrompt/
├── devflow_dataset.csv              # Source: 1,264 tasks
├── data/
│   ├── tasks_master.json            # 48 tasks with gold standards + embeddings
│   ├── conditions_all.json          # 48 × 3 conditions
│   ├── results.db                   # 432 results + scores (SQLite)
│   ├── table1_condition_overall.csv # ← to be updated after all fixes
│   ├── table2_model_condition.csv
│   └── table3_intent_category.csv
├── src/
│   ├── 1_select_tasks.py            # ✅ K-Means task selection
│   ├── 2_generate_conditions.py     # ✅ Condition A/B/C generation
│   ├── 3_run_experiment.py          # 🔧 Fix label line 89
│   ├── 4_score_results.py           # 🔧 Add: intent fidelity, Pass@1, rescore modes, skip-already-scored
│   ├── 5_analyze_results.py         # 🔧 Fix: ttest_rel, Cohen's d, Bonferroni, CIs, new metrics
│   ├── 6_generate_figures.py        # 🔧 Fix: fig9/fig11 bugs; update fig1/fig12 labels; add 3 new figs
│   ├── gold_standards_part1.py      # 🔧 Add alternative_tool_sequences; extend references; fix debug/generate minimums
│   ├── gold_standards_part2.py      # 🔧 Add alternative_tool_sequences; extend references
│   ├── gold_standards_part3.py      # 🔧 Add alternative_tool_sequences; extend references; fix scaffold/test/composite minimums
│   ├── build_tasks_master.py        # 🔧 Add alternative_tool_sequences to gold_standard dict
│   └── utils/
│       ├── api_clients.py           # 🔧 Fix header comment line 15
│       ├── metrics.py               # 🔧 Update compute_agentic_metrics() for best-sequence scoring
│       └── tool_extraction.py       # 🔧 Add few-shot TOOL_CALL examples to TOOL_SYSTEM_PROMPT
├── tests/                           # ❌ EMPTY — write ~20 unit test files
├── figures/                         # ✅ 13 figures (some need regeneration)
├── CHECKLIST.md                     # 📋 Ordered execution task list
├── METHODOLOGY_AND_FLOW.md          # 📄 This file
└── GOLD_STANDARD_AUDIT.md           # 📋 Task-by-task gold standard audit
```

---

## 14. Execution Order

```
Group 0  Gold standard improvements (gold_standards_part*.py → build_tasks_master.py → rescore tools)
   ↓
Group 1  Critical code fixes (ttest_rel, Cohen's d, Bonferroni, CIs, label fix, api comment)
   ↓
Group 2  DB schema additions (ALTER TABLE for new columns)
   ↓
Group 3  Scoring additions (intent fidelity judge, few-shot prompt, unit tests, Pass@1, rescore)
   ↓
Group 4  Analysis updates (new metrics, ANOVA, silhouette, bootstrap, Condition B hallucination deep-dive)
   ↓
Group 5  Figure updates (fix bugs, replace intent fig, add format compliance fig, add latency fig)
   ↓
Group 6  Documentation cleanup (model names, framing, walkthrough, requirements.txt, provenance)
```

*See `CHECKLIST.md` for the ordered item-by-item task list.*
*See `GOLD_STANDARD_AUDIT.md` for the complete task-by-task gold standard audit.*
