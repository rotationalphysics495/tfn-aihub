"""
Integration Tests for Data Source Abstraction Layer (Story 5.2)

Tests the complete flow of data access through the abstraction layer.
"""

import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock, patch

from app.services.agent.data_source import (
    get_data_source,
    reset_data_source,
    DataResult,
    Asset,
    OEEMetrics,
    DowntimeEvent,
    ProductionStatus,
)
from app.services.agent.data_source.supabase import SupabaseDataSource
from app.services.agent.data_source.composite import CompositeDataSource


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client with common responses."""
    mock_client = MagicMock()
    return mock_client


@pytest.fixture
def mock_data_source(mock_supabase_client):
    """Create data source with mocked client."""
    return SupabaseDataSource(client=mock_supabase_client)


class TestEndToEndAssetFlow:
    """Integration tests for asset data flow."""

    @pytest.mark.asyncio
    async def test_asset_lookup_returns_citation_metadata(self, mock_data_source, mock_supabase_client):
        """AC#3: DataResult metadata available for citation generation."""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "asset-uuid",
                "name": "Grinder 5",
                "source_id": "LOC-GRN-005",
                "area": "Grinding",
            }]
        )

        result = await mock_data_source.get_asset("asset-uuid")

        # Verify citation metadata
        metadata = result.to_citation_metadata()
        assert metadata["source"] == "supabase"
        assert metadata["table"] == "assets"
        assert "query" in metadata

        # Verify data parsing
        assert isinstance(result.data, Asset)
        assert result.data.name == "Grinder 5"

    @pytest.mark.asyncio
    async def test_fuzzy_asset_search_workflow(self, mock_data_source, mock_supabase_client):
        """AC#4: Fuzzy name matching for user queries."""
        # User types "grinder" - expect fuzzy match to find "Grinder 5"
        mock_supabase_client.table.return_value.select.return_value.ilike.return_value.limit.return_value.execute.side_effect = [
            MagicMock(data=[]),  # No exact match for "grinder"
            MagicMock(data=[{    # Partial match finds "Grinder 5"
                "id": "asset-uuid",
                "name": "Grinder 5",
                "source_id": "LOC-GRN-005",
                "area": "Grinding",
            }]),
        ]

        result = await mock_data_source.get_asset_by_name("grinder")

        assert result.has_data
        assert result.data.name == "Grinder 5"

    @pytest.mark.asyncio
    async def test_similar_assets_for_suggestions(self, mock_data_source, mock_supabase_client):
        """AC#4: Get similar assets when exact match fails."""
        mock_supabase_client.table.return_value.select.return_value.ilike.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[
                {"id": "1", "name": "Grinder 1", "source_id": "G1", "area": "Grinding"},
                {"id": "2", "name": "Grinder 2", "source_id": "G2", "area": "Grinding"},
                {"id": "5", "name": "Grinder 5", "source_id": "G5", "area": "Grinding"},
            ]
        )

        result = await mock_data_source.get_similar_assets("grind", limit=5)

        assert result.row_count == 3
        names = [a.name for a in result.data]
        assert "Grinder 1" in names
        assert "Grinder 5" in names


class TestEndToEndOEEFlow:
    """Integration tests for OEE data flow."""

    @pytest.mark.asyncio
    async def test_oee_query_with_breakdown(self, mock_data_source, mock_supabase_client):
        """AC#5: OEE includes availability, performance, quality breakdown."""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.order.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "oee-1",
                "asset_id": "asset-uuid",
                "report_date": "2026-01-08",
                "oee_percentage": 87.5,
                "actual_output": 950,
                "target_output": 1000,
                "downtime_minutes": 45,
                "waste_count": 5,
                "financial_loss_dollars": 1500.00,
            }]
        )

        result = await mock_data_source.get_oee(
            asset_id="asset-uuid",
            start_date=date(2026, 1, 8),
            end_date=date(2026, 1, 8),
        )

        # Verify OEE data
        assert result.row_count == 1
        oee = result.data[0]
        assert isinstance(oee, OEEMetrics)
        assert oee.oee_percentage == Decimal("87.5")
        assert oee.actual_output == 950
        assert oee.target_output == 1000

        # Verify citation metadata
        metadata = result.to_citation_metadata()
        assert metadata["table"] == "daily_summaries"


class TestEndToEndDowntimeFlow:
    """Integration tests for downtime data flow."""

    @pytest.mark.asyncio
    async def test_downtime_with_pareto_data(self, mock_data_source, mock_supabase_client):
        """AC#6: Downtime records with reasons and durations for Pareto analysis."""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.gt.return_value.order.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "id": "dt-1",
                    "asset_id": "asset-uuid",
                    "report_date": "2026-01-08",
                    "downtime_minutes": 120,
                    "financial_loss_dollars": 2500.00,
                },
                {
                    "id": "dt-2",
                    "asset_id": "asset-uuid",
                    "report_date": "2026-01-07",
                    "downtime_minutes": 60,
                    "financial_loss_dollars": 1250.00,
                },
            ]
        )

        result = await mock_data_source.get_downtime(
            asset_id="asset-uuid",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 8),
        )

        # Verify downtime data for Pareto analysis
        assert result.row_count == 2
        total_downtime = sum(d.downtime_minutes for d in result.data)
        assert total_downtime == 180

        # Can sort by duration for Pareto
        sorted_events = sorted(result.data, key=lambda x: x.downtime_minutes, reverse=True)
        assert sorted_events[0].downtime_minutes == 120


class TestEndToEndLiveDataFlow:
    """Integration tests for live data flow."""

    @pytest.mark.asyncio
    async def test_live_snapshot_with_freshness(self, mock_data_source, mock_supabase_client):
        """AC#7: Live snapshot includes data freshness timestamp."""
        snapshot_time = "2026-01-09T10:30:00Z"
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "snap-1",
                "asset_id": "asset-uuid",
                "snapshot_timestamp": snapshot_time,
                "current_output": 450,
                "target_output": 500,
                "output_variance": -50,
                "status": "behind",
                "assets": {"name": "Grinder 5", "area": "Grinding"},
            }]
        )

        result = await mock_data_source.get_live_snapshot("asset-uuid")

        # Verify live data with freshness
        assert result.has_data
        status = result.data
        assert isinstance(status, ProductionStatus)
        assert status.current_output == 450
        assert status.status == "behind"
        assert status.snapshot_timestamp is not None

        # Check data freshness is available
        assert result.query_timestamp is not None


class TestToolDecoupling:
    """Tests verifying tools don't need to know database implementation."""

    @pytest.mark.asyncio
    async def test_tool_uses_abstract_interface(self, mock_data_source, mock_supabase_client):
        """AC#4: Tool does not need to know which database was queried."""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "asset-uuid",
                "name": "Grinder 5",
                "source_id": "LOC-GRN-005",
                "area": "Grinding",
            }]
        )

        # Simulate tool usage - tool only knows about DataResult
        async def mock_tool_implementation(data_source, asset_id: str):
            """Mock tool that uses data source abstraction."""
            result = await data_source.get_asset(asset_id)

            # Tool only works with DataResult and domain models
            if result.has_data:
                return {
                    "asset_name": result.data.name,
                    "citation_source": result.to_citation_metadata()["source"],
                }
            return None

        # Tool works without knowing about Supabase
        tool_result = await mock_tool_implementation(mock_data_source, "asset-uuid")

        assert tool_result["asset_name"] == "Grinder 5"
        assert tool_result["citation_source"] == "supabase"


class TestCompositeDataSourceIntegration:
    """Integration tests for CompositeDataSource."""

    @pytest.mark.asyncio
    async def test_composite_delegates_correctly(self, mock_supabase_client):
        """AC#8: CompositeDataSource routes to appropriate source."""
        mock_primary = SupabaseDataSource(client=mock_supabase_client)

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "asset-uuid",
                "name": "Grinder 5",
                "source_id": "LOC-GRN-005",
                "area": "Grinding",
            }]
        )

        composite = CompositeDataSource(primary=mock_primary)

        result = await composite.get_asset("asset-uuid")

        assert result.has_data
        assert result.data.name == "Grinder 5"


class TestCitationGeneration:
    """Tests for citation metadata generation."""

    @pytest.mark.asyncio
    async def test_data_result_provides_citation_info(self, mock_data_source, mock_supabase_client):
        """AC#3: Metadata available for citation generation."""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.gte.return_value.lte.return_value.order.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "oee-1",
                "asset_id": "asset-uuid",
                "report_date": "2026-01-08",
                "oee_percentage": 87.5,
                "actual_output": 950,
                "target_output": 1000,
            }]
        )

        result = await mock_data_source.get_oee(
            asset_id="asset-uuid",
            start_date=date(2026, 1, 8),
            end_date=date(2026, 1, 8),
        )

        # Citation metadata for tools to use
        citation_meta = result.to_citation_metadata()

        assert citation_meta["source"] == "supabase"
        assert citation_meta["table"] == "daily_summaries"
        assert "query" in citation_meta

        # Query timestamp for freshness
        assert result.query_timestamp is not None
