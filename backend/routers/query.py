from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException

from models.schemas import RAGResponse, QueryRequest, MultiQueryRequest
from services.rag_engine import query
from services.vector_store import get_stats

router = APIRouter(prefix="/api/query", tags=["query"])


@router.post("", response_model=RAGResponse)
async def ask_question(request: QueryRequest):
    stats = get_stats()
    if stats["total_chunks"] == 0:
        raise HTTPException(
            status_code=400,
            detail="No documents uploaded yet. Please upload documents before asking questions.",
        )

    return query(request.question, request.context)


@router.post("/multi", response_model=List[RAGResponse])
async def ask_multiple_questions(request: MultiQueryRequest):
    if len(request.questions) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 questions per request")

    stats = get_stats()
    if stats["total_chunks"] == 0:
        raise HTTPException(
            status_code=400,
            detail="No documents uploaded yet. Please upload documents before asking questions.",
        )

    responses = []
    for question in request.questions:
        response = query(question)
        responses.append(response)
    return responses
