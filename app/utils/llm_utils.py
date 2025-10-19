import os, asyncio
from openai import OpenAI
from app.utils.text_utils import normalize_llm_text

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def build_prompt(text, style, audience="college", depth="balanced", tone="neutral", extras=None):
    """
    Construct a prompt that guarantees structured, machine-readable note output
    using EasyNote Markup (ENM) syntax, tuned for distinct note styles.
    """

    # ---------------------------------------------
    # 1️⃣ Base ENM specification
    # ---------------------------------------------
    base_intro = (
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
        "- No extra commentary or formatting outside ENM.\n\n"
        "LECTURE CONTENT STARTS BELOW:\n\n"
    )

    # ---------------------------------------------
    # 2️⃣ Style-Specific Writing Directives
    # ---------------------------------------------
    style_instructions = {
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
        ),
    }.get(style, "Use #SECTION headers and #POINT lines with short #NOTE explanations.")

    # ---------------------------------------------
    # 3️⃣ Audience context
    # ---------------------------------------------
    audience_hint = {
        "beginner": "Write for beginners — simple language and concrete examples.",
        "college": "Write for undergraduate students — clear, structured, moderate technicality.",
        "researcher": "Write for researchers — maintain precision, academic tone, and clarity.",
        "professional": "Write for professionals — emphasize real-world applications and insights."
    }.get(audience, "Write clearly and appropriately for a general audience.")

    # ---------------------------------------------
    # 4️⃣ Depth and tone modifiers
    # ---------------------------------------------
    depth_hint = {
        "concise": "Be brief and to the point; only essential ideas.",
        "balanced": "Provide key ideas with short supporting explanations.",
        "in-depth": "Expand on reasoning, relationships, and examples in detail."
    }.get(depth, "Provide moderate detail — key ideas with short supporting notes.")

    tone_hint = {
        "neutral": "Maintain an objective, academic tone.",
        "friendly": "Use a warm, encouraging tone while staying professional.",
        "formal": "Use polished, formal academic phrasing.",
        "academic": "Adopt a scholarly tone with precise terminology."
    }.get(tone, "Maintain an objective, academic tone.")

    # ---------------------------------------------
    # 5️⃣ Optional extras
    # ---------------------------------------------
    extra_instructions = []
    if extras:
        if "summary" in extras:
            extra_instructions.append(
                "At the end, include a #SECTION Summary with 3–5 #POINT key takeaways."
            )
        if "highlight_terms" in extras:
            extra_instructions.append(
                "Emphasize critical terms using ALL CAPS (e.g., DATABASE, NORMALIZATION)."
            )
        if "glossary" in extras:
            extra_instructions.append(
                "Include a #SECTION Glossary with concise definitions for key terms."
            )

    # ---------------------------------------------
    # 6️⃣ Combine all prompt parts
    # ---------------------------------------------
    final_prompt = (
        f"{base_intro}{text[:6000]}\n\n"
        f"{style_instructions}\n\n"
        f"{audience_hint}\n"
        f"{depth_hint}\n"
        f"{tone_hint}\n"
        f"{' '.join(extra_instructions)}"
    )

    return final_prompt


async def generate_notes_from_llm(text, style):
    """Generate AI-structured notes asynchronously and normalize output."""
    prompt = build_prompt(text, style)

    response = await asyncio.to_thread(
        lambda: client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise academic assistant that outputs notes strictly in EasyNote Markup (ENM) format."
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.65,
        )
    )

    raw_output = response.choices[0].message.content.strip()
    normalized = normalize_llm_text(raw_output)
    return normalized
