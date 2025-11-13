# backend/app.py
import asyncio
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
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

@app.post("/start")
async def start():
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "running"}
    asyncio.create_task(orchestrator.run_job(job_id))
    return {"job_id": job_id}

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await websocket.accept()
    try:
        while True:
            msg = await orchestrator.get_log(job_id)
            # send only non-empty messages to not spam
            if msg:
                await websocket.send_text(msg)
            await asyncio.sleep(0.2)
    except WebSocketDisconnect:
        print(f"Client disconnected {job_id}")
