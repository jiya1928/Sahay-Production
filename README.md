# SAHAY — AI-Powered Mental Health Support System

> **Empathy + Intelligence + Action** — A multi-agent mental wellness platform powered by `openai/gpt-oss-20b` via Groq.

[![Python](https://img.shields.io/badge/Python-3.11-blue)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)]()
[![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-red)]()
[![Groq](https://img.shields.io/badge/Groq-gpt--oss--20b-orange)]()
[![License](https://img.shields.io/badge/License-MIT-yellow)]()

SAHAY is an AI-driven mental health companion that listens, assesses, and supports. Built with 5 specialized AI agents for comprehensive mental wellness analysis.

### 🔗 Live Demo
- Frontend: Streamlit App
- Backend: FastAPI
- Repo: https://github.com/jiya1928/Sahay-Production

---

### ✨ Key Features

- **5-Agent Architecture**
    - `Listener Agent` — Empathetic conversation
    - `Assessor Agent` — PHQ-9 / GAD-7 based scoring
    - `Therapist Agent` — CBT-based coping strategies
    - `Resource Agent` — Personalized wellness resources
    - `Safety Agent` — Crisis detection & escalation

- **Core Capabilities**
    - Real-time mental health risk scoring (`scoring.py`)
    - Persistent emotional state tracking (`core_state.py`)
    - Powered by `openai/gpt-oss-20b` — Fast, private, free via Groq
    - FastAPI backend + Streamlit frontend
    - Safety-first design

---

### 🏗️ Architecture
Sahay-Production/
├── backend/
│   ├── main.py          # FastAPI app, endpoints
│   ├── agents.py        # 5 AI agents with gpt-oss-20b
│   ├── core_state.py    # User emotional state manager
│   ├── scoring.py       # PHQ-9/GAD-7 scoring logic
│   ├── requirements.txt
│   └── .env.example     # Env template
└── frontend/
    └── app.py           # Streamlit UIjavascript
---

### 🚀 Quick Start

**1. Clone**
```bash
git clone https://github.com/jiya1928/Sahay-Production.git
cd Sahay-Production2. Backend Setupbashcd backend
python -m venv .venv
# Windows: .venv\Scripts\activate | Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt3. Environment Variablesbashcp .env.example .env
# Edit .env and add your GROQ_API_KEYGet key from: https://console.groq.com/keys
.env file:javascriptGROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=openai/gpt-oss-20b4. Run Backendbashuvicorn main:app --reload --port 80005. Run Frontendbashcd ../frontend
streamlit run app.pyOpen: http://localhost:8501
🔧 Tech Stack
LLM: Groq — openai/gpt-oss-20b (Open-source, 20B params)Backend: FastAPI, Python, PydanticFrontend: StreamlitScoring: Custom PHQ-9 / GAD-7 implementationDeployment Ready: Docker-friendly, .env based config🛡️ Safety & Ethics
Not a replacement for professional medical adviceSafety agent detects self-harm keywords and provides helpline infoAll user data stored locally in session stateNo conversation logging without consentIndia Helplines:
Kiran: 1800-599-0019iCall: 9152987821📸 Screenshots
Add your screenshots here — UI, agent response, scoring dashboard🤝 Contributing
PRs welcome! Please follow conventional commits.
📄 License
MIT License — Built by Jiya @ Sahay Team
🙏 Acknowledgements
Groq for free gpt-oss-20b inferenceOpenAI for open-weight modelStreamlit & FastAPI communitiesjavascript
**Push kar:**

```powershell
git add README.md
git commit -m "docs: add professional README for internship"
git push origin main
