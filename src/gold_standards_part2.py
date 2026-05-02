# Gold standards: refactor (6) + explain (6) tasks
REFACTOR_EXPLAIN = {
    "refactor_001": {
        "functional_output_description": "Decompose a monolithic API into separate microservices by extracting domain-specific modules (auth, orders, users) into independent service files with clear interfaces and minimal coupling.",
        "intent_preservation_reference": "Refactor the monolithic API into smaller, separate microservices.",
        "expected_tools": ["search_codebase", "read_file", "write_file", "git_diff"],
        "minimum_required_tools": ["read_file", "write_file"],
        "entities": {"error_type": None, "component": "monolithic API", "language": None, "framework": None},
        "has_unit_test": True,
        "unit_test_path": "tests/refactor_001_test.py"
    },
    "refactor_002": {
        "functional_output_description": "Rename all cryptic variable names in the config module to descriptive, self-documenting names following the project's naming conventions, without changing any functional behavior.",
        "intent_preservation_reference": "Rename variables in the config module to be more descriptive.",
        "expected_tools": ["read_file", "write_file", "lint_code", "git_diff"],
        "minimum_required_tools": ["read_file", "write_file"],
        "entities": {"error_type": None, "component": "config module", "language": None, "framework": None},
        "has_unit_test": True,
        "unit_test_path": "tests/refactor_002_test.py"
    },
    "refactor_003": {
        "functional_output_description": "Refactor the user controller by applying the Strategy design pattern so that different user-handling behaviors are encapsulated in interchangeable strategy classes, reducing conditionals and improving extensibility.",
        "intent_preservation_reference": "Refactor the user controller to use the Strategy design pattern.",
        "expected_tools": ["search_codebase", "read_file", "write_file", "lint_code"],
        "minimum_required_tools": ["read_file", "write_file"],
        "entities": {"error_type": None, "component": "user controller", "language": None, "framework": None},
        "has_unit_test": True,
        "unit_test_path": "tests/refactor_003_test.py"
    },
    "refactor_004": {
        "functional_output_description": "Convert the auth service from callback-based or promise chaining to async/await syntax throughout, ensuring all error handling uses try/catch blocks and no callback hell remains.",
        "intent_preservation_reference": "Refactor the auth service to use async/await syntax.",
        "expected_tools": ["read_file", "write_file", "lint_code", "run_tests"],
        "minimum_required_tools": ["read_file", "write_file"],
        "entities": {"error_type": None, "component": "auth service", "language": "javascript", "framework": None},
        "has_unit_test": True,
        "unit_test_path": "tests/refactor_004_test.py"
    },
    "refactor_005": {
        "functional_output_description": "Extract all validation logic from its current location into a dedicated validators.py (or similar) module, update all import references, and ensure existing tests still pass.",
        "intent_preservation_reference": "Extract validation logic into a separate dedicated module.",
        "expected_tools": ["search_codebase", "read_file", "write_file", "run_tests"],
        "minimum_required_tools": ["read_file", "write_file"],
        "entities": {"error_type": None, "component": "validation logic", "language": None, "framework": None},
        "has_unit_test": True,
        "unit_test_path": "tests/refactor_005_test.py"
    },
    "refactor_006": {
        "functional_output_description": "Simplify the payment logic by breaking it into smaller, single-responsibility functions, removing duplicate code, and reducing cyclomatic complexity to improve readability and maintainability.",
        "intent_preservation_reference": "Simplify and reduce complexity of the payment processing logic.",
        "expected_tools": ["read_file", "write_file", "lint_code", "git_diff"],
        "minimum_required_tools": ["read_file", "write_file"],
        "entities": {"error_type": None, "component": "payment logic", "language": None, "framework": None},
        "has_unit_test": True,
        "unit_test_path": "tests/refactor_006_test.py"
    },
    "explain_001": {
        "functional_output_description": "Explain how the caching layer retrieves data (cache-aside, write-through, etc.) and how database indexing (B-tree, hash) speeds up queries that miss the cache. Should be conceptually accurate and referenced to the given architecture.",
        "intent_preservation_reference": "Explain how the caching layer interacts with the database and the role of indexing.",
        "expected_tools": ["read_file", "fetch_docs", "search_codebase"],
        "minimum_required_tools": ["read_file"],
        "entities": {"error_type": None, "component": "caching layer", "language": None, "framework": None},
        "has_unit_test": False,
        "unit_test_path": None
    },
    "explain_002": {
        "functional_output_description": "Explain how the Express middleware stack processes requests sequentially, where OAuth2 fits in the chain (token verification step), and how the callback to next() passes control between middleware.",
        "intent_preservation_reference": "Explain how the Express middleware stack interacts with OAuth authentication.",
        "expected_tools": ["read_file", "fetch_docs"],
        "minimum_required_tools": ["read_file"],
        "entities": {"error_type": None, "component": "middleware stack", "language": "javascript", "framework": "express"},
        "has_unit_test": False,
        "unit_test_path": None
    },
    "explain_003": {
        "functional_output_description": "Explain what the given regex pattern matches, broken down token by token. Should include examples of matching and non-matching strings and note any edge cases or gotchas.",
        "intent_preservation_reference": "Explain what the regex pattern does and what it matches.",
        "expected_tools": ["fetch_docs", "execute_shell"],
        "minimum_required_tools": ["fetch_docs"],
        "entities": {"error_type": None, "component": "regex pattern", "language": None, "framework": None},
        "has_unit_test": False,
        "unit_test_path": None
    },
    "explain_004": {
        "functional_output_description": "Explain the key differences between Docker (containerization, image-based isolation) and Kubernetes (orchestration, scaling, service discovery), and clarify when you need each.",
        "intent_preservation_reference": "Explain the difference between Docker and Kubernetes.",
        "expected_tools": ["fetch_docs"],
        "minimum_required_tools": ["fetch_docs"],
        "entities": {"error_type": None, "component": None, "language": None, "framework": "docker"},
        "has_unit_test": False,
        "unit_test_path": None
    },
    "explain_005": {
        "functional_output_description": "Explain the difference between Promises and async/await in JavaScript: how async/await is syntactic sugar over Promises, error handling differences (then/catch vs try/catch), and readability tradeoffs.",
        "intent_preservation_reference": "Explain the difference between Promises and async/await in JavaScript.",
        "expected_tools": ["fetch_docs"],
        "minimum_required_tools": ["fetch_docs"],
        "entities": {"error_type": None, "component": None, "language": "javascript", "framework": None},
        "has_unit_test": False,
        "unit_test_path": None
    },
    "explain_006": {
        "functional_output_description": "Explain why Redux was chosen for this project: the problem it solves (shared global state, predictable state updates, time-travel debugging), and why simpler alternatives (Context API) were insufficient.",
        "intent_preservation_reference": "Explain why Redux is being used in this project.",
        "expected_tools": ["read_file", "fetch_docs"],
        "minimum_required_tools": ["read_file"],
        "entities": {"error_type": None, "component": None, "language": "javascript", "framework": "redux"},
        "has_unit_test": False,
        "unit_test_path": None
    },
}
