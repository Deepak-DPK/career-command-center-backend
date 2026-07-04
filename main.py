from fastapi import FastAPI, UploadFile, File, Form
from pypdf import PdfReader
import io, requests, os

app = FastAPI()

CREWAI_ENDPOINT = os.getenv("https://career-command-center-v1-745f910e-a809-4c93-5562140f.crewai.com")
CREWAI_API_KEY = os.getenv("42ca4cc24484")


def extract_pdf_text(file_bytes):
    pdf = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in pdf.pages:
        content = page.extract_text()
        if content:
            text += content + "\n"
    return text


@app.post("/generate-prep-kit")
async def generate_prep_kit(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    file_bytes = await resume.read()
    resume_text = extract_pdf_text(file_bytes)

    response = requests.post(
        CREWAI_ENDPOINT,
        headers={
            "Authorization": f"Bearer {CREWAI_API_KEY}"
        },
        json={
            "inputs": {
                "resume_text": resume_text,
                "job_description": job_description
            }
        }
    )

    return response.json()