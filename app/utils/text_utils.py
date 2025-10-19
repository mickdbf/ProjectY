# app/utils/text_utils.py
import re

def normalize_llm_text(raw_text: str) -> str:
    """
    Light cleanup of LLM output that follows the #SECTION / - bullet schema.
    Ensures consistent spacing, removes stray Markdown, and guarantees
    clean structure for the .docx generator.
    """

    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    cleaned = []

    for line in lines:
        # Ignore markdown junk if any slipped through
        line = re.sub(r"[*_`#>]+", "", line).strip()

        # Restore the #SECTION tag if accidentally stripped
        if line.upper().startswith("SECTION "):
            line = "#SECTION " + line[8:].strip()

        # Valid #SECTION header
        if line.startswith("#SECTION "):
            cleaned.append("")  # blank line before
            cleaned.append(line)
            cleaned.append("")  # blank line after
            continue

        # Accept bullets or key:value pairs
        if line.startswith("- ") or ":" in line:
            cleaned.append(line)
            continue

        # Fallback: treat as bullet content
        cleaned.append(f"- {line}")

    # Collapse multiple blank lines
    text = "\n".join(cleaned)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
