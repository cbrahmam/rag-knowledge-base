from __future__ import annotations

from pydantic import BaseModel
from typing import List, Optional


class Chunk(BaseModel):
    text: str
    chunk_index: int
    start_char: int
    end_char: int
    source_document: str
    source_page: Optional[int] = None


class ParsedDocument(BaseModel):
    filename: str
    file_type: str
    total_pages: Optional[int] = None
    total_characters: int
    text_content: str
    pages: Optional[List[dict]] = None


class DocumentUploadResponse(BaseModel):
    filename: str
    file_type: str
    total_chunks: int
    total_characters: int
    status: str
    message: str


class DocumentListItem(BaseModel):
    filename: str
    file_type: str
    total_chunks: int
    uploaded_at: str
    size_bytes: int
