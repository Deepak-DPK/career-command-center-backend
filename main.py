from fastapi import FastAPI, UploadFile, File, Form
from pypdf import PdfReader
import io
import requests
import os
import time

app = FastAPI()

CREWAI_ENDPOINT = os.getenv("CREWAI_ENDPOINT")
CREWAI_API_KEY = os.getenv("CREWAI_API_KEY")


def extract_pdf_text(file_bytes):
    pdf = PdfReader(io.BytesIO(file_bytes))
    text = ""

    for page in pdf.pages:
        content = page.extract_text()
        if content:
            text += content + "\n"

    return text


@app.get("/")
def home():
    return {"message": "Backend running successfully"}


@app.post("/generate-prep-kit")
async def generate_prep_kit(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    try:
        # Read PDF
        file_bytes = await resume.read()
        resume_text = extract_pdf_text(file_bytes)

        # Step 1: Kickoff CrewAI execution
        response = requests.post(
            CREWAI_ENDPOINT,
            headers={
                "Authorization": f"Bearer {CREWAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "inputs": {
                    "resume_text": resume_text,
                    "job_description": job_description
                },
                "taskWebhookUrl": ""
            }
        )

        # Debug if kickoff fails
        if response.status_code != 200:
            return {
                "error": "Kickoff failed",
                "status_code": response.status_code,
                "response": response.text
            }

        kickoff_data = response.json()

        if "kickoff_id" not in kickoff_data:
            return {
                "error": "No kickoff_id returned",
                "response": kickoff_data
            }

        kickoff_id = kickoff_data["kickoff_id"]

        # Step 2: Poll status endpoint
        BASE_URL = CREWAI_ENDPOINT.replace("/kickoff", "")
        status_url = f"{BASE_URL}/status/{kickoff_id}"

        for _ in range(30):   # wait ~60 seconds
            status_response = requests.get(
                status_url,
                headers={
                    "Authorization": f"Bearer {CREWAI_API_KEY}"
                }
            )

            status_data = status_response.json()

            # Debug output while testing
            print(status_data)

            status = (
                status_data.get("status")
                or status_data.get("state")
                or status_data.get("execution_status")
            )

            if status:
                status = status.lower()

            if status in ["completed", "success", "finished"]:
                return status_data

            if status in ["failed", "error"]:
                return {
                    "error": "CrewAI execution failed",
                    "details": status_data
                }

            time.sleep(2)

        return {"error": "CrewAI execution timeout"}

    except Exception as e:
        return {"error": str(e)}