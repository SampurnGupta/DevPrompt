from tests.helper import get_solution_code

def test_test_004():
    code = get_solution_code()
    assert "locust" in code.lower() or "httpuser" in code.lower()
    assert "search" in code.lower()
