from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import json

router = APIRouter(prefix="/drive")

@router.get("/folders")
async def list_folders(request: Request):
    """List all EasyNote AI folders (terms and courses)."""
    creds_json = request.session.get("credentials")
    if not creds_json:
        raise HTTPException(status_code=401, detail="Not authenticated with Google")

    creds = Credentials.from_authorized_user_info(json.loads(creds_json))
    service = build("drive", "v3", credentials=creds)

    # Find base folder
    base_query = "mimeType='application/vnd.google-apps.folder' and name='EasyNote AI'"
    results = service.files().list(q=base_query, fields="files(id)").execute()
    if not results["files"]:
        return {"folders": {}}

    base_id = results["files"][0]["id"]

    # Get terms (subfolders)
    term_results = service.files().list(
        q=f"'{base_id}' in parents and mimeType='application/vnd.google-apps.folder'",
        fields="files(id, name)"
    ).execute()
    folder_map = {}
    for term in term_results["files"]:
        course_results = service.files().list(
            q=f"'{term['id']}' in parents and mimeType='application/vnd.google-apps.folder'",
            fields="files(name)"
        ).execute()
        folder_map[term["name"]] = [c["name"] for c in course_results["files"]]

    return {"folders": folder_map}


@router.post("/folders")
async def create_folder(request: Request):
    """Create a new term or course folder."""
    creds_json = request.session.get("credentials")
    if not creds_json:
        raise HTTPException(status_code=401, detail="Not authenticated with Google")

    data = await request.json()
    name = data.get("name")
    parent = data.get("parent")
    level = data.get("level")

    creds = Credentials.from_authorized_user_info(json.loads(creds_json))
    service = build("drive", "v3", credentials=creds)

    base_id = ensure_folder(service, "EasyNote AI")

    parent_id = base_id
    if level == "course" and parent:
        parent_id = ensure_folder(service, parent, parent_id=base_id)

    ensure_folder(service, name, parent_id=parent_id)
    return JSONResponse(content={"message": "Folder created successfully"})


# Reuse the helper for folder creation
def ensure_folder(service, name, parent_id=None):
    q = f"mimeType='application/vnd.google-apps.folder' and name='{name}'"
    if parent_id:
        q += f" and '{parent_id}' in parents"
    r = service.files().list(q=q, fields="files(id)").execute()
    if r["files"]:
        return r["files"][0]["id"]
    meta = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        meta["parents"] = [parent_id]
    folder = service.files().create(body=meta, fields="id").execute()
    return folder["id"]
