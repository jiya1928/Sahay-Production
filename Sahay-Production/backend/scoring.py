def _validate_scores(scores: list[int], expected_length: int, name: str) -> None:
    if len(scores) != expected_length:
        raise ValueError(f"{name} must contain exactly {expected_length} answers.")
    if any(type(score) is not int or score < 0 or score > 3 for score in scores):
        raise ValueError(f"Each {name} answer must be an integer from 0 to 3.")


def calculate_phq9(scores: list[int]) -> tuple[int, str, str]:
    _validate_scores(scores, 9, "PHQ-9")
    total = sum(scores)
    if total < 5:
        level = "minimal"
    elif total < 10:
        level = "mild"
    elif total < 15:
        level = "moderate"
    elif total < 20:
        level = "moderately severe"
    else:
        level = "severe"
    return total, level, level


def calculate_gad7(scores: list[int]) -> tuple[int, str, str]:
    _validate_scores(scores, 7, "GAD-7")
    total = sum(scores)
    if total < 5:
        level = "minimal"
    elif total < 10:
        level = "mild"
    elif total < 15:
        level = "moderate"
    else:
        level = "severe"
    return total, level, level


def final_wellness_score(
    phq9_total: int,
    gad7_total: int,
    sentiment_score: float = 50,
) -> float:
    """
    A UI-oriented composite, not a validated clinical score or diagnosis.
    Higher values indicate fewer reported symptoms in the questionnaires.
    """
    depression_part = (phq9_total / 27) * 50
    anxiety_part = (gad7_total / 21) * 50
    questionnaire_component = 100 - depression_part - anxiety_part
    score = questionnaire_component * 0.7 + sentiment_score * 0.3
    return round(max(0.0, min(100.0, score)), 1)
