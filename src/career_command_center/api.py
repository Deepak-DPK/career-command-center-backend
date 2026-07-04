import os
import json

# Hotfix: disable CrewAI's automatic cache_breakpoint injection which causes Groq requests to fail
try:
    import crewai.llms.cache as _crewai_cache
    _crewai_cache.mark_cache_breakpoint = lambda msg: msg
except Exception:
    pass
import io
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
        inputs = {
            'resume_text': resume_text,
            'job_description': job_description
        }
        
        # Kick off the sequential crew agents workflow
        result = await CareerCommandCenterCrew().crew().kickoff_async(inputs=inputs)
        
        # Ensure we have enough tasks outputs to parse
        if not result or not result.tasks_outputs or len(result.tasks_outputs) < 7:
            raise ValueError("Crew completed but failed to generate all task output reports.")

        # 4. Parse & Aggregate Task Outputs for the Frontend
        
        # Task 0: resume_gap_analysis
        skill_gaps = []
        try:
            raw_gaps = result.tasks_outputs[0].raw
            # Clean possible markdown wrapping if any
            if raw_gaps.startswith("```json"):
                raw_gaps = raw_gaps.replace("```json", "").replace("```", "").strip()
            gap_data = json.loads(raw_gaps)
            # Combine missing skills and experience gaps for the unified list
            skill_gaps = gap_data.get("missing_skills", []) + gap_data.get("experience_gaps", [])
        except Exception as e:
            print("Failed to parse resume_gap_analysis JSON output:", e)
            skill_gaps = [result.tasks_outputs[0].raw]

        # Task 1: ats_optimization_analysis
        ats_analysis = {
            "ats_score": 70,
            "missing_keywords": [],
            "resume_improvements": []
        }
        try:
            raw_ats = result.tasks_outputs[1].raw
            if raw_ats.startswith("```json"):
                raw_ats = raw_ats.replace("```json", "").replace("```", "").strip()
            ats_data = json.loads(raw_ats)
            ats_analysis = {
                "ats_score": int(ats_data.get("ats_score", 70)),
                "missing_keywords": ats_data.get("missing_keywords", []),
                "resume_improvements": ats_data.get("resume_improvements", [])
            }
        except Exception as e:
            print("Failed to parse ats_optimization_analysis JSON output:", e)

        # Task 2: generate_interview_questions
        questions = []
        try:
            raw_q = result.tasks_outputs[2].raw
            if raw_q.strip().startswith("["):
                if raw_q.startswith("```json"):
                    raw_q = raw_q.replace("```json", "").replace("```", "").strip()
                questions = json.loads(raw_q)
            else:
                questions = [line.strip().lstrip("-*12345. ") for line in raw_q.split("\n") if line.strip()]
        except Exception as e:
            print("Failed to parse generate_interview_questions:", e)
            questions = [line.strip().lstrip("-*12345. ") for line in result.tasks_outputs[2].raw.split("\n") if line.strip()]

        # Task 3: generate_pushback_questions
        pushback_questions = []
        try:
            raw_pb = result.tasks_outputs[3].raw
            if raw_pb.strip().startswith("["):
                if raw_pb.startswith("```json"):
                    raw_pb = raw_pb.replace("```json", "").replace("```", "").strip()
                pushback_questions = json.loads(raw_pb)
            else:
                pushback_questions = [line.strip().lstrip("-*12345. ") for line in raw_pb.split("\n") if line.strip()]
        except Exception as e:
            print("Failed to parse generate_pushback_questions:", e)
            pushback_questions = [line.strip().lstrip("-*12345. ") for line in result.tasks_outputs[3].raw.split("\n") if line.strip()]

        # Task 4: salary_negotiation_strategy
        salary_negotiation = {
            "hr_questions": [],
            "negotiation_tips": [],
            "recommended_answer_frameworks": []
        }
        try:
            raw_sal = result.tasks_outputs[4].raw
            if raw_sal.startswith("```json"):
                raw_sal = raw_sal.replace("```json", "").replace("```", "").strip()
            sal_data = json.loads(raw_sal)
            
            # Map recommended_answer_frameworks to the format expected by the frontend
            raw_frameworks = sal_data.get("recommended_answer_frameworks", [])
            mapped_frameworks = []
            for fw in raw_frameworks:
                mapped_frameworks.append({
                    "title": fw.get("scenario", "Negotiation Scenario"),
                    "framework": fw.get("framework", f"Tactical approach for responding to the {fw.get('scenario', 'scenario')} question."),
                    "example": fw.get("suggested_response", fw.get("example", "No script provided."))
                })
                
            salary_negotiation = {
                "hr_questions": sal_data.get("hr_questions", []),
                "negotiation_tips": sal_data.get("negotiation_tips", []),
                "recommended_answer_frameworks": mapped_frameworks
            }
        except Exception as e:
            print("Failed to parse salary_negotiation_strategy:", e)

        # Task 5: generate_outreach_assets
        outreach_assets = {
            "cold_email": "No cold email template generated.",
            "linkedin_pitch": "No LinkedIn connection pitch generated.",
            "thank_you_note": "No post-interview thank you email generated."
        }
        try:
            raw_outreach = result.tasks_outputs[5].raw
            if raw_outreach.startswith("```json"):
                raw_outreach = raw_outreach.replace("```json", "").replace("```", "").strip()
            outreach_data = json.loads(raw_outreach)
            outreach_assets = {
                "cold_email": outreach_data.get("cold_email", "No cold email template generated."),
                "linkedin_pitch": outreach_data.get("linkedin_pitch", "No LinkedIn connection pitch generated."),
                "thank_you_note": outreach_data.get("thank_you_note", "No post-interview thank you email generated.")
            }
        except Exception as e:
            print("Failed to parse generate_outreach_assets:", e)

        # Task 6: generate_interview_coaching_report
        coach_report = result.tasks_outputs[6].raw

        # 5. Return the unified JSON structure
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
