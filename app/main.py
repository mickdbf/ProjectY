from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import uvicorn

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Welcome to ProjectX"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Use Cloud Run's PORT or fallback to 8080
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
