from tests.helper import get_solution_code

def test_test_003():
    code = get_solution_code()
    assert "login" in code.lower()
    assert any(x in code.lower() for x in ["401", "400", "unauthorized", "bad request", "jwt", "token"])
