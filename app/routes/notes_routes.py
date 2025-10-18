from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import tempfile, os
from app.utils.file_extractors import extract_text_from_pdf, extract_text_from_pptx
from app.utils.llm_utils import generate_notes_from_llm

router = APIRouter()

@router.post("/generate")
async def generate_notes(file: UploadFile = File(...), style: str = Form(...)):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        temp_path = tmp.name

    ext = os.path.splitext(file.filename)[1].lower()
    if ext == ".pdf":
        text = extract_text_from_pdf(temp_path)
    elif ext in [".ppt", ".pptx"]:
        text = extract_text_from_pptx(temp_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    os.remove(temp_path)
    notes = await generate_notes_from_llm(text, style)
    return JSONResponse(content={"notes": notes})
