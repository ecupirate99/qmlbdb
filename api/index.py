# api/index.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import httpx
import os

# === Only import your logic, don't instantiate clients yet ===
from question_router import route_question

app = FastAPI()

# In-memory client (reused across invocations when warm)
_client = None

async def get_client():
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=10.0)
    return _client

@app.get("/")
async def home():
    return HTMLResponse("""
    <h1>MLB Chatbot is running on Vercel!</h1>
    <p>Go to /ask?q=your+question</p>
    <p>Or use the full web UI at your domain</p>
    """)

@app.get("/ask")
async def ask(q: str = ""):
    if not q:
        return {"error": "No question provided"}
    try:
        # Patch the mlb client to use our warm client
        from mlb_api_client import mlb
        mlb.client = await get_client()
        answer = await route_question(q)
        return {"answer": answer}
    except Exception as e:
        return {"error": str(e)}
