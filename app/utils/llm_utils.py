import os, asyncio
from openai import OpenAI
from app.utils.text_utils import normalize_llm_text

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def build_prompt(text, style, audience="college", depth="balanced", tone="neutral", extras=None):
    """
    Construct a prompt that guarantees structured, machine-readable note output
    using EasyNote Markup (ENM) syntax.

    Parameters:
    - text: raw lecture or slide text
    - style: output style ("outline", "detailed", "cheatsheet")
    - audience: intended reader ("college", "beginner", "researcher", "professional")
    - depth: content depth ("concise", "balanced", "in-depth")
    - tone: writing tone ("neutral", "friendly", "formal", "academic")
    - extras: optional list of extra behaviors (["summary", "highlight_terms"])
    """

    # ---------------------------------------------
    # 1️⃣ Base format rules (ENM spec)
    # ---------------------------------------------
    base_intro = (
        "You are EasyNote AI, an assistant that transforms lecture slides into "
        "well-organized, student-friendly notes for college study.\n\n"
        "OUTPUT FORMAT — EASYNOTE MARKUP (ENM):\n"
        "Use the following tags exactly:\n"
        "  #SECTION <name>        → major topic header\n"
        "  #SUBSECTION <name>     → subtopic header\n"
        "  #POINT <text>          → bullet or key/value item\n"
        "  #NOTE <text>           → short paragraph or explanation\n"
        "  #CODE / #ENDCODE       → wrap any code examples\n"
        "  #DIVIDER               → horizontal break (used sparingly)\n"
        "  #QUOTE <text>          → quote or emphasized statement\n"
        "\n"
        "RULES:\n"
        "- Output plain text only (no Markdown, emojis, or decorative symbols).\n"
        "- Each tag must appear on its own line.\n"
        "- Leave one blank line between sections.\n"
        "- Do NOT include --- lines, emojis, or decorative formatting.\n"
        "- Keep the format strictly structured; this text will be parsed by software.\n\n"
        "Here is the lecture content:\n\n"
    )

    # ---------------------------------------------
    # 2️⃣ Style-specific instructions
    # ---------------------------------------------
    style_instructions = {
        "outline": (
            "Summarize the material hierarchically. "
            "Use #SECTION for main topics, #SUBSECTION for subtopics, "
            "and #POINT for concise key ideas or facts."
        ),
        "detailed": (
            "Write comprehensive notes. "
            "Use #SECTION for main topics, #SUBSECTION for subtopics, "
            "#POINT for facts, and #NOTE for explanations. "
            "Include examples using #CODE / #ENDCODE when applicable."
        ),
        "cheatsheet": (
            "Create a compact cheat sheet. "
            "Use #SECTION headers and #POINT lines for terms, definitions, or formulas. "
            "Keep it tightly formatted and scannable."
        ),
    }.get(style, "Use #SECTION headers and #POINT lines with optional #NOTE paragraphs.")

    # ---------------------------------------------
    # 3️⃣ Audience context
    # ---------------------------------------------
    if audience == "beginner":
        audience_hint = "Write for beginners. Use simple language and short explanations."
    elif audience == "college":
        audience_hint = "Write for undergraduate students. Use clear examples and moderate technicality."
    elif audience == "researcher":
        audience_hint = "Write for researchers. Use precise academic phrasing and retain formal structure."
    elif audience == "professional":
        audience_hint = "Write for professionals. Focus on practical applications and advanced terminology."
    else:
        audience_hint = "Write clearly and appropriately for a general audience."

    # ---------------------------------------------
    # 4️⃣ Depth and tone modifiers
    # ---------------------------------------------
    depth_map = {
        "concise": "Be brief and to the point. Summarize essential ideas only.",
        "balanced": "Provide moderate detail — key ideas with short supporting notes.",
        "in-depth": "Include detailed explanations, rationale, and examples where relevant."
    }
    tone_map = {
        "neutral": "Maintain an objective and academic tone.",
        "friendly": "Use a warm, encouraging tone while remaining professional.",
        "formal": "Maintain formal academic language.",
        "academic": "Adopt scholarly tone, avoid casual expressions."
    }

    depth_hint = depth_map.get(depth, depth_map["balanced"])
    tone_hint = tone_map.get(tone, tone_map["neutral"])

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
                "Emphasize important terms using ALL CAPS (e.g., DATABASE, NORMALIZATION)."
            )
        if "glossary" in extras:
            extra_instructions.append(
                "Include a final #SECTION Glossary listing key terms and short definitions."
            )

    extra_text = "\n".join(extra_instructions)

    # ---------------------------------------------
    # 6️⃣ Combine everything
    # ---------------------------------------------
    final_prompt = (
        f"{base_intro}{text[:6000]}\n\n"
        f"{style_instructions}\n\n"
        f"{audience_hint}\n"
        f"{depth_hint}\n"
        f"{tone_hint}\n"
        f"{extra_text}"
    )

    return final_prompt



async def generate_notes_from_llm(text, style):
    """Processes slide text with LLM asynchronously and normalizes output."""
    prompt = build_prompt(text, style)

    response = await asyncio.to_thread(
        lambda: client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful academic assistant that creates structured notes in EasyNote Markup (ENM) format."
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
    )

    raw_output = response.choices[0].message.content.strip()
    normalized = normalize_llm_text(raw_output)
    return normalized
