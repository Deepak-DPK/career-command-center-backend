# Career Command Center (CCC)

The **Career Command Center (CCC)** is an advanced AI-powered career optimization and interview preparation intelligence suite. Its goal is to empower job seekers by providing real-time, personalized analysis of their resumes against target job descriptions, simulating high-pressure interviews, scripting salary negotiation frameworks, and offering an interactive AI Career Mentor.

---

## 🌟 Core Purpose & Mission

Modern technical hiring is complex, requiring candidates to pass automated ATS screening, align with precise job criteria, answer tough behavioral questions, navigate salary expectations, and demonstrate subject-matter expertise. 

The Career Command Center acts as a strategic briefing room that translates a candidate's resume and target job descriptions into a complete prep dossier. It helps candidates identify their weaknesses, optimize their profile, prepare for stress scenarios, and strategize their compensation.

---

## 🛠️ Key Features

The dashboard provides a suite of interactive, specialized resources divided into core panels:

1. **Skill Gaps Analysis**: Scans the candidate's resume against the job description to pinpoint technical, domain, and soft skill discrepancies.
2. **ATS Match & Optimization**: Evaluates the resume using automated screening criteria, calculates an ATS match score, identifies missing keywords, and lists improvement suggestions.
3. **Core Interview Simulator**: Generates role-specific questions divided into technical skills, behavioral performance (STAR method), and situational day-one situational situations.
4. **Tough Scenarios (Stress Questions)**: Anticipates difficult pushback questions targeting gaps in work history, lack of specific framework experience, or resume weak points.
5. **Salary Negotiation Talk Track**: Formulates market-aligned target ranges, lists negotiation tips, and builds scripts to handle compensation trap questions.
6. **Professional Outreach Templates**: Scripts cold emails, LinkedIn connection messages, and post-interview thank you notes tailored to the target role.
7. **Executive Coach Strategy**: Synthesizes the overall assessment into an interview battle plan, detailed roadmaps, and confidence-building advice.
8. **Interactive AI Career Mentor**: A real-time conversational mentor that references the uploaded resume, target job details, and preparation files to answer strategy queries.

---

## 💻 Tech Stack & Integrations

The system is built on a modern, decoupled stack:

### Frontend
- **React & TypeScript**: Powers the responsive single-page dashboard.
- **TailwindCSS**: Delivers a premium dark-themed SaaS aesthetic with custom glassmorphism layers, glow indicators, and animations.
- **Framer Motion**: Handles transitions, tab switching, and fade-in states.

### Backend
- **FastAPI**: Serves high-speed API routes, handles file uploads, and directs chatbot requests.
- **CrewAI**: Manages a collaborative multi-agent pipeline where AI agents exchange context to execute sequential tasks.
- **LiteLLM**: Handles model routing, enabling support for Google Gemini models and automatic fallback to Groq Llama models during API interruptions.

### Infrastructure & Data Layer
- **Supabase**: Handles database storage and vector search. When users log in, resumes are chunked and mapped to vector embeddings for similarity-based chat retrieval.
- **Firebase Auth**: Manages secure user authentication. The system supports a Sandbox mode that runs locally using session cache when Firebase is not active.
