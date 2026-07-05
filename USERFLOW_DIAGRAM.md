# Career Command Center — User Flow Diagram

This diagram tracks the candidate journey from the landing page through the dashboard, showing the authentication branching and which premium features are locked/unlocked.

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
