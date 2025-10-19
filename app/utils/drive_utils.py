from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json

def upload_to_drive(credentials_json, local_path, filename, style_folder="General"):
    """Uploads a DOCX file and converts it into a native Google Doc in the user's Drive."""
    from google.oauth2.credentials import Credentials

    creds = Credentials.from_authorized_user_info(json.loads(credentials_json))
    service = build("drive", "v3", credentials=creds)

    # --- ensure EasyNote AI base folder exists ---
    folder_id = ensure_folder(service, "EasyNote AI")

    # --- ensure style-based subfolder exists ---
    subfolder_id = ensure_folder(service, style_folder, parent_id=folder_id)

    # --- upload file (convert to native Google Doc) ---
    file_metadata = {
        "name": filename,
        "parents": [subfolder_id],
        "mimeType": "application/vnd.google-apps.document",  # ✅ this does the magic
    }

    media = MediaFileUpload(
        local_path,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        resumable=True
    )

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink"
    ).execute()

    return file.get("webViewLink")


def ensure_folder(service, folder_name, parent_id=None):
    """Find or create a Drive folder."""
    query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}'"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get("files", [])

    if folders:
        return folders[0]["id"]

    file_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        file_metadata["parents"] = [parent_id]

    folder = service.files().create(body=file_metadata, fields="id").execute()
    return folder.get("id")
