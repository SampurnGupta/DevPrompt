from tests.helper import get_solution_code

def test_generate_001():
    code = get_solution_code()
    assert "react" in code.lower()
    assert "dropdown" in code.lower()
    assert any(x in code.lower() for x in ["usestate", "state", "toggle", "click", "open", "active"])
