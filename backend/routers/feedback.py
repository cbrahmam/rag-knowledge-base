from __future__ import annotations

from fastapi import APIRouter

from models.schemas import FeedbackRequest, FeedbackSummary
from services.feedback import clear_feedback, get_summary, log_feedback

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("")
async def submit_feedback(feedback: FeedbackRequest):
    log_feedback(feedback)
    return {"status": "recorded"}


@router.get("", response_model=FeedbackSummary)
async def feedback_summary():
    return get_summary()


@router.delete("")
async def reset_feedback():
    cleared = clear_feedback()
    return {"message": f"Cleared {cleared} feedback records", "cleared": cleared}
