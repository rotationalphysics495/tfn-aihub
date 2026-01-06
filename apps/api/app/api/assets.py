from fastapi import APIRouter
from typing import List
from pydantic import BaseModel
from uuid import UUID

router = APIRouter()


class Asset(BaseModel):
    id: UUID
    name: str
    source_id: str
    area: str


@router.get("/", response_model=List[Asset])
async def list_assets():
    """List all plant assets."""
    return []


@router.get("/{asset_id}", response_model=Asset)
async def get_asset(asset_id: UUID):
    """Get a specific asset by ID."""
    pass
