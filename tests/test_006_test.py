from tests.helper import get_solution_code

def test_test_006():
    code = get_solution_code()
    assert "fixture" in code.lower()
    assert any(x in code.lower() for x in ["yield", "teardown", "conn", "db", "database"])
