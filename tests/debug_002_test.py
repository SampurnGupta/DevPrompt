from tests.helper import get_solution_code

def test_debug_002():
    code = get_solution_code()
    assert "pandas" in code or "pd" in code
    assert "merge" in code
    assert any(x in code for x in ["column", "key", "if", "try", "except", "validation", "intersection"])
