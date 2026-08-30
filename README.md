# DevPrompt: Prompt Formulation Sensitivity in LLM Software Engineering Agents

DevPrompt is an automated research pipeline designed to evaluate how different prompt formulations impact the tool selection accuracy, hallucination rate, and token cost of LLM software engineering agents.

By evaluating **3 LLM models** across **3 prompt conditions** on **48 software engineering tasks** (yielding **432 experimental runs**), this project provides empirical insights into how structured prompting shapes agentic workflows.

---

## 1. Project Architecture

```
DevPrompt/
├── data/
│   ├── results.db             # SQLite DB holding all 432 runs, raw outputs, and final scores
│   ├── tasks_master.json      # Gold standards, expected tool chains, and alternative sequences
│   ├── table1_*.csv           # Overall performance CSVs generated during analysis
│   ├── table2_*.csv           # Model-specific stratified tables
│   └── table3_*.csv           # Intent-specific F1 tables
├── src/
│   ├── 1_select_tasks.py      # K-Means centroid sampling logic for task extraction
│   ├── 2_generate_conditions.py # Generates prompt variations (Raw, Clean, JSON)
│   ├── 3_run_experiment.py    # Concurrency-safe experiment execution loop (resume support)
│   ├── 4_score_results.py     # Rescoring, LLM intent fidelity judge, and functional test suite
│   ├── 5_analyze_results.py   # Statistical significance suite (paired t-test, ANOVA, McNemar)
│   ├── 6_generate_figures.py  # Publication-ready figure generation
│   ├── gold_standards_part*.py # Manually curated task expectations
│   └── utils/
│       ├── api_clients.py     # Wrappers for Gemini, Groq, Cerebras, and OpenAI judges
│       ├── metrics.py         # Set F1 calculations, Cohen's d, and bootstrap CIs
│       └── tool_extraction.py # Regex extraction for TOOL_CALL structures
├── tests/                     # 26 Pytest functional verification files (Pass@1)
├── figures/                   # 15 High-resolution generated charts (.png)
├── requirements.txt           # Python dependency freeze
└── README.md                  # This file
```

---

## 2. Experimental Conditions

| Condition | Name | Format / Prompt Style |
|---|---|---|
| **A** | Raw developer prompt | Unstructured, disfluent developer request (natural language baseline). |
| **B** | Cleaned prompt | Cleaned and normalized text representation (no filler words or casing issues). |
| **C** | Structured JSON | Strict JSON payload providing intent class, entity metadata, confidence, and target. |

---

## 3. Installation & Getting Started

### Prerequisites
* Python 3.11+
* SQLite3

### Setup Environment
1. Clone the repository and navigate to the project root:
   ```bash
   cd DevPrompt
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows (cmd):
   venv\Scripts\activate.bat
   # On Windows (pwsh):
   venv\Scripts\Activate.ps1
   # On Linux/macOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables. Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   GROQ_API_KEY=your_groq_api_key_here
   CEREBRAS_API_KEY=your_cerebras_api_key_here
   ```

---

## 4. Re-Scoring and Running Analysis

All 432 experimental outputs are frozen inside `data/results.db`. You can execute scoring, analysis, and visualization without incurring cost or calling model APIs (except for the OpenAI judges):

### Step 1: Rebuild Task Metadata
Generate the task master json which holds the updated gold standards (new minimum requirements, alternative tool sequences, and extended intent preservation benchmarks):
```bash
python src/build_tasks_master.py
```

### Step 2: Re-Score Extracted Results
Recompute F1 metrics, execute the OpenAI judges, and run the functional tests against the solutions written to `scratch/`:
```bash
# 1. Update F1 metrics from stored JSONs (no APIs)
python src/4_score_results.py --rescore-tools

# 2. Run LLM Intent Fidelity judge (OpenAI API key required)
python src/4_score_results.py --rescore-intent

# 3. Run Pass@1 Functional Correctness Pytest suite (runs local pytests)
python src/4_score_results.py --rescore-functional
```

### Step 3: Run Statistical Analysis
Calculate overall performance, model-stratified metrics, paired t-tests, one-way ANOVA per intent, McNemar's success comparisons, and bootstrap confidence intervals:
```bash
python src/5_analyze_results.py
```

### Step 4: Generate Publication Figures
Generate the 15 publication-grade figures showing Pareto frontiers, F1 curves, success breakdowns, format compliance, and ordering correlation:
```bash
python src/6_generate_figures.py
```

---

## 5. Main Findings

* **JSON Structuring Induces "Productive Flailing"**: Formatting dictation into JSON encourages agents to issue more redundant tool calls (0.99 vs 0.70) but yields significantly higher minimum requirement success rates by preventing early aborts.
* **Pareto Frontier CPSTC**: Structured JSON prompts sit strictly on the Pareto frontier, achieving a **CPSTC of 3,445 tokens** compared to Raw Developer Prompts (4,830 tokens) — a $>28\%$ decrease in token waste.
* **Text Normalization Reduces Hallucination**: Simply cleaning transcript noise under Condition B yields the lowest hallucination rate (6.94%), providing critical grounding for smaller-scale models like Llama 3.1 8B.

---

## 6. Citation

If you use this codebase or dataset in your academic work, please cite:
```latex
@article{devprompt2026,
  title={Prompt Formulation Sensitivity in LLM Software Engineering Agents},
  author={Gupta, Sampurn and Antigravity, AI},
  journal={arXiv preprint arXiv:26xx.xxxxx},
  year={2026}
}
```
