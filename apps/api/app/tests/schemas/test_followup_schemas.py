"""
Tests for TokenResponseRequest Pydantic schema validation.

Story: 15.3 - Response Capture via Token Link
AC#2: Response submission creates message record (request validation)

Test-First Development: These tests are written BEFORE the feature is implemented.
They should compile without errors but FAIL when run (imports will fail).
"""

import pytest


# =============================================================================
# AC2: TokenResponseRequest validation
# =============================================================================


class TestTokenResponseRequest:
    """Tests for TokenResponseRequest Pydantic model validation."""

    def test_rejects_empty_response_text(self):
        """
        15-3-response-capture-via-token-link-UNIT-008: TokenResponseRequest validates
        response_text is non-empty.

        Given: A TokenResponseRequest Pydantic model
        When: Constructed with token="valid-token" and response_text="" (empty string)
        Then: A ValidationError is raised indicating response_text must not be empty
        """
        from pydantic import ValidationError
        from app.schemas.action import TokenResponseRequest

        with pytest.raises(ValidationError) as exc_info:
            TokenResponseRequest(token="valid-token", response_text="")

        # Verify the error is about response_text
        errors = exc_info.value.errors()
        field_names = [e["loc"][-1] for e in errors]
        assert "response_text" in field_names

    def test_rejects_response_text_exceeding_max_length(self):
        """
        15-3-response-capture-via-token-link-UNIT-009: TokenResponseRequest validates
        response_text max length (5000 chars).

        Given: A TokenResponseRequest Pydantic model
        When: Constructed with response_text containing 5001 characters
        Then: A ValidationError is raised indicating response_text exceeds maximum length
        """
        from pydantic import ValidationError
        from app.schemas.action import TokenResponseRequest

        with pytest.raises(ValidationError) as exc_info:
            TokenResponseRequest(token="valid-uuid", response_text="x" * 5001)

        errors = exc_info.value.errors()
        field_names = [e["loc"][-1] for e in errors]
        assert "response_text" in field_names

    def test_accepts_valid_payload(self):
        """
        15-3-response-capture-via-token-link-UNIT-010: TokenResponseRequest accepts
        valid payload.

        Given: A TokenResponseRequest Pydantic model
        When: Constructed with token="valid-uuid" and response_text="I will fix the bearing tomorrow"
        Then: The model is constructed without errors, token and response_text match inputs
        """
        from app.schemas.action import TokenResponseRequest

        request = TokenResponseRequest(
            token="valid-uuid",
            response_text="I will fix the bearing tomorrow",
        )

        assert request.token == "valid-uuid"
        assert request.response_text == "I will fix the bearing tomorrow"
