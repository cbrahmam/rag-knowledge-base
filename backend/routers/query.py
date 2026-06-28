from __future__ import annotations

import json
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from models.schemas import RAGResponse, QueryRequest, MultiQueryRequest
from services.rag_engine import query, query_stream
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

    try:
        return query(request.question, request.context, request.search_mode, request.alpha, request.collection)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def ask_question_stream(request: QueryRequest):
    """Stream a RAG answer as Server-Sent Events.

    Emits one ``data:`` line per event. Token events carry incremental text;
    the final ``done`` event carries sources, confidence and timing.
    """
    stats = get_stats()
    if stats["total_chunks"] == 0:
        raise HTTPException(
            status_code=400,
            detail="No documents uploaded yet. Please upload documents before asking questions.",
        )

    def event_generator():
        try:
            for event in query_stream(request.question, request.context, request.search_mode, request.alpha, request.collection):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:  # surface errors to the client as an SSE event
            yield f"data: {json.dumps({'type': 'error', 'detail': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


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

    try:
        responses = []
        for question in request.questions:
            response = query(question)
            responses.append(response)
        return responses
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
