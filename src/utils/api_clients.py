"""
api_clients.py — Standardized LLM client wrappers for DevPrompt experiment.

All client functions return a standardized dict:
    {
        'response': str,
        'input_tokens': int,
        'output_tokens': int,
        'model': str
    }

Models (as of 2026-05):
    Gemini  : gemini-2.0-flash       (google.genai SDK)
    Groq    : llama-3.3-70b-versatile
    Cerebras: qwen-3-235b-a22b-instruct-2507
    Judge   : gpt-4o-mini (OpenAI)
"""

import os
import time
import json
import tiktoken
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Token counting fallback
# ---------------------------------------------------------------------------

_tiktoken_encoder = None

def _count_tokens_fallback(text: str) -> int:
    global _tiktoken_encoder
    if _tiktoken_encoder is None:
        _tiktoken_encoder = tiktoken.encoding_for_model("gpt-4")
    return len(_tiktoken_encoder.encode(text))


# ---------------------------------------------------------------------------
# Gemini 2.0 Flash  (google.genai — new SDK)
# ---------------------------------------------------------------------------

_gemini_client = None

def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set")
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


def call_gemini(prompt: str, system_prompt: str = None, temperature: float = 0.3,
                max_tokens: int = 2048, retries: int = 3) -> dict:
    """Call Gemini 2.5 Flash Lite and return standardized result dict."""
    from google.genai import types

    client = _get_gemini_client()
    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
    )

    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=full_prompt,
                config=config,
            )
            text = response.text
            if text is None:
                # Safety block or empty response — treat as retryable error
                finish = getattr(response.candidates[0], 'finish_reason', 'UNKNOWN') if response.candidates else 'NO_CANDIDATES'
                raise ValueError(f"Gemini returned None text (finish_reason={finish})")
            try:
                meta = response.usage_metadata
                input_tokens  = meta.prompt_token_count
                output_tokens = meta.candidates_token_count
            except Exception:
                input_tokens  = _count_tokens_fallback(full_prompt)
                output_tokens = _count_tokens_fallback(text)

            return {
                'response': text,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'model': 'gemini-2.5-flash-lite'
            }
        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"[Gemini] Attempt {attempt+1} failed: {e}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise


# ---------------------------------------------------------------------------
# Llama 3.3 70B (Groq)
# ---------------------------------------------------------------------------

_groq_client = None

def _get_groq_client():
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set")
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def call_groq(prompt: str, system_prompt: str = None, temperature: float = 0.3,
              max_tokens: int = 2048, retries: int = 3) -> dict:
    """Call Groq Llama 3.3 70B and return standardized result dict."""
    client = _get_groq_client()

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            text = response.choices[0].message.content
            try:
                input_tokens  = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
            except Exception:
                input_tokens  = _count_tokens_fallback(prompt)
                output_tokens = _count_tokens_fallback(text)

            return {
                'response': text,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'model': 'llama-3.3-70b-groq'
            }
        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"[Groq] Attempt {attempt+1} failed: {e}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise


# ---------------------------------------------------------------------------
# Qwen-3 235B (Cerebras)  — most capable model currently available
# ---------------------------------------------------------------------------

_cerebras_client = None

def _get_cerebras_client():
    global _cerebras_client
    if _cerebras_client is None:
        from openai import OpenAI
        api_key = os.getenv("CEREBRAS_API_KEY")
        if not api_key:
            raise ValueError("CEREBRAS_API_KEY not set")
        _cerebras_client = OpenAI(
            api_key=api_key,
            base_url="https://api.cerebras.ai/v1"
        )
    return _cerebras_client


def call_cerebras(prompt: str, system_prompt: str = None, temperature: float = 0.3,
                  max_tokens: int = 2048, retries: int = 5) -> dict:
    """Call Cerebras Qwen-3 235B and return standardized result dict."""
    client = _get_cerebras_client()

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="qwen-3-235b-a22b-instruct-2507",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            text = response.choices[0].message.content
            try:
                input_tokens  = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
            except Exception:
                input_tokens  = _count_tokens_fallback(prompt)
                output_tokens = _count_tokens_fallback(text)

            return {
                'response': text,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'model': 'qwen-3-235b-cerebras'
            }
        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"[Cerebras] Attempt {attempt+1} failed: {e}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise


# ---------------------------------------------------------------------------
# GPT-4o-mini (OpenAI — LLM-as-Judge only)
# ---------------------------------------------------------------------------

_openai_client = None

def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def call_openai_judge(prompt: str, temperature: float = 0.1,
                      max_tokens: int = 300, retries: int = 3) -> dict:
    """Call GPT-4o-mini for LLM-as-Judge hallucination scoring."""
    client = _get_openai_client()

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            text = response.choices[0].message.content
            try:
                input_tokens  = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
            except Exception:
                input_tokens  = _count_tokens_fallback(prompt)
                output_tokens = _count_tokens_fallback(text)

            return {
                'response': text,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'model': 'gpt-4o-mini'
            }
        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"[OpenAI] Attempt {attempt+1} failed: {e}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise


# ---------------------------------------------------------------------------
# Groq — Condition C generation
# ---------------------------------------------------------------------------

def generate_condition_c(raw_utterance: str, retries: int = 3) -> dict:
    """
    Generate a DevPrompt structured JSON (Condition C) for a raw utterance
    via Groq Llama 3.3 70B. Returns parsed JSON dict.
    """
    client = _get_groq_client()

    prompt = f"""You are a developer intent classifier. Convert this voice utterance into structured JSON.

INPUT: "{raw_utterance}"

OUTPUT FORMAT (respond ONLY with valid JSON, no markdown):
{{
  "raw_utterance": "...",
  "normalized": "cleaned version without fillers",
  "intent": "debug|generate|refactor|explain|scaffold|test|document|composite",
  "confidence_score": 0.XX,
  "entities": {{
    "error_type": "...",
    "component": "...",
    "language": "...",
    "framework": "..."
  }}
}}

Rules:
- If entity not mentioned, use null
- For composite intents, use "intent1+intent2" format (e.g., "debug+test")
- confidence_score: 0.7-0.9 for clear, 0.5-0.7 for ambiguous
- normalized: remove fillers, keep technical terms intact
"""

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300
            )
            json_str = response.choices[0].message.content.strip()
            json_str = json_str.replace('```json', '').replace('```', '').strip()
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            if attempt < retries - 1:
                print(f"[ConditionC] JSON parse error attempt {attempt+1}: {e}. Retrying...")
                time.sleep(1)
            else:
                print(f"[ConditionC] Failed to parse JSON for: {raw_utterance[:60]}")
                return {
                    "raw_utterance": raw_utterance,
                    "normalized": raw_utterance,
                    "intent": "unknown",
                    "confidence_score": 0.0,
                    "entities": {"error_type": None, "component": None, "language": None, "framework": None},
                    "_parse_error": str(e)
                }
        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"[ConditionC] API error attempt {attempt+1}: {e}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise


# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------

MODEL_REGISTRY = {
    'gemini':   call_gemini,
    'groq':     call_groq,
    'cerebras': call_cerebras,
}

MODEL_NAMES = list(MODEL_REGISTRY.keys())
