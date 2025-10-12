from api.sanitize import strip_control, basic_deid, normalize_sentences


def test_strip_control_and_links():
    text = "Hello\x01 [Link](http://example.com) World"
    out = strip_control(text)
    assert "\x01" not in out
    assert "[Link]" not in out
    assert "Link" in out


def test_basic_deid_masks_entities():
    text = "John Doe visited on 2021-01-01. Call +1 555-123-4567."
    out = basic_deid(text)
    assert "John Doe" not in out
    assert "2021-01-01" not in out
    assert "555-123-4567" not in out
    assert "[NAME]" in out and "[DATE]" in out and "[PHONE]" in out


def test_normalize_sentences_trims_blank_lines():
    text = "\n line1 \n\n line2  \n"
    out = normalize_sentences(text)
    assert out.splitlines() == ["line1", "line2"]

