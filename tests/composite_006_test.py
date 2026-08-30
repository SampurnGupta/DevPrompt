from tests.helper import get_solution_code

def test_composite_006():
    code = get_solution_code()
    assert "user" in code.lower() or "profile" in code.lower()
    assert "middleware" in code.lower() or "auth" in code.lower() or "token" in code.lower()
