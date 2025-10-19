from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json

def upload_to_drive(credentials_json, local_path, filename, term_folder="Unsorted", course_folder="General"):
    """Uploads a DOCX file into EasyNote AI/{term}/{course}, converting it to a Google Doc."""
    from google.oauth2.credentials import Credentials

    creds = Credentials.from_authorized_user_info(json.loads(credentials_json))
    service = build("drive", "v3", credentials=creds)

    # --- Ensure folder hierarchy ---
    base_id = ensure_folder(service, "EasyNote AI")
    term_id = ensure_folder(service, term_folder, parent_id=base_id)
    course_id = ensure_folder(service, course_folder, parent_id=term_id)

    # --- Upload and convert ---
    file_metadata = {
        "name": filename,
        "parents": [course_id],
        "mimeType": "application/vnd.google-apps.document",
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

    metadata = {"name": folder_name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        metadata["parents"] = [parent_id]

    folder = service.files().create(body=metadata, fields="id").execute()
    return folder.get("id")
