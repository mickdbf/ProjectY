# app/routes/notes_routes.py
from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import JSONResponse
import tempfile, os

from app.utils.file_extractors import extract_text_from_pdf, extract_text_from_pptx
from app.utils.llm_utils import generate_notes_from_llm
from app.utils.doc_utils import create_doc_from_text
from app.utils.drive_utils import upload_to_drive

router = APIRouter()


@router.post("/generate")
async def generate_notes(
    request: Request,
    file: UploadFile = File(...),
    style: str = Form(...),
    term: str = Form(None),
    course: str = Form(None),
    filename: str = Form(None)
):
    """
    Extract text from uploaded slides → generate AI notes → create DOCX → upload to Drive.
    """

    try:
        # --- 1️⃣ Save uploaded file temporarily ---
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(await file.read())
            temp_path = tmp.name

        # --- 2️⃣ Extract text content ---
        ext = os.path.splitext(file.filename)[1].lower()
        if ext == ".pdf":
            text = extract_text_from_pdf(temp_path)
        elif ext in [".ppt", ".pptx"]:
            text = extract_text_from_pptx(temp_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        os.remove(temp_path)

        # --- 3️⃣ Generate AI notes ---
        notes = await generate_notes_from_llm(text, style)

        # --- 4️⃣ Style-based file naming ---
        style_label = {
            "outline": "Outline",
            "detailed": "Detailed",
            "cheatsheet": "CheatSheet"
        }.get(style.lower(), "Notes")

        base_name = os.path.splitext(filename or file.filename)[0]

        # Remove any trailing "_Notes" to avoid duplicates
        if base_name.lower().endswith("_notes"):
            base_name = base_name[:-6]

        output_name = f"{base_name}_{style_label}.docx"

        # --- 5️⃣ Create DOCX file ---
        doc_path = create_doc_from_text(notes, os.path.splitext(output_name)[0])

        # --- 6️⃣ Upload to Google Drive ---
        credentials_json = request.session.get("credentials")
        if not credentials_json:
            raise HTTPException(status_code=401, detail="User not authenticated with Google")

        drive_link = upload_to_drive(
            credentials_json,
            local_path=doc_path,
            filename=os.path.basename(output_name),
            term_folder=term,
            course_folder=course
        )

        os.remove(doc_path)

        # --- 7️⃣ Return response ---
        return JSONResponse(content={
            "notes": notes,
            "drive_link": drive_link,
            "filename": output_name
        })

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
