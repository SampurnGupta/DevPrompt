from tests.helper import get_solution_code

def test_refactor_006():
    code = get_solution_code()
    assert "payment" in code.lower()
