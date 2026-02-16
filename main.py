from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from question_router import route_question

app = FastAPI(title="MLB Chatbot v3")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.get_template("index.html").render({"request": request})

@app.get("/ask")
async def ask(q: str):
    if not q.strip():
        return {"answer": "Ask me anything about MLB!"}
    answer = await route_question(q)
    return {"answer": answer}
