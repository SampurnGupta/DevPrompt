from tests.helper import get_solution_code

def test_refactor_005():
    code = get_solution_code()
    assert any(x in code.lower() for x in ["validate", "validation", "validator", "import", "require", "export"])
