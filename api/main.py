"""FastAPI app exposing the FOI pipeline to the React UI.

Run from the repo root:
    uvicorn api.main:app --reload --port 8000

Endpoints:
    GET  /api/health
    GET  /api/requests
    GET  /api/requests/{id}
    POST /api/requests/{id}/process
    POST /api/requests/{id}/decision   body: {"decision": "...", "notes": "..."}
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Build the policy vector store once on startup so compliance citations work.
    count = pipeline.ensure_index()
    if count >= 0:
        print(f"[api] indexed {count} policy chunks")
    else:
        print("[api] policy index already populated")
    yield


app = FastAPI(title="FOI Automation API", version="1.0.0", lifespan=lifespan)

# The Vite dev server runs on 5173; allow it (and the preview port) to call us.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class DecisionBody(BaseModel):
    decision: str
    notes: str = ""


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/requests")
def get_requests():
    return pipeline.list_requests()


@app.get("/api/requests/{request_id}")
def get_request(request_id: str):
    record = pipeline.get_request(request_id)
    if record is None:
        raise HTTPException(status_code=404, detail="request not found")
    return record


@app.post("/api/requests/{request_id}/process")
def process_request(request_id: str):
    record = pipeline.process(request_id)
    if record is None:
        raise HTTPException(status_code=404, detail="request not found")
    return record


@app.post("/api/requests/{request_id}/decision")
def decide_request(request_id: str, body: DecisionBody):
    try:
        record = pipeline.decide(request_id, body.decision, body.notes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if record is None:
        raise HTTPException(status_code=404, detail="request not found")
    return record
