from tests.helper import get_solution_code

def test_generate_004():
    code = get_solution_code()
    assert "bcrypt" in code.lower() or "hash" in code.lower()
    assert "jwt" in code.lower() or "jsonwebtoken" in code.lower()
    assert "register" in code.lower() or "post" in code.lower()
