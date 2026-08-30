from tests.helper import get_solution_code

def test_generate_003():
    code = get_solution_code()
    assert "pandas" in code.lower() or "pd" in code.lower()
    assert "drop_duplicates" in code.lower() or "duplicates" in code.lower()
    assert "fillna" in code.lower() or "dropna" in code.lower() or "null" in code.lower() or "na" in code.lower()
