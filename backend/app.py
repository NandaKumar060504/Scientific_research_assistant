import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH)

import asyncio
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from orchestrator import Orchestrator

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = Orchestrator()
jobs = {}


# -------- START --------
@app.post("/start")
async def start():
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "running",
        "results": None,
        "html_content": None
    }
    asyncio.create_task(orchestrator.run_job(job_id, jobs))
    return {"job_id": job_id}


# -------- LOG STREAM --------
@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await websocket.accept()
    try:
        while True:
            msg = await orchestrator.get_log(job_id)
            if msg:
                await websocket.send_text(msg)
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        print(f"Client disconnected {job_id}")


# -------- GET RESULT --------
# @app.get("/result/{job_id}")
# async def get_result(job_id: str):
#     """Return final research paper HTML content"""
#     result = orchestrator.get_result(job_id)
    
#     print(f"[/result] job_id={job_id}, result={result}")  # Debug log
    
#     if not result:
#         return {"status": "pending", "html_content": None}
    
#     # Read the HTML file and return its content
#     try:
#         html_path = result.get("html")
        
#         if not html_path:
#             return {"status": "error", "message": "No HTML path in results", "html_content": None}
            
#         if not os.path.exists(html_path):
#             return {"status": "error", "message": f"HTML file not found at {html_path}", "html_content": None}
        
#         with open(html_path, "r", encoding="utf-8") as f:
#             html_content = f.read()
        
#         return {
#             "status": "done",
#             "html_content": html_content
#         }
#     except Exception as e:
#         print(f"[/result] Error reading HTML: {e}")
#         return {"status": "error", "message": str(e), "html_content": None}
@app.get("/result/{job_id}")
async def get_result(job_id: str):
    """Return final research paper HTML content"""
    result = orchestrator.get_result(job_id)
    
    if not result:
        return {"status": "pending", "html_content": None}
    
    # Return in-memory HTML content
    html_content = result.get("html_content")
    
    if not html_content:
        return {"status": "error", "message": "HTML not generated", "html_content": None}
    
    return {
        "status": "done",
        "html_content": html_content,
        "has_pdf": "pdf" in result
    }



# -------- DOWNLOAD PDF --------
@app.get("/download/{job_id}")
async def download(job_id: str):
    result = orchestrator.get_result(job_id)
    if not result:
        return {"error": "Result not ready"}

    pdf_path = result.get("pdf")
    if not pdf_path or not os.path.exists(pdf_path):
        return {"error": "PDF not found"}

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"research_paper_{job_id}.pdf"
    )

