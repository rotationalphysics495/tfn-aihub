"""
Tests for FollowUpCreateRequest Pydantic schema.

Story: 15.2 - Email Notification Service
Cross-Cutting: Data Model and Schema Validations

Test-First Development: These tests are written BEFORE the feature is implemented.
They should compile without errors but FAIL when run (FollowUpCreateRequest doesn't exist yet).
"""

import pytest
from pydantic import ValidationError


# =============================================================================
# Schema Validation Tests
# =============================================================================


class TestFollowUpCreateRequestSchema:
    """Tests for FollowUpCreateRequest Pydantic model."""

    def test_validates_category_enum(self):
        """
        15-2-email-notification-service-UNIT-029: FollowUpCreateRequest validates category enum.

        Given: A FollowUpCreateRequest Pydantic model
        When: Constructed with category="invalid"
        Then: A ValidationError is raised indicating category must be one of
              'safety', 'oee', 'financial'
        """
        from app.schemas.action import FollowUpCreateRequest

        with pytest.raises(ValidationError) as exc_info:
            FollowUpCreateRequest(
                action_item_id="AI-001",
                action_summary="Replace bearing",
                asset_name="Pump-101",
                category="invalid",
                assigned_to="uuid-assignee",
                report_date="2026-02-10",
            )

        errors = exc_info.value.errors()
        assert len(errors) > 0
        # Should mention category field
        assert any("category" in str(e).lower() for e in errors)

    def test_accepts_valid_payload(self):
        """
        15-2-email-notification-service-UNIT-030: FollowUpCreateRequest accepts valid payload.

        Given: A FollowUpCreateRequest Pydantic model
        When: Constructed with all valid fields
        Then: Model is constructed without errors and all fields match inputs
        """
        from app.schemas.action import FollowUpCreateRequest

        model = FollowUpCreateRequest(
            action_item_id="AI-001",
            action_summary="Replace bearing",
            asset_name="Pump-101",
            category="safety",
            assigned_to="uuid-assignee",
            report_date="2026-02-10",
        )

        assert model.action_item_id == "AI-001"
        assert model.action_summary == "Replace bearing"
        assert model.asset_name == "Pump-101"
        assert model.category == "safety"
        assert model.assigned_to == "uuid-assignee"
        assert model.report_date == "2026-02-10"

    def test_accepts_all_valid_categories(self):
        """
        15-2-email-notification-service-UNIT-030 (cont): All valid categories accepted.

        Given: Valid category values
        When: FollowUpCreateRequest is constructed with each valid category
        Then: No validation errors
        """
        from app.schemas.action import FollowUpCreateRequest

        for category in ("safety", "oee", "financial"):
            model = FollowUpCreateRequest(
                action_item_id="AI-001",
                action_summary="Test action",
                asset_name="Asset-1",
                category=category,
                assigned_to="uuid-assignee",
                report_date="2026-02-10",
            )
            assert model.category == category

    def test_optional_note_field(self):
        """
        15-2-email-notification-service-UNIT-030 (cont): Optional note field works correctly.

        Given: A valid payload with and without a note
        When: FollowUpCreateRequest is constructed
        Then: note=None is acceptable, and note with string value works
        """
        from app.schemas.action import FollowUpCreateRequest

        # Without note
        model = FollowUpCreateRequest(
            action_item_id="AI-001",
            action_summary="Test action",
            asset_name="Asset-1",
            category="safety",
            assigned_to="uuid-assignee",
            report_date="2026-02-10",
        )
        assert model.note is None

        # With note
        model_with_note = FollowUpCreateRequest(
            action_item_id="AI-001",
            action_summary="Test action",
            asset_name="Asset-1",
            category="safety",
            assigned_to="uuid-assignee",
            report_date="2026-02-10",
            note="Priority this week",
        )
        assert model_with_note.note == "Priority this week"
