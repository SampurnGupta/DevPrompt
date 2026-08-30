# Gold standards: debug (6) + generate (6) tasks
DEBUG_GENERATE = {
    "debug_001": {
        "functional_output_description": "Identify and fix the database connection timeout that causes an infinite retry loop. Solution should implement exponential backoff or a connection pool with a max-retry limit and proper exception handling.",
        "intent_preservation_reference": "Fix the database connection timeout causing an infinite retry loop. Solution must implement exponential backoff or a connection pool with max-retry limit and proper exception handling.",
        "expected_tools": ["search_codebase", "read_file", "write_file", "run_tests"],
        "minimum_required_tools": ["search_codebase", "read_file", "write_file"],
        "alternative_tool_sequences": [
            ["read_file", "search_codebase", "write_file", "run_tests"],
            ["search_codebase", "read_file", "write_file"],
            ["read_file", "write_file", "run_tests"]
        ],
        "entities": {"error_type": "TimeoutError", "component": "database connection", "language": None, "framework": None},
        "has_unit_test": True,
        "unit_test_path": "tests/debug_001_test.py"
    },
    "debug_002": {
        "functional_output_description": "Fix the KeyError raised when merging two pandas DataFrames with mismatched or missing column keys. Solution should validate shared keys before merge and handle missing columns gracefully.",
        "intent_preservation_reference": "Fix the KeyError when merging two pandas DataFrames. Solution must validate shared keys before merge and handle missing columns gracefully.",
        "expected_tools": ["read_file", "search_codebase", "write_file", "run_tests"],
        "minimum_required_tools": ["search_codebase", "read_file", "write_file"],
        "alternative_tool_sequences": [
            ["search_codebase", "read_file", "write_file", "run_tests"],
            ["read_file", "write_file", "run_tests"],
            ["search_codebase", "read_file", "write_file"]
        ],
        "entities": {"error_type": "KeyError", "component": "DataFrame merge", "language": "python", "framework": "pandas"},
        "has_unit_test": True,
        "unit_test_path": "tests/debug_002_test.py"
    },
    "debug_003": {
        "functional_output_description": "Fix the NullPointerException in the login service by adding null checks before accessing user object fields. Solution should return a proper error response for null inputs rather than crashing.",
        "intent_preservation_reference": "Fix the NullPointerException in the login service. Solution must add null checks and return a proper error response for null inputs.",
        "expected_tools": ["search_codebase", "read_file", "write_file", "run_tests"],
        "minimum_required_tools": ["search_codebase", "read_file", "write_file"],
        "alternative_tool_sequences": [
            ["read_file", "search_codebase", "write_file", "run_tests"],
            ["search_codebase", "read_file", "write_file"],
            ["read_file", "write_file", "run_tests"]
        ],
        "entities": {"error_type": "NullPointerException", "component": "login service", "language": "java", "framework": None},
        "has_unit_test": True,
        "unit_test_path": "tests/debug_003_test.py"
    },
    "debug_004": {
        "functional_output_description": "Diagnose why the Docker container exits with code 137 (OOM kill) every few hours. Solution should identify memory-intensive processes, set appropriate container memory limits, and suggest heap tuning.",
        "intent_preservation_reference": "Fix the Docker container OOM crash (exit code 137). Solution must identify memory-intensive processes, set memory limits, or suggest heap tuning.",
        "expected_tools": ["execute_shell", "read_file", "write_file"],
        "minimum_required_tools": ["execute_shell", "read_file", "write_file"],
        "alternative_tool_sequences": [
            ["read_file", "execute_shell", "write_file"],
            ["execute_shell", "write_file"],
            ["read_file", "write_file"]
        ],
        "entities": {"error_type": "OOMKilled", "component": "docker container", "language": None, "framework": "docker"},
        "has_unit_test": False,
        "unit_test_path": None
    },
    "debug_005": {
        "functional_output_description": "Fix the Android app crash that occurs when uploading an image. Solution should handle large bitmap memory allocation, add try-catch for OutOfMemoryError, and compress images before upload.",
        "intent_preservation_reference": "Fix the Android app crash when uploading an image. Solution must handle bitmap memory allocation, catch OutOfMemoryError, and compress images.",
        "expected_tools": ["search_codebase", "read_file", "write_file", "run_tests"],
        "minimum_required_tools": ["search_codebase", "read_file", "write_file"],
        "alternative_tool_sequences": [
            ["read_file", "search_codebase", "write_file", "run_tests"],
            ["search_codebase", "read_file", "write_file"],
            ["read_file", "write_file", "run_tests"]
        ],
        "entities": {"error_type": "OutOfMemoryError", "component": "image upload", "language": "kotlin", "framework": "android"},
        "has_unit_test": False,
        "unit_test_path": None
    },
    "debug_006": {
        "functional_output_description": "Fix the RuntimeException thrown by the order handler caused by a memory leak. Solution should identify unclosed resources or circular references, fix the leak, and add proper resource cleanup.",
        "intent_preservation_reference": "Fix the RuntimeException and memory leak in the order handler. Solution must close resources, resolve circular references, and clean up.",
        "expected_tools": ["search_codebase", "read_file", "write_file", "run_tests"],
        "minimum_required_tools": ["search_codebase", "read_file", "write_file"],
        "alternative_tool_sequences": [
            ["read_file", "search_codebase", "write_file", "run_tests"],
            ["search_codebase", "read_file", "write_file"],
            ["read_file", "write_file", "run_tests"]
        ],
        "entities": {"error_type": "RuntimeException", "component": "order handler", "language": None, "framework": None},
        "has_unit_test": True,
        "unit_test_path": "tests/debug_006_test.py"
    },
    "generate_001": {
        "functional_output_description": "Generate a React dropdown menu component with state management, open/close toggle, option selection, and keyboard accessibility. Should be reusable with customizable options prop.",
        "intent_preservation_reference": "Create a dropdown menu component in React. Solution must have state management, toggle, option selection, and keyboard accessibility.",
        "expected_tools": ["fetch_docs", "write_file"],
        "minimum_required_tools": ["write_file"],
        "alternative_tool_sequences": [
            ["write_file"],
            ["fetch_docs", "write_file", "lint_code"],
            ["write_file", "lint_code"]
        ],
        "entities": {"error_type": None, "component": "dropdown menu", "language": "javascript", "framework": "react"},
        "has_unit_test": True,
        "unit_test_path": "tests/generate_001_test.py"
    },
    "generate_002": {
        "functional_output_description": "Generate a Django middleware that validates JWT tokens on incoming requests, extracts user identity, and returns 401 for missing or invalid tokens. Should support token refresh logic.",
        "intent_preservation_reference": "Write a JWT authentication middleware for Django. Solution must validate tokens, extract user identity, return 401 for invalid tokens, and support refresh.",
        "expected_tools": ["fetch_docs", "write_file", "lint_code"],
        "minimum_required_tools": ["fetch_docs", "write_file"],
        "alternative_tool_sequences": [
            ["write_file"],
            ["write_file", "lint_code"],
            ["fetch_docs", "write_file"]
        ],
        "entities": {"error_type": None, "component": "middleware", "language": "python", "framework": "django"},
        "has_unit_test": True,
        "unit_test_path": "tests/generate_002_test.py"
    },
    "generate_003": {
        "functional_output_description": "Generate a pandas script that loads a CSV, removes duplicates, handles missing values, normalizes numeric columns to 0-1 range, and outputs a cleaned CSV file.",
        "intent_preservation_reference": "Write a pandas script to clean and normalize a CSV file. Solution must load CSV, deduplicate, handle nulls, scale/normalize columns, and export CSV.",
        "expected_tools": ["read_file", "write_file", "execute_shell"],
        "minimum_required_tools": ["write_file"],
        "alternative_tool_sequences": [
            ["write_file", "execute_shell"],
            ["read_file", "write_file"],
            ["read_file", "write_file", "execute_shell"]
        ],
        "entities": {"error_type": None, "component": "data pipeline", "language": "python", "framework": "pandas"},
        "has_unit_test": True,
        "unit_test_path": "tests/generate_003_test.py"
    },
    "generate_004": {
        "functional_output_description": "Generate an Express.js REST endpoint POST /register that validates input fields, hashes the password with bcrypt, saves the user to the database, and returns a JWT token on success.",
        "intent_preservation_reference": "Generate a user registration REST endpoint in Express.js. Solution must validate fields, bcrypt hash password, save user, and return JWT on success.",
        "expected_tools": ["fetch_docs", "write_file", "run_tests"],
        "minimum_required_tools": ["fetch_docs", "write_file"],
        "alternative_tool_sequences": [
            ["write_file"],
            ["write_file", "run_tests"],
            ["fetch_docs", "write_file"]
        ],
        "entities": {"error_type": None, "component": "registration endpoint", "language": "javascript", "framework": "express"},
        "has_unit_test": True,
        "unit_test_path": "tests/generate_004_test.py"
    },
    "generate_005": {
        "functional_output_description": "Generate a bash script that automates daily backups of specified directories using tar and cron scheduling. Should include logging, error handling, and cleanup of old backups.",
        "intent_preservation_reference": "Write a bash script to automate daily backups using tar and cron. Solution must include logging, error handling, and cleanup of old backups.",
        "expected_tools": ["fetch_docs", "write_file", "execute_shell"],
        "minimum_required_tools": ["write_file"],
        "alternative_tool_sequences": [
            ["write_file", "execute_shell"],
            ["fetch_docs", "write_file"],
            ["write_file"]
        ],
        "entities": {"error_type": None, "component": "backup script", "language": "bash", "framework": None},
        "has_unit_test": False,
        "unit_test_path": None
    },
    "generate_006": {
        "functional_output_description": "Generate a SQL query that retrieves the top 10 customers by total purchase amount, including customer name and total spend, ordered descending.",
        "intent_preservation_reference": "Write a SQL query to get the top 10 customers by total spend. Query must include customer name and spend, ordered descending.",
        "expected_tools": ["fetch_docs", "write_file"],
        "minimum_required_tools": ["write_file"],
        "alternative_tool_sequences": [
            ["write_file"],
            ["fetch_docs", "write_file"]
        ],
        "entities": {"error_type": None, "component": "customer query", "language": "sql", "framework": None},
        "has_unit_test": False,
        "unit_test_path": None
    },
}
