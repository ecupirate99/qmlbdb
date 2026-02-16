# api/index.py - FULL VERSION WITH WEB UI
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import os

# Import your logic
from question_router import route_question

app = FastAPI()

# Serve static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")

# Use absolute path for templates
templates = Jinja2Templates(directory="templates")

# Warm client for serverless
_client = None
async def get_client():
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=10.0)
    return _client

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.get_template("index.html").render({"request": request})

@app.get("/ask")
async def ask(q: str = ""):
    if not q:
        return {"answer": "Ask me anything about MLB!"}
    try:
        from mlb_api_client import mlb
        mlb.client = await get_client()
        answer = await route_question(q)
        return {"answer": answer}
    except Exception as e:
        return {"answer": f"Oops! {str(e)}"}
