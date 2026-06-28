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


class SearchResult(BaseModel):
    text: str
    source_document: str
    source_page: Optional[int] = None
    chunk_index: int
    similarity_score: float


class SourceCitation(BaseModel):
    document: str
    page: Optional[int] = None
    chunk_text: str
    relevance_score: float


class RAGResponse(BaseModel):
    answer: str
    sources: List[SourceCitation]
    confidence: str
    chunks_searched: int
    processing_time_ms: int


class QueryRequest(BaseModel):
    question: str
    context: Optional[List[dict]] = None


class MultiQueryRequest(BaseModel):
    questions: List[str]


class DocumentContent(BaseModel):
    filename: str
    file_type: str
    total_characters: int
    total_pages: Optional[int] = None
    content: str
