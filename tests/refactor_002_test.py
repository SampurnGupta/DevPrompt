from tests.helper import get_solution_code

def test_refactor_002():
    code = get_solution_code()
    assert "config" in code.lower()
