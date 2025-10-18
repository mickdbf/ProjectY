from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import google.auth.transport.requests
import requests
import os

# Allow OAuth over HTTP for local dev
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# -----------------------------
# CONFIGURATION
# -----------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Ensure this points to your actual JSON file
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "..", "client_secret.json")

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/drive.file"
]
REDIRECT_URI = "http://localhost:8080/auth/callback"

IS_PRODUCTION = os.environ.get("ENVIRONMENT") == "production"

# -----------------------------
# APP SETUP
# -----------------------------

app = FastAPI()
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Session middleware configuration
# `same_site="none"` allows cookies on Google redirect; required for OAuth.
# Use a fixed secret key in dev so cookies stay valid across reloads.
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", "dev-session-key-123"),
    session_cookie="session",
    same_site="lax" if not IS_PRODUCTION else "none",
    https_only=IS_PRODUCTION,
    max_age=3600,
)


# -----------------------------
# ROUTES
# -----------------------------

@app.get("/", response_class=HTMLResponse)
async def splash_page(request: Request):
    """Landing page with Google login."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/auth/login")
async def login(request: Request):
    """Begin OAuth flow with Google."""
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )

    # Save OAuth state in session
    request.session["state"] = state
    print(f"Saved OAuth state: {state}")
    print(f"Session before redirect: {dict(request.session)}")

    return RedirectResponse(authorization_url)


@app.get("/auth/callback")
async def auth_callback(request: Request):
    """Handle redirect from Google after user grants permissions."""
    print(f"Session at callback: {dict(request.session)}")
    state = request.session.get("state")

    if not state:
        raise HTTPException(status_code=400, detail="Missing OAuth state")

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=REDIRECT_URI
    )

    flow.fetch_token(authorization_response=str(request.url))
    credentials = flow.credentials
    request.session["credentials"] = credentials.to_json()

    # Fetch user info from Google
    userinfo = requests.get(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization": f"Bearer {credentials.token}"}
    ).json()

    user_email = userinfo.get("email")
    request.session["user_email"] = user_email
    print(f"Logged in as {user_email}")

    return RedirectResponse(url="/app")


@app.get("/logout")
async def logout(request: Request):
    """Logout user and clear session."""
    request.session.clear()
    print("Logged out, session cleared.")
    return RedirectResponse(url="/")


@app.get("/app", response_class=HTMLResponse)
async def app_page(request: Request):
    """Main app page — requires login."""
    if not request.session.get("credentials"):
        return RedirectResponse(url="/auth/login")

    user_email = request.session.get("user_email")
    return templates.TemplateResponse("app.html", {"request": request, "user_email": user_email})


@app.post("/generate")
async def generate_notes(file: UploadFile = File(...), style: str = Form(...)):
    """Simulate file processing and upload."""
    fake_results = [
        {"name": f"{file.filename}_Notes.pdf", "link": "https://drive.google.com/file/d/xyz"},
        {"name": f"{file.filename}_CheatSheet.pdf", "link": "https://drive.google.com/file/d/abc"},
    ]
    return JSONResponse(content={"files": fake_results})


# -----------------------------
# DEBUG TEST ROUTE (OPTIONAL)
# -----------------------------
@app.get("/test-session")
async def test_session(request: Request):
    """Helper route to confirm session persistence."""
    count = request.session.get("count", 0) + 1
    request.session["count"] = count
    return {"count": count, "session": dict(request.session)}


# -----------------------------
# RUN LOCALLY
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
