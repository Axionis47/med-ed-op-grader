from api.analysis import find_hpi_bounds, find_time_events, extract_pertinents, simple_summary, simple_ddx


def sample_lines():
    return [
        "Chief Complaint: facial droop",
        "HPI: 68-year-old with facial droop, forehead spared, no seizure.",
        "Last known well at 09:40.",
        "Ear rash denied. Aphasia noted.",
        "ROS: negative except as above.",
    ]


def test_find_hpi_bounds_basic():
    s, e, ev = find_hpi_bounds(sample_lines())
    assert s == 2 and e == 4
    assert ev and ev[0][0] == 2


def test_find_time_events_detects_onset():
    lines = sample_lines()
    tl = find_time_events(lines, (2, 4))
    assert tl["events"]
    ev = tl["events"][0]
    assert ev["type"] == "onset"
    assert ev["confidence"] >= 0.7


def test_extract_pertinents_marks_hpi():
    lines = sample_lines()
    out = extract_pertinents(lines, (2, 4), "stroke")
    names = {it["name"] for it in out["items"]}
    assert {"forehead spared", "no seizure"}.issubset(names)
    assert any(it["placement"] == "hpi" for it in out["items"])


def test_simple_summary_and_ddx_shapes():
    lines = sample_lines()
    summ = simple_summary(lines, (2, 4))
    assert isinstance(summ.get("has_two_sentences"), bool)
    ddx = simple_ddx(lines, (2, 4))
    assert isinstance(ddx, list) and len(ddx) >= 1 and {"dx", "evidence"}.issubset(ddx[0].keys())

