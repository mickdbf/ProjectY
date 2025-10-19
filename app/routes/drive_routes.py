# app/routes/drive_routes.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from app.utils.drive_utils import get_drive_service, ensure_main_folder

router = APIRouter()

@router.get("/drive/test")
async def drive_test(request: Request):
    """Checks if the user’s Google Drive is connected and accessible."""
    creds_json = request.session.get("credentials")
    if not creds_json:
        raise HTTPException(status_code=401, detail="User not authenticated with Google")

    try:
        service = get_drive_service(creds_json)
        folder_id = ensure_main_folder(service)
        return JSONResponse(content={"status": "ok", "main_folder_id": folder_id})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
