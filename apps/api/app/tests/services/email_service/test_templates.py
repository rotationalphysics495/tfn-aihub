"""
Tests for email template rendering.

Story: 15.2 - Email Notification Service
AC#1: Email sent on follow-up assignment (template rendering)

Test-First Development: These tests are written BEFORE the feature is implemented.
They should compile without errors but FAIL when run (imports will fail).
"""

import pytest


# =============================================================================
# AC1: Email template rendering
# =============================================================================


class TestRenderAssignmentEmail:
    """Tests for render_assignment_email() function."""

    def test_subject_line_format(self):
        """
        15-2-email-notification-service-UNIT-008: render_assignment_email produces correct subject line format.

        Given: Follow-up data with category="safety", asset_name="Pump-101", action_summary="Replace bearing"
        When: render_assignment_email() is called with this data
        Then: The returned subject equals "[Action Required] safety - Pump-101: Replace bearing"
        """
        from app.services.email.templates import render_assignment_email

        result = render_assignment_email(
            category="safety",
            asset_name="Pump-101",
            action_summary="Replace bearing",
            recommendation="Replace worn bearing immediately",
            evidence_summary="Vibration levels exceeded threshold",
            assigner_name="John Manager",
            followup_id="uuid-123",
            app_base_url="https://plant.example.com",
        )

        assert result["subject"] == "[Action Required] safety - Pump-101: Replace bearing"

    def test_html_body_contains_all_required_fields(self):
        """
        15-2-email-notification-service-UNIT-009: render_assignment_email HTML body contains all required fields.

        Given: Follow-up data with all fields populated
        When: render_assignment_email() is called
        Then: HTML body contains recommendation, evidence summary, financial impact,
              assigner name, optional note, category, asset name, and Respond button/link
        """
        from app.services.email.templates import render_assignment_email

        result = render_assignment_email(
            category="safety",
            asset_name="Pump-101",
            action_summary="Replace bearing",
            recommendation="Replace worn bearing immediately",
            evidence_summary="Vibration levels exceeded threshold 3x in past week",
            financial_impact="$15,000 estimated repair cost",
            assigner_name="John Manager",
            note="Please prioritize this week",
            followup_id="uuid-123",
            app_base_url="https://plant.example.com",
        )

        html = result["html_body"]

        # All required fields must be present
        assert "Replace worn bearing immediately" in html
        assert "Vibration levels exceeded threshold 3x in past week" in html
        assert "$15,000 estimated repair cost" in html
        assert "John Manager" in html
        assert "Assigned by" in html or "assigned by" in html.lower()
        assert "Please prioritize this week" in html
        assert "safety" in html
        assert "Pump-101" in html
        # Respond button/link
        assert "/followups/uuid-123/respond" in html

    def test_respond_button_url(self):
        """
        15-2-email-notification-service-UNIT-010: render_assignment_email includes Respond button with correct URL.

        Given: app_base_url="https://plant.example.com" and followup_id="abc-123-def"
        When: render_assignment_email() is called
        Then: HTML body contains href="https://plant.example.com/followups/abc-123-def/respond"
        """
        from app.services.email.templates import render_assignment_email

        result = render_assignment_email(
            category="safety",
            asset_name="Pump-101",
            action_summary="Replace bearing",
            recommendation="Replace worn bearing",
            evidence_summary="Vibration exceeded threshold",
            assigner_name="John Manager",
            followup_id="abc-123-def",
            app_base_url="https://plant.example.com",
        )

        html = result["html_body"]
        assert "https://plant.example.com/followups/abc-123-def/respond" in html

    def test_plain_text_fallback(self):
        """
        15-2-email-notification-service-UNIT-011: render_assignment_email produces plain-text fallback.

        Given: Follow-up data with all required fields populated
        When: render_assignment_email() is called
        Then: The result includes a plain-text version containing action details
              in readable text format without HTML tags
        """
        from app.services.email.templates import render_assignment_email

        result = render_assignment_email(
            category="safety",
            asset_name="Pump-101",
            action_summary="Replace bearing",
            recommendation="Replace worn bearing immediately",
            evidence_summary="Vibration levels exceeded threshold 3x in past week",
            financial_impact="$15,000 estimated repair cost",
            assigner_name="John Manager",
            note="Please prioritize this week",
            followup_id="uuid-123",
            app_base_url="https://plant.example.com",
        )

        text = result["text_body"]

        # Should contain action details
        assert "Replace worn bearing immediately" in text
        assert "Vibration levels exceeded threshold 3x in past week" in text
        assert "$15,000 estimated repair cost" in text
        assert "John Manager" in text
        assert "Please prioritize this week" in text

        # Should NOT contain HTML tags
        assert "<html>" not in text
        assert "<div" not in text
        assert "<table" not in text
        assert "<td" not in text

    def test_industrial_clarity_color_scheme(self):
        """
        15-2-email-notification-service-UNIT-012: render_assignment_email uses Industrial Clarity color scheme.

        Given: Follow-up data with required fields
        When: render_assignment_email() is called
        Then: HTML includes dark background header (#1a1a2e), white content area,
              and blue CTA button (#3b82f6)
        """
        from app.services.email.templates import render_assignment_email

        result = render_assignment_email(
            category="safety",
            asset_name="Pump-101",
            action_summary="Replace bearing",
            recommendation="Replace worn bearing",
            evidence_summary="Vibration exceeded threshold",
            assigner_name="John Manager",
            followup_id="uuid-123",
            app_base_url="https://plant.example.com",
        )

        html = result["html_body"]

        # Industrial Clarity colors
        assert "#1a1a2e" in html, "Dark header background color missing"
        assert "#3b82f6" in html, "Blue CTA button color missing"
        # White content area (could be #ffffff or white)
        assert "#ffffff" in html.lower() or "white" in html.lower(), \
            "White content area color missing"

    def test_handles_missing_optional_fields(self):
        """
        15-2-email-notification-service-UNIT-013: render_assignment_email handles missing optional fields gracefully.

        Given: Follow-up data with note=None and financial_impact=None
        When: render_assignment_email() is called
        Then: HTML renders without errors, does not show "None" text, still includes required fields
        """
        from app.services.email.templates import render_assignment_email

        result = render_assignment_email(
            category="safety",
            asset_name="Pump-101",
            action_summary="Replace bearing",
            recommendation="Replace worn bearing immediately",
            evidence_summary="Vibration exceeded threshold",
            assigner_name="John Manager",
            note=None,
            financial_impact=None,
            followup_id="uuid-123",
            app_base_url="https://plant.example.com",
        )

        html = result["html_body"]

        # Should not contain "None" as visible text
        assert ">None<" not in html, "None should not appear as visible text"
        assert ": None" not in html, "None should not appear after a label"

        # Required fields should still be present
        assert "Replace worn bearing immediately" in html
        assert "Vibration exceeded threshold" in html
        assert "John Manager" in html
        assert "/followups/uuid-123/respond" in html


# =============================================================================
# Story 15.3: Token URL in email templates
# =============================================================================


class TestRenderAssignmentEmailWithToken:
    """Tests for render_assignment_email() with response_token parameter (Story 15.3)."""

    def test_includes_token_in_respond_url(self):
        """
        15-3-response-capture-via-token-link-UNIT-011: render_assignment_email includes
        token in Respond URL when provided.

        Given: render_assignment_email() is called with response_token="abc-uuid-token"
               and followup_id="uuid-123" and app_base_url="https://plant.example.com"
        When: The email template is rendered
        Then: The HTML body Respond link href includes the full URL with token:
              "https://plant.example.com/followups/uuid-123/respond?token=abc-uuid-token"
        """
        from app.services.email.templates import render_assignment_email

        result = render_assignment_email(
            category="safety",
            asset_name="Pump-101",
            action_summary="Replace bearing",
            recommendation="Replace worn bearing immediately",
            evidence_summary="Vibration levels exceeded threshold",
            assigner_name="John Manager",
            followup_id="uuid-123",
            app_base_url="https://plant.example.com",
            response_token="abc-uuid-token",
        )

        html = result["html_body"]
        expected_url = "https://plant.example.com/followups/uuid-123/respond?token=abc-uuid-token"
        assert expected_url in html, (
            f"Expected token URL '{expected_url}' in HTML body"
        )

    def test_works_without_token_backward_compatible(self):
        """
        15-3-response-capture-via-token-link-UNIT-012: render_assignment_email works
        without token (backward compatibility).

        Given: render_assignment_email() is called with response_token=None (default)
        When: The email template is rendered
        Then: The HTML body Respond link href does NOT contain "?token=" -- the URL is
              just "https://plant.example.com/followups/{id}/respond" without a token
              query parameter
        """
        from app.services.email.templates import render_assignment_email

        result = render_assignment_email(
            category="safety",
            asset_name="Pump-101",
            action_summary="Replace bearing",
            recommendation="Replace worn bearing immediately",
            evidence_summary="Vibration levels exceeded threshold",
            assigner_name="John Manager",
            followup_id="uuid-123",
            app_base_url="https://plant.example.com",
            response_token=None,
        )

        html = result["html_body"]

        # Should still have the respond URL
        assert "/followups/uuid-123/respond" in html

        # Should NOT have a token query parameter
        assert "?token=" not in html
