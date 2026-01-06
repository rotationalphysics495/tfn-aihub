from fastapi import APIRouter, Depends
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID
from enum import Enum

from app.core.security import get_current_user
from app.models.user import CurrentUser

router = APIRouter()


class ActionPriority(str, Enum):
    safety = "safety"
    high = "high"
    medium = "medium"
    low = "low"


class Action(BaseModel):
    id: UUID
    asset_id: UUID
    priority: ActionPriority
    title: str
    description: str
    financial_impact: Optional[float] = None


@router.get("/", response_model=List[Action])
async def list_actions(current_user: CurrentUser = Depends(get_current_user)):
    """List prioritized actions based on daily summaries and safety events. Requires authentication."""
    return []


@router.get("/safety", response_model=List[Action])
async def list_safety_actions(current_user: CurrentUser = Depends(get_current_user)):
    """List safety-related actions only. Requires authentication."""
    return []
