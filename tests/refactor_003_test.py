from tests.helper import get_solution_code

def test_refactor_003():
    code = get_solution_code()
    assert any(x in code.lower() for x in ["strategy", "interface", "class", "encapsulate", "behavior"])
