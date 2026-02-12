"""
Token Service for follow-up response capture.

Story: 15.3 - Response Capture via Token Link
Provides token generation, validation, and usage tracking for
unauthenticated follow-up responses via email links.
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

TOKEN_EXPIRY_HOURS = 72


@dataclass
class TokenValidationResult:
    """Result of token validation."""
    is_valid: bool
    followup_id: Optional[str] = None
    assignee_email: Optional[str] = None
    error_reason: Optional[str] = None


class TokenService:
    """Service for generating and validating response tokens.

    Uses the service_role Supabase client since token operations
    are performed by unauthenticated users (token IS the auth).
    """

    def __init__(self, supabase_client: Any):
        self.supabase_client = supabase_client

    def generate_token(self, followup_id: str, assignee_email: str) -> str:
        """Generate a UUID v4 response token and store it in followup_messages.

        Args:
            followup_id: The follow-up ID this token is for.
            assignee_email: Email of the assignee who will use this token.

        Returns:
            The generated token string.
        """
        token = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=TOKEN_EXPIRY_HOURS)

        self.supabase_client.table("followup_messages").insert({
            "followup_id": followup_id,
            "response_token": token,
            "token_expires_at": expires_at.isoformat(),
            "token_used_at": None,
            "sender_email": assignee_email,
            "direction": "outbound",
            "message_type": "assignment",
        }).execute()

        return token

    def validate_token(self, token: str) -> TokenValidationResult:
        """Validate a response token.

        Checks existence, expiry, and used status.

        Args:
            token: The token string to validate.

        Returns:
            TokenValidationResult with validation outcome.
        """
        result = (
            self.supabase_client.table("followup_messages")
            .select("followup_id, sender_email, token_expires_at, token_used_at")
            .eq("response_token", token)
            .execute()
        )

        if not result.data:
            return TokenValidationResult(is_valid=False, error_reason="invalid")

        record = result.data[0]

        # Check if token has been used
        if record.get("token_used_at") is not None:
            return TokenValidationResult(is_valid=False, error_reason="expired")

        # Check if token has expired
        expires_at_str = record.get("token_expires_at")
        if expires_at_str:
            if isinstance(expires_at_str, str):
                expires_at = datetime.fromisoformat(expires_at_str)
            else:
                expires_at = expires_at_str

            # Ensure timezone-aware comparison
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            if expires_at < datetime.now(timezone.utc):
                return TokenValidationResult(is_valid=False, error_reason="expired")

        return TokenValidationResult(
            is_valid=True,
            followup_id=record.get("followup_id"),
            assignee_email=record.get("sender_email"),
        )

    def mark_token_used(self, token: str) -> None:
        """Mark a token as used by setting token_used_at.

        Args:
            token: The token string to mark as used.
        """
        now = datetime.now(timezone.utc)
        (
            self.supabase_client.table("followup_messages")
            .update({"token_used_at": now.isoformat()})
            .eq("response_token", token)
            .execute()
        )
