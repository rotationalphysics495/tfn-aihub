"""
Tests for Financial Impact API Endpoints.

Story: 2.7 - Financial Impact Calculator
AC: #5 - API Endpoint for Financial Data
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock, AsyncMock


class TestFinancialImpactEndpoint:
    """Tests for GET /api/financial/impact/{asset_id} (AC #5)."""

    def test_financial_impact_requires_auth(self, client):
        """Financial impact endpoint requires authentication."""
        response = client.get("/api/financial/impact/test-asset-id")
        assert response.status_code == 401

    def test_financial_impact_returns_correct_structure(self, client, mock_verify_jwt):
        """AC#5: Response includes required fields."""
        with patch('app.api.financial.get_financial_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_financial_impact = AsyncMock(return_value=MagicMock(
                asset_id="test-asset-id",
                asset_name="Test Asset",
                period_start=date.today() - timedelta(days=1),
                period_end=date.today() - timedelta(days=1),
                downtime_minutes=45,
                downtime_loss=112.50,
                waste_count=10,
                waste_loss=250.00,
                total_loss=362.50,
                currency="USD",
                standard_hourly_rate=150.00,
                cost_per_unit=25.00,
                is_estimated=False,
            ))
            mock_service.return_value = mock_instance

            response = client.get(
                "/api/financial/impact/test-asset-id",
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()

            # AC#5: Check required fields
            assert "downtime_loss" in data
            assert "waste_loss" in data
            assert "total_loss" in data
            assert "currency" in data
            assert "standard_hourly_rate" in data
            assert data["asset_id"] == "test-asset-id"

    def test_financial_impact_with_date_range(self, client, mock_verify_jwt):
        """AC#5: Supports date parameters."""
        with patch('app.api.financial.get_financial_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_financial_impact = AsyncMock(return_value=MagicMock(
                asset_id="test-asset-id",
                asset_name="Test Asset",
                period_start=date(2026, 1, 1),
                period_end=date(2026, 1, 5),
                downtime_minutes=200,
                downtime_loss=500.00,
                waste_count=50,
                waste_loss=1250.00,
                total_loss=1750.00,
                currency="USD",
                standard_hourly_rate=150.00,
                cost_per_unit=25.00,
                is_estimated=False,
            ))
            mock_service.return_value = mock_instance

            response = client.get(
                "/api/financial/impact/test-asset-id",
                params={"start_date": "2026-01-01", "end_date": "2026-01-05"},
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["period_start"] == "2026-01-01"
            assert data["period_end"] == "2026-01-05"

    def test_financial_impact_date_validation(self, client, mock_verify_jwt):
        """AC#5: Validates end_date >= start_date."""
        response = client.get(
            "/api/financial/impact/test-asset-id",
            params={"start_date": "2026-01-10", "end_date": "2026-01-05"},
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 400
        assert "end_date must be >= start_date" in response.json()["detail"]


class TestLiveFinancialImpactEndpoint:
    """Tests for GET /api/financial/impact/{asset_id}/live."""

    def test_live_financial_impact_requires_auth(self, client):
        """Live financial impact endpoint requires authentication."""
        response = client.get("/api/financial/impact/test-asset-id/live")
        assert response.status_code == 401

    def test_live_financial_impact_returns_accumulated_values(self, client, mock_verify_jwt):
        """Returns accumulated financial impact for current shift."""
        with patch('app.api.financial.get_financial_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_live_financial_impact = AsyncMock(return_value=MagicMock(
                asset_id="test-asset-id",
                asset_name="Test Asset",
                shift_start="2026-01-06T06:00:00Z",
                accumulated_downtime_minutes=30,
                accumulated_downtime_loss=75.00,
                accumulated_waste_count=5,
                accumulated_waste_loss=125.00,
                accumulated_total_loss=200.00,
                currency="USD",
                is_estimated=False,
            ))
            mock_service.return_value = mock_instance

            response = client.get(
                "/api/financial/impact/test-asset-id/live",
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "accumulated_total_loss" in data
            assert data["accumulated_total_loss"] == 200.00


class TestFinancialSummaryEndpoint:
    """Tests for GET /api/financial/summary."""

    def test_financial_summary_requires_auth(self, client):
        """Financial summary endpoint requires authentication."""
        response = client.get("/api/financial/summary")
        assert response.status_code == 401

    def test_financial_summary_aggregates_data(self, client, mock_verify_jwt):
        """Returns aggregated financial impact across assets."""
        with patch('app.api.financial.get_supabase_client') as mock_supabase:
            with patch('app.api.financial.get_financial_service') as mock_service:
                mock_client = MagicMock()
                mock_supabase.return_value = mock_client

                # Mock daily_summaries response
                mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                    {"asset_id": "asset-1", "downtime_minutes": 30, "waste": 5, "financial_loss": 200.00},
                    {"asset_id": "asset-2", "downtime_minutes": 45, "waste": 10, "financial_loss": 350.00},
                ]

                mock_instance = MagicMock()
                mock_instance.load_cost_centers = MagicMock()
                mock_instance.get_hourly_rate = MagicMock(return_value=(Decimal("100.00"), False))
                mock_instance.get_cost_per_unit = MagicMock(return_value=(Decimal("10.00"), False))
                mock_instance.calculate_downtime_loss = MagicMock(return_value=Decimal("50.00"))
                mock_instance.calculate_waste_loss = MagicMock(return_value=(Decimal("50.00")))
                mock_service.return_value = mock_instance

                response = client.get(
                    "/api/financial/summary",
                    headers={"Authorization": "Bearer test-token"}
                )

                assert response.status_code == 200
                data = response.json()
                assert "total_loss" in data
                assert "total_downtime_minutes" in data
                assert "asset_count" in data


class TestAssetFinancialContextEndpoint:
    """Tests for GET /api/financial/context/{asset_id}."""

    def test_financial_context_requires_auth(self, client):
        """Financial context endpoint requires authentication."""
        response = client.get("/api/financial/context/test-asset-id")
        assert response.status_code == 401

    def test_financial_context_returns_rates(self, client, mock_verify_jwt):
        """Returns financial rates for an asset."""
        with patch('app.api.financial.get_financial_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.load_cost_centers = MagicMock()
            mock_instance.load_assets = MagicMock()
            mock_instance._asset_cache = {"test-asset-id": {"name": "Test Asset"}}
            mock_instance.get_hourly_rate = MagicMock(return_value=(Decimal("150.00"), False))
            mock_instance.get_cost_per_unit = MagicMock(return_value=(Decimal("25.00"), False))
            mock_service.return_value = mock_instance

            response = client.get(
                "/api/financial/context/test-asset-id",
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["asset_id"] == "test-asset-id"
            assert "standard_hourly_rate" in data
            assert "cost_per_unit" in data
            assert "is_estimated" in data

    def test_financial_context_indicates_estimated_rates(self, client, mock_verify_jwt):
        """AC#8: Response indicates when default rates are used."""
        with patch('app.api.financial.get_financial_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.load_cost_centers = MagicMock()
            mock_instance.load_assets = MagicMock()
            mock_instance._asset_cache = {"test-asset-id": {"name": "Test Asset"}}
            # Return True for is_estimated
            mock_instance.get_hourly_rate = MagicMock(return_value=(Decimal("100.00"), True))
            mock_instance.get_cost_per_unit = MagicMock(return_value=(Decimal("10.00"), True))
            mock_service.return_value = mock_instance

            response = client.get(
                "/api/financial/context/test-asset-id",
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["is_estimated"] is True


class TestFinancialAPIErrorHandling:
    """Tests for error handling in financial API."""

    def test_handles_service_error(self, client, mock_verify_jwt):
        """Returns 500 on service error."""
        with patch('app.api.financial.get_financial_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_financial_impact = AsyncMock(
                side_effect=Exception("Database connection failed")
            )
            mock_service.return_value = mock_instance

            response = client.get(
                "/api/financial/impact/test-asset-id",
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 500

    def test_handles_missing_supabase_config(self, client, mock_verify_jwt):
        """Returns 503 when Supabase not configured."""
        with patch('app.api.financial.get_supabase_client') as mock_supabase:
            from fastapi import HTTPException, status
            mock_supabase.side_effect = HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase not configured"
            )

            response = client.get(
                "/api/financial/summary",
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 503
