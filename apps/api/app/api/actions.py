from fastapi import APIRouter
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID
from enum import Enum

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
async def list_actions():
    """List prioritized actions based on daily summaries and safety events."""
    return []


@router.get("/safety", response_model=List[Action])
async def list_safety_actions():
    """List safety-related actions only."""
    return []
