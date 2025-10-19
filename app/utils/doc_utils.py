# app/utils/doc_utils.py
import os
import tempfile
from docx import Document
from datetime import datetime

def create_doc_from_text(text: str, title: str = "AI_Generated_Notes") -> str:
    """
    Creates a .docx document from plain text and returns the file path.
    """
    # Create a new Word document
    doc = Document()

    # Title section
    doc.add_heading(title, level=1)
    doc.add_paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    doc.add_paragraph("")  # spacing

    # Split text into paragraphs based on line breaks
    for paragraph in text.split("\n"):
        clean_para = paragraph.strip()
        if clean_para:
            doc.add_paragraph(clean_para)
        else:
            doc.add_paragraph("")

    # Save to a temporary path
    temp_dir = tempfile.gettempdir()
    safe_title = title.replace(" ", "_")
    file_path = os.path.join(temp_dir, f"{safe_title}.docx")
    doc.save(file_path)

    return file_path
