from tests.helper import get_solution_code

def test_composite_004():
    code = get_solution_code()
    assert "order" in code.lower()
    assert "test" in code.lower()
