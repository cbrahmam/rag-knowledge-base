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


DEFAULT_COLLECTION = "General"


class DocumentUploadResponse(BaseModel):
    filename: str
    file_type: str
    total_chunks: int
    total_characters: int
    status: str
    message: str
    collection: str = DEFAULT_COLLECTION


class DocumentListItem(BaseModel):
    filename: str
    file_type: str
    total_chunks: int
    uploaded_at: str
    size_bytes: int
    collection: str = DEFAULT_COLLECTION


class CollectionInfo(BaseModel):
    name: str
    document_count: int
    chunk_count: int


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
    search_mode: str = "hybrid"  # "hybrid" | "semantic" | "keyword"
    alpha: float = 0.5  # hybrid blend weight: 1.0=semantic, 0.0=keyword
    collection: Optional[str] = None  # scope retrieval to one collection


class MultiQueryRequest(BaseModel):
    questions: List[str]


class QueryRecord(BaseModel):
    question: str
    confidence: str
    processing_time_ms: int
    chunks_searched: int
    source_count: int
    timestamp: str


class AnalyticsSummary(BaseModel):
    total_queries: int
    avg_processing_time_ms: int
    avg_source_count: float
    confidence_distribution: dict
    recent: List[QueryRecord]


class DocumentSummary(BaseModel):
    filename: str
    summary: str
    key_points: List[str]
    suggested_questions: List[str]
    cached: bool = False
