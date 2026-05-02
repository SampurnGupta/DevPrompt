# DevPrompt Research — Complete Context Document

## 1. RESEARCH OVERVIEW

### 1.1 What Is Being Built
Two connected projects:

**Project A — NLP Model (Devflow) [COMPLETED]**
- Sits inside pipeline: `Voice → Whisper ASR → [NLP MODEL] → Intent-Classified JSON → LLM`
- Two jobs:
  1. **Intent Classification** — 7 classes: `debug / generate / refactor / explain / scaffold / test / document`
  2. **Entity Extraction** — extracts: programming language, framework, error type, component/file name
- Models built:
  - `LinearSVC` classifier (`svc_pipeline.pkl`) — classical baseline via TF-IDF (bigrams) → LinearSVC
  - `DistilBERT` — fine-tuned intent classifier (cannot run locally due to compute limits)
  - `spaCy NER` — custom EntityRuler for language/framework/error entity extraction
- Dataset: 1,264 utterances, ~180 per intent class (balanced; balance ratio std/mean = 0.004)
- Dataset columns: `utterance, intent, word_count, language, framework, error_type`

**Project B — Research Paper (DevPrompt) [IN PROGRESS]**
- Title: *"DevPrompt: Evaluating the Impact of Intent-Classified Structured Prompts on LLM Performance in Agentic Software Development Tasks"*

---

### 1.2 Core Hypothesis
Raw, noisy, unstructured developer utterances (especially voice-transcribed) are ambiguous and hurt LLM performance. Converting them into a **structured, intent-classified JSON prompt** (via the Devflow pipeline) will **measurably improve** LLM performance across:
- Output accuracy
- Token cost efficiency
- Agentic tool-use behavior

---

### 1.3 Devflow JSON Output Schema
```json
{
  "raw_utterance": "um fix the null pointer in login service",
  "normalized": "fix null pointer login service",
  "intent": "debug",
  "confidence_score": 0.94,
  "entities": {
    "error_type": "NullPointerException",
    "component": "login service",
    "language": "java",
    "framework": null
  }
}
```

---

### 1.4 Intent Classes (8 total — 7 original + 1 new)
| Class | Description |
|-------|-------------|
| `debug` | Fix errors, exceptions, crashes |
| `generate` | Write new code, endpoints, scripts |
| `refactor` | Restructure existing code |
| `explain` | Clarify code, architecture, concepts |
| `scaffold` | Bootstrap projects, setup structure |
| `test` | Write unit/integration tests |
| `document` | Generate docs, README, comments |
| `composite` | **NEW** — multi-intent tasks (e.g., "debug then write tests") |

> **Why composite?** Real developers often combine intents in one utterance. No prior work handles multi-intent developer prompts. Novel contribution.

---

### 1.5 Experimental Design (3 Conditions × 3 Models × 48 Tasks)

**Three Conditions:**
| Condition | Description | Purpose |
|-----------|-------------|---------|
| **A** | Raw voice transcription (unprocessed, with fillers "um/uh") | Baseline: what ASR produces |
| **B** | Cleaned plain text (grammar-corrected, no fillers, no structure) | Isolates **format effect** from quality effect |
| **C** | Devflow JSON (intent-classified, fully structured) | The proposed solution |

> **Why Condition B matters**: Without it, you can't tell if JSON helps because it's *structured* or just because it's *cleaner*. Condition B isolates these.

**Three Models (all free/low-cost):**
| Model | Provider | API | Cost |
|-------|----------|-----|------|
| Gemini 1.5 Flash | Google AI Studio | `google.generativeai` | Free (1,500 RPD) |
| Llama 3.3 70B | Cerebras | OpenAI-compatible | Free (unlimited) |
| Llama 3.1 70B | Groq | `groq` SDK | Free (14,400 TPD) |

**LLM-as-Judge:** GPT-4o-mini (OpenAI, ~$2.50 from $3 budget)
**Condition C Generation:** Groq Llama 3.1 70B (free)

**Scale:**
- 48 tasks × 3 conditions × 3 models = **432 API calls** (main experiment)
- + 432 judge calls = ~864 total API calls
- Runtime: ~15–20 minutes (automated)

**Per-task structure:**
```
Task (e.g., debug_001)
├── Condition A → Gemini     → Result 1
├── Condition A → Cerebras   → Result 2
├── Condition A → Groq       → Result 3
├── Condition B → Gemini     → Result 4
├── Condition B → Cerebras   → Result 5
├── Condition B → Groq       → Result 6
├── Condition C → Gemini     → Result 7
├── Condition C → Cerebras   → Result 8
└── Condition C → Groq       → Result 9
```
**= 9 results per task × 48 tasks = 432 data points**

---

### 1.6 Research Metrics (5 categories)

**1. Functional Correctness**
- Pass@1 against pre-written unit tests
- Only for ~20–25 tasks where code output is testable (debug/generate/refactor/test)
- Not applicable for explain/document/scaffold (prose output)

**2. Hallucination Rate**
- LLM-as-Judge (GPT-4o-mini) with structured rubric
- Scores: 0 (none), 1 (minor), 2 (major)
- Human spot-check 20%; Cohen's Kappa reported

**3. Intent Preservation Score**
- Cosine similarity between LLM response embedding and gold-standard embedding
- Model: `all-MiniLM-L6-v2` (sentence-transformers)
- Works for ALL task types (including prose)

**4. Token Cost / Efficiency**
- Track: input tokens, output tokens, total tokens per task
- CPSTC = total_tokens / tasks_completed_correctly (tokens per success)
- Most models free → cost = $0; CPSTC becomes token efficiency metric

**5. Agentic Behavior (most novel contribution)**
- Tool Selection Precision = correct_tools_used / total_tools_used
- Tool Recall = correct_tools_used / expected_tools
- Tool F1 score
- Redundant calls (same tool called >1x)
- First-call success (did first tool match expected first tool?)
- Minimum requirements met (boolean)

---

### 1.7 Gap in Existing Literature
| Gap | Our Paper |
|-----|-----------|
| No paper studies developer-specific intent taxonomy | ✅ 8-class developer intent taxonomy |
| No paper measures how prompt structure affects tool selection | ✅ Agentic tool-use metrics |
| No paper studies voice→structured prompt pipeline | ✅ Devflow pipeline |
| No paper uses intent-classified JSON schemas | ✅ Devflow JSON (Condition C) |
| No paper handles multi-intent developer utterances | ✅ Composite intent class |

**Key prior work:**
- He et al. (2024) arXiv:2411.10541 — 40% variation on code tasks for GPT-3.5 by prompt format
- Sclar et al. (ICLR 2024) — up to 76pt accuracy variance across formats in LLaMA-2-13B
- CFPO arXiv:2502.04295 — no universally optimal format
- Preprints.org 2025 — 6 prompt styles across GPT-4o/Claude/Gemini, measures token cost but NOT agentic behavior

---

## 2. COMPLETE RESEARCH EXECUTION FLOW

---

### PHASE 1: SETUP + DATA PREP

#### 1.1 Dataset Sampling & Selection
- Load `devflow_dataset.csv` (1,264 entries, 7 classes, ~180/class)
- Embed all utterances with `SentenceTransformer('all-MiniLM-L6-v2')`
  - *Reason*: Capture semantic meaning, not just word overlap
- Apply **K-Means clustering** (k=6) within each intent class
  - *Reason*: Ensures selected tasks are semantically diverse (null pointer ≠ 403 error ≠ memory leak — all are debug but different sub-types)
- Select utterance nearest to each cluster centroid
  - *Reason*: Most representative of that semantic sub-type
- Tie-breaker: pick utterance with most non-null entities (language/framework/error_type)
  - *Reason*: Entity-rich tasks make evaluation more interesting and test entity extraction
- Result: **42 tasks** (7 classes × 6 tasks each)
- Output: `selected_tasks_base.csv`

#### 1.2 Composite/Multi-Intent Task Creation
- **Manually author 6 composite tasks** (one per combination of common intent pairs):
  ```
  - "debug the null pointer then write unit tests for it"          → debug+test
  - "refactor the payment service and document the changes"        → refactor+document
  - "explain why the kafka consumer is lagging and generate a fix" → explain+generate
  - "scaffold a new microservice and add integration tests"        → scaffold+test
  - "fix the memory leak and write documentation about the cause"  → debug+document
  - "generate a new API endpoint and explain how it integrates"    → generate+explain
  ```
- **Why not sample from dataset?** Dataset is single-label only. Multi-intent requires explicit authoring.
- Each composite task must clearly name ≥2 sequential actions (not vague "also do X")
- Result: **48 total tasks** (42 single-intent + 6 composite)
- Output: `tasks_raw.json`

#### 1.3 Gold Standard Definition
For each of 48 tasks, manually define:

**A. Expected Functional Output Description**
- 2–3 sentence natural language description of what correct output looks like
- NOT full code (too rigid; penalizes valid alternative implementations)
- Example: "Code that checks for null before accessing user.email, handles gracefully with an error response"

**B. Expected Tool Sequence**
- Ordered list of tools LLM should invoke:
  ```json
  {
    "expected_tools": ["search_codebase", "read_file", "write_file", "run_tests"],
    "minimum_required_tools": ["read_file", "write_file"]
  }
  ```
- `expected_tools` = ideal sequence; `minimum_required_tools` = bare minimum for success
- Tools available (8 total):
  ```
  read_file(path)
  write_file(path, content)
  run_tests(test_file)
  search_codebase(query, file_pattern)
  git_diff()
  lint_code(file)
  fetch_docs(library)
  execute_shell(command)
  ```

**C. Key Entities (gold standard labels)**
```json
{
  "error_type": "NullPointerException",
  "component": "LoginService",
  "language": "java",
  "framework": null
}
```

**D. Intent Preservation Reference + Embedding**
- Gold standard paraphrase: "Fix the NullPointerException in the LoginService class"
- Pre-compute embedding using `all-MiniLM-L6-v2` and store
- *Reason*: Avoid re-encoding 432 times during scoring; cosine similarity against this = intent score

#### 1.4 Unit Test Creation (Selective)
- **Write unit tests ONLY for**: debug / generate / refactor / test intent classes
- **Skip for**: explain / document / scaffold (prose or structural output, not testable)
- ~20–25 tasks will have unit tests
- Format: simple `pytest` pass/fail
  ```python
  # Example: debug_001_test.py
  def test_login_service_null_pointer():
      service = LoginService()
      result = service.authenticate(None)
      assert result == {"error": "Invalid credentials"}
  ```

#### 1.5 Master Task File Assembly
- Merge all above into `tasks_master.json`
- Schema per task:
  ```json
  {
    "task_id": "debug_001",
    "intent": "debug",
    "raw_utterance": "um fix the null pointer in login service",
    "gold_standard": {
      "functional_output_description": "...",
      "intent_preservation_reference": "Fix the NullPointerException in LoginService",
      "intent_preservation_embedding": [0.123, -0.456, "..."],
      "expected_tools": ["search_codebase", "read_file", "write_file", "run_tests"],
      "minimum_required_tools": ["read_file", "write_file"],
      "entities": {
        "error_type": "NullPointerException",
        "component": "LoginService",
        "language": "java",
        "framework": null
      }
    },
    "has_unit_test": true,
    "unit_test_path": "tests/debug_001_test.py"
  }
  ```
- Validation checklist:
  - [ ] All 48 tasks have unique IDs
  - [ ] All required fields present
  - [ ] Intent labels valid
  - [ ] Tool lists non-empty
  - [ ] No duplicate raw utterances

---

### PHASE 2: CONDITION GENERATION

#### 2.1 Condition A — Raw Voice
- Use `raw_utterance` as-is from dataset
- Already has: fillers ("um", "uh"), lowercase, missing punctuation, run-on sentences
- Labelled in prompt as "voice transcription" when sent to LLM
- Output: plain string
  ```json
  { "condition_a": "um fix the null pointer in login service" }
  ```

#### 2.2 Condition B — Clean Plain Text (Local Pipeline, FREE)
Step-by-step deterministic cleaning:
1. Lowercase everything
2. Remove fillers via regex: `\b(um|uh|like|you know|basically|okay so)\b`
3. Expand contractions: `don't → do not`, `can't → cannot`, `it's → it is`
4. Normalize whitespace: collapse multiple spaces, strip edges
5. Capitalize first letter, ensure ends with period
6. (Optional) TextBlob grammar correction — skip if time-constrained

- **Why local pipeline (not LLM)?** Deterministic, free, fast, reproducible
- Quality target: reads like a well-written Slack message or GitHub issue title — NOT over-formal
- Output:
  ```json
  { "condition_b": "Fix the null pointer in login service." }
  ```

#### 2.3 Condition C — Devflow JSON (via Groq Llama 3.1 70B, FREE)
- **Why not use LinearSVC + spaCy?**
  - LinearSVC: one intent only, no composite support
  - spaCy NER: insufficient accuracy for paper-quality results
  - DistilBERT: cannot run locally (compute limits)
- **Solution**: Generate via Groq API (free, fast, accurate)

Prompt template:
```
You are a developer intent classifier. Convert this voice utterance into structured JSON.

INPUT: "{raw_utterance}"

OUTPUT FORMAT (respond ONLY with valid JSON, no markdown):
{
  "raw_utterance": "...",
  "normalized": "cleaned version without fillers",
  "intent": "debug|generate|refactor|explain|scaffold|test|document|composite",
  "confidence_score": 0.XX,
  "entities": {
    "error_type": "...",
    "component": "...",
    "language": "...",
    "framework": "..."
  }
}

Rules:
- If entity not mentioned, use null
- For composite intents, use "intent1+intent2" format (e.g., "debug+test")
- confidence_score: 0.7–0.9 for clear, 0.5–0.7 for ambiguous
- normalized: remove fillers, keep technical terms intact
```

API call:
```python
from groq import Groq
client = Groq(api_key="YOUR_GROQ_API_KEY")

response = client.chat.completions.create(
    model="llama-3.1-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.1,
    max_tokens=300
)
json_str = response.choices[0].message.content.strip()
json_str = json_str.replace('```json', '').replace('```', '').strip()
devflow_json = json.loads(json_str)
```

- **After generation**: spot-check 5–10 random JSONs manually, fix errors
- Cost: 48 tasks × ~150 tokens = 7,200 tokens (FREE on Groq)
- Output: `conditions_all.json` (48 tasks × 3 conditions)

---

### PHASE 3: EVALUATION HARNESS

#### 3.1 System Prompt (All Conditions)
```
You are an expert software engineer helping with development tasks.
You have access to these 8 tools:

1. read_file(path)
2. write_file(path, content)
3. run_tests(test_file)
4. search_codebase(query, file_pattern)
5. git_diff()
6. lint_code(file)
7. fetch_docs(library)
8. execute_shell(command)

When you use a tool, format it EXACTLY as:
TOOL_CALL: tool_name(parameters)

Provide working code solutions. Be concise but complete.
```

#### 3.2 Prompt Templates per Condition
- **Condition A**: label = "voice transcription" → LLM knows to interpret noisy input
- **Condition B**: no special label → standard interaction
- **Condition C**: label = "structured request" → LLM knows to parse JSON

#### 3.3 API Clients

**Gemini 1.5 Flash (Google AI Studio):**
```python
import google.generativeai as genai
genai.configure(api_key="YOUR_GOOGLE_API_KEY")
model = genai.GenerativeModel('gemini-1.5-flash')

def call_gemini(prompt):
    response = model.generate_content(
        prompt,
        generation_config={'temperature': 0.3, 'max_output_tokens': 2048}
    )
    return {
        'response': response.text,
        'input_tokens': response.usage_metadata.prompt_token_count,
        'output_tokens': response.usage_metadata.candidates_token_count
    }
```

**Llama 3.3 70B (Cerebras — OpenAI-compatible):**
```python
from openai import OpenAI
cerebras_client = OpenAI(api_key="YOUR_CEREBRAS_KEY", base_url="https://api.cerebras.ai/v1")

def call_cerebras(prompt):
    response = cerebras_client.chat.completions.create(
        model="llama3.3-70b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3, max_tokens=2048
    )
    return {
        'response': response.choices[0].message.content,
        'input_tokens': response.usage.prompt_tokens,
        'output_tokens': response.usage.completion_tokens
    }
```

**Llama 3.1 70B (Groq):**
```python
from groq import Groq
groq_client = Groq(api_key="YOUR_GROQ_API_KEY")

def call_groq(prompt):
    response = groq_client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3, max_tokens=2048
    )
    return {
        'response': response.choices[0].message.content,
        'input_tokens': response.usage.prompt_tokens,
        'output_tokens': response.usage.completion_tokens
    }
```

> **All return standardized dict**: `{response, input_tokens, output_tokens}`

> **Token counting fallback** (if API doesn't return tokens):
> ```python
> import tiktoken
> encoder = tiktoken.encoding_for_model("gpt-4")
> token_count = len(encoder.encode(text))
> ```

#### 3.4 Tool Call Extraction
> **Important**: Tools are NOT actually executed. LLMs declare which tools they would use via text. This is parsed and compared against gold standard.

```python
import re

def extract_tool_calls(response_text):
    pattern = r'TOOL_CALL:\s*(\w+)\((.*?)\)'
    matches = re.findall(pattern, response_text, re.MULTILINE)
    return [{'tool': tool, 'params': params.strip()} for tool, params in matches]

# Validate: check tool names against VALID_TOOLS list
VALID_TOOLS = ['read_file', 'write_file', 'run_tests', 'search_codebase',
               'git_diff', 'lint_code', 'fetch_docs', 'execute_shell']
```

> **Alternative** (if using native function calling — Gemini supports this):
> Define tools via API schema; Gemini returns structured function_call objects in response

#### 3.5 Experimental Loop
```python
import sqlite3, json, time
from datetime import datetime

# SQLite results database
conn = sqlite3.connect('results.db')
# Table: run_id, task_id, intent, condition, model, timestamp,
#        prompt, response, input_tokens, output_tokens, tool_calls, execution_time_sec

models = {'gemini': call_gemini, 'cerebras': call_cerebras, 'groq': call_groq}
tasks = json.load(open('conditions_all.json'))

for task in tasks:
    for condition in ['a', 'b', 'c']:
        for model_name, model_fn in models.items():
            prompt = build_prompt(task, condition)
            start = time.time()
            try:
                result = model_fn(prompt)
                tools = extract_tool_calls(result['response'])
                run_id = f"{task['task_id']}_cond{condition}_{model_name}"
                # INSERT into results.db
                time.sleep(1)  # Rate limit buffer
            except Exception as e:
                # Log error, continue loop
                pass
```

- 432 calls × 1 sec delay = ~7–8 minutes total runtime
- Checkpoints every 10 tasks (in case of crash)

---

### PHASE 4: SCORING & METRICS

#### 4.1 Functional Correctness (unit-tested tasks only)
```python
import subprocess, re

def run_unit_test(task_id, response):
    code = extract_code_block(response)  # Parse ```python ... ``` blocks
    with open(f'temp/{task_id}_solution.py', 'w') as f:
        f.write(code)
    result = subprocess.run(['pytest', f'tests/{task_id}_test.py', '-v'],
                            capture_output=True, timeout=10)
    return result.returncode == 0  # True = pass
```

#### 4.2 Hallucination Detection (GPT-4o-mini, ~$2.50 total)
Rubric:
- **Score 0**: No hallucination — all claims verifiable, uncertainties stated
- **Score 1**: Minor — 1–2 unverifiable minor details, doesn't affect correctness
- **Score 2**: Major — invented APIs/methods, confidently wrong facts, would break code

```python
from openai import OpenAI
openai_client = OpenAI(api_key="YOUR_OPENAI_KEY")

def judge_hallucination(task, response):
    judge_prompt = f"""
You are evaluating an LLM response for hallucinations.
TASK: {task['gold_standard']['functional_output_description']}
RESPONSE: {response}
[... rubric ...]
Output ONLY valid JSON: {{"score": 0-2, "reasoning": "...", "hallucinated_claims": []}}
"""
    result = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": judge_prompt}],
        temperature=0.1, max_tokens=300
    )
    return json.loads(result.choices[0].message.content)
```

#### 4.3 Intent Preservation Score
```python
from sentence_transformers import SentenceTransformer, util
sim_model = SentenceTransformer('all-MiniLM-L6-v2')

def compute_intent_preservation(task, response):
    gold_embedding = task['gold_standard']['intent_preservation_embedding']
    response_embedding = sim_model.encode(response)
    return util.cos_sim(gold_embedding, response_embedding).item()  # 0.0 to 1.0
```

#### 4.4 Agentic Metrics
```python
def compute_agentic_metrics(task, extracted_tools):
    expected = set(task['gold_standard']['expected_tools'])
    minimum = set(task['gold_standard']['minimum_required_tools'])
    actual_list = [t['tool'] for t in extracted_tools]
    actual = set(actual_list)

    correct = actual & expected
    precision = len(correct) / len(actual) if actual else 0
    recall = len(correct) / len(expected) if expected else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    redundant = len(actual_list) - len(actual)
    first_call_correct = (len(extracted_tools) > 0 and
                          extracted_tools[0]['tool'] == task['gold_standard']['expected_tools'][0])

    return {
        'tool_precision': precision, 'tool_recall': recall, 'tool_f1': f1,
        'total_tool_calls': len(extracted_tools), 'redundant_calls': redundant,
        'first_call_correct': first_call_correct,
        'minimum_requirements_met': minimum.issubset(actual)
    }
```

#### 4.5 Token Efficiency (CPSTC)
- Since most APIs are free, cost = $0
- Report as **tokens per successful task** instead of $ cost
- CPSTC = total_tokens / tasks_completed_correctly
- Condition C may have longer input (JSON overhead) but higher success → lower CPSTC

---

### PHASE 5: STATISTICAL ANALYSIS

#### 5.1 Primary Hypothesis Tests

**H1: Condition C > Condition B on functional correctness (paired t-test)**
```python
from scipy.stats import ttest_rel
# Merge on task_id + model to ensure pairing
t_stat, p_value = ttest_rel(cond_c_scores, cond_b_scores)
effect_size = cohens_d(cond_c_scores, cond_b_scores)
# Report: t(df) = X, p = X, Cohen's d = X, 95% CI [X, X]
```

**H2: Condition C reduces hallucinations (McNemar's test — binary)**
```python
from statsmodels.stats.contingency_tables import mcnemar
# Contingency: B_fail_C_pass vs B_pass_C_fail
result = mcnemar([[b_fail_c_pass, b_pass_c_fail]], exact=True)
```

**H3: Cross-model differences (one-way ANOVA + Tukey HSD)**
```python
from scipy.stats import f_oneway, tukey_hsd
f_stat, p_value = f_oneway(gemini_scores, cerebras_scores, groq_scores)
posthoc = tukey_hsd(gemini_scores, cerebras_scores, groq_scores)
```

**H4: Two-way ANOVA (Condition × Model interaction)**
```python
import statsmodels.formula.api as smf
model = smf.ols('functional_correctness ~ C(condition) * C(model)', data=df).fit()
anova_table = sm.stats.anova_lm(model, typ=2)
# Check interaction term: does JSON help more for specific models?
```

#### 5.2 Always Report:
- Cohen's d (effect size) alongside every t-test
- 95% confidence intervals for all means
- p < 0.05 threshold throughout
- Example reporting: *"Condition C achieved 23% higher functional correctness (M=0.79 vs M=0.64, t(143)=4.82, p<0.001, d=0.87, 95% CI [0.58, 1.16])"*

#### 5.3 Figures (8 minimum, 300 DPI, colorblind palette)
1. Functional correctness by condition (bar + error bars = 95% CI)
2. Tool precision/recall heatmap (condition × metric)
3. Cross-model grouped bar chart
4. Intent class breakdown (per-class delta: JSON vs clean text)
5. Token efficiency (CPSTC by condition)
6. Failure taxonomy (horizontal bar chart)

```python
import seaborn as sns
sns.set_palette("colorblind")  # Accessible colors
# Always: fontsize ≥ 12, dpi=300, tight_layout
```

---

### PHASE 6: PAPER WRITING

#### 6.1 Paper Structure (Target: minimum 9–10 pages, IEEE format)
1. **Introduction** (1.5p) — Problem, gap, contribution, key finding preview
2. **Background & Related Work** (2p) — Prior prompt engineering papers + gaps
3. **DevPrompt Schema Design** (1.5p) — 8-intent taxonomy + JSON schema rationale
4. **Devflow Pipeline** (1p) — Architecture diagram, NLP preprocessing overview
5. **Experimental Methodology** (2.5p) — 3-condition design, task construction, metrics, stats plan
6. **Results** (4p) — Tables + figures + statistical findings
7. **Discussion** (2p) — Why JSON helps, when it doesn't, cross-model insights
8. **Limitations & Future Work** (0.5p)
9. **Conclusion** (0.5p)

#### 6.2 Write Results First
- Easier to frame contribution after seeing data
- Tables needed:
  - Table 1: Mean ± SD for all metrics × conditions × models
  - Table 2: Tool use breakdown by condition
  - Table 3: Failure taxonomy
  - Table 4: Per-intent-class breakdown

#### 6.3 Three Key Arguments to Make
1. **Lemmatisation > stemming** for technical vocabulary (validated in your NLP coursework)
2. **Bigrams essential** for developer compound terms ("null pointer", "unit test")
3. **Structured JSON isolates format from quality** (why 3 conditions, not 2)

---

### PHASE 7: REPRODUCIBILITY PACKAGE

#### 7.1 Repository Structure
```
devprompt-research/
├── README.md
├── requirements.txt
├── data/
│   ├── devflow_dataset.csv
│   ├── tasks_master.json
│   ├── conditions_all.json
│   └── results.db
├── src/
│   ├── 1_select_tasks.py
│   ├── 2_generate_conditions.py
│   ├── 3_run_experiment.py
│   ├── 4_score_results.py
│   ├── 5_analyze_stats.py
│   ├── 6_generate_figures.py
│   └── utils/
│       ├── api_clients.py
│       ├── tool_extraction.py
│       └── metrics.py
├── tests/
│   └── {task_id}_test.py × 20-25 files
├── figures/
│   └── fig1...fig6.png
└── paper/
    └── devprompt_paper.pdf
```

---

## 3. KEY DECISIONS & REASONING SUMMARY

| Decision | Choice | Reason |
|----------|--------|--------|
| Condition C generation | Groq Llama 3.1 70B API | LinearSVC single-intent only; spaCy NER insufficient; DistilBERT can't run locally |
| Condition B generation | Local cleaning pipeline | Deterministic, free, fast, reproducible |
| LLM-as-Judge | GPT-4o-mini | Cheap, reliable structured scoring, within $3 budget |
| Tool calls | Text-based TOOL_CALL: parsing | No actual code execution needed; tests LLM intent |
| Token counting | API response metadata | All 3 providers return usage stats; tiktoken as fallback |
| # tasks | 48 (6 per class) | 432 data points is statistically sufficient; feasible within free tier limits |
| # intent classes | 8 (7 + composite) | Composite = novel contribution; real developers issue multi-intent commands |
| Models | Gemini Flash, Llama 3.3, Llama 3.1 | All free; covers different architectures; no OpenAI dependency |
| Statistical tests | Paired t-test + McNemar + ANOVA + Cohen's d | Paired = same tasks across conditions; McNemar = binary outcomes; Cohen's d = effect magnitude |
| Figure styling | seaborn colorblind palette, ≥300 DPI | Accessibility + publication quality |

---

## 4. DATASET PROFILE (for reference)

- **File**: `devflow_dataset.csv`
- **Total**: 1,264 utterances
- **Columns**: `utterance, intent, word_count, language, framework, error_type`
- **Balance**: Near-perfect (std/mean = 0.004); ~180 per class
- **Word count**: avg 13.4, range 2–47, std 7.25
- **Entity coverage**: language=13%, framework=24.2%, error_type=9.7%
- **Voice artifacts present**: fillers ("um", "uh", "like"), lowercase, missing punctuation, run-ons
- **NB**: Dataset has duplicate entity columns (data entry artifact) — use first `language`, `framework`, `error_type` columns only

---

## 5. BUDGET & TIMELINE

### Budget
| Item | Provider | Cost |
|------|----------|------|
| Main experiment (432 calls) | Gemini + Cerebras + Groq | $0 |
| Condition C generation (48 calls) | Groq | $0 |
| LLM-as-Judge (432 calls) | GPT-4o-mini | ~$2.50 |
| **Total** | | **~$2.50** |

### Timeline (fast-track)
| Week | Tasks |
|------|-------|
| Week 1, Days 1–2 | Dataset sampling (1.1) + composite tasks (1.2) |
| Week 1, Days 3–4 | Gold standards (1.3) + unit tests (1.4) + master file (1.5) |
| Week 1, Days 5–6 | Condition B pipeline (2.2) + Condition C generation (2.3) |
| Week 1, Day 7 | Build evaluation harness (Phase 3) |
| Week 2, Days 8–9 | Pilot run (10 tasks, 1 model) — verify pipeline |
| Week 2, Days 10–12 | Full run (48 tasks, all 3 models) — split across 3 days |
| Week 2, Days 13–14 | LLM-as-Judge scoring (Phase 4) |
| Week 3, Days 15–16 | Statistical analysis + figures (Phase 5) |
| Week 3, Days 17–19 | Paper writing (Phase 6) |
| Week 3, Days 20–21 | Polish, proofread, reproducibility package |

---

## 6. SCRIPTS TO BUILD (in order)

1. `1_select_tasks.py` — embedding + K-Means sampling, outputs `selected_tasks_base.csv`
2. `2_generate_conditions.py` — Condition A (passthrough), B (cleaning pipeline), C (Groq API)
3. `3_run_experiment.py` — main loop: 48 × 3 × 3 = 432 API calls, stores to `results.db`
4. `4_score_results.py` — unit tests + GPT-4o-mini judge + semantic similarity + agentic metrics
5. `5_analyze_stats.py` — all hypothesis tests, effect sizes, CIs
6. `6_generate_figures.py` — all 6 paper figures at 300 DPI

---

*End of context document. All implementation decisions, API choices, metric definitions, and reasoning are captured above.*