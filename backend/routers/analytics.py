from __future__ import annotations

from typing import List

from fastapi import APIRouter, Query

from models.schemas import AnalyticsSummary, QueryRecord
from services.analytics import clear_history, get_history, get_summary

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("", response_model=AnalyticsSummary)
async def analytics_summary():
    return get_summary()


@router.get("/history", response_model=List[QueryRecord])
async def analytics_history(limit: int = Query(50, ge=1, le=500)):
    return get_history(limit)


@router.delete("/history")
async def reset_history():
    cleared = clear_history()
    return {"message": f"Cleared {cleared} query records", "cleared": cleared}
