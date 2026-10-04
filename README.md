# Career Command Center — Backend API

The backend service powering the Career Command Center, an AI-driven interview preparation suite. Built with FastAPI and CrewAI multi-agent orchestration.

**Frontend Repository**: [career-command-center](https://github.com/Deepak-DPK/career-command-center)

---

## Features

- **Multi-Agent CrewAI Pipeline** — Four specialized AI agents collaborate sequentially to analyze resumes and generate career strategy packages.
- **Hybrid ATS Scoring** — Python-based keyword matching with weighted technical keyword analysis for accurate, dynamic ATS scores.
- **RAG-Powered AI Chat** — Resume chunks embedded via Gemini and stored in Supabase pgvector for hybrid similarity + full-text search retrieval.
- **PDF Resume Parsing** — Extracts and processes text from uploaded PDF resumes.
- **Smart Query Router** — Fast-bypasses the LLM for simple greetings and common messages.
- **Session History Management** — Summarizes long conversation histories and maintains sliding context windows.

---

## AI Agents

| Agent | Role | Responsibility |
|-------|------|----------------|
| **Sleuth** | Resume Intelligence Specialist | Compares resume vs job description to detect skill gaps and missing keywords |
| **Recruiter** | Hiring Manager Simulator | Generates tailored technical, behavioral, and scenario interview questions |
| **Challenger** | Stress Interview Specialist | Creates tough pushback questions and salary negotiation scenarios |
| **Coach** | Career Strategy Coach | Synthesizes all insights into a comprehensive interview battle plan |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI, Python 3.10+ |
| AI Orchestration | CrewAI 1.15 |
| LLM Provider | Google Gemini (primary), Groq (fallback) |
| LLM Routing | LiteLLM |
| Embeddings | Gemini text-embedding-004 |
| Database | Supabase (PostgreSQL + pgvector) |
| PDF Parsing | pypdf |
| Hosting | Render |

---

## Project Structure

```
src/career_command_center/
├── api.py              # FastAPI routes (/generate-prep-kit, /chat)
├── crew.py             # CrewAI agent and task definitions
├── main.py             # CLI entry points (run, train, api)
├── config/
│   ├── agents.yaml     # Agent roles, goals, and backstories
│   └── tasks.yaml      # Task prompts and expected outputs
├── tools/
│   └── custom_tool.py  # Custom CrewAI tools
└── __init__.py
```

---

## API Endpoints

### `POST /generate-prep-kit`

Generates a complete career preparation kit.

**Request**: `multipart/form-data`
- `resume` (file) — PDF resume file
- `job_description` (string) — Target job description
- `user_id` (string, optional) — User ID for database storage

**Response**: JSON object containing skill_gaps, ats_analysis, questions, pushback_questions, salary_negotiation, coach_report, and outreach_assets.

### `POST /chat`

Interactive AI career mentor chat with RAG context.

**Request**: JSON
- `message` (string) — User message
- `history` (array) — Chat history
- `resume_text` (string) — Resume context
- `job_description` (string) — Job description context
- `resume_id` (string, optional) — For RAG vector retrieval
- `user_id` (string) — Required (premium feature)

**Response**: `{ "reply": "..." }`

---

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
git clone https://github.com/Deepak-DPK/career-command-center-backend.git
cd career-command-center-backend
pip install -r requirements.txt
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key (powers agents, chat, and embeddings) |
| `GROQ_API_KEY` | Optional | Groq API key (fallback if Gemini is not set) |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Supabase service role key |
| `MODEL_NAME` | Optional | Override default LLM model (default: `gemini/gemini-2.0-flash`) |
| `CHAT_MODEL_NAME` | Optional | Override chat model (default: `gemini/gemini-2.0-flash`) |

### Run Locally

```bash
PYTHONPATH=src python -m uvicorn career_command_center.api:app --host 0.0.0.0 --port 8000 --reload
```

### Deploy on Render

| Setting | Value |
|---------|-------|
| Build Command | `pip install -r requirements.txt` |
| Start Command | `PYTHONPATH=src python -m uvicorn career_command_center.api:app --host 0.0.0.0 --port $PORT` |

---

## License

This project is open source and available under the [MIT License](LICENSE).
