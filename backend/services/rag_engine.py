from __future__ import annotations

import json
import logging
import os
import time
from typing import List, Optional

import anthropic

from models.schemas import SearchResult, SourceCitation, RAGResponse
from services.embeddings import generate_embeddings
from services.vector_store import search
from services import analytics

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a knowledgeable assistant that answers questions based ONLY on the provided context documents. "
    "If the context doesn't contain enough information to answer the question, say so clearly. "
    "Always cite which document and section your answer comes from."
)

SIMILARITY_THRESHOLD = 0.3


def _build_context_prompt(
    question: str,
    results: List[SearchResult],
    conversation_context: Optional[List[dict]] = None,
) -> str:
    context_parts = []
    for r in results:
        page_info = f", Page: {r.source_page}" if r.source_page else ""
        context_parts.append(f"[Source: {r.source_document}{page_info}]\n{r.text}")

    context_block = "\n---\n".join(context_parts)

    conversation_section = ""
    if conversation_context:
        pairs = []
        for item in conversation_context[-5:]:
            pairs.append(f"Q: {item.get('question', '')}\nA: {item.get('answer', '')}")
        conversation_section = f"\nPrevious conversation:\n{'---'.join(pairs)}\n"

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


def _get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
    return anthropic.Anthropic(api_key=api_key)


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
) -> RAGResponse:
    start_time = time.time()

    query_embedding = generate_embeddings([question])[0]
    results = search(query_embedding, n_results=5)

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

    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6-20250514",
        max_tokens=1024,
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
