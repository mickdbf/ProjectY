# app/utils/text_utils.py
import re

def normalize_llm_text(raw_text: str) -> str:
    """Normalize EasyNote Markup (ENM) output."""
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    cleaned = []

    for line in lines:
        # Fix accidental markdown or formatting
        line = re.sub(r"[*`>]+", "", line).strip()

        # Ensure tags are uppercase
        m = re.match(r"^#([A-Za-z]+)\s*(.*)", line)
        if m:
            tag, content = m.groups()
            cleaned.append(f"#{tag.upper()} {content.strip()}")
            continue

        # Fallback: wrap stray text in a #POINT
        cleaned.append(f"#POINT {line}")

    return "\n".join(cleaned)
