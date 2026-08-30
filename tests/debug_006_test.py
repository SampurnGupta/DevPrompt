from tests.helper import get_solution_code

def test_debug_006():
    code = get_solution_code()
    assert any(x in code.lower() for x in ["close", "finally", "cleanup", "with", "try"])
