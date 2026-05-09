from __future__ import annotations

import re
from typing import List, Optional

from models.schemas import Chunk


SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


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
