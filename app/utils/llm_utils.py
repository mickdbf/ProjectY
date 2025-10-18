# app/utils/llm_utils.py
import os, asyncio
from openai import OpenAI

# Initialize modern OpenAI client (uses OPENAI_API_KEY from environment)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def build_prompt(text, style):
    """Constructs a context-aware LLM prompt based on note style."""
    base = f"Convert the following lecture slides into study notes:\n\n{text[:6000]}"
    if style == "outline":
        base += "\n\nReturn concise bullet points organized by topic."
    elif style == "detailed":
        base += "\n\nWrite detailed study notes with explanations and examples."
    elif style == "cheatsheet":
        base += "\n\nCreate a compact cheat sheet highlighting formulas, terms, and facts."
    else:
        base += "\n\nGenerate clear, useful notes summarizing the main ideas."
    return base


async def generate_notes_from_llm(text, style):
    """Processes slide text with LLM asynchronously."""
    prompt = build_prompt(text, style)

    # Run the blocking API call in a thread so FastAPI’s event loop isn’t blocked
    response = await asyncio.to_thread(
        lambda: client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful academic assistant that creates well-structured notes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
    )

    return response.choices[0].message.content.strip()
