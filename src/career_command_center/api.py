import os
import json
import io
import re
import requests

# Hotfix: disable CrewAI's automatic cache_breakpoint injection which causes Groq requests to fail
try:
    import crewai.llms.cache as _crewai_cache
    _crewai_cache.mark_cache_breakpoint = lambda msg: msg
except Exception:
    pass

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
from pydantic import BaseModel
from career_command_center.crew import CareerCommandCenterCrew

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    resume_text: str = ""
    job_description: str = ""
    resume_id: str = ""
    persona: str = "mentor"

app = FastAPI(title="Career Command Center API", version="2.0.0")

# Enable CORS for frontend clients (e.g. Vercel deployment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_json_substring(text: str) -> str:
    """
    Robustly extracts the first JSON object or array from a string.
    This handles cases where the LLM appends conversational text before or after the JSON.
    """
    if not text:
        return ""
    text_str = text.strip()
    
    # Try to find JSON object {}
    first_brace = text_str.find('{')
    last_brace = text_str.rfind('}')
    
    # Try to find JSON array []
    first_bracket = text_str.find('[')
    last_bracket = text_str.rfind(']')
    
    # Extract based on which comes first and forms a valid outer boundary
    if first_brace != -1 and last_brace != -1:
        if first_bracket != -1 and first_bracket < first_brace and last_bracket > last_brace:
            return text_str[first_bracket:last_bracket+1]
        return text_str[first_brace:last_brace+1]
    elif first_bracket != -1 and last_bracket != -1:
        return text_str[first_bracket:last_bracket+1]
    
    return text_str

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extracts plain text from raw PDF bytes.
    """
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to read PDF resume: {str(e)}")

def calculate_ats_score(resume_text: str, job_description: str):
    """
    Computes ATS score, extracts missing keywords, and lists improvements using Python string operations.
    """
    def get_keywords(text):
        # find alphanumeric words of 3+ letters, lowercase
        words = re.findall(r'\b[a-zA-Z0-9_]{3,}\b', text.lower())
        stop_words = {
            'and', 'the', 'for', 'with', 'you', 'this', 'that', 'from', 'have', 'were',
            'are', 'was', 'not', 'but', 'can', 'will', 'your', 'their', 'they', 'our',
            'all', 'any', 'one', 'use', 'out', 'into', 'been', 'has', 'had', 'its',
            'who', 'whom', 'whose', 'which', 'what', 'when', 'where', 'why', 'how',
            'about', 'more', 'some', 'other', 'been', 'here', 'there', 'than', 'them',
            'would', 'should', 'could', 'their', 'into', 'also', 'some'
        }
        return {w for w in words if w not in stop_words and not w.isdigit()}

    resume_words = get_keywords(resume_text)
    jd_words = get_keywords(job_description)
    
    if not jd_words:
        return 100, [], []
        
    missing = sorted(list(jd_words - resume_words))
    overlap = jd_words.intersection(resume_words)
    
    ats_score = int(len(overlap) / len(jd_words) * 100)
    # normalize score between 45 and 95 to look realistic
    ats_score = max(45, min(92, ats_score))
    
    # Filter missing keywords to return the most meaningful ones (length >= 4)
    meaningful_missing = [w for w in missing if len(w) >= 4][:12]
    
    # Generate specific resume improvements based on missing keywords
    improvements = []
    for kw in meaningful_missing[:4]:
        improvements.append(f"Incorporate the keyword '{kw}' within your work experience descriptions to match job requirements.")
    
    improvements.extend([
        "Restructure bullet points to start with strong action verbs (e.g., 'Engineered', 'Optimized', 'Orchestrated').",
        "Quantify accomplishments with concrete metrics (e.g., 'improved page speed by 40%', 'reduced error rates by 15%').",
        "Ensure resume has a clear hierarchy with standard headings like 'Experience', 'Projects', and 'Skills'."
    ])
    
    return ats_score, meaningful_missing, improvements

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

def get_supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

def generate_resume_summary(resume_text: str) -> dict:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    api_key = gemini_api_key or os.getenv("GROQ_API_KEY")
    model_name = "google/gemini-2.5-flash" if gemini_api_key else os.getenv("MODEL_NAME", "groq/llama-3.1-8b-instant")
    
    prompt = f"""You are a professional recruiting assistant. Extract a structured JSON summary from this candidate's resume text.
RESUME TEXT:
\"\"\"
{resume_text}
\"\"\"

Your response must be a single, valid JSON object containing exactly these fields:
- "candidate_name": string or null
- "experience_summary": a 2-3 sentence overview of their background
- "top_skills": list of their top 6 technical skills
- "education": list of degrees and school names

Do not write any markdown code blocks, conversational greetings, or notes. Respond with ONLY the raw JSON string.
"""
    try:
        from litellm import completion
        response = completion(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            api_key=api_key,
            temperature=0.2
        )
        raw_content = response.choices[0].message.content.strip()
        raw_content = extract_json_substring(raw_content)
        if raw_content.startswith("```json"):
            raw_content = raw_content.replace("```json", "").replace("```", "").strip()
        return json.loads(raw_content)
    except Exception as e:
        print("Failed to generate resume summary:", e)
        return {
            "candidate_name": "Applicant",
            "experience_summary": "Extracted resume details.",
            "top_skills": [],
            "education": []
        }

def insert_resume(user_id: str, filename: str, text: str, summary: dict) -> str:
    url = f"{SUPABASE_URL}/rest/v1/resumes"
    payload = {
        "user_id": user_id,
        "resume_name": filename,
        "resume_text": text,
        "resume_summary": summary
    }
    resp = requests.post(url, headers=get_supabase_headers(), json=payload)
    resp.raise_for_status()
    return resp.json()[0]["id"]

def chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 150) -> list[str]:
    if not text:
        return []
    cleaned_text = re.sub(r'\s+', ' ', text).strip()
    chunks = []
    start = 0
    while start < len(cleaned_text):
        end = start + chunk_size
        if end < len(cleaned_text):
            split_idx = -1
            for i in range(end, max(start, end - 100), -1):
                if cleaned_text[i] in {'.', '!', '?', ' '}:
                    split_idx = i
                    break
            if split_idx != -1:
                end = split_idx + 1
        chunks.append(cleaned_text[start:end].strip())
        start = end - chunk_overlap
        if start >= len(cleaned_text) or end >= len(cleaned_text):
            break
    return [c for c in chunks if c]

def generate_embeddings(chunks: list[str]) -> list[list[float]]:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("Warning: GEMINI_API_KEY is not defined. Skipping embedding generation.")
        return [[0.0] * 768 for _ in chunks]
        
    try:
        from litellm import embedding
        resp = embedding(
            model="google/text-embedding-004",
            input=chunks,
            api_key=gemini_api_key
        )
        return [item["embedding"] for item in resp["data"]]
    except Exception as e:
        print("Failed to generate embeddings:", e)
        return [[0.0] * 768 for _ in chunks]

def insert_embeddings(resume_id: str, chunks: list[str], embeddings: list[list[float]]):
    url = f"{SUPABASE_URL}/rest/v1/resume_embeddings"
    payload = []
    for chunk, vector in zip(chunks, embeddings):
        payload.append({
            "resume_id": resume_id,
            "chunk_text": chunk,
            "embedding": vector
        })
    resp = requests.post(url, headers=get_supabase_headers(), json=payload)
    resp.raise_for_status()

def insert_prep_kit(user_id: str, resume_id: str, filename: str, job_description: str, prep_kit: dict):
    url = f"{SUPABASE_URL}/rest/v1/prep_kits"
    payload = {
        "user_id": user_id,
        "resume_id": resume_id,
        "resume_filename": filename,
        "job_description": job_description,
        "prep_kit": prep_kit
    }
    resp = requests.post(url, headers=get_supabase_headers(), json=payload)
    resp.raise_for_status()

def query_hybrid_search(query_text: str, query_embedding: list[float], resume_id: str, match_count: int = 5) -> list[str]:
    url = f"{SUPABASE_URL}/rest/v1/rpc/hybrid_search_resume_chunks"
    payload = {
        "query_text": query_text,
        "query_embedding": query_embedding,
        "match_count": match_count,
        "p_resume_id": resume_id
    }
    resp = requests.post(url, headers=get_supabase_headers(), json=payload)
    resp.raise_for_status()
    return [item["chunk_text"] for item in resp.json()]

def query_router(message: str) -> str | None:
    msg = message.strip().lower().rstrip(".!?")
    greetings = {"hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"}
    farewells = {"bye", "goodbye", "exit", "quit", "see you"}
    thanks = {"thank you", "thanks", "thank you so much", "appreciate it"}
    
    if msg in greetings:
        return "Hello! I am your AI Career Mentor. I have your dossier loaded. How can I help you strategize today?"
    if msg in farewells:
        return "Goodbye! Good luck with your preparation. The Command Center is always open whenever you want to run another briefing."
    if msg in thanks:
        return "You're very welcome! Let me know if you need help with salary negotiations, resolving skill gaps, or preparing for tough interview scenarios."
    return None

def generate_history_summary(messages: list[ChatMessage]) -> str:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    api_key = gemini_api_key or os.getenv("GROQ_API_KEY")
    model_name = "google/gemini-2.5-flash" if gemini_api_key else os.getenv("MODEL_NAME", "groq/llama-3.1-8b-instant")
    
    conversation_text = ""
    for msg in messages:
        conversation_text += f"{msg.role.upper()}: {msg.content}\n"
        
    prompt = f"""Summarize the key topics discussed and candidate background facts mentioned in this conversation history:
\"\"\"
{conversation_text}
\"\"\"
Write a 1-paragraph summary. Keep it concise."""
    try:
        from litellm import completion
        response = completion(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            api_key=api_key,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "Previous context discussed interview prep strategy."

@app.post("/generate-prep-kit")
@app.post("/api/generate-prep-kit")
async def generate_prep_kit(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    user_id: str = Form(None)
):
    # 1. Read PDF file bytes
    try:
        pdf_bytes = await resume.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {str(e)}")

    # 2. Extract plain text from PDF
    try:
        resume_text = extract_text_from_pdf(pdf_bytes)
        if not resume_text:
            raise ValueError("Extracted text is empty. Make sure the PDF contains readable text.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 3. Trigger CrewAI pipeline execution
    try:
        # Truncate inputs for LLM processing to reduce tokens
        resume_text_truncated = resume_text[:3500]
        job_description_truncated = job_description[:1800]
        
        inputs = {
            'resume_text': resume_text_truncated,
            'job_description': job_description_truncated
        }
        
        # Kick off the sequential crew agents workflow (4 tasks)
        result = await CareerCommandCenterCrew().crew().kickoff_async(inputs=inputs)
        
        # Ensure we have enough tasks outputs to parse (at least 4 tasks now)
        if not result or not result.tasks_output or len(result.tasks_output) < 4:
            raise ValueError("Crew completed but failed to generate all task output reports.")

        # 4. Parse & Aggregate Task Outputs for the Frontend
        
        # Task 0: resume_analysis
        skill_gaps = []
        gap_data = {}
        try:
            raw_gaps = result.tasks_output[0].raw
            cleaned_gaps = extract_json_substring(raw_gaps)
            if cleaned_gaps.startswith("```json"):
                cleaned_gaps = cleaned_gaps.replace("```json", "").replace("```", "").strip()
            gap_data = json.loads(cleaned_gaps)
            # Extracted skill gaps
            skill_gaps = gap_data.get("skill_gaps", [])
        except Exception as e:
            print("Failed to parse resume_analysis JSON output:", e)
            # If JSON parsing fails, try to clean the lines from raw text
            lines = [line.strip().lstrip("-*12345. ") for line in result.tasks_output[0].raw.split("\n") if line.strip()]
            skill_gaps = [line for line in lines if not line.startswith(("{", "}", "[", "]", '"'))]

        # Task 1: interview_questions
        questions = []
        try:
            raw_q = result.tasks_output[1].raw
            cleaned_q = extract_json_substring(raw_q)
            if cleaned_q.startswith("```json"):
                cleaned_q = cleaned_q.replace("```json", "").replace("```", "").strip()
            if cleaned_q.strip().startswith("["):
                questions = json.loads(cleaned_q)
            else:
                questions = [line.strip().lstrip("-*12345. ") for line in cleaned_q.split("\n") if line.strip()]
        except Exception as e:
            print("Failed to parse generate_interview_questions:", e)
            questions = [line.strip().lstrip("-*12345. ") for line in result.tasks_output[1].raw.split("\n") if line.strip()]

        # Task 2: challenger_questions
        pushback_questions = []
        salary_questions = []
        try:
            raw_challenger = result.tasks_output[2].raw
            cleaned_challenger = extract_json_substring(raw_challenger)
            if cleaned_challenger.startswith("```json"):
                cleaned_challenger = cleaned_challenger.replace("```json", "").replace("```", "").strip()
            challenger_data = json.loads(cleaned_challenger)
            pushback_questions = challenger_data.get("pushback_questions", [])
            salary_questions = challenger_data.get("salary_questions", [])
        except Exception as e:
            print("Failed to parse challenger_questions JSON output:", e)
            lines = [line.strip().lstrip("-*12345. ") for line in result.tasks_output[2].raw.split("\n") if line.strip()]
            pushback_questions = lines[:3]
            salary_questions = lines[3:6]

        # Task 3: coach_report
        coach_report = result.tasks_output[3].raw

        # 5. Hybrid logic: Calculate ATS score, missing keywords & improvements via Python
        py_ats_score, py_missing_keywords, py_improvements = calculate_ats_score(resume_text, job_description)
        
        # Merge Sleuth and Python outputs for robustness
        final_ats_score = py_ats_score
        if gap_data and "ats_score" in gap_data:
            try:
                final_ats_score = int(gap_data["ats_score"])
            except Exception:
                pass
                
        combined_missing_keywords = list(set(py_missing_keywords + gap_data.get("missing_keywords", [])))
        
        ats_analysis = {
            "ats_score": final_ats_score,
            "missing_keywords": combined_missing_keywords[:12],
            "resume_improvements": py_improvements
        }

        # 6. Hybrid logic: Generate salary negotiation kit using Challenger's questions and templates
        if not salary_questions:
            salary_questions = [
                "What are your salary expectations for this position?",
                "What is your current compensation package?",
                "What is your notice period and are you open to relocation?"
            ]
            
        jd_lower = job_description.lower()
        if any(x in jd_lower for x in ["india", "inr", "lpa", "mumbai", "bangalore", "bengaluru", "pune", "delhi", "noida"]):
            expected_range = "₹8–12 LPA"
            if "senior" in jd_lower or "lead" in jd_lower:
                expected_range = "₹18–25 LPA"
            elif "junior" in jd_lower or "entry" in jd_lower or "fresher" in jd_lower:
                expected_range = "₹4–6 LPA"
        else:
            expected_range = "$90,000–$120,000"
            if "senior" in jd_lower or "lead" in jd_lower:
                expected_range = "$140,000–$180,000"
            elif "junior" in jd_lower or "entry" in jd_lower or "fresher" in jd_lower:
                expected_range = "$60,000–$80,000"
                
        salary_negotiation = {
            "hr_questions": salary_questions,
            "negotiation_tips": [
                "Research local market compensation standards for this job title and level before negotiations.",
                "Focus on the value and impact you bring to the team rather than your personal financial needs.",
                "Defer the salary discussion during early interviews until you have established your value and fit.",
                "Consider the full reward package, including benefits, equity, flexible hours, and professional development."
            ],
            "recommended_answer_frameworks": [
                {
                    "title": "Expected Salary",
                    "framework": "Provide a research-backed range, frame it around the role value, and keep it flexible.",
                    "example": f"Based on my research of similar roles in this area and my relevant experience, I'm targeting a range of {expected_range}. I'm open to discussing the complete package once we align on the scope."
                },
                {
                    "title": "Current Salary",
                    "framework": "Focus on the value of the new role rather than your historical earnings.",
                    "example": "I'd prefer to focus on the value I can bring to this position and the market rate for this role, rather than my past compensation."
                },
                {
                    "title": "Competing Offers",
                    "framework": "Be honest but focus on the current opportunity and mutual alignment.",
                    "example": "I am in active discussions with other companies, but this opportunity is my top priority because it perfectly aligns with my skill set."
                }
            ]
        }

        # 7. Hybrid logic: Generate Outreach Assets
        # Extract title if present or default
        title_match = re.search(r'(?:title|role|position):\s*([^\n\r]+)', job_description, re.IGNORECASE)
        job_title = title_match.group(1).strip() if title_match else "Software Engineer"
        job_title = job_title[:50]
        
        cold_email = f"Subject: Application for {job_title} - Outreach\n\nDear Hiring Team,\n\nI recently applied for the {job_title} position and wanted to reach out directly. With my background in software development and hands-on project experience, I am confident I can contribute effectively to your team's goals.\n\nI would love the opportunity to discuss how my skills align with your current engineering challenges.\n\nBest regards,\nCandidate"
        
        linkedin_pitch = f"Hi, I noticed your team is hiring for a {job_title}. With my experience in software engineering and technical projects, I'd love to connect and briefly discuss how my background aligns with your current team needs. Thanks!"
        
        thank_you_note = f"Subject: Thank you - {job_title} Interview\n\nDear Interviewer,\n\nThank you for taking the time to speak with me today about the {job_title} role. I really enjoyed our conversation and learning more about the engineering challenges your team is solving.\n\nI am very excited about the opportunity to join the team and bring my technical skills to the role.\n\nBest regards,\nCandidate"
        
        outreach_assets = {
            "cold_email": cold_email,
            "linkedin_pitch": linkedin_pitch[:300],
            "thank_you_note": thank_you_note
        }

        # RAG Embedding & Storage Pipeline (if user_id is supplied)
        resume_id = None
        if user_id and SUPABASE_URL and SUPABASE_KEY:
            try:
                # 1. Summarize resume
                summary = generate_resume_summary(resume_text)
                # 2. Insert into resumes table
                resume_id = insert_resume(user_id, resume.filename, resume_text, summary)
                # 3. Chunk and embed resume text
                chunks = chunk_text(resume_text)
                if chunks:
                    vectors = generate_embeddings(chunks)
                    insert_embeddings(resume_id, chunks, vectors)
                # 4. Insert into prep_kits table
                prep_kit_data = {
                    "skill_gaps": skill_gaps,
                    "ats_analysis": ats_analysis,
                    "questions": questions,
                    "pushback_questions": pushback_questions,
                    "salary_negotiation": salary_negotiation,
                    "coach_report": coach_report,
                    "outreach_assets": outreach_assets
                }
                insert_prep_kit(user_id, resume_id, resume.filename, job_description, prep_kit_data)
            except Exception as db_err:
                print("Failed to store resume RAG pipeline on Supabase:", db_err)

        # 8. Return the unified JSON structure matching the frontend schema
        return {
            "skill_gaps": skill_gaps,
            "ats_analysis": ats_analysis,
            "questions": questions,
            "pushback_questions": pushback_questions,
            "salary_negotiation": salary_negotiation,
            "coach_report": coach_report,
            "outreach_assets": outreach_assets,
            "resume_text": resume_text_truncated,
            "resume_id": resume_id
        }

    except Exception as e:
        print("Error during CrewAI execution:", e)
        raise HTTPException(status_code=500, detail=f"CrewAI execution failed: {str(e)}")

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """
    Simulates a session-based Career Mentor / Coach chatbot.
    Supports 4 specialized personas (Mentor, Recruiter, ATS, Negotiator).
    Uses pgvector Hybrid search RAG context in logged-in mode, and fallback plain text context in Sandbox mode.
    Maintains session history limits (last 6 messages) and generates long-term memory summaries (>=15 messages).
    Includes a query router to fast-bypass the LLM for simple greetings or thank-yous.
    """
    try:
        # 1. Query Router check (Fast path bypass)
        fast_response = query_router(req.message)
        if fast_response:
            return {"reply": fast_response}

        # 2. Get API credentials & resolve models
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key:
            model_name = os.getenv("CHAT_MODEL_NAME", "google/gemini-2.5-flash")
            api_key = gemini_api_key
        else:
            # Fallback to Groq if Gemini API Key is not set
            groq_api_key = os.getenv("GROQ_API_KEY")
            if not groq_api_key:
                raise HTTPException(status_code=500, detail="Neither GEMINI_API_KEY nor GROQ_API_KEY is configured in the environment.")
            model_name = os.getenv("MODEL_NAME", "groq/llama-3.1-8b-instant")
            api_key = groq_api_key

        # 3. Retrieve relevant resume chunks (RAG)
        rag_context = ""
        if req.resume_id and SUPABASE_URL and SUPABASE_KEY and gemini_api_key:
            try:
                # Generate embedding for user query
                from litellm import embedding
                embed_resp = embedding(
                    model="google/text-embedding-004",
                    input=[req.message],
                    api_key=gemini_api_key
                )
                query_vector = embed_resp["data"][0]["embedding"]
                
                # Perform hybrid vector similarity + FTS search
                chunks = query_hybrid_search(req.message, query_vector, req.resume_id, match_count=4)
                if chunks:
                    rag_context = "\n---\n".join(chunks)
            except Exception as rag_err:
                print("Failed to perform hybrid RAG search, falling back to raw text:", rag_err)
        
        # Fallback to plain truncated resume text if no RAG chunks were resolved
        if not rag_context:
            rag_context = req.resume_text[:2000] if req.resume_text else "No resume data available."

        # 4. Resolve Chat Persona Prompt
        PERSONA_PROMPTS = {
            "mentor": "You are an elite, senior Career Coach and Mentor. Focus on strategic advice, interview strategies, confidence building, and professional growth.",
            "recruiter": "You are a tough, corporate HR Recruiter. Focus on credentials, direct alignment with core job description keywords, and bulletproof brief corporate communication.",
            "ats": "You are a cold, analytical ATS scanning algorithm. Focus on keyword density, formatting compliance, search engine relevancy, and parser optimization strategies.",
            "negotiator": "You are a seasoned compensation strategist. Focus on salary negotiation range frameworks, total reward packages (benefits/equity), and script phrasing."
        }
        active_persona = req.persona.lower().strip()
        persona_instructions = PERSONA_PROMPTS.get(active_persona, PERSONA_PROMPTS["mentor"])

        # 5. Long-term memory summaries (>=15 messages)
        long_term_summary = ""
        history_to_use = req.history
        if len(req.history) >= 15:
            older_history = req.history[:-6]
            long_term_summary = generate_history_summary(older_history)
            history_to_use = req.history[-6:]
        else:
            # Spec constraint: Keep only the last 6 messages of active history
            history_to_use = req.history[-6:]

        # 6. Build the System Prompt
        system_prompt = f"""{persona_instructions}

You have access to the following context (RAG):
TARGET JOB DESCRIPTION:
\"\"\"
{req.job_description}
\"\"\"

CANDIDATE RESUME DOSSIER:
\"\"\"
{rag_context}
\"\"\"
"""
        if long_term_summary:
            system_prompt += f"\nSUMMARY OF OLDER CONVERSATION HISTORY:\n\"\"\"\n{long_term_summary}\n\"\"\"\n"

        system_prompt += """
Instructions:
- Be highly professional, strategic, encouraging, and clear.
- Directly reference the candidate's achievements, projects, or gaps when answering questions.
- Address their queries systematically (e.g. use bullet points if helpful, but keep answers concise).
- Do not make up facts not present in the resume or job description; maintain realistic constraints.
- Format all your responses using clean Markdown.
"""

        # 7. Format messages list
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history_to_use:
            messages.append({"role": msg.role, "content": msg.content})
        
        # Append the new user message
        messages.append({"role": "user", "content": req.message})

        from litellm import completion
        response = completion(
            model=model_name,
            messages=messages,
            api_key=api_key,
            temperature=0.7
        )
        
        reply = response.choices[0].message.content
        return {"reply": reply}
    except Exception as e:
        print("Chat completion failed:", e)
        raise HTTPException(status_code=500, detail=f"Failed to generate AI response: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Default local dev port
    uvicorn.run("career_command_center.api:app", host="0.0.0.0", port=8000, reload=True)
