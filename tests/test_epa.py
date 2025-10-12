from api.epa import suggest_epa_from_payload


def test_epa_schema_valid_payload_passes():
    section_scores = {"sections_present": 2, "hpi_quality": 2, "ddx": 2}
    payload = {"epa6": 4, "epa2": 3}
    out = suggest_epa_from_payload(payload, section_scores)
    assert out["epa6"] == 4 and out["epa2"] == 3
    assert out["provenance"]["source"] == "bedrock"
    assert out["provenance"]["validated"] is True


def test_epa_schema_invalid_payload_falls_back():
    section_scores = {"sections_present": 2, "hpi_quality": 2, "ddx": 2}
    payload = {"epa6": 6, "epa2": 5, "extra": True}  # invalid per schema
    out = suggest_epa_from_payload(payload, section_scores)
    assert out["provenance"]["source"] == "fallback"
    # fallback defaults given section_scores above
    assert 3 <= out["epa6"] <= 4
    assert 2 <= out["epa2"] <= 3


def test_epa_clipping_rules_apply():
    section_scores = {"sections_present": 0, "hpi_quality": 0, "ddx": 0}
    payload = {"epa6": 5, "epa2": 3}
    out = suggest_epa_from_payload(payload, section_scores)
    # even if payload is valid, clipping should cap
    assert out["epa6"] <= 3
    assert out["epa2"] <= 2
    assert "presence_or_hpi_quality_zero" in out["clipped_by"]
    assert "ddx_zero" in out["clipped_by"]

