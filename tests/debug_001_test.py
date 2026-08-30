from tests.helper import get_solution_code

def test_debug_001():
    code = get_solution_code()
    assert any(x in code.lower() for x in ["retry", "backoff", "sleep", "delay"])
    assert any(x in code.lower() for x in ["try", "except", "catch"])
