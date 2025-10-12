from api.gatekeeper import is_sufficient


def test_is_sufficient_false_on_short_text():
    ok, reason = is_sufficient("too short", min_lines=2, min_tokens=5)
    assert not ok
    assert "Too few" in reason


def test_is_sufficient_true_on_enough_lines_tokens():
    text = "one\n two three four five six\n seven eight nine ten"
    ok, _ = is_sufficient(text, min_lines=2, min_tokens=5)
    assert ok

