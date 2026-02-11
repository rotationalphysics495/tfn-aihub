"""
Tests for Follow-Ups List API Endpoint.

Story: 13.5 - "My Assignments" Panel
AC: #1 - Panel shows follow-ups grouped by status
AC: #2 - Status group movement and "New update" indicator
AC: #4 - Empty state when no open follow-ups

TDD tests — these MUST FAIL until the followups list endpoint and
schemas are implemented.
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MANAGER_USER_ID = "123e4567-e89b-12d3-a456-426614174000"
OTHER_USER_ID = "987e6543-e21b-34d5-a654-426614174999"
ASSIGNEE_USER_ID = "aaa11111-bbbb-cccc-dddd-eeeeeeee1111"
ASSIGNEE_USER_ID_2 = "aaa22222-bbbb-cccc-dddd-eeeeeeee2222"
ASSIGNEE_EMAIL = "john@company.com"
ASSIGNEE_EMAIL_2 = "jane@company.com"


def _make_followup(
    status="assigned",
    assigned_by=MANAGER_USER_ID,
    assigned_to=ASSIGNEE_USER_ID,
    followup_id=None,
    action_item_id=None,
    created_at=None,
    updated_at=None,
    **overrides,
):
    """Factory for follow-up database records."""
    fid = followup_id or str(uuid4())
    now = datetime.utcnow().isoformat()
    return {
        "id": fid,
        "action_item_id": action_item_id or f"action-safety-{fid[:8]}",
        "action_summary": overrides.get("action_summary", "Investigate pressure anomaly on main valve"),
        "asset_name": overrides.get("asset_name", "Grinder 5"),
        "category": overrides.get("category", "safety"),
        "assigned_to": assigned_to,
        "assigned_by": assigned_by,
        "note": overrides.get("note", "Please check by EOD"),
        "status": status,
        "report_date": overrides.get("report_date", date.today().isoformat()),
        "created_at": created_at or now,
        "updated_at": updated_at or now,
    }


def _make_followups_by_status(assigned_by=MANAGER_USER_ID):
    """Create 3 follow-ups with 1 per status."""
    return [
        _make_followup(status="assigned", assigned_by=assigned_by),
        _make_followup(status="in_progress", assigned_by=assigned_by),
        _make_followup(status="resolved", assigned_by=assigned_by),
    ]


def _make_user_record(user_id, email):
    """Factory for user records (as returned from auth.users lookup)."""
    return {
        "id": user_id,
        "email": email,
    }


# ---------------------------------------------------------------------------
# Schema Unit Tests (UNIT-001, UNIT-002)
# ---------------------------------------------------------------------------

class TestFollowUpListSchemas:
    """Tests for follow-up list Pydantic schemas (Story 13.5)."""

    def test_followup_list_item_includes_assigned_to_email(self):
        """UNIT-001: FollowUpListItem schema includes assigned_to_email field.

        Given: A FollowUpListItem Pydantic model is instantiated with all
               required fields including assigned_to_email
        When: The model is serialized to dict/JSON
        Then: The output includes the assigned_to_email field alongside all
              FollowUpResponse fields
        """
        from app.schemas.action import FollowUpListItem

        item = FollowUpListItem(
            id=str(uuid4()),
            action_item_id="action-safety-abc123",
            action_summary="Investigate pressure anomaly",
            asset_name="Grinder 5",
            category="safety",
            assigned_to=ASSIGNEE_USER_ID,
            assigned_to_email=ASSIGNEE_EMAIL,
            assigned_by=MANAGER_USER_ID,
            note="Check by EOD",
            status="assigned",
            report_date=date.today().isoformat(),
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        )

        data = item.model_dump()

        # All FollowUpResponse fields
        assert "id" in data
        assert "action_item_id" in data
        assert "action_summary" in data
        assert "asset_name" in data
        assert "category" in data
        assert "assigned_to" in data
        assert "assigned_by" in data
        assert "note" in data
        assert "status" in data
        assert "report_date" in data
        assert "created_at" in data
        assert "updated_at" in data

        # NEW field
        assert "assigned_to_email" in data
        assert data["assigned_to_email"] == ASSIGNEE_EMAIL

    def test_followup_list_response_validates_counts_by_status(self):
        """UNIT-002: FollowUpListResponse validates counts_by_status.

        Given: A FollowUpListResponse is constructed with followups list,
               total_count, and counts_by_status dict
        When: The model is validated
        Then: The schema accepts the structure with proper types;
              counts_by_status maps status strings to integers
        """
        from app.schemas.action import FollowUpListResponse, FollowUpListItem

        items = [
            FollowUpListItem(
                id=str(uuid4()),
                action_item_id="action-safety-a1",
                action_summary="Investigate safety event",
                asset_name="Grinder 5",
                category="safety",
                assigned_to=ASSIGNEE_USER_ID,
                assigned_to_email=ASSIGNEE_EMAIL,
                assigned_by=MANAGER_USER_ID,
                status="assigned",
                report_date=date.today().isoformat(),
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
            ),
            FollowUpListItem(
                id=str(uuid4()),
                action_item_id="action-safety-a2",
                action_summary="Investigate oee gap",
                asset_name="Lathe 3",
                category="oee",
                assigned_to=ASSIGNEE_USER_ID,
                assigned_to_email=ASSIGNEE_EMAIL,
                assigned_by=MANAGER_USER_ID,
                status="assigned",
                report_date=date.today().isoformat(),
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
            ),
            FollowUpListItem(
                id=str(uuid4()),
                action_item_id="action-oee-b1",
                action_summary="Review performance",
                asset_name="Press 2",
                category="oee",
                assigned_to=ASSIGNEE_USER_ID_2,
                assigned_to_email=ASSIGNEE_EMAIL_2,
                assigned_by=MANAGER_USER_ID,
                status="in_progress",
                report_date=date.today().isoformat(),
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
            ),
        ]

        response = FollowUpListResponse(
            followups=items,
            total_count=3,
            counts_by_status={"assigned": 2, "in_progress": 1, "resolved": 0},
        )

        data = response.model_dump()
        assert data["total_count"] == 3
        assert isinstance(data["counts_by_status"], dict)
        assert data["counts_by_status"]["assigned"] == 2
        assert data["counts_by_status"]["in_progress"] == 1
        assert data["counts_by_status"]["resolved"] == 0


# ---------------------------------------------------------------------------
# Integration Tests (INT-001 to INT-009)
# ---------------------------------------------------------------------------

class TestFollowUpsListEndpoint:
    """Integration tests for GET /api/v1/actions/followups endpoint (Story 13.5)."""

    def test_followups_list_requires_auth(self, client):
        """INT-006: Backend requires authentication.

        Given: No Bearer token is provided in the request
        When: GET /api/v1/actions/followups is called without Authorization header
        Then: The response returns status 401 Unauthorized
        """
        response = client.get("/api/v1/actions/followups")
        assert response.status_code in (401, 403)

    def test_followups_list_returns_own_assignments(
        self, client, mock_verify_jwt, mock_action_engine
    ):
        """INT-001: Backend returns follow-ups filtered by assigned_by=me.

        Given: The authenticated manager has created 3 follow-up assignments
               (1 assigned, 1 in_progress, 1 resolved) and at least 1
               follow-up assigned_by a different user
        When: GET /api/v1/actions/followups?assigned_by=me is called
        Then: The response returns status 200 with all 3 follow-ups where
              assigned_by matches the current user's ID, counts_by_status
              shows {"assigned": 1, "in_progress": 1, "resolved": 1},
              total_count is 3
        """
        # Data: 3 follow-ups by manager + 1 by other user (should NOT be returned)
        manager_followups = _make_followups_by_status(assigned_by=MANAGER_USER_ID)
        other_followup = _make_followup(
            status="assigned", assigned_by=OTHER_USER_ID
        )

        mock_client = MagicMock()
        mock_action_engine._get_client = MagicMock(return_value=mock_client)

        # Mock the Supabase query chain for follow-ups
        mock_chain = MagicMock()
        mock_client.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.execute.return_value.data = manager_followups

        # Mock user lookup for assigned_to_email resolution
        mock_client.rpc = MagicMock()
        mock_client.rpc.return_value.execute.return_value.data = [
            _make_user_record(ASSIGNEE_USER_ID, ASSIGNEE_EMAIL),
        ]

        response = client.get(
            "/api/v1/actions/followups?assigned_by=me",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "followups" in data
        assert "total_count" in data
        assert "counts_by_status" in data

        assert data["total_count"] == 3
        assert len(data["followups"]) == 3
        assert data["counts_by_status"] == {
            "assigned": 1,
            "in_progress": 1,
            "resolved": 1,
        }

    def test_followups_list_resolves_assigned_to_email(
        self, client, mock_verify_jwt, mock_action_engine
    ):
        """INT-002: Backend resolves assigned_to UUIDs to email addresses.

        Given: A follow-up exists with assigned_to pointing to a valid user UUID
        When: GET /api/v1/actions/followups?assigned_by=me is called
        Then: Each follow-up includes assigned_to_email with the resolved email
        """
        followups = [
            _make_followup(
                status="assigned",
                assigned_to=ASSIGNEE_USER_ID,
            ),
        ]

        mock_client = MagicMock()
        mock_action_engine._get_client = MagicMock(return_value=mock_client)

        mock_chain = MagicMock()
        mock_client.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.execute.return_value.data = followups

        mock_client.rpc = MagicMock()
        mock_client.rpc.return_value.execute.return_value.data = [
            _make_user_record(ASSIGNEE_USER_ID, ASSIGNEE_EMAIL),
        ]

        response = client.get(
            "/api/v1/actions/followups?assigned_by=me",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["followups"]) == 1
        followup = data["followups"][0]
        assert "assigned_to_email" in followup
        assert followup["assigned_to_email"] == ASSIGNEE_EMAIL

    def test_followups_list_filters_by_status_active(
        self, client, mock_verify_jwt, mock_action_engine
    ):
        """INT-003: Backend filters by status=active parameter.

        Given: The manager has follow-ups in all 3 statuses
        When: GET /api/v1/actions/followups?assigned_by=me&status=active
        Then: Only "assigned" or "in_progress" are returned; resolved excluded
        """
        all_followups = _make_followups_by_status()

        mock_client = MagicMock()
        mock_action_engine._get_client = MagicMock(return_value=mock_client)

        mock_chain = MagicMock()
        mock_client.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.in_.return_value = mock_chain
        # When filtering by active, only assigned + in_progress should come back
        active_only = [f for f in all_followups if f["status"] != "resolved"]
        mock_chain.execute.return_value.data = active_only

        mock_client.rpc = MagicMock()
        mock_client.rpc.return_value.execute.return_value.data = [
            _make_user_record(ASSIGNEE_USER_ID, ASSIGNEE_EMAIL),
        ]

        response = client.get(
            "/api/v1/actions/followups?assigned_by=me&status=active",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        data = response.json()

        # Resolved should NOT be included
        statuses = [f["status"] for f in data["followups"]]
        assert "resolved" not in statuses
        assert len(data["followups"]) == 2

    def test_followups_list_filters_by_specific_status(
        self, client, mock_verify_jwt, mock_action_engine
    ):
        """INT-004: Backend status filter for specific statuses.

        Given: The manager has follow-ups in all 3 statuses
        When: GET /api/v1/actions/followups?assigned_by=me&status=assigned
        Then: Only follow-ups with status "assigned" are returned
        """
        all_followups = _make_followups_by_status()

        mock_client = MagicMock()
        mock_action_engine._get_client = MagicMock(return_value=mock_client)

        mock_chain = MagicMock()
        mock_client.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        assigned_only = [f for f in all_followups if f["status"] == "assigned"]
        mock_chain.execute.return_value.data = assigned_only

        mock_client.rpc = MagicMock()
        mock_client.rpc.return_value.execute.return_value.data = [
            _make_user_record(ASSIGNEE_USER_ID, ASSIGNEE_EMAIL),
        ]

        response = client.get(
            "/api/v1/actions/followups?assigned_by=me&status=assigned",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["followups"]) == 1
        assert data["followups"][0]["status"] == "assigned"

    def test_followups_list_status_all_returns_all(
        self, client, mock_verify_jwt, mock_action_engine
    ):
        """INT-005: Backend status filter for "all" returns all statuses.

        Given: The manager has follow-ups in all 3 statuses
        When: GET /api/v1/actions/followups?assigned_by=me&status=all
        Then: All 3 follow-ups are returned regardless of status
        """
        all_followups = _make_followups_by_status()

        mock_client = MagicMock()
        mock_action_engine._get_client = MagicMock(return_value=mock_client)

        mock_chain = MagicMock()
        mock_client.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.execute.return_value.data = all_followups

        mock_client.rpc = MagicMock()
        mock_client.rpc.return_value.execute.return_value.data = [
            _make_user_record(ASSIGNEE_USER_ID, ASSIGNEE_EMAIL),
        ]

        response = client.get(
            "/api/v1/actions/followups?assigned_by=me&status=all",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == 3
        assert len(data["followups"]) == 3

    def test_followups_list_response_has_all_required_fields(
        self, client, mock_verify_jwt, mock_action_engine
    ):
        """INT-007: Backend response includes all required fields per schema.

        Given: A follow-up assignment exists with all fields populated
        When: GET /api/v1/actions/followups?assigned_by=me is called
        Then: Each follow-up item includes all required fields
        """
        followup = _make_followup(
            status="assigned",
            note="Please check by EOD and report back",
            action_summary="Investigate pressure anomaly on main valve",
            asset_name="Grinder 5",
            category="safety",
        )

        mock_client = MagicMock()
        mock_action_engine._get_client = MagicMock(return_value=mock_client)

        mock_chain = MagicMock()
        mock_client.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.execute.return_value.data = [followup]

        mock_client.rpc = MagicMock()
        mock_client.rpc.return_value.execute.return_value.data = [
            _make_user_record(ASSIGNEE_USER_ID, ASSIGNEE_EMAIL),
        ]

        response = client.get(
            "/api/v1/actions/followups?assigned_by=me",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        data = response.json()
        item = data["followups"][0]

        required_fields = [
            "id",
            "action_item_id",
            "action_summary",
            "asset_name",
            "category",
            "assigned_to",
            "assigned_to_email",
            "assigned_by",
            "note",
            "status",
            "report_date",
            "created_at",
            "updated_at",
        ]
        for field in required_fields:
            assert field in item, f"Missing required field: {field}"

    def test_followups_list_supports_pagination(
        self, client, mock_verify_jwt, mock_action_engine
    ):
        """INT-008: Backend supports pagination with limit and offset.

        Given: The manager has 10 follow-up assignments
        When: GET /api/v1/actions/followups?assigned_by=me&limit=3&offset=0
        Then: The response returns exactly 3 follow-ups, total_count=10,
              and subsequent calls with offset=3 return the next 3 items
        """
        all_followups = [
            _make_followup(status="assigned", followup_id=str(uuid4()))
            for _ in range(10)
        ]

        mock_client = MagicMock()
        mock_action_engine._get_client = MagicMock(return_value=mock_client)

        mock_chain = MagicMock()
        mock_client.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.in_.return_value = mock_chain
        mock_chain.range.return_value = mock_chain
        # Count query returns 10 total, paginated query returns 3
        mock_chain.execute.return_value.data = all_followups[:3]
        mock_chain.execute.return_value.count = 10

        mock_client.rpc = MagicMock()
        mock_client.rpc.return_value.execute.return_value.data = [
            _make_user_record(ASSIGNEE_USER_ID, ASSIGNEE_EMAIL),
        ]

        response = client.get(
            "/api/v1/actions/followups?assigned_by=me&limit=3&offset=0",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["followups"]) == 3
        # total_count should reflect the full count, not just the page
        assert data["total_count"] >= 3

    def test_followups_list_empty_for_no_assignments(
        self, client, mock_verify_jwt, mock_action_engine
    ):
        """INT-009: Backend returns empty list for manager with no follow-ups.

        Given: The authenticated manager has not created any follow-up assignments
        When: GET /api/v1/actions/followups?assigned_by=me is called
        Then: The response returns status 200 with followups=[], total_count=0,
              counts_by_status={"assigned": 0, "in_progress": 0, "resolved": 0}
        """
        mock_client = MagicMock()
        mock_action_engine._get_client = MagicMock(return_value=mock_client)

        mock_chain = MagicMock()
        mock_client.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.execute.return_value.data = []

        response = client.get(
            "/api/v1/actions/followups?assigned_by=me",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["followups"] == []
        assert data["total_count"] == 0
        assert data["counts_by_status"] == {
            "assigned": 0,
            "in_progress": 0,
            "resolved": 0,
        }

    def test_followups_list_updated_at_reflects_status_change(
        self, client, mock_verify_jwt, mock_action_engine
    ):
        """INT-022 (AC2): Backend returns updated_at reflecting latest status change.

        Given: A follow-up was created at T1 with status "assigned" and later
               updated to "in_progress" at T2
        When: GET /api/v1/actions/followups?assigned_by=me is called
        Then: The follow-up's updated_at reflects T2 (not T1)
        """
        t1 = "2026-02-09T08:30:00Z"
        t2 = "2026-02-10T14:00:00Z"

        followup = _make_followup(
            status="in_progress",
            created_at=t1,
            updated_at=t2,
        )

        mock_client = MagicMock()
        mock_action_engine._get_client = MagicMock(return_value=mock_client)

        mock_chain = MagicMock()
        mock_client.table.return_value = mock_chain
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.execute.return_value.data = [followup]

        mock_client.rpc = MagicMock()
        mock_client.rpc.return_value.execute.return_value.data = [
            _make_user_record(ASSIGNEE_USER_ID, ASSIGNEE_EMAIL),
        ]

        response = client.get(
            "/api/v1/actions/followups?assigned_by=me",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        data = response.json()
        item = data["followups"][0]

        # updated_at should be T2, not T1
        assert item["updated_at"] == t2
        assert item["created_at"] == t1
        assert item["updated_at"] > item["created_at"]
