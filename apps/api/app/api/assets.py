from fastapi import APIRouter, Depends
from typing import List
from pydantic import BaseModel
from uuid import UUID

from app.core.security import get_current_user
from app.models.user import CurrentUser

router = APIRouter()


class Asset(BaseModel):
    id: UUID
    name: str
    source_id: str
    area: str


@router.get("/", response_model=List[Asset])
async def list_assets(current_user: CurrentUser = Depends(get_current_user)):
    """List all plant assets. Requires authentication."""
    return []


@router.get("/{asset_id}", response_model=Asset)
async def get_asset(
    asset_id: UUID, current_user: CurrentUser = Depends(get_current_user)
):
    """Get a specific asset by ID. Requires authentication."""
    pass
