from __future__ import annotations

import re
from typing import List, Optional

from models.schemas import Chunk


SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")
MARKDOWN_HEADING = re.compile(r"^#{1,6}\s", re.MULTILINE)

# Per-content-type chunking defaults. Denser, well-structured formats
# (Markdown) tolerate larger chunks; flat prose stays smaller for tighter
# retrieval. (chunk_size, overlap) in characters.
ADAPTIVE_PARAMS = {
    "md": (800, 100),
    "pdf": (600, 80),
    "docx": (600, 80),
    "txt": (500, 50),
}
DEFAULT_PARAMS = (500, 50)


def adaptive_params(file_type: str) -> tuple[int, int]:
    """Return the (chunk_size, overlap) defaults for a file type."""
    return ADAPTIVE_PARAMS.get(file_type, DEFAULT_PARAMS)


def _split_markdown_sections(text: str) -> List[str]:
    """Split Markdown at heading boundaries so chunks respect section structure."""
    starts = [m.start() for m in MARKDOWN_HEADING.finditer(text)]
    if not starts:
        return [text]

    sections: List[str] = []
    if starts[0] > 0 and text[: starts[0]].strip():
        sections.append(text[: starts[0]])
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(text)
        sections.append(text[start:end])
    return sections


def chunk_document(
    text: str,
    source_document: str,
    file_type: str,
    source_pages: Optional[List[dict]] = None,
    chunk_size: Optional[int] = None,
    overlap: Optional[int] = None,
) -> List[Chunk]:
    """Content-type-aware chunking.

    Picks size/overlap defaults per file type (overridable), and for
    Markdown chunks each heading-delimited section independently so chunks
    don't straddle sections.
    """
    size, ov = adaptive_params(file_type)
    if chunk_size:
        size = chunk_size
    if overlap is not None:
        ov = overlap

    if file_type == "md":
        chunks: List[Chunk] = []
        for section in _split_markdown_sections(text):
            chunks.extend(chunk_text(section, source_document, size, ov, source_pages))
        for idx, c in enumerate(chunks):
            c.chunk_index = idx
        return chunks

    return chunk_text(text, source_document, size, ov, source_pages)


def chunk_text(
    text: str,
    source_document: str,
    chunk_size: int = 500,
    overlap: int = 50,
    source_pages: Optional[List[dict]] = None,
) -> List[Chunk]:
    if not text.strip():
        return []

    sentences = SENTENCE_BOUNDARY.split(text)
    chunks: list[Chunk] = []
    current_chunk: list[str] = []
    current_length = 0
    chunk_start = 0
    char_pos = 0

    for sentence in sentences:
        sentence_len = len(sentence)

        if current_length + sentence_len > chunk_size and current_chunk:
            chunk_text_str = " ".join(current_chunk)
            chunk_end = chunk_start + len(chunk_text_str)

            chunks.append(Chunk(
                text=chunk_text_str,
                chunk_index=len(chunks),
                start_char=chunk_start,
                end_char=chunk_end,
                source_document=source_document,
                source_page=_find_page(chunk_start, source_pages),
            ))

            overlap_text = ""
            overlap_sentences: list[str] = []
            for s in reversed(current_chunk):
                if len(overlap_text) + len(s) > overlap:
                    break
                overlap_sentences.insert(0, s)
                overlap_text = " ".join(overlap_sentences)

            current_chunk = overlap_sentences
            current_length = len(overlap_text)
            chunk_start = chunk_end - len(overlap_text)

        current_chunk.append(sentence)
        current_length += sentence_len
        char_pos += sentence_len

    if current_chunk:
        chunk_text_str = " ".join(current_chunk)
        chunks.append(Chunk(
            text=chunk_text_str,
            chunk_index=len(chunks),
            start_char=chunk_start,
            end_char=chunk_start + len(chunk_text_str),
            source_document=source_document,
            source_page=_find_page(chunk_start, source_pages),
        ))

    return chunks


def _find_page(char_pos: int, pages: Optional[List[dict]] = None) -> Optional[int]:
    if not pages:
        return None

    running = 0
    for page in pages:
        page_len = len(page["text"])
        if running + page_len > char_pos:
            return page["page_number"]
        running += page_len + 1

    return pages[-1]["page_number"] if pages else None
