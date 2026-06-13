from app.services.execution_compare import _total_tokens


def test_total_tokens_from_total_field():
    assert _total_tokens({"total_tokens": 100}) == 100


def test_total_tokens_from_input_output():
    assert _total_tokens({"input_tokens": 40, "output_tokens": 60}) == 100


def test_total_tokens_empty():
    assert _total_tokens(None) == 0
    assert _total_tokens({}) == 0
