import os
import html

import requests
import streamlit as st
import plotly.graph_objects as go


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="SAHAY | AI Mental Wellbeing",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE = os.getenv(
    "SAHAY_API_BASE",
    "http://127.0.0.1:8000",
).rstrip("/")

ASSESS_URL = f"{API_BASE}/api/v1/assess"
CHAT_URL = f"{API_BASE}/api/v1/counselling/chat"
HEALTH_URL = f"{API_BASE}/health"


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "page": "Dashboard",
    "language": "en",
    "consent": False,
    "assessment_result": None,
    "chat_history": [],
    "chat_consent": False,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# STYLING
# ============================================================

st.markdown(
    """
    <style>
    @import url(
      'https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=JetBrains+Mono:wght@400;700&display=swap'
    );

    .stApp {
        background: #07080D;
        color: #E8E9F0;
    }

    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif;
        color: #F5F6FF;
    }

    p, label, li {
        color: #D6D8E5;
    }

    [data-testid="stSidebar"] {
        background: #0B0D17;
        border-right: 1px solid #24253A;
    }

    .topbar {
        padding: 20px 24px;
        margin-bottom: 24px;
        border: 1px solid #282542;
        border-radius: 18px;
        background: linear-gradient(120deg, #15132B, #0B0D17);
    }

    .brand {
        font-family: 'JetBrains Mono', monospace;
        font-size: 21px;
        font-weight: 700;
        letter-spacing: 2px;
    }

    .green {
        color: #00FF94;
    }

    .muted {
        color: #9B9EB5;
        font-size: 13px;
    }

    .panel {
        background: #101222;
        border: 1px solid #292B45;
        border-radius: 18px;
        padding: 22px;
        margin-bottom: 16px;
    }

    .metric {
        background: #111429;
        border: 1px solid #30324D;
        border-radius: 15px;
        padding: 18px;
        text-align: center;
    }

    .metric-label {
        font-size: 12px;
        color: #A6A9C0;
        letter-spacing: 1px;
    }

    .metric-value {
        font-size: 29px;
        font-weight: 700;
        color: #00FF94;
    }

    .notice {
        background: #17192B;
        border-left: 4px solid #8B5CF6;
        padding: 14px 17px;
        border-radius: 8px;
        margin: 12px 0;
    }

    .stButton > button {
        border-radius: 12px;
        min-height: 43px;
        font-weight: 600;
        border: 1px solid #51417E;
    }

    .stTextArea textarea,
    .stTextInput input {
        background: #101222;
        color: white;
        border-radius: 10px;
        border: 1px solid #393B58;
    }

    [data-testid="stChatMessage"] {
        background: #111429;
        border: 1px solid #292B45;
        border-radius: 14px;
        padding: 12px;
    }

    div[data-testid="stProgressBar"] > div > div {
        background: #00FF94;
    }

    #MainMenu, footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="topbar">
        <div class="brand">
            SAHAY // <span class="green">NEURAL OS</span>
        </div>
        <div class="muted">
            AI MENTAL WELLBEING & SUPPORT
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

with st.sidebar:
    st.markdown("## 🧠 SAHAY")
    st.caption("Mental Wellbeing Support")

    page_options = [
        "Dashboard",
        "Mental Health Assessment",
        "AI Counselling Room",
        "Self-Help Library",
        "About & Support",
    ]

    selected_page = st.radio(
        "NAVIGATION",
        page_options,
        index=page_options.index(st.session_state.page),
        key="navigation",
    )

    st.session_state.page = selected_page

    st.divider()

    st.markdown("### Preferences")

    st.session_state.language = st.selectbox(
        "AI response language",
        ["en", "hi"],
        format_func=lambda x: {
            "en": "English",
            "hi": "Hindi / Hinglish",
        }[x],
        index=0 if st.session_state.language == "en" else 1,
    )

    if st.button("Check backend connection", use_container_width=True):
        try:
            response = requests.get(HEALTH_URL, timeout=5)

            if response.ok:
                st.success("Backend is online.")
            else:
                st.error(f"Backend returned HTTP {response.status_code}.")

        except requests.RequestException:
            st.error(
                "Backend is unreachable. Start FastAPI on port 8000."
            )

    st.divider()

    st.caption(
        "SAHAY is an AI support tool, not a replacement for "
        "a qualified mental health professional."
    )


# ============================================================
# REUSABLE FUNCTIONS
# ============================================================

def metric_card(label, value):
    st.markdown(
        f"""
        <div class="metric">
            <div class="metric-label">{html.escape(str(label))}</div>
            <div class="metric-value">{html.escape(str(value))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_support_information():
    st.markdown("### Support options")

    st.markdown(
        """
        - **India emergency services:** 112
        - **Tele-MANAS mental health support:** 14416

        If you may be in immediate danger, contact emergency services
        or a trusted person who can help you in person.
        """
    )


def render_assessment_result(data):
    st.markdown("---")
    st.subheader("Your assessment results")

    risk = str(data.get("risk_level", "unknown")).lower()

    risk_labels = {
        "low": "Lower screening concern",
        "moderate": "Moderate screening concern",
        "high": "Higher screening concern",
        "needs_safety_followup": "Safety follow-up recommended",
        "crisis": "Urgent safety follow-up",
    }

    st.markdown(
        f"**Case reference:** `{html.escape(str(data.get('case_id', 'N/A')))}`"
    )

    st.markdown(
        f"**Screening category:** {risk_labels.get(risk, 'Review recommended')}"
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        metric_card(
            "PHQ-9",
            f"{data.get('phq9_total', 0)}/27",
        )

    with c2:
        metric_card(
            "GAD-7",
            f"{data.get('gad7_total', 0)}/21",
        )

    with c3:
        metric_card(
            "WELLNESS INDICATOR",
            f"{data.get('final_score', 'N/A')}/100",
        )

    st.markdown("### Supportive guidance")

    guidance = data.get(
        "ai_guidance",
        "No guidance was returned.",
    )

    st.write(guidance)

    st.caption(
        "Screening results do not establish a diagnosis. "
        "The wellness indicator is not a validated clinical measure."
    )

    if data.get("safety_followup_required") or data.get("is_crisis"):
        st.warning(
            "Please seek appropriate human support. "
            "This application does not automatically contact a counsellor."
        )
        show_support_information()

    if st.button("Open AI Counselling Room", use_container_width=True):
        st.session_state.page = "AI Counselling Room"
        st.rerun()


# ============================================================
# DASHBOARD
# ============================================================

if st.session_state.page == "Dashboard":

    st.title("Your Mental Wellbeing Dashboard")

    st.write(
        "A private space in which to reflect on your feelings, "
        "complete wellbeing screenings and explore coping strategies."
    )

    left, right = st.columns([1.2, 1])

    with left:
        st.markdown(
            """
            <div class="panel">
                <h3>AI Counselling Room</h3>
                <p>
                    Talk with an AI support assistant, explore your
                    feelings and practise optional coping exercises.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Enter Counselling Room", use_container_width=True):
            st.session_state.page = "AI Counselling Room"
            st.rerun()

        st.markdown(
            """
            <div class="panel">
                <h3>Mental Health Assessment</h3>
                <p>
                    Complete PHQ-9 and GAD-7 screening questionnaires.
                    Review the results and consider appropriate support.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Start Assessment", use_container_width=True):
            st.session_state.page = "Mental Health Assessment"
            st.rerun()

    with right:
        st.markdown("### Your latest assessment")

        result = st.session_state.assessment_result

        if result:
            metric_card(
                "PHQ-9",
                f"{result.get('phq9_total', 0)}/27",
            )
            st.write("")

            metric_card(
                "GAD-7",
                f"{result.get('gad7_total', 0)}/21",
            )

            st.write("")

            if st.button("View complete results", use_container_width=True):
                render_assessment_result(result)
        else:
            st.info(
                "You have not completed an assessment in this session."
            )

    st.markdown("---")
    st.markdown("### Quick wellbeing exercises")

    a, b, c = st.columns(3)

    with a:
        st.markdown("**Grounding**")
        st.caption("Notice your surroundings and reconnect with the present.")

    with b:
        st.markdown("**Journaling**")
        st.caption("Write down what you feel without judging yourself.")

    with c:
        st.markdown("**Small steps**")
        st.caption("Choose one manageable activity for today.")


# ============================================================
# MENTAL HEALTH ASSESSMENT
# ============================================================

elif st.session_state.page == "Mental Health Assessment":

    st.title("Mental Health Assessment")

    st.markdown(
        """
        Answer the questions based on your experiences over the **last
        two weeks**. These questionnaires are screening tools, not
        diagnostic tests.
        """
    )

    st.warning(
        "If you need urgent help, do not wait for an assessment result. "
        "Contact a trusted person or local emergency services."
    )

    phq_questions = [
        "Little interest or pleasure in doing things",
        "Feeling down, depressed, or hopeless",
        "Trouble falling or staying asleep, or sleeping too much",
        "Feeling tired or having little energy",
        "Poor appetite or overeating",
        "Feeling bad about yourself, or that you are a failure",
        "Trouble concentrating on things",
        "Moving or speaking slowly, or being unusually restless",
        "Thoughts that you would be better off dead or of hurting yourself",
    ]

    gad_questions = [
        "Feeling nervous, anxious, or on edge",
        "Not being able to stop or control worrying",
        "Worrying too much about different things",
        "Trouble relaxing",
        "Being so restless that it is hard to sit still",
        "Becoming easily annoyed or irritable",
        "Feeling afraid as if something awful might happen",
    ]

    answer_options = {
        "Not at all": 0,
        "Several days": 1,
        "More than half the days": 2,
        "Nearly every day": 3,
    }

    with st.form("mental_health_assessment"):

        st.subheader("PHQ-9 — Depression Screening")

        phq = []

        for i, question in enumerate(phq_questions):
            answer = st.radio(
                f"{i + 1}. {question}",
                options=list(answer_options.keys()),
                index=0,
                key=f"phq_answer_{i}",
                horizontal=False,
            )
            phq.append(answer_options[answer])

        st.divider()

        st.subheader("GAD-7 — Anxiety Screening")

        gad = []

        for i, question in enumerate(gad_questions):
            answer = st.radio(
                f"{i + 1}. {question}",
                options=list(answer_options.keys()),
                index=0,
                key=f"gad_answer_{i}",
                horizontal=False,
            )
            gad.append(answer_options[answer])

        st.divider()

        journal = st.text_area(
            "Optional: Is there anything else you want to share?",
            max_chars=5000,
            placeholder=(
                "Describe what has been difficult lately, "
                "if you feel comfortable sharing."
            ),
            height=140,
        )

        assessment_consent = st.checkbox(
            "I understand that this is an AI-assisted screening tool, "
            "not a diagnosis, and I consent to sending my answers "
            "to the configured backend for processing.",
            value=False,
        )

        submitted = st.form_submit_button(
            "Submit Assessment",
            use_container_width=True,
        )

    if submitted:

        if not assessment_consent:
            st.error("Please provide consent before submitting.")

        else:
            payload = {
                "user_id": "streamlit_session_user",
                "phq9": phq,
                "gad7": gad,
                "journal": journal,
                "consent": True,
                "language": st.session_state.language,
            }

            try:
                with st.spinner("Processing your assessment..."):
                    response = requests.post(
                        ASSESS_URL,
                        json=payload,
                        timeout=90,
                    )

                if response.ok:
                    data = response.json()
                    st.session_state.assessment_result = data
                    st.success("Assessment completed.")
                    render_assessment_result(data)

                else:
                    st.error(
                        f"Assessment failed ({response.status_code}): "
                        f"{response.text[:500]}"
                    )

            except requests.RequestException as exc:
                st.error(
                    f"Could not connect to the backend: {exc}"
                )

    if st.session_state.assessment_result and not submitted:
        render_assessment_result(
            st.session_state.assessment_result
        )


# ============================================================
# AI COUNSELLING ROOM
# ============================================================

elif st.session_state.page == "AI Counselling Room":

    st.title("AI Counselling Room")

    st.markdown(
        """
        <div class="panel">
            <h3>SAHAY AI Support Assistant</h3>
            <p>
                Share what is on your mind at your own pace.
                The AI can listen, reflect on what you share,
                and suggest optional coping strategies.
            </p>
            <p class="muted">
                This is an AI assistant, not a human counsellor
                or a substitute for professional treatment.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.session_state.chat_consent = st.checkbox(
        "I consent to sending my chat messages to the configured "
        "AI provider for generating responses.",
        value=st.session_state.chat_consent,
        key="chat_consent_checkbox",
    )

    if not st.session_state.chat_consent:
        st.info(
            "Consent is required before using the AI counselling chat."
        )

    col1, col2 = st.columns([3, 1])

    with col1:
        st.caption(
            "Your chat history is held in this Streamlit session. "
            "It is not a secure medical record."
        )

    with col2:
        if st.button("Clear chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if not st.session_state.chat_history:
        st.markdown("### Where would you like to start?")

        prompts = [
            "I have been feeling anxious lately.",
            "I feel low and want to talk about it.",
            "Help me practise a grounding exercise.",
        ]

        for i, prompt in enumerate(prompts):
            if st.button(prompt, key=f"starter_{i}"):
                st.session_state.pending_chat_prompt = prompt
                st.rerun()

    user_prompt = st.chat_input(
        "Write what you are feeling..."
    )

    if not user_prompt:
        user_prompt = st.session_state.pop(
            "pending_chat_prompt",
            None,
        )

    if user_prompt:

        if not st.session_state.chat_consent:
            st.warning(
                "Please consent to AI processing before sending a message."
            )

        else:
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_prompt,
            })

            with st.chat_message("user"):
                st.markdown(user_prompt)

            payload = {
                "messages": [
                    {
                        "role": message["role"],
                        "content": message["content"],
                    }
                    for message in st.session_state.chat_history[-20:]
                ],
                "language": st.session_state.language,
                "consent": True,
            }

            try:
                with st.chat_message("assistant"):
                    with st.spinner("SAHAY is preparing a response..."):
                        response = requests.post(
                            CHAT_URL,
                            json=payload,
                            timeout=90,
                        )

                    if response.ok:
                        data = response.json()
                        reply = data.get(
                            "reply",
                            "No response was returned.",
                        )

                        st.markdown(reply)

                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": reply,
                        })

                        if data.get("safety_followup"):
                            st.warning(
                                "Human support is recommended. "
                                "The application has not contacted "
                                "emergency services or a counsellor."
                            )
                            show_support_information()

                    else:
                        st.error(
                            f"Chat error {response.status_code}: "
                            f"{response.text[:400]}"
                        )

                        # Remove the unanswered user message so it
                        # is not resent as if a response existed.
                        st.session_state.chat_history.pop()

            except requests.RequestException:
                st.error(
                    "The counselling service is unavailable. "
                    "Check that FastAPI is running and your Groq "
                    "configuration is correct."
                )

                st.session_state.chat_history.pop()


# ============================================================
# SELF-HELP LIBRARY
# ============================================================

elif st.session_state.page == "Self-Help Library":

    st.title("Self-Help Library")

    st.write(
        "These exercises may help with everyday stress. "
        "Choose what feels comfortable and stop if an exercise "
        "makes you feel worse."
    )

    with st.expander("1. Grounding exercise", expanded=True):
        st.markdown(
            """
            1. Notice five things you can see.
            2. Notice four things you can physically feel.
            3. Identify three sounds.
            4. Notice two smells, if any.
            5. Notice one taste, if any.

            You can skip any step that feels uncomfortable.
            """
        )

    with st.expander("2. Slow, comfortable breathing"):
        st.markdown(
            """
            Sit comfortably and breathe gently without forcing
            deep breaths. Let your exhalation be comfortable.
            Continue for a short time, then return to normal breathing.

            Stop if you feel dizzy or uncomfortable.
            """
        )

    with st.expander("3. CBT-inspired thought reflection"):
        st.markdown(
            """
            Write down:

            - What happened?
            - What thought came to mind?
            - What emotion did I notice?
            - What facts support this thought?
            - Is there another reasonable explanation?
            - What is one helpful next step?

            This is a reflection exercise, not a substitute for CBT
            delivered by a qualified professional.
            """
        )

    with st.expander("4. Journaling"):
        st.markdown(
            """
            Try these prompts:

            - What has been difficult today?
            - What would I say to someone in a similar situation?
            - What is one thing I need right now?
            - Who might be able to support me?
            """
        )

        journal_note = st.text_area(
            "Write a private reflection in this session",
            key="self_help_journal",
            height=140,
        )

        st.caption(
            "This note remains in the current Streamlit session. "
            "Do not use this field to store sensitive medical records."
        )

    with st.expander("5. Practical problem-solving"):
        st.markdown(
            """
            1. Describe one problem clearly.
            2. List small actions that could help.
            3. Choose one realistic action.
            4. Decide when to try it.
            5. Review what worked and what did not.
            """
        )

    st.info(
        "If symptoms persist, interfere with daily life, or become "
        "difficult to manage, consider speaking with a qualified "
        "mental health professional."
    )


# ============================================================
# ABOUT AND SUPPORT
# ============================================================

elif st.session_state.page == "About & Support":

    st.title("About SAHAY")

    st.markdown(
        """
        SAHAY is an AI-assisted mental wellbeing application designed
        to provide screening information, supportive conversation
        and self-help exercises.
        """
    )

    st.subheader("System components")

    st.markdown(
        """
        - **Crisis Guard:** preliminary safety-signal detection.
        - **Clinical Scorer:** PHQ-9 and GAD-7 score calculation.
        - **Risk Stratifier:** preliminary routing based on configured rules.
        - **Empathy Agent:** AI-generated supportive guidance.
        - **Care Coordinator:** suggested next-step routing.
        """
    )

    st.warning(
        "The agent routing is not a clinically validated risk assessment. "
        "It does not automatically alert or contact a real counsellor."
    )

    show_support_information()

    st.markdown("---")

    st.markdown(
        """
        **Privacy:** Do not enter identifying or highly sensitive patient
        information into an unreviewed development deployment.

        **Clinical use:** A qualified professional should review screening
        interpretation, crisis procedures and any proposed clinical workflow.
        """
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "SAHAY AI Mental Wellbeing | Educational and supportive use only. "
    "Not a diagnosis, emergency service, or replacement for professional care."
)
