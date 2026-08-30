from tests.helper import get_solution_code

def test_test_005():
    code = get_solution_code()
    assert "test" in code.lower()
    assert any(x in code.lower() for x in ["none", "empty", "null", "invalid", "raise", "exception", "error"])
