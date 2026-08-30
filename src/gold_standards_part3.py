# Gold standards: scaffold (6) + test (6) + document (6) + composite (6) tasks
SCAFFOLD_TEST_DOCUMENT_COMPOSITE = {
    "scaffold_001": {
        "functional_output_description": "Scaffold a Node.js Express application with TypeScript support and Next.js integration: directory structure, package.json with all dependencies, tsconfig.json, and a working dev server entry point.",
        "intent_preservation_reference": "Scaffold a Node.js Express app with Next.js and TypeScript. Solution must set up directory structure, package.json, tsconfig.json, and dev entry point.",
        "expected_tools": ["execute_shell", "write_file", "fetch_docs"],
        "minimum_required_tools": ["execute_shell", "write_file"],
        "alternative_tool_sequences": [
            ["write_file", "execute_shell"],
            ["execute_shell", "write_file"],
            ["write_file"]
        ],
        "entities": {"error_type": None, "component": "project scaffold", "language": "typescript", "framework": "express"},
        "has_unit_test": False,
        "unit_test_path": None
    },
    "scaffold_002": {
        "functional_output_description": "Scaffold a Flutter app integrated with Firebase (Auth + Firestore) alongside a FastAPI Python backend. Should include directory structure, pubspec.yaml, firebase_options.dart placeholder, and FastAPI main.py skeleton.",
        "intent_preservation_reference": "Scaffold a Flutter app with Firebase and a FastAPI backend. Solution must configure directory, pubspec.yaml, Firebase options, and main.py.",
        "expected_tools": ["execute_shell", "write_file", "fetch_docs"],
        "minimum_required_tools": ["fetch_docs", "write_file"],
        "alternative_tool_sequences": [
            ["write_file", "execute_shell"],
            ["fetch_docs", "write_file"],
            ["write_file"]
        ],
        "entities": {"error_type": None, "component": "project scaffold", "language": "dart", "framework": "flutter"},
        "has_unit_test": False,
        "unit_test_path": None
    },
    "scaffold_003": {
        "functional_output_description": "Scaffold a new Django project with Django REST Framework and token-based authentication (djoser or SimpleJWT), including settings.py configuration, requirements.txt, and a working /api/auth/ URL route.",
        "intent_preservation_reference": "Scaffold a Django project with REST Framework and authentication. Solution must include settings.py, requirements.txt, and auth routes.",
        "expected_tools": ["execute_shell", "write_file", "fetch_docs"],
        "minimum_required_tools": ["execute_shell", "write_file"],
        "alternative_tool_sequences": [
            ["write_file", "execute_shell"],
            ["execute_shell", "write_file"],
            ["write_file"]
        ],
        "entities": {"error_type": None, "component": "project scaffold", "language": "python", "framework": "django"},
        "has_unit_test": False,
        "unit_test_path": None
    },
    "scaffold_004": {
        "functional_output_description": "Scaffold a Terraform project for AWS infrastructure with Prometheus monitoring: directory layout (modules/, environments/), provider.tf, main.tf with EC2/ECS resource stubs, and a prometheus.yml config.",
        "intent_preservation_reference": "Scaffold a Terraform project for AWS with Prometheus monitoring. Solution must set up provider.tf, modules, environment config, and prometheus.yml.",
        "expected_tools": ["fetch_docs", "write_file", "execute_shell"],
        "minimum_required_tools": ["write_file"],
        "alternative_tool_sequences": [
            ["write_file", "execute_shell"],
            ["fetch_docs", "write_file"],
            ["write_file"]
        ],
        "entities": {"error_type": None, "component": "infrastructure scaffold", "language": None, "framework": "terraform"},
        "has_unit_test": False,
        "unit_test_path": None
    },
    "scaffold_005": {
        "functional_output_description": "Create a monorepo structure using npm workspaces or Turborepo with a shared component library (packages/ui), an app (apps/web), and proper package.json linking between them.",
        "intent_preservation_reference": "Create a monorepo with a shared component library. Solution must set up spaces/Turborepo, shared ui package, app, and package.json linking.",
        "expected_tools": ["execute_shell", "write_file", "fetch_docs"],
        "minimum_required_tools": ["execute_shell", "write_file"],
        "alternative_tool_sequences": [
            ["write_file", "execute_shell"],
            ["execute_shell", "write_file"],
            ["write_file"]
        ],
        "entities": {"error_type": None, "component": "monorepo", "language": "javascript", "framework": None},
        "has_unit_test": False,
        "unit_test_path": None
    },
    "scaffold_006": {
        "functional_output_description": "Scaffold a data science project with a Conda environment (environment.yml), Jupyter notebooks directory, and a FastAPI app skeleton for serving model predictions, with README instructions.",
        "intent_preservation_reference": "Scaffold a Jupyter + Conda project with a FastAPI backend. Solution must provide environment.yml, notebook folders, API skeleton, and README.",
        "expected_tools": ["execute_shell", "write_file", "fetch_docs"],
        "minimum_required_tools": ["write_file"],
        "alternative_tool_sequences": [
            ["write_file", "execute_shell"],
            ["execute_shell", "write_file"],
            ["write_file"]
        ],
        "entities": {"error_type": None, "component": "project scaffold", "language": "python", "framework": "fastapi"},
        "has_unit_test": False,
        "unit_test_path": None
    },
    "test_001": {
        "functional_output_description": "Write end-to-end tests for the checkout flow: add item to cart, proceed to checkout, enter payment details, submit order, and assert order confirmation response. Should cover happy path and one failure case.",
        "intent_preservation_reference": "Write tests for the checkout flow. Tests must cover adding to cart, checkout, payment, confirmation, and failure cases.",
        "expected_tools": ["read_file", "write_file", "run_tests"],
        "minimum_required_tools": ["write_file"],
        "alternative_tool_sequences": [
            ["read_file", "write_file", "run_tests"],
            ["write_file", "run_tests"],
            ["read_file", "write_file"]
        ],
        "entities": {"error_type": None, "component": "checkout flow", "language": None, "framework": None},
        "has_unit_test": True,
        "unit_test_path": "tests/test_001_test.py"
    },
    "test_002": {
        "functional_output_description": "Write unit tests for the payment service that mock the Stripe API using jest.mock() or unittest.mock, testing both successful charge and declined card scenarios without making real API calls.",
        "intent_preservation_reference": "Write unit tests that mock the Stripe API for the payment service. Tests must use jest.mock/unittest.mock, covering success and declined scenarios.",
        "expected_tools": ["read_file", "fetch_docs", "write_file", "run_tests"],
        "minimum_required_tools": ["write_file"],
        "alternative_tool_sequences": [
            ["read_file", "write_file", "run_tests"],
            ["fetch_docs", "write_file", "run_tests"],
            ["read_file", "fetch_docs", "write_file"],
            ["write_file", "run_tests"]
        ],
        "entities": {"error_type": None, "component": "payment service", "language": None, "framework": "stripe"},
        "has_unit_test": True,
        "unit_test_path": "tests/test_002_test.py"
    },
    "test_003": {
        "functional_output_description": "Write Jest unit tests for the login service: test successful login returns JWT, test wrong password returns 401, test missing fields returns 400, using mocked database calls.",
        "intent_preservation_reference": "Write Jest unit tests for the login service. Tests must cover success, 401 wrong password, 400 missing fields, using mocked database calls.",
        "expected_tools": ["read_file", "fetch_docs", "write_file", "run_tests"],
        "minimum_required_tools": ["write_file"],
        "alternative_tool_sequences": [
            ["read_file", "write_file", "run_tests"],
            ["fetch_docs", "write_file", "run_tests"],
            ["read_file", "fetch_docs", "write_file"],
            ["write_file", "run_tests"]
        ],
        "entities": {"error_type": None, "component": "login service", "language": "javascript", "framework": "jest"},
        "has_unit_test": True,
        "unit_test_path": "tests/test_003_test.py"
    },
    "test_004": {
        "functional_output_description": "Write Locust load tests for the search endpoint that simulate concurrent users sending search queries, with configurable user count and ramp-up rate, and assertions on p95 response time.",
        "intent_preservation_reference": "Write Locust load tests for the search endpoint. Tests must simulate concurrent search queries, ramp-up, and assert p95 response times.",
        "expected_tools": ["read_file", "fetch_docs", "write_file", "execute_shell"],
        "minimum_required_tools": ["write_file"],
        "alternative_tool_sequences": [
            ["read_file", "write_file"],
            ["fetch_docs", "write_file", "execute_shell"],
            ["read_file", "fetch_docs", "write_file"]
        ],
        "entities": {"error_type": None, "component": "search endpoint", "language": "python", "framework": "locust"},
        "has_unit_test": True,
        "unit_test_path": "tests/test_004_test.py"
    },
    "test_005": {
        "functional_output_description": "Write pytest unit tests for data validation functions: test valid inputs pass, test edge cases (empty string, None, out-of-range values) raise appropriate exceptions or return error flags.",
        "intent_preservation_reference": "Write pytest unit tests for data validation functions. Tests must cover valid inputs and edge cases like empty strings, nulls, and limits.",
        "expected_tools": ["read_file", "write_file", "run_tests"],
        "minimum_required_tools": ["write_file"],
        "alternative_tool_sequences": [
            ["read_file", "write_file", "run_tests"],
            ["write_file", "run_tests"],
            ["read_file", "write_file"]
        ],
        "entities": {"error_type": None, "component": "data validation", "language": "python", "framework": "pytest"},
        "has_unit_test": True,
        "unit_test_path": "tests/test_005_test.py"
    },
    "test_006": {
        "functional_output_description": "Write a pytest fixture that sets up a real or in-memory database connection before each test and tears it down after, usable across multiple test modules via conftest.py.",
        "intent_preservation_reference": "Write a pytest fixture for database connection. Solution must implement setup and teardown of DB connections in conftest.py.",
        "expected_tools": ["read_file", "fetch_docs", "write_file", "run_tests"],
        "minimum_required_tools": ["write_file"],
        "alternative_tool_sequences": [
            ["read_file", "write_file"],
            ["fetch_docs", "write_file"],
            ["read_file", "fetch_docs", "write_file", "run_tests"]
        ],
        "entities": {"error_type": None, "component": "database connection", "language": "python", "framework": "pytest"},
        "has_unit_test": True,
        "unit_test_path": "tests/test_006_test.py"
    },
    "document_001": {
        "functional_output_description": "Add clear inline comments to the payment processing code explaining each major step: validation, charge initiation, rollback logic, and confirmation. Comments should explain WHY, not just what.",
        "intent_preservation_reference": "Add inline comments explaining payment processing step logic. Comments must explain why validation, charge, and rollback are implemented.",
        "expected_tools": ["read_file", "write_file"],
        "minimum_required_tools": ["read_file", "write_file"],
        "alternative_tool_sequences": [
            ["read_file", "write_file"],
            ["write_file"]
        ],
        "entities": {"error_type": None, "component": "payment processing", "language": None, "framework": None},
        "has_unit_test": False,
        "unit_test_path": None
    },
    "document_002": {
        "functional_output_description": "Write a README section documenting all environment variables required by the project (name, description, example value, whether required) and the full project setup steps from clone to running locally.",
        "intent_preservation_reference": "Document environment variables and project setup in the README. README must detail names, usage, local setup, and clone instructions.",
        "expected_tools": ["read_file", "write_file"],
        "minimum_required_tools": ["read_file", "write_file"],
        "alternative_tool_sequences": [
            ["read_file", "write_file"],
            ["write_file"]
        ],
        "entities": {"error_type": None, "component": "README", "language": None, "framework": None},
        "has_unit_test": False,
        "unit_test_path": None
    },
    "document_003": {
        "functional_output_description": "Write JSDoc comments for all public functions in the API module: @param with types and descriptions, @returns with type and description, @throws for error cases, and a one-line @description.",
        "intent_preservation_reference": "Write JSDoc comments for public API functions. Comments must document @param with types, @returns, @throws, and @description.",
        "expected_tools": ["read_file", "write_file", "lint_code"],
        "minimum_required_tools": ["read_file", "write_file"],
        "alternative_tool_sequences": [
            ["read_file", "write_file"],
            ["read_file", "write_file", "lint_code"]
        ],
        "entities": {"error_type": None, "component": "API module", "language": "javascript", "framework": None},
        "has_unit_test": False,
        "unit_test_path": None
    },
    "document_004": {
        "functional_output_description": "Write CHANGELOG entries for the new release following Keep a Changelog format: Added, Changed, Fixed, Deprecated sections with bullet points for each change in the version.",
        "intent_preservation_reference": "Write CHANGELOG entries for the new release following Keep a Changelog. Changelog must have Added, Changed, Fixed, and Deprecated bullet lists.",
        "expected_tools": ["git_diff", "write_file"],
        "minimum_required_tools": ["git_diff", "write_file"],
        "alternative_tool_sequences": [
            ["git_diff", "write_file"],
            ["write_file"]
        ],
        "entities": {"error_type": None, "component": "CHANGELOG", "language": None, "framework": None},
        "has_unit_test": False,
        "unit_test_path": None
    },
    "document_005": {
        "functional_output_description": "Add Google-style docstrings to all Python data processing functions: one-line summary, Args section with types, Returns section with type and description, and Raises section where applicable.",
        "intent_preservation_reference": "Add Google-style docstrings to Python data functions. Docstrings must cover summaries, Args with types, Returns, and Raises.",
        "expected_tools": ["read_file", "write_file", "lint_code"],
        "minimum_required_tools": ["read_file", "write_file"],
        "alternative_tool_sequences": [
            ["read_file", "write_file"],
            ["read_file", "write_file", "lint_code"]
        ],
        "entities": {"error_type": None, "component": "data processing functions", "language": "python", "framework": None},
        "has_unit_test": False,
        "unit_test_path": None
    },
    "document_006": {
        "functional_output_description": "Create a Postman collection JSON and a Swagger/OpenAPI YAML spec documenting all API endpoints: path, method, request body schema, response codes, and example payloads.",
        "intent_preservation_reference": "Create Postman collection and Swagger OpenAPI spec. Spec must document path, methods, request bodies, response codes, and payloads.",
        "expected_tools": ["read_file", "fetch_docs", "write_file"],
        "minimum_required_tools": ["read_file", "write_file"],
        "alternative_tool_sequences": [
            ["read_file", "write_file"],
            ["fetch_docs", "write_file"],
            ["read_file", "fetch_docs", "write_file"]
        ],
        "entities": {"error_type": None, "component": "API endpoints", "language": "python", "framework": "swagger"},
        "has_unit_test": False,
        "unit_test_path": None
    },
    "composite_001": {
        "functional_output_description": "Fix the NullPointerException in the user service AND write unit tests that verify the fix prevents regression. The fix should handle null inputs gracefully; tests should cover null, valid, and edge-case inputs.",
        "intent_preservation_reference": "Fix the NullPointerException in the user service and write regression unit tests. Fix must check null inputs gracefully; tests must cover valid and boundary cases.",
        "expected_tools": ["search_codebase", "read_file", "write_file", "run_tests"],
        "minimum_required_tools": ["read_file", "write_file", "run_tests"],
        "alternative_tool_sequences": [
            ["read_file", "search_codebase", "write_file", "run_tests"],
            ["search_codebase", "read_file", "write_file", "run_tests"],
            ["read_file", "write_file", "run_tests"]
        ],
        "entities": {"error_type": "NullPointerException", "component": "user service", "language": None, "framework": None},
        "has_unit_test": True,
        "unit_test_path": "tests/composite_001_test.py"
    },
    "composite_002": {
        "functional_output_description": "Refactor the payment service to separate concerns (validation, charge, notification into distinct modules) AND add inline documentation comments explaining each module's responsibility.",
        "intent_preservation_reference": "Refactor the payment service for separation of concerns and document changes. Refactoring must split modules; inline comments must explain responsibilities.",
        "expected_tools": ["read_file", "write_file", "lint_code", "git_diff"],
        "minimum_required_tools": ["git_diff", "read_file", "write_file"],
        "alternative_tool_sequences": [
            ["read_file", "write_file", "git_diff"],
            ["read_file", "write_file", "lint_code"],
            ["read_file", "write_file"]
        ],
        "entities": {"error_type": None, "component": "payment service", "language": None, "framework": None},
        "has_unit_test": True,
        "unit_test_path": "tests/composite_002_test.py"
    },
    "composite_003": {
        "functional_output_description": "Explain why the Kafka consumer is lagging (consumer group lag, slow processing, partition imbalance) AND generate a fixed implementation using async processing to reduce lag.",
        "intent_preservation_reference": "Explain Kafka consumer lag reasons and generate an async fix. Explanation must address consumer group partition lag; fix must use async processing.",
        "expected_tools": ["read_file", "fetch_docs", "write_file", "run_tests"],
        "minimum_required_tools": ["fetch_docs", "read_file", "write_file"],
        "alternative_tool_sequences": [
            ["read_file", "write_file", "run_tests"],
            ["read_file", "fetch_docs", "write_file"],
            ["fetch_docs", "write_file", "run_tests"],
            ["read_file", "write_file"]
        ],
        "entities": {"error_type": None, "component": "kafka consumer", "language": None, "framework": "kafka"},
        "has_unit_test": True,
        "unit_test_path": "tests/composite_003_test.py"
    },
    "composite_004": {
        "functional_output_description": "Scaffold a new order management microservice (directory structure, entry point, dependencies) AND write integration tests for the main endpoints (create order, get order, cancel order).",
        "intent_preservation_reference": "Scaffold an order management microservice and write integration tests. Solution must generate files/folders and write integration tests for create/get/cancel API endpoints.",
        "expected_tools": ["execute_shell", "write_file", "fetch_docs", "run_tests"],
        "minimum_required_tools": ["execute_shell", "write_file", "run_tests"],
        "alternative_tool_sequences": [
            ["write_file", "run_tests"],
            ["execute_shell", "write_file", "run_tests"],
            ["write_file", "execute_shell", "run_tests"]
        ],
        "entities": {"error_type": None, "component": "order management service", "language": None, "framework": None},
        "has_unit_test": True,
        "unit_test_path": "tests/composite_004_test.py"
    },
    "composite_005": {
        "functional_output_description": "Fix the memory leak in the connection pool (identify unclosed connections, add cleanup logic) AND write documentation explaining the root cause and the fix applied.",
        "intent_preservation_reference": "Fix connection pool memory leak and document cause and fix. Fix must close connections and add cleanup; documentation must detail root cause.",
        "expected_tools": ["search_codebase", "read_file", "write_file", "run_tests"],
        "minimum_required_tools": ["search_codebase", "read_file", "write_file"],
        "alternative_tool_sequences": [
            ["read_file", "search_codebase", "write_file", "run_tests"],
            ["search_codebase", "read_file", "write_file"],
            ["read_file", "write_file", "run_tests"]
        ],
        "entities": {"error_type": "MemoryLeak", "component": "connection pool", "language": None, "framework": None},
        "has_unit_test": True,
        "unit_test_path": "tests/composite_005_test.py"
    },
    "composite_006": {
        "functional_output_description": "Generate a REST API endpoint for user profile updates (PUT /users/:id with validation and DB update) AND explain how it integrates with the existing auth middleware (token verification, user ownership check).",
        "intent_preservation_reference": "Generate a user profile update endpoint and explain auth middleware integration. Endpoint must validate PUT requests; explanation must cover token verification.",
        "expected_tools": ["read_file", "fetch_docs", "write_file", "run_tests"],
        "minimum_required_tools": ["read_file", "write_file"],
        "alternative_tool_sequences": [
            ["read_file", "write_file"],
            ["write_file", "run_tests"],
            ["read_file", "fetch_docs", "write_file"]
        ],
        "entities": {"error_type": None, "component": "user profile endpoint", "language": None, "framework": None},
        "has_unit_test": True,
        "unit_test_path": "tests/composite_006_test.py"
    },
}
