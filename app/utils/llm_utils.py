import os, asyncio
from openai import OpenAI
from app.utils.text_utils import normalize_llm_text

# Initialize modern OpenAI client (uses OPENAI_API_KEY from environment)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def build_prompt(text, style):
    """
    Construct a prompt that guarantees structured, machine-readable note output.
    The model must emit lines that begin with '#SECTION' for section titles
    and '-' for bullets or key:value pairs.
    """

    base_intro = (
        "You are EasyNote AI, an assistant that transforms lecture slides into "
        "well-organized, student-friendly notes for college study.\n\n"
        "FORMAT RULES (follow exactly):\n"
        "- Output plain text only — no Markdown, emojis, or decorative symbols.\n"
        "- Each major topic MUST start with '#SECTION ' followed by the section name.\n"
        "- Inside each section, use '- ' for bullet lines or 'Key: Value' pairs.\n"
        "- Leave one blank line between sections.\n"
        "- Do NOT include any dividers like --- or =====.\n"
        "- Keep the format strictly structured — this text will be parsed by software.\n\n"
        "Here is the lecture content:\n\n"
    )

    if style == "outline":
        style_instructions = (
            "Summarize the material as an academic outline with clear #SECTION headers "
            "and concise bullet points under each."
        )
    elif style == "detailed":
        style_instructions = (
            "Write detailed, structured notes in full sentences under each #SECTION header, "
            "but still follow the exact '#SECTION' and '-' format."
        )
    elif style == "cheatsheet":
        style_instructions = (
            "Produce a compact cheat sheet using '#SECTION' headers and short 'Term: Definition' lines. "
            "Keep it concise and readable."
        )
    else:
        style_instructions = (
            "Organize content into '#SECTION' headers and '-' bullet lines."
        )

    return f"{base_intro}{text[:6000]}\n\n{style_instructions}"


async def generate_notes_from_llm(text, style):
    """Processes slide text with LLM asynchronously and normalizes output."""
    prompt = build_prompt(text, style)

    # Run the blocking API call in a thread so FastAPI’s event loop isn’t blocked
    response = await asyncio.to_thread(
        lambda: client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful academic assistant that creates well-structured notes."
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
    )

    raw_output = response.choices[0].message.content.strip()
    normalized = normalize_llm_text(raw_output)
    return normalized
