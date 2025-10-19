# app/utils/drive_utils.py
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

EASYNOTE_FOLDER_NAME = "EasyNote AI"

def get_drive_service(credentials_json: str):
    """Builds a Drive API client from stored session credentials."""
    creds = Credentials.from_authorized_user_info(eval(credentials_json))
    return build("drive", "v3", credentials=creds)

def ensure_main_folder(service):
    """Ensures the main 'EasyNote AI' folder exists and returns its ID."""
    query = f"name='{EASYNOTE_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields="files(id, name)").execute()
    folders = results.get("files", [])

    if folders:
        return folders[0]["id"]

    # Create folder if it doesn’t exist
    file_metadata = {"name": EASYNOTE_FOLDER_NAME, "mimeType": "application/vnd.google-apps.folder"}
    folder = service.files().create(body=file_metadata, fields="id").execute()
    return folder["id"]

def upload_to_drive(credentials_json: str, file_path: str, file_name: str, category: str = "Lecture Notes"):
    """Uploads a file into the EasyNote AI folder (creates it if needed)."""
    service = get_drive_service(credentials_json)
    main_folder_id = ensure_main_folder(service)

    # Optional: create a category subfolder (e.g., "Cheat Sheets", "Outlines")
    subfolder_id = None
    if category:
        query = f"name='{category}' and '{main_folder_id}' in parents and trashed=false"
        result = service.files().list(q=query, fields="files(id, name)").execute()
        subfolders = result.get("files", [])
        if subfolders:
            subfolder_id = subfolders[0]["id"]
        else:
            metadata = {
                "name": category,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [main_folder_id],
            }
            subfolder = service.files().create(body=metadata, fields="id").execute()
            subfolder_id = subfolder["id"]

    parent_id = subfolder_id or main_folder_id

    media = MediaFileUpload(file_path, mimetype="application/pdf")
    file_metadata = {"name": file_name, "parents": [parent_id]}
    uploaded = service.files().create(body=file_metadata, media_body=media, fields="id").execute()

    # Make file link-shareable
    service.permissions().create(
        fileId=uploaded["id"],
        body={"role": "reader", "type": "anyone"},
    ).execute()

    file_link = f"https://drive.google.com/file/d/{uploaded['id']}/view"
    return file_link
