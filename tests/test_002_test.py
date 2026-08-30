from tests.helper import get_solution_code

def test_test_002():
    code = get_solution_code()
    assert "stripe" in code.lower()
    assert any(x in code.lower() for x in ["mock", "jest.mock", "patch", "mocker"])
