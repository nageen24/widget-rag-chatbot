"""
FastAPI backend for the RAG chatbot.
Endpoints:
  POST /chat          — ask a question, get an answer
  GET  /health        — health check
  POST /ingest        — re-ingest the knowledge base (admin use)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.rag import answer
from backend.ingest import ingest

app = FastAPI(title="ABC Tech Chatbot API")

# Allow the widget to call the API from any origin (for local dev + embedding)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Serve frontend widget
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


class ChatMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    question: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    answer: str
    intent: str = "specific"


@app.get("/")
def root():
    index = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return {"status": "Hewmann Chatbot API running. Visit /docs for API docs."}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    try:
        history = [{"role": m.role, "content": m.content} for m in req.history]
        result = answer(req.question, history=history)
        return ChatResponse(answer=result["answer"], intent=result.get("intent", "specific"))
    except Exception as e:
        if "Knowledge base not found" in str(e) or "ingest" in str(e):
            raise HTTPException(status_code=503, detail="Knowledge base not built yet. Run ingest first.")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest")
def run_ingest(force: bool = False):
    success = ingest(force=force)
    if not success:
        raise HTTPException(status_code=500, detail="Ingest failed. Check data/knowledge_base.docx exists.")
    return {"status": "Ingest complete."}
