"""
metrics.py — All scoring functions for the DevPrompt evaluation pipeline.

Metrics implemented:
1. Intent Preservation Score  (cosine similarity via sentence-transformers)
2. Agentic Tool Metrics       (precision, recall, F1, redundancy, first-call accuracy)
3. Token Efficiency (CPSTC)   (tokens per successful task)
4. Functional Correctness     (pytest-based, used externally in 4_score_results.py)
5. Cohen's Kappa              (for human spot-check agreement on hallucination)
"""

import numpy as np
from typing import List, Dict, Any, Optional


# -------------------------------------------------------------------------
# 1. Intent Preservation Score
# -------------------------------------------------------------------------

_sim_model = None

def _get_sim_model():
    """Lazy-load sentence transformer (heavy import)."""
    global _sim_model
    if _sim_model is None:
        from sentence_transformers import SentenceTransformer
        _sim_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _sim_model


def encode_text(text: str) -> List[float]:
    """Encode text to embedding vector using all-MiniLM-L6-v2."""
    model = _get_sim_model()
    embedding = model.encode(text)
    return embedding.tolist()


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two embedding vectors."""
    a = np.array(vec_a)
    b = np.array(vec_b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def compute_intent_preservation(gold_embedding: List[float], response_text: str) -> float:
    """
    Compute intent preservation score: cosine similarity between
    the gold standard embedding and the response embedding.

    Args:
        gold_embedding: Pre-computed embedding from tasks_master.json
        response_text:  LLM's full response string

    Returns:
        Float in [0.0, 1.0]
    """
    response_embedding = encode_text(response_text)
    return cosine_similarity(gold_embedding, response_embedding)


# -------------------------------------------------------------------------
# 2. Agentic Tool Metrics
# -------------------------------------------------------------------------

def compute_agentic_metrics(
    task: Dict[str, Any],
    extracted_tool_names: List[str]
) -> Dict[str, Any]:
    """
    Compute all agentic behavior metrics for a single task result.

    Args:
        task:                 Task dict from tasks_master.json
        extracted_tool_names: List of valid tool names in order from LLM response

    Returns:
        Dict with: tool_precision, tool_recall, tool_f1,
                   total_tool_calls, redundant_calls,
                   first_call_correct, minimum_requirements_met
    """
    gold = task['gold_standard']
    expected_list: List[str] = gold['expected_tools']
    minimum_set: set = set(gold['minimum_required_tools'])
    expected_set = set(expected_list)
    actual_list = extracted_tool_names
    actual_set = set(actual_list)

    correct = actual_set & expected_set
    precision = len(correct) / len(actual_set) if actual_set else 0.0
    recall = len(correct) / len(expected_set) if expected_set else 0.0
    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) > 0 else 0.0)

    redundant = len(actual_list) - len(actual_set)

    first_call_correct = (
        len(actual_list) > 0
        and len(expected_list) > 0
        and actual_list[0] == expected_list[0]
    )

    minimum_met = minimum_set.issubset(actual_set)

    return {
        'tool_precision': round(precision, 4),
        'tool_recall': round(recall, 4),
        'tool_f1': round(f1, 4),
        'total_tool_calls': len(actual_list),
        'redundant_calls': max(0, redundant),
        'first_call_correct': first_call_correct,
        'minimum_requirements_met': minimum_met,
        'tools_called': actual_list,
        'expected_tools': expected_list,
        'minimum_required_tools': list(minimum_set)
    }


# -------------------------------------------------------------------------
# 3. Token Efficiency (CPSTC)
# -------------------------------------------------------------------------

def compute_cpstc(
    total_tokens: int,
    successful_tasks: int
) -> Optional[float]:
    """
    Cost Per Successful Task Completion (in tokens, since APIs are free).
    Returns None if no tasks were successful.
    """
    if successful_tasks == 0:
        return None
    return total_tokens / successful_tasks


def aggregate_token_stats(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate token usage statistics across a list of result dicts.
    Each result must have: input_tokens, output_tokens, functional_correct (bool)

    Returns:
        {
            total_input_tokens, total_output_tokens, total_tokens,
            avg_input_tokens, avg_output_tokens, avg_total_tokens,
            successful_tasks, cpstc
        }
    """
    total_input = sum(r.get('input_tokens', 0) for r in results)
    total_output = sum(r.get('output_tokens', 0) for r in results)
    total = total_input + total_output
    n = len(results)
    successful = sum(1 for r in results if r.get('functional_correct', False))

    return {
        'total_input_tokens': total_input,
        'total_output_tokens': total_output,
        'total_tokens': total,
        'avg_input_tokens': round(total_input / n, 1) if n else 0,
        'avg_output_tokens': round(total_output / n, 1) if n else 0,
        'avg_total_tokens': round(total / n, 1) if n else 0,
        'successful_tasks': successful,
        'cpstc': compute_cpstc(total, successful)
    }


# -------------------------------------------------------------------------
# 4. Cohen's Kappa (human spot-check agreement)
# -------------------------------------------------------------------------

def cohens_kappa(ratings_a: List[int], ratings_b: List[int]) -> float:
    """
    Compute Cohen's Kappa for inter-rater agreement between two raters.
    Ratings should be integer class labels (e.g., 0, 1, 2 for hallucination scores).

    Returns kappa in [-1, 1]. Values > 0.6 indicate substantial agreement.
    """
    if len(ratings_a) != len(ratings_b):
        raise ValueError("Rating lists must be the same length")
    if len(ratings_a) == 0:
        return 0.0

    n = len(ratings_a)
    categories = sorted(set(ratings_a) | set(ratings_b))
    k = len(categories)

    # Build confusion matrix
    cat_idx = {c: i for i, c in enumerate(categories)}
    matrix = np.zeros((k, k), dtype=float)
    for a, b in zip(ratings_a, ratings_b):
        matrix[cat_idx[a]][cat_idx[b]] += 1

    # Observed agreement
    p_o = np.trace(matrix) / n

    # Expected agreement
    row_sums = matrix.sum(axis=1) / n
    col_sums = matrix.sum(axis=0) / n
    p_e = np.dot(row_sums, col_sums)

    if p_e == 1.0:
        return 1.0

    kappa = (p_o - p_e) / (1 - p_e)
    return round(float(kappa), 4)


# -------------------------------------------------------------------------
# 5. Effect sizes
# -------------------------------------------------------------------------

def cohens_d(group_a: List[float], group_b: List[float]) -> float:
    """
    Compute Cohen's d effect size between two groups.
    Uses pooled standard deviation.
    """
    a = np.array(group_a)
    b = np.array(group_b)
    n_a, n_b = len(a), len(b)
    if n_a < 2 or n_b < 2:
        return 0.0
    pooled_std = np.sqrt(
        ((n_a - 1) * np.var(a, ddof=1) + (n_b - 1) * np.var(b, ddof=1))
        / (n_a + n_b - 2)
    )
    if pooled_std == 0:
        return 0.0
    return round(float((np.mean(a) - np.mean(b)) / pooled_std), 4)


def confidence_interval_95(values: List[float]) -> tuple:
    """
    Compute 95% confidence interval for a list of values.
    Returns (lower_bound, upper_bound).
    """
    from scipy import stats
    a = np.array(values)
    n = len(a)
    if n < 2:
        mean = np.mean(a) if n == 1 else 0.0
        return (mean, mean)
    se = stats.sem(a)
    ci = stats.t.interval(0.95, df=n-1, loc=np.mean(a), scale=se)
    return (round(float(ci[0]), 4), round(float(ci[1]), 4))


# -------------------------------------------------------------------------
# 6. Summary stats helper
# -------------------------------------------------------------------------

def describe(values: List[float]) -> Dict[str, float]:
    """
    Return descriptive statistics for a list of floats.
    """
    a = np.array(values)
    ci = confidence_interval_95(values)
    return {
        'mean': round(float(np.mean(a)), 4),
        'std': round(float(np.std(a, ddof=1)), 4),
        'median': round(float(np.median(a)), 4),
        'min': round(float(np.min(a)), 4),
        'max': round(float(np.max(a)), 4),
        'n': len(a),
        'ci_lower': ci[0],
        'ci_upper': ci[1]
    }
