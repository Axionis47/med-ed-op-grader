import re

CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
MD_LINK_RE = re.compile(r"\[(.*?)\]\((.*?)\)")


def strip_control(text: str) -> str:
    text = CONTROL_CHARS_RE.sub(" ", text)
    text = MD_LINK_RE.sub(r"\1", text)
    return text


NAME_RE = re.compile(r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b")
DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\b")
PHONE_RE = re.compile(r"\b(\+?\d[\d\-\s]{7,}\d)\b")


def basic_deid(text: str) -> str:
    text = NAME_RE.sub("[NAME]", text)
    text = DATE_RE.sub("[DATE]", text)
    text = PHONE_RE.sub("[PHONE]", text)
    return text


def normalize_sentences(text: str) -> str:
    # naive normalization; can be replaced later
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return "\n".join(lines)


def confidence_summary_from_transcribe(json_obj: dict) -> dict:
    # Placeholder: compute simple average if present
    items = json_obj.get("results", {}).get("items", [])
    scores = []
    for it in items:
        for alt in it.get("alternatives", []):
            conf = alt.get("confidence")
            if conf is not None:
                try:
                    scores.append(float(conf))
                except Exception:
                    pass
    if not scores:
        return {"avg": None, "p10": None, "n": 0}
    scores.sort()
    n = len(scores)
    p10_idx = max(0, int(0.1 * (n - 1)))
    return {"avg": sum(scores) / n, "p10": scores[p10_idx], "n": n}

