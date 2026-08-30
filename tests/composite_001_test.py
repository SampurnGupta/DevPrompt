from tests.helper import get_solution_code

def test_composite_001():
    code = get_solution_code()
    assert "null" in code.lower()
    assert "test" in code.lower() or "assert" in code.lower() or "expect" in code.lower()
