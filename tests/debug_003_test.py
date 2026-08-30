from tests.helper import get_solution_code

def test_debug_003():
    code = get_solution_code()
    assert "null" in code.lower()
    assert "if" in code.lower()
    assert any(x in code.lower() for x in ["login", "user", "username", "password"])
