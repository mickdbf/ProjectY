# app/main.py
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routes import auth_routes, notes_routes
import os


# -----------------------------
# ENVIRONMENT CONFIGURATION
# -----------------------------

# Allow OAuth over HTTP for local dev
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

IS_PRODUCTION = os.environ.get("ENVIRONMENT") == "production"

# -----------------------------
# APP INITIALIZATION
# -----------------------------

app = FastAPI(title="EasyNote AI", description="AI-powered lecture note generator")

# Session middleware configuration
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", "dev-session-key-123"),
    session_cookie="session",
    same_site="lax" if not IS_PRODUCTION else "none",
    https_only=IS_PRODUCTION,
    max_age=3600,
)

# Serve static files and Jinja templates
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# -----------------------------
# ROUTE REGISTRATION
# -----------------------------

# Core routes (OAuth + main app UI)
app.include_router(auth_routes.router)

# AI Notes / LLM route
app.include_router(notes_routes.router)

# -----------------------------
# ROOT TEST ROUTE
# -----------------------------

@app.get("/health")
async def health_check():
    """Simple route to verify service health."""
    return {"status": "ok", "environment": "production" if IS_PRODUCTION else "development"}

# -----------------------------
# RUN LOCALLY
# -----------------------------

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
