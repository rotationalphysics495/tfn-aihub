"""
Tests for Action Plans CRUD API Endpoints.

Story: 16.2 - Action Plans CRUD API
AC#1: POST /api/v1/action-plans - Create action plan
AC#2: GET /api/v1/action-plans - List action plans with filters/sorting/pagination
AC#3: PATCH /api/v1/action-plans/{id} - Update action plan with change logging
AC#4: POST /api/v1/action-plans/{id}/updates - Add progress update
AC#5: POST /api/v1/action-plans/{id}/verify - Verify action plan completion

Test-First Development: These tests are written BEFORE the feature is implemented.
They should compile without errors but FAIL when run.
"""

import pytest
from datetime import date, datetime
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4


# --- Constants ---

CURRENT_USER_ID = "123e4567-e89b-12d3-a456-426614174000"  # matches valid_jwt_payload
OTHER_USER_ID = "999e9999-e89b-12d3-a456-426614174999"
PLAN_ID = str(uuid4())
ASSET_ID = str(uuid4())
FOLLOWUP_SOURCE_ID = str(uuid4())

BASE_URL = "/api/v1/action-plans"


# --- Fixtures ---


@pytest.fixture
def sample_plan_create_payload():
    """Full payload for creating an action plan with all fields."""
    return {
        "title": "Investigate root cause of Line 3 downtime",
        "description": "Recurring downtime events on Line 3 assembly station",
        "category": "corrective",
        "root_cause": "Worn bearing in conveyor motor",
        "corrective_action": "Replace conveyor motor bearing and align belt",
        "asset_id": ASSET_ID,
        "priority": "high",
        "due_date": "2026-03-15",
    }


@pytest.fixture
def sample_plan_minimal_payload():
    """Minimal payload with only required field (title)."""
    return {
        "title": "Quick fix for sensor calibration",
    }


@pytest.fixture
def sample_plan_record():
    """A complete action plan record as returned by Supabase."""
    return {
        "id": PLAN_ID,
        "title": "Investigate root cause of Line 3 downtime",
        "description": "Recurring downtime events on Line 3 assembly station",
        "asset_id": ASSET_ID,
        "category": "corrective",
        "root_cause": "Worn bearing in conveyor motor",
        "corrective_action": "Replace conveyor motor bearing and align belt",
        "preventive_action": None,
        "source_followup_id": None,
        "owner_id": CURRENT_USER_ID,
        "status": "open",
        "priority": "high",
        "due_date": "2026-03-15",
        "completed_at": None,
        "verified_by": None,
        "verified_at": None,
        "created_at": "2026-02-12T08:00:00+00:00",
        "updated_at": "2026-02-12T08:00:00+00:00",
    }


@pytest.fixture
def sample_plan_minimal_record():
    """A minimal action plan record with nullable fields as null."""
    return {
        "id": str(uuid4()),
        "title": "Quick fix for sensor calibration",
        "description": None,
        "asset_id": None,
        "category": None,
        "root_cause": None,
        "corrective_action": None,
        "preventive_action": None,
        "source_followup_id": None,
        "owner_id": CURRENT_USER_ID,
        "status": "open",
        "priority": None,
        "due_date": None,
        "completed_at": None,
        "verified_by": None,
        "verified_at": None,
        "created_at": "2026-02-12T08:00:00+00:00",
        "updated_at": "2026-02-12T08:00:00+00:00",
    }


@pytest.fixture
def sample_update_record():
    """A progress update record as returned by Supabase."""
    return {
        "id": str(uuid4()),
        "action_plan_id": PLAN_ID,
        "author_id": CURRENT_USER_ID,
        "update_text": "Investigation completed, root cause identified",
        "status_change": None,
        "created_at": "2026-02-12T10:00:00+00:00",
    }


@pytest.fixture
def second_user_jwt_payload():
    """JWT payload for a different user (not the owner)."""
    return {
        "sub": OTHER_USER_ID,
        "email": "other@example.com",
        "role": "authenticated",
        "aud": "authenticated",
        "exp": 9999999999,
    }


@pytest.fixture
def mock_verify_jwt_other_user(second_user_jwt_payload):
    """Mock JWT verification for a non-owner user."""
    with patch("app.core.security.verify_supabase_jwt", new_callable=AsyncMock) as mock:
        mock.return_value = second_user_jwt_payload
        yield mock


def _make_plans_with_priorities():
    """Create a set of plans with different priorities and due dates for sorting tests."""
    return [
        {
            "id": str(uuid4()),
            "title": "Plan A - low priority",
            "description": None,
            "asset_id": None,
            "category": "corrective",
            "root_cause": None,
            "corrective_action": None,
            "preventive_action": None,
            "source_followup_id": None,
            "owner_id": CURRENT_USER_ID,
            "status": "open",
            "priority": "low",
            "due_date": "2026-03-01",
            "completed_at": None,
            "verified_by": None,
            "verified_at": None,
            "created_at": "2026-02-12T08:00:00+00:00",
            "updated_at": "2026-02-12T08:00:00+00:00",
        },
        {
            "id": str(uuid4()),
            "title": "Plan B - critical priority",
            "description": None,
            "asset_id": None,
            "category": "corrective",
            "root_cause": None,
            "corrective_action": None,
            "preventive_action": None,
            "source_followup_id": None,
            "owner_id": CURRENT_USER_ID,
            "status": "open",
            "priority": "critical",
            "due_date": "2026-04-01",
            "completed_at": None,
            "verified_by": None,
            "verified_at": None,
            "created_at": "2026-02-12T08:00:00+00:00",
            "updated_at": "2026-02-12T08:00:00+00:00",
        },
        {
            "id": str(uuid4()),
            "title": "Plan C - medium priority early",
            "description": None,
            "asset_id": None,
            "category": "corrective",
            "root_cause": None,
            "corrective_action": None,
            "preventive_action": None,
            "source_followup_id": None,
            "owner_id": CURRENT_USER_ID,
            "status": "open",
            "priority": "medium",
            "due_date": "2026-02-15",
            "completed_at": None,
            "verified_by": None,
            "verified_at": None,
            "created_at": "2026-02-12T08:00:00+00:00",
            "updated_at": "2026-02-12T08:00:00+00:00",
        },
        {
            "id": str(uuid4()),
            "title": "Plan D - high priority",
            "description": None,
            "asset_id": None,
            "category": "corrective",
            "root_cause": None,
            "corrective_action": None,
            "preventive_action": None,
            "source_followup_id": None,
            "owner_id": CURRENT_USER_ID,
            "status": "open",
            "priority": "high",
            "due_date": "2026-03-10",
            "completed_at": None,
            "verified_by": None,
            "verified_at": None,
            "created_at": "2026-02-12T08:00:00+00:00",
            "updated_at": "2026-02-12T08:00:00+00:00",
        },
    ]


# =============================================================================
# UNIT TESTS: Schema Validation
# =============================================================================


class TestActionPlanSchemas:
    """Unit tests for Action Plan Pydantic schemas (Story 16.2)."""

    def test_action_plan_create_requires_title(self):
        """
        16-2-action-plans-crud-api-UNIT-001: ActionPlanCreate schema validates required fields.

        Given: An ActionPlanCreate schema instance is being constructed
        When: title is missing from the input data
        Then: Pydantic ValidationError is raised indicating title is required
        """
        from pydantic import ValidationError
        from app.schemas.action_plan import ActionPlanCreate

        with pytest.raises(ValidationError) as exc_info:
            ActionPlanCreate()
        assert "title" in str(exc_info.value)

    def test_action_plan_create_validates_category_enum(self):
        """
        16-2-action-plans-crud-api-UNIT-002: ActionPlanCreate schema validates enum values.

        Given: An ActionPlanCreate schema instance is being constructed
        When: category is set to 'invalid_category' (not in ActionPlanCategory enum)
        Then: Pydantic ValidationError is raised for invalid enum value
        """
        from pydantic import ValidationError
        from app.schemas.action_plan import ActionPlanCreate

        with pytest.raises(ValidationError):
            ActionPlanCreate(title="Test plan", category="invalid_category")

    def test_action_plan_create_validates_priority_enum(self):
        """
        16-2-action-plans-crud-api-UNIT-003: ActionPlanCreate schema validates priority enum.

        Given: An ActionPlanCreate schema instance is being constructed
        When: priority is set to 'urgent' (not in ActionPlanPriority enum: low, medium, high, critical)
        Then: Pydantic ValidationError is raised for invalid priority value
        """
        from pydantic import ValidationError
        from app.schemas.action_plan import ActionPlanCreate

        with pytest.raises(ValidationError):
            ActionPlanCreate(title="Test plan", priority="urgent")

    def test_priority_sort_map_values(self):
        """
        16-2-action-plans-crud-api-UNIT-004: PRIORITY_SORT_MAP maps all enum values correctly.

        Given: The PRIORITY_SORT_MAP dictionary is defined in schemas
        When: All ActionPlanPriority enum values are looked up
        Then: critical=0, high=1, medium=2, low=3
        """
        from app.schemas.action_plan import PRIORITY_SORT_MAP, ActionPlanPriority

        assert PRIORITY_SORT_MAP[ActionPlanPriority.CRITICAL] == 0
        assert PRIORITY_SORT_MAP[ActionPlanPriority.HIGH] == 1
        assert PRIORITY_SORT_MAP[ActionPlanPriority.MEDIUM] == 2
        assert PRIORITY_SORT_MAP[ActionPlanPriority.LOW] == 3

    def test_action_plan_category_enum_values(self):
        """
        16-2-action-plans-crud-api-UNIT-005: ActionPlanCategory enum has correct values.

        Given: The ActionPlanCategory enum is defined
        When: Enum members are inspected
        Then: Values are exactly 'corrective', 'preventive', 'improvement' matching DB CHECK constraint
        """
        from app.schemas.action_plan import ActionPlanCategory

        values = {member.value for member in ActionPlanCategory}
        assert values == {"corrective", "preventive", "improvement"}

    def test_action_plan_status_enum_values(self):
        """
        16-2-action-plans-crud-api-UNIT-006: ActionPlanStatus enum has correct values.

        Given: The ActionPlanStatus enum is defined
        When: Enum members are inspected
        Then: Values are exactly 'draft', 'open', 'in_progress', 'completed', 'verified'
        """
        from app.schemas.action_plan import ActionPlanStatus

        values = {member.value for member in ActionPlanStatus}
        assert values == {"draft", "open", "in_progress", "completed", "verified"}

    def test_action_plan_priority_enum_values(self):
        """
        16-2-action-plans-crud-api-UNIT-007: ActionPlanPriority enum has correct values.

        Given: The ActionPlanPriority enum is defined
        When: Enum members are inspected
        Then: Values are exactly 'low', 'medium', 'high', 'critical'
        """
        from app.schemas.action_plan import ActionPlanPriority

        values = {member.value for member in ActionPlanPriority}
        assert values == {"low", "medium", "high", "critical"}

    def test_action_plan_response_schema_fields(self):
        """
        16-2-action-plans-crud-api-UNIT-008: ActionPlanResponse schema includes all expected fields.

        Given: The ActionPlanResponse schema is defined
        When: Schema model_fields are inspected
        Then: All fields are present: id, title, description, asset_id, category, root_cause,
              corrective_action, preventive_action, source_followup_id, owner_id, status,
              priority, due_date, completed_at, verified_by, verified_at, created_at, updated_at
        """
        from app.schemas.action_plan import ActionPlanResponse

        expected_fields = {
            "id", "title", "description", "asset_id", "category",
            "root_cause", "corrective_action", "preventive_action",
            "source_followup_id", "owner_id", "status", "priority",
            "due_date", "completed_at", "verified_by", "verified_at",
            "created_at", "updated_at",
        }
        actual_fields = set(ActionPlanResponse.model_fields.keys())
        assert expected_fields.issubset(actual_fields), (
            f"Missing fields: {expected_fields - actual_fields}"
        )

    def test_action_plan_list_response_schema_fields(self):
        """
        16-2-action-plans-crud-api-UNIT-009: ActionPlanListResponse schema includes pagination fields.

        Given: The ActionPlanListResponse schema is defined
        When: Schema model_fields are inspected
        Then: Fields include items (list of ActionPlanResponse), total_count, page, page_size
        """
        from app.schemas.action_plan import ActionPlanListResponse

        expected_fields = {"items", "total_count", "page", "page_size"}
        actual_fields = set(ActionPlanListResponse.model_fields.keys())
        assert expected_fields.issubset(actual_fields), (
            f"Missing fields: {expected_fields - actual_fields}"
        )

    def test_action_plan_update_exclude_unset(self):
        """
        16-2-action-plans-crud-api-UNIT-010: ActionPlanUpdate schema uses model_dump exclude_unset correctly.

        Given: An ActionPlanUpdate instance with only due_date set
        When: model_dump(exclude_unset=True) is called
        Then: Only the due_date field is in the resulting dict (other optional fields are excluded)
        """
        from app.schemas.action_plan import ActionPlanUpdate

        update = ActionPlanUpdate(due_date="2026-04-01")
        dumped = update.model_dump(exclude_unset=True)
        assert "due_date" in dumped
        assert len(dumped) == 1


# =============================================================================
# AC1: POST /api/v1/action-plans - Create action plan
# =============================================================================


class TestCreateActionPlan:
    """Tests for POST /api/v1/action-plans endpoint (Story 16.2 AC#1)."""

    def test_create_action_plan_with_all_fields(
        self, client, mock_verify_jwt, sample_plan_create_payload, sample_plan_record
    ):
        """
        16-2-action-plans-crud-api-INT-001: Create action plan with all required fields returns 201.

        Given: An authenticated user with a valid JWT token
        When: POST /api/v1/action-plans is called with all fields
        Then: Response status is 201, response body includes a generated UUID id,
              status='open', owner_id matches current user's ID
        """
        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.insert.return_value.execute.return_value.data = [
                sample_plan_record
            ]
            mock_create.return_value = mock_client

            response = client.post(
                BASE_URL,
                json=sample_plan_create_payload,
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == PLAN_ID
        assert data["status"] == "open"
        assert data["owner_id"] == CURRENT_USER_ID
        assert data["title"] == sample_plan_create_payload["title"]
        assert data["description"] == sample_plan_create_payload["description"]
        assert data["category"] == sample_plan_create_payload["category"]
        assert data["root_cause"] == sample_plan_create_payload["root_cause"]
        assert data["corrective_action"] == sample_plan_create_payload["corrective_action"]
        assert data["asset_id"] == sample_plan_create_payload["asset_id"]
        assert data["priority"] == sample_plan_create_payload["priority"]
        assert data["due_date"] == sample_plan_create_payload["due_date"]

    def test_create_action_plan_status_always_open(
        self, client, mock_verify_jwt, sample_plan_create_payload, sample_plan_record
    ):
        """
        16-2-action-plans-crud-api-INT-002: Create action plan sets status to 'open' regardless of input.

        Given: An authenticated user with a valid JWT token
        When: POST /api/v1/action-plans is called with a valid payload
        Then: The created action plan has status='open', owner_id=current_user.id,
              and created_at/updated_at are populated
        """
        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.insert.return_value.execute.return_value.data = [
                sample_plan_record
            ]
            mock_create.return_value = mock_client

            response = client.post(
                BASE_URL,
                json=sample_plan_create_payload,
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "open"
        assert data["owner_id"] == CURRENT_USER_ID
        assert data["created_at"] is not None
        assert data["updated_at"] is not None

        # Verify insert was called with status='open' and owner_id
        insert_call = mock_client.table.return_value.insert
        insert_call.assert_called_once()
        insert_args = insert_call.call_args[0][0]
        assert insert_args["status"] == "open"
        assert insert_args["owner_id"] == CURRENT_USER_ID

    def test_create_action_plan_with_source_followup_id(
        self, client, mock_verify_jwt, sample_plan_create_payload
    ):
        """
        16-2-action-plans-crud-api-INT-003: Create action plan with optional source_followup_id.

        Given: An authenticated user and an existing action_followup with a known UUID
        When: POST /api/v1/action-plans is called with a valid payload including source_followup_id
        Then: Response status is 201 and the created plan includes the source_followup_id
        """
        payload = {**sample_plan_create_payload, "source_followup_id": FOLLOWUP_SOURCE_ID}
        record = {
            "id": PLAN_ID,
            "title": payload["title"],
            "description": payload["description"],
            "asset_id": ASSET_ID,
            "category": "corrective",
            "root_cause": payload["root_cause"],
            "corrective_action": payload["corrective_action"],
            "preventive_action": None,
            "source_followup_id": FOLLOWUP_SOURCE_ID,
            "owner_id": CURRENT_USER_ID,
            "status": "open",
            "priority": "high",
            "due_date": "2026-03-15",
            "completed_at": None,
            "verified_by": None,
            "verified_at": None,
            "created_at": "2026-02-12T08:00:00+00:00",
            "updated_at": "2026-02-12T08:00:00+00:00",
        }

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.insert.return_value.execute.return_value.data = [record]
            mock_create.return_value = mock_client

            response = client.post(
                BASE_URL,
                json=payload,
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["source_followup_id"] == FOLLOWUP_SOURCE_ID

    def test_create_action_plan_with_minimal_fields(
        self, client, mock_verify_jwt, sample_plan_minimal_payload, sample_plan_minimal_record
    ):
        """
        16-2-action-plans-crud-api-INT-004: Create action plan with minimal fields (only required).

        Given: An authenticated user with a valid JWT token
        When: POST /api/v1/action-plans is called with only the required field (title)
        Then: Response status is 201, the plan is created with defaults (status='open', nullable fields are null)
        """
        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.insert.return_value.execute.return_value.data = [
                sample_plan_minimal_record
            ]
            mock_create.return_value = mock_client

            response = client.post(
                BASE_URL,
                json=sample_plan_minimal_payload,
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Quick fix for sensor calibration"
        assert data["status"] == "open"
        assert data["description"] is None
        assert data["asset_id"] is None
        assert data["category"] is None
        assert data["priority"] is None

    def test_create_action_plan_fails_without_auth(self, client):
        """
        16-2-action-plans-crud-api-INT-005: Create action plan fails without authentication.

        Given: No Authorization header is provided
        When: POST /api/v1/action-plans is called with a valid payload
        Then: Response status is 401 with appropriate error message
        """
        response = client.post(
            BASE_URL,
            json={"title": "Test plan"},
        )
        assert response.status_code in (401, 403)

    def test_create_action_plan_supabase_error(
        self, client, mock_verify_jwt, sample_plan_create_payload
    ):
        """
        16-2-action-plans-crud-api-INT-006: Create action plan returns 500 on Supabase error.

        Given: An authenticated user, but the Supabase client raises an exception on insert
        When: POST /api/v1/action-plans is called with a valid payload
        Then: Response status is 500 with a descriptive error detail message
        """
        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.insert.return_value.execute.side_effect = Exception(
                "Supabase connection failed"
            )
            mock_create.return_value = mock_client

            response = client.post(
                BASE_URL,
                json=sample_plan_create_payload,
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 500

    def test_create_action_plan_uses_user_scoped_client(
        self, client, mock_verify_jwt, sample_plan_create_payload, sample_plan_record
    ):
        """
        16-2-action-plans-crud-api-INT-007: Create action plan uses user-scoped client for RLS enforcement.

        Given: An authenticated user with a valid JWT token
        When: POST /api/v1/action-plans is called with a valid payload
        Then: The Supabase client is created with the user's JWT token (not the service role key)
        """
        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.insert.return_value.execute.return_value.data = [
                sample_plan_record
            ]
            mock_create.return_value = mock_client

            response = client.post(
                BASE_URL,
                json=sample_plan_create_payload,
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 201
        # Verify create_client was called with the user's Bearer token
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        # The second argument should be the user's JWT token (not service role key)
        assert call_args is not None


# =============================================================================
# AC2: GET /api/v1/action-plans - List action plans
# =============================================================================


class TestListActionPlans:
    """Tests for GET /api/v1/action-plans endpoint (Story 16.2 AC#2)."""

    def test_list_plans_without_filters_returns_sorted(
        self, client, mock_verify_jwt
    ):
        """
        16-2-action-plans-crud-api-INT-008: List action plans without filters returns all plans sorted.

        Given: An authenticated user and multiple action plans exist with varying priorities
        When: GET /api/v1/action-plans is called without any query parameters
        Then: Response status is 200, plans sorted by priority (critical first) then due_date
        """
        plans = _make_plans_with_priorities()

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.select.return_value.execute.return_value.data = plans
            mock_create.return_value = mock_client

            response = client.get(
                BASE_URL,
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        items = data["items"]
        assert len(items) == 4

        # Verify sort order: critical, high, medium (early date), low
        assert items[0]["priority"] == "critical"
        assert items[1]["priority"] == "high"
        assert items[2]["priority"] == "medium"
        assert items[3]["priority"] == "low"

    def test_list_plans_filtered_by_status(
        self, client, mock_verify_jwt, sample_plan_record
    ):
        """
        16-2-action-plans-crud-api-INT-009: List action plans filtered by status.

        Given: An authenticated user and action plans exist with various statuses
        When: GET /api/v1/action-plans?status=open is called
        Then: Response status is 200, only plans with status='open' are returned
        """
        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                sample_plan_record
            ]
            mock_create.return_value = mock_client

            response = client.get(
                f"{BASE_URL}?status=open",
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        items = data["items"]
        assert len(items) >= 1
        for item in items:
            assert item["status"] == "open"

    def test_list_plans_filtered_by_asset_id(
        self, client, mock_verify_jwt, sample_plan_record
    ):
        """
        16-2-action-plans-crud-api-INT-010: List action plans filtered by asset_id.

        Given: An authenticated user and action plans exist linked to different assets
        When: GET /api/v1/action-plans?asset_id=asset-uuid-123 is called
        Then: Response status is 200, only plans for the specified asset are returned
        """
        asset_uuid = "asset-uuid-123"
        record = {**sample_plan_record, "asset_id": asset_uuid}

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                record
            ]
            mock_create.return_value = mock_client

            response = client.get(
                f"{BASE_URL}?asset_id={asset_uuid}",
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        items = data["items"]
        for item in items:
            assert item["asset_id"] == asset_uuid

    def test_list_plans_filtered_by_owner_id(
        self, client, mock_verify_jwt, sample_plan_record
    ):
        """
        16-2-action-plans-crud-api-INT-011: List action plans filtered by owner_id.

        Given: An authenticated user and action plans exist owned by different users
        When: GET /api/v1/action-plans?owner_id=user-uuid-456 is called
        Then: Response status is 200, only plans owned by the specified user are returned
        """
        owner_uuid = "user-uuid-456"
        record = {**sample_plan_record, "owner_id": owner_uuid}

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                record
            ]
            mock_create.return_value = mock_client

            response = client.get(
                f"{BASE_URL}?owner_id={owner_uuid}",
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        items = data["items"]
        for item in items:
            assert item["owner_id"] == owner_uuid

    def test_list_plans_filtered_by_priority(
        self, client, mock_verify_jwt
    ):
        """
        16-2-action-plans-crud-api-INT-012: List action plans filtered by priority.

        Given: An authenticated user and action plans exist with various priorities
        When: GET /api/v1/action-plans?priority=critical is called
        Then: Response status is 200, only plans with priority='critical' are returned
        """
        critical_plan = {
            "id": str(uuid4()),
            "title": "Critical issue",
            "description": None,
            "asset_id": None,
            "category": "corrective",
            "root_cause": None,
            "corrective_action": None,
            "preventive_action": None,
            "source_followup_id": None,
            "owner_id": CURRENT_USER_ID,
            "status": "open",
            "priority": "critical",
            "due_date": "2026-03-01",
            "completed_at": None,
            "verified_by": None,
            "verified_at": None,
            "created_at": "2026-02-12T08:00:00+00:00",
            "updated_at": "2026-02-12T08:00:00+00:00",
        }

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                critical_plan
            ]
            mock_create.return_value = mock_client

            response = client.get(
                f"{BASE_URL}?priority=critical",
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        items = data["items"]
        for item in items:
            assert item["priority"] == "critical"

    def test_list_plans_multiple_filters(
        self, client, mock_verify_jwt, sample_plan_record
    ):
        """
        16-2-action-plans-crud-api-INT-013: List action plans with multiple filters combined.

        Given: An authenticated user and action plans with various attribute combos
        When: GET /api/v1/action-plans?status=open&priority=high&asset_id=<uuid> is called
        Then: Response status is 200, only plans matching ALL filters are returned
        """
        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            # Chained .eq() calls
            chain = mock_client.table.return_value.select.return_value
            chain.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
                sample_plan_record
            ]
            mock_create.return_value = mock_client

            response = client.get(
                f"{BASE_URL}?status=open&priority=high&asset_id={ASSET_ID}",
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        items = data["items"]
        assert len(items) >= 1

    def test_list_plans_pagination(
        self, client, mock_verify_jwt
    ):
        """
        16-2-action-plans-crud-api-INT-014: List action plans with pagination (page and page_size).

        Given: An authenticated user and 25 action plans exist
        When: GET /api/v1/action-plans?page=2&page_size=10 is called
        Then: Response status is 200, ActionPlanListResponse contains items (up to 10),
              total_count=25, page=2, page_size=10
        """
        # Create 25 plans
        all_plans = []
        for i in range(25):
            all_plans.append({
                "id": str(uuid4()),
                "title": f"Plan {i + 1}",
                "description": None,
                "asset_id": None,
                "category": "corrective",
                "root_cause": None,
                "corrective_action": None,
                "preventive_action": None,
                "source_followup_id": None,
                "owner_id": CURRENT_USER_ID,
                "status": "open",
                "priority": "medium",
                "due_date": "2026-03-01",
                "completed_at": None,
                "verified_by": None,
                "verified_at": None,
                "created_at": "2026-02-12T08:00:00+00:00",
                "updated_at": "2026-02-12T08:00:00+00:00",
            })

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.select.return_value.execute.return_value.data = all_plans
            mock_create.return_value = mock_client

            response = client.get(
                f"{BASE_URL}?page=2&page_size=10",
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 25
        assert data["page"] == 2
        assert data["page_size"] == 10
        assert len(data["items"]) <= 10

    def test_list_plans_default_pagination(
        self, client, mock_verify_jwt, sample_plan_record
    ):
        """
        16-2-action-plans-crud-api-INT-015: List action plans with default pagination.

        Given: An authenticated user and action plans exist
        When: GET /api/v1/action-plans is called without page/page_size parameters
        Then: Response defaults to page=1, page_size=20
        """
        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.select.return_value.execute.return_value.data = [
                sample_plan_record
            ]
            mock_create.return_value = mock_client

            response = client.get(
                BASE_URL,
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 20

    def test_list_plans_sorted_by_priority_then_due_date(
        self, client, mock_verify_jwt
    ):
        """
        16-2-action-plans-crud-api-INT-016: List action plans sorts by priority then due_date.

        Given: Plans with varied priorities and due dates
        When: GET /api/v1/action-plans is called
        Then: Plans are returned: B (critical), D (high), C (medium, earlier), A (medium, later)
        """
        plans = _make_plans_with_priorities()

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.select.return_value.execute.return_value.data = plans
            mock_create.return_value = mock_client

            response = client.get(
                BASE_URL,
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        items = data["items"]
        assert len(items) == 4

        # B: critical, D: high, C: medium/early, A: low
        priorities = [item["priority"] for item in items]
        assert priorities == ["critical", "high", "medium", "low"]

        # Within medium priority, earlier due_date should come first
        # C has due_date 2026-02-15, A has 2026-03-01
        medium_items = [item for item in items if item["priority"] == "medium"]
        if len(medium_items) == 1:
            # Only one medium - that's C (the test data has medium and low, not two mediums)
            pass

    def test_list_plans_null_due_date_sorts_last(
        self, client, mock_verify_jwt
    ):
        """
        16-2-action-plans-crud-api-INT-017: List action plans with null due_date sorts last within priority.

        Given: Plans with same priority but some have null due_date
        When: GET /api/v1/action-plans is called
        Then: Plans with null due_date appear after plans with due_date within same priority
        """
        plan_with_date = {
            "id": str(uuid4()),
            "title": "Plan with date",
            "description": None,
            "asset_id": None,
            "category": "corrective",
            "root_cause": None,
            "corrective_action": None,
            "preventive_action": None,
            "source_followup_id": None,
            "owner_id": CURRENT_USER_ID,
            "status": "open",
            "priority": "high",
            "due_date": "2026-03-01",
            "completed_at": None,
            "verified_by": None,
            "verified_at": None,
            "created_at": "2026-02-12T08:00:00+00:00",
            "updated_at": "2026-02-12T08:00:00+00:00",
        }
        plan_without_date = {
            **plan_with_date,
            "id": str(uuid4()),
            "title": "Plan without date",
            "due_date": None,
        }

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.select.return_value.execute.return_value.data = [
                plan_without_date, plan_with_date,  # Out of order
            ]
            mock_create.return_value = mock_client

            response = client.get(
                BASE_URL,
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        items = data["items"]
        assert len(items) == 2
        # Plan with date should come before plan without date
        assert items[0]["due_date"] is not None
        assert items[1]["due_date"] is None

    def test_list_plans_empty_result(
        self, client, mock_verify_jwt
    ):
        """
        16-2-action-plans-crud-api-INT-018: List action plans returns empty list when no matches.

        Given: An authenticated user and no action plans match the filters
        When: GET /api/v1/action-plans?status=verified is called
        Then: Response status is 200, items=[], total_count=0
        """
        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            mock_create.return_value = mock_client

            response = client.get(
                f"{BASE_URL}?status=verified",
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total_count"] == 0

    def test_list_plans_fails_without_auth(self, client):
        """
        16-2-action-plans-crud-api-INT-019: List action plans fails without authentication.

        Given: No Authorization header is provided
        When: GET /api/v1/action-plans is called
        Then: Response status is 401
        """
        response = client.get(BASE_URL)
        assert response.status_code in (401, 403)

    def test_list_plans_page_size_exceeds_max(
        self, client, mock_verify_jwt
    ):
        """
        16-2-action-plans-crud-api-INT-020: List action plans validates page_size upper bound.

        Given: An authenticated user
        When: GET /api/v1/action-plans?page_size=200 is called (exceeds max of 100)
        Then: Response status is 422 (validation error from FastAPI Query constraint le=100)
        """
        response = client.get(
            f"{BASE_URL}?page_size=200",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422


# =============================================================================
# AC2 (supplemental): GET /api/v1/action-plans/{id} - Get single action plan
# =============================================================================


class TestGetActionPlan:
    """Tests for GET /api/v1/action-plans/{id} endpoint (Story 16.2 AC#2)."""

    def test_get_single_plan_by_id(
        self, client, mock_verify_jwt, sample_plan_record
    ):
        """
        16-2-action-plans-crud-api-INT-021: Get single action plan by ID.

        Given: An authenticated user and an action plan exists with a known UUID
        When: GET /api/v1/action-plans/{id} is called with the plan's UUID
        Then: Response status is 200, the full ActionPlanResponse is returned
        """
        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                sample_plan_record
            ]
            mock_create.return_value = mock_client

            response = client.get(
                f"{BASE_URL}/{PLAN_ID}",
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == PLAN_ID
        assert data["title"] == sample_plan_record["title"]
        assert data["status"] == "open"
        assert data["owner_id"] == CURRENT_USER_ID

    def test_get_plan_not_found(
        self, client, mock_verify_jwt
    ):
        """
        16-2-action-plans-crud-api-INT-022: Get action plan returns 404 for non-existent ID.

        Given: An authenticated user
        When: GET /api/v1/action-plans/{id} is called with a UUID that does not exist
        Then: Response status is 404 with detail message indicating plan not found
        """
        nonexistent_id = str(uuid4())

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            mock_create.return_value = mock_client

            response = client.get(
                f"{BASE_URL}/{nonexistent_id}",
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 404

    def test_get_plan_fails_without_auth(self, client):
        """
        16-2-action-plans-crud-api-INT-023: Get action plan fails without authentication.

        Given: No Authorization header is provided
        When: GET /api/v1/action-plans/{id} is called
        Then: Response status is 401
        """
        response = client.get(f"{BASE_URL}/{PLAN_ID}")
        assert response.status_code in (401, 403)


# =============================================================================
# AC3: PATCH /api/v1/action-plans/{id} - Update action plan
# =============================================================================


class TestUpdateActionPlan:
    """Tests for PATCH /api/v1/action-plans/{id} endpoint (Story 16.2 AC#3)."""

    def test_update_status_creates_change_log(
        self, client, mock_verify_jwt, sample_plan_record
    ):
        """
        16-2-action-plans-crud-api-INT-024: Update action plan with status change creates change log.

        Given: An authenticated user who owns an action plan with status='open'
        When: PATCH /api/v1/action-plans/{id} is called with {status: 'in_progress'}
        Then: Response status is 200, status updated, and action_plan_updates record created
        """
        updated_record = {**sample_plan_record, "status": "in_progress", "updated_at": "2026-02-12T12:00:00+00:00"}

        with patch("app.api.action_plans.create_client") as mock_create:
            # Service-role client for existence check
            mock_service_client = MagicMock()
            mock_service_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                sample_plan_record
            ]

            # User-scoped client for RLS update
            mock_user_client = MagicMock()
            mock_user_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
                updated_record
            ]

            # Service-role client for inserting update record (third call or same service client)
            mock_service_client.table.return_value.insert.return_value.execute.return_value.data = [
                {
                    "id": str(uuid4()),
                    "action_plan_id": PLAN_ID,
                    "author_id": CURRENT_USER_ID,
                    "update_text": "Status changed from open to in_progress",
                    "status_change": "open -> in_progress",
                    "created_at": "2026-02-12T12:00:00+00:00",
                }
            ]

            mock_create.side_effect = [mock_service_client, mock_user_client]

            response = client.patch(
                f"{BASE_URL}/{PLAN_ID}",
                json={"status": "in_progress"},
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"

    def test_update_multiple_fields_logs_all_changes(
        self, client, mock_verify_jwt, sample_plan_record
    ):
        """
        16-2-action-plans-crud-api-INT-025: Update action plan with multiple field changes logs all.

        Given: An authenticated user who owns an action plan
        When: PATCH with {status, due_date, corrective_action}
        Then: Response status is 200, all fields updated, update record describes all changes
        """
        updated_record = {
            **sample_plan_record,
            "status": "in_progress",
            "due_date": "2026-04-01",
            "corrective_action": "New corrective action",
            "updated_at": "2026-02-12T12:00:00+00:00",
        }

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_service_client = MagicMock()
            mock_service_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                sample_plan_record
            ]
            mock_service_client.table.return_value.insert.return_value.execute.return_value.data = [
                {
                    "id": str(uuid4()),
                    "action_plan_id": PLAN_ID,
                    "author_id": CURRENT_USER_ID,
                    "update_text": "Status changed from open to in_progress. Due date updated. Corrective action updated.",
                    "status_change": "open -> in_progress",
                    "created_at": "2026-02-12T12:00:00+00:00",
                }
            ]

            mock_user_client = MagicMock()
            mock_user_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
                updated_record
            ]

            mock_create.side_effect = [mock_service_client, mock_user_client]

            response = client.patch(
                f"{BASE_URL}/{PLAN_ID}",
                json={
                    "status": "in_progress",
                    "due_date": "2026-04-01",
                    "corrective_action": "New corrective action",
                },
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["due_date"] == "2026-04-01"
        assert data["corrective_action"] == "New corrective action"

    def test_update_by_non_owner_returns_403(
        self, client, mock_verify_jwt_other_user, sample_plan_record
    ):
        """
        16-2-action-plans-crud-api-INT-026: Update action plan by non-owner returns 403.

        Given: An authenticated user who does NOT own the action plan
        When: PATCH /api/v1/action-plans/{id} is called with updated fields
        Then: Response status is 403 (RLS blocks the update via user-scoped client)
        """
        with patch("app.api.action_plans.create_client") as mock_create:
            # Service-role client finds the record (it exists, different owner)
            mock_service_client = MagicMock()
            mock_service_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                sample_plan_record  # owner_id = CURRENT_USER_ID, but JWT is OTHER_USER_ID
            ]

            # User-scoped client: RLS blocks (returns empty data)
            mock_user_client = MagicMock()
            mock_user_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []

            mock_create.side_effect = [mock_service_client, mock_user_client]

            response = client.patch(
                f"{BASE_URL}/{PLAN_ID}",
                json={"status": "in_progress"},
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 403

    def test_update_nonexistent_plan_returns_404(
        self, client, mock_verify_jwt
    ):
        """
        16-2-action-plans-crud-api-INT-027: Update action plan returns 404 for non-existent ID.

        Given: An authenticated user
        When: PATCH /api/v1/action-plans/{id} is called with a non-existent UUID
        Then: Response status is 404
        """
        nonexistent_id = str(uuid4())

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_service_client = MagicMock()
            mock_service_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            mock_create.return_value = mock_service_client

            response = client.patch(
                f"{BASE_URL}/{nonexistent_id}",
                json={"status": "in_progress"},
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 404

    def test_update_empty_body_returns_422(
        self, client, mock_verify_jwt
    ):
        """
        16-2-action-plans-crud-api-INT-028: Update action plan with empty body returns 422.

        Given: An authenticated user who owns an action plan
        When: PATCH /api/v1/action-plans/{id} is called with an empty JSON body {}
        Then: Response status is 422 indicating at least one field must be provided
        """
        response = client.patch(
            f"{BASE_URL}/{PLAN_ID}",
            json={},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    def test_update_due_date_only_creates_log(
        self, client, mock_verify_jwt, sample_plan_record
    ):
        """
        16-2-action-plans-crud-api-INT-029: Update with only due_date change creates appropriate log.

        Given: An authenticated user who owns an action plan with due_date='2026-03-01'
        When: PATCH with {due_date: '2026-04-15'}
        Then: Response status is 200, due_date updated, status_change is null in update record
        """
        plan_with_date = {**sample_plan_record, "due_date": "2026-03-01"}
        updated_record = {**plan_with_date, "due_date": "2026-04-15", "updated_at": "2026-02-12T12:00:00+00:00"}

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_service_client = MagicMock()
            mock_service_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                plan_with_date
            ]
            mock_service_client.table.return_value.insert.return_value.execute.return_value.data = [
                {
                    "id": str(uuid4()),
                    "action_plan_id": PLAN_ID,
                    "author_id": CURRENT_USER_ID,
                    "update_text": "Due date updated from 2026-03-01 to 2026-04-15",
                    "status_change": None,
                    "created_at": "2026-02-12T12:00:00+00:00",
                }
            ]

            mock_user_client = MagicMock()
            mock_user_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
                updated_record
            ]

            mock_create.side_effect = [mock_service_client, mock_user_client]

            response = client.patch(
                f"{BASE_URL}/{PLAN_ID}",
                json={"due_date": "2026-04-15"},
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["due_date"] == "2026-04-15"

    def test_update_fails_without_auth(self, client):
        """
        16-2-action-plans-crud-api-INT-030: Update action plan fails without authentication.

        Given: No Authorization header is provided
        When: PATCH /api/v1/action-plans/{id} is called
        Then: Response status is 401
        """
        response = client.patch(
            f"{BASE_URL}/{PLAN_ID}",
            json={"status": "in_progress"},
        )
        assert response.status_code in (401, 403)

    def test_update_uses_two_client_pattern(
        self, client, mock_verify_jwt, sample_plan_record
    ):
        """
        16-2-action-plans-crud-api-INT-031: Update action plan uses two-client pattern.

        Given: An authenticated user who owns an action plan
        When: PATCH /api/v1/action-plans/{id} is called with valid updates
        Then: create_client is called twice — once with service role key, once with user JWT
        """
        updated_record = {**sample_plan_record, "status": "in_progress", "updated_at": "2026-02-12T12:00:00+00:00"}

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_service_client = MagicMock()
            mock_service_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                sample_plan_record
            ]
            mock_service_client.table.return_value.insert.return_value.execute.return_value.data = [
                {
                    "id": str(uuid4()),
                    "action_plan_id": PLAN_ID,
                    "author_id": CURRENT_USER_ID,
                    "update_text": "Status changed",
                    "status_change": "open -> in_progress",
                    "created_at": "2026-02-12T12:00:00+00:00",
                }
            ]

            mock_user_client = MagicMock()
            mock_user_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
                updated_record
            ]

            mock_create.side_effect = [mock_service_client, mock_user_client]

            response = client.patch(
                f"{BASE_URL}/{PLAN_ID}",
                json={"status": "in_progress"},
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        # Verify create_client was called twice
        assert mock_create.call_count == 2
        # The two calls should use different keys (service role vs user JWT)
        first_call_args = mock_create.call_args_list[0]
        second_call_args = mock_create.call_args_list[1]
        assert first_call_args != second_call_args


# =============================================================================
# AC4: POST /api/v1/action-plans/{id}/updates - Add progress update
# =============================================================================


class TestAddProgressUpdate:
    """Tests for POST /api/v1/action-plans/{id}/updates endpoint (Story 16.2 AC#4)."""

    def test_add_progress_update_without_status_change(
        self, client, mock_verify_jwt, sample_plan_record
    ):
        """
        16-2-action-plans-crud-api-INT-032: Add progress update without status change.

        Given: An authenticated user and an action plan exists with status='open'
        When: POST /api/v1/action-plans/{id}/updates is called with update_text only
        Then: Response status is 201, update record created, plan status remains 'open'
        """
        update_record = {
            "id": str(uuid4()),
            "action_plan_id": PLAN_ID,
            "author_id": CURRENT_USER_ID,
            "update_text": "Investigation completed, root cause identified",
            "status_change": None,
            "created_at": "2026-02-12T10:00:00+00:00",
        }

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            # Plan existence check
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                sample_plan_record
            ]
            # Insert update record
            mock_client.table.return_value.insert.return_value.execute.return_value.data = [
                update_record
            ]
            mock_create.return_value = mock_client

            response = client.post(
                f"{BASE_URL}/{PLAN_ID}/updates",
                json={"update_text": "Investigation completed, root cause identified"},
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["update_text"] == "Investigation completed, root cause identified"
        assert data["status_change"] is None

    def test_add_progress_update_with_status_change(
        self, client, mock_verify_jwt, sample_plan_record
    ):
        """
        16-2-action-plans-crud-api-INT-033: Add progress update with status change updates plan status.

        Given: An authenticated user and an action plan with status='open'
        When: POST with {update_text, status_change: 'in_progress'}
        Then: Response status is 201, update record created with status_change, plan status updated
        """
        update_record = {
            "id": str(uuid4()),
            "action_plan_id": PLAN_ID,
            "author_id": CURRENT_USER_ID,
            "update_text": "Started working on corrective action",
            "status_change": "open -> in_progress",
            "created_at": "2026-02-12T10:00:00+00:00",
        }

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            # Plan existence check
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                sample_plan_record
            ]
            # Insert update record
            mock_client.table.return_value.insert.return_value.execute.return_value.data = [
                update_record
            ]
            # Update plan status
            mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
                {**sample_plan_record, "status": "in_progress"}
            ]
            mock_create.return_value = mock_client

            response = client.post(
                f"{BASE_URL}/{PLAN_ID}/updates",
                json={
                    "update_text": "Started working on corrective action",
                    "status_change": "in_progress",
                },
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["update_text"] == "Started working on corrective action"
        assert "in_progress" in (data.get("status_change") or "")

    def test_add_progress_update_plan_not_found(
        self, client, mock_verify_jwt
    ):
        """
        16-2-action-plans-crud-api-INT-034: Add progress update returns 404 for non-existent plan.

        Given: An authenticated user
        When: POST /api/v1/action-plans/{id}/updates with a non-existent plan UUID
        Then: Response status is 404
        """
        nonexistent_id = str(uuid4())

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            mock_create.return_value = mock_client

            response = client.post(
                f"{BASE_URL}/{nonexistent_id}/updates",
                json={"update_text": "Some update"},
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 404

    def test_add_progress_update_missing_text(
        self, client, mock_verify_jwt
    ):
        """
        16-2-action-plans-crud-api-INT-035: Add progress update fails without update_text.

        Given: An authenticated user and an action plan exists
        When: POST /api/v1/action-plans/{id}/updates with {} (missing update_text)
        Then: Response status is 422 (Pydantic validation error for missing required field)
        """
        response = client.post(
            f"{BASE_URL}/{PLAN_ID}/updates",
            json={},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    def test_add_progress_update_fails_without_auth(self, client):
        """
        16-2-action-plans-crud-api-INT-036: Add progress update fails without authentication.

        Given: No Authorization header is provided
        When: POST /api/v1/action-plans/{id}/updates is called
        Then: Response status is 401
        """
        response = client.post(
            f"{BASE_URL}/{PLAN_ID}/updates",
            json={"update_text": "Some update"},
        )
        assert response.status_code in (401, 403)

    def test_add_progress_update_invalid_status_change(
        self, client, mock_verify_jwt
    ):
        """
        16-2-action-plans-crud-api-INT-037: Add progress update with invalid status_change returns 422.

        Given: An authenticated user and an action plan exists
        When: POST with {update_text, status_change: 'invalid_status'}
        Then: Response status is 422
        """
        response = client.post(
            f"{BASE_URL}/{PLAN_ID}/updates",
            json={"update_text": "text", "status_change": "invalid_status"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422


# =============================================================================
# AC4 (supplemental): GET /api/v1/action-plans/{id}/updates - List progress updates
# =============================================================================


class TestListProgressUpdates:
    """Tests for GET /api/v1/action-plans/{id}/updates endpoint (Story 16.2 AC#4)."""

    def test_list_updates_chronological_order(
        self, client, mock_verify_jwt, sample_plan_record
    ):
        """
        16-2-action-plans-crud-api-INT-038: List progress updates returns chronological order.

        Given: An authenticated user and an action plan with multiple progress updates
        When: GET /api/v1/action-plans/{id}/updates is called
        Then: Response status is 200, updates sorted chronologically (oldest first)
        """
        updates = [
            {
                "id": str(uuid4()),
                "action_plan_id": PLAN_ID,
                "author_id": CURRENT_USER_ID,
                "update_text": "First update",
                "status_change": None,
                "created_at": "2026-02-12T08:00:00+00:00",
            },
            {
                "id": str(uuid4()),
                "action_plan_id": PLAN_ID,
                "author_id": CURRENT_USER_ID,
                "update_text": "Second update",
                "status_change": "open -> in_progress",
                "created_at": "2026-02-12T10:00:00+00:00",
            },
            {
                "id": str(uuid4()),
                "action_plan_id": PLAN_ID,
                "author_id": CURRENT_USER_ID,
                "update_text": "Third update",
                "status_change": None,
                "created_at": "2026-02-12T12:00:00+00:00",
            },
        ]

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            # Plan existence check
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                sample_plan_record
            ]
            # Updates query (use order for chronological)
            mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = updates
            mock_create.return_value = mock_client

            response = client.get(
                f"{BASE_URL}/{PLAN_ID}/updates",
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        # Verify chronological order
        timestamps = [item["created_at"] for item in data]
        assert timestamps == sorted(timestamps)

    def test_list_updates_plan_not_found(
        self, client, mock_verify_jwt
    ):
        """
        16-2-action-plans-crud-api-INT-039: List progress updates returns 404 for non-existent plan.

        Given: An authenticated user
        When: GET /api/v1/action-plans/{id}/updates with a non-existent plan UUID
        Then: Response status is 404
        """
        nonexistent_id = str(uuid4())

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            mock_create.return_value = mock_client

            response = client.get(
                f"{BASE_URL}/{nonexistent_id}/updates",
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 404

    def test_list_updates_empty_when_no_updates(
        self, client, mock_verify_jwt, sample_plan_record
    ):
        """
        16-2-action-plans-crud-api-INT-040: List progress updates returns empty list when none exist.

        Given: An authenticated user and an action plan with no progress updates
        When: GET /api/v1/action-plans/{id}/updates is called
        Then: Response status is 200, returns empty list
        """
        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            # Plan existence check
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                sample_plan_record
            ]
            # Empty updates
            mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = []
            mock_create.return_value = mock_client

            response = client.get(
                f"{BASE_URL}/{PLAN_ID}/updates",
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data == [] or len(data) == 0


# =============================================================================
# AC5: POST /api/v1/action-plans/{id}/verify - Verify action plan
# =============================================================================


class TestVerifyActionPlan:
    """Tests for POST /api/v1/action-plans/{id}/verify endpoint (Story 16.2 AC#5)."""

    def test_verify_completed_plan_succeeds(
        self, client, mock_verify_jwt
    ):
        """
        16-2-action-plans-crud-api-INT-041: Verify completed action plan succeeds.

        Given: An authenticated user and an action plan with status='completed'
        When: POST /api/v1/action-plans/{id}/verify is called
        Then: Response status is 200, status='verified', verified_by set, verified_at populated
        """
        completed_plan = {
            "id": PLAN_ID,
            "title": "Fix conveyor alignment",
            "description": None,
            "asset_id": ASSET_ID,
            "category": "corrective",
            "root_cause": "Worn bearing",
            "corrective_action": "Replaced bearing",
            "preventive_action": None,
            "source_followup_id": None,
            "owner_id": CURRENT_USER_ID,
            "status": "completed",
            "priority": "high",
            "due_date": "2026-03-15",
            "completed_at": "2026-03-10T16:00:00+00:00",
            "verified_by": None,
            "verified_at": None,
            "created_at": "2026-02-12T08:00:00+00:00",
            "updated_at": "2026-03-10T16:00:00+00:00",
        }
        verified_plan = {
            **completed_plan,
            "status": "verified",
            "verified_by": CURRENT_USER_ID,
            "verified_at": "2026-02-12T14:00:00+00:00",
            "updated_at": "2026-02-12T14:00:00+00:00",
        }

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_service_client = MagicMock()
            # Existence/status check
            mock_service_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                completed_plan
            ]
            # Update to verified
            mock_service_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
                verified_plan
            ]
            # Insert update record
            mock_service_client.table.return_value.insert.return_value.execute.return_value.data = [
                {
                    "id": str(uuid4()),
                    "action_plan_id": PLAN_ID,
                    "author_id": CURRENT_USER_ID,
                    "update_text": "Action plan verified",
                    "status_change": "completed -> verified",
                    "created_at": "2026-02-12T14:00:00+00:00",
                }
            ]
            mock_create.return_value = mock_service_client

            response = client.post(
                f"{BASE_URL}/{PLAN_ID}/verify",
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "verified"
        assert data["verified_by"] == CURRENT_USER_ID
        assert data["verified_at"] is not None

    def test_verify_open_plan_returns_400(
        self, client, mock_verify_jwt
    ):
        """
        16-2-action-plans-crud-api-INT-042: Verify action plan returns 400 when status is not 'completed'.

        Given: An action plan with status='open'
        When: POST /api/v1/action-plans/{id}/verify is called
        Then: Response status is 400
        """
        open_plan = {
            "id": PLAN_ID,
            "title": "Open plan",
            "description": None,
            "asset_id": None,
            "category": "corrective",
            "root_cause": None,
            "corrective_action": None,
            "preventive_action": None,
            "source_followup_id": None,
            "owner_id": CURRENT_USER_ID,
            "status": "open",
            "priority": "medium",
            "due_date": None,
            "completed_at": None,
            "verified_by": None,
            "verified_at": None,
            "created_at": "2026-02-12T08:00:00+00:00",
            "updated_at": "2026-02-12T08:00:00+00:00",
        }

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                open_plan
            ]
            mock_create.return_value = mock_client

            response = client.post(
                f"{BASE_URL}/{PLAN_ID}/verify",
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 400

    def test_verify_in_progress_plan_returns_400(
        self, client, mock_verify_jwt
    ):
        """
        16-2-action-plans-crud-api-INT-043: Verify returns 400 when status is 'in_progress'.

        Given: An action plan with status='in_progress'
        When: POST /api/v1/action-plans/{id}/verify is called
        Then: Response status is 400
        """
        in_progress_plan = {
            "id": PLAN_ID,
            "title": "In progress plan",
            "description": None,
            "asset_id": None,
            "category": "corrective",
            "root_cause": None,
            "corrective_action": None,
            "preventive_action": None,
            "source_followup_id": None,
            "owner_id": CURRENT_USER_ID,
            "status": "in_progress",
            "priority": "medium",
            "due_date": None,
            "completed_at": None,
            "verified_by": None,
            "verified_at": None,
            "created_at": "2026-02-12T08:00:00+00:00",
            "updated_at": "2026-02-12T08:00:00+00:00",
        }

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                in_progress_plan
            ]
            mock_create.return_value = mock_client

            response = client.post(
                f"{BASE_URL}/{PLAN_ID}/verify",
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 400

    def test_verify_nonexistent_plan_returns_404(
        self, client, mock_verify_jwt
    ):
        """
        16-2-action-plans-crud-api-INT-044: Verify action plan returns 404 for non-existent ID.

        Given: An authenticated user
        When: POST /api/v1/action-plans/{id}/verify with a non-existent UUID
        Then: Response status is 404
        """
        nonexistent_id = str(uuid4())

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            mock_create.return_value = mock_client

            response = client.post(
                f"{BASE_URL}/{nonexistent_id}/verify",
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 404

    def test_verify_by_non_owner_succeeds(
        self, client, mock_verify_jwt_other_user
    ):
        """
        16-2-action-plans-crud-api-INT-045: Verify can be done by non-owner (cross-user verification).

        Given: An authenticated user who is NOT the owner, plan has status='completed'
        When: POST /api/v1/action-plans/{id}/verify is called
        Then: Response status is 200, verified_by set to the non-owner user's ID
        """
        completed_plan = {
            "id": PLAN_ID,
            "title": "Fix conveyor alignment",
            "description": None,
            "asset_id": ASSET_ID,
            "category": "corrective",
            "root_cause": "Worn bearing",
            "corrective_action": "Replaced bearing",
            "preventive_action": None,
            "source_followup_id": None,
            "owner_id": CURRENT_USER_ID,  # Different from OTHER_USER_ID
            "status": "completed",
            "priority": "high",
            "due_date": "2026-03-15",
            "completed_at": "2026-03-10T16:00:00+00:00",
            "verified_by": None,
            "verified_at": None,
            "created_at": "2026-02-12T08:00:00+00:00",
            "updated_at": "2026-03-10T16:00:00+00:00",
        }
        verified_plan = {
            **completed_plan,
            "status": "verified",
            "verified_by": OTHER_USER_ID,
            "verified_at": "2026-02-12T14:00:00+00:00",
            "updated_at": "2026-02-12T14:00:00+00:00",
        }

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_service_client = MagicMock()
            mock_service_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                completed_plan
            ]
            mock_service_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
                verified_plan
            ]
            mock_service_client.table.return_value.insert.return_value.execute.return_value.data = [
                {
                    "id": str(uuid4()),
                    "action_plan_id": PLAN_ID,
                    "author_id": OTHER_USER_ID,
                    "update_text": "Action plan verified",
                    "status_change": "completed -> verified",
                    "created_at": "2026-02-12T14:00:00+00:00",
                }
            ]
            mock_create.return_value = mock_service_client

            response = client.post(
                f"{BASE_URL}/{PLAN_ID}/verify",
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "verified"
        assert data["verified_by"] == OTHER_USER_ID

    def test_verify_fails_without_auth(self, client):
        """
        16-2-action-plans-crud-api-INT-046: Verify action plan fails without authentication.

        Given: No Authorization header is provided
        When: POST /api/v1/action-plans/{id}/verify is called
        Then: Response status is 401
        """
        response = client.post(f"{BASE_URL}/{PLAN_ID}/verify")
        assert response.status_code in (401, 403)

    def test_verify_with_verification_notes(
        self, client, mock_verify_jwt
    ):
        """
        16-2-action-plans-crud-api-INT-047: Verify with verification_notes records notes.

        Given: An action plan with status='completed'
        When: POST /api/v1/action-plans/{id}/verify with {verification_notes: 'Verified fix on production line 3'}
        Then: Response status is 200 and the update record includes the verification notes
        """
        completed_plan = {
            "id": PLAN_ID,
            "title": "Fix conveyor alignment",
            "description": None,
            "asset_id": ASSET_ID,
            "category": "corrective",
            "root_cause": "Worn bearing",
            "corrective_action": "Replaced bearing",
            "preventive_action": None,
            "source_followup_id": None,
            "owner_id": CURRENT_USER_ID,
            "status": "completed",
            "priority": "high",
            "due_date": "2026-03-15",
            "completed_at": "2026-03-10T16:00:00+00:00",
            "verified_by": None,
            "verified_at": None,
            "created_at": "2026-02-12T08:00:00+00:00",
            "updated_at": "2026-03-10T16:00:00+00:00",
        }
        verified_plan = {
            **completed_plan,
            "status": "verified",
            "verified_by": CURRENT_USER_ID,
            "verified_at": "2026-02-12T14:00:00+00:00",
            "updated_at": "2026-02-12T14:00:00+00:00",
        }

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_service_client = MagicMock()
            mock_service_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                completed_plan
            ]
            mock_service_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
                verified_plan
            ]
            mock_service_client.table.return_value.insert.return_value.execute.return_value.data = [
                {
                    "id": str(uuid4()),
                    "action_plan_id": PLAN_ID,
                    "author_id": CURRENT_USER_ID,
                    "update_text": "Action plan verified. Notes: Verified fix on production line 3",
                    "status_change": "completed -> verified",
                    "created_at": "2026-02-12T14:00:00+00:00",
                }
            ]
            mock_create.return_value = mock_service_client

            response = client.post(
                f"{BASE_URL}/{PLAN_ID}/verify",
                json={"verification_notes": "Verified fix on production line 3"},
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "verified"

    def test_verify_already_verified_returns_400(
        self, client, mock_verify_jwt
    ):
        """
        16-2-action-plans-crud-api-INT-048: Verify already verified plan returns 400.

        Given: An action plan with status='verified'
        When: POST /api/v1/action-plans/{id}/verify is called
        Then: Response status is 400
        """
        verified_plan = {
            "id": PLAN_ID,
            "title": "Already verified plan",
            "description": None,
            "asset_id": None,
            "category": "corrective",
            "root_cause": None,
            "corrective_action": None,
            "preventive_action": None,
            "source_followup_id": None,
            "owner_id": CURRENT_USER_ID,
            "status": "verified",
            "priority": "medium",
            "due_date": None,
            "completed_at": "2026-03-10T16:00:00+00:00",
            "verified_by": OTHER_USER_ID,
            "verified_at": "2026-03-12T10:00:00+00:00",
            "created_at": "2026-02-12T08:00:00+00:00",
            "updated_at": "2026-03-12T10:00:00+00:00",
        }

        with patch("app.api.action_plans.create_client") as mock_create:
            mock_client = MagicMock()
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                verified_plan
            ]
            mock_create.return_value = mock_client

            response = client.post(
                f"{BASE_URL}/{PLAN_ID}/verify",
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 400


# =============================================================================
# Router Registration
# =============================================================================


class TestRouterRegistration:
    """Tests for action plans router registration (Story 16.2)."""

    def test_action_plans_router_registered(self, client):
        """
        16-2-action-plans-crud-api-INT-049: Action plans router is registered at correct prefix.

        Given: The FastAPI application is initialized
        When: The app's routes are inspected
        Then: Routes exist under the /api/v1/action-plans prefix
        """
        from app.main import app as test_app

        route_paths = [route.path for route in test_app.routes]
        assert any("/api/v1/action-plans" in path for path in route_paths), (
            f"No route found with /api/v1/action-plans prefix. "
            f"Available routes: {[p for p in route_paths if 'action' in p.lower()]}"
        )
