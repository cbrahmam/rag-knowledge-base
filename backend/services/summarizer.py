"""Document summarization and auto-generated FAQ.

Given a document's indexed chunks, asks Claude for a short summary, a few
key points, and suggested starter questions. Used to give users a quick
overview of a document and a jumping-off point for asking questions.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import List

import anthropic

from models.schemas import DocumentSummary

logger = logging.getLogger(__name__)

# Cap the context we send so summarizing a large doc stays cheap and fast.
MAX_CONTEXT_CHARS = 12000

SYSTEM_PROMPT = (
    "You are a precise document analyst. You produce concise overviews of "
    "documents and propose useful questions a reader might ask about them."
)


def _get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
    return anthropic.Anthropic(api_key=api_key)


def _build_prompt(filename: str, text: str) -> str:
    return f"""Document: {filename}

Content:
---
{text}
---

Produce a JSON object with exactly these fields:
- "summary": a 2-3 sentence overview of what this document is about
- "key_points": an array of 3-5 short strings capturing the most important points
- "suggested_questions": an array of 3-5 natural questions a reader could ask, answerable from this document

Return ONLY the JSON object, no prose before or after."""


def _parse_response(raw: str, filename: str) -> DocumentSummary:
    # Models occasionally wrap JSON in a ```json fence; strip it if present.
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    data = json.loads(cleaned)
    return DocumentSummary(
        filename=filename,
        summary=data.get("summary", "").strip(),
        key_points=[str(p).strip() for p in data.get("key_points", []) if str(p).strip()],
        suggested_questions=[str(q).strip() for q in data.get("suggested_questions", []) if str(q).strip()],
    )


def summarize_document(filename: str, chunks: List[str]) -> DocumentSummary:
    if not chunks:
        raise ValueError("Document has no indexed content to summarize")

    text = "\n\n".join(chunks)
    if len(text) > MAX_CONTEXT_CHARS:
        text = text[:MAX_CONTEXT_CHARS] + "\n\n[... truncated ...]"

    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6-20250514",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_prompt(filename, text)}],
    )

    raw = response.content[0].text
    try:
        return _parse_response(raw, filename)
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("failed to parse summary JSON for %s: %s", filename, e)
        # Fall back to the raw text as the summary so the user still gets something.
        return DocumentSummary(
            filename=filename,
            summary=raw.strip()[:500],
            key_points=[],
            suggested_questions=[],
        )
