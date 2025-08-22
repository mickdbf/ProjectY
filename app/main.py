from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os


app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # directory of main.py
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Welcome to ProjectX"})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
