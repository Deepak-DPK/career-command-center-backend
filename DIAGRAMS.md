# Career Command Center — System Diagrams Reference

This document compiles the simplified, clean, and crisp Mermaid architecture diagrams and process flows that represent the design of the **Career Command Center (CCC)** application. It also provides copy-pasteable prompts to generate professional visual diagrams in **Eraser.io**.

---

## 1. System Architecture Diagram

This diagram maps the high-level system boundaries and integrations.

```mermaid
graph TD
    A["React Frontend UI"] <-->|API Request and Auth| B["FastAPI Backend Gateway"]
    B <-->|Session Verification| C["Firebase Auth"]
    B <-->|Storage and Vector Search| D["Supabase Database"]
    B -->|Triggers Pipeline| E["CrewAI Orchestrator"]
    E -->|Model Routing via LiteLLM| F["LLMs: Gemini or Groq"]
```

---

## 2. Backend Architecture Diagram

This diagram zooms into the FastAPI backend server, detailing the API layers and the sequential agent workflow.

```mermaid
graph LR
    A["HTTP Request"] --> B["FastAPI Router"]
    B --> C["PDF Text Extractor"]
    C --> D["CrewAI Orchestrator"]
    
    subgraph agent_sequence ["Sequential Agent Pipeline"]
        D --> E["Sleuth ATS and Gaps"]
        E --> F["Recruiter Core Questions"]
        F --> G["Challenger Pushback"]
        G --> H["Coach Strategy Battle Plan"]
    end
    
    H --> I["Unified JSON Response"]
    I --> B
```

---

## 3. RAG Architecture Diagram

This diagram details the dual RAG Ingestion (PDF index upload) and Retrieval (AI Chat query) flows.

```mermaid
graph TD
    subgraph ingestion ["1. Ingestion Flow: PDF Upload"]
        A["Resume PDF"] --> B["Text Chunking"]
        B --> C["768-Dimensional Vector Embeddings"]
        C --> D["Store in Supabase pgvector"]
    end

    subgraph retrieval ["2. Retrieval Flow: AI Chat"]
        E["User Question"] --> F["Generate Query Vector"]
        F --> G["Cosine Similarity Search"]
        G --> H["Inject Matching Chunks to Prompt"]
        H --> I["LLM Completion: Gemini or Groq"]
        I --> J["Deliver AI Chat Response"]
    end
```

---

## 4. User Flow Architecture Diagram

This diagram tracks the candidate journey from landing page to dashboard interaction based on authentication status.

```mermaid
graph TD
    A["Candidate Landing Page"] --> B{"Has Google Auth?"}
    B -->|Yes| C["Google Login Mode: All 8 Features Unlocked"]
    B -->|No| D["Sandbox Guest Mode: 4 Features Unlocked and 4 Locked"]
    
    C & D --> E["Upload Resume and Enter Job Description"]
    E --> F["FastAPI executes CrewAI sequential pipeline"]
    
    F --> G["Review Dashboard Gaps and Questions"]
    G --> H{"Is Google Auth User?"}
    H -->|Yes| I["Access Coach Strategy, Salary scripts, and RAG Chat Mentor"]
    H -->|No| J["Blocked from Premium Features and Chat overlay"]
```

---

## 🎨 Eraser.io Diagram Code Prompts

Copy and paste the code blocks below into **Eraser.io**'s diagram-as-code editor to generate high-resolution, professional architecture diagrams.

### System Architecture Code
```text
// System Architecture
ReactFrontend [icon: react, label: "React Frontend UI"]
FastAPIGateway [icon: fastapi, label: "FastAPI Backend Gateway"]
FirebaseAuth [icon: firebase, label: "Firebase Auth"]
SupabaseDB [icon: database, label: "Supabase Database"]
CrewAIOrchestrator [icon: python, label: "CrewAI Orchestrator"]
LLMProviders [icon: openai, label: "LLMs: Gemini / Groq"]

ReactFrontend > FastAPIGateway: "API Requests & Auth"
FastAPIGateway > FirebaseAuth: "Session Verification"
FastAPIGateway > SupabaseDB: "RAG search & cache storage"
FastAPIGateway > CrewAIOrchestrator: "Trigger sequential agents"
CrewAIOrchestrator > LLMProviders: "Route models via LiteLLM"
```

### Backend Architecture Code
```text
// Backend Architecture
HTTPRequest [icon: check, label: "HTTP Request"]
FastAPIRouter [icon: fastapi, label: "FastAPI Router"]
PDFExtractor [icon: document, label: "PDF Text Extractor"]
CrewAIOrchestrator [icon: python, label: "CrewAI Orchestrator"]

subgraph agent_pipeline [label: "Sequential Agent Pipeline"]
  Sleuth [icon: search, label: "Sleuth: ATS & Gaps"]
  Recruiter [icon: user, label: "Recruiter: Core Questions"]
  Challenger [icon: shield, label: "Challenger: Pushback"]
  Coach [icon: compass, label: "Coach: Strategy Battle Plan"]
  
  Sleuth > Recruiter
  Recruiter > Challenger
  Challenger > Coach
end

HTTPRequest > FastAPIRouter
FastAPIRouter > PDFExtractor
PDFExtractor > CrewAIOrchestrator
CrewAIOrchestrator > Sleuth
Coach > FastAPIRouter: "Unified JSON response"
```

### RAG Architecture Code
```text
// RAG Architecture
subgraph ingestion_flow [label: "1. Ingestion Flow (PDF Upload)"]
  ResumePDF [icon: document, label: "Resume PDF"]
  Chunking [icon: grid, label: "Text Chunking"]
  Embeddings [icon: hash, label: "768-Dim Vector Embeddings"]
  SupabaseStorage [icon: database, label: "Supabase pgvector"]
  
  ResumePDF > Chunking > Embeddings > SupabaseStorage
end

subgraph retrieval_flow [label: "2. Retrieval Flow (AI Chat)"]
  UserQuestion [icon: message, label: "User Question"]
  QueryVector [icon: hash, label: "Generate Query Vector"]
  CosineSearch [icon: search, label: "Cosine Similarity Match"]
  ContextInjection [icon: plus, label: "Inject Chunks to Prompt"]
  LLMCompletion [icon: openai, label: "LLM: Gemini / Groq"]
  ChatReply [icon: check, label: "Deliver Chat Response"]
  
  UserQuestion > QueryVector > CosineSearch > ContextInjection > LLMCompletion > ChatReply
end

SupabaseStorage > CosineSearch: "Retrieve matching chunks"
```
