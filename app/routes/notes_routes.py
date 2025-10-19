from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import JSONResponse
import tempfile, os

from app.utils.file_extractors import extract_text_from_pdf, extract_text_from_pptx
from app.utils.llm_utils import generate_notes_from_llm
from app.utils.doc_utils import create_doc_from_text
from app.utils.drive_utils import upload_to_drive

router = APIRouter()

@router.post("/generate")
async def generate_notes(request: Request, file: UploadFile = File(...), style: str = Form(...)):
    """
    Extract text from uploaded slides → generate AI notes → create PDF → upload to Google Drive.
    """
    try:
        # 1️⃣ Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(await file.read())
            temp_path = tmp.name

        # 2️⃣ Extract text content
        ext = os.path.splitext(file.filename)[1].lower()
        if ext == ".pdf":
            text = extract_text_from_pdf(temp_path)
        elif ext in [".ppt", ".pptx"]:
            text = extract_text_from_pptx(temp_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        os.remove(temp_path)

        # 3️⃣ Generate AI notes
        notes = await generate_notes_from_llm(text, style)

        # 4️⃣ Convert generated notes to DOCX instead of PDF
        doc_path = create_doc_from_text(notes, f"{os.path.splitext(file.filename)[0]}_Notes")

        # 5️⃣ Upload to user's Google Drive
        credentials_json = request.session.get("credentials")
        if not credentials_json:
            raise HTTPException(status_code=401, detail="User not authenticated with Google")

        drive_link = upload_to_drive(
            credentials_json,
            doc_path,
            os.path.basename(doc_path),
            style.capitalize()
        )

        # 6️⃣ Clean up temp file
        os.remove(doc_path)

        # 7️⃣ Return JSON with notes text and Drive link
        return JSONResponse(content={
            "notes": notes,
            "drive_link": drive_link
        })

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
