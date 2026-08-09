"""
ai_service.py — Part 3: LLM-powered assistance.

Updated for the new schema: Note has title + content + tag (single string).

Exports
-------
get_ai_response(note, question)   — free-form Q&A about a note
suggest_tag(title, content)       — suggest a single tag string
summarise_note(note)              — one-sentence summary
classify_tag(title, content)      — predict best tag for raw text
generate_next_action(note)        — next-action suggestion
"""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

KNOWN_TAGS = ["work", "health", "recipes", "travel", "random"]


# ---------------------------------------------------------------------------
# 5-part prompt template
# ---------------------------------------------------------------------------

PROMPT_TEMPLATE = """\
You are a helpful personal notes assistant.

[NOTE]
Title:   {title}
Tag:     {tag}
Content:
{content}

[TASK]
{task}

[CONSTRAINTS]
- Be concise and practical.
- Use bullet points where appropriate.
- Do not invent details not present in the note.

[FORMAT]
{format_instruction}

[RESPONSE]"""


def _build_prompt(note, task: str, fmt: str) -> str:
    return PROMPT_TEMPLATE.format(
        title=note.title,
        tag=note.tag or "(none)",
        content=note.content,
        task=task,
        format_instruction=fmt,
    )


async def _call_openai(prompt: str, max_tokens: int = 256) -> Optional[str]:
    if not OPENAI_API_KEY:
        logger.info("OPENAI_API_KEY not set — AI features disabled.")
        return None
    try:
        from openai import AsyncOpenAI  # type: ignore
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        resp = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        logger.warning("OpenAI call failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def get_ai_response(note, question: str) -> str:
    """Ask the LLM an arbitrary question about the note."""
    prompt = _build_prompt(
        note,
        task=f"Answer this question about the note:\n{question}",
        fmt="Plain prose, 3–5 sentences maximum.",
    )
    return await _call_openai(prompt, max_tokens=300) or \
        "AI assistance unavailable (OPENAI_API_KEY not configured)."


async def suggest_tag(title: str, content: str) -> str:
    """
    Suggest the single best tag for a note.
    Tries to pick from known tags: work, health, recipes, travel, random.
    Returns empty string when AI is unavailable.
    """
    class _FakeNote:
        tag = ""
    fake = _FakeNote()
    fake.title   = title
    fake.content = content

    prompt = _build_prompt(
        fake,
        task=(
            f"Choose the single best tag for this note from: {', '.join(KNOWN_TAGS)}. "
            "If none fit well, suggest a short lowercase single-word tag."
        ),
        fmt='Respond with ONLY the tag word, e.g. "work" or "health".',
    )
    raw = await _call_openai(prompt, max_tokens=10)
    if raw:
        tag = raw.strip().lower().split()[0]
        return tag[:64]
    return ""


async def summarise_note(note) -> str:
    """One-sentence summary of the note."""
    prompt = _build_prompt(
        note,
        task="Write a single-sentence summary of this note.",
        fmt="One sentence, ≤ 25 words.",
    )
    return await _call_openai(prompt, max_tokens=64) or "Summary unavailable."


async def classify_tag(title: str, content: str) -> str:
    """Predict the best tag for raw title + content. Returns 'unknown' on failure."""
    class _FakeNote:
        tag = ""
    fake = _FakeNote()
    fake.title   = title
    fake.content = content

    prompt = _build_prompt(
        fake,
        task=(
            f"Classify this note with the single best tag from: {', '.join(KNOWN_TAGS)}."
        ),
        fmt='Respond with ONLY the tag word, e.g. "recipes".',
    )
    raw = await _call_openai(prompt, max_tokens=10)
    if raw:
        tag = raw.strip().lower().split()[0]
        return tag[:64]
    return "unknown"


async def generate_next_action(note) -> str:
    """Suggest the single most useful next action based on the note content."""
    prompt = _build_prompt(
        note,
        task="What is the single most useful next action based on this note?",
        fmt="One bullet point, ≤ 20 words.",
    )
    return await _call_openai(prompt, max_tokens=64) or "Next-action generation unavailable."
