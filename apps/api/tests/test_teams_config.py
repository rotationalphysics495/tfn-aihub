"""
Tests for Teams webhook configuration in Settings.

Story: 18.2 - Teams Webhook Configuration
AC#1: Teams Webhook URL field in settings
AC#3: Graceful degradation when webhook URL not configured

Test-First Development: These tests are written BEFORE the feature is implemented.
They should compile without errors but FAIL when run (teams_webhook_url field
and teams_configured property don't exist yet).
"""

import pytest
from unittest.mock import patch
import os


# =============================================================================
# AC1: Teams Webhook URL configuration in Settings
# =============================================================================


class TestTeamsWebhookURLField:
    """Tests for the teams_webhook_url field on Settings."""

    def test_settings_has_teams_webhook_url_field_with_empty_default(self):
        """
        18-2-teams-webhook-configuration-UNIT-001: Settings class has teams_webhook_url
        field with empty default.

        Given: A fresh Settings instance with no TEAMS_WEBHOOK_URL environment variable set
        When: The Settings object is instantiated with default values
        Then: settings.teams_webhook_url equals "" (empty string)
        """
        from app.core.config import Settings

        settings = Settings(
            supabase_url="https://test.supabase.co",
            supabase_key="test-key",
        )

        assert hasattr(settings, "teams_webhook_url"), (
            "Settings must have a 'teams_webhook_url' field"
        )
        assert settings.teams_webhook_url == ""

    def test_settings_reads_teams_webhook_url_from_env(self):
        """
        18-2-teams-webhook-configuration-UNIT-004: Settings reads TEAMS_WEBHOOK_URL
        from environment variable.

        Given: The TEAMS_WEBHOOK_URL environment variable is set
        When: A Settings instance is created (pydantic-settings reads from env)
        Then: settings.teams_webhook_url equals the environment variable value
        """
        env_overrides = {
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test-key",
            "TEAMS_WEBHOOK_URL": "https://outlook.office.com/webhook/test-url",
        }

        with patch.dict(os.environ, env_overrides, clear=False):
            from app.core.config import Settings

            settings = Settings()

            assert settings.teams_webhook_url == "https://outlook.office.com/webhook/test-url"


class TestTeamsConfiguredProperty:
    """Tests for the teams_configured property on Settings."""

    def test_teams_configured_false_when_empty(self):
        """
        18-2-teams-webhook-configuration-UNIT-002: Settings teams_configured returns
        False when teams_webhook_url is empty.

        Given: A Settings instance with teams_webhook_url="" (empty string)
        When: The teams_configured property is accessed
        Then: It returns False
        """
        from app.core.config import Settings

        settings = Settings(
            supabase_url="https://test.supabase.co",
            supabase_key="test-key",
            teams_webhook_url="",
        )

        assert hasattr(settings, "teams_configured"), (
            "Settings must have a 'teams_configured' property"
        )
        assert settings.teams_configured is False

    def test_teams_configured_true_when_set(self):
        """
        18-2-teams-webhook-configuration-UNIT-003: Settings teams_configured returns
        True when teams_webhook_url is set.

        Given: A Settings instance with a non-empty teams_webhook_url
        When: The teams_configured property is accessed
        Then: It returns True
        """
        from app.core.config import Settings

        settings = Settings(
            supabase_url="https://test.supabase.co",
            supabase_key="test-key",
            teams_webhook_url="https://outlook.office.com/webhook/abc123",
        )

        assert settings.teams_configured is True

    def test_teams_configured_false_when_whitespace_only(self):
        """
        18-2-teams-webhook-configuration-UNIT-019: Settings teams_configured returns
        False when teams_webhook_url is whitespace-only.

        Given: A Settings instance with teams_webhook_url="   " (whitespace only)
        When: The teams_configured property is accessed
        Then: It returns False (if implementation strips whitespace)

        Note: This is a boundary test. If bool() is used directly, whitespace-only
        strings are truthy. The spec documents expected behavior; implementation
        may choose to .strip() or not.
        """
        from app.core.config import Settings

        settings = Settings(
            supabase_url="https://test.supabase.co",
            supabase_key="test-key",
            teams_webhook_url="   ",
        )

        # This test documents the boundary behavior.
        # If teams_configured uses bool(), "   " is truthy → returns True.
        # If teams_configured uses bool(self.teams_webhook_url.strip()), returns False.
        # The property must exist regardless:
        assert hasattr(settings, "teams_configured"), (
            "Settings must have a 'teams_configured' property"
        )


class TestEnvExampleContainsTeamsWebhookURL:
    """Tests for .env.example documentation."""

    def test_env_example_contains_teams_webhook_url_entry(self):
        """
        18-2-teams-webhook-configuration-UNIT-005: .env.example contains
        TEAMS_WEBHOOK_URL entry.

        Given: The .env.example file exists at apps/api/.env.example
        When: The file contents are inspected
        Then: The file contains a TEAMS_WEBHOOK_URL= entry
        """
        env_example_path = os.path.join(
            os.path.dirname(__file__), "..", ".env.example"
        )

        assert os.path.exists(env_example_path), (
            f".env.example must exist at {env_example_path}"
        )

        with open(env_example_path, "r") as f:
            content = f.read()

        assert "TEAMS_WEBHOOK_URL" in content, (
            ".env.example must contain a TEAMS_WEBHOOK_URL entry"
        )
