"""
Tests for Schedule Attainment API Endpoint (Story 12.5)

Integration and unit tests for GET /api/v1/production/schedule-attainment.

AC: #1 - Per-workcenter schedule attainment with product breakdown and variances
AC: #2 - Product swap variance callouts
AC: #3 - Empty schedule returns 200 with message
AC: #4 - Authentication required (401 without token)
AC: #5 - Optional area filter
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4


# =============================================================================
# Test Data Constants
# =============================================================================

# Deterministic UUIDs for assets
ASSET_ROASTER_1_ID = str(uuid4())
ASSET_ROASTER_2_ID = str(uuid4())
ASSET_GRINDER_1_ID = str(uuid4())

# Deterministic UUIDs for products
PRODUCT_COLOMBIAN_ID = str(uuid4())
PRODUCT_BRAZILIAN_ID = str(uuid4())
PRODUCT_ETHIOPIAN_ID = str(uuid4())

SAMPLE_ASSETS = [
    {"id": ASSET_ROASTER_1_ID, "name": "Roaster 1", "area": "Roasting"},
    {"id": ASSET_ROASTER_2_ID, "name": "Roaster 2", "area": "Roasting"},
    {"id": ASSET_GRINDER_1_ID, "name": "Grinder 1", "area": "Grinding"},
]

SAMPLE_PRODUCTS = [
    {"id": PRODUCT_COLOMBIAN_ID, "name": "Colombian"},
    {"id": PRODUCT_BRAZILIAN_ID, "name": "Brazilian"},
    {"id": PRODUCT_ETHIOPIAN_ID, "name": "Ethiopian"},
]

AUTH_HEADERS = {"Authorization": "Bearer test-token"}
TEST_DATE = "2026-02-09"
EMPTY_DATE = "2026-03-01"


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for production schedule-attainment endpoint."""
    with patch("app.api.production.get_supabase_client", new_callable=AsyncMock) as mock:
        client_mock = MagicMock()
        mock.return_value = client_mock
        yield client_mock


def _make_table_mock(client_mock, responses_by_table):
    """
    Helper to set up mock Supabase client so that different .table() calls
    return different mock chains based on the table name.

    responses_by_table: dict mapping table name -> list of row dicts
    """
    def table_side_effect(table_name):
        table_mock = MagicMock()
        data = responses_by_table.get(table_name, [])
        response = MagicMock(data=data)

        # select().execute()
        table_mock.select.return_value.execute.return_value = response
        # select().eq().execute()
        table_mock.select.return_value.eq.return_value.execute.return_value = response
        # select().eq().eq().execute()
        table_mock.select.return_value.eq.return_value.eq.return_value.execute.return_value = response
        # select().ilike().execute() (for case-insensitive area filter)
        table_mock.select.return_value.ilike.return_value.execute.return_value = response

        return table_mock

    client_mock.table.side_effect = table_side_effect


# =============================================================================
# AC1: Per-workcenter schedule attainment — Integration Tests
# =============================================================================


class TestScheduleAttainmentHappyPath:
    """Tests for happy path schedule attainment responses (AC#1)."""

    def test_INT_001_happy_path_returns_per_workcenter_breakdown(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-001: Happy path returns per-workcenter schedule attainment breakdown.

        Given: Two workcenters ("Roasting" with 2 assets, "Grinding" with 1 asset).
               Schedule and actuals entries exist for date 2026-02-09.
        When: GET /api/v1/production/schedule-attainment?date=2026-02-09 with valid JWT
        Then: Response 200, has_data=true, date="2026-02-09", workcenters has 2 entries,
              each with workcenter name, products, variances, and overall_attainment_pct
        """
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "products": SAMPLE_PRODUCTS,
            "production_schedule": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "scheduled_quantity": 500,
                    "scheduled_date": TEST_DATE,
                    "shift": "Day",
                },
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_GRINDER_1_ID,
                    "product_id": PRODUCT_BRAZILIAN_ID,
                    "scheduled_quantity": 300,
                    "scheduled_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
            "production_actuals": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "actual_quantity": 450,
                    "production_date": TEST_DATE,
                    "shift": "Day",
                },
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_GRINDER_1_ID,
                    "product_id": PRODUCT_BRAZILIAN_ID,
                    "actual_quantity": 300,
                    "production_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
        })

        response = client.get(
            f"/api/v1/production/schedule-attainment?date={TEST_DATE}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_data"] is True
        assert data["date"] == TEST_DATE
        assert len(data["workcenters"]) == 2

        # Each workcenter has required fields
        for wc in data["workcenters"]:
            assert "workcenter" in wc
            assert "products" in wc
            assert "variances" in wc
            assert "overall_attainment_pct" in wc

        wc_names = [wc["workcenter"] for wc in data["workcenters"]]
        assert "Roasting" in wc_names
        assert "Grinding" in wc_names

    def test_INT_002_per_product_attainment_calculated_correctly(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-002: Per-product attainment percentage is correctly calculated.

        Given: Schedule has P1 with scheduled_quantity=500. Actuals have P1 with actual_quantity=450.
        When: GET /api/v1/production/schedule-attainment?date=2026-02-09
        Then: Product P1 shows scheduled_quantity=500, actual_quantity=450, attainment_pct=90.0
        """
        _make_table_mock(mock_supabase_client, {
            "assets": [SAMPLE_ASSETS[0]],  # Roaster 1 only
            "products": [SAMPLE_PRODUCTS[0]],  # Colombian only
            "production_schedule": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "scheduled_quantity": 500,
                    "scheduled_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
            "production_actuals": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "actual_quantity": 450,
                    "production_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
        })

        response = client.get(
            f"/api/v1/production/schedule-attainment?date={TEST_DATE}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()

        # Find Colombian product entry in the Roasting workcenter
        roasting = next(wc for wc in data["workcenters"] if wc["workcenter"] == "Roasting")
        colombian = next(p for p in roasting["products"] if p["product_name"] == "Colombian")

        assert colombian["scheduled_quantity"] == 500
        assert colombian["actual_quantity"] == 450
        assert colombian["attainment_pct"] == 90.0

    def test_INT_003_overall_workcenter_attainment_is_weighted_average(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-003: Overall workcenter attainment is weighted average across products.

        Given: "Roasting" has two schedule entries: A1/P1 (scheduled=500, actual=450)
               and A2/P2 (scheduled=300, actual=300)
        When: GET /api/v1/production/schedule-attainment?date=2026-02-09
        Then: Roasting overall_attainment_pct = 93.8 ((450+300)/(500+300)*100)
        """
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS[:2],  # Roaster 1 and 2
            "products": SAMPLE_PRODUCTS[:2],  # Colombian and Brazilian
            "production_schedule": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "scheduled_quantity": 500,
                    "scheduled_date": TEST_DATE,
                    "shift": "Day",
                },
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_2_ID,
                    "product_id": PRODUCT_BRAZILIAN_ID,
                    "scheduled_quantity": 300,
                    "scheduled_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
            "production_actuals": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "actual_quantity": 450,
                    "production_date": TEST_DATE,
                    "shift": "Day",
                },
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_2_ID,
                    "product_id": PRODUCT_BRAZILIAN_ID,
                    "actual_quantity": 300,
                    "production_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
        })

        response = client.get(
            f"/api/v1/production/schedule-attainment?date={TEST_DATE}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()

        roasting = next(wc for wc in data["workcenters"] if wc["workcenter"] == "Roasting")
        # (450 + 300) / (500 + 300) * 100 = 750/800 * 100 = 93.75 -> 93.8 rounded to 1 decimal
        assert roasting["overall_attainment_pct"] == 93.8

    def test_INT_004_product_entry_includes_product_name_and_id(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-004: Product entry includes product_name and product_id.

        Given: Schedule and actuals for product P1 (name: "Colombian", id: PRODUCT_COLOMBIAN_ID)
        When: GET /api/v1/production/schedule-attainment?date=2026-02-09
        Then: Product entry has product_name="Colombian" AND product_id=PRODUCT_COLOMBIAN_ID
        """
        _make_table_mock(mock_supabase_client, {
            "assets": [SAMPLE_ASSETS[0]],
            "products": [SAMPLE_PRODUCTS[0]],
            "production_schedule": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "scheduled_quantity": 500,
                    "scheduled_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
            "production_actuals": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "actual_quantity": 450,
                    "production_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
        })

        response = client.get(
            f"/api/v1/production/schedule-attainment?date={TEST_DATE}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        roasting = next(wc for wc in data["workcenters"] if wc["workcenter"] == "Roasting")
        product = roasting["products"][0]

        assert product["product_name"] == "Colombian"
        assert product["product_id"] == PRODUCT_COLOMBIAN_ID

    def test_INT_005_variance_callout_for_missing_production(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-005: Variance callout for product scheduled but not produced.

        Given: Schedule has A1/P1/Day on 2026-02-09. No matching actuals entry.
        When: GET /api/v1/production/schedule-attainment?date=2026-02-09
        Then: Workcenter for A1 has variance_type="missing", asset_name="Roaster 1",
              message mentions scheduled product but no production recorded
        """
        _make_table_mock(mock_supabase_client, {
            "assets": [SAMPLE_ASSETS[0]],
            "products": [SAMPLE_PRODUCTS[0]],
            "production_schedule": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "scheduled_quantity": 500,
                    "scheduled_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
            "production_actuals": [],  # No actuals at all
        })

        response = client.get(
            f"/api/v1/production/schedule-attainment?date={TEST_DATE}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()

        roasting = next(wc for wc in data["workcenters"] if wc["workcenter"] == "Roasting")
        assert len(roasting["variances"]) >= 1

        missing_var = next(
            v for v in roasting["variances"] if v["variance_type"] == "missing"
        )
        assert missing_var["asset_name"] == "Roaster 1"
        assert "Colombian" in missing_var["message"]
        assert "no production recorded" in missing_var["message"].lower() or \
               "not produced" in missing_var["message"].lower()

    def test_INT_006_variance_callout_for_unscheduled_production(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-006: Variance callout for product produced but not scheduled.

        Given: Actuals has A2/P2/Night on 2026-02-09. No matching schedule entry.
        When: GET /api/v1/production/schedule-attainment?date=2026-02-09
        Then: Workcenter for A2 has variance_type="unscheduled", asset_name="Roaster 2",
              message mentions produced but not scheduled
        """
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS[:2],  # Roaster 1 and Roaster 2
            "products": SAMPLE_PRODUCTS[:2],  # Colombian and Brazilian
            "production_schedule": [
                {
                    # Schedule exists for a DIFFERENT asset/shift so the query
                    # is non-empty (avoids AC#3 early return), while Roaster 2 /
                    # Night has no matching schedule entry.
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "scheduled_quantity": 500,
                    "scheduled_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
            "production_actuals": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_2_ID,
                    "product_id": PRODUCT_BRAZILIAN_ID,
                    "actual_quantity": 300,
                    "production_date": TEST_DATE,
                    "shift": "Night",
                },
            ],
        })

        response = client.get(
            f"/api/v1/production/schedule-attainment?date={TEST_DATE}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()

        # Find the workcenter containing Roaster 2
        roasting = next(
            (wc for wc in data["workcenters"] if wc["workcenter"] == "Roasting"),
            None,
        )
        assert roasting is not None

        unscheduled_var = next(
            v for v in roasting["variances"] if v["variance_type"] == "unscheduled"
        )
        assert unscheduled_var["asset_name"] == "Roaster 2"
        assert "Brazilian" in unscheduled_var["message"]
        assert "not scheduled" in unscheduled_var["message"].lower()

    def test_INT_007_response_structure_contains_all_required_fields(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-007: Response structure contains all required top-level fields.

        Given: Schedule and actuals data exist for 2026-02-09
        When: GET /api/v1/production/schedule-attainment?date=2026-02-09
        Then: Response has date (str), workcenters (array), has_data (bool, true), message (null or absent)
        """
        _make_table_mock(mock_supabase_client, {
            "assets": [SAMPLE_ASSETS[0]],
            "products": [SAMPLE_PRODUCTS[0]],
            "production_schedule": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "scheduled_quantity": 100,
                    "scheduled_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
            "production_actuals": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "actual_quantity": 100,
                    "production_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
        })

        response = client.get(
            f"/api/v1/production/schedule-attainment?date={TEST_DATE}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()

        assert "date" in data
        assert isinstance(data["date"], str)
        assert "workcenters" in data
        assert isinstance(data["workcenters"], list)
        assert "has_data" in data
        assert data["has_data"] is True
        # message should be null or absent when data exists
        assert data.get("message") is None

    def test_INT_008_endpoint_accessible_on_both_paths(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-008: Endpoint accessible on both /api/production and /api/v1/production paths.

        Given: The production router is registered at both prefixes
        When: GET on both /api/production/schedule-attainment and /api/v1/production/schedule-attainment
        Then: Both return 200 with identical structure
        """
        _make_table_mock(mock_supabase_client, {
            "assets": [SAMPLE_ASSETS[0]],
            "products": [SAMPLE_PRODUCTS[0]],
            "production_schedule": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "scheduled_quantity": 100,
                    "scheduled_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
            "production_actuals": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "actual_quantity": 100,
                    "production_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
        })

        response_v1 = client.get(
            f"/api/v1/production/schedule-attainment?date={TEST_DATE}",
            headers=AUTH_HEADERS,
        )
        response_legacy = client.get(
            f"/api/production/schedule-attainment?date={TEST_DATE}",
            headers=AUTH_HEADERS,
        )

        assert response_v1.status_code == 200
        assert response_legacy.status_code == 200

        # Both should have the same structure
        data_v1 = response_v1.json()
        data_legacy = response_legacy.json()
        assert "workcenters" in data_v1
        assert "workcenters" in data_legacy

    def test_INT_009_attainment_above_100_when_actual_exceeds_scheduled(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-009: Attainment above 100% when actual exceeds scheduled.

        Given: Schedule has P1 with scheduled_quantity=100. Actuals have actual_quantity=120.
        When: GET /api/v1/production/schedule-attainment?date=2026-02-09
        Then: Product shows attainment_pct=120.0
        """
        _make_table_mock(mock_supabase_client, {
            "assets": [SAMPLE_ASSETS[0]],
            "products": [SAMPLE_PRODUCTS[0]],
            "production_schedule": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "scheduled_quantity": 100,
                    "scheduled_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
            "production_actuals": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "actual_quantity": 120,
                    "production_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
        })

        response = client.get(
            f"/api/v1/production/schedule-attainment?date={TEST_DATE}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        roasting = next(wc for wc in data["workcenters"] if wc["workcenter"] == "Roasting")
        product = roasting["products"][0]
        assert product["attainment_pct"] == 120.0

    def test_INT_010_zero_scheduled_quantity_no_division_by_zero(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-010: Zero scheduled quantity does not cause division by zero.

        Given: Schedule has P1 with scheduled_quantity=0
        When: GET /api/v1/production/schedule-attainment?date=2026-02-09
        Then: Response 200, attainment_pct=100.0 (safe default)
        """
        _make_table_mock(mock_supabase_client, {
            "assets": [SAMPLE_ASSETS[0]],
            "products": [SAMPLE_PRODUCTS[0]],
            "production_schedule": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "scheduled_quantity": 0,
                    "scheduled_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
            "production_actuals": [],
        })

        response = client.get(
            f"/api/v1/production/schedule-attainment?date={TEST_DATE}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        roasting = next(wc for wc in data["workcenters"] if wc["workcenter"] == "Roasting")
        product = roasting["products"][0]
        assert product["attainment_pct"] == 100.0

    def test_INT_011_multiple_shifts_handled_independently(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-011: Multiple shifts on same asset are handled independently.

        Given: A1 has schedule for Day and Night shifts. Actuals match both.
        When: GET /api/v1/production/schedule-attainment?date=2026-02-09
        Then: Both shifts contribute to workcenter attainment calculation
        """
        _make_table_mock(mock_supabase_client, {
            "assets": [SAMPLE_ASSETS[0]],
            "products": [SAMPLE_PRODUCTS[0]],
            "production_schedule": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "scheduled_quantity": 500,
                    "scheduled_date": TEST_DATE,
                    "shift": "Day",
                },
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "scheduled_quantity": 400,
                    "scheduled_date": TEST_DATE,
                    "shift": "Night",
                },
            ],
            "production_actuals": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "actual_quantity": 500,
                    "production_date": TEST_DATE,
                    "shift": "Day",
                },
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "actual_quantity": 350,
                    "production_date": TEST_DATE,
                    "shift": "Night",
                },
            ],
        })

        response = client.get(
            f"/api/v1/production/schedule-attainment?date={TEST_DATE}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()

        roasting = next(wc for wc in data["workcenters"] if wc["workcenter"] == "Roasting")
        # (500 + 350) / (500 + 400) * 100 = 850/900 * 100 = 94.4
        assert roasting["overall_attainment_pct"] == pytest.approx(94.4, abs=0.1)


# =============================================================================
# AC2: Product swap variance callouts — Integration Tests
# =============================================================================


class TestScheduleAttainmentProductSwap:
    """Tests for product swap variance callouts (AC#2)."""

    def test_INT_012_product_swap_generates_variance_callout(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-012: Product swap generates variance callout with descriptive message.

        Given: Schedule A1/P1("Brazilian")/Day with 500. Actuals A1/P2("Colombian")/Day with 480.
        When: GET /api/v1/production/schedule-attainment?date=2026-02-09
        Then: Variance with type="swap", asset_name="Roaster 1",
              message contains "Roaster 1 ran Colombian instead of scheduled Brazilian"
              and "500 units of Brazilian still needed"
        """
        _make_table_mock(mock_supabase_client, {
            "assets": [SAMPLE_ASSETS[0]],  # Roaster 1
            "products": SAMPLE_PRODUCTS[:2],  # Colombian and Brazilian
            "production_schedule": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_BRAZILIAN_ID,
                    "scheduled_quantity": 500,
                    "scheduled_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
            "production_actuals": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "actual_quantity": 480,
                    "production_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
        })

        response = client.get(
            f"/api/v1/production/schedule-attainment?date={TEST_DATE}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()

        roasting = next(wc for wc in data["workcenters"] if wc["workcenter"] == "Roasting")
        swap_vars = [v for v in roasting["variances"] if v["variance_type"] == "swap"]
        assert len(swap_vars) >= 1

        swap = swap_vars[0]
        assert swap["asset_name"] == "Roaster 1"
        assert "Roaster 1 ran Colombian instead of scheduled Brazilian" in swap["message"]
        assert "500 units of Brazilian still needed" in swap["message"]

    def test_INT_013_multiple_product_swaps_generate_separate_callouts(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-013: Multiple product swaps on different assets generate separate callouts.

        Given: A1 scheduled P1 but ran P2. A2 scheduled P2 but ran P3.
        When: GET /api/v1/production/schedule-attainment?date=2026-02-09
        Then: At least 2 swap variance callouts with correct asset names and product names
        """
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS[:2],  # Roaster 1 and Roaster 2
            "products": SAMPLE_PRODUCTS,  # All 3 products
            "production_schedule": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "scheduled_quantity": 500,
                    "scheduled_date": TEST_DATE,
                    "shift": "Day",
                },
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_2_ID,
                    "product_id": PRODUCT_BRAZILIAN_ID,
                    "scheduled_quantity": 300,
                    "scheduled_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
            "production_actuals": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_BRAZILIAN_ID,  # Swap: Colombian -> Brazilian
                    "actual_quantity": 450,
                    "production_date": TEST_DATE,
                    "shift": "Day",
                },
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_2_ID,
                    "product_id": PRODUCT_ETHIOPIAN_ID,  # Swap: Brazilian -> Ethiopian
                    "actual_quantity": 280,
                    "production_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
        })

        response = client.get(
            f"/api/v1/production/schedule-attainment?date={TEST_DATE}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()

        # Collect all swap variances across workcenters
        all_swaps = []
        for wc in data["workcenters"]:
            swaps = [v for v in wc["variances"] if v["variance_type"] == "swap"]
            all_swaps.extend(swaps)

        assert len(all_swaps) >= 2

        swap_asset_names = {s["asset_name"] for s in all_swaps}
        assert "Roaster 1" in swap_asset_names
        assert "Roaster 2" in swap_asset_names

    def test_INT_014_product_swap_shows_remaining_units_needed(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-014: Product swap shows remaining units of scheduled product still needed.

        Given: Schedule A1/P1 with 500. Actual A1/P2 (different product) with 480.
        When: GET /api/v1/production/schedule-attainment?date=2026-02-09
        Then: Swap callout message includes 500 as units still needed
        """
        _make_table_mock(mock_supabase_client, {
            "assets": [SAMPLE_ASSETS[0]],
            "products": SAMPLE_PRODUCTS[:2],
            "production_schedule": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_BRAZILIAN_ID,
                    "scheduled_quantity": 500,
                    "scheduled_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
            "production_actuals": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "actual_quantity": 480,
                    "production_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
        })

        response = client.get(
            f"/api/v1/production/schedule-attainment?date={TEST_DATE}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()

        roasting = next(wc for wc in data["workcenters"] if wc["workcenter"] == "Roasting")
        swap_vars = [v for v in roasting["variances"] if v["variance_type"] == "swap"]
        assert len(swap_vars) >= 1
        assert "500" in swap_vars[0]["message"]
        assert "Brazilian" in swap_vars[0]["message"]

    def test_INT_015_swap_combined_with_partial_production(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-015: Swap combined with partial production of scheduled product.

        Given: A1/Day schedule for P1 (500 units). Actuals: P1 (200, partial) and P2 (300, swap).
        When: GET /api/v1/production/schedule-attainment?date=2026-02-09
        Then: P1 attainment shows actual=200, scheduled=500, attainment_pct=40.0.
              Variance for unscheduled P2 production exists.
        """
        _make_table_mock(mock_supabase_client, {
            "assets": [SAMPLE_ASSETS[0]],
            "products": SAMPLE_PRODUCTS[:2],
            "production_schedule": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "scheduled_quantity": 500,
                    "scheduled_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
            "production_actuals": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "actual_quantity": 200,
                    "production_date": TEST_DATE,
                    "shift": "Day",
                },
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_BRAZILIAN_ID,
                    "actual_quantity": 300,
                    "production_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
        })

        response = client.get(
            f"/api/v1/production/schedule-attainment?date={TEST_DATE}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()

        roasting = next(wc for wc in data["workcenters"] if wc["workcenter"] == "Roasting")

        # Colombian product should show partial attainment
        colombian = next(
            p for p in roasting["products"] if p["product_name"] == "Colombian"
        )
        assert colombian["actual_quantity"] == 200
        assert colombian["scheduled_quantity"] == 500
        assert colombian["attainment_pct"] == 40.0

        # Brazilian should appear as unscheduled variance
        unscheduled_vars = [
            v for v in roasting["variances"] if v["variance_type"] == "unscheduled"
        ]
        assert len(unscheduled_vars) >= 1


# =============================================================================
# AC3: No schedule data — Integration Tests
# =============================================================================


class TestScheduleAttainmentNoData:
    """Tests for no-schedule-data scenario (AC#3)."""

    def test_INT_016_no_schedule_returns_200_with_empty_result(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-016: No schedule data returns 200 with empty result and message.

        Given: production_schedule returns empty for date 2026-03-01
        When: GET /api/v1/production/schedule-attainment?date=2026-03-01
        Then: 200, has_data=false, workcenters=[], message="No schedule data for this date"
        """
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "products": SAMPLE_PRODUCTS,
            "production_schedule": [],
            "production_actuals": [],
        })

        response = client.get(
            f"/api/v1/production/schedule-attainment?date={EMPTY_DATE}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_data"] is False
        assert data["workcenters"] == []
        assert data["message"] == "No schedule data for this date"

    def test_INT_017_no_schedule_does_not_return_404(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-017: No schedule data does NOT return 404.

        Given: production_schedule returns no rows
        When: GET /api/v1/production/schedule-attainment?date=2026-03-01
        Then: Response status is explicitly 200, NOT 404
        """
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "products": SAMPLE_PRODUCTS,
            "production_schedule": [],
            "production_actuals": [],
        })

        response = client.get(
            f"/api/v1/production/schedule-attainment?date={EMPTY_DATE}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        assert response.status_code != 404

    def test_INT_018_empty_schedule_with_actuals_still_returns_empty(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-018: Empty schedule with actuals present still returns empty result.

        Given: No schedule for 2026-03-01. Actuals DO exist.
        When: GET /api/v1/production/schedule-attainment?date=2026-03-01
        Then: 200, has_data=false, workcenters=[], message="No schedule data for this date"
        """
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "products": SAMPLE_PRODUCTS,
            "production_schedule": [],  # Empty schedule
            "production_actuals": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "actual_quantity": 500,
                    "production_date": EMPTY_DATE,
                    "shift": "Day",
                },
            ],
        })

        response = client.get(
            f"/api/v1/production/schedule-attainment?date={EMPTY_DATE}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_data"] is False
        assert data["workcenters"] == []
        assert data["message"] == "No schedule data for this date"


# =============================================================================
# AC4: Authentication required — Integration Tests
# =============================================================================


class TestScheduleAttainmentAuth:
    """Tests for authentication on schedule-attainment endpoint (AC#4)."""

    def test_INT_019_no_auth_token_returns_401(self, client):
        """12-5-schedule-attainment-api-INT-019: No auth token returns 401.

        Given: No Authorization header
        When: GET /api/v1/production/schedule-attainment?date=2026-02-09
        Then: Response status is 401
        """
        response = client.get(
            f"/api/v1/production/schedule-attainment?date={TEST_DATE}",
        )

        assert response.status_code == 401

    def test_INT_020_no_auth_token_returns_401_on_legacy_path(self, client):
        """12-5-schedule-attainment-api-INT-020: No auth token returns 401 on legacy path.

        Given: No Authorization header
        When: GET /api/production/schedule-attainment?date=2026-02-09
        Then: Response status is 401
        """
        response = client.get(
            f"/api/production/schedule-attainment?date={TEST_DATE}",
        )

        assert response.status_code == 401

    def test_INT_021_expired_token_returns_401(
        self, client, mock_verify_jwt_expired
    ):
        """12-5-schedule-attainment-api-INT-021: Expired token returns 401.

        Given: An expired JWT token
        When: GET /api/v1/production/schedule-attainment?date=2026-02-09
        Then: Response status is 401
        """
        response = client.get(
            f"/api/v1/production/schedule-attainment?date={TEST_DATE}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 401

    def test_INT_022_invalid_token_returns_401(
        self, client, mock_verify_jwt_invalid
    ):
        """12-5-schedule-attainment-api-INT-022: Invalid token returns 401.

        Given: An invalid JWT token
        When: GET /api/v1/production/schedule-attainment?date=2026-02-09
        Then: Response status is 401
        """
        response = client.get(
            f"/api/v1/production/schedule-attainment?date={TEST_DATE}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 401


# =============================================================================
# AC5: Area filter — Integration Tests
# =============================================================================


class TestScheduleAttainmentAreaFilter:
    """Tests for area filtering on schedule-attainment endpoint (AC#5)."""

    def test_INT_023_area_filter_returns_only_matching_workcenters(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-023: Area filter returns only matching workcenters.

        Given: Data for "Roasting" and "Grinding" workcenters
        When: GET with area=Roasting
        Then: Only "Roasting" workcenter in response; "Grinding" excluded
        """
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "products": SAMPLE_PRODUCTS[:2],
            "production_schedule": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "scheduled_quantity": 500,
                    "scheduled_date": TEST_DATE,
                    "shift": "Day",
                },
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_GRINDER_1_ID,
                    "product_id": PRODUCT_BRAZILIAN_ID,
                    "scheduled_quantity": 300,
                    "scheduled_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
            "production_actuals": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "actual_quantity": 450,
                    "production_date": TEST_DATE,
                    "shift": "Day",
                },
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_GRINDER_1_ID,
                    "product_id": PRODUCT_BRAZILIAN_ID,
                    "actual_quantity": 300,
                    "production_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
        })

        response = client.get(
            f"/api/v1/production/schedule-attainment?date={TEST_DATE}&area=Roasting",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()

        wc_names = [wc["workcenter"] for wc in data["workcenters"]]
        assert "Roasting" in wc_names
        assert "Grinding" not in wc_names

    def test_INT_024_area_filter_is_case_insensitive(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-024: Area filter is case-insensitive.

        Given: Assets have area "Roasting" (title case)
        When: GET with area=roasting (lowercase)
        Then: 200 and "Roasting" workcenter is included
        """
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "products": [SAMPLE_PRODUCTS[0]],
            "production_schedule": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "scheduled_quantity": 500,
                    "scheduled_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
            "production_actuals": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "actual_quantity": 450,
                    "production_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
        })

        response = client.get(
            f"/api/v1/production/schedule-attainment?date={TEST_DATE}&area=roasting",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        wc_names = [wc["workcenter"] for wc in data["workcenters"]]
        assert "Roasting" in wc_names

    def test_INT_025_area_filter_with_no_matching_workcenters_returns_empty(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-025: Area filter with no matching workcenters returns empty.

        Given: Schedule data exists but no assets have area "NonExistent"
        When: GET with area=NonExistent
        Then: 200, workcenters=[], has_data=true (schedule exists, just no matching area)
        """
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "products": [SAMPLE_PRODUCTS[0]],
            "production_schedule": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "scheduled_quantity": 500,
                    "scheduled_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
            "production_actuals": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "actual_quantity": 450,
                    "production_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
        })

        response = client.get(
            f"/api/v1/production/schedule-attainment?date={TEST_DATE}&area=NonExistent",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["workcenters"] == []
        # has_data should be true since schedule data exists overall
        assert data["has_data"] is True

    def test_INT_026_no_area_parameter_returns_all_workcenters(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-026: No area parameter returns all workcenters.

        Given: Data for "Roasting" and "Grinding" workcenters
        When: GET without area parameter
        Then: Both workcenters included in response
        """
        _make_table_mock(mock_supabase_client, {
            "assets": SAMPLE_ASSETS,
            "products": SAMPLE_PRODUCTS[:2],
            "production_schedule": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "scheduled_quantity": 500,
                    "scheduled_date": TEST_DATE,
                    "shift": "Day",
                },
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_GRINDER_1_ID,
                    "product_id": PRODUCT_BRAZILIAN_ID,
                    "scheduled_quantity": 300,
                    "scheduled_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
            "production_actuals": [
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_ROASTER_1_ID,
                    "product_id": PRODUCT_COLOMBIAN_ID,
                    "actual_quantity": 450,
                    "production_date": TEST_DATE,
                    "shift": "Day",
                },
                {
                    "id": str(uuid4()),
                    "asset_id": ASSET_GRINDER_1_ID,
                    "product_id": PRODUCT_BRAZILIAN_ID,
                    "actual_quantity": 300,
                    "production_date": TEST_DATE,
                    "shift": "Day",
                },
            ],
        })

        response = client.get(
            f"/api/v1/production/schedule-attainment?date={TEST_DATE}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        wc_names = [wc["workcenter"] for wc in data["workcenters"]]
        assert "Roasting" in wc_names
        assert "Grinding" in wc_names


# =============================================================================
# Error Scenarios — Integration Tests
# =============================================================================


class TestScheduleAttainmentErrors:
    """Tests for error scenarios."""

    def test_INT_027_supabase_query_failure_returns_500(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-027: Supabase query failure returns 500.

        Given: Supabase client raises an unexpected exception
        When: GET /api/v1/production/schedule-attainment?date=2026-02-09
        Then: Response 500 with detail "Failed to fetch schedule attainment data"
        """
        mock_supabase_client.table.side_effect = Exception("Connection refused")

        response = client.get(
            f"/api/v1/production/schedule-attainment?date={TEST_DATE}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to fetch schedule attainment data"

    def test_INT_028_supabase_not_configured_returns_503(
        self, client, mock_verify_jwt
    ):
        """12-5-schedule-attainment-api-INT-028: Supabase not configured returns 503.

        Given: get_supabase_client raises HTTPException 503
        When: GET /api/v1/production/schedule-attainment?date=2026-02-09
        Then: Response 503 with detail "Supabase not configured"
        """
        from fastapi import HTTPException, status

        with patch("app.api.production.get_supabase_client", new_callable=AsyncMock) as mock_client:
            mock_client.side_effect = HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase not configured",
            )

            response = client.get(
                f"/api/v1/production/schedule-attainment?date={TEST_DATE}",
                headers=AUTH_HEADERS,
            )

        assert response.status_code == 503
        assert response.json()["detail"] == "Supabase not configured"

    def test_INT_029_invalid_date_format_returns_422(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-029: Invalid date format returns 422.

        Given: Invalid date string "not-a-date"
        When: GET /api/v1/production/schedule-attainment?date=not-a-date
        Then: Response 422 (Unprocessable Entity)
        """
        response = client.get(
            "/api/v1/production/schedule-attainment?date=not-a-date",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 422

    def test_INT_030_missing_date_parameter_returns_422(
        self, client, mock_verify_jwt, mock_supabase_client
    ):
        """12-5-schedule-attainment-api-INT-030: Missing required date parameter returns 422.

        Given: No date parameter
        When: GET /api/v1/production/schedule-attainment (no date)
        Then: Response 422
        """
        response = client.get(
            "/api/v1/production/schedule-attainment",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 422


# =============================================================================
# Schema Validation — Unit Tests
# =============================================================================


class TestScheduleAttainmentSchemas:
    """Unit tests for Pydantic response schemas."""

    def test_UNIT_001_schedule_attainment_response_schema(self):
        """12-5-schedule-attainment-api-UNIT-001: ScheduleAttainmentResponse schema validates correctly.

        Given: Valid data for ScheduleAttainmentResponse
        When: Instantiated with date, workcenters=[], has_data=True, message=None
        Then: All fields are correctly typed
        """
        from app.schemas.production import ScheduleAttainmentResponse

        resp = ScheduleAttainmentResponse(
            date="2026-02-09",
            workcenters=[],
            has_data=True,
            message=None,
        )

        assert resp.date == "2026-02-09"
        assert resp.workcenters == []
        assert resp.has_data is True
        assert resp.message is None

    def test_UNIT_002_product_attainment_schema(self):
        """12-5-schedule-attainment-api-UNIT-002: ProductAttainment schema validates correctly.

        Given: Valid data for ProductAttainment
        When: Instantiated with known values
        Then: All fields are correctly typed
        """
        from app.schemas.production import ProductAttainment

        product = ProductAttainment(
            product_name="Colombian",
            product_id="uuid-string",
            scheduled_quantity=500,
            actual_quantity=450,
            attainment_pct=90.0,
        )

        assert product.product_name == "Colombian"
        assert product.product_id == "uuid-string"
        assert product.scheduled_quantity == 500
        assert product.actual_quantity == 450
        assert product.attainment_pct == 90.0

    def test_UNIT_003_variance_callout_schema(self):
        """12-5-schedule-attainment-api-UNIT-003: VarianceCallout schema validates correctly.

        Given: Valid data for VarianceCallout
        When: Instantiated with each variance_type value
        Then: All fields are correctly typed and all variance_type values accepted
        """
        from app.schemas.production import VarianceCallout

        # Test "swap" variance type
        swap = VarianceCallout(
            asset_name="Roaster 1",
            message="Roaster 1 ran Colombian instead of scheduled Brazilian",
            variance_type="swap",
        )
        assert swap.asset_name == "Roaster 1"
        assert swap.variance_type == "swap"

        # Test "missing" variance type
        missing = VarianceCallout(
            asset_name="Roaster 1",
            message="Scheduled Colombian but no production recorded",
            variance_type="missing",
        )
        assert missing.variance_type == "missing"

        # Test "unscheduled" variance type
        unscheduled = VarianceCallout(
            asset_name="Grinder 1",
            message="Produced Brazilian but not scheduled",
            variance_type="unscheduled",
        )
        assert unscheduled.variance_type == "unscheduled"

    def test_UNIT_004_workcenter_schedule_attainment_schema(self):
        """12-5-schedule-attainment-api-UNIT-004: WorkcenterScheduleAttainment schema validates correctly.

        Given: Valid data with nested models
        When: Instantiated with products and variances lists
        Then: All fields are correctly typed
        """
        from app.schemas.production import (
            ProductAttainment,
            VarianceCallout,
            WorkcenterScheduleAttainment,
        )

        product = ProductAttainment(
            product_name="Colombian",
            product_id="uuid-string",
            scheduled_quantity=500,
            actual_quantity=450,
            attainment_pct=90.0,
        )

        variance = VarianceCallout(
            asset_name="Roaster 1",
            message="Test variance",
            variance_type="swap",
        )

        wc = WorkcenterScheduleAttainment(
            workcenter="Roasting",
            products=[product],
            variances=[variance],
            overall_attainment_pct=93.8,
        )

        assert wc.workcenter == "Roasting"
        assert len(wc.products) == 1
        assert isinstance(wc.products[0], ProductAttainment)
        assert len(wc.variances) == 1
        assert isinstance(wc.variances[0], VarianceCallout)
        assert wc.overall_attainment_pct == 93.8
