"""
Tests for Financial Impact Calculator Service.

Story: 2.7 - Financial Impact Calculator
AC: #1 - Financial Impact Service Exists
AC: #2 - Downtime Financial Calculation
AC: #3 - Waste/Scrap Financial Calculation
AC: #4 - Combined Financial Impact
AC: #8 - Error Handling for Missing Cost Data
"""

import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.financial import (
    FinancialService,
    get_financial_service,
    FinancialServiceError,
)
from app.schemas.financial import FinancialImpactBreakdown


@pytest.fixture
def financial_service():
    """Create a fresh financial service instance."""
    service = FinancialService()
    service.clear_cache()
    return service


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    mock = MagicMock()
    return mock


class TestDowntimeLossCalculation:
    """Tests for downtime financial calculation (AC #2)."""

    def test_calculate_downtime_loss_basic(self, financial_service):
        """AC#2: financial_loss = (downtime_minutes / 60) * standard_hourly_rate."""
        hourly_rate = Decimal("150.00")
        downtime_minutes = 45

        loss = financial_service.calculate_downtime_loss(downtime_minutes, hourly_rate)

        # (45/60) * 150 = 0.75 * 150 = 112.50
        expected = Decimal("112.50")
        assert loss == expected

    def test_calculate_downtime_loss_full_hour(self, financial_service):
        """AC#2: One hour of downtime equals hourly rate."""
        hourly_rate = Decimal("200.00")
        downtime_minutes = 60

        loss = financial_service.calculate_downtime_loss(downtime_minutes, hourly_rate)

        assert loss == Decimal("200.00")

    def test_calculate_downtime_loss_zero_minutes(self, financial_service):
        """AC#2: Zero downtime = zero loss."""
        hourly_rate = Decimal("150.00")
        downtime_minutes = 0

        loss = financial_service.calculate_downtime_loss(downtime_minutes, hourly_rate)

        assert loss == Decimal("0.00")

    def test_calculate_downtime_loss_zero_rate(self, financial_service):
        """AC#2: Zero rate = zero loss."""
        hourly_rate = Decimal("0")
        downtime_minutes = 60

        loss = financial_service.calculate_downtime_loss(downtime_minutes, hourly_rate)

        assert loss == Decimal("0.00")

    def test_calculate_downtime_loss_precision(self, financial_service):
        """AC#2: Result has 2 decimal places for currency."""
        hourly_rate = Decimal("100.00")
        downtime_minutes = 7  # 7/60 = 0.11666... hours

        loss = financial_service.calculate_downtime_loss(downtime_minutes, hourly_rate)

        # Should be rounded to 2 decimal places
        assert loss == Decimal("11.67")


class TestWasteLossCalculation:
    """Tests for waste financial calculation (AC #3)."""

    def test_calculate_waste_loss_basic(self, financial_service):
        """AC#3: waste_loss = waste_count * cost_per_unit."""
        cost_per_unit = Decimal("25.00")
        waste_count = 10

        loss = financial_service.calculate_waste_loss(waste_count, cost_per_unit)

        expected = Decimal("250.00")
        assert loss == expected

    def test_calculate_waste_loss_zero_count(self, financial_service):
        """AC#3: Zero waste = zero loss."""
        cost_per_unit = Decimal("25.00")
        waste_count = 0

        loss = financial_service.calculate_waste_loss(waste_count, cost_per_unit)

        assert loss == Decimal("0.00")

    def test_calculate_waste_loss_zero_cost(self, financial_service):
        """AC#3: Zero cost = zero loss."""
        cost_per_unit = Decimal("0")
        waste_count = 100

        loss = financial_service.calculate_waste_loss(waste_count, cost_per_unit)

        assert loss == Decimal("0.00")

    def test_calculate_waste_loss_precision(self, financial_service):
        """AC#3: Result has 2 decimal places for currency."""
        cost_per_unit = Decimal("3.33")
        waste_count = 7

        loss = financial_service.calculate_waste_loss(waste_count, cost_per_unit)

        # 7 * 3.33 = 23.31
        assert loss == Decimal("23.31")


class TestTotalImpactCalculation:
    """Tests for combined financial impact (AC #4)."""

    def test_calculate_total_impact_combined(self, financial_service):
        """AC#4: total_loss = downtime_loss + waste_loss."""
        # Mock cost center lookup to return known values
        with patch.object(financial_service, 'get_hourly_rate') as mock_rate:
            with patch.object(financial_service, 'get_cost_per_unit') as mock_cost:
                mock_rate.return_value = (Decimal("150.00"), False)
                mock_cost.return_value = (Decimal("25.00"), False)

                breakdown = financial_service.calculate_total_impact(
                    asset_id="test-asset-id",
                    downtime_minutes=45,
                    waste_count=10
                )

                # Downtime: (45/60) * 150 = 112.50
                # Waste: 10 * 25 = 250.00
                # Total: 362.50
                assert breakdown.downtime_loss == 112.50
                assert breakdown.waste_loss == 250.00
                assert breakdown.total_loss == 362.50

    def test_calculate_total_impact_only_downtime(self, financial_service):
        """AC#4: Total with only downtime."""
        with patch.object(financial_service, 'get_hourly_rate') as mock_rate:
            with patch.object(financial_service, 'get_cost_per_unit') as mock_cost:
                mock_rate.return_value = (Decimal("100.00"), False)
                mock_cost.return_value = (Decimal("10.00"), False)

                breakdown = financial_service.calculate_total_impact(
                    asset_id="test-asset-id",
                    downtime_minutes=30,
                    waste_count=0
                )

                # Downtime: (30/60) * 100 = 50.00
                # Waste: 0 * 10 = 0
                # Total: 50.00
                assert breakdown.downtime_loss == 50.00
                assert breakdown.waste_loss == 0.00
                assert breakdown.total_loss == 50.00

    def test_calculate_total_impact_only_waste(self, financial_service):
        """AC#4: Total with only waste."""
        with patch.object(financial_service, 'get_hourly_rate') as mock_rate:
            with patch.object(financial_service, 'get_cost_per_unit') as mock_cost:
                mock_rate.return_value = (Decimal("100.00"), False)
                mock_cost.return_value = (Decimal("15.00"), False)

                breakdown = financial_service.calculate_total_impact(
                    asset_id="test-asset-id",
                    downtime_minutes=0,
                    waste_count=20
                )

                # Downtime: 0
                # Waste: 20 * 15 = 300.00
                # Total: 300.00
                assert breakdown.downtime_loss == 0.00
                assert breakdown.waste_loss == 300.00
                assert breakdown.total_loss == 300.00

    def test_calculate_total_impact_zero_values(self, financial_service):
        """AC#4: Both zero = zero total."""
        with patch.object(financial_service, 'get_hourly_rate') as mock_rate:
            with patch.object(financial_service, 'get_cost_per_unit') as mock_cost:
                mock_rate.return_value = (Decimal("100.00"), False)
                mock_cost.return_value = (Decimal("10.00"), False)

                breakdown = financial_service.calculate_total_impact(
                    asset_id="test-asset-id",
                    downtime_minutes=0,
                    waste_count=0
                )

                assert breakdown.total_loss == 0.00

    def test_calculate_total_impact_breakdown_structure(self, financial_service):
        """AC#4: Breakdown includes all components."""
        with patch.object(financial_service, 'get_hourly_rate') as mock_rate:
            with patch.object(financial_service, 'get_cost_per_unit') as mock_cost:
                mock_rate.return_value = (Decimal("100.00"), False)
                mock_cost.return_value = (Decimal("10.00"), False)

                breakdown = financial_service.calculate_total_impact(
                    asset_id="test-asset-id",
                    downtime_minutes=60,
                    waste_count=5
                )

                assert breakdown.downtime_minutes == 60
                assert breakdown.downtime_hours == 1.0
                assert breakdown.hourly_rate == 100.00
                assert breakdown.waste_count == 5
                assert breakdown.cost_per_unit == 10.00


class TestDefaultRateFallback:
    """Tests for default rate fallback (AC #8)."""

    def test_get_hourly_rate_uses_default_when_missing(self, financial_service):
        """AC#8: Uses DEFAULT_HOURLY_RATE when cost_centers entry missing."""
        # Empty cache = no cost center data
        financial_service._cost_center_cache = {}

        with patch('app.services.financial.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                default_hourly_rate=100.00,
                default_cost_per_unit=10.00
            )
            financial_service.load_cost_centers = MagicMock(return_value={})

            rate, is_estimated = financial_service.get_hourly_rate("unknown-asset-id")

            assert rate == Decimal("100.00")
            assert is_estimated is True

    def test_get_cost_per_unit_uses_default_when_missing(self, financial_service):
        """AC#8: Uses DEFAULT_COST_PER_UNIT when cost_centers entry missing."""
        financial_service._cost_center_cache = {}

        with patch('app.services.financial.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                default_hourly_rate=100.00,
                default_cost_per_unit=10.00
            )
            financial_service.load_cost_centers = MagicMock(return_value={})

            cost, is_estimated = financial_service.get_cost_per_unit("unknown-asset-id")

            assert cost == Decimal("10.00")
            assert is_estimated is True

    def test_get_hourly_rate_from_cost_center(self, financial_service):
        """AC#8: Uses cost_centers value when available."""
        asset_id = "test-asset-123"
        financial_service._cost_center_cache = {
            asset_id: {
                "hourly_rate": Decimal("250.00"),
                "cost_per_unit": Decimal("50.00"),
            }
        }

        with patch('app.services.financial.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                default_hourly_rate=100.00,
                default_cost_per_unit=10.00
            )

            rate, is_estimated = financial_service.get_hourly_rate(asset_id)

            assert rate == Decimal("250.00")
            assert is_estimated is False


class TestCostCenterLoading:
    """Tests for cost center data loading."""

    def test_load_cost_centers_success(self, financial_service, mock_supabase_client):
        """Load cost centers from Supabase."""
        mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = [
            {
                "id": "cc-1",
                "asset_id": "asset-1",
                "standard_hourly_rate": 150.00,
                "cost_per_unit": 25.00,
            },
            {
                "id": "cc-2",
                "asset_id": "asset-2",
                "standard_hourly_rate": 200.00,
                "cost_per_unit": 30.00,
            },
        ]
        financial_service._supabase_client = mock_supabase_client

        result = financial_service.load_cost_centers()

        assert len(result) == 2
        assert "asset-1" in result
        assert result["asset-1"]["hourly_rate"] == Decimal("150.00")
        assert result["asset-2"]["cost_per_unit"] == Decimal("30.00")

    def test_cache_is_used(self, financial_service):
        """Cached data is used on subsequent calls."""
        financial_service._cost_center_cache = {"cached": {"hourly_rate": Decimal("100")}}
        financial_service._cache_timestamp = __import__('datetime').datetime.utcnow()

        # Patch _get_supabase_client to raise if called (shouldn't be called)
        with patch.object(financial_service, '_get_supabase_client') as mock_client:
            result = financial_service.load_cost_centers()

            # Should return cache without calling Supabase
            assert "cached" in result

    def test_clear_cache(self, financial_service):
        """Clear cache removes all cached data."""
        financial_service._cost_center_cache = {"test": {}}
        financial_service._asset_cache = {"test": {}}
        financial_service._cache_timestamp = __import__('datetime').datetime.utcnow()

        financial_service.clear_cache()

        assert len(financial_service._cost_center_cache) == 0
        assert len(financial_service._asset_cache) == 0
        assert financial_service._cache_timestamp is None


class TestFinancialServiceSingleton:
    """Tests for singleton pattern."""

    def test_get_financial_service_returns_same_instance(self):
        """get_financial_service returns singleton."""
        # Reset the singleton for testing
        import app.services.financial as fin_module
        fin_module._financial_service = None

        service1 = get_financial_service()
        service2 = get_financial_service()

        assert service1 is service2


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_large_numbers(self, financial_service):
        """Handle very large downtime and waste values."""
        hourly_rate = Decimal("1000.00")
        downtime_minutes = 10000  # ~166 hours

        loss = financial_service.calculate_downtime_loss(downtime_minutes, hourly_rate)

        # (10000/60) * 1000 = 166666.67
        assert loss == Decimal("166666.67")

    def test_decimal_precision_maintained(self, financial_service):
        """Decimal precision is maintained throughout calculations."""
        hourly_rate = Decimal("333.33")
        downtime_minutes = 17

        loss = financial_service.calculate_downtime_loss(downtime_minutes, hourly_rate)

        # (17/60) * 333.33 = 94.44
        assert isinstance(loss, Decimal)
        # Check 2 decimal places
        str_loss = str(loss)
        if "." in str_loss:
            decimals = len(str_loss.split(".")[1])
            assert decimals <= 2

    def test_negative_values_handled(self, financial_service):
        """Negative values result in zero loss."""
        hourly_rate = Decimal("100.00")

        # Negative downtime
        loss = financial_service.calculate_downtime_loss(-10, hourly_rate)
        assert loss == Decimal("0.00")

        # Negative waste
        loss = financial_service.calculate_waste_loss(-5, Decimal("10.00"))
        assert loss == Decimal("0.00")


class TestCalculateForPipelines:
    """Tests for pipeline integration methods."""

    def test_calculate_for_daily_summary(self, financial_service):
        """Calculate financial loss for daily summary (Pipeline A)."""
        with patch.object(financial_service, 'get_hourly_rate') as mock_rate:
            with patch.object(financial_service, 'get_cost_per_unit') as mock_cost:
                mock_rate.return_value = (Decimal("100.00"), False)
                mock_cost.return_value = (Decimal("10.00"), False)

                loss, is_estimated = financial_service.calculate_for_daily_summary(
                    asset_id="test-asset",
                    downtime_minutes=60,
                    waste_count=10
                )

                # Downtime: 1h * 100 = 100
                # Waste: 10 * 10 = 100
                # Total: 200
                assert loss == Decimal("200.00")
                assert is_estimated is False

    def test_calculate_for_live_snapshot(self, financial_service):
        """Calculate financial loss for live snapshot (Pipeline B)."""
        with patch.object(financial_service, 'get_hourly_rate') as mock_rate:
            with patch.object(financial_service, 'get_cost_per_unit') as mock_cost:
                mock_rate.return_value = (Decimal("150.00"), True)  # Using default
                mock_cost.return_value = (Decimal("20.00"), False)

                loss, is_estimated = financial_service.calculate_for_live_snapshot(
                    asset_id="test-asset",
                    downtime_minutes=30,
                    waste_count=5
                )

                # Downtime: 0.5h * 150 = 75
                # Waste: 5 * 20 = 100
                # Total: 175
                assert loss == Decimal("175.00")
                assert is_estimated is True  # Because hourly rate was estimated
