from tests.helper import get_solution_code

def test_composite_003():
    code = get_solution_code()
    assert "kafka" in code.lower()
    assert any(x in code.lower() for x in ["lag", "partition", "async", "await", "promise", "thread"])
