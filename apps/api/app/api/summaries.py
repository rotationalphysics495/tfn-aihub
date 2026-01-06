from fastapi import APIRouter, Depends
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import date

from app.core.security import get_current_user
from app.models.user import CurrentUser

router = APIRouter()


class DailySummary(BaseModel):
    id: UUID
    asset_id: UUID
    date: date
    oee: float
    waste: float
    financial_loss: float
    smart_summary: Optional[str] = None


@router.get("/daily", response_model=List[DailySummary])
async def list_daily_summaries(
    asset_id: Optional[UUID] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    """List daily summaries, optionally filtered by asset. Requires authentication."""
    return []


@router.get("/daily/{summary_date}", response_model=List[DailySummary])
async def get_daily_summary(
    summary_date: date, current_user: CurrentUser = Depends(get_current_user)
):
    """Get daily summaries for a specific date. Requires authentication."""
    return []
