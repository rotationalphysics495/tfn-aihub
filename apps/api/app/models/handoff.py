"""
Handoff Models (Story 9.1)

Pydantic schemas for shift handoff management.
Used by the handoff service for creating and managing shift handoffs.

AC#1: Create handoff flow with pre-populated assets and auto-detected shift
AC#2: Handoff screen with summary, notes, and confirmation
AC#3: No assets assigned error handling
AC#4: Duplicate handoff handling

References:
- [Source: architecture/voice-briefing.md#Shift-Handoff-Workflow]
- [Source: prd-functional-requirements.md#FR21-FR30]
"""

from typing import Optional, List
from enum import Enum
from datetime import datetime, date, timezone
from uuid import UUID
from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)


class ShiftType(str, Enum):
    """
    Type of shift for handoff (AC#1).

    Standard 8-hour shifts:
    - Morning: 6:00 AM - 2:00 PM
    - Afternoon: 2:00 PM - 10:00 PM
    - Night: 10:00 PM - 6:00 AM
    """
    MORNING = "morning"
    AFTERNOON = "afternoon"
    NIGHT = "night"


class HandoffStatus(str, Enum):
    """
    Status of a shift handoff (AC#4).

    draft: Handoff is being created, can be edited
    pending_acknowledgment: Handoff submitted, waiting for incoming supervisor
    acknowledged: Incoming supervisor has acknowledged receipt
    """
    DRAFT = "draft"
    PENDING_ACKNOWLEDGMENT = "pending_acknowledgment"
    ACKNOWLEDGED = "acknowledged"


class ShiftHandoffBase(BaseModel):
    """
    Base schema for shift handoff data.

    Common fields shared between create and read operations.
    """
    shift_date: date = Field(..., description="Date of the shift")
    shift_type: ShiftType = Field(..., description="Type of shift (morning/afternoon/night)")
    assets_covered: List[UUID] = Field(
        default_factory=list,
        description="List of asset IDs covered in this handoff"
    )
    summary: Optional[str] = Field(None, description="Auto-generated shift summary")
    text_notes: Optional[str] = Field(None, description="User-added text notes")


class ShiftHandoffCreate(ShiftHandoffBase):
    """
    Schema for creating a new shift handoff (AC#1, AC#2).

    Used when a supervisor initiates the handoff process.
    """
    pass


class ShiftHandoffUpdate(BaseModel):
    """
    Schema for updating a draft handoff (AC#4).

    Only draft handoffs can be updated.
    """
    summary: Optional[str] = Field(None, description="Updated summary")
    text_notes: Optional[str] = Field(None, description="Updated text notes")
    assets_covered: Optional[List[UUID]] = Field(None, description="Updated asset list")


class ShiftHandoff(ShiftHandoffBase):
    """
    Complete shift handoff schema (AC#1, AC#2).

    Represents a full handoff record with all fields.
    """
    id: UUID = Field(..., description="Unique handoff identifier")
    user_id: UUID = Field(..., description="User ID of the outgoing supervisor")
    status: HandoffStatus = Field(
        default=HandoffStatus.DRAFT,
        description="Current handoff status"
    )
    created_at: datetime = Field(
        default_factory=_utcnow,
        description="When the handoff was created"
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        description="When the handoff was last updated"
    )

    model_config = {"from_attributes": True}


class ShiftTimeRange(BaseModel):
    """
    Time range for a shift (AC#1).

    Represents the start and end times for shift data collection.
    """
    shift_type: ShiftType = Field(..., description="Detected shift type")
    start_time: datetime = Field(..., description="Start of shift period")
    end_time: datetime = Field(..., description="End of shift period")
    shift_date: date = Field(..., description="Date of the shift")


class SupervisorAsset(BaseModel):
    """
    Asset assigned to a supervisor (AC#1, AC#3).

    Represents an asset in the supervisor_assignments table.
    """
    asset_id: UUID = Field(..., description="Asset unique identifier")
    asset_name: str = Field(..., description="Asset display name")
    area_name: Optional[str] = Field(None, description="Production area name")


class HandoffExistsResponse(BaseModel):
    """
    Response when a handoff already exists (AC#4).

    Provides information about the existing handoff.
    """
    exists: bool = Field(..., description="Whether a handoff exists")
    existing_handoff_id: Optional[UUID] = Field(None, description="ID of existing handoff")
    status: Optional[HandoffStatus] = Field(None, description="Status of existing handoff")
    message: str = Field(..., description="User-friendly message")
    can_edit: bool = Field(False, description="Whether user can edit the existing handoff")
    can_add_supplemental: bool = Field(
        False,
        description="Whether user can add a supplemental note"
    )


class HandoffCreationResponse(BaseModel):
    """
    Response after handoff creation attempt.

    Includes shift detection info and pre-populated data.
    """
    handoff: Optional[ShiftHandoff] = Field(None, description="Created handoff if successful")
    shift_info: ShiftTimeRange = Field(..., description="Detected shift information")
    assigned_assets: List[SupervisorAsset] = Field(
        default_factory=list,
        description="Assets assigned to the supervisor"
    )
    existing_handoff: Optional[HandoffExistsResponse] = Field(
        None,
        description="Info about existing handoff if one exists"
    )


class NoAssetsError(BaseModel):
    """
    Error response when supervisor has no assigned assets (AC#3).
    """
    error: str = Field(
        default="No assets assigned - contact your administrator",
        description="Error message"
    )
    code: str = Field(default="NO_ASSETS_ASSIGNED", description="Error code")


# =============================================================================
# Handoff Synthesis Models (Story 9.2)
# =============================================================================


class HandoffSynthesisCitation(BaseModel):
    """
    Citation for handoff synthesis data (AC#6).

    Each data point includes a citation with source table and timestamp.
    Follows the established Citation model pattern.
    """
    source: str = Field(..., description="Data source name (e.g., 'supabase')")
    table: Optional[str] = Field(None, description="Database table name")
    timestamp: datetime = Field(
        default_factory=_utcnow,
        description="When data was retrieved"
    )


class HandoffSectionStatus(str, Enum):
    """
    Status of a handoff section (AC#3, AC#4).

    Used to track completion state during synthesis.
    """
    PENDING = "pending"
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"
    LOADING = "loading"


class HandoffSection(BaseModel):
    """
    A section of the handoff summary (AC#2).

    Represents a logical segment of the handoff narrative.
    """
    section_type: str = Field(
        ...,
        description="Section type: overview/issues/concerns/focus"
    )
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Narrative content for this section")
    citations: List[HandoffSynthesisCitation] = Field(
        default_factory=list,
        description="Citations for data in this section"
    )
    status: HandoffSectionStatus = Field(
        default=HandoffSectionStatus.PENDING,
        description="Section completion status"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if section failed to load"
    )


class HandoffSynthesisRequest(BaseModel):
    """
    Request for handoff synthesis (Task 2.1).

    Used to initiate shift data synthesis for a handoff.
    """
    user_id: str = Field(..., description="User requesting synthesis")
    handoff_id: Optional[str] = Field(
        None,
        description="Optional handoff ID to associate synthesis with"
    )
    supervisor_assignments: Optional[List[UUID]] = Field(
        None,
        description="Asset IDs to filter by (defaults to user's assignments)"
    )


class HandoffSynthesisMetadata(BaseModel):
    """
    Metadata for handoff synthesis response.

    Tracks synthesis performance and completion status.
    """
    generated_at: datetime = Field(
        default_factory=_utcnow,
        description="When synthesis was generated"
    )
    generation_duration_ms: Optional[int] = Field(
        None,
        description="Total generation time in milliseconds"
    )
    completion_percentage: float = Field(
        100.0,
        description="Percentage of sections completed"
    )
    timed_out: bool = Field(
        False,
        description="Whether synthesis timed out (AC#4)"
    )
    tool_failures: List[str] = Field(
        default_factory=list,
        description="Names of tools that failed (AC#3)"
    )
    partial_result: bool = Field(
        False,
        description="True if showing partial results due to timeout"
    )
    background_loading: bool = Field(
        False,
        description="True if background still loading remaining sections"
    )


class HandoffSynthesisResponse(BaseModel):
    """
    Complete handoff synthesis response (Task 2.2).

    Contains all sections of the handoff summary with citations.

    AC#1: Tool Composition for Synthesis
    AC#2: Narrative Summary Structure
    AC#3: Graceful Degradation on Tool Failure
    AC#4: Progressive Loading
    AC#6: Citation Compliance
    """
    id: str = Field(..., description="Unique synthesis ID")
    handoff_id: Optional[str] = Field(
        None,
        description="Associated handoff ID if created from handoff"
    )
    user_id: str = Field(..., description="User who requested synthesis")
    shift_info: ShiftTimeRange = Field(
        ...,
        description="Shift time range for this synthesis"
    )

    # Narrative sections (AC#2)
    sections: List[HandoffSection] = Field(
        default_factory=list,
        description="Narrative summary sections"
    )

    # All citations (AC#6)
    citations: List[HandoffSynthesisCitation] = Field(
        default_factory=list,
        description="All citations from all sections"
    )

    # Summary fields for quick access
    total_sections: int = Field(
        default=4,
        description="Expected number of sections"
    )
    completed_sections: int = Field(
        default=0,
        description="Number of completed sections"
    )

    # Metadata
    metadata: HandoffSynthesisMetadata = Field(
        default_factory=HandoffSynthesisMetadata,
        description="Synthesis metadata"
    )

    @property
    def is_complete(self) -> bool:
        """Check if synthesis is fully complete."""
        return self.completed_sections == self.total_sections

    @property
    def has_partial_data(self) -> bool:
        """Check if synthesis has at least some data."""
        return self.completed_sections > 0


class HandoffToolResultData(BaseModel):
    """
    Aggregated data from a single tool execution (Task 2.4).

    Used internally to track tool outputs during synthesis.
    """
    tool_name: str = Field(..., description="Name of the tool")
    success: bool = Field(True, description="Whether tool execution succeeded")
    data: Optional[dict] = Field(None, description="Tool output data")
    citations: List[HandoffSynthesisCitation] = Field(
        default_factory=list,
        description="Citations from this tool"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if failed"
    )
    execution_time_ms: Optional[int] = Field(
        None,
        description="Execution time in milliseconds"
    )


class HandoffSynthesisData(BaseModel):
    """
    Aggregated data from all tool executions (AC#1).

    Internal structure used during handoff synthesis.
    """
    production_status: Optional[HandoffToolResultData] = None
    downtime_analysis: Optional[HandoffToolResultData] = None
    safety_events: Optional[HandoffToolResultData] = None
    alert_check: Optional[HandoffToolResultData] = None

    @property
    def all_citations(self) -> List[HandoffSynthesisCitation]:
        """Get all citations from all tools."""
        citations = []
        for field in [self.production_status, self.downtime_analysis,
                      self.safety_events, self.alert_check]:
            if field and field.citations:
                citations.extend(field.citations)
        return citations

    @property
    def successful_tools(self) -> List[str]:
        """Get names of tools that succeeded."""
        tools = []
        for name, field in [
            ("production_status", self.production_status),
            ("downtime_analysis", self.downtime_analysis),
            ("safety_events", self.safety_events),
            ("alert_check", self.alert_check),
        ]:
            if field and field.success:
                tools.append(name)
        return tools

    @property
    def failed_tools(self) -> List[str]:
        """Get names of tools that failed."""
        tools = []
        for name, field in [
            ("production_status", self.production_status),
            ("downtime_analysis", self.downtime_analysis),
            ("safety_events", self.safety_events),
            ("alert_check", self.alert_check),
        ]:
            if field and not field.success:
                tools.append(name)
        return tools
