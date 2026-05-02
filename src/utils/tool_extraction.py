"""
tool_extraction.py — Parse and validate TOOL_CALL declarations from LLM responses.

LLMs are instructed to format tool usage as:
    TOOL_CALL: tool_name(parameters)

This module extracts those calls and validates against the 8-tool whitelist.
NOTE: Tools are NOT executed — this is declarative intent measurement.
"""

import re
from typing import List, Dict, Any

# -------------------------------------------------------------------------
# 8-tool whitelist
# -------------------------------------------------------------------------

VALID_TOOLS = [
    'read_file',
    'write_file',
    'run_tests',
    'search_codebase',
    'git_diff',
    'lint_code',
    'fetch_docs',
    'execute_shell'
]

VALID_TOOLS_SET = set(VALID_TOOLS)

# Regex: matches TOOL_CALL: tool_name(anything)
_TOOL_CALL_PATTERN = re.compile(
    r'TOOL_CALL:\s*(\w+)\s*\(([^)]*)\)',
    re.MULTILINE | re.IGNORECASE
)


# -------------------------------------------------------------------------
# Core extraction
# -------------------------------------------------------------------------

def extract_tool_calls(response_text: str) -> List[Dict[str, Any]]:
    """
    Extract all TOOL_CALL declarations from a response string.

    Returns a list of dicts:
        [
            {'tool': 'read_file', 'params': 'path="src/login.py"', 'valid': True},
            {'tool': 'nonexistent_tool', 'params': '', 'valid': False},
            ...
        ]
    """
    matches = _TOOL_CALL_PATTERN.findall(response_text)
    results = []
    for tool_name, params in matches:
        tool_name_clean = tool_name.strip().lower()
        results.append({
            'tool': tool_name_clean,
            'params': params.strip(),
            'valid': tool_name_clean in VALID_TOOLS_SET
        })
    return results


def get_valid_tool_calls(response_text: str) -> List[Dict[str, Any]]:
    """Return only tool calls that use valid (whitelisted) tool names."""
    return [t for t in extract_tool_calls(response_text) if t['valid']]


def get_tool_names(response_text: str) -> List[str]:
    """Return list of valid tool names in order of appearance."""
    return [t['tool'] for t in get_valid_tool_calls(response_text)]


# -------------------------------------------------------------------------
# Validation + diagnostics
# -------------------------------------------------------------------------

def validate_tool_calls(extracted: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Given extracted tool calls, return a validation summary:
        {
            'total_calls': int,
            'valid_calls': int,
            'invalid_calls': int,
            'invalid_tool_names': list[str],
            'has_any_tool_call': bool,
            'tool_sequence': list[str]   # only valid tools, in order
        }
    """
    valid = [t for t in extracted if t['valid']]
    invalid = [t for t in extracted if not t['valid']]

    return {
        'total_calls': len(extracted),
        'valid_calls': len(valid),
        'invalid_calls': len(invalid),
        'invalid_tool_names': [t['tool'] for t in invalid],
        'has_any_tool_call': len(extracted) > 0,
        'tool_sequence': [t['tool'] for t in valid]
    }


def count_redundant_calls(tool_sequence: List[str]) -> int:
    """
    Count redundant tool calls: any call to a tool already called previously.
    Redundant = total_calls - unique_tools_called.
    """
    return len(tool_sequence) - len(set(tool_sequence))


# -------------------------------------------------------------------------
# System prompt fragment (injected into LLM prompts)
# -------------------------------------------------------------------------

TOOL_SYSTEM_PROMPT = """You are an expert software engineer helping with development tasks.
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

Provide working code solutions. Be concise but complete."""
