"""
Tests for SMTP configuration in Settings.

Story: 15.2 - Email Notification Service
AC#2: Graceful degradation when SMTP not configured

Test-First Development: These tests are written BEFORE the feature is implemented.
They should compile without errors but FAIL when run (smtp_configured property doesn't exist yet).
"""

import pytest
from unittest.mock import patch
import os


# =============================================================================
# AC2: SMTP configuration validation
# =============================================================================


class TestSMTPConfigured:
    """Tests for the smtp_configured property on Settings."""

    def test_smtp_configured_false_when_all_empty(self):
        """
        15-2-email-notification-service-UNIT-017: smtp_configured returns False when SMTP fields are empty.

        Given: Settings instance with all SMTP fields empty or unset
        When: The smtp_configured property is accessed
        Then: It returns False
        """
        env_overrides = {
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test-key",
            "SMTP_HOST": "",
            "SMTP_PORT": "0",
            "SMTP_USER": "",
            "SMTP_PASSWORD": "",
            "SMTP_FROM": "",
        }

        with patch.dict(os.environ, env_overrides, clear=False):
            from app.core.config import Settings

            settings = Settings(
                smtp_host="",
                smtp_port=0,
                smtp_user="",
                smtp_password="",
                smtp_from="",
            )

            assert settings.smtp_configured is False

    def test_smtp_configured_true_when_all_populated(self):
        """
        15-2-email-notification-service-UNIT-018: smtp_configured returns True when all SMTP fields are populated.

        Given: Settings with all required SMTP fields populated
        When: The smtp_configured property is accessed
        Then: It returns True
        """
        from app.core.config import Settings

        settings = Settings(
            supabase_url="https://test.supabase.co",
            supabase_key="test-key",
            smtp_host="smtp.office365.com",
            smtp_port=587,
            smtp_user="user@plant.com",
            smtp_password="secret",
            smtp_from="noreply@plant.com",
        )

        assert settings.smtp_configured is True

    def test_smtp_configured_false_when_partial(self):
        """
        15-2-email-notification-service-UNIT-019: smtp_configured returns False when partial SMTP fields are set.

        Given: Settings with smtp_host set but smtp_password empty
        When: The smtp_configured property is accessed
        Then: It returns False (all required fields must be non-empty)
        """
        from app.core.config import Settings

        settings = Settings(
            supabase_url="https://test.supabase.co",
            supabase_key="test-key",
            smtp_host="smtp.office365.com",
            smtp_port=587,
            smtp_user="user@plant.com",
            smtp_password="",
            smtp_from="noreply@plant.com",
        )

        assert settings.smtp_configured is False
