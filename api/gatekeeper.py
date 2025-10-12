def is_sufficient(text: str, min_lines: int = 8, min_tokens: int = 60) -> tuple[bool, str]:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    tokens = text.split()
    if len(lines) < min_lines:
        return False, f"Too few lines: {len(lines)} < {min_lines}"
    if len(tokens) < min_tokens:
        return False, f"Too few tokens: {len(tokens)} < {min_tokens}"
    return True, "OK"

