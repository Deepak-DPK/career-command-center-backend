# Project Submission & Hackathon Requirements Document

This document compiles the submission requirements, project summary, and framework details for the **Career Command Center (CCC)** project.

---

## 📄 Project Summary (179 Words)

**Career Command Center** is a full-stack platform designed to help job seekers optimize their resumes and prepare for tough interviews. The backend runs a sequential workflow featuring four custom CrewAI agents:
1. **Sleuth** (*Resume Analyst*): Detects skill gaps and resume weaknesses using custom PDF text-extraction tools.
2. **Recruiter** (*Hiring Simulator*): Generates 5 realistic technical and behavioral interview questions.
3. **Challenger** (*Stress Tester*): Formulates 3 high-pressure pushback questions and 3 salary screening scenarios.
4. **Coach** (*Career Advisor*): Compiles these insights into a structured markdown study roadmap.

We implement **Retrieval-Augmented Generation (RAG)** by segmenting, embedding, and storing resumes in Supabase PostgreSQL tables using Google's `text-embedding-004` model. An interactive mentor chat then uses similarity vector searches to pull relevant resume chunks and ground conversation responses.

Using multiple specialized agents is superior to a single ChatGPT prompt because each agent operates with distinct expert instructions and dependencies. One agent's output sequentially feeds into the next, which prevents context loss, resolves token bottlenecks, and delivers deeply personalized, modular preparation kits that a single prompt cannot replicate.

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
