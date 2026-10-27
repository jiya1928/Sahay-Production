import logging
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

try:
    from .core_state import MentalHealthState
    from .scoring import (
        calculate_phq9,
        calculate_gad7,
        final_wellness_score,
    )
except ImportError:
    from core_state import MentalHealthState
    from scoring import (
        calculate_phq9,
        calculate_gad7,
        final_wellness_score,
    )

# ============================================================
# CONFIGURATION - ONLY MODEL NAME CHANGED, REST SAME
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=False)

logger = logging.getLogger("sahay.agents")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b",  # <-- FIX: was llama-3.3-70b-versatile which is 404 now
)

if not GROQ_API_KEY:
    logger.warning(
        "GROQ_API_KEY is missing. AI responses will fail until "
        "backend/.env is configured."
    )

# Same initialization, same params
llm = ChatGroq(
    model=GROQ_MODEL,
    temperature=0.4,
    api_key=GROQ_API_KEY or "missing-api-key",
    timeout=45,
    max_retries=2,
)

# ============================================================
# SAFETY HELPERS - SAME
# ============================================================
CRISIS_PHRASES = (
    "kill myself", "want to kill myself", "suicide",
    "end my life", "want to die", "going to hurt myself",
    "self harm", "self-harm",
)

def contains_crisis_signal(text):
    normalized = (text or "").lower()
    return any(phrase in normalized for phrase in CRISIS_PHRASES)

def detect_emotion(text):
    text = (text or "").lower()
    categories = {
        "anxious": ("anxious", "anxiety", "nervous", "panic", "worried", "overthinking", "stress",),
        "sad": ("sad", "lonely", "hopeless", "crying", "unhappy", "depressed", "low",),
        "angry": ("angry", "furious", "irritated", "frustrated",),
        "positive": ("happy", "hopeful", "grateful", "excited", "better", "good",),
    }
    for label, keywords in categories.items():
        if any(word in text for word in keywords):
            return {"label": label, "score": None, "method": "keyword_heuristic"}
    return {"label": "neutral_or_uncertain", "score": None, "method": "keyword_heuristic"}

# ============================================================
# AGENT 1: CRISIS GUARD - SAME
# ============================================================
def crisis_guard_node(state: MentalHealthState):
    journal = state.get("journal", "")
    is_crisis = contains_crisis_signal(journal)
    return {"is_crisis": is_crisis, "audit_log": [f"crisis_guard: urgent_language_signal={is_crisis}"]}

# ============================================================
# AGENT 2: CLINICAL SCORER - SAME
# ============================================================
def clinical_scorer_node(state: MentalHealthState):
    phq_answers = state.get("phq9", [0] * 9)
    gad_answers = state.get("gad7", [0] * 7)
    phq_total, phq_level, _ = calculate_phq9(phq_answers)
    gad_total, gad_level, _ = calculate_gad7(gad_answers)
    emotion = detect_emotion(state.get("journal", ""))
    sentiment_scores = {"positive": 75, "neutral_or_uncertain": 50, "anxious": 35, "sad": 30, "angry": 35}
    sentiment_score = sentiment_scores.get(emotion["label"], 50)
    wellness_score = final_wellness_score(phq_total, gad_total, sentiment_score)
    return {
        "phq9_total": phq_total, "gad7_total": gad_total,
        "emotion": emotion, "final_score": wellness_score,
        "audit_log": [f"clinical_scorer: PHQ9={phq_total} ({phq_level}), GAD7={gad_total} ({gad_level}); results are screening indicators"]
    }

# ============================================================
# AGENT 3: RISK STRATIFIER - SAME
# ============================================================
def risk_stratifier_node(state: MentalHealthState):
    phq_total = state.get("phq9_total", 0)
    gad_total = state.get("gad7_total", 0)
    wellness = state.get("final_score", 50)
    is_crisis = state.get("is_crisis", False)
    if is_crisis: risk = "crisis"
    elif phq_total >= 20 or gad_total >= 15 or wellness < 35: risk = "high"
    elif phq_total >= 10 or gad_total >= 10 or wellness < 60: risk = "moderate"
    else: risk = "low"
    return {"risk_level": risk, "case_id": str(uuid.uuid4()), "audit_log": [f"risk_stratifier: screening_category={risk}"]}

# ============================================================
# AGENT 4: EMPATHY AND COPING GENERATOR - SAME
# ============================================================
def empathy_node(state: MentalHealthState):
    language = state.get("language", "en")
    language_instruction = "Respond in natural Hindi or Hinglish." if language == "hi" else "Respond in clear, natural English."
    if state.get("is_crisis"):
        safety_instruction = "The journal contains language that may indicate a safety concern. Respond calmly... For India, emergency services can be reached at 112 and Tele-MANAS at 14416."
    else:
        safety_instruction = "Offer two or three manageable, optional coping ideas... Ask one relevant follow-up question if appropriate."
    prompt = f"""You are the supportive AI assistant for SAHAY.\n{language_instruction}\nScreening: PHQ-9 {state.get('phq9_total')}/27, GAD-7 {state.get('gad7_total')}/21, Category: {state.get('risk_level')}\nJournal: {state.get('journal', '')[:3000]}\n{safety_instruction}\nRules: Do not claim to be human therapist, do not diagnose, do not prescribe, keep concise."""
    response = llm.invoke([SystemMessage(content="You provide supportive, non-diagnostic mental wellbeing guidance."), HumanMessage(content=prompt)])
    return {"messages": [response], "audit_log": ["empathy_agent: guidance_generated"]}

# ============================================================
# AGENT 5: CARE COORDINATOR - SAME
# ============================================================
def care_coordinator_node(state: MentalHealthState):
    risk = state.get("risk_level", "moderate")
    routing_map = {"low": "self_help_and_optional_counsellor", "moderate": "counsellor_review_recommended", "high": "priority_human_review_recommended", "crisis": "urgent_human_support_recommended"}
    assigned = routing_map.get(risk, "counsellor_review_recommended")
    return {"counsellor_id": assigned, "audit_log": [f"care_coordinator: routing_recommendation={assigned}; no real counsellor has been automatically contacted"]}

# ============================================================
# BUILD GRAPH - SAME
# ============================================================
def build_graph():
    workflow = StateGraph(MentalHealthState)
    workflow.add_node("crisis_guard", crisis_guard_node)
    workflow.add_node("clinical_scorer", clinical_scorer_node)
    workflow.add_node("risk_stratifier", risk_stratifier_node)
    workflow.add_node("empathy", empathy_node)
    workflow.add_node("care_coordinator", care_coordinator_node)
    workflow.add_edge(START, "crisis_guard")
    workflow.add_edge("crisis_guard", "clinical_scorer")
    workflow.add_edge("clinical_scorer", "risk_stratifier")
    workflow.add_edge("risk_stratifier", "empathy")
    workflow.add_edge("empathy", "care_coordinator")
    workflow.add_edge("care_coordinator", END)
    return workflow.compile()

mental_health_multiagent = build_graph()