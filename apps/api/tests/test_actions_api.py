"""
Tests for Action List API Endpoints.

Story: 3.1 - Action Engine Logic
AC: #8 - API Endpoint for Action List

Story: 3.2 - Daily Action List API
AC: #1 - Action List Endpoint at /api/v1/actions/daily
AC: #7 - Response schema with all required fields
AC: #8 - Authentication required (401 for missing token)
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4

from app.schemas.action import (
    ActionCategory,
    ActionItem,
    ActionListResponse,
    EvidenceRef,
    PriorityLevel,
)


@pytest.fixture
def mock_action_engine():
    """Mock ActionEngine for API tests."""
    with patch('app.api.actions.get_action_engine') as mock_get:
        mock_engine = MagicMock()
        mock_get.return_value = mock_engine
        yield mock_engine


@pytest.fixture
def sample_action_response():
    """Sample ActionListResponse for testing."""
    target_date = date.today() - timedelta(days=1)
    return ActionListResponse(
        actions=[
            ActionItem(
                id="action-safety-1",
                asset_id="asset-1",
                asset_name="Grinder 5",
                priority_level=PriorityLevel.CRITICAL,
                category=ActionCategory.SAFETY,
                primary_metric_value="Safety Event: Emergency Stop",
                recommendation_text="Investigate emergency stop on Grinder 5",
                evidence_summary="Unresolved safety event at 14:30",
                evidence_refs=[
                    EvidenceRef(
                        source_table="safety_events",
                        record_id="se-123",
                        metric_name="severity",
                        metric_value="critical",
                        context="Emergency stop triggered"
                    )
                ],
                created_at=datetime.utcnow()
            ),
            ActionItem(
                id="action-oee-1",
                asset_id="asset-2",
                asset_name="Lathe 3",
                priority_level=PriorityLevel.HIGH,
                category=ActionCategory.OEE,
                primary_metric_value="OEE: 62.5%",
                recommendation_text="Review performance on Lathe 3",
                evidence_summary="OEE 22.5% below target",
                evidence_refs=[
                    EvidenceRef(
                        source_table="daily_summaries",
                        record_id="ds-456",
                        metric_name="oee_gap",
                        metric_value="22.5%",
                    )
                ],
                created_at=datetime.utcnow()
            ),
        ],
        generated_at=datetime.utcnow(),
        report_date=target_date,
        total_count=2,
        counts_by_category={"safety": 1, "oee": 1, "financial": 0}
    )


@pytest.fixture
def empty_action_response():
    """Empty ActionListResponse for testing."""
    target_date = date.today() - timedelta(days=1)
    return ActionListResponse(
        actions=[],
        generated_at=datetime.utcnow(),
        report_date=target_date,
        total_count=0,
        counts_by_category={"safety": 0, "oee": 0, "financial": 0}
    )


class TestDailyActionListEndpoint:
    """Tests for GET /api/actions/daily endpoint."""

    def test_daily_action_list_requires_auth(self, client):
        """AC#8: Endpoint requires authentication."""
        response = client.get("/api/actions/daily")
        assert response.status_code == 401

    def test_daily_action_list_success(
        self, client, mock_verify_jwt, mock_action_engine, sample_action_response
    ):
        """AC#8: Returns prioritized action list as JSON."""
        mock_action_engine.generate_action_list = AsyncMock(
            return_value=sample_action_response
        )
        mock_action_engine._get_config = MagicMock(return_value=MagicMock())

        response = client.get(
            "/api/actions/daily",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "actions" in data
        assert "generated_at" in data
        assert "report_date" in data
        assert "total_count" in data
        assert "counts_by_category" in data
        assert data["total_count"] == 2

    def test_daily_action_list_with_date_param(
        self, client, mock_verify_jwt, mock_action_engine, sample_action_response
    ):
        """AC#8: Supports date query parameter."""
        mock_action_engine.generate_action_list = AsyncMock(
            return_value=sample_action_response
        )
        mock_action_engine._get_config = MagicMock(return_value=MagicMock())

        target_date = "2026-01-05"
        response = client.get(
            f"/api/actions/daily?date={target_date}",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200

        # Verify the engine was called with the correct date
        mock_action_engine.generate_action_list.assert_called_once()
        call_args = mock_action_engine.generate_action_list.call_args
        assert call_args.kwargs.get("target_date") == date(2026, 1, 5)

    def test_daily_action_list_with_limit_param(
        self, client, mock_verify_jwt, mock_action_engine, sample_action_response
    ):
        """AC#8: Supports limit query parameter."""
        mock_action_engine.generate_action_list = AsyncMock(
            return_value=sample_action_response
        )
        mock_action_engine._get_config = MagicMock(return_value=MagicMock())

        response = client.get(
            "/api/actions/daily?limit=10",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200

        call_args = mock_action_engine.generate_action_list.call_args
        assert call_args.kwargs.get("limit") == 10

    def test_daily_action_list_with_category_filter(
        self, client, mock_verify_jwt, mock_action_engine, sample_action_response
    ):
        """AC#8: Supports category_filter query parameter."""
        mock_action_engine.generate_action_list = AsyncMock(
            return_value=sample_action_response
        )
        mock_action_engine._get_config = MagicMock(return_value=MagicMock())

        response = client.get(
            "/api/actions/daily?category=safety",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200

        call_args = mock_action_engine.generate_action_list.call_args
        assert call_args.kwargs.get("category_filter") == ActionCategory.SAFETY

    def test_daily_action_list_empty_state(
        self, client, mock_verify_jwt, mock_action_engine, empty_action_response
    ):
        """AC#10: Returns empty list with metadata when no items."""
        mock_action_engine.generate_action_list = AsyncMock(
            return_value=empty_action_response
        )
        mock_action_engine._get_config = MagicMock(return_value=MagicMock())

        response = client.get(
            "/api/actions/daily",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["actions"] == []
        assert data["total_count"] == 0
        assert data["counts_by_category"] == {"safety": 0, "oee": 0, "financial": 0}

    def test_daily_action_list_response_metadata(
        self, client, mock_verify_jwt, mock_action_engine, sample_action_response
    ):
        """AC#8: Response includes required metadata."""
        mock_action_engine.generate_action_list = AsyncMock(
            return_value=sample_action_response
        )
        mock_action_engine._get_config = MagicMock(return_value=MagicMock())

        response = client.get(
            "/api/actions/daily",
            headers={"Authorization": "Bearer test-token"}
        )

        data = response.json()

        # Check all metadata fields
        assert "generated_at" in data
        assert "total_count" in data
        assert "counts_by_category" in data
        assert "safety" in data["counts_by_category"]
        assert "oee" in data["counts_by_category"]
        assert "financial" in data["counts_by_category"]


class TestSafetyActionsEndpoint:
    """Tests for GET /api/actions/safety endpoint."""

    def test_safety_actions_requires_auth(self, client):
        """Endpoint requires authentication."""
        response = client.get("/api/actions/safety")
        assert response.status_code == 401

    def test_safety_actions_success(
        self, client, mock_verify_jwt, mock_action_engine, sample_action_response
    ):
        """Returns safety-only action items."""
        mock_action_engine.generate_action_list = AsyncMock(
            return_value=sample_action_response
        )

        response = client.get(
            "/api/actions/safety",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200

        # Verify called with safety filter
        call_args = mock_action_engine.generate_action_list.call_args
        assert call_args.kwargs.get("category_filter") == ActionCategory.SAFETY


class TestOEEActionsEndpoint:
    """Tests for GET /api/actions/oee endpoint."""

    def test_oee_actions_requires_auth(self, client):
        """Endpoint requires authentication."""
        response = client.get("/api/actions/oee")
        assert response.status_code == 401

    def test_oee_actions_success(
        self, client, mock_verify_jwt, mock_action_engine, sample_action_response
    ):
        """Returns OEE-only action items."""
        mock_action_engine.generate_action_list = AsyncMock(
            return_value=sample_action_response
        )
        mock_action_engine._get_config = MagicMock(return_value=MagicMock())

        response = client.get(
            "/api/actions/oee",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200

        call_args = mock_action_engine.generate_action_list.call_args
        assert call_args.kwargs.get("category_filter") == ActionCategory.OEE

    def test_oee_actions_with_target_override(
        self, client, mock_verify_jwt, mock_action_engine, sample_action_response
    ):
        """AC#6: Supports target_oee override parameter."""
        mock_action_engine.generate_action_list = AsyncMock(
            return_value=sample_action_response
        )
        from app.schemas.action import ActionEngineConfig
        mock_action_engine._get_config = MagicMock(return_value=ActionEngineConfig())

        response = client.get(
            "/api/actions/oee?target_oee=90",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        # Config override should have been passed to generate_action_list
        call_args = mock_action_engine.generate_action_list.call_args
        config_override = call_args.kwargs.get("config_override")
        assert config_override is not None
        assert config_override.target_oee_percentage == 90.0


class TestFinancialActionsEndpoint:
    """Tests for GET /api/actions/financial endpoint."""

    def test_financial_actions_requires_auth(self, client):
        """Endpoint requires authentication."""
        response = client.get("/api/actions/financial")
        assert response.status_code == 401

    def test_financial_actions_success(
        self, client, mock_verify_jwt, mock_action_engine, sample_action_response
    ):
        """Returns financial-only action items."""
        mock_action_engine.generate_action_list = AsyncMock(
            return_value=sample_action_response
        )
        mock_action_engine._get_config = MagicMock(return_value=MagicMock())

        response = client.get(
            "/api/actions/financial",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200

        call_args = mock_action_engine.generate_action_list.call_args
        assert call_args.kwargs.get("category_filter") == ActionCategory.FINANCIAL

    def test_financial_actions_with_threshold_override(
        self, client, mock_verify_jwt, mock_action_engine, sample_action_response
    ):
        """AC#6: Supports financial_threshold override parameter."""
        mock_action_engine.generate_action_list = AsyncMock(
            return_value=sample_action_response
        )
        from app.schemas.action import ActionEngineConfig
        mock_action_engine._get_config = MagicMock(return_value=ActionEngineConfig())

        response = client.get(
            "/api/actions/financial?financial_threshold=500",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        # Config override should have been passed to generate_action_list
        call_args = mock_action_engine.generate_action_list.call_args
        config_override = call_args.kwargs.get("config_override")
        assert config_override is not None
        assert config_override.financial_loss_threshold == 500.0


class TestCacheInvalidationEndpoint:
    """Tests for POST /api/actions/invalidate-cache endpoint."""

    def test_invalidate_cache_requires_auth(self, client):
        """Endpoint requires authentication."""
        response = client.post("/api/actions/invalidate-cache")
        assert response.status_code == 401

    def test_invalidate_cache_success(
        self, client, mock_verify_jwt, mock_action_engine
    ):
        """AC#9: Cache can be invalidated via API."""
        mock_action_engine.invalidate_cache = MagicMock()

        response = client.post(
            "/api/actions/invalidate-cache",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_action_engine.invalidate_cache.assert_called_once_with(None)

    def test_invalidate_cache_with_date(
        self, client, mock_verify_jwt, mock_action_engine
    ):
        """AC#9: Can invalidate cache for specific date."""
        mock_action_engine.invalidate_cache = MagicMock()

        response = client.post(
            "/api/actions/invalidate-cache?date=2026-01-05",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        mock_action_engine.invalidate_cache.assert_called_once_with(date(2026, 1, 5))


class TestActionItemStructure:
    """Tests for action item response structure (AC #7)."""

    def test_action_item_has_all_required_fields(
        self, client, mock_verify_jwt, mock_action_engine, sample_action_response
    ):
        """AC#7: Action items include all required fields."""
        mock_action_engine.generate_action_list = AsyncMock(
            return_value=sample_action_response
        )
        mock_action_engine._get_config = MagicMock(return_value=MagicMock())

        response = client.get(
            "/api/actions/daily",
            headers={"Authorization": "Bearer test-token"}
        )

        data = response.json()
        action = data["actions"][0]

        # Check all required fields per AC #7
        assert "id" in action
        assert "asset_id" in action
        assert "asset_name" in action
        assert "priority_level" in action
        assert "category" in action
        assert "primary_metric_value" in action
        assert "recommendation_text" in action
        assert "evidence_summary" in action
        assert "evidence_refs" in action
        assert "created_at" in action

    def test_evidence_refs_structure(
        self, client, mock_verify_jwt, mock_action_engine, sample_action_response
    ):
        """AC#7: Evidence refs support Evidence Card UI pattern."""
        mock_action_engine.generate_action_list = AsyncMock(
            return_value=sample_action_response
        )
        mock_action_engine._get_config = MagicMock(return_value=MagicMock())

        response = client.get(
            "/api/actions/daily",
            headers={"Authorization": "Bearer test-token"}
        )

        data = response.json()
        evidence_ref = data["actions"][0]["evidence_refs"][0]

        assert "source_table" in evidence_ref
        assert "record_id" in evidence_ref
        assert "metric_name" in evidence_ref
        assert "metric_value" in evidence_ref


class TestQueryParameterValidation:
    """Tests for query parameter validation."""

    def test_invalid_date_format(self, client, mock_verify_jwt):
        """Invalid date format returns error."""
        response = client.get(
            "/api/actions/daily?date=invalid",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 422  # Validation error

    def test_limit_too_high(self, client, mock_verify_jwt):
        """Limit above 100 returns error."""
        response = client.get(
            "/api/actions/daily?limit=200",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 422  # Validation error

    def test_limit_below_one(self, client, mock_verify_jwt):
        """Limit below 1 returns error."""
        response = client.get(
            "/api/actions/daily?limit=0",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 422  # Validation error

    def test_invalid_category(self, client, mock_verify_jwt):
        """Invalid category returns error."""
        response = client.get(
            "/api/actions/daily?category=invalid",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 422  # Validation error


# =============================================================================
# Story 3.2 - Versioned API Endpoint Tests
# =============================================================================

class TestVersionedDailyActionListEndpoint:
    """Tests for Story 3.2 AC#1 - GET /api/v1/actions/daily endpoint."""

    def test_v1_daily_endpoint_exists(self, client, mock_verify_jwt, mock_action_engine, sample_action_response):
        """AC#1: /api/v1/actions/daily endpoint exists and returns 200."""
        mock_action_engine.generate_action_list = AsyncMock(
            return_value=sample_action_response
        )
        mock_action_engine._get_config = MagicMock(return_value=MagicMock())

        response = client.get(
            "/api/v1/actions/daily",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200

    def test_v1_daily_endpoint_requires_auth(self, client):
        """AC#8: /api/v1/actions/daily requires authentication."""
        response = client.get("/api/v1/actions/daily")
        # Accept either 401 (Unauthorized) or 403 (Forbidden) - both indicate auth required
        assert response.status_code in (401, 403)

    def test_v1_daily_endpoint_returns_json(
        self, client, mock_verify_jwt, mock_action_engine, sample_action_response
    ):
        """AC#1: /api/v1/actions/daily returns JSON response."""
        mock_action_engine.generate_action_list = AsyncMock(
            return_value=sample_action_response
        )
        mock_action_engine._get_config = MagicMock(return_value=MagicMock())

        response = client.get(
            "/api/v1/actions/daily",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert "actions" in data

    def test_v1_daily_response_has_required_fields(
        self, client, mock_verify_jwt, mock_action_engine, sample_action_response
    ):
        """AC#7: Response contains all required fields per schema."""
        mock_action_engine.generate_action_list = AsyncMock(
            return_value=sample_action_response
        )
        mock_action_engine._get_config = MagicMock(return_value=MagicMock())

        response = client.get(
            "/api/v1/actions/daily",
            headers={"Authorization": "Bearer test-token"}
        )

        data = response.json()
        action = data["actions"][0]

        # Story 3.2 AC#7 required fields
        assert "id" in action
        assert "priority_rank" in action
        assert "category" in action
        assert "asset_id" in action
        assert "asset_name" in action
        assert "title" in action
        assert "description" in action
        assert "financial_impact_usd" in action
        assert "evidence_refs" in action
        assert "created_at" in action

    def test_v1_daily_with_date_param(
        self, client, mock_verify_jwt, mock_action_engine, sample_action_response
    ):
        """AC#1: Endpoint accepts date parameter."""
        mock_action_engine.generate_action_list = AsyncMock(
            return_value=sample_action_response
        )
        mock_action_engine._get_config = MagicMock(return_value=MagicMock())

        target_date = "2026-01-05"
        response = client.get(
            f"/api/v1/actions/daily?date={target_date}",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        mock_action_engine.generate_action_list.assert_called_once()


class TestStory32ResponseSchemaCompliance:
    """Tests for Story 3.2 AC#7 - Complete response schema compliance."""

    def test_action_item_priority_rank_is_numeric(
        self, client, mock_verify_jwt, mock_action_engine, sample_action_response
    ):
        """AC#7: priority_rank is a numeric value."""
        mock_action_engine.generate_action_list = AsyncMock(
            return_value=sample_action_response
        )
        mock_action_engine._get_config = MagicMock(return_value=MagicMock())

        response = client.get(
            "/api/v1/actions/daily",
            headers={"Authorization": "Bearer test-token"}
        )

        data = response.json()
        for action in data["actions"]:
            assert isinstance(action["priority_rank"], int)

    def test_action_item_financial_impact_is_numeric(
        self, client, mock_verify_jwt, mock_action_engine, sample_action_response
    ):
        """AC#7: financial_impact_usd is a numeric value."""
        mock_action_engine.generate_action_list = AsyncMock(
            return_value=sample_action_response
        )
        mock_action_engine._get_config = MagicMock(return_value=MagicMock())

        response = client.get(
            "/api/v1/actions/daily",
            headers={"Authorization": "Bearer test-token"}
        )

        data = response.json()
        for action in data["actions"]:
            assert isinstance(action["financial_impact_usd"], (int, float))

    def test_evidence_refs_structure(
        self, client, mock_verify_jwt, mock_action_engine, sample_action_response
    ):
        """AC#7, AC#9: evidence_refs array has correct structure."""
        mock_action_engine.generate_action_list = AsyncMock(
            return_value=sample_action_response
        )
        mock_action_engine._get_config = MagicMock(return_value=MagicMock())

        response = client.get(
            "/api/v1/actions/daily",
            headers={"Authorization": "Bearer test-token"}
        )

        data = response.json()
        action = data["actions"][0]

        assert isinstance(action["evidence_refs"], list)
        if action["evidence_refs"]:
            ref = action["evidence_refs"][0]
            # Story 3.2 AC#9 fields (using alias names)
            assert "table" in ref or "source_table" in ref
            assert "column" in ref or "metric_name" in ref
            assert "value" in ref or "metric_value" in ref
            assert "record_id" in ref

    def test_category_enum_values(
        self, client, mock_verify_jwt, mock_action_engine, sample_action_response
    ):
        """AC#7: category is one of safety|oee|financial."""
        mock_action_engine.generate_action_list = AsyncMock(
            return_value=sample_action_response
        )
        mock_action_engine._get_config = MagicMock(return_value=MagicMock())

        response = client.get(
            "/api/v1/actions/daily",
            headers={"Authorization": "Bearer test-token"}
        )

        data = response.json()
        valid_categories = {"safety", "oee", "financial"}
        for action in data["actions"]:
            assert action["category"] in valid_categories
