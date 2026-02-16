# api/index.py - FINAL VERCEL-COMPATIBLE VERSION
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx

# Import your logic
from question_router import route_question

app = FastAPI()

# Mount static and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Shared HTTP client
_client = None
async def get_client():
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=10.0)
    return _client

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.get_template("index.html").render({"request": request})

@app.get("/ask")
async def ask(q: str = ""):
    if not q.strip():
        return JSONResponse({"answer": "Ask me anything about MLB!"})
    try:
        from mlb_api_client import mlb
        mlb.client = await get_client()
        answer = await route_question(q)
        return JSONResponse({"answer": answer})
    except Exception as e:
        return JSONResponse({"answer": f"Error: {str(e)}"})
