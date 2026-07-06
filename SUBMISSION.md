# Project Submission & Hackathon Requirements Document

This document compiles the submission requirements, project summary, and framework details for the **Career Command Center (CCC)** project.

---

## 📄 Project Summary (164 Words)

**Career Command Center** is a full-stack platform for job seekers to optimize resumes and prep for interviews. It orchestrates a 4-agent CrewAI pipeline:
1. **Sleuth** (*Resume Intelligence Specialist*): Scans resumes against job descriptions for technical gaps using customized text-extraction tools.
2. **Recruiter** (*Hiring Manager Simulator*): Generates 5 realistic technical and behavioral questions.
3. **Challenger** (*Stress Interview Specialist*): Formulates 3 tough pushback and salary negotiation queries.
4. **Coach** (*Career Strategy Coach*): Synthesizes findings into a markdown strategy report.

The system implements hybrid **RAG (Retrieval-Augmented Generation)** by chunking, embedding (Google `text-embedding-004`), and storing resumes in Supabase pgvector. In chat, a hybrid cosine similarity + full-text search retrieves matching resume chunks to ground the AI Career Mentor.

We use multiple agents rather than a single prompt because different agents represent separate expert personas (screener, hostile interviewer, executive coach) that require unique system instructions, task dependencies, and sequential data refinement (one agent's output serves as the next agent's context) to produce targeted prep kits without context dilution.

---

## 🛠️ Submission Details

- **Frontend GitHub Repository**: [github.com/Deepak-DPK/career-command-center](https://github.com/Deepak-DPK/career-command-center)
- **Backend GitHub Repository**: [github.com/Deepak-DPK/career-command-center-backend](https://github.com/Deepak-DPK/career-command-center-backend)

---

## ✅ Framework & Requirements Checklist

### 1. Real-World Use Case
Solves the problem of alignment between resumes and job requirements, addressing ATS filters, tough behavioral questions, and salary negotiation strategies.

### 2. Multi-Agent System (4 Custom Agents)
Uses **CrewAI** as the primary orchestration framework with 4 distinct agents (none of which are generic researchers or summarizers):
- **Sleuth**: Resume Intelligence Specialist
- **Recruiter**: Hiring Manager Simulator
- **Challenger**: Stress Interview Specialist
- **Coach**: Career Strategy Coach

### 3. Agent Tool Calling & API Integrations
- **File System Operations**: Backend extracts and parses uploaded PDF resumes in memory.
- **Supabase DB & pgvector**: Saves raw data and generates text chunk vectors to store in the PostgreSQL vector table.
- **LiteLLM Model Router**: Routes completions to Gemini endpoints and triggers fallback completions to Groq Llama endpoints during timeouts or API deprecations.

### 4. RAG Implementation
- **Knowledge Source**: Uploaded candidate resume PDF files.
- **Mechanism**: The backend chunks the resume text, embeds the chunks using `text-embedding-004`, and index searches them using Cosine Similarity + Full-Text Search in PostgreSQL.

### 5. Authentication & Login
- Secure login implemented via **Firebase Auth** (Google Login).
- Features a local **Sandbox Guest Mode** that routes database operations to `sessionStorage` if client API variables are not configured, maintaining seamless application previews.
