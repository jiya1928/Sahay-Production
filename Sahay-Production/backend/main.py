
import logging
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

# Load backend/.env regardless of the current working directory.
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=False)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sahay.api")

try:
    from .agents import mental_health_multiagent, llm
except ImportError:
    from agents import mental_health_multiagent, llm

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


app = FastAPI(
    title="SAHAY Mental Wellbeing API",
    version="3.0.0",
    description=(
        "AI-assisted mental wellbeing screening and supportive conversation. "
        "Not a diagnostic or emergency service."
    ),
)

origins = [
    item.strip()
    for item in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:8501,http://127.0.0.1:8501",
    ).split(",")
    if item.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


class AssessmentRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    phq9: list[int] = Field(min_length=9, max_length=9)
    gad7: list[int] = Field(min_length=7, max_length=7)
    journal: str = Field(default="", max_length=5000)
    consent: bool = False
    language: Literal["en", "hi"] = "en"

    @field_validator("phq9")
    @classmethod
    def validate_phq9(cls, values):
        if any(value not in range(4) for value in values):
            raise ValueError("PHQ-9 answers must be between 0 and 3.")
        return values

    @field_validator("gad7")
    @classmethod
    def validate_gad7(cls, values):
        if any(value not in range(4) for value in values):
            raise ValueError("GAD-7 answers must be between 0 and 3.")
        return values


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=5000)


class CounsellingRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=20)
    language: Literal["en", "hi"] = "en"
    consent: bool = False


def detect_safety_followup(phq9, journal):
    """
    A preliminary safety flag, not a clinical risk assessment.
    Any nonzero PHQ-9 item 9 response merits human follow-up.
    """
    text = journal.lower()

    indicators = (
        "suicide",
        "kill myself",
        "end my life",
        "want to die",
        "self harm",
        "self-harm",
        "hurt myself",
    )

    return bool(
        (len(phq9) >= 9 and phq9[8] > 0)
        or any(term in text for term in indicators)
    )


def get_ai_text(message):
    """Extract text from a LangChain AI message safely."""
    content = getattr(message, "content", message)

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts)

    return str(content)


@app.get("/")
def root():
    return {
        "status": "SAHAY ONLINE",
        "version": "3.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "api": "available",
        "groq_key_configured": bool(os.getenv("GROQ_API_KEY")),
    }


@app.post("/api/v1/assess")
def assess(req: AssessmentRequest):
    if not req.consent:
        raise HTTPException(
            status_code=400,
            detail="Consent is required before assessment.",
        )

    try:
        safety_followup = detect_safety_followup(
            req.phq9,
            req.journal,
        )

        result = mental_health_multiagent.invoke({
            "user_id": req.user_id,
            "phq9": req.phq9,
            "gad7": req.gad7,
            "journal": req.journal,
            "messages": [],
            "audit_log": [],
        })

        messages = result.get("messages") or []
        last_message = messages[-1] if messages else None

        if last_message is not None:
            guidance = get_ai_text(last_message)
        else:
            guidance = (
                "Your screening has been calculated. "
                "Consider discussing your results with a qualified professional."
            )

        risk_level = result.get("risk_level", "unknown")
        is_crisis = bool(result.get("is_crisis", False))

        return {
            "case_id": result.get("case_id"),
            "risk_level": risk_level,
            "phq9_total": result.get("phq9_total"),
            "gad7_total": result.get("gad7_total"),
            "final_score": result.get("final_score"),
            "is_crisis": is_crisis,
            "safety_followup_required": safety_followup or is_crisis,
            "emotion": result.get("emotion"),
            "counsellor_id": result.get("counsellor_id"),
            "messages": [
                {"content": get_ai_text(message)}
                for message in messages
            ],
            "ai_guidance": guidance,
            "assigned_counsellor": result.get("counsellor_id"),
            "next_action": (
                "seek_urgent_human_support"
                if is_crisis
                else "human_followup_recommended"
                if safety_followup
                else "counsellor_review"
            ),
            "helplines": {
                "TeleMANAS": "14416",
                "Emergency": "112",
            },
            "audit": result.get("audit_log", []),
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Assessment processing failed")
        raise HTTPException(
            status_code=500,
            detail="Assessment failed. Check backend logs.",
        ) from exc


@app.post("/api/v1/counselling/chat")
def counselling_chat(req: CounsellingRequest):
    if not req.consent:
        raise HTTPException(
            status_code=400,
            detail="Consent is required before counselling chat.",
        )

    if not os.getenv("GROQ_API_KEY"):
        logger.error("GROQ_API_KEY is not configured")
        raise HTTPException(
            status_code=503,
            detail="AI counselling is not configured. Check backend/.env.",
        )

    try:
        language_instruction = (
            "Respond in natural Hindi or Hinglish."
            if req.language == "hi"
            else "Respond in clear, natural English."
        )

        system_prompt = f"""
You are SAHAY, an AI mental wellbeing support assistant.

{language_instruction}

Your responsibilities:
- Listen carefully and reflect the user's feelings without judgement.
- Ask at most one gentle, relevant follow-up question at a time.
- Offer practical, optional coping strategies when appropriate.
- You may use supportive CBT-inspired reflection, grounding,
  gentle breathing, journaling and problem-solving exercises.
- Never claim to be a human counsellor, psychiatrist or therapist.
- Do not diagnose, prescribe medication or promise confidentiality.
- Do not shame, pressure or argue with the user.
- Do not imply that a screening score proves a diagnosis.
- If the user may be in immediate danger, encourage contacting
  emergency services and a trusted person who can be physically present.
- Do not claim that you have contacted a counsellor or emergency service.
- Keep replies conversational, clear and reasonably concise.
- Do not request identifying details that are unnecessary for support.
"""

        conversation = [SystemMessage(content=system_prompt)]

        for message in req.messages:
            if message.role == "user":
                conversation.append(HumanMessage(content=message.content))
            else:
                conversation.append(AIMessage(content=message.content))

        response = llm.invoke(conversation)
        reply = get_ai_text(response).strip()

        if not reply:
            raise RuntimeError("Groq returned an empty response.")

        latest_user_message = next(
            (
                item.content.lower()
                for item in reversed(req.messages)
                if item.role == "user"
            ),
            "",
        )

        safety_terms = (
            "kill myself",
            "suicide",
            "want to die",
            "end my life",
            "self harm",
            "self-harm",
            "hurt myself",
        )

        safety_followup = any(
            term in latest_user_message
            for term in safety_terms
        )

        return {
            "reply": reply,
            "safety_followup": safety_followup,
            "helplines": {
                "TeleMANAS": "14416",
                "Emergency": "112",
            },
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Groq counselling request failed")
        raise HTTPException(
            status_code=502,
            detail="Counselling AI is temporarily unavailable. Check backend logs.",
        ) from exc
