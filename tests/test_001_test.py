from tests.helper import get_solution_code

def test_test_001():
    code = get_solution_code()
    assert any(x in code.lower() for x in ["cart", "checkout", "payment", "order"])
    assert any(x in code.lower() for x in ["assert", "expect", "test", "should", "it("])
