import os
import json
import io
import re

# Hotfix: disable CrewAI's automatic cache_breakpoint injection which causes Groq requests to fail
try:
    import crewai.llms.cache as _crewai_cache
    _crewai_cache.mark_cache_breakpoint = lambda msg: msg
except Exception:
    pass

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
from career_command_center.crew import CareerCommandCenterCrew

app = FastAPI(title="Career Command Center API", version="2.0.0")

# Enable CORS for frontend clients (e.g. Vercel deployment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.post("/generate-prep-kit")
@app.post("/api/generate-prep-kit")
async def generate_prep_kit(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
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
            # Clean possible markdown wrapping if any
            if raw_gaps.startswith("```json"):
                raw_gaps = raw_gaps.replace("```json", "").replace("```", "").strip()
            gap_data = json.loads(raw_gaps)
            # Extracted skill gaps
            skill_gaps = gap_data.get("skill_gaps", [])
        except Exception as e:
            print("Failed to parse resume_analysis JSON output:", e)
            skill_gaps = [result.tasks_output[0].raw]

        # Task 1: interview_questions
        questions = []
        try:
            raw_q = result.tasks_output[1].raw
            if raw_q.startswith("```json"):
                raw_q = raw_q.replace("```json", "").replace("```", "").strip()
            if raw_q.strip().startswith("["):
                questions = json.loads(raw_q)
            else:
                questions = [line.strip().lstrip("-*12345. ") for line in raw_q.split("\n") if line.strip()]
        except Exception as e:
            print("Failed to parse generate_interview_questions:", e)
            questions = [line.strip().lstrip("-*12345. ") for line in result.tasks_output[1].raw.split("\n") if line.strip()]

        # Task 2: challenger_questions
        pushback_questions = []
        salary_questions = []
        try:
            raw_challenger = result.tasks_output[2].raw
            if raw_challenger.startswith("```json"):
                raw_challenger = raw_challenger.replace("```json", "").replace("```", "").strip()
            challenger_data = json.loads(raw_challenger)
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

        # 8. Return the unified JSON structure matching the frontend schema
        return {
            "skill_gaps": skill_gaps,
            "ats_analysis": ats_analysis,
            "questions": questions,
            "pushback_questions": pushback_questions,
            "salary_negotiation": salary_negotiation,
            "coach_report": coach_report,
            "outreach_assets": outreach_assets
        }

    except Exception as e:
        print("Error during CrewAI execution:", e)
        raise HTTPException(status_code=500, detail=f"CrewAI execution failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Default local dev port
    uvicorn.run("career_command_center.api:app", host="0.0.0.0", port=8000, reload=True)
