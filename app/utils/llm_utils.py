import os
import asyncio
import math
from openai import OpenAI
from app.utils.text_utils import normalize_llm_text

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === CONFIG ===
MODEL = "gpt-4o"              # Larger context + output capacity than mini
BATCH_SIZE = 8                # 6–10 slides per chunk is a good sweet spot
MAX_OUTPUT_TOKENS = 4096      # Ensure large enough output per batch
SLIDE_SEPARATOR = "---"       # Adjust if your pipeline uses a different delimiter


# -------------------------------
# Style / audience / depth / tone
# -------------------------------
STYLE_INSTRUCTIONS = {
    "outline": (
        "STYLE: SIMPLE OUTLINE\n"
        "→ Goal: Provide a clear, hierarchical summary for quick scanning.\n"
        "→ Structure:\n"
        "   - Use #SECTION and #SUBSECTION to mirror slide organization.\n"
        "   - Use #POINT for short bullet ideas (5–12 words each).\n"
        "→ Language:\n"
        "   - Write in phrases, not sentences.\n"
        "   - Avoid #NOTE or long paragraphs.\n"
        "   - Emphasize structure over detail.\n"
        "→ Example:\n"
        "   #SECTION Databases\n"
        "   #SUBSECTION SQL Basics\n"
        "   #POINT SELECT retrieves data\n"
        "   #POINT WHERE filters results"
    ),
    "detailed": (
        "STYLE: DETAILED NOTES\n"
        "→ Goal: Recreate rich lecture notes with explanations, transitions, and examples.\n"
        "→ Structure:\n"
        "   - Use #SECTION for main topics and #SUBSECTION for slide groups.\n"
        "   - Use #POINT for facts and key steps.\n"
        "   - Use #NOTE for short explanatory paragraphs.\n"
        "   - Include #CODE / #ENDCODE for formulas or snippets.\n"
        "→ Language:\n"
        "   - Write in full sentences and connected paragraphs.\n"
        "   - Maintain clarity and logical flow, as if explaining to classmates.\n"
        "→ Example:\n"
        "   #SECTION Transactions\n"
        "   #POINT A transaction is a unit of work.\n"
        "   #NOTE Transactions ensure data consistency and integrity across operations."
    ),
    "cheatsheet": (
        "STYLE: CHEAT SHEET\n"
        "→ Goal: Produce a condensed, exam-review version — dense, formulaic, and minimal.\n"
        "→ Structure:\n"
        "   - Use #SECTION for main concepts.\n"
        "   - Use #POINT lines for terms, definitions, and formulas.\n"
        "   - Use #QUOTE for key rules, principles, or quick reminders.\n"
        "→ Language:\n"
        "   - Ultra-concise (one line per idea).\n"
        "   - Prefer symbols, abbreviations, or compact phrasing.\n"
        "   - Avoid #NOTE and long sentences.\n"
        "→ Example:\n"
        "   #SECTION Normal Forms\n"
        "   #POINT 1NF → No repeating groups\n"
        "   #POINT 2NF → 1NF + no partial dependency\n"
        "   #QUOTE Keep each table single-purpose!"
    )
}

AUDIENCE_HINT = {
    "beginner": "Write for beginners — simple language and concrete examples.",
    "college": "Write for undergraduate students — clear, structured, moderate technicality.",
    "researcher": "Write for researchers — maintain precision, academic tone, and clarity.",
    "professional": "Write for professionals — emphasize real-world applications and insights."
}

DEPTH_HINT = {
    "concise": "Be brief and to the point; only essential ideas.",
    "balanced": "Provide key ideas with short supporting explanations.",
    "in-depth": "Expand on reasoning, relationships, and examples in detail."
}

TONE_HINT = {
    "neutral": "Maintain an objective, academic tone.",
    "friendly": "Use a warm, encouraging tone while staying professional.",
    "formal": "Use polished, formal academic phrasing.",
    "academic": "Adopt a scholarly tone with precise terminology."
}


def _extras_instructions(extras: set | list | None, is_final_batch: bool) -> str:
    """
    Build instructions for extras. Only include Summary/Glossary on the final batch.
    """
    if not extras:
        return ""

    extras = set(extras)
    lines = []

    if "summary" in extras and is_final_batch:
        lines.append("At the end, include a #SECTION Summary with 3–5 #POINT key takeaways.")
    if "glossary" in extras and is_final_batch:
        lines.append("Include a #SECTION Glossary with concise definitions for key terms.")
    if "highlight_terms" in extras:
        lines.append("Emphasize critical terms using ALL CAPS (e.g., DATABASE, NORMALIZATION).")

    # If it's not the final batch, explicitly forbid summary/glossary now.
    if not is_final_batch and (("summary" in extras) or ("glossary" in extras)):
        lines.append("Do NOT include Summary or Glossary in this batch.")

    return "\n".join(lines)


def _base_enm_spec() -> str:
    return (
        "You are EasyNote AI — an assistant that converts lecture slides into organized, "
        "student-friendly notes using the EASYNOTE MARKUP (ENM) format.\n\n"
        "ENM TAGS:\n"
        "  #SECTION <name>        → major topic header\n"
        "  #SUBSECTION <name>     → subtopic header\n"
        "  #POINT <text>          → bullet or key/value item\n"
        "  #NOTE <text>           → short paragraph or explanation\n"
        "  #CODE / #ENDCODE       → wrap code, formula, or example blocks\n"
        "  #DIVIDER               → horizontal break between major ideas\n"
        "  #QUOTE <text>          → quote or highlighted rule\n\n"
        "RULES:\n"
        "- Plain text only (no Markdown, emojis, or decorative lines).\n"
        "- One tag per line; blank line between sections.\n"
        "- No extra commentary or formatting outside ENM.\n"
    )


def _compose_style_block(style: str, audience: str, depth: str, tone: str) -> str:
    style_block = STYLE_INSTRUCTIONS.get(
        style, "Use #SECTION headers and #POINT lines with short #NOTE explanations."
    )
    audience_block = AUDIENCE_HINT.get(audience, "Write clearly and appropriately for a general audience.")
    depth_block = DEPTH_HINT.get(depth, "Provide moderate detail — key ideas with short supporting notes.")
    tone_block = TONE_HINT.get(tone, "Maintain an objective, academic tone.")
    return f"{style_block}\n\n{audience_block}\n{depth_block}\n{tone_block}"


def _build_prompt(
    slides_text: str,
    style: str,
    batch_index: int,
    total_batches: int,
    start_slide_number: int,
    audience: str,
    depth: str,
    tone: str,
    extras: set | list | None,
    is_final_batch: bool
) -> str:
    """
    Batch-aware prompt that includes ENM spec + style/audience/depth/tone + extras.
    """
    base_spec = _base_enm_spec()
    style_block = _compose_style_block(style, audience, depth, tone)
    extras_block = _extras_instructions(extras, is_final_batch)

    return f"""
{base_spec}

ADDITIONAL DIRECTIVES:
- One #SECTION per slide.
- Start each section as: "#SECTION {start_slide_number} — <Concise Title>" and increment the number for each slide.
- If a title is missing in the slide, infer a concise title from the first line.
- Keep the slide numbering continuous across batches (do not reset).
- Do not stop early — complete ALL slides in this batch.
- Preserve semantic order and avoid skipping slides.
- Use only the ENM tags listed above.
- No Markdown, no emojis, no decorative lines.

STYLE & TONE:
{style_block}

{"EXTRAS:\n" + extras_block if extras_block else ""}

You are processing batch {batch_index + 1} of {total_batches}.
Slides in this batch start at Slide {start_slide_number}.

LECTURE CONTENT STARTS BELOW (SOURCE TEXT):
{slides_text}

--- END OF SLIDES ---

Now produce ENM notes ONLY, adhering to the directives above.
""".strip()


async def _process_batch(
    slides_chunk: list[str],
    style: str,
    batch_index: int,
    total_batches: int,
    start_slide_number: int,
    audience: str,
    depth: str,
    tone: str,
    extras: set | list | None,
    is_final_batch: bool
) -> str:
    prompt = _build_prompt(
        slides_text="\n\n".join(slides_chunk),
        style=style,
        batch_index=batch_index,
        total_batches=total_batches,
        start_slide_number=start_slide_number,
        audience=audience,
        depth=depth,
        tone=tone,
        extras=extras,
        is_final_batch=is_final_batch
    )

    # Using the modern Responses API for robust long outputs
    response = await asyncio.to_thread(
        lambda: client.responses.create(
            model=MODEL,
            input=prompt,
            max_output_tokens=MAX_OUTPUT_TOKENS,
            temperature=0.35
        )
    )

    output_text = response.output_text.strip()
    return normalize_llm_text(output_text)


# -------------------------------
# PUBLIC ENTRYPOINT (same signature you had)
# -------------------------------
async def generate_notes_from_llm(
    text: str,
    style: str,
    audience: str = "college",
    depth: str = "balanced",
    tone: str = "neutral",
    extras: set | list | None = None,
):
    """
    Generate full-length ENM notes from a long slide deck with style/audience/depth/tone/extras.
    Splits content into batches to avoid token limits and guarantees sequential coverage.
    """
    # Split into slides
    slides = [s.strip() for s in text.split(SLIDE_SEPARATOR) if s.strip()]
    total_slides = len(slides)
    if total_slides == 0:
        return ""

    total_batches = math.ceil(total_slides / BATCH_SIZE)

    all_output = []
    next_slide_number = 1

    for batch_i in range(total_batches):
        start = batch_i * BATCH_SIZE
        end = start + BATCH_SIZE
        slides_chunk = slides[start:end]

        batch_output = await _process_batch(
            slides_chunk=slides_chunk,
            style=style,
            batch_index=batch_i,
            total_batches=total_batches,
            start_slide_number=next_slide_number,
            audience=audience,
            depth=depth,
            tone=tone,
            extras=extras,
            is_final_batch=(batch_i == total_batches - 1),
        )

        all_output.append(batch_output)
        next_slide_number += len(slides_chunk)

    final_output = "\n\n".join(all_output)
    return normalize_llm_text(final_output)
