from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
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
    chunk_size: Optional[int] = None
    overlap: Optional[int] = None


class DocumentListItem(BaseModel):
    filename: str
    file_type: str
    total_chunks: int
    uploaded_at: str
    size_bytes: int
    collection: str = DEFAULT_COLLECTION
    tags: List[str] = []


class CollectionInfo(BaseModel):
    name: str
    document_count: int
    chunk_count: int


class TagUpdateRequest(BaseModel):
    tags: List[str]


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
    question: str = Field(min_length=1, max_length=2000)
    context: Optional[List[dict]] = None
    search_mode: str = "hybrid"  # "hybrid" | "semantic" | "keyword"
    alpha: float = Field(default=0.5, ge=0.0, le=1.0)  # 1.0=semantic, 0.0=keyword
    collection: Optional[str] = None  # scope retrieval to one collection
    n_results: int = Field(default=5, ge=1, le=20)  # chunks to retrieve

    @field_validator("question")
    @classmethod
    def _strip_question(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("question must not be empty")
        return v

    @field_validator("search_mode")
    @classmethod
    def _valid_mode(cls, v: str) -> str:
        if v not in {"hybrid", "semantic", "keyword"}:
            raise ValueError("search_mode must be hybrid, semantic or keyword")
        return v


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


class FeedbackRequest(BaseModel):
    question: str
    answer: str
    rating: str  # "up" | "down"
    confidence: Optional[str] = None
    comment: Optional[str] = None


class FeedbackSummary(BaseModel):
    total: int
    up: int
    down: int
    satisfaction_rate: float  # 0-100, share of rated answers that are positive


class ConversationCreate(BaseModel):
    title: Optional[str] = None
    messages: List[dict]


class SavedConversation(BaseModel):
    id: str
    title: str
    messages: List[dict]
    created_at: str
    updated_at: str


class ConversationListItem(BaseModel):
    id: str
    title: str
    message_count: int
    updated_at: str


class DocumentContent(BaseModel):
    filename: str
    file_type: str
    total_characters: int
    total_pages: Optional[int] = None
    content: str
