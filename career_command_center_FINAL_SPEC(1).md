
# Career Command Center — FINAL Architecture Specification

## Overview
Production-grade AI interview prep SaaS with:
- React frontend
- FastAPI backend
- CrewAI (4 agents)
- Gemini / Groq LLM
- Supabase + pgvector
- Resume-aware RAG chat
- Sandbox & logged-in modes

## Modes
### Sandbox Mode
- No login required
- Resume upload + prep kit + AI chat
- Session stored only in sessionStorage
- Expires on tab/browser close
- No persistent storage
- Lower token budget

### Logged-In Mode
- Firebase / Supabase auth
- Multiple resumes per user
- Persistent RAG
- Chat memory across sessions
- Premium experience

## Final 4 Agents
1. Sleuth — gap analysis + ATS scoring
2. Recruiter — interview questions
3. Challenger — pushback + salary scenarios
4. Coach — final battle plan

Remove:
- ATS Optimizer
- Salary Negotiator
- Outreach Strategist

Set CrewAI:
max_iter = 3

## Token Optimization
1. Resume summarization (store summary JSON)
2. Chunked RAG retrieval
3. Only last 6 chat messages
4. Query router (simple queries bypass LLM)
5. Long-term memory summarization every 15 messages
6. Specialized chat personas:
   - Mentor
   - Recruiter
   - ATS
   - Negotiator

## Resume Storage
Multiple resumes supported.

Each resume has:
- resume_text
- resume_summary
- embeddings
- prep kits
- chat sessions
- memory summaries

## Supabase Schema

The database model is designed as a relational system with Row-Level Security (RLS) to prevent cross-user data leakage. A dedicated `prep_kits` table has been added to support multiple resumes and maintain their historical generation reports.

All tables, policies, indexes, and search functions are defined in [supabase_setup.sql](file:///c:/Users/deepa/OneDrive/Desktop/career-command-center-backend/supabase_setup.sql).

### Relational Tables
1. **`public.users`**: Sync profile linked to Supabase authentication schema.
2. **`public.resumes`**: Stores the raw resume text and parsed summary models, belonging to a user.
3. **`public.prep_kits`**: Stores generated coach prep kits, linked directly to the parent resume.
4. **`public.chat_sessions`**: Main session container for AI Mentor RAG conversations.
5. **`public.chat_messages`**: Message history logs mapped inside chat sessions.
6. **`public.resume_embeddings`**: Stores text chunks and their 768-dimension vectors for similarity search.

### Privacy & Row-Level Security (RLS)
Every table has RLS enabled with access control policies:
- Users can view and manage their own profiles, resumes, and prep kits.
- Access to chat messages and embeddings is restricted to matching owners by asserting existence checks against their session and resume structures.

### Performance Indexing
- Standard foreign key lookup indexes on `resume_id` and `session_id`.
- **HNSW Indexing**: Added a Hierarchical Navigable Small World (HNSW) index on `resume_embeddings(embedding)` using `vector_cosine_ops` to enable highly scalable, low-latency semantic search queries.

### Vector Search (Hybrid Retrieval Function)
To combine semantic understanding with keyword searches, we implement a **Hybrid Search SQL Function** `hybrid_search_resume_chunks`:
- **70% Semantic Weight**: Determined via pgvector cosine distance (`<=>`).
- **30% Keyword Matching Weight**: Derived using Postgres English Full-Text Search (FTS) ranking via `ts_rank_cd`.
- Fusion is achieved via a Full Outer Join scoring both matching vectors and rank scores.

## Chat Flow
Logged-in:
Login → Choose Resume → Prep Kit → RAG Chat

Sandbox:
Upload Resume → Prep Kit → Temporary Chat

## Backend Requirements
FastAPI must:
- generate prep kit
- summarize resume
- chunk resume
- store embeddings
- route chat queries
- retrieve relevant chunks
- maintain session logic

## Antigravity Prompt
Refactor the entire Career Command Center project using this architecture.
Requirements:
1. Implement sandbox mode using sessionStorage.
2. Implement logged-in mode using Supabase.
3. Support multiple resumes per user.
4. Implement Supabase pgvector.
5. Refactor CrewAI to 4 agents.
6. Add resume summarization.
7. Add chunked RAG retrieval.
8. Add query router.
9. Add long-term memory summaries.
10. Preserve existing frontend UI and API contracts.
All code must be production-ready and fully deployable.
