import requests
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from fastapi import Request, HTTPException
import os

# Allow OAuth over HTTP locally
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# -----------------------------
# SESSION HELPERS
# -----------------------------

def save_session_state(request: Request, state: str):
    """Save the OAuth state to the session."""
    request.session["state"] = state
    print(f"🌀 Saved OAuth state: {state}")


def get_session_state(request: Request):
    """Retrieve the OAuth state from the session."""
    state = request.session.get("state")
    if not state:
        raise HTTPException(status_code=400, detail="Missing OAuth state in session.")
    return state


# -----------------------------
# TOKEN + USER INFO HELPERS
# -----------------------------

async def fetch_user_info(request: Request, client_secrets_file: str, scopes: list, redirect_uri: str):
    """
    Complete the OAuth callback flow:
      1️⃣ Retrieve the saved state
      2️⃣ Exchange the authorization code for an access token
      3️⃣ Get user info (email, picture, etc.)
    """

    # Restore state from session
    state = get_session_state(request)

    # Build the OAuth flow again
    flow = Flow.from_client_secrets_file(
        client_secrets_file,
        scopes=scopes,
        state=state,
        redirect_uri=redirect_uri,
    )

    # Exchange the code for tokens
    flow.fetch_token(authorization_response=str(request.url))
    credentials = flow.credentials

    # Store credentials JSON in session
    request.session["credentials"] = credentials.to_json()

    # Fetch user info from Google
    userinfo_resp = requests.get(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization": f"Bearer {credentials.token}"},
    )

    if not userinfo_resp.ok:
        raise HTTPException(status_code=401, detail="Failed to retrieve user info from Google.")

    userinfo = userinfo_resp.json()
    email = userinfo.get("email")
    picture = userinfo.get("picture", None)

    print(f"Logged in as {email}")

    return credentials.to_json(), email, picture


def restore_credentials(request: Request) -> Credentials | None:
    """Rebuild a Credentials object from session JSON."""
    creds_json = request.session.get("credentials")
    if not creds_json:
        return None
    return Credentials.from_authorized_user_info(eval(creds_json))
