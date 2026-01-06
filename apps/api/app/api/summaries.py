from fastapi import APIRouter
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import date

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
async def list_daily_summaries(asset_id: Optional[UUID] = None):
    """List daily summaries, optionally filtered by asset."""
    return []


@router.get("/daily/{summary_date}", response_model=List[DailySummary])
async def get_daily_summary(summary_date: date):
    """Get daily summaries for a specific date."""
    return []
