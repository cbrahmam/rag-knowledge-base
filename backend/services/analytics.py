"""Lightweight query analytics.

Every answered question is appended to a JSON log so we can show usage
metrics (volume, latency, confidence mix) and a recent-question history.
Storage is a flat JSON file — fine for the local/single-user scope of the
app; a production deployment would swap this for a real datastore.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from models.schemas import RAGResponse, QueryRecord, AnalyticsSummary

logger = logging.getLogger(__name__)

ANALYTICS_STORE = Path(__file__).parent.parent / "analytics_store.json"
MAX_RECORDS = 1000


def _load() -> List[dict]:
    if ANALYTICS_STORE.exists():
        try:
            with open(ANALYTICS_STORE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            logger.warning("analytics store unreadable; starting fresh")
    return []


def _save(records: List[dict]) -> None:
    with open(ANALYTICS_STORE, "w") as f:
        json.dump(records[-MAX_RECORDS:], f, indent=2)


def log_query(question: str, response: RAGResponse) -> None:
    """Append one answered query. Never raises — analytics must not break a query."""
    try:
        records = _load()
        records.append(QueryRecord(
            question=question,
            confidence=response.confidence,
            processing_time_ms=response.processing_time_ms,
            chunks_searched=response.chunks_searched,
            source_count=len(response.sources),
            timestamp=datetime.now(timezone.utc).isoformat(),
        ).model_dump())
        _save(records)
    except Exception as e:  # pragma: no cover - best-effort logging
        logger.warning("failed to log query analytics: %s", e)


def get_history(limit: int = 50) -> List[QueryRecord]:
    records = _load()
    recent = list(reversed(records))[:limit]
    return [QueryRecord(**r) for r in recent]


def get_summary(recent_limit: int = 10) -> AnalyticsSummary:
    records = _load()
    total = len(records)

    distribution = {"high": 0, "medium": 0, "low": 0}
    for r in records:
        distribution[r.get("confidence", "low")] = distribution.get(r.get("confidence", "low"), 0) + 1

    avg_time = round(sum(r["processing_time_ms"] for r in records) / total) if total else 0
    avg_sources = round(sum(r["source_count"] for r in records) / total, 1) if total else 0.0

    recent = [QueryRecord(**r) for r in reversed(records[-recent_limit:])]

    return AnalyticsSummary(
        total_queries=total,
        avg_processing_time_ms=avg_time,
        avg_source_count=avg_sources,
        confidence_distribution=distribution,
        recent=recent,
    )


def clear_history() -> int:
    count = len(_load())
    _save([])
    return count
