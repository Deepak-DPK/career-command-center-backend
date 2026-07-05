# Career Command Center (CCC)

Welcome to the **Career Command Center (CCC)** — a modern AI-powered interview preparation suite designed to align your resume with target job descriptions, calculate ATS match metrics, simulate interview pushback scenarios, compile tailored salary negotiation templates, and host an interactive, RAG-enabled AI Career Mentor.

---

## 🚀 Project Overview

The Career Command Center consists of a dual-repo setup:
1. **Frontend**: A React + TypeScript + TailwindCSS single page dashboard hosting command controls, resume uploads, and preparation kit display panels.
2. **Backend**: A FastAPI server driving a CrewAI multi-agent sequential workflow, handling Supabase RAG storage/retrieval, and serving an interactive conversational mentor.

---

## 📂 Project Repository Structures

### 1. Backend: `career-command-center-backend`
```
career-command-center-backend/
├── src/career_command_center/
│   ├── config/
│   │   ├── agents.yaml       # CrewAI Agent definitions (Sleuth, Recruiter, Challenger, Coach)
│   │   └── tasks.yaml        # CrewAI Task definitions (Analysis, Core/Pushback questions, Coach Report)
│   ├── api.py                # FastAPI routes, DB transactions, hybrid search & Groq/Gemini LLM fallbacks
│   ├── crew.py               # CrewAI class orchestrating the multi-agent execution pipeline
│   └── main.py               # Entrypoint script for Uvicorn or CLI runs
├── .env.example              # Template for keys (Gemini, Groq, Supabase, Firebase)
├── pyproject.toml            # Poetry/UV package manager configuration
├── requirements.txt          # Python dependencies
└── render.yaml               # Render Cloud service blueprints
```

### 2. Frontend: `career-command-center`
```
career-command-center/
├── src/
│   ├── components/           # Reusable UI cards, nav bars, Accordions, & Chat panels
│   ├── services/
│   │   └── api.ts            # Axios configuration interfacing the backend endpoints
│   ├── types/
│   │   └── index.ts          # Core TypeScript schema declarations
│   ├── App.tsx               # Main application entry point orchestrating state transitions
│   ├── index.css             # Main stylesheet injecting custom SaaS glassmorphism & glows
│   └── supabaseClient.ts     # Supabase client routing mock data locally in Sandbox guest sessions
├── .env.example              # Template for client API configurations
├── package.json              # NPM dependencies and commands
└── tsconfig.json             # TypeScript compiler settings
```

---

## 🛠️ Installation & Setup

### Prerequisites
- **Python**: `>=3.10` and `<3.14`
- **Node.js**: `>=18.x`
- **Package Managers**: [uv](https://docs.astral.sh/uv/) (highly recommended for Python) and `npm`

---

### Step 1: Backend Setup (`career-command-center-backend`)

1. Clone or navigate to the backend repository:
   ```bash
   cd career-command-center-backend
   ```
2. Create and configure your environment variables:
   ```bash
   cp .env.example .env
   ```
   Provide the following parameters:
   - `GEMINI_API_KEY`: Google AI studio credential (main pipeline).
   - `GROQ_API_KEY`: Groq Cloud credential (automatic fallback routing).
   - `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY`: Admin credentials for storage and vector RAG.
   - `FIREBASE_PROJECT_ID`: Authentication validator.

3. Install dependencies and sync via `uv`:
   ```bash
   uv sync
   ```
   *(Alternative without uv)*:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI development server:
   ```bash
   uv run python src/career_command_center/main.py api
   ```
   The backend will launch on `http://localhost:8000`.

---

### Step 2: Frontend Setup (`career-command-center`)

1. Navigate to the frontend directory:
   ```bash
   cd ../career-command-center
   ```
2. Set up client environment configurations:
   ```bash
   cp .env.example .env
   ```
   Key parameters:
   - `VITE_API_URL`: Points to backend, e.g., `http://localhost:8000` (local) or `https://career-command-center-backend.onrender.com` (prod).
   - `VITE_FIREBASE_API_KEY` (and other Firebase properties): Required for real Google Sign-In. If omitted, the frontend automatically falls back to guest Sandbox mode.
   - `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY`: Client connection to database.

3. Install NPM dependencies:
   ```bash
   npm install
   ```

4. Start the React/Vite development server:
   ```bash
   npm run dev
   ```
   Access the dashboard in your browser at `http://localhost:5173`.

---

## 🔍 Sandbox vs Login Mode

- **Sandbox Mode (Guest)**:
  Runs if client Firebase configurations are not supplied or if you click "Launch Sandbox Mode". Session histories and resume assets are cached in local browser storage (`sessionStorage`) instead of hitting Supabase tables, skipping remote database errors.
- **Login Mode (Google Authenticated)**:
  Signs in via Firebase Auth. The backend parses real user UIDs and triggers the Supabase RAG storage pipeline, splitting, embedding, and saving candidate resumes to run intelligent matching and contextual chats.
