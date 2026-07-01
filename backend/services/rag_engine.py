from __future__ import annotations

import json
import logging
import time
from typing import Iterator, List, Optional

from config import (
    ANTHROPIC_MODEL,
    DEFAULT_N_RESULTS,
    MAX_N_RESULTS,
    MAX_TOKENS,
    SIMILARITY_THRESHOLD,
)
from models.schemas import RAGResponse, SearchResult, SourceCitation
from services import analytics
from services.embeddings import generate_embeddings
from services.llm import get_client
from services.vector_store import hybrid_search, keyword_search, search


def _retrieve(
    question: str,
    search_mode: str,
    alpha: float,
    collection: Optional[str] = None,
    n_results: int = DEFAULT_N_RESULTS,
) -> List[SearchResult]:
    """Dispatch retrieval to the selected strategy, optionally scoped to a collection.

    ``n_results`` controls how many chunks are retrieved (clamped to a sane range).
    """
    n_results = max(1, min(n_results, MAX_N_RESULTS))
    if search_mode == "keyword":
        return keyword_search(question, n_results=n_results, collection_name=collection)

    query_embedding = generate_embeddings([question])[0]
    if search_mode == "semantic":
        return search(query_embedding, n_results=n_results, collection_name=collection)
    return hybrid_search(question, query_embedding, n_results=n_results, alpha=alpha, collection_name=collection)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a knowledgeable assistant that answers questions based ONLY on the provided context documents. "
    "If the context doesn't contain enough information to answer the question, say so clearly. "
    "Always cite which document and section your answer comes from."
)


def _format_context(results: List[SearchResult]) -> str:
    parts = []
    for r in results:
        page_info = f", Page: {r.source_page}" if r.source_page else ""
        parts.append(f"[Source: {r.source_document}{page_info}]\n{r.text}")
    return "\n---\n".join(parts)


def _format_conversation(conversation_context: Optional[List[dict]]) -> str:
    if not conversation_context:
        return ""
    pairs = [
        f"Q: {item.get('question', '')}\nA: {item.get('answer', '')}"
        for item in conversation_context[-5:]
    ]
    return f"\nPrevious conversation:\n{'---'.join(pairs)}\n"


def _build_context_prompt(
    question: str,
    results: List[SearchResult],
    conversation_context: Optional[List[dict]] = None,
) -> str:
    context_block = _format_context(results)
    conversation_section = _format_conversation(conversation_context)

    return f"""Context documents:
---
{context_block}
---
{conversation_section}
Question: {question}

Instructions:
- Answer based ONLY on the context above
- Cite sources using [Source: filename] format
- If the context doesn't contain the answer, say "I couldn't find information about this in the uploaded documents"
- Be concise but thorough
- Return your response as JSON with fields: answer, sources (list of filenames used), confidence (high/medium/low)"""


def _build_streaming_prompt(
    question: str,
    results: List[SearchResult],
    conversation_context: Optional[List[dict]] = None,
) -> str:
    """Prompt variant for streaming: asks for a direct prose answer.

    Unlike the non-streaming path, we don't ask Claude to wrap the answer in
    JSON — that would force us to buffer the whole response before parsing.
    Sources and confidence are computed on the backend from the retrieved
    chunks, so the model only needs to produce the answer text.
    """
    context_block = _format_context(results)
    conversation_section = _format_conversation(conversation_context)

    return f"""Context documents:
---
{context_block}
---
{conversation_section}
Question: {question}

Instructions:
- Answer based ONLY on the context above
- Cite sources inline using [Source: filename] format
- If the context doesn't contain the answer, say "I couldn't find information about this in the uploaded documents"
- Be concise but thorough
- Write a direct, well-formatted answer (Markdown allowed). Do NOT wrap it in JSON."""


def _determine_confidence(results: List[SearchResult]) -> str:
    if not results:
        return "low"
    top_score = results[0].similarity_score
    if top_score > 0.7:
        return "high"
    elif top_score > 0.5:
        return "medium"
    return "low"


def query(
    question: str,
    conversation_context: Optional[List[dict]] = None,
    search_mode: str = "hybrid",
    alpha: float = 0.5,
    collection: Optional[str] = None,
    n_results: int = DEFAULT_N_RESULTS,
) -> RAGResponse:
    start_time = time.time()

    results = _retrieve(question, search_mode, alpha, collection, n_results)

    relevant_results = [r for r in results if r.similarity_score >= SIMILARITY_THRESHOLD]

    if not relevant_results:
        elapsed = int((time.time() - start_time) * 1000)
        no_match = RAGResponse(
            answer="I couldn't find information about this in the uploaded documents.",
            sources=[],
            confidence="low",
            chunks_searched=len(results),
            processing_time_ms=elapsed,
        )
        analytics.log_query(question, no_match)
        return no_match

    prompt = _build_context_prompt(question, relevant_results, conversation_context)

    client = get_client()
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_answer = response.content[0].text

    try:
        parsed = json.loads(raw_answer)
        answer_text = parsed.get("answer", raw_answer)
    except json.JSONDecodeError:
        answer_text = raw_answer

    sources = [
        SourceCitation(
            document=r.source_document,
            page=r.source_page,
            chunk_text=r.text[:200],
            relevance_score=r.similarity_score,
        )
        for r in relevant_results
    ]

    elapsed = int((time.time() - start_time) * 1000)
    confidence = _determine_confidence(relevant_results)

    response = RAGResponse(
        answer=answer_text,
        sources=sources,
        confidence=confidence,
        chunks_searched=len(results),
        processing_time_ms=elapsed,
    )
    analytics.log_query(question, response)
    return response


def query_stream(
    question: str,
    conversation_context: Optional[List[dict]] = None,
    search_mode: str = "hybrid",
    alpha: float = 0.5,
    collection: Optional[str] = None,
    n_results: int = DEFAULT_N_RESULTS,
) -> Iterator[dict]:
    """Stream a RAG answer token-by-token.

    Yields a sequence of event dicts:
      {"type": "token", "text": ...}   — one per streamed text delta
      {"type": "done", ...}            — final event with sources + metadata

    The retrieval step is identical to ``query`` (honoring search_mode/alpha
    and the optional collection); only generation streams. Each answered
    query is recorded to analytics, same as the non-streaming path.
    """
    start_time = time.time()

    results = _retrieve(question, search_mode, alpha, collection, n_results)
    relevant_results = [r for r in results if r.similarity_score >= SIMILARITY_THRESHOLD]

    if not relevant_results:
        elapsed = int((time.time() - start_time) * 1000)
        fallback = "I couldn't find information about this in the uploaded documents."
        analytics.log_query(question, RAGResponse(
            answer=fallback, sources=[], confidence="low",
            chunks_searched=len(results), processing_time_ms=elapsed,
        ))
        yield {"type": "token", "text": fallback}
        yield {
            "type": "done",
            "sources": [],
            "confidence": "low",
            "chunks_searched": len(results),
            "processing_time_ms": elapsed,
        }
        return

    prompt = _build_streaming_prompt(question, relevant_results, conversation_context)
    client = get_client()

    with client.messages.stream(
        model=ANTHROPIC_MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            yield {"type": "token", "text": text}

    citations = [
        SourceCitation(
            document=r.source_document,
            page=r.source_page,
            chunk_text=r.text[:200],
            relevance_score=r.similarity_score,
        )
        for r in relevant_results
    ]
    confidence = _determine_confidence(relevant_results)
    elapsed = int((time.time() - start_time) * 1000)

    analytics.log_query(question, RAGResponse(
        answer="", sources=citations, confidence=confidence,
        chunks_searched=len(results), processing_time_ms=elapsed,
    ))

    yield {
        "type": "done",
        "sources": [c.model_dump() for c in citations],
        "confidence": confidence,
        "chunks_searched": len(results),
        "processing_time_ms": elapsed,
    }
