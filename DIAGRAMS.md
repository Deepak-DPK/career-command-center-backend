# Career Command Center — System Diagrams Reference

This document compiles the Mermaid architecture diagrams and process flows that represent the design of the **Career Command Center (CCC)** application.

---

## 1. System Architecture Diagram

This diagram maps the high-level boundaries between the user's browser, external cloud APIs, authentication services, and the backend engine.

```mermaid
graph TB
    subgraph client_layer ["Client Layer"]
        A["React TypeScript SPA Dashboard"]
    end

    subgraph auth_cdn ["Authentication & CDN"]
        B["Firebase Auth Service (Google Login)"]
        C["Vite Static Asset Server"]
    end

    subgraph service_layer ["Service Layer (FastAPI Backend)"]
        D["FastAPI Gateway"]
        E["CrewAI Execution pipeline"]
        F["LiteLLM Routing Module"]
    end

    subgraph db_storage ["Vector DB & Storage (Supabase PostgreSQL)"]
        G["resumes Table (Raw Document)"]
        H["resume_embeddings Table (pgvector)"]
        I["prep_kits Table (Cached Dossiers)"]
    end

    subgraph llm_providers ["Third-Party LLM Providers"]
        J["Google AI API (Gemini-1.5-Flash)"]
        K["Groq API (Llama-3.1-8B-Instant)"]
    end

    %% Client Interactions
    A -->|User Session Info| B
    A -->|1. Upload File & Form Parameters| D
    A -->|3. Query chat message| D

    %% Backend Routing
    D -->|2. Trigger sequential agents| E
    E -->|Call LLM endpoints| F
    D -->|Retrieve matching chunks| H
    D -->|Store processed kit| I
    D -->|Store parsed resume| G

    %% LLM Routing
    F -->|Primary Route| J
    F -->|Failover Route| K
```

---

## 2. Backend Architecture Diagram

This diagram zooms into the FastAPI backend server, illustrating the API router layers, business components, and the sequential CrewAI task pipeline.

```mermaid
graph LR
    subgraph endpoints ["FastAPI Endpoints"]
        A["POST /generate-prep-kit"]
        B["POST /chat"]
    end

    subgraph pipeline ["Data Processing Pipeline"]
        C["PDF text parser"]
        D["Hybrid keyword matcher"]
        E["RAG semantic retrieval"]
    end

    subgraph agent_seq ["CrewAI Agent Sequence"]
        F["Sleuth Agent<br/>(Resume Analysis)"]
        G["Recruiter Agent<br/>(Core Questions)"]
        H["Challenger Agent<br/>(Pushback & Salary)"]
        I["Coach Agent<br/>(Career Battle Plan)"]
    end

    %% Endpoint routing
    A -->|Extract text| C
    C -->|Truncated inputs| F
    
    %% Sequential crew execution
    F -->|Analysis outputs| G
    G -->|Analysis + Core Questions| H
    H -->|All intermediate context| I
    
    %% Response and Storage
    I -->|JSON output kit| D
    B -->|User message| E
    E -->|Retrieve semantic context| B
```

---

## 3. RAG Architecture Diagram

This diagram details the dual RAG pipeline: **Ingestion Flow** (how the resume is split and indexed) and **Retrieval Flow** (how candidate queries are semantically matched and answered).

```mermaid
flowchart TD
    subgraph ingestion_flow ["Ingestion Flow (PDF Upload)"]
        A["Candidate Resume Uploaded"] --> B["FastAPI extracts raw string text"]
        B --> C["Text divided into overlapping chunks"]
        C --> D["Gemini embedding model generates 768-dim vectors"]
        D --> E["Store chunks and vector keys in Supabase postgres table"]
    end

    subgraph retrieval_flow ["Retrieval Flow (User Chat Query)"]
        F["Candidate inputs chat question"] --> G["Generate query vector embedding"]
        G --> H["PostgreSQL Cosine Similarity search matching user resume_id"]
        H --> I["Retrieve top 4 closest matching resume chunks"]
        I --> J["Assemble prompt with System Rules + RAG chunks + Message History"]
        J --> K["Gemini API generates chat response"]
        K -->|If API fails| L["Failover to Groq API Llama model"]
        L --> M["Deliver chat reply to client"]
        K --> M
    end
```

---

## 4. User Flow Architecture Diagram

This diagram tracks the step-by-step journey of a job candidate, showing how they navigate the application states from initial landing through dashboard analysis.

```mermaid
graph TD
    A["Candidate visits dashboard site"] --> B{"Is Firebase credentials loaded?"}
    
    %% Auth path selection
    B -->|No| C["Enters Sandbox mode as Guest"]
    B -->|Yes| D["Authenticates via Google Login"]
    
    %% File input step
    C --> E["Access Command Dashboard Panel"]
    D --> E
    E --> F["Uploads Resume PDF & types Target Job Description"]
    F --> G["Clicks 'Generate Prep Kit' trigger button"]
    G --> H["FastAPI processes CrewAI sequence"]
    
    %% Results viewing
    H --> I["Display interactive command results"]
    I --> J["Read Skill Gaps and ATS Score metrics"]
    I --> K["Review simulated Interview and Pushback questions"]
    I --> L["Access Salary scripts and Outreach drafts"]
    
    %% Interactive chat
    I --> M["Initiate chat session with AI Career Mentor"]
    M --> N["Consult mentor on specific gaps or salary traps"]
```
