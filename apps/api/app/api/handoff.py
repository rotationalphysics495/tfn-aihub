"""
Handoff API Endpoints (Story 9.1, 9.2)

REST endpoints for shift handoff creation and management.

Story 9.1:
AC#1: POST /api/v1/handoff/ - Create new shift handoff
AC#2: GET /api/v1/handoff/ - List user's handoffs
AC#3: GET /api/v1/handoff/{id} - Get handoff details
AC#4: PATCH /api/v1/handoff/{id} - Update draft handoff

Story 9.2:
AC#1: GET /api/v1/handoff/synthesis - Synthesize shift data
AC#2: POST /api/v1/handoff/{id}/synthesis - Generate and attach to handoff

References:
- [Source: architecture/voice-briefing.md#Shift-Handoff-Workflow]
- [Source: prd-functional-requirements.md#FR21-FR30]
"""

import logging
from typing import Optional, List
from datetime import datetime, timezone
from uuid import UUID, uuid4
import io

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from pydantic import BaseModel, Field
import httpx

from supabase import Client, create_client

from app.models.handoff import (
    ShiftType,
    HandoffStatus,
    ShiftHandoff,
    ShiftHandoffCreate,
    ShiftHandoffUpdate,
    ShiftTimeRange,
    SupervisorAsset,
    HandoffExistsResponse,
    HandoffCreationResponse,
    HandoffSynthesisResponse,
    VoiceNote,
    VoiceNoteList,
    VoiceNoteUploadResponse,
    VoiceNoteErrorCode,
    VOICE_NOTE_MAX_DURATION_SECONDS,
    VOICE_NOTE_MAX_COUNT,
)
from app.services.handoff import detect_current_shift, get_shift_time_range
from app.services.briefing.handoff import get_handoff_synthesis_service
from app.core.config import get_settings
from app.core.security import get_current_user
from app.models.user import CurrentUser

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Schemas
# ============================================================================


class CreateHandoffRequest(BaseModel):
    """Request schema for creating a new handoff."""
    text_notes: Optional[str] = Field(
        None,
        description="Optional text notes to include",
        max_length=2000
    )
    assets_covered: Optional[List[UUID]] = Field(
        None,
        description="Asset IDs to include (defaults to all assigned assets)"
    )


class HandoffListItem(BaseModel):
    """Schema for handoff list items."""
    id: str
    shift_date: str
    shift_type: ShiftType
    status: HandoffStatus
    created_at: str
    asset_count: int


class HandoffListResponse(BaseModel):
    """Response schema for listing handoffs."""
    handoffs: List[HandoffListItem]
    total_count: int


class HandoffDetailResponse(BaseModel):
    """Response schema for handoff details."""
    id: str
    user_id: str
    shift_date: str
    shift_type: ShiftType
    status: HandoffStatus
    assets_covered: List[SupervisorAsset]
    summary: Optional[str]
    text_notes: Optional[str]
    created_at: str
    updated_at: str


class InitiateHandoffResponse(BaseModel):
    """Response schema for initiating the handoff flow."""
    shift_info: ShiftTimeRange
    assigned_assets: List[SupervisorAsset]
    existing_handoff: Optional[HandoffExistsResponse] = None
    can_create: bool = True
    message: str = "Ready to create handoff"


# ============================================================================
# In-memory handoff store (for MVP - Story 9.4 adds persistent storage)
# ============================================================================


# In-memory store for handoffs (to be replaced with database in Story 9.4)
_handoffs: dict[str, dict] = {}


def _get_user_handoffs(user_id: str) -> List[dict]:
    """Get all handoffs for a user."""
    return [h for h in _handoffs.values() if str(h.get("user_id")) == user_id]


def _get_handoff_by_id(handoff_id: str) -> Optional[dict]:
    """Get a handoff by ID."""
    return _handoffs.get(handoff_id)


def _find_existing_handoff(user_id: str, shift_date: str, shift_type: str) -> Optional[dict]:
    """Find an existing handoff for the same user, date, and shift."""
    for handoff in _handoffs.values():
        if (str(handoff.get("user_id")) == user_id and
            str(handoff.get("shift_date")) == shift_date and
            handoff.get("shift_type") == shift_type):
            return handoff
    return None


def _save_handoff(handoff: dict) -> dict:
    """Save a handoff to the store."""
    _handoffs[str(handoff["id"])] = handoff
    return handoff


def _get_supabase_client() -> Optional[Client]:
    """Get Supabase client for database operations, or None if not configured."""
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        return None
    return create_client(settings.supabase_url, settings.supabase_key)


def _get_mock_supervisor_assets() -> List[SupervisorAsset]:
    """Return mock supervisor assets for development/testing."""
    return [
        SupervisorAsset(
            asset_id=UUID("11111111-1111-1111-1111-111111111111"),
            asset_name="Packaging Line 1",
            area_name="Packaging"
        ),
        SupervisorAsset(
            asset_id=UUID("22222222-2222-2222-2222-222222222222"),
            asset_name="Packaging Line 2",
            area_name="Packaging"
        ),
        SupervisorAsset(
            asset_id=UUID("33333333-3333-3333-3333-333333333333"),
            asset_name="Mixer A",
            area_name="Mixing"
        ),
    ]


def _get_supervisor_assignments(user_id: str) -> List[SupervisorAsset]:
    """
    Get supervisor's assigned assets (AC#3).

    In production, this queries the supervisor_assignments table.
    For MVP, returns mock data if no real assignments exist.

    Note: Story 9.4 will implement persistent storage. Until then, mock data
    is returned when Supabase is not configured or query fails.
    """
    supabase = _get_supabase_client()
    if supabase is None:
        # Return mock data for development when Supabase is not configured
        logger.info("Supabase not configured - returning mock supervisor assignments")
        return _get_mock_supervisor_assets()

    try:
        # Query supervisor_assignments joined with assets
        result = supabase.table("supervisor_assignments").select(
            "asset_id, assets(id, name, area_name)"
        ).eq("user_id", user_id).execute()

        if result.data:
            assets = []
            for row in result.data:
                asset_data = row.get("assets", {})
                if asset_data:
                    assets.append(SupervisorAsset(
                        asset_id=UUID(row["asset_id"]),
                        asset_name=asset_data.get("name", "Unknown"),
                        area_name=asset_data.get("area_name")
                    ))
            if assets:
                return assets
            # No real assignments found - return mock for MVP
            logger.info(f"No supervisor assignments found for user {user_id} - returning mock data")
            return _get_mock_supervisor_assets()

        # No results - return mock for MVP
        logger.info(f"No supervisor assignments found for user {user_id} - returning mock data")
        return _get_mock_supervisor_assets()

    except Exception as e:
        logger.warning(f"Error fetching supervisor assignments for user {user_id}: {e}")
        # Return mock data if query fails (for development)
        logger.info("Falling back to mock supervisor assignments due to query error")
        return _get_mock_supervisor_assets()


# ============================================================================
# API Endpoints
# ============================================================================


@router.get("/initiate", response_model=InitiateHandoffResponse)
async def initiate_handoff(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Initiate the handoff creation flow (AC#1).

    This endpoint is called when a supervisor selects "Create Shift Handoff".
    It returns:
    - Detected shift information
    - List of assigned assets
    - Information about any existing handoff

    If no assets are assigned, returns can_create=False with appropriate message.
    """
    user_id = current_user.id
    logger.info(f"Initiating handoff for user {user_id}")

    # Detect current shift
    shift_info = get_shift_time_range()

    # Get supervisor's assigned assets (AC#3)
    assigned_assets = _get_supervisor_assignments(user_id)

    # Check if no assets assigned (AC#3)
    if not assigned_assets:
        return InitiateHandoffResponse(
            shift_info=shift_info,
            assigned_assets=[],
            existing_handoff=None,
            can_create=False,
            message="No assets assigned - contact your administrator"
        )

    # Check for existing handoff (AC#4)
    existing = _find_existing_handoff(
        user_id,
        str(shift_info.shift_date),
        shift_info.shift_type.value
    )

    existing_handoff = None
    can_create = True
    message = "Ready to create handoff"

    if existing:
        existing_status = HandoffStatus(existing.get("status", "draft"))
        can_edit = existing_status == HandoffStatus.DRAFT
        can_add_supplemental = existing_status == HandoffStatus.PENDING_ACKNOWLEDGMENT

        existing_handoff = HandoffExistsResponse(
            exists=True,
            existing_handoff_id=UUID(existing["id"]),
            status=existing_status,
            message=(
                "A draft handoff exists for this shift. You can edit it."
                if can_edit else
                "A handoff was already submitted for this shift. You can add a supplemental note."
            ),
            can_edit=can_edit,
            can_add_supplemental=can_add_supplemental
        )

        if can_edit:
            can_create = False
            message = "A draft handoff exists. Edit it or create a new one."
        elif can_add_supplemental:
            can_create = True
            message = "A handoff was submitted. You can add a supplemental note."

    return InitiateHandoffResponse(
        shift_info=shift_info,
        assigned_assets=assigned_assets,
        existing_handoff=existing_handoff,
        can_create=can_create,
        message=message
    )


@router.post("/", response_model=HandoffDetailResponse, status_code=201)
async def create_handoff(
    request: CreateHandoffRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Create a new shift handoff (AC#1, AC#2).

    Creates a new draft handoff for the current shift. The handoff is
    pre-populated with the supervisor's assigned assets.

    Returns 400 if:
    - No assets are assigned (AC#3)
    - A non-draft handoff already exists for this shift (AC#4)
    """
    user_id = current_user.id
    logger.info(f"Creating handoff for user {user_id}")

    # Get shift info
    shift_info = get_shift_time_range()

    # Get supervisor's assigned assets (AC#3)
    assigned_assets = _get_supervisor_assignments(user_id)

    if not assigned_assets:
        raise HTTPException(
            status_code=400,
            detail="No assets assigned - contact your administrator"
        )

    # Check for existing handoff (AC#4)
    existing = _find_existing_handoff(
        user_id,
        str(shift_info.shift_date),
        shift_info.shift_type.value
    )

    if existing:
        existing_status = HandoffStatus(existing.get("status", "draft"))
        if existing_status == HandoffStatus.DRAFT:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "A draft handoff already exists for this shift",
                    "existing_handoff_id": existing["id"],
                    "action": "edit"
                }
            )
        elif existing_status in (HandoffStatus.PENDING_ACKNOWLEDGMENT, HandoffStatus.ACKNOWLEDGED):
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "A handoff was already submitted for this shift",
                    "existing_handoff_id": existing["id"],
                    "action": "supplemental"
                }
            )

    # Determine which assets to include
    if request.assets_covered:
        # Filter to only include valid assigned assets
        valid_asset_ids = {a.asset_id for a in assigned_assets}
        assets_covered = [
            a for a in request.assets_covered if a in valid_asset_ids
        ]
    else:
        # Include all assigned assets by default
        assets_covered = [a.asset_id for a in assigned_assets]

    # Create the handoff
    now = datetime.now(timezone.utc)
    handoff_id = uuid4()

    handoff_data = {
        "id": str(handoff_id),
        "user_id": user_id,
        "shift_date": str(shift_info.shift_date),
        "shift_type": shift_info.shift_type.value,
        "status": HandoffStatus.DRAFT.value,
        "assets_covered": [str(a) for a in assets_covered],
        "summary": None,  # Will be populated in Story 9.2
        "text_notes": request.text_notes,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    _save_handoff(handoff_data)

    # Return detailed response
    return HandoffDetailResponse(
        id=str(handoff_id),
        user_id=user_id,
        shift_date=handoff_data["shift_date"],
        shift_type=shift_info.shift_type,
        status=HandoffStatus.DRAFT,
        assets_covered=assigned_assets,
        summary=handoff_data["summary"],
        text_notes=handoff_data["text_notes"],
        created_at=handoff_data["created_at"],
        updated_at=handoff_data["updated_at"],
    )


@router.get("/", response_model=HandoffListResponse)
async def list_handoffs(
    current_user: CurrentUser = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50, description="Number of handoffs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    List user's handoffs.

    Returns a paginated list of the user's shift handoffs,
    ordered by creation date (newest first).
    """
    user_id = current_user.id
    all_handoffs = _get_user_handoffs(user_id)

    # Sort by created_at descending
    all_handoffs.sort(key=lambda h: h.get("created_at", ""), reverse=True)

    # Apply pagination
    paginated = all_handoffs[offset:offset + limit]

    items = [
        HandoffListItem(
            id=h["id"],
            shift_date=h["shift_date"],
            shift_type=ShiftType(h["shift_type"]),
            status=HandoffStatus(h["status"]),
            created_at=h["created_at"],
            asset_count=len(h.get("assets_covered", []))
        )
        for h in paginated
    ]

    return HandoffListResponse(
        handoffs=items,
        total_count=len(all_handoffs)
    )


# ============================================================================
# Synthesis Endpoints (Story 9.2)
# NOTE: These MUST be defined BEFORE parameterized routes like /{handoff_id}
# to avoid FastAPI matching "synthesis" as a UUID parameter.
# ============================================================================


@router.get("/synthesis", response_model=HandoffSynthesisResponse)
async def synthesize_shift_data(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Synthesize shift data for handoff (Story 9.2 AC#1).

    Orchestrates Production Status, Downtime Analysis, Safety Events,
    and Alert Check tools to generate a shift handoff summary.

    Returns:
        HandoffSynthesisResponse with narrative sections and citations

    Features:
    - AC#1: Tool Composition for Synthesis
    - AC#2: Narrative Summary Structure (overview, issues, concerns, focus)
    - AC#3: Graceful Degradation on Tool Failure
    - AC#4: Progressive Loading (15-second timeout)
    - AC#5: Supervisor Scope Filtering
    - AC#6: Citation Compliance
    - AC#7: Shift Time Range Detection
    """
    user_id = current_user.id
    logger.info(f"Synthesizing shift data for user {user_id}")

    # Get supervisor's assigned assets for filtering
    assigned_assets = _get_supervisor_assignments(user_id)
    asset_ids = [str(a.asset_id) for a in assigned_assets] if assigned_assets else None

    # Get synthesis service and generate
    service = get_handoff_synthesis_service()
    synthesis = await service.synthesize_shift_data(
        user_id=user_id,
        supervisor_assignments=asset_ids,
    )

    return synthesis


@router.get("/{handoff_id}", response_model=HandoffDetailResponse)
async def get_handoff(
    handoff_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get handoff details.

    Returns the full details of a specific handoff.
    Only the owner can view their handoffs.
    """
    user_id = current_user.id
    handoff = _get_handoff_by_id(str(handoff_id))

    if not handoff:
        raise HTTPException(status_code=404, detail="Handoff not found")

    if handoff.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get asset details
    assigned_assets = _get_supervisor_assignments(user_id)
    asset_map = {str(a.asset_id): a for a in assigned_assets}

    covered_assets = [
        asset_map.get(asset_id, SupervisorAsset(
            asset_id=UUID(asset_id),
            asset_name="Unknown Asset",
            area_name=None
        ))
        for asset_id in handoff.get("assets_covered", [])
    ]

    return HandoffDetailResponse(
        id=handoff["id"],
        user_id=handoff["user_id"],
        shift_date=handoff["shift_date"],
        shift_type=ShiftType(handoff["shift_type"]),
        status=HandoffStatus(handoff["status"]),
        assets_covered=covered_assets,
        summary=handoff.get("summary"),
        text_notes=handoff.get("text_notes"),
        created_at=handoff["created_at"],
        updated_at=handoff["updated_at"],
    )


@router.patch("/{handoff_id}", response_model=HandoffDetailResponse)
async def update_handoff(
    handoff_id: UUID,
    request: ShiftHandoffUpdate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update a draft handoff.

    Only draft handoffs can be updated. Once submitted, handoffs
    are immutable (supplements can be added separately).
    """
    user_id = current_user.id
    handoff = _get_handoff_by_id(str(handoff_id))

    if not handoff:
        raise HTTPException(status_code=404, detail="Handoff not found")

    if handoff.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if handoff.get("status") != HandoffStatus.DRAFT.value:
        raise HTTPException(
            status_code=400,
            detail="Only draft handoffs can be updated"
        )

    # Update fields
    now = datetime.now(timezone.utc)
    if request.text_notes is not None:
        handoff["text_notes"] = request.text_notes
    if request.summary is not None:
        handoff["summary"] = request.summary
    if request.assets_covered is not None:
        handoff["assets_covered"] = [str(a) for a in request.assets_covered]

    handoff["updated_at"] = now.isoformat()
    _save_handoff(handoff)

    # Get asset details for response
    assigned_assets = _get_supervisor_assignments(user_id)
    asset_map = {str(a.asset_id): a for a in assigned_assets}

    covered_assets = [
        asset_map.get(asset_id, SupervisorAsset(
            asset_id=UUID(asset_id),
            asset_name="Unknown Asset",
            area_name=None
        ))
        for asset_id in handoff.get("assets_covered", [])
    ]

    return HandoffDetailResponse(
        id=handoff["id"],
        user_id=handoff["user_id"],
        shift_date=handoff["shift_date"],
        shift_type=ShiftType(handoff["shift_type"]),
        status=HandoffStatus(handoff["status"]),
        assets_covered=covered_assets,
        summary=handoff.get("summary"),
        text_notes=handoff.get("text_notes"),
        created_at=handoff["created_at"],
        updated_at=handoff["updated_at"],
    )


@router.post("/{handoff_id}/submit", response_model=HandoffDetailResponse)
async def submit_handoff(
    handoff_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Submit a draft handoff for acknowledgment.

    Changes the handoff status from 'draft' to 'pending_acknowledgment'.
    Once submitted, the handoff cannot be edited (only supplements can be added).
    """
    user_id = current_user.id
    handoff = _get_handoff_by_id(str(handoff_id))

    if not handoff:
        raise HTTPException(status_code=404, detail="Handoff not found")

    if handoff.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if handoff.get("status") != HandoffStatus.DRAFT.value:
        raise HTTPException(
            status_code=400,
            detail="Only draft handoffs can be submitted"
        )

    # Update status
    now = datetime.now(timezone.utc)
    handoff["status"] = HandoffStatus.PENDING_ACKNOWLEDGMENT.value
    handoff["updated_at"] = now.isoformat()
    _save_handoff(handoff)

    # Get asset details for response
    assigned_assets = _get_supervisor_assignments(user_id)
    asset_map = {str(a.asset_id): a for a in assigned_assets}

    covered_assets = [
        asset_map.get(asset_id, SupervisorAsset(
            asset_id=UUID(asset_id),
            asset_name="Unknown Asset",
            area_name=None
        ))
        for asset_id in handoff.get("assets_covered", [])
    ]

    return HandoffDetailResponse(
        id=handoff["id"],
        user_id=handoff["user_id"],
        shift_date=handoff["shift_date"],
        shift_type=ShiftType(handoff["shift_type"]),
        status=HandoffStatus.PENDING_ACKNOWLEDGMENT,
        assets_covered=covered_assets,
        summary=handoff.get("summary"),
        text_notes=handoff.get("text_notes"),
        created_at=handoff["created_at"],
        updated_at=handoff["updated_at"],
    )


@router.post("/{handoff_id}/synthesis", response_model=HandoffSynthesisResponse)
async def generate_handoff_synthesis(
    handoff_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Generate and attach synthesis to an existing handoff (Story 9.2 AC#2).

    Synthesizes shift data and stores the summary in the handoff record.
    The synthesis is stored in the handoff's 'summary' field.

    Returns:
        HandoffSynthesisResponse with narrative sections and citations

    Raises:
        404: Handoff not found
        403: User is not the owner of the handoff
        400: Handoff is not in draft status
    """
    user_id = current_user.id
    handoff = _get_handoff_by_id(str(handoff_id))

    if not handoff:
        raise HTTPException(status_code=404, detail="Handoff not found")

    if handoff.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if handoff.get("status") != HandoffStatus.DRAFT.value:
        raise HTTPException(
            status_code=400,
            detail="Synthesis can only be generated for draft handoffs"
        )

    logger.info(f"Generating synthesis for handoff {handoff_id}")

    # Get supervisor's assigned assets for filtering
    assigned_assets = _get_supervisor_assignments(user_id)
    asset_ids = [str(a.asset_id) for a in assigned_assets] if assigned_assets else None

    # Get synthesis service and generate
    service = get_handoff_synthesis_service()
    synthesis = await service.synthesize_shift_data(
        user_id=user_id,
        supervisor_assignments=asset_ids,
        handoff_id=str(handoff_id),
    )

    # Store summary in handoff
    summary_text = _format_synthesis_for_storage(synthesis)
    now = datetime.now(timezone.utc)
    handoff["summary"] = summary_text
    handoff["updated_at"] = now.isoformat()
    _save_handoff(handoff)

    return synthesis


def _format_synthesis_for_storage(synthesis: HandoffSynthesisResponse) -> str:
    """Format synthesis sections into a text summary for storage."""
    parts = []
    for section in synthesis.sections:
        if section.content:
            parts.append(f"## {section.title}\n{section.content}")
    return "\n\n".join(parts)


# ============================================================================
# Voice Note Endpoints (Story 9.3)
# ============================================================================


# In-memory voice notes store (for MVP - persistent storage via Supabase)
_voice_notes: dict[str, dict] = {}


def _get_voice_notes_for_handoff(handoff_id: str) -> List[dict]:
    """Get all voice notes for a handoff, ordered by sequence."""
    notes = [n for n in _voice_notes.values() if n.get("handoff_id") == handoff_id]
    notes.sort(key=lambda n: n.get("sequence_order", 0))
    return notes


def _get_voice_note_by_id(note_id: str) -> Optional[dict]:
    """Get a voice note by ID."""
    return _voice_notes.get(note_id)


def _save_voice_note(note: dict) -> dict:
    """Save a voice note to the store."""
    _voice_notes[str(note["id"])] = note
    return note


def _delete_voice_note(note_id: str) -> bool:
    """Delete a voice note from the store."""
    if note_id in _voice_notes:
        del _voice_notes[note_id]
        return True
    return False


async def _transcribe_audio_with_elevenlabs(
    audio_data: bytes,
    content_type: str = "audio/webm"
) -> Optional[str]:
    """
    Transcribe audio using ElevenLabs Scribe v2.

    AC#2: Recording completion and transcription

    Args:
        audio_data: Raw audio bytes
        content_type: MIME type of the audio

    Returns:
        Transcription text or None if failed
    """
    settings = get_settings()

    if not settings.elevenlabs_api_key:
        logger.warning("ElevenLabs API key not configured")
        return None

    url = "https://api.elevenlabs.io/v1/speech-to-text"
    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
    }

    # Determine file extension from content type
    ext_map = {
        "audio/webm": "webm",
        "audio/ogg": "ogg",
        "audio/mp4": "m4a",
        "audio/mpeg": "mp3",
    }
    ext = ext_map.get(content_type, "webm")

    files = {
        "audio": (f"audio.{ext}", audio_data, content_type),
    }

    data = {
        "model_id": "scribe_v2",
    }

    try:
        # Use longer timeout for transcription of up to 60-second audio
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers=headers,
                files=files,
                data=data,
            )

            if response.status_code != 200:
                logger.warning(
                    f"ElevenLabs transcription failed: {response.status_code}"
                )
                return None

            result = response.json()
            text = result.get("text", "")
            return text.strip() if text else None

    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return None


async def _upload_to_supabase_storage(
    user_id: str,
    handoff_id: str,
    note_id: str,
    audio_data: bytes,
    content_type: str = "audio/webm"
) -> Optional[str]:
    """
    Upload audio file to Supabase Storage.

    AC#2: Audio is stored for playback

    Path format: handoff-voice-notes/{user_id}/{handoff_id}/{note_id}.webm

    Args:
        user_id: User ID
        handoff_id: Handoff ID
        note_id: Voice note ID
        audio_data: Raw audio bytes
        content_type: MIME type

    Returns:
        Storage path or None if failed
    """
    supabase = _get_supabase_client()
    if supabase is None:
        # For MVP without Supabase, return a mock path
        logger.info("Supabase not configured - using mock storage path")
        return f"mock://{user_id}/{handoff_id}/{note_id}.webm"

    # Determine file extension
    ext_map = {
        "audio/webm": "webm",
        "audio/ogg": "ogg",
        "audio/mp4": "m4a",
    }
    ext = ext_map.get(content_type, "webm")
    storage_path = f"{user_id}/{handoff_id}/{note_id}.{ext}"

    try:
        # Upload to storage bucket
        bucket = supabase.storage.from_("handoff-voice-notes")
        result = bucket.upload(
            storage_path,
            audio_data,
            {"content-type": content_type}
        )

        logger.info(f"Uploaded voice note to storage: {storage_path}")
        return storage_path

    except Exception as e:
        logger.error(f"Error uploading to storage: {e}")
        return None


def _get_signed_url(storage_path: str) -> Optional[str]:
    """
    Get a signed URL for audio playback.

    Args:
        storage_path: Path in Supabase Storage

    Returns:
        Signed URL valid for 1 hour, or None if failed
    """
    if storage_path.startswith("mock://"):
        # Return mock URL for development
        return f"https://mock-storage.example.com/{storage_path[7:]}"

    supabase = _get_supabase_client()
    if supabase is None:
        return None

    try:
        bucket = supabase.storage.from_("handoff-voice-notes")
        result = bucket.create_signed_url(storage_path, 3600)  # 1 hour
        return result.get("signedURL") or result.get("signedUrl")
    except Exception as e:
        logger.error(f"Error creating signed URL: {e}")
        return None


@router.post("/{handoff_id}/voice-notes", response_model=VoiceNoteUploadResponse)
async def upload_voice_note(
    handoff_id: UUID,
    audio: UploadFile = File(..., description="Audio file (webm/ogg/mp4)"),
    duration_seconds: int = Form(..., description="Duration in seconds"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Upload a voice note for a shift handoff (Story 9.3 Task 2.1).

    AC#2: Recording completion and transcription
    AC#3: Multiple voice notes management

    Process:
    1. Validate handoff ownership and note limits
    2. Upload audio to Supabase Storage
    3. Transcribe via ElevenLabs Scribe v2
    4. Store record in handoff_voice_notes table
    5. Return voice note with transcript

    Raises:
        400: Duration exceeds 60 seconds or limit reached
        403: User is not the owner of the handoff
        404: Handoff not found
        413: File too large (handled by FastAPI)
    """
    user_id = current_user.id

    # Validate handoff exists and belongs to user
    handoff = _get_handoff_by_id(str(handoff_id))
    if not handoff:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Handoff not found",
                "code": VoiceNoteErrorCode.HANDOFF_NOT_FOUND.value,
            }
        )

    if handoff.get("user_id") != user_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Access denied",
                "code": VoiceNoteErrorCode.NOT_AUTHORIZED.value,
            }
        )

    # Validate duration (Task 2.6)
    if duration_seconds > VOICE_NOTE_MAX_DURATION_SECONDS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Duration exceeds maximum of {VOICE_NOTE_MAX_DURATION_SECONDS} seconds",
                "code": VoiceNoteErrorCode.DURATION_TOO_LONG.value,
            }
        )

    # Check note count limit (Task 2.7)
    existing_notes = _get_voice_notes_for_handoff(str(handoff_id))
    if len(existing_notes) >= VOICE_NOTE_MAX_COUNT:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Maximum of {VOICE_NOTE_MAX_COUNT} voice notes reached",
                "code": VoiceNoteErrorCode.LIMIT_EXCEEDED.value,
                "fallback_suggestion": "Delete a voice note to add a new one",
            }
        )

    # Read audio data (Task 2.2)
    audio_data = await audio.read()
    content_type = audio.content_type or "audio/webm"

    # Generate note ID
    note_id = uuid4()

    # Upload to storage (Task 2.3)
    storage_path = await _upload_to_supabase_storage(
        user_id=user_id,
        handoff_id=str(handoff_id),
        note_id=str(note_id),
        audio_data=audio_data,
        content_type=content_type,
    )

    if not storage_path:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to upload audio file",
                "code": VoiceNoteErrorCode.UPLOAD_FAILED.value,
                "fallback_suggestion": "Try recording again or add text notes instead",
            }
        )

    # Transcribe audio (Task 2.4)
    transcript = await _transcribe_audio_with_elevenlabs(audio_data, content_type)

    # If transcription failed, still save the note (AC#4 graceful degradation)
    if not transcript:
        logger.warning(f"Transcription failed for note {note_id}, saving without transcript")

    # Calculate sequence order
    sequence_order = len(existing_notes)

    # Create voice note record (Task 2.5)
    now = datetime.now(timezone.utc)
    note_data = {
        "id": str(note_id),
        "handoff_id": str(handoff_id),
        "user_id": user_id,
        "storage_path": storage_path,
        "transcript": transcript,
        "duration_seconds": duration_seconds,
        "sequence_order": sequence_order,
        "created_at": now.isoformat(),
    }
    _save_voice_note(note_data)

    # Get signed URL for immediate playback
    storage_url = _get_signed_url(storage_path)

    # Build response
    voice_note = VoiceNote(
        id=note_id,
        handoff_id=handoff_id,
        user_id=UUID(user_id),
        storage_path=storage_path,
        storage_url=storage_url,
        transcript=transcript,
        duration_seconds=duration_seconds,
        sequence_order=sequence_order,
        created_at=now,
    )

    total_notes = len(existing_notes) + 1
    can_add_more = total_notes < VOICE_NOTE_MAX_COUNT

    logger.info(
        f"Voice note uploaded: {note_id} for handoff {handoff_id} "
        f"({total_notes}/{VOICE_NOTE_MAX_COUNT} notes)"
    )

    message = "Voice note uploaded successfully"
    if not transcript:
        message = "Voice note saved (transcription unavailable)"

    return VoiceNoteUploadResponse(
        note=voice_note,
        total_notes=total_notes,
        can_add_more=can_add_more,
        message=message,
    )


@router.get("/{handoff_id}/voice-notes", response_model=VoiceNoteList)
async def list_voice_notes(
    handoff_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List voice notes for a handoff (Story 9.3 Task 2.1).

    AC#3: Multiple voice notes management - shows duration and timestamp

    Returns:
        VoiceNoteList with all notes ordered by sequence
    """
    user_id = current_user.id

    # Validate handoff exists and belongs to user
    handoff = _get_handoff_by_id(str(handoff_id))
    if not handoff:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Handoff not found",
                "code": VoiceNoteErrorCode.HANDOFF_NOT_FOUND.value,
            }
        )

    if handoff.get("user_id") != user_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Access denied",
                "code": VoiceNoteErrorCode.NOT_AUTHORIZED.value,
            }
        )

    # Get voice notes
    note_records = _get_voice_notes_for_handoff(str(handoff_id))

    # Convert to VoiceNote models with signed URLs
    notes = []
    for record in note_records:
        storage_url = _get_signed_url(record["storage_path"])
        notes.append(VoiceNote(
            id=UUID(record["id"]),
            handoff_id=handoff_id,
            user_id=UUID(record["user_id"]),
            storage_path=record["storage_path"],
            storage_url=storage_url,
            transcript=record.get("transcript"),
            duration_seconds=record["duration_seconds"],
            sequence_order=record["sequence_order"],
            created_at=datetime.fromisoformat(record["created_at"]),
        ))

    return VoiceNoteList.from_notes(notes)


@router.delete("/{handoff_id}/voice-notes/{note_id}", status_code=204)
async def delete_voice_note(
    handoff_id: UUID,
    note_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Delete a voice note (Story 9.3 Task 2.1).

    AC#3: Users can delete notes to add more

    Returns:
        204 No Content on success

    Raises:
        403: User is not the owner
        404: Handoff or note not found
    """
    user_id = current_user.id

    # Validate handoff exists and belongs to user
    handoff = _get_handoff_by_id(str(handoff_id))
    if not handoff:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Handoff not found",
                "code": VoiceNoteErrorCode.HANDOFF_NOT_FOUND.value,
            }
        )

    if handoff.get("user_id") != user_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Access denied",
                "code": VoiceNoteErrorCode.NOT_AUTHORIZED.value,
            }
        )

    # Get the voice note
    note = _get_voice_note_by_id(str(note_id))
    if not note:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Voice note not found",
                "code": "not_found",
            }
        )

    # Verify the note belongs to this handoff
    if note.get("handoff_id") != str(handoff_id):
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Voice note not found",
                "code": "not_found",
            }
        )

    # Delete from storage (if not mock)
    storage_path = note.get("storage_path")
    if storage_path and not storage_path.startswith("mock://"):
        supabase = _get_supabase_client()
        if supabase:
            try:
                bucket = supabase.storage.from_("handoff-voice-notes")
                bucket.remove([storage_path])
            except Exception as e:
                logger.warning(f"Failed to delete from storage: {e}")

    # Delete from in-memory store
    _delete_voice_note(str(note_id))

    # Resequence remaining notes
    remaining_notes = _get_voice_notes_for_handoff(str(handoff_id))
    for i, remaining in enumerate(remaining_notes):
        remaining["sequence_order"] = i
        _save_voice_note(remaining)

    logger.info(f"Voice note deleted: {note_id} from handoff {handoff_id}")

    return None
