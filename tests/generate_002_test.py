from tests.helper import get_solution_code

def test_generate_002():
    code = get_solution_code()
    assert any(x in code.lower() for x in ["jwt", "token", "payload", "decode"])
    assert any(x in code.lower() for x in ["middleware", "request", "response", "get_response"])
