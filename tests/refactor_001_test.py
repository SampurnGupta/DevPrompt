from tests.helper import get_solution_code

def test_refactor_001():
    code = get_solution_code()
    assert any(x in code.lower() for x in ["auth", "order", "user", "module", "service", "import", "require"])
