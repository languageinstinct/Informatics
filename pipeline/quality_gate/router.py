def route(score_result: dict) -> str:
    """Determine routing path based on gate score."""
    if score_result.get("status") == "GOOD":
        return "STANDARD_PATH"
    return "EXCEPTION_PATH"
