"""
Action Plan Schemas

Pydantic models for Action Plan CRUD API endpoints.

Story: 16.2 - Action Plans CRUD API
AC: #1 - Create action plan
AC: #2 - List action plans with filters/sorting/pagination
AC: #3 - Update action plan with change logging
AC: #4 - Progress updates
AC: #5 - Verify action plan completion
"""

from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ActionPlanCategory(str, Enum):
    """Category of action plan - matches DB CHECK constraint."""
    CORRECTIVE = "corrective"
    PREVENTIVE = "preventive"
    IMPROVEMENT = "improvement"


class ActionPlanStatus(str, Enum):
    """Status of action plan - matches DB CHECK constraint."""
    DRAFT = "draft"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"


class ActionPlanPriority(str, Enum):
    """Priority level of action plan - matches DB CHECK constraint."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Priority sort map for Python-side sorting (critical first)
PRIORITY_SORT_MAP = {
    ActionPlanPriority.CRITICAL: 0,
    ActionPlanPriority.HIGH: 1,
    ActionPlanPriority.MEDIUM: 2,
    ActionPlanPriority.LOW: 3,
}


# --- Request Schemas ---


class ActionPlanCreate(BaseModel):
    """Request schema for creating a new action plan (AC#1)."""
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., description="Title of the action plan")
    description: Optional[str] = Field(None, description="Detailed description")
    category: Optional[ActionPlanCategory] = Field(None, description="Plan category")
    root_cause: Optional[str] = Field(None, description="Root cause analysis")
    corrective_action: Optional[str] = Field(None, description="Corrective action to take")
    preventive_action: Optional[str] = Field(None, description="Preventive action to take")
    asset_id: Optional[str] = Field(None, description="Associated asset UUID")
    priority: Optional[ActionPlanPriority] = Field(None, description="Priority level")
    due_date: Optional[str] = Field(None, description="Due date (YYYY-MM-DD)")
    source_followup_id: Optional[str] = Field(None, description="Source follow-up UUID")


class ActionPlanUpdate(BaseModel):
    """Request schema for updating an action plan (AC#3). All fields optional."""
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[ActionPlanCategory] = None
    root_cause: Optional[str] = None
    corrective_action: Optional[str] = None
    preventive_action: Optional[str] = None
    asset_id: Optional[str] = None
    status: Optional[ActionPlanStatus] = None
    priority: Optional[ActionPlanPriority] = None
    due_date: Optional[str] = None


class ActionPlanUpdateCreate(BaseModel):
    """Request schema for adding a progress update (AC#4)."""
    model_config = ConfigDict(extra="forbid")

    update_text: str = Field(..., description="Progress update text")
    status_change: Optional[ActionPlanStatus] = Field(
        None, description="New status to transition to"
    )


class ActionPlanVerifyRequest(BaseModel):
    """Request schema for verifying an action plan (AC#5)."""
    model_config = ConfigDict(extra="forbid")

    verification_notes: Optional[str] = Field(
        None, description="Optional notes about the verification"
    )


# --- Response Schemas ---


class ActionPlanResponse(BaseModel):
    """Response schema for a single action plan."""
    id: str
    title: str
    description: Optional[str] = None
    asset_id: Optional[str] = None
    category: Optional[str] = None
    root_cause: Optional[str] = None
    corrective_action: Optional[str] = None
    preventive_action: Optional[str] = None
    source_followup_id: Optional[str] = None
    owner_id: str
    status: str
    priority: Optional[str] = None
    due_date: Optional[str] = None
    completed_at: Optional[str] = None
    verified_by: Optional[str] = None
    verified_at: Optional[str] = None
    created_at: str
    updated_at: str


class ActionPlanListResponse(BaseModel):
    """Response schema for listing action plans with pagination."""
    items: List[ActionPlanResponse] = Field(default_factory=list)
    total_count: int = 0
    page: int = 1
    page_size: int = 20


class ActionPlanUpdateResponse(BaseModel):
    """Response schema for a progress update record."""
    id: str
    action_plan_id: str
    author_id: str
    update_text: str
    status_change: Optional[str] = None
    created_at: str
