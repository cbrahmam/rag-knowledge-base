from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException

from models.schemas import (
    ConversationCreate,
    SavedConversation,
    ConversationListItem,
)
from services.conversations import (
    save_conversation,
    list_conversations,
    get_conversation,
    update_conversation,
    delete_conversation,
)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("", response_model=SavedConversation)
async def create_conversation(data: ConversationCreate):
    if not data.messages:
        raise HTTPException(status_code=400, detail="Cannot save an empty conversation")
    return save_conversation(data)


@router.get("", response_model=List[ConversationListItem])
async def get_conversations():
    return list_conversations()


@router.get("/{conv_id}", response_model=SavedConversation)
async def read_conversation(conv_id: str):
    conv = get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.put("/{conv_id}", response_model=SavedConversation)
async def edit_conversation(conv_id: str, data: ConversationCreate):
    conv = update_conversation(conv_id, data)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.delete("/{conv_id}")
async def remove_conversation(conv_id: str):
    if not delete_conversation(conv_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation deleted", "id": conv_id}
