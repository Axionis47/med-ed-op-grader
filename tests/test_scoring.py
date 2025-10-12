from api.scoring import run_all_scoring


def test_scoring_bundle_happy_path():
    analysis = {
        "sections": [
            {"name": "CC", "start_line": 1, "end_line": 1},
            {"name": "HPI", "start_line": 2, "end_line": 5},
            {"name": "PMH", "start_line": 6, "end_line": 7},
            {"name": "FH", "start_line": 8, "end_line": 8},
            {"name": "SH", "start_line": 9, "end_line": 9},
            {"name": "ROS", "start_line": 10, "end_line": 10},
        ],
        "timeline": {"events": [
            {"type": "onset", "confidence": 0.8, "evidence": [[2, 2]]}
        ]},
        "pertinents": {"items": [
            {"name": "forehead spared", "placement": "hpi", "evidence": [[3,3]]},
            {"name": "no seizure", "placement": "hpi", "evidence": [[4,4]]},
            {"name": "aphasia", "placement": "hpi", "evidence": [[5,5]]},
        ]},
        "summary": {"has_two_sentences": True, "evidence": [[2,5]]},
        "ddx": [
            {"dx":"ischemic stroke","why_for":["focal"],"why_against":[],"priority":1,"evidence":[[2,2]]},
            {"dx":"hemorrhagic stroke","why_for":[],"why_against":["no severe headache"],"priority":2,"evidence":[[2,2]]},
            {"dx":"Bell's palsy","why_for":["facial droop"],"why_against":["forehead spared"],"priority":3,"evidence":[[2,2]]},
        ],
    }
    out = run_all_scoring(analysis)
    assert out["overall"]["sum"] >= 12
    assert out["overall"]["max"] == 16
    assert len(out["steps"]) == 2

