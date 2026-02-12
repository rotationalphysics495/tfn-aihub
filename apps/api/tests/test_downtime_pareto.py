"""
Tests for Downtime Pareto API Endpoint - Story 14.3

Tests for the enhanced Pareto endpoint that uses downtime_events table
with is_planned field, planned/unplanned split, area aggregation,
and fallback to daily_summaries.

Story: 14.3 - Downtime Pareto API Endpoint
AC: #1 - Pareto with downtime_events, is_planned, planned/unplanned split
AC: #2 - Area aggregation across all assets in a workcenter
AC: #3 - Empty results and fallback to daily_summaries
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock, call
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.models.downtime import (
    DowntimeEvent,
    ParetoItem,
    ParetoResponse,
    DataSource,
)
from app.services.downtime_analysis import DowntimeAnalysisService


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    with patch("app.core.database.mssql_db") as mock_db:
        mock_db.initialize = MagicMock()
        mock_db.dispose = MagicMock()
        mock_db.check_health.return_value = {
            "status": "not_configured",
            "connected": False,
        }
        with patch("app.services.scheduler.get_scheduler") as mock_sched:
            mock_scheduler = MagicMock()
            mock_scheduler.start = AsyncMock()
            mock_scheduler.shutdown = AsyncMock()
            mock_scheduler.status.to_dict.return_value = {"status": "stopped"}
            mock_sched.return_value = mock_scheduler
            with TestClient(app) as test_client:
                yield test_client


@pytest.fixture
def mock_verify_jwt():
    """Mock JWT verification to return a valid payload."""
    with patch("app.core.security.verify_supabase_jwt", new_callable=AsyncMock) as mock:
        mock.return_value = {
            "sub": "123e4567-e89b-12d3-a456-426614174000",
            "email": "test@example.com",
            "role": "authenticated",
            "aud": "authenticated",
            "exp": 9999999999,
        }
        yield mock


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for endpoint tests."""
    with patch("app.api.downtime.get_supabase_client", new_callable=AsyncMock) as mock:
        client_mock = MagicMock()
        mock.return_value = client_mock
        yield client_mock


@pytest.fixture
def service_mock_client():
    """Mock Supabase client for service-level tests."""
    return MagicMock()


@pytest.fixture
def service(service_mock_client):
    """Create a DowntimeAnalysisService with mocked Supabase client."""
    return DowntimeAnalysisService(service_mock_client)


# --- Asset fixtures ---

ASSET_1_ID = "a0000000-0000-0000-0000-000000000001"
ASSET_2_ID = "a0000000-0000-0000-0000-000000000002"
ASSET_3_ID = "a0000000-0000-0000-0000-000000000003"
COST_CENTER_1_ID = "cc000000-0000-0000-0000-000000000001"


@pytest.fixture
def sample_assets():
    """Sample assets with areas."""
    return [
        {
            "id": ASSET_1_ID,
            "name": "Asset 1",
            "area": "Workcenter A",
            "source_id": "ASSET_1",
            "cost_center_id": COST_CENTER_1_ID,
        },
        {
            "id": ASSET_2_ID,
            "name": "Asset 2",
            "area": "Workcenter A",
            "source_id": "ASSET_2",
            "cost_center_id": COST_CENTER_1_ID,
        },
        {
            "id": ASSET_3_ID,
            "name": "Asset 3",
            "area": "Workcenter B",
            "source_id": "ASSET_3",
            "cost_center_id": COST_CENTER_1_ID,
        },
    ]


@pytest.fixture
def sample_cost_centers():
    """Sample cost center data."""
    return [
        {
            "id": COST_CENTER_1_ID,
            "standard_hourly_rate": 150.0,
        },
    ]


# --- Downtime events fixtures ---


@pytest.fixture
def downtime_events_sorted():
    """4 downtime_events: 2 Mechanical (90min), 1 Material Shortage (45min), 1 Changeover (20min)."""
    return [
        {
            "id": str(uuid4()),
            "asset_id": ASSET_1_ID,
            "event_date": "2025-01-15",
            "shift": "morning",
            "reason_code": "Mechanical",
            "reason_detail": "Bearing wear",
            "duration_minutes": 60,
            "is_planned": False,
            "source_system": "manual",
        },
        {
            "id": str(uuid4()),
            "asset_id": ASSET_1_ID,
            "event_date": "2025-01-15",
            "shift": "afternoon",
            "reason_code": "Mechanical",
            "reason_detail": "Belt snap",
            "duration_minutes": 30,
            "is_planned": False,
            "source_system": "manual",
        },
        {
            "id": str(uuid4()),
            "asset_id": ASSET_1_ID,
            "event_date": "2025-01-15",
            "shift": "morning",
            "reason_code": "Material Shortage",
            "reason_detail": "Raw material delay",
            "duration_minutes": 45,
            "is_planned": False,
            "source_system": "manual",
        },
        {
            "id": str(uuid4()),
            "asset_id": ASSET_1_ID,
            "event_date": "2025-01-15",
            "shift": "afternoon",
            "reason_code": "Changeover",
            "reason_detail": "Product changeover",
            "duration_minutes": 20,
            "is_planned": True,
            "source_system": "manual",
        },
    ]


@pytest.fixture
def downtime_events_planned_unplanned():
    """Events with mixed is_planned for planned/unplanned split testing."""
    return [
        {
            "id": str(uuid4()),
            "asset_id": ASSET_1_ID,
            "event_date": "2025-01-15",
            "shift": "morning",
            "reason_code": "Planned Maintenance",
            "duration_minutes": 40,
            "is_planned": True,
            "source_system": "manual",
        },
        {
            "id": str(uuid4()),
            "asset_id": ASSET_1_ID,
            "event_date": "2025-01-15",
            "shift": "morning",
            "reason_code": "Changeover",
            "duration_minutes": 25,
            "is_planned": True,
            "source_system": "manual",
        },
        {
            "id": str(uuid4()),
            "asset_id": ASSET_1_ID,
            "event_date": "2025-01-15",
            "shift": "afternoon",
            "reason_code": "Mechanical",
            "duration_minutes": 60,
            "is_planned": False,
            "source_system": "manual",
        },
        {
            "id": str(uuid4()),
            "asset_id": ASSET_1_ID,
            "event_date": "2025-01-15",
            "shift": "afternoon",
            "reason_code": "Material Shortage",
            "duration_minutes": 30,
            "is_planned": False,
            "source_system": "manual",
        },
    ]


@pytest.fixture
def downtime_events_clean_percentages():
    """Events with clean percentage math: Mechanical 90, Material Shortage 45, Safety Issue 15 = 150."""
    return [
        {
            "id": str(uuid4()),
            "asset_id": ASSET_1_ID,
            "event_date": "2025-01-15",
            "shift": "morning",
            "reason_code": "Mechanical",
            "duration_minutes": 90,
            "is_planned": False,
            "source_system": "manual",
        },
        {
            "id": str(uuid4()),
            "asset_id": ASSET_1_ID,
            "event_date": "2025-01-15",
            "shift": "morning",
            "reason_code": "Material Shortage",
            "duration_minutes": 45,
            "is_planned": False,
            "source_system": "manual",
        },
        {
            "id": str(uuid4()),
            "asset_id": ASSET_1_ID,
            "event_date": "2025-01-15",
            "shift": "afternoon",
            "reason_code": "Safety Issue",
            "duration_minutes": 15,
            "is_planned": False,
            "source_system": "manual",
        },
    ]


@pytest.fixture
def downtime_events_multi_area():
    """Events across multiple areas for area aggregation testing."""
    return [
        {
            "id": str(uuid4()),
            "asset_id": ASSET_1_ID,  # Workcenter A
            "event_date": "2025-01-15",
            "shift": "morning",
            "reason_code": "Mechanical",
            "duration_minutes": 60,
            "is_planned": False,
            "source_system": "manual",
        },
        {
            "id": str(uuid4()),
            "asset_id": ASSET_2_ID,  # Workcenter A
            "event_date": "2025-01-15",
            "shift": "morning",
            "reason_code": "Mechanical",
            "duration_minutes": 30,
            "is_planned": False,
            "source_system": "manual",
        },
        {
            "id": str(uuid4()),
            "asset_id": ASSET_2_ID,  # Workcenter A
            "event_date": "2025-01-15",
            "shift": "afternoon",
            "reason_code": "Material Shortage",
            "duration_minutes": 45,
            "is_planned": False,
            "source_system": "manual",
        },
        {
            "id": str(uuid4()),
            "asset_id": ASSET_3_ID,  # Workcenter B
            "event_date": "2025-01-15",
            "shift": "morning",
            "reason_code": "Mechanical",
            "duration_minutes": 20,
            "is_planned": False,
            "source_system": "manual",
        },
    ]


# =============================================================================
# Unit Tests - Models
# =============================================================================


class TestParetoItemModel:
    """Unit tests for ParetoItem model extensions (Story 14.3)."""

    def test_UNIT_001_pareto_item_has_is_planned_default_false(self):
        """
        14-3-downtime-pareto-api-endpoint-UNIT-001:
        ParetoItem model includes is_planned field with default False.

        Given: A ParetoItem is instantiated with only required fields
        When: The is_planned field is accessed
        Then: is_planned is False (default value); the field is a boolean type
        """
        item = ParetoItem(
            reason_code="Mechanical",
            total_minutes=60,
            percentage=50.0,
            cumulative_percentage=50.0,
        )
        # The is_planned field should exist with default False
        assert hasattr(item, "is_planned"), "ParetoItem must have an is_planned field"
        assert item.is_planned is False, "is_planned should default to False"
        assert isinstance(item.is_planned, bool), "is_planned should be a boolean"


class TestParetoResponseModel:
    """Unit tests for ParetoResponse model extensions (Story 14.3)."""

    def test_UNIT_002_pareto_response_has_planned_unplanned_defaults(self):
        """
        14-3-downtime-pareto-api-endpoint-UNIT-002:
        ParetoResponse model includes planned_minutes and unplanned_minutes with defaults of 0.

        Given: A ParetoResponse is instantiated with only required fields
        When: planned_minutes and unplanned_minutes are accessed
        Then: Both default to 0; both are integer types with ge=0 constraint
        """
        response = ParetoResponse(
            items=[],
            total_downtime_minutes=0,
            total_financial_impact=0.0,
            total_events=0,
            data_source="downtime_events",
            last_updated="2025-01-15T06:00:00Z",
        )
        # planned_minutes and unplanned_minutes should exist with default 0
        assert hasattr(response, "planned_minutes"), "ParetoResponse must have planned_minutes field"
        assert hasattr(response, "unplanned_minutes"), "ParetoResponse must have unplanned_minutes field"
        assert response.planned_minutes == 0, "planned_minutes should default to 0"
        assert response.unplanned_minutes == 0, "unplanned_minutes should default to 0"
        assert isinstance(response.planned_minutes, int), "planned_minutes should be an integer"
        assert isinstance(response.unplanned_minutes, int), "unplanned_minutes should be an integer"

    def test_UNIT_005_new_fields_are_backward_compatible(self):
        """
        14-3-downtime-pareto-api-endpoint-UNIT-005:
        New ParetoResponse fields are backward compatible.

        Given: ParetoResponse with pre-story-14.3 fields only
        When: Serialized to JSON
        Then: planned_minutes=0, unplanned_minutes=0 appear; ParetoItems have is_planned=False
        """
        item = ParetoItem(
            reason_code="Mechanical",
            total_minutes=60,
            percentage=100.0,
            cumulative_percentage=100.0,
            financial_impact=150.0,
            event_count=1,
            is_safety_related=False,
        )
        response = ParetoResponse(
            items=[item],
            total_downtime_minutes=60,
            total_financial_impact=150.0,
            total_events=1,
            data_source="daily_summaries",
            last_updated="2025-01-15T06:00:00Z",
            threshold_80_index=0,
        )
        data = response.model_dump()

        # New fields should appear with defaults
        assert "planned_minutes" in data, "planned_minutes must appear in serialized output"
        assert data["planned_minutes"] == 0
        assert "unplanned_minutes" in data, "unplanned_minutes must appear in serialized output"
        assert data["unplanned_minutes"] == 0

        # ParetoItem should have is_planned
        assert "is_planned" in data["items"][0], "is_planned must appear in ParetoItem serialization"
        assert data["items"][0]["is_planned"] is False


class TestDowntimeEventIsPlanned:
    """Unit tests for DowntimeEvent is_planned field (Story 14.3)."""

    def test_UNIT_004_downtime_event_supports_is_planned(self):
        """
        14-3-downtime-pareto-api-endpoint-UNIT-004:
        DowntimeEvent model supports is_planned field.

        Given: A DowntimeEvent is instantiated with is_planned=True
        When: The object is accessed
        Then: is_planned is True; default when not provided is False
        """
        # Note: The current DowntimeEvent model from Story 2.5 does NOT have is_planned.
        # Story 14.3 must either add it, or the raw downtime_events records carry it.
        # The ParetoItem is what gets is_planned in the response.
        # However, the test spec says DowntimeEvent should support is_planned.
        # This test will FAIL until the model is extended.

        event_with_planned = DowntimeEvent(
            asset_id=ASSET_1_ID,
            asset_name="Asset 1",
            reason_code="Planned Maintenance",
            duration_minutes=40,
            event_timestamp="2025-01-15T10:00:00Z",
            is_planned=True,
        )
        assert event_with_planned.is_planned is True

        # Default should be False
        event_default = DowntimeEvent(
            asset_id=ASSET_1_ID,
            asset_name="Asset 1",
            reason_code="Mechanical",
            duration_minutes=60,
            event_timestamp="2025-01-15T10:00:00Z",
        )
        assert event_default.is_planned is False


class TestCalculateParetoPlannedUnplanned:
    """Unit tests for calculate_pareto with planned/unplanned tracking."""

    def test_UNIT_003_calculate_pareto_tracks_planned_unplanned(self, service):
        """
        14-3-downtime-pareto-api-endpoint-UNIT-003:
        calculate_pareto tracks planned and unplanned minutes per reason code.

        Given: DowntimeEvent objects with mixed is_planned values
        When: calculate_pareto(events) is called
        Then: is_planned is determined by majority of minutes per reason code
        """
        events = [
            DowntimeEvent(
                id="1",
                asset_id=ASSET_1_ID,
                asset_name="Asset 1",
                reason_code="Mechanical",
                duration_minutes=60,
                event_timestamp="2025-01-15T10:00:00Z",
                financial_impact=150.0,
                is_safety_related=False,
                is_planned=True,
            ),
            DowntimeEvent(
                id="2",
                asset_id=ASSET_1_ID,
                asset_name="Asset 1",
                reason_code="Mechanical",
                duration_minutes=30,
                event_timestamp="2025-01-15T11:00:00Z",
                financial_impact=75.0,
                is_safety_related=False,
                is_planned=False,
            ),
            DowntimeEvent(
                id="3",
                asset_id=ASSET_1_ID,
                asset_name="Asset 1",
                reason_code="Material Shortage",
                duration_minutes=45,
                event_timestamp="2025-01-15T12:00:00Z",
                financial_impact=112.5,
                is_safety_related=False,
                is_planned=False,
            ),
        ]

        items, _ = service.calculate_pareto(events)

        # Mechanical: 60min planned > 30min unplanned => is_planned=True
        mech_item = next((i for i in items if i.reason_code == "Mechanical"), None)
        assert mech_item is not None
        assert mech_item.is_planned is True, (
            "Mechanical should be is_planned=True because 60 planned > 30 unplanned"
        )

        # Material Shortage: 0min planned < 45min unplanned => is_planned=False
        mat_item = next((i for i in items if i.reason_code == "Material Shortage"), None)
        assert mat_item is not None
        assert mat_item.is_planned is False, (
            "Material Shortage should be is_planned=False because 0 planned < 45 unplanned"
        )


# =============================================================================
# Integration Tests - Service Layer
# =============================================================================


class TestServiceQueryFilters:
    """Integration tests for service-level query behavior."""

    @pytest.mark.asyncio
    async def test_INT_001_service_queries_downtime_events_with_filters(
        self, service, service_mock_client
    ):
        """
        14-3-downtime-pareto-api-endpoint-INT-001:
        Service queries downtime_events table with correct filters.

        Given: Mock Supabase client with downtime_events data
        When: get_downtime_from_events_table(event_date, asset_id) is called
        Then: Correct table and filter chain is used
        """
        mock_response = MagicMock()
        mock_response.data = [
            {
                "id": str(uuid4()),
                "asset_id": ASSET_1_ID,
                "event_date": "2025-01-15",
                "reason_code": "Mechanical",
                "duration_minutes": 60,
                "is_planned": False,
            }
        ]

        # Set up chained query mock
        (
            service_mock_client.table.return_value
            .select.return_value
            .eq.return_value
            .eq.return_value
            .execute
        ).return_value = mock_response

        # This method does not exist yet - will fail
        records = await service.get_downtime_from_events_table(
            event_date=date(2025, 1, 15),
            asset_id=ASSET_1_ID,
        )

        # Verify table was called correctly
        service_mock_client.table.assert_called_with("downtime_events")
        assert len(records) == 1
        assert records[0]["reason_code"] == "Mechanical"


class TestServiceAreaFilter:
    """Integration tests for area-based filtering."""

    @pytest.mark.asyncio
    async def test_INT_004_service_filters_by_area(
        self, service, service_mock_client, sample_assets
    ):
        """
        14-3-downtime-pareto-api-endpoint-INT-004:
        Service method filters events by area using assets_map lookup.

        Given: Mock Supabase returns events across multiple areas
        When: get_downtime_from_events_table(area="Assembly") is called
        Then: Only events for assets in "Assembly" area are returned
        """
        # Setup assets query
        service_mock_client.table.return_value.select.return_value.execute.return_value = MagicMock(
            data=sample_assets
        )

        # Setup downtime_events query returns events for all assets
        all_events = [
            {"id": str(uuid4()), "asset_id": ASSET_1_ID, "event_date": "2025-01-15",
             "reason_code": "Mechanical", "duration_minutes": 60, "is_planned": False},
            {"id": str(uuid4()), "asset_id": ASSET_2_ID, "event_date": "2025-01-15",
             "reason_code": "Changeover", "duration_minutes": 30, "is_planned": True},
            {"id": str(uuid4()), "asset_id": ASSET_3_ID, "event_date": "2025-01-15",
             "reason_code": "Mechanical", "duration_minutes": 20, "is_planned": False},
        ]

        (
            service_mock_client.table.return_value
            .select.return_value
            .eq.return_value
            .execute
        ).return_value = MagicMock(data=all_events)

        # This method does not exist yet - will fail
        records = await service.get_downtime_from_events_table(
            event_date=date(2025, 1, 15),
            area="Workcenter A",
        )

        # Should only return events for ASSET_1 and ASSET_2 (both in Workcenter A)
        asset_ids = [r["asset_id"] for r in records]
        assert ASSET_1_ID in asset_ids
        assert ASSET_2_ID in asset_ids
        assert ASSET_3_ID not in asset_ids, "Workcenter B asset should be excluded"


class TestCaching:
    """Integration tests for caching behavior."""

    def test_INT_002_caching_returns_cached_response(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers, downtime_events_sorted
    ):
        """
        14-3-downtime-pareto-api-endpoint-INT-002:
        Caching returns cached response on second call with same parameters.

        Given: Pareto endpoint called once, populating cache
        When: Same endpoint called again with identical params
        Then: Supabase NOT called again; response matches; TTL is 15min (900s)
        """
        # Setup mock responses for downtime_events table query
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]
        (
            mock_supabase_client.table.return_value
            .select.return_value
            .eq.return_value
            .eq.return_value
            .execute
        ).return_value = MagicMock(data=downtime_events_sorted)

        # First call
        response1 = client.get(
            "/api/v1/downtime/pareto?date=2025-01-15&asset_id=" + ASSET_1_ID,
            headers={"Authorization": "Bearer valid-token"},
        )

        # Reset call counts
        initial_call_count = mock_supabase_client.table.call_count

        # Second call with same params
        response2 = client.get(
            "/api/v1/downtime/pareto?date=2025-01-15&asset_id=" + ASSET_1_ID,
            headers={"Authorization": "Bearer valid-token"},
        )

        # Both should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200

        # The Supabase client should NOT be called again on second request (cached)
        # This assertion will fail until caching is implemented
        assert mock_supabase_client.table.call_count == initial_call_count, (
            "Supabase should not be called again when result is cached"
        )

    def test_INT_003_cache_key_differentiates_by_params(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers, downtime_events_sorted
    ):
        """
        14-3-downtime-pareto-api-endpoint-INT-003:
        Cache key differentiates by date, asset_id, and area.

        Given: Pareto endpoint called for date 2025-01-15
        When: Called again for date 2025-01-16
        Then: Supabase IS called again (different cache key)
        """
        # Setup for first call
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]
        (
            mock_supabase_client.table.return_value
            .select.return_value
            .eq.return_value
            .eq.return_value
            .execute
        ).return_value = MagicMock(data=downtime_events_sorted)

        response1 = client.get(
            "/api/v1/downtime/pareto?date=2025-01-15&asset_id=" + ASSET_1_ID,
            headers={"Authorization": "Bearer valid-token"},
        )

        call_count_after_first = mock_supabase_client.table.call_count

        # Setup for second call (different date)
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]
        (
            mock_supabase_client.table.return_value
            .select.return_value
            .eq.return_value
            .eq.return_value
            .execute
        ).return_value = MagicMock(data=[])

        response2 = client.get(
            "/api/v1/downtime/pareto?date=2025-01-16&asset_id=" + ASSET_1_ID,
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Supabase SHOULD be called for the different date
        assert mock_supabase_client.table.call_count > call_count_after_first, (
            "Different cache key should trigger new Supabase query"
        )


class TestFallbackBehavior:
    """Integration tests for downtime_events to daily_summaries fallback."""

    @pytest.mark.asyncio
    async def test_INT_005_fallback_queries_daily_summaries(
        self, service, service_mock_client, sample_assets
    ):
        """
        14-3-downtime-pareto-api-endpoint-INT-005:
        Fallback queries daily_summaries when downtime_events returns empty.

        Given: downtime_events returns empty; daily_summaries has data
        When: Pareto endpoint handler executes
        Then: Service falls through to daily_summaries
        """
        # The service should have a method that tries downtime_events first,
        # then falls back to daily_summaries. This test verifies that fallback.

        # Mock empty downtime_events
        (
            service_mock_client.table.return_value
            .select.return_value
            .eq.return_value
            .eq.return_value
            .execute
        ).return_value = MagicMock(data=[])

        # This method does not exist yet - will fail
        events_records = await service.get_downtime_from_events_table(
            event_date=date(2025, 1, 15),
            asset_id=ASSET_1_ID,
        )

        assert events_records == [], "downtime_events should return empty"

        # Setup daily_summaries fallback (with server-side asset_id filter in chain)
        daily_records = [
            {
                "id": str(uuid4()),
                "asset_id": ASSET_1_ID,
                "report_date": "2025-01-15",
                "downtime_minutes": 45,
                "reason_code": "Mechanical Failure",
            }
        ]
        (
            service_mock_client.table.return_value
            .select.return_value
            .gte.return_value
            .lte.return_value
            .eq.return_value
            .execute
        ).return_value = MagicMock(data=daily_records)

        # Fallback should work
        fallback = await service.get_downtime_from_daily_summaries(
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 15),
            asset_id=ASSET_1_ID,
        )

        assert len(fallback) == 1


class TestDataSourceReporting:
    """Integration tests for data source reporting."""

    def test_INT_007_data_source_reports_downtime_events(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers, downtime_events_sorted
    ):
        """
        14-3-downtime-pareto-api-endpoint-INT-007:
        Data source is "downtime_events" when events table is used.

        Given: downtime_events table has records
        When: Pareto endpoint processes using events table
        Then: data_source is "downtime_events"
        """
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]
        (
            mock_supabase_client.table.return_value
            .select.return_value
            .eq.return_value
            .eq.return_value
            .execute
        ).return_value = MagicMock(data=downtime_events_sorted)

        response = client.get(
            "/api/v1/downtime/pareto?date=2025-01-15&asset_id=" + ASSET_1_ID,
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        # When downtime_events table is used, data_source should be "downtime_events"
        assert data["data_source"] == "downtime_events", (
            "data_source should be 'downtime_events' when events table provides data"
        )


class TestAsyncMethods:
    """Integration tests for async compliance."""

    def test_INT_006_endpoint_and_service_are_async(self):
        """
        14-3-downtime-pareto-api-endpoint-INT-006:
        Endpoint is async and uses async service methods.

        Given: The code is defined
        When: Inspected
        Then: get_downtime_pareto is async; get_downtime_from_events_table is async
        """
        import asyncio
        import inspect

        from app.api.downtime import get_downtime_pareto

        # Endpoint should be async
        assert asyncio.iscoroutinefunction(get_downtime_pareto), (
            "get_downtime_pareto must be an async function"
        )

        # New service method should be async
        assert hasattr(DowntimeAnalysisService, "get_downtime_from_events_table"), (
            "DowntimeAnalysisService must have get_downtime_from_events_table method"
        )
        method = getattr(DowntimeAnalysisService, "get_downtime_from_events_table")
        assert asyncio.iscoroutinefunction(method), (
            "get_downtime_from_events_table must be an async method"
        )


# =============================================================================
# E2E Tests - AC1: Pareto with downtime_events, fields, sorting
# =============================================================================


class TestParetoEndpointSorted:
    """E2E tests for Pareto endpoint sorting and structure (AC1)."""

    def test_E2E_001_pareto_returns_items_sorted_by_total_minutes_desc(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers, downtime_events_sorted
    ):
        """
        14-3-downtime-pareto-api-endpoint-E2E-001:
        Pareto endpoint returns items sorted by total_minutes descending.

        Given: 4 downtime_events: Mechanical(90), Material Shortage(45), Changeover(20)
        When: GET /api/v1/downtime/pareto?date=2025-01-15&asset_id=asset-1
        Then: Items sorted [Mechanical(90), Material Shortage(45), Changeover(20)]
        """
        # Setup: assets and cost_centers queries
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]

        # Setup: downtime_events query
        (
            mock_supabase_client.table.return_value
            .select.return_value
            .eq.return_value
            .eq.return_value
            .execute
        ).return_value = MagicMock(data=downtime_events_sorted)

        response = client.get(
            "/api/v1/downtime/pareto?date=2025-01-15&asset_id=" + ASSET_1_ID,
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        items = data["items"]
        assert len(items) == 3, f"Expected 3 reason codes, got {len(items)}"

        # Verify descending order
        assert items[0]["reason_code"] == "Mechanical"
        assert items[0]["total_minutes"] == 90
        assert items[1]["reason_code"] == "Material Shortage"
        assert items[1]["total_minutes"] == 45
        assert items[2]["reason_code"] == "Changeover"
        assert items[2]["total_minutes"] == 20

        # Verify each item's total_minutes >= next
        for i in range(len(items) - 1):
            assert items[i]["total_minutes"] >= items[i + 1]["total_minutes"]

    def test_E2E_002_each_item_includes_required_fields(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers
    ):
        """
        14-3-downtime-pareto-api-endpoint-E2E-002:
        Each Pareto item includes reason_code, total_minutes, percentage,
        event_count, and is_planned.

        Given: Events with different is_planned values
        When: GET /api/v1/downtime/pareto
        Then: Each item has all required fields with correct types
        """
        events = [
            {
                "id": str(uuid4()), "asset_id": ASSET_1_ID, "event_date": "2025-01-15",
                "reason_code": "Mechanical", "duration_minutes": 60, "is_planned": False,
                "source_system": "manual",
            },
            {
                "id": str(uuid4()), "asset_id": ASSET_1_ID, "event_date": "2025-01-15",
                "reason_code": "Planned Maintenance", "duration_minutes": 40, "is_planned": True,
                "source_system": "manual",
            },
        ]

        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]
        (
            mock_supabase_client.table.return_value
            .select.return_value
            .eq.return_value
            .eq.return_value
            .execute
        ).return_value = MagicMock(data=events)

        response = client.get(
            "/api/v1/downtime/pareto?date=2025-01-15&asset_id=" + ASSET_1_ID,
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        items = data["items"]

        for item in items:
            assert "reason_code" in item and isinstance(item["reason_code"], str)
            assert "total_minutes" in item and isinstance(item["total_minutes"], int)
            assert item["total_minutes"] >= 0
            assert "percentage" in item and isinstance(item["percentage"], (int, float))
            assert 0 <= item["percentage"] <= 100
            assert "event_count" in item and isinstance(item["event_count"], int)
            assert item["event_count"] >= 1
            assert "is_planned" in item and isinstance(item["is_planned"], bool)

        # Mechanical should be unplanned
        mech = next((i for i in items if i["reason_code"] == "Mechanical"), None)
        assert mech is not None
        assert mech["is_planned"] is False

        # Planned Maintenance should be planned
        pm = next((i for i in items if i["reason_code"] == "Planned Maintenance"), None)
        assert pm is not None
        assert pm["is_planned"] is True

    def test_E2E_003_total_downtime_minutes_matches_sum(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers, downtime_events_sorted
    ):
        """
        14-3-downtime-pareto-api-endpoint-E2E-003:
        Response includes total_downtime_minutes matching sum of all item minutes.

        Given: Events totaling 155 minutes (60+30+45+20)
        When: GET /api/v1/downtime/pareto
        Then: total_downtime_minutes == 155; sum of items' total_minutes == 155
        """
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]
        (
            mock_supabase_client.table.return_value
            .select.return_value
            .eq.return_value
            .eq.return_value
            .execute
        ).return_value = MagicMock(data=downtime_events_sorted)

        response = client.get(
            "/api/v1/downtime/pareto?date=2025-01-15&asset_id=" + ASSET_1_ID,
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        # 60 + 30 + 45 + 20 = 155
        assert data["total_downtime_minutes"] == 155
        items_sum = sum(item["total_minutes"] for item in data["items"])
        assert items_sum == 155
        assert items_sum == data["total_downtime_minutes"]

    def test_E2E_004_planned_and_unplanned_minutes_sum_to_total(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers, downtime_events_planned_unplanned
    ):
        """
        14-3-downtime-pareto-api-endpoint-E2E-004:
        Response includes planned_minutes and unplanned_minutes that sum to total.

        Given: Planned Maintenance(40), Changeover(25) = 65 planned;
               Mechanical(60), Material Shortage(30) = 90 unplanned
        When: GET /api/v1/downtime/pareto
        Then: planned_minutes=65, unplanned_minutes=90, sum=155
        """
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]
        (
            mock_supabase_client.table.return_value
            .select.return_value
            .eq.return_value
            .eq.return_value
            .execute
        ).return_value = MagicMock(data=downtime_events_planned_unplanned)

        response = client.get(
            "/api/v1/downtime/pareto?date=2025-01-15&asset_id=" + ASSET_1_ID,
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["planned_minutes"] == 65, f"Expected planned_minutes=65, got {data.get('planned_minutes')}"
        assert data["unplanned_minutes"] == 90, f"Expected unplanned_minutes=90, got {data.get('unplanned_minutes')}"
        assert data["planned_minutes"] + data["unplanned_minutes"] == data["total_downtime_minutes"]

    def test_E2E_005_percentage_equals_total_minutes_over_total(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers, downtime_events_clean_percentages
    ):
        """
        14-3-downtime-pareto-api-endpoint-E2E-005:
        Percentage of each item equals (total_minutes / total_downtime_minutes) * 100.

        Given: Mechanical(90), Material Shortage(45), Safety Issue(15) = 150
        When: GET /api/v1/downtime/pareto
        Then: Mechanical≈60%, Material Shortage≈30%, Safety Issue≈10%; sum≈100%
        """
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]
        (
            mock_supabase_client.table.return_value
            .select.return_value
            .eq.return_value
            .eq.return_value
            .execute
        ).return_value = MagicMock(data=downtime_events_clean_percentages)

        response = client.get(
            "/api/v1/downtime/pareto?date=2025-01-15&asset_id=" + ASSET_1_ID,
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        items = data["items"]

        mech = next((i for i in items if i["reason_code"] == "Mechanical"), None)
        mat = next((i for i in items if i["reason_code"] == "Material Shortage"), None)
        safety = next((i for i in items if i["reason_code"] == "Safety Issue"), None)

        assert mech is not None
        assert mat is not None
        assert safety is not None

        assert abs(mech["percentage"] - 60.0) < 0.5, f"Mechanical should be ~60%, got {mech['percentage']}"
        assert abs(mat["percentage"] - 30.0) < 0.5, f"Material Shortage should be ~30%, got {mat['percentage']}"
        assert abs(safety["percentage"] - 10.0) < 0.5, f"Safety Issue should be ~10%, got {safety['percentage']}"

        total_pct = sum(i["percentage"] for i in items)
        assert abs(total_pct - 100.0) < 0.5, f"Percentages should sum to ~100%, got {total_pct}"

    def test_E2E_006_event_count_per_reason_code(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers
    ):
        """
        14-3-downtime-pareto-api-endpoint-E2E-006:
        event_count accurately reflects number of events per reason code.

        Given: 3 Mechanical events (60+30+20) and 1 Changeover event (45)
        When: GET /api/v1/downtime/pareto
        Then: Mechanical event_count=3, Changeover event_count=1
        """
        events = [
            {"id": str(uuid4()), "asset_id": ASSET_1_ID, "event_date": "2025-01-15",
             "reason_code": "Mechanical", "duration_minutes": 60, "is_planned": False,
             "source_system": "manual"},
            {"id": str(uuid4()), "asset_id": ASSET_1_ID, "event_date": "2025-01-15",
             "reason_code": "Mechanical", "duration_minutes": 30, "is_planned": False,
             "source_system": "manual"},
            {"id": str(uuid4()), "asset_id": ASSET_1_ID, "event_date": "2025-01-15",
             "reason_code": "Mechanical", "duration_minutes": 20, "is_planned": False,
             "source_system": "manual"},
            {"id": str(uuid4()), "asset_id": ASSET_1_ID, "event_date": "2025-01-15",
             "reason_code": "Changeover", "duration_minutes": 45, "is_planned": True,
             "source_system": "manual"},
        ]

        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]
        (
            mock_supabase_client.table.return_value
            .select.return_value
            .eq.return_value
            .eq.return_value
            .execute
        ).return_value = MagicMock(data=events)

        response = client.get(
            "/api/v1/downtime/pareto?date=2025-01-15&asset_id=" + ASSET_1_ID,
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        items = response.json()["items"]

        mech = next((i for i in items if i["reason_code"] == "Mechanical"), None)
        assert mech is not None
        assert mech["event_count"] == 3

        chg = next((i for i in items if i["reason_code"] == "Changeover"), None)
        assert chg is not None
        assert chg["event_count"] == 1


class TestParetoAuthentication:
    """E2E tests for authentication."""

    def test_E2E_007_authentication_required(self, client):
        """
        14-3-downtime-pareto-api-endpoint-E2E-007:
        Authentication is required for the Pareto endpoint.

        Given: No authentication token
        When: GET /api/v1/downtime/pareto without Authorization header
        Then: 401 Unauthorized
        """
        response = client.get(
            "/api/v1/downtime/pareto?date=2025-01-15&asset_id=" + ASSET_1_ID,
        )
        assert response.status_code == 401


class TestParetoDateDefaults:
    """E2E tests for date parameter defaults."""

    def test_E2E_008_date_defaults_to_yesterday(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers
    ):
        """
        14-3-downtime-pareto-api-endpoint-E2E-008:
        Date parameter defaults to yesterday when not provided.

        Given: Events for yesterday's date
        When: GET /api/v1/downtime/pareto?asset_id=... (no date)
        Then: 200; service queries with event_date = yesterday
        """
        yesterday = (date.today() - timedelta(days=1)).isoformat()

        events_for_yesterday = [
            {
                "id": str(uuid4()), "asset_id": ASSET_1_ID,
                "event_date": yesterday,
                "reason_code": "Mechanical", "duration_minutes": 60,
                "is_planned": False, "source_system": "manual",
            },
        ]

        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]
        (
            mock_supabase_client.table.return_value
            .select.return_value
            .eq.return_value
            .eq.return_value
            .execute
        ).return_value = MagicMock(data=events_for_yesterday)

        # No date parameter
        response = client.get(
            "/api/v1/downtime/pareto?asset_id=" + ASSET_1_ID,
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0, "Should return items from yesterday's data"


class TestParetoIsPlannedMajority:
    """E2E tests for is_planned determination by majority."""

    def test_E2E_009_is_planned_determined_by_majority_minutes(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers
    ):
        """
        14-3-downtime-pareto-api-endpoint-E2E-009:
        is_planned is determined by majority of minutes within a reason code.

        Given: Changeover with 60min (planned) and 20min (unplanned)
        When: GET /api/v1/downtime/pareto
        Then: Changeover has is_planned=True (60 of 80 minutes are planned)
        """
        events = [
            {
                "id": str(uuid4()), "asset_id": ASSET_1_ID, "event_date": "2025-01-15",
                "reason_code": "Changeover", "duration_minutes": 60, "is_planned": True,
                "source_system": "manual",
            },
            {
                "id": str(uuid4()), "asset_id": ASSET_1_ID, "event_date": "2025-01-15",
                "reason_code": "Changeover", "duration_minutes": 20, "is_planned": False,
                "source_system": "manual",
            },
        ]

        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]
        (
            mock_supabase_client.table.return_value
            .select.return_value
            .eq.return_value
            .eq.return_value
            .execute
        ).return_value = MagicMock(data=events)

        response = client.get(
            "/api/v1/downtime/pareto?date=2025-01-15&asset_id=" + ASSET_1_ID,
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) == 1

        changeover = items[0]
        assert changeover["reason_code"] == "Changeover"
        assert changeover["is_planned"] is True, (
            "Changeover should be is_planned=True because 60 of 80 minutes are planned"
        )


# =============================================================================
# E2E Tests - AC2: Area aggregation
# =============================================================================


class TestParetoAreaAggregation:
    """E2E tests for area-based aggregation (AC2)."""

    def test_E2E_010_area_aggregates_across_workcenter(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers, downtime_events_multi_area
    ):
        """
        14-3-downtime-pareto-api-endpoint-E2E-010:
        Area parameter aggregates downtime across all assets in that workcenter.

        Given: Events for 3 assets in 2 areas: A (assets 1,2), B (asset 3)
        When: GET /api/v1/downtime/pareto?date=2025-01-15&area=Workcenter A
        Then: Only Workcenter A events; Mechanical=90(60+30), Material Shortage=45; total=135
        """
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]
        # The query for downtime_events with area filter
        (
            mock_supabase_client.table.return_value
            .select.return_value
            .eq.return_value
            .execute
        ).return_value = MagicMock(data=downtime_events_multi_area)

        response = client.get(
            "/api/v1/downtime/pareto?date=2025-01-15&area=Workcenter A",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should only include Workcenter A assets (ASSET_1 and ASSET_2)
        # Mechanical: 60 (asset-1) + 30 (asset-2) = 90
        # Material Shortage: 45 (asset-2) = 45
        # Total: 135 (asset-3's 20 excluded)
        assert data["total_downtime_minutes"] == 135, (
            f"Expected 135 total minutes for Workcenter A, got {data['total_downtime_minutes']}"
        )

        mech = next((i for i in data["items"] if i["reason_code"] == "Mechanical"), None)
        assert mech is not None
        assert mech["total_minutes"] == 90

        mat = next((i for i in data["items"] if i["reason_code"] == "Material Shortage"), None)
        assert mat is not None
        assert mat["total_minutes"] == 45

    def test_E2E_011_area_filter_is_case_insensitive(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers, downtime_events_multi_area
    ):
        """
        14-3-downtime-pareto-api-endpoint-E2E-011:
        Area filter is case-insensitive.

        Given: Assets with area="Workcenter A"
        When: GET /api/v1/downtime/pareto?area=workcenter a (lowercase)
        Then: 200; events from "Workcenter A" included
        """
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]
        (
            mock_supabase_client.table.return_value
            .select.return_value
            .eq.return_value
            .execute
        ).return_value = MagicMock(data=downtime_events_multi_area)

        response = client.get(
            "/api/v1/downtime/pareto?date=2025-01-15&area=workcenter a",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_downtime_minutes"] == 135, (
            "Case-insensitive area filter should still match Workcenter A assets"
        )

    def test_E2E_012_area_no_matching_assets_returns_empty(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers
    ):
        """
        14-3-downtime-pareto-api-endpoint-E2E-012:
        Area with no matching assets returns empty result.

        Given: No assets in "Nonexistent Area"
        When: GET /api/v1/downtime/pareto?area=Nonexistent Area
        Then: 200; items=[]; total_downtime_minutes=0; planned/unplanned=0
        """
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]
        (
            mock_supabase_client.table.return_value
            .select.return_value
            .eq.return_value
            .execute
        ).return_value = MagicMock(data=[])

        response = client.get(
            "/api/v1/downtime/pareto?date=2025-01-15&area=Nonexistent Area",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total_downtime_minutes"] == 0
        assert data.get("planned_minutes", -1) == 0, "planned_minutes should be 0"
        assert data.get("unplanned_minutes", -1) == 0, "unplanned_minutes should be 0"


# =============================================================================
# E2E Tests - AC3: Empty results and fallback
# =============================================================================


class TestParetoEmptyResults:
    """E2E tests for empty results and fallback behavior (AC3)."""

    def test_E2E_013_no_events_returns_empty_and_zero_totals(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers
    ):
        """
        14-3-downtime-pareto-api-endpoint-E2E-013:
        No downtime events returns empty items and zero totals.

        Given: Both downtime_events and daily_summaries are empty
        When: GET /api/v1/downtime/pareto
        Then: 200; items=[]; total_downtime_minutes=0; planned/unplanned=0; total_events=0
        """
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]
        # downtime_events returns empty
        (
            mock_supabase_client.table.return_value
            .select.return_value
            .eq.return_value
            .eq.return_value
            .execute
        ).return_value = MagicMock(data=[])
        # daily_summaries fallback also empty (with server-side asset_id filter in chain)
        (
            mock_supabase_client.table.return_value
            .select.return_value
            .gte.return_value
            .lte.return_value
            .eq.return_value
            .execute
        ).return_value = MagicMock(data=[])

        response = client.get(
            "/api/v1/downtime/pareto?date=2025-01-15&asset_id=" + ASSET_1_ID,
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total_downtime_minutes"] == 0
        assert data.get("planned_minutes", -1) == 0
        assert data.get("unplanned_minutes", -1) == 0
        assert data["total_events"] == 0

    def test_E2E_014_no_events_falls_back_to_daily_summaries(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers
    ):
        """
        14-3-downtime-pareto-api-endpoint-E2E-014:
        No downtime_events falls back to daily_summaries data.

        Given: downtime_events is empty; daily_summaries has data
        When: GET /api/v1/downtime/pareto
        Then: 200; items from daily_summaries; data_source="daily_summaries";
              planned/unplanned default to 0
        """
        daily_summary_records = [
            {
                "id": str(uuid4()),
                "asset_id": ASSET_1_ID,
                "report_date": "2025-01-15",
                "downtime_minutes": 60,
                "reason_code": "Mechanical Failure",
            },
            {
                "id": str(uuid4()),
                "asset_id": ASSET_1_ID,
                "report_date": "2025-01-15",
                "downtime_minutes": 30,
                "reason_code": "Material Shortage",
            },
        ]

        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]
        # downtime_events returns empty
        (
            mock_supabase_client.table.return_value
            .select.return_value
            .eq.return_value
            .eq.return_value
            .execute
        ).return_value = MagicMock(data=[])

        # daily_summaries fallback returns data (with server-side asset_id filter in chain)
        (
            mock_supabase_client.table.return_value
            .select.return_value
            .gte.return_value
            .lte.return_value
            .eq.return_value
            .execute
        ).return_value = MagicMock(data=daily_summary_records)

        response = client.get(
            "/api/v1/downtime/pareto?date=2025-01-15&asset_id=" + ASSET_1_ID,
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) > 0, "Should have items from daily_summaries fallback"
        assert data["data_source"] == "daily_summaries", (
            "data_source should be 'daily_summaries' when using fallback"
        )
        # daily_summaries has no is_planned data, so planned/unplanned default to 0
        assert data.get("planned_minutes", -1) == 0
        assert data.get("unplanned_minutes", -1) == 0

    def test_E2E_015_both_tables_empty_returns_valid_empty_response(
        self, client, mock_verify_jwt, mock_supabase_client,
        sample_assets, sample_cost_centers
    ):
        """
        14-3-downtime-pareto-api-endpoint-E2E-015:
        Both tables empty returns valid empty response.

        Given: Both downtime_events and daily_summaries empty
        When: GET /api/v1/downtime/pareto
        Then: 200 (not 404); items=[]; all totals=0; valid ParetoResponse
        """
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = [
            MagicMock(data=sample_assets),
            MagicMock(data=sample_cost_centers),
        ]
        (
            mock_supabase_client.table.return_value
            .select.return_value
            .eq.return_value
            .eq.return_value
            .execute
        ).return_value = MagicMock(data=[])
        (
            mock_supabase_client.table.return_value
            .select.return_value
            .gte.return_value
            .lte.return_value
            .eq.return_value
            .execute
        ).return_value = MagicMock(data=[])

        response = client.get(
            "/api/v1/downtime/pareto?date=2025-01-15&asset_id=" + ASSET_1_ID,
            headers={"Authorization": "Bearer valid-token"},
        )

        # MUST be 200, not 404
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total_downtime_minutes"] == 0
        assert data["total_events"] == 0


# =============================================================================
# E2E Tests - Error Handling / Cross-cutting
# =============================================================================


class TestParetoErrorHandling:
    """E2E tests for error handling."""

    def test_E2E_016_database_error_returns_500(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """
        14-3-downtime-pareto-api-endpoint-E2E-016:
        Endpoint handles database errors gracefully.

        Given: Supabase client raises an exception
        When: GET /api/v1/downtime/pareto
        Then: 500; error message in body
        """
        mock_supabase_client.table.return_value.select.return_value.execute.side_effect = Exception(
            "Database connection failed"
        )

        response = client.get(
            "/api/v1/downtime/pareto?date=2025-01-15&asset_id=" + ASSET_1_ID,
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
