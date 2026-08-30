from tests.helper import get_solution_code

def test_refactor_004():
    code = get_solution_code()
    assert "async" in code.lower()
    assert "await" in code.lower()
    assert "try" in code.lower() or "catch" in code.lower()
