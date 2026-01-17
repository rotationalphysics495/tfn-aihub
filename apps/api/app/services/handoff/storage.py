"""
Handoff Storage Service (Story 9.4)

Handles persistence of shift handoff records with immutability guarantees.

AC#1: Handoff stored with all required fields, status = pending_acknowledgment
AC#2: Core fields immutable, only supplemental_notes appendable
AC#3: Voice files in Supabase Storage, references in handoff_voice_notes
AC#4: Error handling with retry hints

References:
- [Source: architecture/voice-briefing.md#Offline-Caching-Architecture]
- [Source: prd/prd-functional-requirements.md#FR21-FR30]
- [Source: prd/prd-non-functional-requirements.md#NFR24]
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from supabase import Client

from app.models.handoff_storage import (
    ShiftHandoffRecord,
    ShiftHandoffCreate,
    HandoffVoiceNoteRecord,
    HandoffStatus,
    SupplementalNote,
)

logger = logging.getLogger(__name__)


class HandoffPersistenceError(Exception):
    """
    Error raised when handoff persistence fails (AC#4).

    Includes retry_hint to indicate if the operation should be retried,
    and draft_key for client-side draft recovery.
    """

    def __init__(
        self,
        message: str,
        retry_hint: bool = True,
        draft_key: Optional[str] = None,
        error_code: Optional[str] = None,
    ):
        self.message = message
        self.retry_hint = retry_hint
        self.draft_key = draft_key
        self.error_code = error_code
        super().__init__(self.message)


class HandoffImmutabilityError(Exception):
    """
    Error raised when attempting to modify immutable fields (AC#2).
    """

    def __init__(self, message: str, field_name: Optional[str] = None):
        self.message = message
        self.field_name = field_name
        super().__init__(self.message)


class HandoffStorageService:
    """
    Handoff Storage Service for persistent handoff records.

    Story 9.4 Implementation:
    - AC#1: Creates handoffs with all required fields
    - AC#2: Enforces immutability of core fields after submission
    - AC#3: Manages voice note references
    - AC#4: Provides error handling with retry hints

    Usage:
        service = HandoffStorageService(supabase_client)
        handoff = await service.create_handoff(create_data, user_id)
    """

    def __init__(self, supabase: Client):
        """
        Initialize the HandoffStorageService.

        Args:
            supabase: Supabase client instance
        """
        self.supabase = supabase
        self.storage_bucket = "handoff-voice-notes"

    async def create_handoff(
        self,
        handoff: ShiftHandoffCreate,
        user_id: str,
    ) -> ShiftHandoffRecord:
        """
        Create a new shift handoff record (AC#1).

        Creates a handoff in 'draft' status by default. The handoff includes:
        - created_by (user who created)
        - shift_date
        - shift_type
        - assets_covered
        - summary_text (optional)
        - notes (optional)
        - status = 'draft'

        Args:
            handoff: Handoff creation data
            user_id: ID of the user creating the handoff

        Returns:
            ShiftHandoffRecord: The created handoff record

        Raises:
            HandoffPersistenceError: If database write fails (AC#4)
        """
        handoff_id = str(uuid4())
        now = datetime.now(timezone.utc)

        try:
            data = {
                "id": handoff_id,
                "user_id": user_id,
                "created_by": user_id,
                "shift_date": str(handoff.shift_date),
                "shift_type": handoff.shift_type.value,
                "summary_text": handoff.summary_text,
                "notes": handoff.notes,
                "text_notes": handoff.notes,  # Backward compatibility
                "summary": handoff.summary_text,  # Backward compatibility
                "status": HandoffStatus.DRAFT.value,
                "assets_covered": [str(a) for a in handoff.assets_covered],
                "supplemental_notes": [],
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }

            result = self.supabase.table("shift_handoffs").insert(data).execute()

            if not result.data:
                raise HandoffPersistenceError(
                    message="Failed to create handoff - no data returned",
                    retry_hint=True,
                    draft_key=f"draft_{user_id}_{handoff.shift_date}_{handoff.shift_type.value}",
                    error_code="INSERT_FAILED",
                )

            logger.info(f"Created handoff {handoff_id} for user {user_id}")

            return ShiftHandoffRecord.model_validate(result.data[0])

        except HandoffPersistenceError:
            raise
        except Exception as e:
            logger.error(f"Failed to create handoff: {e}")
            raise HandoffPersistenceError(
                message=f"Database error while creating handoff: {str(e)}",
                retry_hint=True,
                draft_key=f"draft_{user_id}_{handoff.shift_date}_{handoff.shift_type.value}",
                error_code="DATABASE_ERROR",
            )

    async def get_handoff(
        self,
        handoff_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[ShiftHandoffRecord]:
        """
        Get a handoff record by ID.

        Args:
            handoff_id: The handoff ID
            user_id: Optional user ID for access validation (RLS handles this)

        Returns:
            ShiftHandoffRecord if found, None otherwise
        """
        try:
            result = (
                self.supabase.table("shift_handoffs")
                .select("*")
                .eq("id", handoff_id)
                .execute()
            )

            if not result.data:
                return None

            return ShiftHandoffRecord.model_validate(result.data[0])

        except Exception as e:
            logger.error(f"Failed to get handoff {handoff_id}: {e}")
            return None

    async def list_handoffs(
        self,
        user_id: str,
        status: Optional[HandoffStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[ShiftHandoffRecord]:
        """
        List handoffs for a user (created by or assigned to).

        Args:
            user_id: User ID to filter by
            status: Optional status filter
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of ShiftHandoffRecord
        """
        try:
            query = (
                self.supabase.table("shift_handoffs")
                .select("*")
                .or_(f"created_by.eq.{user_id},user_id.eq.{user_id}")
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
            )

            if status:
                query = query.eq("status", status.value)

            result = query.execute()

            if not result.data:
                return []

            return [ShiftHandoffRecord.model_validate(row) for row in result.data]

        except Exception as e:
            logger.error(f"Failed to list handoffs for user {user_id}: {e}")
            return []

    async def list_pending_handoffs(
        self,
        user_id: str,
        limit: int = 20,
    ) -> List[ShiftHandoffRecord]:
        """
        List pending handoffs for incoming supervisor (AC#1).

        Returns handoffs with status 'pending_acknowledgment' that the user
        is assigned to receive (based on supervisor_assignments).

        Args:
            user_id: User ID of the incoming supervisor
            limit: Maximum number of results

        Returns:
            List of pending ShiftHandoffRecord
        """
        try:
            # Query handoffs where user is assigned to covered assets
            # RLS policy handles access control
            result = (
                self.supabase.table("shift_handoffs")
                .select("*")
                .eq("status", HandoffStatus.PENDING_ACKNOWLEDGMENT.value)
                .neq("created_by", user_id)  # Not their own handoffs
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )

            if not result.data:
                return []

            return [ShiftHandoffRecord.model_validate(row) for row in result.data]

        except Exception as e:
            logger.error(f"Failed to list pending handoffs for user {user_id}: {e}")
            return []

    async def submit_handoff(
        self,
        handoff_id: str,
        user_id: str,
    ) -> ShiftHandoffRecord:
        """
        Submit a draft handoff for acknowledgment (AC#1).

        Changes status from 'draft' to 'pending_acknowledgment'.
        After submission, core fields become immutable (AC#2).

        Args:
            handoff_id: The handoff ID
            user_id: User ID (must be the creator)

        Returns:
            Updated ShiftHandoffRecord

        Raises:
            HandoffPersistenceError: If submission fails
            HandoffImmutabilityError: If handoff is not in draft status
        """
        # Get current handoff
        current = await self.get_handoff(handoff_id)

        if not current:
            raise HandoffPersistenceError(
                message="Handoff not found",
                retry_hint=False,
                error_code="NOT_FOUND",
            )

        if str(current.created_by) != user_id and str(current.user_id) != user_id:
            raise HandoffPersistenceError(
                message="Access denied - not the handoff creator",
                retry_hint=False,
                error_code="ACCESS_DENIED",
            )

        if current.status != HandoffStatus.DRAFT:
            raise HandoffImmutabilityError(
                message=f"Cannot submit handoff - current status is {current.status.value}"
            )

        try:
            now = datetime.now(timezone.utc)
            result = (
                self.supabase.table("shift_handoffs")
                .update({
                    "status": HandoffStatus.PENDING_ACKNOWLEDGMENT.value,
                    "updated_at": now.isoformat(),
                })
                .eq("id", handoff_id)
                .execute()
            )

            if not result.data:
                raise HandoffPersistenceError(
                    message="Failed to submit handoff",
                    retry_hint=True,
                    error_code="UPDATE_FAILED",
                )

            logger.info(f"Submitted handoff {handoff_id}")
            return ShiftHandoffRecord.model_validate(result.data[0])

        except (HandoffPersistenceError, HandoffImmutabilityError):
            raise
        except Exception as e:
            logger.error(f"Failed to submit handoff {handoff_id}: {e}")
            raise HandoffPersistenceError(
                message=f"Database error while submitting handoff: {str(e)}",
                retry_hint=True,
                error_code="DATABASE_ERROR",
            )

    async def add_supplemental_note(
        self,
        handoff_id: str,
        note_text: str,
        user_id: str,
    ) -> ShiftHandoffRecord:
        """
        Append a supplemental note to an existing handoff (AC#2).

        This is the only allowed modification after a handoff is submitted.
        The note is appended to the supplemental_notes JSONB array.

        Args:
            handoff_id: The handoff ID
            note_text: The note text to append
            user_id: User ID adding the note

        Returns:
            Updated ShiftHandoffRecord

        Raises:
            HandoffPersistenceError: If the append fails
        """
        # Get current handoff
        current = await self.get_handoff(handoff_id)

        if not current:
            raise HandoffPersistenceError(
                message="Handoff not found",
                retry_hint=False,
                error_code="NOT_FOUND",
            )

        # Supplemental notes can only be added after submission
        if current.status == HandoffStatus.DRAFT:
            raise HandoffImmutabilityError(
                message="Submit the handoff before adding supplemental notes"
            )

        try:
            now = datetime.now(timezone.utc)

            # Create the new supplemental note
            new_note = {
                "added_at": now.isoformat(),
                "added_by": user_id,
                "note_text": note_text,
            }

            # Append to existing notes
            existing_notes = current.supplemental_notes or []
            updated_notes = existing_notes + [new_note]

            result = (
                self.supabase.table("shift_handoffs")
                .update({
                    "supplemental_notes": updated_notes,
                    "updated_at": now.isoformat(),
                })
                .eq("id", handoff_id)
                .execute()
            )

            if not result.data:
                raise HandoffPersistenceError(
                    message="Failed to add supplemental note",
                    retry_hint=True,
                    error_code="UPDATE_FAILED",
                )

            logger.info(f"Added supplemental note to handoff {handoff_id}")
            return ShiftHandoffRecord.model_validate(result.data[0])

        except (HandoffPersistenceError, HandoffImmutabilityError):
            raise
        except Exception as e:
            logger.error(f"Failed to add supplemental note to {handoff_id}: {e}")
            raise HandoffPersistenceError(
                message=f"Database error while adding note: {str(e)}",
                retry_hint=True,
                error_code="DATABASE_ERROR",
            )

    async def update_status(
        self,
        handoff_id: str,
        new_status: HandoffStatus,
        user_id: str,
        acknowledged_by: Optional[str] = None,
    ) -> ShiftHandoffRecord:
        """
        Update handoff status (AC#2 - allowed transitions only).

        Allowed transitions:
        - draft -> pending_acknowledgment (via submit_handoff)
        - pending_acknowledgment -> acknowledged
        - pending_acknowledgment -> expired

        Args:
            handoff_id: The handoff ID
            new_status: The new status
            user_id: User ID making the change
            acknowledged_by: User ID acknowledging (for acknowledgment)

        Returns:
            Updated ShiftHandoffRecord

        Raises:
            HandoffImmutabilityError: If transition is not allowed
        """
        current = await self.get_handoff(handoff_id)

        if not current:
            raise HandoffPersistenceError(
                message="Handoff not found",
                retry_hint=False,
                error_code="NOT_FOUND",
            )

        # Validate status transition
        valid_transitions = {
            HandoffStatus.DRAFT: [HandoffStatus.PENDING_ACKNOWLEDGMENT],
            HandoffStatus.PENDING_ACKNOWLEDGMENT: [
                HandoffStatus.ACKNOWLEDGED,
                HandoffStatus.EXPIRED,
            ],
            HandoffStatus.ACKNOWLEDGED: [],  # Terminal state
            HandoffStatus.EXPIRED: [],  # Terminal state
        }

        if new_status not in valid_transitions.get(current.status, []):
            raise HandoffImmutabilityError(
                message=f"Invalid status transition: {current.status.value} -> {new_status.value}"
            )

        try:
            now = datetime.now(timezone.utc)
            update_data = {
                "status": new_status.value,
                "updated_at": now.isoformat(),
            }

            # Add acknowledgment fields if acknowledging
            if new_status == HandoffStatus.ACKNOWLEDGED and acknowledged_by:
                update_data["acknowledged_by"] = acknowledged_by
                update_data["acknowledged_at"] = now.isoformat()

            result = (
                self.supabase.table("shift_handoffs")
                .update(update_data)
                .eq("id", handoff_id)
                .execute()
            )

            if not result.data:
                raise HandoffPersistenceError(
                    message="Failed to update status",
                    retry_hint=True,
                    error_code="UPDATE_FAILED",
                )

            logger.info(
                f"Updated handoff {handoff_id} status: "
                f"{current.status.value} -> {new_status.value}"
            )
            return ShiftHandoffRecord.model_validate(result.data[0])

        except (HandoffPersistenceError, HandoffImmutabilityError):
            raise
        except Exception as e:
            logger.error(f"Failed to update status for {handoff_id}: {e}")
            raise HandoffPersistenceError(
                message=f"Database error while updating status: {str(e)}",
                retry_hint=True,
                error_code="DATABASE_ERROR",
            )

    async def upload_voice_note(
        self,
        handoff_id: str,
        user_id: str,
        audio_data: bytes,
        duration_seconds: int,
        content_type: str = "audio/webm",
    ) -> HandoffVoiceNoteRecord:
        """
        Upload a voice note to Supabase Storage (AC#3).

        Stores the audio file and creates a reference in handoff_voice_notes table.

        Args:
            handoff_id: The handoff ID
            user_id: User ID uploading the note
            audio_data: Raw audio bytes
            duration_seconds: Duration in seconds
            content_type: MIME type

        Returns:
            HandoffVoiceNoteRecord with storage path

        Raises:
            HandoffPersistenceError: If upload fails
        """
        note_id = str(uuid4())

        # Determine file extension
        ext_map = {
            "audio/webm": "webm",
            "audio/ogg": "ogg",
            "audio/mp4": "m4a",
        }
        ext = ext_map.get(content_type, "webm")
        storage_path = f"{user_id}/{handoff_id}/{note_id}.{ext}"

        try:
            # Upload to storage
            bucket = self.supabase.storage.from_(self.storage_bucket)
            bucket.upload(
                storage_path,
                audio_data,
                {"content-type": content_type},
            )

            logger.info(f"Uploaded voice note to storage: {storage_path}")

            # Get sequence order
            existing_notes = await self.get_voice_notes(handoff_id)
            sequence_order = len(existing_notes)

            # Create database record
            now = datetime.now(timezone.utc)
            data = {
                "id": note_id,
                "handoff_id": handoff_id,
                "user_id": user_id,
                "storage_path": storage_path,
                "duration_seconds": duration_seconds,
                "sequence_order": sequence_order,
                "created_at": now.isoformat(),
            }

            result = (
                self.supabase.table("handoff_voice_notes")
                .insert(data)
                .execute()
            )

            if not result.data:
                # Clean up storage if DB insert fails
                try:
                    bucket.remove([storage_path])
                except Exception:
                    pass
                raise HandoffPersistenceError(
                    message="Failed to create voice note record",
                    retry_hint=True,
                    error_code="INSERT_FAILED",
                )

            return HandoffVoiceNoteRecord.model_validate(result.data[0])

        except HandoffPersistenceError:
            raise
        except Exception as e:
            logger.error(f"Failed to upload voice note: {e}")
            raise HandoffPersistenceError(
                message=f"Failed to upload voice note: {str(e)}",
                retry_hint=True,
                error_code="UPLOAD_FAILED",
            )

    async def get_voice_notes(
        self,
        handoff_id: str,
    ) -> List[HandoffVoiceNoteRecord]:
        """
        Get all voice notes for a handoff (AC#3).

        Args:
            handoff_id: The handoff ID

        Returns:
            List of HandoffVoiceNoteRecord ordered by sequence
        """
        try:
            result = (
                self.supabase.table("handoff_voice_notes")
                .select("*")
                .eq("handoff_id", handoff_id)
                .order("sequence_order")
                .execute()
            )

            if not result.data:
                return []

            return [HandoffVoiceNoteRecord.model_validate(row) for row in result.data]

        except Exception as e:
            logger.error(f"Failed to get voice notes for {handoff_id}: {e}")
            return []

    def get_signed_url(
        self,
        storage_path: str,
        expires_in: int = 3600,
    ) -> Optional[str]:
        """
        Get a signed URL for voice note playback.

        Args:
            storage_path: Path in Supabase Storage
            expires_in: URL validity in seconds (default 1 hour)

        Returns:
            Signed URL or None if failed
        """
        try:
            bucket = self.supabase.storage.from_(self.storage_bucket)
            result = bucket.create_signed_url(storage_path, expires_in)
            return result.get("signedURL") or result.get("signedUrl")
        except Exception as e:
            logger.error(f"Failed to create signed URL: {e}")
            return None


# Module-level singleton and factory
_handoff_storage_service: Optional[HandoffStorageService] = None


def get_handoff_storage_service(supabase: Client) -> HandoffStorageService:
    """
    Get or create the HandoffStorageService instance.

    Args:
        supabase: Supabase client instance

    Returns:
        HandoffStorageService instance
    """
    global _handoff_storage_service
    if _handoff_storage_service is None:
        _handoff_storage_service = HandoffStorageService(supabase)
    return _handoff_storage_service
