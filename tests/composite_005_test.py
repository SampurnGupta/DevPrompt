from tests.helper import get_solution_code

def test_composite_005():
    code = get_solution_code()
    assert any(x in code.lower() for x in ["leak", "pool", "connection", "close", "cleanup"])
