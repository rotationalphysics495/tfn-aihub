"""
Tests for Story 10.3: Cost of Loss Schema Fix.

Validates that the financial API endpoints use the correct column name
`waste_count` (not `waste`) when querying the `daily_summaries` table.

The daily_summaries table schema defines the column as `waste_count`
(see supabase/migrations/0003_analytical_cache.sql).

Test-First Development: These tests are designed to FAIL until the
feature code is updated to use the correct column name.
"""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# AC1: Daily Summary Query Uses Correct Column Name
# ---------------------------------------------------------------------------


class TestCostOfLossDailyQueryColumnName:
    """AC1: The cost-of-loss endpoint queries daily_summaries with waste_count."""

    def test_unit_001_cost_of_loss_daily_select_references_waste_count(
        self, client, mock_verify_jwt
    ):
        """
        10-3-cost-of-loss-schema-fix-UNIT-001:
        Cost-of-loss daily query SELECT references waste_count column.

        Given: An authenticated user and the get_cost_of_loss endpoint
        When: The endpoint queries daily_summaries with period=daily
        Then: The Supabase .select() call includes 'waste_count' (not 'waste')
        """
        with patch("app.api.financial.get_supabase_client") as mock_supabase:
            with patch("app.api.financial.get_financial_service") as mock_service:
                mock_client = MagicMock()
                mock_supabase.return_value = mock_client

                # Set up the chain to return empty data so the endpoint completes
                mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

                mock_instance = MagicMock()
                mock_instance.load_cost_centers = MagicMock()
                mock_service.return_value = mock_instance

                response = client.get(
                    "/api/financial/cost-of-loss?period=daily",
                    headers={"Authorization": "Bearer test-token"},
                )

                assert response.status_code == 200

                # Verify .select() was called with a string containing 'waste_count'
                select_call = mock_client.table.return_value.select
                select_call.assert_called_once()
                select_arg = select_call.call_args[0][0]
                assert "waste_count" in select_arg, (
                    f"Expected 'waste_count' in SELECT string, got: '{select_arg}'"
                )
                assert "waste," not in select_arg.replace("waste_count", "").replace(
                    "waste_cost", ""
                ).replace("waste_loss", ""), (
                    f"Found bare 'waste' column in SELECT string: '{select_arg}'"
                )

    def test_unit_002_cost_of_loss_extracts_waste_count_from_record(
        self, client, mock_verify_jwt
    ):
        """
        10-3-cost-of-loss-schema-fix-UNIT-002:
        Cost-of-loss daily query extracts waste_count from record.

        Given: The daily_summaries query returns records with key "waste_count"
        When: The endpoint iterates over response data and calls record.get()
        Then: The value is extracted using key "waste_count" (not "waste")
        And: The extracted value is passed to calculate_waste_loss()
        """
        with patch("app.api.financial.get_supabase_client") as mock_supabase:
            with patch("app.api.financial.get_financial_service") as mock_service:
                mock_client = MagicMock()
                mock_supabase.return_value = mock_client

                # Mock data using the CORRECT key "waste_count"
                # If the code reads record.get("waste"), it will get None -> 0
                mock_data = [
                    {
                        "asset_id": "asset-1",
                        "downtime_minutes": 60,
                        "waste_count": 10,
                        "financial_loss": 500.00,
                        "oee_percentage": 75.0,
                        "created_at": "2026-01-05T06:00:00Z",
                    }
                ]
                mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
                    mock_data
                )

                mock_instance = MagicMock()
                mock_instance.load_cost_centers = MagicMock()
                mock_instance.get_hourly_rate = MagicMock(
                    return_value=(Decimal("100.00"), False)
                )
                mock_instance.get_cost_per_unit = MagicMock(
                    return_value=(Decimal("20.00"), False)
                )
                mock_instance.calculate_downtime_loss = MagicMock(
                    return_value=Decimal("100.00")
                )
                mock_instance.calculate_waste_loss = MagicMock(
                    return_value=Decimal("200.00")
                )
                mock_service.return_value = mock_instance

                response = client.get(
                    "/api/financial/cost-of-loss?period=daily",
                    headers={"Authorization": "Bearer test-token"},
                )

                assert response.status_code == 200

                # The endpoint should call calculate_waste_loss with 10 (the waste_count value)
                # If it reads record.get("waste"), it gets None -> 0, and passes 0 instead
                mock_instance.calculate_waste_loss.assert_called_once()
                waste_arg = mock_instance.calculate_waste_loss.call_args[0][0]
                assert waste_arg == 10, (
                    f"Expected waste_count=10 to be passed to calculate_waste_loss, "
                    f"but got {waste_arg}. The code likely reads 'waste' instead of 'waste_count'."
                )

    def test_int_001_cost_of_loss_daily_returns_200_with_correct_waste_cost(
        self, client, mock_verify_jwt
    ):
        """
        10-3-cost-of-loss-schema-fix-INT-001:
        Cost-of-loss daily endpoint returns 200 with correct waste cost.

        Given: Mock daily_summaries data with waste_count: 10 and cost_per_unit: 20.00
        When: GET /api/financial/cost-of-loss?period=daily is called
        Then: Response 200, breakdown.waste_cost equals 10 * 20.00 = 200.00
        """
        with patch("app.api.financial.get_supabase_client") as mock_supabase:
            with patch("app.api.financial.get_financial_service") as mock_service:
                mock_client = MagicMock()
                mock_supabase.return_value = mock_client

                mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                    {
                        "asset_id": "asset-1",
                        "downtime_minutes": 30,
                        "waste_count": 10,
                        "financial_loss": 500.00,
                        "oee_percentage": 85.0,
                        "created_at": "2026-02-10T06:00:00Z",
                    }
                ]

                mock_instance = MagicMock()
                mock_instance.load_cost_centers = MagicMock()
                mock_instance.get_hourly_rate = MagicMock(
                    return_value=(Decimal("100.00"), False)
                )
                mock_instance.get_cost_per_unit = MagicMock(
                    return_value=(Decimal("20.00"), False)
                )
                # calculate_waste_loss should be called with waste_count=10
                # Return the expected result: 10 * 20.00 = 200.00
                mock_instance.calculate_waste_loss = MagicMock(
                    return_value=Decimal("200.00")
                )
                mock_instance.calculate_downtime_loss = MagicMock(
                    return_value=Decimal("50.00")
                )
                mock_service.return_value = mock_instance

                response = client.get(
                    "/api/financial/cost-of-loss?period=daily",
                    headers={"Authorization": "Bearer test-token"},
                )

                assert response.status_code == 200
                data = response.json()

                # Verify calculate_waste_loss was called with the correct waste_count
                waste_arg = mock_instance.calculate_waste_loss.call_args[0][0]
                assert waste_arg == 10, (
                    f"Expected waste_count=10, got {waste_arg}. "
                    f"Code likely reads 'waste' key instead of 'waste_count'."
                )

                # The breakdown should reflect the correct waste cost
                assert data["breakdown"]["waste_cost"] == 200.00, (
                    f"Expected waste_cost=200.00, got {data['breakdown']['waste_cost']}. "
                    f"Waste cost is 0 because code reads wrong column name."
                )

    def test_int_002_cost_of_loss_daily_no_500_from_wrong_column(
        self, client, mock_verify_jwt
    ):
        """
        10-3-cost-of-loss-schema-fix-INT-002:
        Cost-of-loss daily endpoint does not produce 500 error from wrong column.

        Given: Valid daily_summaries data
        When: GET /api/financial/cost-of-loss?period=daily is called
        Then: Response 200 (not 500), no error about non-existent 'waste' column
        """
        with patch("app.api.financial.get_supabase_client") as mock_supabase:
            with patch("app.api.financial.get_financial_service") as mock_service:
                mock_client = MagicMock()
                mock_supabase.return_value = mock_client

                # Data uses the CORRECT schema key "waste_count"
                mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                    {
                        "asset_id": "asset-1",
                        "downtime_minutes": 30,
                        "waste_count": 5,
                        "financial_loss": 200.00,
                        "oee_percentage": 90.0,
                        "created_at": "2026-02-10T06:00:00Z",
                    }
                ]

                mock_instance = MagicMock()
                mock_instance.load_cost_centers = MagicMock()
                mock_instance.get_hourly_rate = MagicMock(
                    return_value=(Decimal("100.00"), False)
                )
                mock_instance.get_cost_per_unit = MagicMock(
                    return_value=(Decimal("10.00"), False)
                )
                mock_instance.calculate_downtime_loss = MagicMock(
                    return_value=Decimal("50.00")
                )
                mock_instance.calculate_waste_loss = MagicMock(
                    return_value=Decimal("50.00")
                )
                mock_service.return_value = mock_instance

                response = client.get(
                    "/api/financial/cost-of-loss?period=daily",
                    headers={"Authorization": "Bearer test-token"},
                )

                assert response.status_code == 200

                # Verify the SELECT string uses waste_count
                select_call = mock_client.table.return_value.select
                select_arg = select_call.call_args[0][0]
                assert "waste_count" in select_arg, (
                    f"SELECT should use 'waste_count', not 'waste'. Got: '{select_arg}'"
                )

    def test_unit_003_cost_of_loss_handles_null_waste_count(
        self, client, mock_verify_jwt
    ):
        """
        10-3-cost-of-loss-schema-fix-UNIT-003:
        Cost-of-loss daily query handles null/zero waste_count gracefully.

        Given: A daily_summaries record where waste_count is null (None)
        When: The endpoint processes this record
        Then: waste_count defaults to 0, waste_cost is 0.00, no exception
        """
        with patch("app.api.financial.get_supabase_client") as mock_supabase:
            with patch("app.api.financial.get_financial_service") as mock_service:
                mock_client = MagicMock()
                mock_supabase.return_value = mock_client

                mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                    {
                        "asset_id": "asset-1",
                        "downtime_minutes": 30,
                        "waste_count": None,
                        "financial_loss": 100.00,
                        "oee_percentage": 90.0,
                        "created_at": "2026-02-10T06:00:00Z",
                    }
                ]

                mock_instance = MagicMock()
                mock_instance.load_cost_centers = MagicMock()
                mock_instance.get_hourly_rate = MagicMock(
                    return_value=(Decimal("100.00"), False)
                )
                mock_instance.get_cost_per_unit = MagicMock(
                    return_value=(Decimal("10.00"), False)
                )
                mock_instance.calculate_downtime_loss = MagicMock(
                    return_value=Decimal("50.00")
                )
                mock_instance.calculate_waste_loss = MagicMock(
                    return_value=Decimal("0.00")
                )
                mock_service.return_value = mock_instance

                response = client.get(
                    "/api/financial/cost-of-loss?period=daily",
                    headers={"Authorization": "Bearer test-token"},
                )

                assert response.status_code == 200

                # calculate_waste_loss should be called with 0 (null defaults to 0)
                mock_instance.calculate_waste_loss.assert_called_once()
                waste_arg = mock_instance.calculate_waste_loss.call_args[0][0]
                assert waste_arg == 0, (
                    f"Expected waste_count to default to 0 for null value, got {waste_arg}"
                )

    def test_int_003_cost_of_loss_with_asset_id_filter_uses_correct_column(
        self, client, mock_verify_jwt
    ):
        """
        10-3-cost-of-loss-schema-fix-INT-003:
        Cost-of-loss with asset_id filter uses correct column.

        Given: Authenticated user requesting cost-of-loss filtered by asset_id
        When: GET /api/financial/cost-of-loss?period=daily&asset_id=asset-1
        Then: The query still uses waste_count in the SELECT
        And: Response returns data only for the specified asset
        """
        with patch("app.api.financial.get_supabase_client") as mock_supabase:
            with patch("app.api.financial.get_financial_service") as mock_service:
                mock_client = MagicMock()
                mock_supabase.return_value = mock_client

                # With asset_id filter, the chain includes an extra .eq()
                mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
                    {
                        "asset_id": "asset-1",
                        "downtime_minutes": 45,
                        "waste_count": 8,
                        "financial_loss": 300.00,
                        "oee_percentage": 80.0,
                        "created_at": "2026-02-10T06:00:00Z",
                    }
                ]

                mock_instance = MagicMock()
                mock_instance.load_cost_centers = MagicMock()
                mock_instance.get_hourly_rate = MagicMock(
                    return_value=(Decimal("100.00"), False)
                )
                mock_instance.get_cost_per_unit = MagicMock(
                    return_value=(Decimal("15.00"), False)
                )
                mock_instance.calculate_downtime_loss = MagicMock(
                    return_value=Decimal("75.00")
                )
                mock_instance.calculate_waste_loss = MagicMock(
                    return_value=Decimal("120.00")
                )
                mock_service.return_value = mock_instance

                response = client.get(
                    "/api/financial/cost-of-loss?period=daily&asset_id=asset-1",
                    headers={"Authorization": "Bearer test-token"},
                )

                assert response.status_code == 200

                # Verify the SELECT contains waste_count
                select_call = mock_client.table.return_value.select
                select_arg = select_call.call_args[0][0]
                assert "waste_count" in select_arg, (
                    f"Expected 'waste_count' in SELECT with asset filter, got: '{select_arg}'"
                )


# ---------------------------------------------------------------------------
# AC2: Financial Summary Query Uses Correct Column Name
# ---------------------------------------------------------------------------


class TestFinancialSummaryQueryColumnName:
    """AC2: The financial summary endpoint queries daily_summaries with waste_count."""

    def test_unit_004_financial_summary_select_references_waste_count(
        self, client, mock_verify_jwt
    ):
        """
        10-3-cost-of-loss-schema-fix-UNIT-004:
        Financial summary SELECT references waste_count column.

        Given: The get_financial_summary endpoint handler
        When: The endpoint queries daily_summaries
        Then: The Supabase .select() call includes 'waste_count' (not 'waste')
        """
        with patch("app.api.financial.get_supabase_client") as mock_supabase:
            with patch("app.api.financial.get_financial_service") as mock_service:
                mock_client = MagicMock()
                mock_supabase.return_value = mock_client

                mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

                mock_instance = MagicMock()
                mock_instance.load_cost_centers = MagicMock()
                mock_service.return_value = mock_instance

                response = client.get(
                    "/api/financial/summary",
                    headers={"Authorization": "Bearer test-token"},
                )

                assert response.status_code == 200

                # Verify .select() was called with waste_count
                select_call = mock_client.table.return_value.select
                select_call.assert_called_once()
                select_arg = select_call.call_args[0][0]
                assert "waste_count" in select_arg, (
                    f"Expected 'waste_count' in SELECT for financial summary, got: '{select_arg}'"
                )

    def test_unit_005_financial_summary_extracts_waste_count_and_aggregates(
        self, client, mock_verify_jwt
    ):
        """
        10-3-cost-of-loss-schema-fix-UNIT-005:
        Financial summary extracts waste_count and aggregates correctly.

        Given: Multiple daily_summaries records with waste_count values 5, 10, 15
        When: The endpoint aggregates total_waste_count
        Then: total_waste_count equals 30 (sum), extracted using key "waste_count"
        """
        with patch("app.api.financial.get_supabase_client") as mock_supabase:
            with patch("app.api.financial.get_financial_service") as mock_service:
                mock_client = MagicMock()
                mock_supabase.return_value = mock_client

                # Use CORRECT key "waste_count" — code using "waste" will get None -> 0
                mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                    {
                        "asset_id": "a1",
                        "downtime_minutes": 30,
                        "waste_count": 5,
                        "financial_loss": 200.00,
                    },
                    {
                        "asset_id": "a2",
                        "downtime_minutes": 45,
                        "waste_count": 10,
                        "financial_loss": 300.00,
                    },
                    {
                        "asset_id": "a3",
                        "downtime_minutes": 60,
                        "waste_count": 15,
                        "financial_loss": 400.00,
                    },
                ]

                mock_instance = MagicMock()
                mock_instance.load_cost_centers = MagicMock()
                mock_instance.get_hourly_rate = MagicMock(
                    return_value=(Decimal("100.00"), False)
                )
                mock_instance.get_cost_per_unit = MagicMock(
                    return_value=(Decimal("10.00"), False)
                )
                mock_instance.calculate_downtime_loss = MagicMock(
                    return_value=Decimal("50.00")
                )
                mock_instance.calculate_waste_loss = MagicMock(
                    return_value=Decimal("50.00")
                )
                mock_service.return_value = mock_instance

                response = client.get(
                    "/api/financial/summary",
                    headers={"Authorization": "Bearer test-token"},
                )

                assert response.status_code == 200
                data = response.json()

                # total_waste_count should be 5 + 10 + 15 = 30
                assert data["total_waste_count"] == 30, (
                    f"Expected total_waste_count=30, got {data.get('total_waste_count')}. "
                    f"Code likely reads 'waste' key instead of 'waste_count', getting 0 for each record."
                )

    def test_int_004_financial_summary_returns_correct_total_waste_count(
        self, client, mock_verify_jwt
    ):
        """
        10-3-cost-of-loss-schema-fix-INT-004:
        Financial summary endpoint returns correct total_waste_count.

        Given: Mock daily_summaries with known waste_count values
        When: GET /api/financial/summary
        Then: Response 200, total_waste_count correct, total_waste_loss calculated
        """
        with patch("app.api.financial.get_supabase_client") as mock_supabase:
            with patch("app.api.financial.get_financial_service") as mock_service:
                mock_client = MagicMock()
                mock_supabase.return_value = mock_client

                mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                    {
                        "asset_id": "asset-1",
                        "downtime_minutes": 30,
                        "waste_count": 5,
                        "financial_loss": 200.00,
                    },
                    {
                        "asset_id": "asset-2",
                        "downtime_minutes": 45,
                        "waste_count": 10,
                        "financial_loss": 350.00,
                    },
                ]

                mock_instance = MagicMock()
                mock_instance.load_cost_centers = MagicMock()
                mock_instance.get_hourly_rate = MagicMock(
                    return_value=(Decimal("100.00"), False)
                )

                # Different cost_per_unit per asset
                def cost_per_unit_side_effect(asset_id):
                    rates = {
                        "asset-1": (Decimal("10.00"), False),
                        "asset-2": (Decimal("15.00"), False),
                    }
                    return rates.get(asset_id, (Decimal("10.00"), False))

                mock_instance.get_cost_per_unit = MagicMock(
                    side_effect=cost_per_unit_side_effect
                )
                mock_instance.calculate_downtime_loss = MagicMock(
                    return_value=Decimal("50.00")
                )

                # calculate_waste_loss should be called with actual waste_count values
                def waste_loss_side_effect(waste_count, cost_per_unit):
                    return Decimal(str(waste_count)) * cost_per_unit

                mock_instance.calculate_waste_loss = MagicMock(
                    side_effect=waste_loss_side_effect
                )
                mock_service.return_value = mock_instance

                response = client.get(
                    "/api/financial/summary",
                    headers={"Authorization": "Bearer test-token"},
                )

                assert response.status_code == 200
                data = response.json()

                # total_waste_count should be 5 + 10 = 15
                assert data["total_waste_count"] == 15, (
                    f"Expected total_waste_count=15, got {data.get('total_waste_count')}"
                )

    def test_unit_006_financial_summary_handles_empty_response(
        self, client, mock_verify_jwt
    ):
        """
        10-3-cost-of-loss-schema-fix-UNIT-006:
        Financial summary handles empty daily_summaries response.

        Given: The daily_summaries query returns an empty list
        When: The endpoint aggregates waste data
        Then: total_waste_count is 0, total_waste_loss is 0.00, response 200
        """
        with patch("app.api.financial.get_supabase_client") as mock_supabase:
            with patch("app.api.financial.get_financial_service") as mock_service:
                mock_client = MagicMock()
                mock_supabase.return_value = mock_client

                mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
                    []
                )

                mock_instance = MagicMock()
                mock_instance.load_cost_centers = MagicMock()
                mock_service.return_value = mock_instance

                response = client.get(
                    "/api/financial/summary",
                    headers={"Authorization": "Bearer test-token"},
                )

                assert response.status_code == 200
                data = response.json()

                assert data["total_waste_count"] == 0, (
                    f"Expected total_waste_count=0 for empty data, got {data.get('total_waste_count')}"
                )
                assert data["total_loss"] == 0.0


# ---------------------------------------------------------------------------
# AC3: Financial Impact Service Uses Correct Column Name
# ---------------------------------------------------------------------------


class TestFinancialImpactServiceColumnName:
    """AC3: The FinancialService.get_financial_impact() uses waste_count."""

    @staticmethod
    def _make_service_with_mock_client(mock_client, asset_id, cost_center, asset_name="Test Asset"):
        """Helper to create a FinancialService with a mock Supabase client injected."""
        from app.services.financial import FinancialService

        service = FinancialService()
        # Inject mock client directly, bypassing _get_supabase_client
        service._supabase_client = mock_client
        # Pre-populate caches to avoid real queries
        service._cost_center_cache = {
            asset_id: {
                "hourly_rate": Decimal(str(cost_center["standard_hourly_rate"])),
                "cost_per_unit": Decimal(str(cost_center["cost_per_unit"])),
            }
        }
        service._asset_cache = {asset_id: {"name": asset_name}}
        from datetime import datetime

        service._cache_timestamp = datetime.utcnow()
        return service

    @pytest.mark.asyncio
    async def test_unit_007_financial_impact_select_references_waste_count(self):
        """
        10-3-cost-of-loss-schema-fix-UNIT-007:
        Financial impact SELECT references waste_count column.

        Given: The FinancialService.get_financial_impact() method
        When: It queries daily_summaries for an asset's date range
        Then: The Supabase .select() call includes 'waste_count' (not 'waste')
        """
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []

        service = self._make_service_with_mock_client(
            mock_client,
            "asset-grd-005",
            {"standard_hourly_rate": 100.00, "cost_per_unit": 20.24},
            "Grinder 005",
        )

        await service.get_financial_impact("asset-grd-005", start_date=date.today())

        # Verify the SELECT string
        select_call = mock_client.table.return_value.select
        assert select_call.called, "Expected Supabase .select() to be called"
        select_arg = select_call.call_args[0][0]
        assert "waste_count" in select_arg, (
            f"Expected 'waste_count' in SELECT for financial impact, got: '{select_arg}'"
        )

    @pytest.mark.asyncio
    async def test_unit_008_financial_impact_extracts_waste_count_with_correct_key(self):
        """
        10-3-cost-of-loss-schema-fix-UNIT-008:
        Financial impact extracts waste_count with correct key.

        Given: daily_summaries records containing "waste_count": 23
        When: get_financial_impact() processes the records
        Then: The value is extracted using key "waste_count" (not "waste")
        And: total_waste is summed correctly
        """
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {
                "asset_id": "asset-grd-005",
                "date": "2026-02-10",
                "downtime_minutes": 47,
                "waste_count": 23,
                "financial_loss": 500.00,
            }
        ]

        service = self._make_service_with_mock_client(
            mock_client,
            "asset-grd-005",
            {"standard_hourly_rate": 2393.62, "cost_per_unit": 20.24},
            "Grinder 005",
        )

        result = await service.get_financial_impact("asset-grd-005", start_date=date(2026, 2, 10))

        # If code reads "waste" key, total_waste will be 0, not 23
        assert result.waste_count == 23, (
            f"Expected waste_count=23, got {result.waste_count}. "
            f"Code likely reads 'waste' key instead of 'waste_count'."
        )

    @pytest.mark.asyncio
    async def test_unit_009_financial_impact_calculates_waste_loss(self):
        """
        10-3-cost-of-loss-schema-fix-UNIT-009:
        Financial impact calculates waste_loss using waste_count * cost_per_unit.

        Given: waste_count: 23 and cost_per_unit: 20.24
        When: get_financial_impact() calculates waste loss
        Then: waste_loss equals 23 * 20.24 = 465.52
        """
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {
                "asset_id": "asset-grd-005",
                "date": "2026-02-10",
                "downtime_minutes": 47,
                "waste_count": 23,
                "financial_loss": 500.00,
            }
        ]

        service = self._make_service_with_mock_client(
            mock_client,
            "asset-grd-005",
            {"standard_hourly_rate": 2393.62, "cost_per_unit": 20.24},
            "Grinder 005",
        )

        result = await service.get_financial_impact("asset-grd-005", start_date=date(2026, 2, 10))

        # waste_loss should be 23 * 20.24 = 465.52
        assert result.waste_loss == pytest.approx(465.52, abs=0.01), (
            f"Expected waste_loss=465.52 (23 * 20.24), got {result.waste_loss}. "
            f"Code likely reads 'waste' key instead of 'waste_count', yielding 0."
        )

    @pytest.mark.asyncio
    async def test_unit_010_financial_impact_multiple_records_sums_waste_count(self):
        """
        10-3-cost-of-loss-schema-fix-UNIT-010:
        Financial impact with multiple records sums waste_count correctly.

        Given: Three records with waste_count 10, 20, 30
        When: get_financial_impact() aggregates over date range
        Then: total_waste equals 60, waste_loss = 60 * 15.00 = 900.00
        """
        mock_client = MagicMock()
        # For date range queries: .eq(asset_id).gte(date).lte(date).execute()
        mock_client.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value.data = [
            {
                "asset_id": "asset-1",
                "date": "2026-02-08",
                "downtime_minutes": 30,
                "waste_count": 10,
                "financial_loss": 200.00,
            },
            {
                "asset_id": "asset-1",
                "date": "2026-02-09",
                "downtime_minutes": 45,
                "waste_count": 20,
                "financial_loss": 300.00,
            },
            {
                "asset_id": "asset-1",
                "date": "2026-02-10",
                "downtime_minutes": 60,
                "waste_count": 30,
                "financial_loss": 400.00,
            },
        ]

        service = self._make_service_with_mock_client(
            mock_client,
            "asset-1",
            {"standard_hourly_rate": 100.00, "cost_per_unit": 15.00},
        )

        result = await service.get_financial_impact(
            "asset-1",
            start_date=date(2026, 2, 8),
            end_date=date(2026, 2, 10),
        )

        assert result.waste_count == 60, (
            f"Expected total waste_count=60 (10+20+30), got {result.waste_count}"
        )
        assert result.waste_loss == pytest.approx(900.00, abs=0.01), (
            f"Expected waste_loss=900.00 (60 * 15.00), got {result.waste_loss}"
        )

    @pytest.mark.asyncio
    async def test_unit_011_financial_impact_handles_null_waste_count(self):
        """
        10-3-cost-of-loss-schema-fix-UNIT-011:
        Financial impact handles null waste_count in records.

        Given: A record where waste_count is None
        When: get_financial_impact() processes the record
        Then: waste_count defaults to 0, waste_loss is 0.00, no exception
        """
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {
                "asset_id": "asset-1",
                "date": "2026-02-10",
                "downtime_minutes": 30,
                "waste_count": None,
                "financial_loss": 100.00,
            }
        ]

        service = self._make_service_with_mock_client(
            mock_client,
            "asset-1",
            {"standard_hourly_rate": 100.00, "cost_per_unit": 10.00},
        )

        result = await service.get_financial_impact("asset-1", start_date=date(2026, 2, 10))

        assert result.waste_count == 0, (
            f"Expected waste_count=0 for null, got {result.waste_count}"
        )
        assert result.waste_loss == pytest.approx(0.00, abs=0.01), (
            f"Expected waste_loss=0.00, got {result.waste_loss}"
        )


# ---------------------------------------------------------------------------
# AC4: Existing Tests Updated To Match Schema
# ---------------------------------------------------------------------------


class TestExistingTestMockDataUpdated:
    """AC4: Existing test mocks use waste_count key, not bare 'waste'."""

    def test_unit_012_all_test_mock_data_uses_waste_count_key(self):
        """
        10-3-cost-of-loss-schema-fix-UNIT-012:
        All test mock data uses waste_count key.

        Given: The test file test_financial_api.py with mock daily_summaries data
        When: We search for bare "waste" key in mock data dictionaries
        Then: Zero matches — all mock data uses "waste_count"
        """
        import re
        import os

        # Resolve path relative to this test file's location
        test_dir = os.path.dirname(os.path.abspath(__file__))
        test_file = os.path.join(test_dir, "test_financial_api.py")
        with open(test_file, "r") as f:
            content = f.read()

        # Find all instances of "waste" that are NOT followed by _count, _cost, _loss
        # This catches "waste": as a dictionary key but not "waste_count", "waste_cost", etc.
        # Pattern: "waste" followed by optional quote then colon (dict key context)
        pattern = r'"waste"\s*:'
        matches = re.findall(pattern, content)

        # Filter out any that are within comments
        lines_with_bare_waste = []
        for line_num, line in enumerate(content.split("\n"), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.search(r'"waste"\s*:', line):
                lines_with_bare_waste.append((line_num, stripped))

        assert len(lines_with_bare_waste) == 0, (
            f"Found {len(lines_with_bare_waste)} mock data entries using bare 'waste' key "
            f"instead of 'waste_count' in {test_file}:\n"
            + "\n".join(
                f"  Line {ln}: {text}" for ln, text in lines_with_bare_waste
            )
        )

    def test_int_005_financial_summary_aggregates_data_passes_with_waste_count(
        self, client, mock_verify_jwt
    ):
        """
        10-3-cost-of-loss-schema-fix-INT-005:
        test_financial_summary_aggregates_data passes with waste_count mocks.

        Given: TestFinancialSummaryEndpoint with mock data using "waste_count" keys
        When: The test is executed
        Then: The test passes without assertion failures
        And: The endpoint correctly reads waste_count from the mock data
        """
        with patch("app.api.financial.get_supabase_client") as mock_supabase:
            with patch("app.api.financial.get_financial_service") as mock_service:
                mock_client = MagicMock()
                mock_supabase.return_value = mock_client

                # Updated mock data using waste_count (correct schema)
                mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                    {
                        "asset_id": "asset-1",
                        "downtime_minutes": 30,
                        "waste_count": 5,
                        "financial_loss": 200.00,
                    },
                    {
                        "asset_id": "asset-2",
                        "downtime_minutes": 45,
                        "waste_count": 10,
                        "financial_loss": 350.00,
                    },
                ]

                mock_instance = MagicMock()
                mock_instance.load_cost_centers = MagicMock()
                mock_instance.get_hourly_rate = MagicMock(
                    return_value=(Decimal("100.00"), False)
                )
                mock_instance.get_cost_per_unit = MagicMock(
                    return_value=(Decimal("10.00"), False)
                )
                mock_instance.calculate_downtime_loss = MagicMock(
                    return_value=Decimal("50.00")
                )
                mock_instance.calculate_waste_loss = MagicMock(
                    return_value=Decimal("50.00")
                )
                mock_service.return_value = mock_instance

                response = client.get(
                    "/api/financial/summary",
                    headers={"Authorization": "Bearer test-token"},
                )

                assert response.status_code == 200
                data = response.json()
                assert "total_loss" in data
                assert "total_downtime_minutes" in data
                assert "asset_count" in data

                # Verify waste_count is properly extracted (not 0 from wrong key)
                # The code should call calculate_waste_loss with 5 and 10, not 0 and 0
                waste_calls = mock_instance.calculate_waste_loss.call_args_list
                waste_values = [c[0][0] for c in waste_calls]
                assert 5 in waste_values and 10 in waste_values, (
                    f"Expected calculate_waste_loss called with 5 and 10, "
                    f"but got values: {waste_values}. "
                    f"Code likely reads 'waste' key instead of 'waste_count'."
                )

    def test_int_006_cost_of_loss_calculates_breakdown_with_waste_count(
        self, client, mock_verify_jwt
    ):
        """
        10-3-cost-of-loss-schema-fix-INT-006:
        test_cost_of_loss_calculates_breakdown passes with waste_count mocks.

        Given: TestCostOfLossEndpoint with mock data using "waste_count" keys
        When: The test is executed
        Then: All cost-of-loss tests pass, breakdown.waste_cost correct
        """
        with patch("app.api.financial.get_supabase_client") as mock_supabase:
            with patch("app.api.financial.get_financial_service") as mock_service:
                mock_client = MagicMock()
                mock_supabase.return_value = mock_client

                # Updated mock data using waste_count (correct schema)
                mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                    {
                        "asset_id": "asset-1",
                        "downtime_minutes": 120,
                        "waste_count": 20,
                        "financial_loss": 800.00,
                        "oee_percentage": 80.0,
                        "created_at": "2026-01-05T06:00:00Z",
                    },
                ]

                mock_instance = MagicMock()
                mock_instance.load_cost_centers = MagicMock()
                mock_instance.get_hourly_rate = MagicMock(
                    return_value=(Decimal("150.00"), False)
                )
                mock_instance.get_cost_per_unit = MagicMock(
                    return_value=(Decimal("25.00"), False)
                )
                mock_instance.calculate_downtime_loss = MagicMock(
                    return_value=Decimal("300.00")
                )
                mock_instance.calculate_waste_loss = MagicMock(
                    return_value=Decimal("500.00")
                )
                mock_service.return_value = mock_instance

                response = client.get(
                    "/api/financial/cost-of-loss",
                    headers={"Authorization": "Bearer test-token"},
                )

                assert response.status_code == 200
                data = response.json()
                breakdown = data["breakdown"]

                assert "downtime_cost" in breakdown
                assert "waste_cost" in breakdown
                assert "oee_loss_cost" in breakdown

                # Verify waste was actually extracted (not 0 from wrong key)
                mock_instance.calculate_waste_loss.assert_called_once()
                waste_arg = mock_instance.calculate_waste_loss.call_args[0][0]
                assert waste_arg == 20, (
                    f"Expected calculate_waste_loss called with waste_count=20, "
                    f"got {waste_arg}. Code reads 'waste' key instead of 'waste_count'."
                )


# ---------------------------------------------------------------------------
# AC5: Agent Data Source Remains Correct
# ---------------------------------------------------------------------------


class TestAgentDataSourceCorrect:
    """AC5: Agent data source already uses waste_count and remains unchanged."""

    def test_unit_013_supabase_data_source_uses_waste_count(self):
        """
        10-3-cost-of-loss-schema-fix-UNIT-013:
        SupabaseDataSource.get_cost_of_loss() already uses waste_count.

        Given: The SupabaseDataSource.get_cost_of_loss() method
        When: The SELECT fields string is inspected
        Then: The select includes waste_count
        """
        import inspect
        from app.services.agent.data_source.supabase import SupabaseDataSource

        # Get the source code of the get_cost_of_loss method
        source = inspect.getsource(SupabaseDataSource.get_cost_of_loss)

        # Verify waste_count is used in the select
        assert "waste_count" in source, (
            "Expected 'waste_count' in SupabaseDataSource.get_cost_of_loss() source code"
        )

        # Also verify it's in a select context (not just a comment)
        import re

        select_pattern = r"select_fields.*?waste_count"
        assert re.search(select_pattern, source, re.DOTALL), (
            "Expected 'waste_count' in select_fields of SupabaseDataSource.get_cost_of_loss()"
        )
