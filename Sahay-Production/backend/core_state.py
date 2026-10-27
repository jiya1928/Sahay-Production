from operator import add
from typing import Annotated, Any, TypedDict


class MentalHealthState(TypedDict, total=False):
    user_id: str
    phq9: list[int]
    gad7: list[int]
    journal: str
    language: str

    phq9_total: int
    gad7_total: int
    phq9_level: str
    gad7_level: str

    emotion: dict[str, Any]
    final_score: float
    risk_level: str
    is_crisis: bool
    safety_followup_required: bool

    counsellor_id: str
    case_id: str

    # Reducers preserve entries from each graph node.
    messages: Annotated[list[Any], add]
    audit_log: Annotated[list[str], add]
