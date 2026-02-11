"""
Tests for Follow-Up Status Updates & RLS.

Story: 13.3 - Follow-Up Status Updates & RLS
AC#1: Assignee can update follow-up status (partial update via PATCH)
AC#2: RLS denies unauthorized updates (403 for non-assignees)
AC#3: Manager sees updated follow-up status (response includes status and note)

Test-First Development: These tests are written BEFORE the feature is implemented.
They should compile without errors but FAIL when run.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4


# --- Constants ---

FOLLOWUP_ID = str(uuid4())
ASSIGNEE_USER_ID = "123e4567-e89b-12d3-a456-426614174000"  # matches valid_jwt_payload
OTHER_USER_ID = "999e9999-e89b-12d3-a456-426614174999"
ASSIGNER_USER_ID = "aaa11111-e89b-12d3-a456-426614174111"

PATCH_URL = f"/api/v1/actions/followups/{FOLLOWUP_ID}"


# --- Fixtures ---


@pytest.fixture
def sample_followup_record():
    """A complete follow-up record as returned by Supabase."""
    return {
        "id": FOLLOWUP_ID,
        "action_item_id": "action-safety-abc123",
        "action_summary": "Check valve pressure on Line 3",
        "asset_name": "Line 3 Assembly",
        "category": "safety",
        "assigned_to": ASSIGNEE_USER_ID,
        "assigned_by": ASSIGNER_USER_ID,
        "status": "assigned",
        "note": None,
        "report_date": "2026-02-10",
        "created_at": "2026-02-10T08:00:00+00:00",
        "updated_at": "2026-02-10T08:00:00+00:00",
    }


@pytest.fixture
def updated_followup_record(sample_followup_record):
    """A follow-up record after status update."""
    return {
        **sample_followup_record,
        "status": "in_progress",
        "note": "Working on this now",
        "updated_at": "2026-02-11T10:30:00+00:00",
    }


@pytest.fixture
def second_user_jwt_payload():
    """JWT payload for a different user (not the assignee)."""
    return {
        "sub": OTHER_USER_ID,
        "email": "other@example.com",
        "role": "authenticated",
        "aud": "authenticated",
        "exp": 9999999999,
    }


@pytest.fixture
def mock_verify_jwt_other_user(second_user_jwt_payload):
    """Mock JWT verification for a non-assignee user."""
    with patch("app.core.security.verify_supabase_jwt", new_callable=AsyncMock) as mock:
        mock.return_value = second_user_jwt_payload
        yield mock


# =============================================================================
# AC1: Assignee can update follow-up status
# =============================================================================


class TestFollowUpStatusUpdate:
    """Tests for PATCH /api/v1/actions/followups/{followup_id} endpoint (Story 13.3 AC#1)."""

    def test_followup_update_full_status_and_note(
        self, client, mock_verify_jwt, sample_followup_record, updated_followup_record
    ):
        """
        13-3-followup-status-updates-rls-UNIT-001: Successful full status update by assignee.

        Given: An authenticated user has a follow-up assigned to them with status "assigned"
        When: They call PATCH with {"status": "in_progress", "note": "Working on this now"}
        Then: Response is 200, response body contains the updated follow-up with all fields
        """
        with patch("app.api.actions.create_client") as mock_create:
            # Service-role client for existence check
            mock_service_client = MagicMock()
            mock_service_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                sample_followup_record
            ]

            # User-scoped client for RLS update
            mock_user_client = MagicMock()
            mock_user_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
                updated_followup_record
            ]

            mock_create.side_effect = [mock_service_client, mock_user_client]

            response = client.patch(
                PATCH_URL,
                json={"status": "in_progress", "note": "Working on this now"},
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["note"] == "Working on this now"
        assert data["id"] == FOLLOWUP_ID
        assert data["action_item_id"] == "action-safety-abc123"
        assert data["action_summary"] == "Check valve pressure on Line 3"
        assert data["asset_name"] == "Line 3 Assembly"
        assert data["assigned_to"] == ASSIGNEE_USER_ID
        assert data["assigned_by"] == ASSIGNER_USER_ID
        assert "updated_at" in data
        assert "created_at" in data
        assert "report_date" in data

    def test_followup_partial_update_status_only(
        self, client, mock_verify_jwt, sample_followup_record
    ):
        """
        13-3-followup-status-updates-rls-UNIT-002: Partial update with status only.

        Given: An authenticated assignee has a follow-up with status "assigned" and note "Initial note"
        When: They call PATCH with {"status": "resolved"}
        Then: Response is 200, Supabase update called with only status field (note NOT included)
        """
        record_with_note = {**sample_followup_record, "note": "Initial note"}
        resolved_record = {
            **record_with_note,
            "status": "resolved",
            "updated_at": "2026-02-11T10:30:00+00:00",
        }

        with patch("app.api.actions.create_client") as mock_create:
            mock_service_client = MagicMock()
            mock_service_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                record_with_note
            ]

            mock_user_client = MagicMock()
            mock_user_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
                resolved_record
            ]

            mock_create.side_effect = [mock_service_client, mock_user_client]

            response = client.patch(
                PATCH_URL,
                json={"status": "resolved"},
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resolved"
        # Original note should be preserved
        assert data["note"] == "Initial note"

        # Verify .update() was called with only status (not note)
        update_call = mock_user_client.table.return_value.update
        update_call.assert_called_once()
        update_args = update_call.call_args[0][0]
        assert "status" in update_args
        assert "note" not in update_args

    def test_followup_partial_update_note_only(
        self, client, mock_verify_jwt, sample_followup_record
    ):
        """
        13-3-followup-status-updates-rls-UNIT-003: Partial update with note only.

        Given: An authenticated assignee has a follow-up with status "in_progress"
        When: They call PATCH with {"note": "Still investigating root cause"}
        Then: Response is 200, Supabase update called with only note field
        """
        in_progress_record = {**sample_followup_record, "status": "in_progress"}
        updated_record = {
            **in_progress_record,
            "note": "Still investigating root cause",
            "updated_at": "2026-02-11T10:30:00+00:00",
        }

        with patch("app.api.actions.create_client") as mock_create:
            mock_service_client = MagicMock()
            mock_service_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                in_progress_record
            ]

            mock_user_client = MagicMock()
            mock_user_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
                updated_record
            ]

            mock_create.side_effect = [mock_service_client, mock_user_client]

            response = client.patch(
                PATCH_URL,
                json={"note": "Still investigating root cause"},
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["note"] == "Still investigating root cause"
        # Original status should be preserved
        assert data["status"] == "in_progress"

        # Verify .update() was called with only note (not status)
        update_call = mock_user_client.table.return_value.update
        update_call.assert_called_once()
        update_args = update_call.call_args[0][0]
        assert "note" in update_args
        assert "status" not in update_args

    def test_followup_update_requires_auth(self, client):
        """
        13-3-followup-status-updates-rls-UNIT-004: Endpoint requires authentication.

        Given: No authentication token is provided
        When: PATCH is called without Authorization header
        Then: Response is 401 Unauthorized
        """
        response = client.patch(
            PATCH_URL,
            json={"status": "in_progress"},
        )
        assert response.status_code in (401, 403)

    def test_followup_update_rejects_invalid_status(
        self, client, mock_verify_jwt
    ):
        """
        13-3-followup-status-updates-rls-UNIT-005: Validation rejects invalid status values.

        Given: An authenticated assignee
        When: They call PATCH with {"status": "completed"} (not in allowed values)
        Then: Response is 422 Unprocessable Entity
        """
        response = client.patch(
            PATCH_URL,
            json={"status": "completed"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    def test_followup_update_rejects_empty_body(
        self, client, mock_verify_jwt
    ):
        """
        13-3-followup-status-updates-rls-UNIT-006: Validation rejects empty update body.

        Given: An authenticated assignee
        When: They call PATCH with {}
        Then: Response is 422 Unprocessable Entity (at least one field required)
        """
        response = client.patch(
            PATCH_URL,
            json={},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    def test_followup_status_assigned_to_in_progress(
        self, client, mock_verify_jwt, sample_followup_record
    ):
        """
        13-3-followup-status-updates-rls-UNIT-007: Status transition from assigned to in_progress.

        Given: An authenticated assignee has a follow-up with status "assigned"
        When: They call PATCH with {"status": "in_progress"}
        Then: Response is 200, status is updated to "in_progress"
        """
        updated_record = {
            **sample_followup_record,
            "status": "in_progress",
            "updated_at": "2026-02-11T10:30:00+00:00",
        }

        with patch("app.api.actions.create_client") as mock_create:
            mock_service_client = MagicMock()
            mock_service_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                sample_followup_record
            ]

            mock_user_client = MagicMock()
            mock_user_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
                updated_record
            ]

            mock_create.side_effect = [mock_service_client, mock_user_client]

            response = client.patch(
                PATCH_URL,
                json={"status": "in_progress"},
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"

    def test_followup_status_in_progress_to_resolved(
        self, client, mock_verify_jwt, sample_followup_record
    ):
        """
        13-3-followup-status-updates-rls-UNIT-008: Status transition from in_progress to resolved.

        Given: An authenticated assignee has a follow-up with status "in_progress"
        When: They call PATCH with {"status": "resolved"}
        Then: Response is 200, status is updated to "resolved"
        """
        in_progress_record = {**sample_followup_record, "status": "in_progress"}
        resolved_record = {
            **in_progress_record,
            "status": "resolved",
            "updated_at": "2026-02-11T10:30:00+00:00",
        }

        with patch("app.api.actions.create_client") as mock_create:
            mock_service_client = MagicMock()
            mock_service_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                in_progress_record
            ]

            mock_user_client = MagicMock()
            mock_user_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
                resolved_record
            ]

            mock_create.side_effect = [mock_service_client, mock_user_client]

            response = client.patch(
                PATCH_URL,
                json={"status": "resolved"},
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resolved"

    def test_followup_status_can_go_back_to_assigned(
        self, client, mock_verify_jwt, sample_followup_record
    ):
        """
        13-3-followup-status-updates-rls-UNIT-009: Status can be set back to assigned.

        Given: An authenticated assignee has a follow-up with status "in_progress"
        When: They call PATCH with {"status": "assigned"}
        Then: Response is 200, status is updated to "assigned" (no forward-only constraint)
        """
        in_progress_record = {**sample_followup_record, "status": "in_progress"}
        reassigned_record = {
            **in_progress_record,
            "status": "assigned",
            "updated_at": "2026-02-11T10:30:00+00:00",
        }

        with patch("app.api.actions.create_client") as mock_create:
            mock_service_client = MagicMock()
            mock_service_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                in_progress_record
            ]

            mock_user_client = MagicMock()
            mock_user_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
                reassigned_record
            ]

            mock_create.side_effect = [mock_service_client, mock_user_client]

            response = client.patch(
                PATCH_URL,
                json={"status": "assigned"},
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "assigned"

    def test_followup_update_both_status_and_note(
        self, client, mock_verify_jwt, sample_followup_record
    ):
        """
        13-3-followup-status-updates-rls-UNIT-010: Update with both status and note simultaneously.

        Given: An authenticated assignee has a follow-up with status "assigned" and no note
        When: They call PATCH with {"status": "resolved", "note": "Issue was resolved by replacing the valve"}
        Then: Response is 200, both fields updated, update dict contains both
        """
        updated_record = {
            **sample_followup_record,
            "status": "resolved",
            "note": "Issue was resolved by replacing the valve",
            "updated_at": "2026-02-11T10:30:00+00:00",
        }

        with patch("app.api.actions.create_client") as mock_create:
            mock_service_client = MagicMock()
            mock_service_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                sample_followup_record
            ]

            mock_user_client = MagicMock()
            mock_user_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
                updated_record
            ]

            mock_create.side_effect = [mock_service_client, mock_user_client]

            response = client.patch(
                PATCH_URL,
                json={
                    "status": "resolved",
                    "note": "Issue was resolved by replacing the valve",
                },
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resolved"
        assert data["note"] == "Issue was resolved by replacing the valve"

        # Verify both fields were passed to .update()
        update_call = mock_user_client.table.return_value.update
        update_call.assert_called_once()
        update_args = update_call.call_args[0][0]
        assert "status" in update_args
        assert "note" in update_args


# =============================================================================
# Schema Validation Tests
# =============================================================================


class TestFollowUpSchemas:
    """Tests for FollowUpUpdateRequest and FollowUpResponse Pydantic schemas (Story 13.3)."""

    def test_followup_update_request_valid_statuses(self):
        """
        13-3-followup-status-updates-rls-UNIT-011: FollowUpUpdateRequest schema validates correctly.

        Given: Various input payloads
        When: Pydantic model is constructed with valid statuses
        Then: Valid statuses pass validation, invalid statuses raise ValidationError
        """
        from app.schemas.action import FollowUpUpdateRequest

        # Valid statuses should pass
        for valid_status in ("assigned", "in_progress", "resolved"):
            model = FollowUpUpdateRequest(status=valid_status)
            assert model.status == valid_status

        # None status is allowed (optional field for partial update)
        model = FollowUpUpdateRequest(note="just a note")
        assert model.status is None

    def test_followup_update_request_invalid_statuses(self):
        """
        13-3-followup-status-updates-rls-UNIT-011 (cont): Invalid statuses raise ValidationError.
        """
        from pydantic import ValidationError
        from app.schemas.action import FollowUpUpdateRequest

        invalid_statuses = ["completed", "pending", "done", "closed", ""]
        for invalid_status in invalid_statuses:
            with pytest.raises(ValidationError):
                FollowUpUpdateRequest(status=invalid_status)

    def test_followup_response_schema_serialization(self):
        """
        13-3-followup-status-updates-rls-UNIT-012: FollowUpResponse schema serializes correctly.

        Given: A raw follow-up record dict from Supabase
        When: FollowUpResponse is constructed
        Then: All fields are correctly serialized
        """
        from app.schemas.action import FollowUpResponse

        record = {
            "id": str(uuid4()),
            "action_item_id": "action-safety-abc123",
            "action_summary": "Check valve pressure on Line 3",
            "asset_name": "Line 3 Assembly",
            "category": "safety",
            "assigned_to": ASSIGNEE_USER_ID,
            "assigned_by": ASSIGNER_USER_ID,
            "status": "in_progress",
            "note": "Working on it",
            "report_date": "2026-02-10",
            "created_at": "2026-02-10T08:00:00+00:00",
            "updated_at": "2026-02-11T10:30:00+00:00",
        }

        model = FollowUpResponse(**record)
        assert model.id == record["id"]
        assert model.action_item_id == record["action_item_id"]
        assert model.action_summary == record["action_summary"]
        assert model.asset_name == record["asset_name"]
        assert model.category == record["category"]
        assert model.assigned_to == record["assigned_to"]
        assert model.assigned_by == record["assigned_by"]
        assert model.status == record["status"]
        assert model.note == record["note"]
        assert model.report_date == record["report_date"]
        assert model.created_at == record["created_at"]
        assert model.updated_at == record["updated_at"]

    def test_followup_response_optional_fields_handle_none(self):
        """
        13-3-followup-status-updates-rls-UNIT-012 (cont): Optional fields handle None values.
        """
        from app.schemas.action import FollowUpResponse

        record = {
            "id": str(uuid4()),
            "action_item_id": "action-safety-abc123",
            "action_summary": "Check valve pressure",
            "asset_name": None,
            "category": None,
            "assigned_to": ASSIGNEE_USER_ID,
            "assigned_by": ASSIGNER_USER_ID,
            "status": "assigned",
            "note": None,
            "report_date": "2026-02-10",
            "created_at": "2026-02-10T08:00:00+00:00",
            "updated_at": "2026-02-10T08:00:00+00:00",
        }

        model = FollowUpResponse(**record)
        assert model.asset_name is None
        assert model.category is None
        assert model.note is None


# =============================================================================
# AC2: RLS denies unauthorized updates
# =============================================================================


class TestFollowUpRLSEnforcement:
    """Tests for RLS enforcement on follow-up updates (Story 13.3 AC#2)."""

    def test_403_when_non_assignee_tries_to_update(
        self, client, mock_verify_jwt_other_user, sample_followup_record
    ):
        """
        13-3-followup-status-updates-rls-UNIT-013: 403 when non-assignee tries to update.

        Given: Authenticated user A attempts to update a follow-up assigned to user B
        When: They call PATCH with {"status": "resolved"}
        Then: Response is 403 Forbidden (service-role SELECT found it, user UPDATE returned 0 rows)
        """
        with patch("app.api.actions.create_client") as mock_create:
            # Service-role client finds the record (it exists)
            mock_service_client = MagicMock()
            mock_service_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                sample_followup_record
            ]

            # User-scoped client: RLS blocks the update (returns empty data)
            mock_user_client = MagicMock()
            mock_user_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []

            mock_create.side_effect = [mock_service_client, mock_user_client]

            response = client.patch(
                PATCH_URL,
                json={"status": "resolved"},
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 403

    def test_404_when_followup_does_not_exist(
        self, client, mock_verify_jwt
    ):
        """
        13-3-followup-status-updates-rls-UNIT-014: 404 when follow-up does not exist.

        Given: An authenticated user attempts to update a non-existent follow-up
        When: They call PATCH with {"status": "in_progress"}
        Then: Response is 404 Not Found (service-role SELECT returned no rows)
        """
        nonexistent_id = str(uuid4())

        with patch("app.api.actions.create_client") as mock_create:
            # Service-role client returns nothing (not found)
            mock_service_client = MagicMock()
            mock_service_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

            mock_create.return_value = mock_service_client

            response = client.patch(
                f"/api/v1/actions/followups/{nonexistent_id}",
                json={"status": "in_progress"},
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 404

    def test_user_scoped_client_used_for_update(
        self, client, mock_verify_jwt, sample_followup_record, updated_followup_record
    ):
        """
        13-3-followup-status-updates-rls-UNIT-015: User-scoped Supabase client is used for update.

        Given: An authenticated assignee with a valid JWT token
        When: They call PATCH
        Then: The update operation uses a Supabase client with the user's JWT (not service role)
        """
        with patch("app.api.actions.create_client") as mock_create:
            mock_service_client = MagicMock()
            mock_service_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                sample_followup_record
            ]

            mock_user_client = MagicMock()
            mock_user_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
                updated_followup_record
            ]

            mock_create.side_effect = [mock_service_client, mock_user_client]

            response = client.patch(
                PATCH_URL,
                json={"status": "in_progress", "note": "Working on this now"},
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200

        # Verify create_client was called twice: once for service-role, once for user-scoped
        assert mock_create.call_count == 2
        # The second call should include the user's JWT token (not service key)
        second_call_args = mock_create.call_args_list[1]
        # The user-scoped client should be created with the user's access token
        # (specific assertion depends on implementation, but the client should differ)
        assert second_call_args != mock_create.call_args_list[0]


# =============================================================================
# Integration Tests: RLS Migration Validation
# =============================================================================


class TestRLSMigration:
    """Integration tests for RLS migration (Story 13.3 AC#2)."""

    def test_rls_migration_has_assignee_update_policy(self):
        """
        13-3-followup-status-updates-rls-INT-001: RLS migration adds correct assignee update policy.

        Given: The migration 0028_followup_assignee_rls.sql has been applied
        When: The policy is inspected
        Then: A new RLS policy exists with correct USING and WITH CHECK clauses
        """
        import os

        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..",
            "supabase", "migrations", "0028_followup_assignee_rls.sql",
        )

        assert os.path.exists(migration_path), (
            "Migration file 0028_followup_assignee_rls.sql does not exist"
        )

        with open(migration_path, "r") as f:
            content = f.read()

        # Verify policy name
        assert "Assignees can update their own followups" in content
        # Verify it's for UPDATE
        assert "FOR UPDATE" in content
        # Verify USING clause
        assert "assigned_to = auth.uid()" in content
        # Verify WITH CHECK clause
        assert "WITH CHECK" in content

    def test_rls_migration_preserves_existing_policies(self):
        """
        13-3-followup-status-updates-rls-INT-002: RLS migration preserves existing policies.

        Given: The migration is applied on top of existing 0025 migration
        When: The migration content is inspected
        Then: It only creates new policy, doesn't drop or alter existing ones
        """
        import os

        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..",
            "supabase", "migrations", "0028_followup_assignee_rls.sql",
        )

        assert os.path.exists(migration_path), (
            "Migration file 0028_followup_assignee_rls.sql does not exist"
        )

        with open(migration_path, "r") as f:
            content = f.read().upper()

        # Must only CREATE, not DROP or ALTER existing policies
        assert "CREATE POLICY" in content
        assert "DROP POLICY" not in content
        assert "ALTER POLICY" not in content

    def test_rls_with_check_prevents_reassignment(
        self, client, mock_verify_jwt, sample_followup_record
    ):
        """
        13-3-followup-status-updates-rls-INT-003: WITH CHECK prevents assignee field reassignment.

        Given: The RLS policy has WITH CHECK (assigned_to = auth.uid())
        When: An assignee attempts to update the assigned_to field to a different user ID
        Then: The update is rejected (either by schema validation or WITH CHECK)
        """
        # Attempt to include assigned_to in the update payload
        response = client.patch(
            PATCH_URL,
            json={
                "status": "resolved",
                "assigned_to": OTHER_USER_ID,  # Trying to reassign
            },
            headers={"Authorization": "Bearer test-token"},
        )

        # Should be rejected - either 422 (schema rejects extra fields)
        # or the assigned_to field should be ignored by the update logic
        # If status is 200, the assigned_to field must NOT have been changed
        if response.status_code == 200:
            data = response.json()
            assert data["assigned_to"] == ASSIGNEE_USER_ID  # Not reassigned
        else:
            # Schema validation rejection is also acceptable
            assert response.status_code == 422


# =============================================================================
# E2E Test: Multi-user authorization
# =============================================================================


class TestFollowUpE2EAuthorization:
    """E2E tests for follow-up authorization (Story 13.3)."""

    def test_unauthorized_user_blocked_from_update(self, client):
        """
        13-3-followup-status-updates-rls-E2E-001: Non-assignee/non-assigner blocked.

        Given: A follow-up exists with assigned_to=UserA and assigned_by=UserB
        When: UserC (neither assignee nor assigner) attempts PATCH
        Then: UserC receives 403 Forbidden
        """
        user_c_payload = {
            "sub": str(uuid4()),  # UserC - neither assignee nor assigner
            "email": "userc@example.com",
            "role": "authenticated",
            "aud": "authenticated",
            "exp": 9999999999,
        }

        followup_record = {
            "id": FOLLOWUP_ID,
            "action_item_id": "action-safety-abc123",
            "action_summary": "Check valve pressure on Line 3",
            "asset_name": "Line 3 Assembly",
            "category": "safety",
            "assigned_to": ASSIGNEE_USER_ID,  # UserA
            "assigned_by": ASSIGNER_USER_ID,  # UserB
            "status": "assigned",
            "note": None,
            "report_date": "2026-02-10",
            "created_at": "2026-02-10T08:00:00+00:00",
            "updated_at": "2026-02-10T08:00:00+00:00",
        }

        with patch(
            "app.core.security.verify_supabase_jwt", new_callable=AsyncMock
        ) as mock_jwt:
            mock_jwt.return_value = user_c_payload

            with patch("app.api.actions.create_client") as mock_create:
                # Service-role: follow-up exists
                mock_service_client = MagicMock()
                mock_service_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                    followup_record
                ]

                # User-scoped: RLS blocks (UserC is not assignee/assigner)
                mock_user_client = MagicMock()
                mock_user_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []

                mock_create.side_effect = [mock_service_client, mock_user_client]

                response = client.patch(
                    PATCH_URL,
                    json={"status": "resolved"},
                    headers={"Authorization": "Bearer test-token"},
                )

        assert response.status_code == 403


# =============================================================================
# AC3: Manager sees updated follow-up status
# =============================================================================


class TestManagerFollowUpVisibility:
    """Tests for manager visibility of follow-up updates (Story 13.3 AC#3)."""

    def test_response_includes_status_and_note_after_update(
        self, client, mock_verify_jwt, sample_followup_record
    ):
        """
        13-3-followup-status-updates-rls-UNIT-016: FollowUpResponse includes status and note.

        Given: An assignee has updated a follow-up to resolved with a note
        When: The PATCH endpoint returns the updated record
        Then: The response includes status, note, and all context fields
        """
        resolved_record = {
            **sample_followup_record,
            "status": "resolved",
            "note": "Fixed the alignment issue",
            "updated_at": "2026-02-11T10:30:00+00:00",
        }

        with patch("app.api.actions.create_client") as mock_create:
            mock_service_client = MagicMock()
            mock_service_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                sample_followup_record
            ]

            mock_user_client = MagicMock()
            mock_user_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
                resolved_record
            ]

            mock_create.side_effect = [mock_service_client, mock_user_client]

            response = client.patch(
                PATCH_URL,
                json={"status": "resolved", "note": "Fixed the alignment issue"},
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resolved"
        assert data["note"] == "Fixed the alignment issue"
        assert data["id"] == FOLLOWUP_ID
        assert data["action_item_id"] == "action-safety-abc123"
        assert data["action_summary"] == "Check valve pressure on Line 3"
        assert data["asset_name"] == "Line 3 Assembly"
        assert data["assigned_to"] == ASSIGNEE_USER_ID
        assert data["assigned_by"] == ASSIGNER_USER_ID
        assert "report_date" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_response_updated_at_reflects_update_time(
        self, client, mock_verify_jwt, sample_followup_record
    ):
        """
        13-3-followup-status-updates-rls-UNIT-017: Response updated_at reflects the update time.

        Given: An assignee updates a follow-up's status
        When: The PATCH endpoint returns the updated record
        Then: updated_at is different from created_at (refreshed by DB trigger)
        """
        updated_record = {
            **sample_followup_record,
            "status": "in_progress",
            "updated_at": "2026-02-11T14:00:00+00:00",  # Later than created_at
        }

        with patch("app.api.actions.create_client") as mock_create:
            mock_service_client = MagicMock()
            mock_service_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                sample_followup_record
            ]

            mock_user_client = MagicMock()
            mock_user_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
                updated_record
            ]

            mock_create.side_effect = [mock_service_client, mock_user_client]

            response = client.patch(
                PATCH_URL,
                json={"status": "in_progress"},
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["updated_at"] != data["created_at"]
        assert data["updated_at"] == "2026-02-11T14:00:00+00:00"

    def test_existing_select_rls_allows_manager_read(self):
        """
        13-3-followup-status-updates-rls-INT-004: Existing SELECT RLS allows manager to read.

        Given: The existing SELECT RLS policy from migration 0025
        When: A manager (assigned_by) queries follow-ups
        Then: The SELECT policy permits reading follow-ups where assigned_by = auth.uid()
        """
        import os

        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..",
            "supabase", "migrations", "0025_action_followups.sql",
        )

        with open(migration_path, "r") as f:
            content = f.read()

        # Verify the existing SELECT policy allows assigned_by to read
        assert "FOR SELECT" in content
        assert "assigned_by = auth.uid()" in content
        # The SELECT policy uses OR so both assigned_to and assigned_by can read
        assert "assigned_to = auth.uid() OR assigned_by = auth.uid()" in content

    def test_response_includes_action_context_fields(
        self, client, mock_verify_jwt, sample_followup_record
    ):
        """
        13-3-followup-status-updates-rls-UNIT-018: Response includes action context fields.

        Given: A follow-up has been updated by the assignee
        When: The response is serialized via FollowUpResponse
        Then: action_summary and asset_name fields are present
        """
        updated_record = {
            **sample_followup_record,
            "status": "resolved",
            "note": "Done",
            "updated_at": "2026-02-11T10:30:00+00:00",
        }

        with patch("app.api.actions.create_client") as mock_create:
            mock_service_client = MagicMock()
            mock_service_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                sample_followup_record
            ]

            mock_user_client = MagicMock()
            mock_user_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
                updated_record
            ]

            mock_create.side_effect = [mock_service_client, mock_user_client]

            response = client.patch(
                PATCH_URL,
                json={"status": "resolved", "note": "Done"},
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["action_summary"] == "Check valve pressure on Line 3"
        assert data["asset_name"] == "Line 3 Assembly"
