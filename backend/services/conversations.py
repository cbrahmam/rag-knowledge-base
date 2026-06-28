"""Saved conversations.

Persists chat sessions so users can revisit or restore them later. Each
conversation is a list of messages plus metadata, keyed by id in a flat
JSON file (local-first, consistent with the rest of the app).
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from models.schemas import (
    ConversationCreate,
    SavedConversation,
    ConversationListItem,
)

logger = logging.getLogger(__name__)

CONVERSATIONS_STORE = Path(__file__).parent.parent / "conversations_store.json"


def _load() -> dict:
    if CONVERSATIONS_STORE.exists():
        try:
            with open(CONVERSATIONS_STORE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            logger.warning("conversations store unreadable; starting fresh")
    return {}


def _save(store: dict) -> None:
    with open(CONVERSATIONS_STORE, "w") as f:
        json.dump(store, f, indent=2)


def _derive_title(messages: List[dict]) -> str:
    for m in messages:
        if m.get("role") == "user" and m.get("content"):
            text = m["content"].strip()
            return text[:60] + ("…" if len(text) > 60 else "")
    return "Untitled conversation"


def save_conversation(data: ConversationCreate) -> SavedConversation:
    store = _load()
    now = datetime.now(timezone.utc).isoformat()
    conv_id = uuid.uuid4().hex[:12]
    record = SavedConversation(
        id=conv_id,
        title=(data.title or _derive_title(data.messages)),
        messages=data.messages,
        created_at=now,
        updated_at=now,
    )
    store[conv_id] = record.model_dump()
    _save(store)
    return record


def list_conversations() -> List[ConversationListItem]:
    store = _load()
    items = [
        ConversationListItem(
            id=c["id"],
            title=c["title"],
            message_count=len(c["messages"]),
            updated_at=c["updated_at"],
        )
        for c in store.values()
    ]
    items.sort(key=lambda c: c.updated_at, reverse=True)
    return items


def get_conversation(conv_id: str) -> Optional[SavedConversation]:
    store = _load()
    record = store.get(conv_id)
    return SavedConversation(**record) if record else None


def update_conversation(conv_id: str, data: ConversationCreate) -> Optional[SavedConversation]:
    store = _load()
    existing = store.get(conv_id)
    if not existing:
        return None
    existing["messages"] = data.messages
    if data.title:
        existing["title"] = data.title
    existing["updated_at"] = datetime.now(timezone.utc).isoformat()
    store[conv_id] = existing
    _save(store)
    return SavedConversation(**existing)


def delete_conversation(conv_id: str) -> bool:
    store = _load()
    if conv_id in store:
        del store[conv_id]
        _save(store)
        return True
    return False
