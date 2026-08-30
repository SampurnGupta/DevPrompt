from tests.helper import get_solution_code

def test_composite_002():
    code = get_solution_code()
    assert "payment" in code.lower()
    assert any(x in code for x in ["#", "//", "/*"])
