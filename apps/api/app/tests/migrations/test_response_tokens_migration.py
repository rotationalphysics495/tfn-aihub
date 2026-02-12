"""
Tests for migration 0032 adding response token columns to followup_messages.

Story: 15.3 - Response Capture via Token Link
AC#1: Response page renders via token link (token storage)
Cross-Cutting: Database migration

Test-First Development: These tests are written BEFORE the feature is implemented.
They should compile without errors but FAIL when run (migration file doesn't exist yet).
"""

import os
import pytest


# =============================================================================
# Migration Validation
# =============================================================================


class TestMigration0032ResponseTokens:
    """Tests for migration 0032_response_tokens.sql."""

    def test_migration_adds_token_columns(self):
        """
        15-3-response-capture-via-token-link-INT-023: Migration 0032 adds token columns
        to followup_messages.

        Given: The followup_messages table exists from migrations 0030 and 0031
        When: Migration 0032_response_tokens.sql is applied
        Then: The followup_messages table has three new columns: response_token (TEXT, nullable),
              token_expires_at (TIMESTAMPTZ, nullable), and token_used_at (TIMESTAMPTZ, nullable)
        """
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..", "..", "..",
            "supabase", "migrations", "0032_response_tokens.sql",
        )

        assert os.path.exists(migration_path), (
            "Migration file 0032_response_tokens.sql does not exist"
        )

        with open(migration_path, "r") as f:
            content = f.read()

        content_upper = content.upper()

        # Must target followup_messages table
        assert "followup_messages" in content, \
            "Migration must target followup_messages table"

        # Must add response_token column
        assert "response_token" in content, \
            "Migration must add response_token column"

        # Must add token_expires_at column
        assert "token_expires_at" in content, \
            "Migration must add token_expires_at column"

        # Must add token_used_at column
        assert "token_used_at" in content, \
            "Migration must add token_used_at column"

        # response_token should be TEXT type
        assert "TEXT" in content_upper, \
            "response_token column must be TEXT type"

        # token_expires_at and token_used_at should be TIMESTAMPTZ
        timestamptz_count = content_upper.count("TIMESTAMPTZ") + \
            content_upper.count("TIMESTAMP WITH TIME ZONE")
        assert timestamptz_count >= 2, \
            "token_expires_at and token_used_at must be TIMESTAMPTZ type"

        # Must be ALTER TABLE ADD COLUMN
        assert "ALTER TABLE" in content_upper, \
            "Migration should ALTER TABLE to add columns"

    def test_migration_creates_unique_partial_index(self):
        """
        15-3-response-capture-via-token-link-INT-024: Migration 0032 creates unique partial
        index on response_token.

        Given: The followup_messages table has the response_token column
        When: Migration 0032_response_tokens.sql is applied
        Then: A unique index idx_followup_messages_response_token is created on response_token
              WHERE response_token IS NOT NULL, enabling fast token lookups while allowing
              multiple NULL values
        """
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..", "..", "..",
            "supabase", "migrations", "0032_response_tokens.sql",
        )

        assert os.path.exists(migration_path), (
            "Migration file 0032_response_tokens.sql does not exist"
        )

        with open(migration_path, "r") as f:
            content = f.read()

        content_upper = content.upper()

        # Must create a unique index
        assert "UNIQUE" in content_upper and "INDEX" in content_upper, \
            "Migration must create a UNIQUE INDEX"

        # Must be on response_token
        assert "response_token" in content, \
            "Index must be on response_token column"

        # Must be a partial index (WHERE IS NOT NULL)
        assert "WHERE" in content_upper, \
            "Index must be a partial index with WHERE clause"
        assert "IS NOT NULL" in content_upper, \
            "Partial index must filter WHERE response_token IS NOT NULL"

        # Index name should follow convention
        assert "idx_followup_messages_response_token" in content, \
            "Index should be named idx_followup_messages_response_token"
