# app/routes/auth_routes.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from google_auth_oauthlib.flow import Flow
from app.utils.oauth_utils import save_session_state, fetch_user_info
from fastapi.templating import Jinja2Templates
import os

router = APIRouter()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


CLIENT_SECRETS_FILE = os.environ.get(
    "GOOGLE_CLIENT_SECRETS_FILE",
    os.path.join(os.path.dirname(__file__), "../../client_secret.json"),
)
REDIRECT_URI = os.environ.get("OAUTH_REDIRECT_URI", "http://localhost:8080/auth/callback")
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/drive.file"
]

@router.get("/", response_class=HTMLResponse)
async def splash_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/auth/login")
async def login(request: Request):
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    authorization_url, state = flow.authorization_url(access_type="offline", include_granted_scopes="true", prompt="consent")
    save_session_state(request, state)
    return RedirectResponse(authorization_url)

@router.get("/auth/callback")
async def callback(request: Request):
    creds, email, picture = await fetch_user_info(request, CLIENT_SECRETS_FILE, SCOPES, REDIRECT_URI)
    request.session["credentials"] = creds
    request.session["user_email"] = email
    request.session["user_picture"] = picture
    return RedirectResponse(url="/app")

@router.get("/app", response_class=HTMLResponse)
async def app_page(request: Request):
    if not request.session.get("credentials"):
        return RedirectResponse(url="/auth/login")
    return templates.TemplateResponse("app.html", {"request": request,
        "user_email": request.session.get("user_email"),
        "user_picture": request.session.get("user_picture")})

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")
