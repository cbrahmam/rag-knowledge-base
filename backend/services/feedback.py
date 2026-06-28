"""Answer feedback collection.

Records thumbs-up / thumbs-down on answers so we can track answer quality
over time and surface a satisfaction rate. Storage is a flat JSON file,
matching the rest of the app's local-first scope.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from models.schemas import FeedbackRequest, FeedbackSummary

logger = logging.getLogger(__name__)

FEEDBACK_STORE = Path(__file__).parent.parent / "feedback_store.json"
MAX_RECORDS = 2000


def _load() -> List[dict]:
    if FEEDBACK_STORE.exists():
        try:
            with open(FEEDBACK_STORE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            logger.warning("feedback store unreadable; starting fresh")
    return []


def _save(records: List[dict]) -> None:
    with open(FEEDBACK_STORE, "w") as f:
        json.dump(records[-MAX_RECORDS:], f, indent=2)


def log_feedback(feedback: FeedbackRequest) -> None:
    records = _load()
    record = feedback.model_dump()
    record["timestamp"] = datetime.now(timezone.utc).isoformat()
    records.append(record)
    _save(records)


def get_summary() -> FeedbackSummary:
    records = _load()
    up = sum(1 for r in records if r.get("rating") == "up")
    down = sum(1 for r in records if r.get("rating") == "down")
    total = up + down
    rate = round((up / total) * 100, 1) if total else 0.0
    return FeedbackSummary(total=total, up=up, down=down, satisfaction_rate=rate)


def clear_feedback() -> int:
    count = len(_load())
    _save([])
    return count
