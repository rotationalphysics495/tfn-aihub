"""
Tests for migration 0031 adding failed_at column to followup_messages.

Story: 15.2 - Email Notification Service
AC#3: Graceful failure on send error (failed_at indicator)

Test-First Development: These tests are written BEFORE the feature is implemented.
They should compile without errors but FAIL when run (migration file doesn't exist yet).
"""

import os
import pytest


# =============================================================================
# Migration Validation
# =============================================================================


class TestMigration0031FailedAt:
    """Tests for migration 0031_followup_messages_failed_at.sql."""

    def test_migration_file_exists(self):
        """
        15-2-email-notification-service-INT-010: Migration 0031 adds failed_at column.

        Given: The followup_messages table exists from migration 0030
        When: Migration 0031_followup_messages_failed_at.sql is applied
        Then: The followup_messages table has a new failed_at column of type TIMESTAMPTZ,
              nullable, defaulting to NULL
        """
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..", "..", "..", "..",
            "supabase", "migrations", "0031_followup_messages_failed_at.sql",
        )

        assert os.path.exists(migration_path), (
            "Migration file 0031_followup_messages_failed_at.sql does not exist"
        )

        with open(migration_path, "r") as f:
            content = f.read()

        # Must add failed_at column
        assert "failed_at" in content, "Migration must add a failed_at column"

        # Must be TIMESTAMPTZ type
        content_upper = content.upper()
        assert "TIMESTAMPTZ" in content_upper or "TIMESTAMP WITH TIME ZONE" in content_upper, \
            "failed_at column must be TIMESTAMPTZ"

        # Must target followup_messages table
        assert "followup_messages" in content, \
            "Migration must target followup_messages table"

        # Must be an ALTER TABLE ADD COLUMN
        assert "ALTER TABLE" in content_upper, \
            "Migration should ALTER TABLE to add the column"
        assert "ADD COLUMN" in content_upper or "ADD" in content_upper, \
            "Migration should ADD COLUMN"

    def test_migration_is_nullable_with_null_default(self):
        """
        15-2-email-notification-service-INT-010 (cont): Column defaults to NULL.

        Given: The migration file exists
        When: The migration SQL is inspected
        Then: The failed_at column is nullable and defaults to NULL
        """
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..", "..", "..", "..",
            "supabase", "migrations", "0031_followup_messages_failed_at.sql",
        )

        assert os.path.exists(migration_path), (
            "Migration file does not exist"
        )

        with open(migration_path, "r") as f:
            content = f.read().upper()

        # Must NOT have NOT NULL constraint (should be nullable)
        # The column should default to NULL or have no default (implicit NULL)
        assert "NOT NULL" not in content or "DEFAULT NULL" in content, \
            "failed_at column should be nullable (no NOT NULL constraint)"
