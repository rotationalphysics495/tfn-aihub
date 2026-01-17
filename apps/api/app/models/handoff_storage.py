"""
Handoff Storage Models (Story 9.4)

Pydantic schemas for persistent handoff records storage layer.

These models are used by the HandoffStorageService for database operations.
They differ from the API-facing models in app/models/handoff.py which handle
request/response serialization.

AC#1: ShiftHandoffRecord with all required fields
AC#2: Validators for immutable field protection
AC#3: HandoffVoiceNoteRecord for voice note references
AC#4: HandoffStatus enum with all valid states

References:
- [Source: architecture/voice-briefing.md#Offline-Caching-Architecture]
- [Source: prd/prd-functional-requirements.md#FR21-FR30]
- [Source: prd/prd-non-functional-requirements.md#NFR24]
"""

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)


class HandoffStatus(str, Enum):
    """
    Status of a shift handoff (AC#4).

    Status lifecycle:
    - draft: Handoff is being created, can be edited
    - pending_acknowledgment: Handoff submitted, waiting for incoming supervisor (AC#1)
    - acknowledged: Incoming supervisor has acknowledged receipt
    - expired: Handoff was not acknowledged within the expiration window
    """

    DRAFT = "draft"
    PENDING_ACKNOWLEDGMENT = "pending_acknowledgment"
    ACKNOWLEDGED = "acknowledged"
    EXPIRED = "expired"


class ShiftType(str, Enum):
    """
    Type of shift for handoff.

    Standard 8-hour shifts:
    - morning: 6:00 AM - 2:00 PM (AC#1)
    - afternoon: 2:00 PM - 10:00 PM
    - night: 10:00 PM - 6:00 AM

    Legacy support:
    - day: Alias for morning
    - swing: Alias for afternoon
    """

    MORNING = "morning"
    AFTERNOON = "afternoon"
    NIGHT = "night"
    DAY = "day"  # Legacy alias
    SWING = "swing"  # Legacy alias


class SupplementalNote(BaseModel):
    """
    A supplemental note added after handoff submission (AC#2).

    Supplemental notes are the only content that can be added after
    a handoff is submitted, maintaining immutability of core fields.
    """

    added_at: datetime = Field(
        default_factory=_utcnow,
        description="When the note was added",
    )
    added_by: str = Field(
        ...,
        description="User ID who added the note",
    )
    note_text: str = Field(
        ...,
        description="The note content",
        min_length=1,
        max_length=2000,
    )


class ShiftHandoffCreate(BaseModel):
    """
    Schema for creating a new shift handoff (AC#1).

    Used when a supervisor initiates the handoff process.
    All core fields are set at creation and become immutable after submission.
    """

    shift_date: date = Field(
        ...,
        description="Date of the shift being handed off",
    )
    shift_type: ShiftType = Field(
        ...,
        description="Type of shift (morning/afternoon/night)",
    )
    summary_text: Optional[str] = Field(
        None,
        description="Auto-generated shift summary",
        max_length=10000,
    )
    notes: Optional[str] = Field(
        None,
        description="User-provided text notes",
        max_length=2000,
    )
    assets_covered: List[UUID] = Field(
        default_factory=list,
        description="List of asset IDs covered in this handoff",
    )


class ShiftHandoffRecord(BaseModel):
    """
    Complete shift handoff database record (AC#1, AC#2).

    Represents a handoff stored in the shift_handoffs table.
    Core fields are immutable once status != 'draft'.

    Immutable fields (AC#2):
    - shift_date
    - shift_type
    - summary_text
    - notes
    - assets_covered
    - created_by

    Mutable fields:
    - status (controlled transitions)
    - supplemental_notes (append-only)
    - acknowledged_by
    - acknowledged_at
    - updated_at
    """

    id: UUID = Field(
        ...,
        description="Unique handoff identifier",
    )
    user_id: UUID = Field(
        ...,
        description="User ID (backward compatibility)",
    )
    created_by: UUID = Field(
        ...,
        description="User ID of outgoing supervisor who created the handoff",
    )
    shift_date: date = Field(
        ...,
        description="Date of the shift",
    )
    shift_type: ShiftType = Field(
        ...,
        description="Type of shift",
    )
    summary_text: Optional[str] = Field(
        None,
        description="Auto-generated shift summary (immutable after submission)",
    )
    summary: Optional[str] = Field(
        None,
        description="Summary (backward compatibility alias)",
    )
    notes: Optional[str] = Field(
        None,
        description="User-provided text notes (immutable after submission)",
    )
    text_notes: Optional[str] = Field(
        None,
        description="Text notes (backward compatibility alias)",
    )
    supplemental_notes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Append-only array of supplemental notes",
    )
    status: HandoffStatus = Field(
        default=HandoffStatus.DRAFT,
        description="Current handoff status",
    )
    assets_covered: List[UUID] = Field(
        default_factory=list,
        description="Array of asset UUIDs covered by this handoff",
    )
    acknowledged_by: Optional[UUID] = Field(
        None,
        description="User ID of incoming supervisor who acknowledged",
    )
    acknowledged_at: Optional[datetime] = Field(
        None,
        description="Timestamp when handoff was acknowledged",
    )
    created_at: datetime = Field(
        default_factory=_utcnow,
        description="When the handoff was created",
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        description="When the handoff was last updated",
    )

    model_config = {"from_attributes": True}

    @field_validator("assets_covered", mode="before")
    @classmethod
    def parse_assets_covered(cls, v: Any) -> List[UUID]:
        """Parse assets_covered from database format (string array)."""
        if not v:
            return []
        if isinstance(v, list):
            return [UUID(str(a)) if not isinstance(a, UUID) else a for a in v]
        return []

    @field_validator("supplemental_notes", mode="before")
    @classmethod
    def parse_supplemental_notes(cls, v: Any) -> List[Dict[str, Any]]:
        """Parse supplemental_notes from database JSONB."""
        if not v:
            return []
        if isinstance(v, list):
            return v
        return []

    @field_validator("shift_type", mode="before")
    @classmethod
    def parse_shift_type(cls, v: Any) -> ShiftType:
        """Parse shift_type from string."""
        if isinstance(v, ShiftType):
            return v
        if isinstance(v, str):
            return ShiftType(v.lower())
        raise ValueError(f"Invalid shift_type: {v}")

    @field_validator("status", mode="before")
    @classmethod
    def parse_status(cls, v: Any) -> HandoffStatus:
        """Parse status from string."""
        if isinstance(v, HandoffStatus):
            return v
        if isinstance(v, str):
            return HandoffStatus(v)
        raise ValueError(f"Invalid status: {v}")

    @model_validator(mode="after")
    def sync_backward_compat_fields(self) -> "ShiftHandoffRecord":
        """Sync backward compatibility fields."""
        # Sync summary fields
        if self.summary_text and not self.summary:
            object.__setattr__(self, "summary", self.summary_text)
        elif self.summary and not self.summary_text:
            object.__setattr__(self, "summary_text", self.summary)

        # Sync notes fields
        if self.notes and not self.text_notes:
            object.__setattr__(self, "text_notes", self.notes)
        elif self.text_notes and not self.notes:
            object.__setattr__(self, "notes", self.text_notes)

        return self

    @property
    def is_immutable(self) -> bool:
        """Check if core fields are immutable (AC#2)."""
        return self.status != HandoffStatus.DRAFT

    @property
    def can_be_acknowledged(self) -> bool:
        """Check if handoff can be acknowledged."""
        return self.status == HandoffStatus.PENDING_ACKNOWLEDGMENT

    @property
    def parsed_supplemental_notes(self) -> List[SupplementalNote]:
        """Get supplemental notes as typed objects."""
        return [
            SupplementalNote(
                added_at=datetime.fromisoformat(n["added_at"])
                if isinstance(n.get("added_at"), str)
                else n.get("added_at", _utcnow()),
                added_by=n.get("added_by", "unknown"),
                note_text=n.get("note_text", ""),
            )
            for n in self.supplemental_notes
        ]


class HandoffVoiceNoteRecord(BaseModel):
    """
    Voice note database record (AC#3).

    Represents a voice note stored in handoff_voice_notes table
    with audio file in Supabase Storage.
    """

    id: UUID = Field(
        ...,
        description="Unique voice note identifier",
    )
    handoff_id: UUID = Field(
        ...,
        description="Reference to parent handoff",
    )
    user_id: UUID = Field(
        ...,
        description="User who created the voice note",
    )
    storage_path: str = Field(
        ...,
        description="Path in Supabase Storage: {user_id}/{handoff_id}/{note_id}.webm",
    )
    transcript: Optional[str] = Field(
        None,
        description="ElevenLabs Scribe transcription",
    )
    duration_seconds: int = Field(
        ...,
        description="Duration of the recording in seconds (max 60)",
        ge=1,
        le=60,
    )
    sequence_order: int = Field(
        default=0,
        description="Order of the voice note within the handoff (0-indexed)",
        ge=0,
    )
    created_at: datetime = Field(
        default_factory=_utcnow,
        description="When the voice note was created",
    )

    model_config = {"from_attributes": True}


class HandoffPersistenceErrorResponse(BaseModel):
    """
    Error response for handoff persistence failures (AC#4).

    Includes retry_hint and draft_key for client-side error handling.
    """

    error: str = Field(
        ...,
        description="Error message",
    )
    code: str = Field(
        ...,
        description="Error code for programmatic handling",
    )
    retry_hint: bool = Field(
        default=True,
        description="Whether the operation should be retried",
    )
    draft_key: Optional[str] = Field(
        None,
        description="Key for client-side draft recovery",
    )


class HandoffListResponse(BaseModel):
    """
    Response for listing handoffs.
    """

    handoffs: List[ShiftHandoffRecord] = Field(
        default_factory=list,
        description="List of handoff records",
    )
    total_count: int = Field(
        default=0,
        description="Total number of handoffs",
    )
    has_more: bool = Field(
        default=False,
        description="Whether more handoffs are available",
    )
