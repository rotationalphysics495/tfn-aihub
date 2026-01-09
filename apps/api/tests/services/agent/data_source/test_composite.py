"""
Tests for CompositeDataSource (Story 5.2)

AC#8: CompositeDataSource Router (Future-Ready)
"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock

from app.services.agent.data_source.composite import CompositeDataSource
from app.services.agent.data_source.protocol import DataResult, Asset


@pytest.fixture
def mock_primary_source():
    """Create a mock primary data source."""
    mock = MagicMock()
    mock.source_name = "supabase"
    return mock


@pytest.fixture
def composite_source(mock_primary_source):
    """Create CompositeDataSource with mock primary."""
    return CompositeDataSource(primary=mock_primary_source)


class TestCompositeDataSourceInit:
    """Tests for CompositeDataSource initialization."""

    def test_source_name(self, composite_source):
        """Source name is 'composite'."""
        assert composite_source.source_name == "composite"

    def test_primary_source_assignment(self, composite_source, mock_primary_source):
        """Primary source is properly assigned."""
        assert composite_source.primary is mock_primary_source

    def test_default_primary_is_supabase(self):
        """Default primary is SupabaseDataSource when none provided."""
        from app.services.agent.data_source.supabase import SupabaseDataSource

        # CompositeDataSource creates SupabaseDataSource as default primary
        composite = CompositeDataSource()

        assert isinstance(composite.primary, SupabaseDataSource)


class TestAssetMethodsDelegation:
    """Tests for asset methods delegation to primary."""

    @pytest.mark.asyncio
    async def test_get_asset_delegates_to_primary(self, composite_source, mock_primary_source):
        """AC#8: get_asset delegates to primary source."""
        expected_result = DataResult(
            data=Asset(id="123", name="Test", source_id="T1"),
            source_name="supabase",
            table_name="assets",
        )
        mock_primary_source.get_asset = AsyncMock(return_value=expected_result)

        result = await composite_source.get_asset("123")

        mock_primary_source.get_asset.assert_called_once_with("123")
        assert result is expected_result

    @pytest.mark.asyncio
    async def test_get_asset_by_name_delegates_to_primary(self, composite_source, mock_primary_source):
        """AC#8: get_asset_by_name delegates to primary source."""
        expected_result = DataResult(
            data=Asset(id="123", name="Grinder 5", source_id="G5"),
            source_name="supabase",
            table_name="assets",
        )
        mock_primary_source.get_asset_by_name = AsyncMock(return_value=expected_result)

        result = await composite_source.get_asset_by_name("Grinder 5")

        mock_primary_source.get_asset_by_name.assert_called_once_with("Grinder 5")
        assert result is expected_result

    @pytest.mark.asyncio
    async def test_get_assets_by_area_delegates_to_primary(self, composite_source, mock_primary_source):
        """AC#8: get_assets_by_area delegates to primary source."""
        expected_result = DataResult(
            data=[],
            source_name="supabase",
            table_name="assets",
        )
        mock_primary_source.get_assets_by_area = AsyncMock(return_value=expected_result)

        result = await composite_source.get_assets_by_area("Grinding")

        mock_primary_source.get_assets_by_area.assert_called_once_with("Grinding")

    @pytest.mark.asyncio
    async def test_get_similar_assets_delegates_to_primary(self, composite_source, mock_primary_source):
        """AC#8: get_similar_assets delegates to primary source."""
        expected_result = DataResult(
            data=[],
            source_name="supabase",
            table_name="assets",
        )
        mock_primary_source.get_similar_assets = AsyncMock(return_value=expected_result)

        result = await composite_source.get_similar_assets("grind", limit=5)

        mock_primary_source.get_similar_assets.assert_called_once_with("grind", 5)

    @pytest.mark.asyncio
    async def test_get_all_assets_delegates_to_primary(self, composite_source, mock_primary_source):
        """AC#8: get_all_assets delegates to primary source."""
        expected_result = DataResult(
            data=[],
            source_name="supabase",
            table_name="assets",
        )
        mock_primary_source.get_all_assets = AsyncMock(return_value=expected_result)

        result = await composite_source.get_all_assets()

        mock_primary_source.get_all_assets.assert_called_once()


class TestOEEMethodsDelegation:
    """Tests for OEE methods delegation to primary."""

    @pytest.mark.asyncio
    async def test_get_oee_delegates_to_primary(self, composite_source, mock_primary_source):
        """AC#8: get_oee delegates to primary source."""
        expected_result = DataResult(
            data=[],
            source_name="supabase",
            table_name="daily_summaries",
        )
        mock_primary_source.get_oee = AsyncMock(return_value=expected_result)

        start = date(2026, 1, 1)
        end = date(2026, 1, 8)

        result = await composite_source.get_oee("123", start, end)

        mock_primary_source.get_oee.assert_called_once_with("123", start, end)

    @pytest.mark.asyncio
    async def test_get_oee_by_area_delegates_to_primary(self, composite_source, mock_primary_source):
        """AC#8: get_oee_by_area delegates to primary source."""
        expected_result = DataResult(
            data=[],
            source_name="supabase",
            table_name="daily_summaries",
        )
        mock_primary_source.get_oee_by_area = AsyncMock(return_value=expected_result)

        start = date(2026, 1, 1)
        end = date(2026, 1, 8)

        result = await composite_source.get_oee_by_area("Grinding", start, end)

        mock_primary_source.get_oee_by_area.assert_called_once_with("Grinding", start, end)


class TestDowntimeMethodsDelegation:
    """Tests for downtime methods delegation to primary."""

    @pytest.mark.asyncio
    async def test_get_downtime_delegates_to_primary(self, composite_source, mock_primary_source):
        """AC#8: get_downtime delegates to primary source."""
        expected_result = DataResult(
            data=[],
            source_name="supabase",
            table_name="daily_summaries",
        )
        mock_primary_source.get_downtime = AsyncMock(return_value=expected_result)

        start = date(2026, 1, 1)
        end = date(2026, 1, 8)

        result = await composite_source.get_downtime("123", start, end)

        mock_primary_source.get_downtime.assert_called_once_with("123", start, end)

    @pytest.mark.asyncio
    async def test_get_downtime_by_area_delegates_to_primary(self, composite_source, mock_primary_source):
        """AC#8: get_downtime_by_area delegates to primary source."""
        expected_result = DataResult(
            data=[],
            source_name="supabase",
            table_name="daily_summaries",
        )
        mock_primary_source.get_downtime_by_area = AsyncMock(return_value=expected_result)

        start = date(2026, 1, 1)
        end = date(2026, 1, 8)

        result = await composite_source.get_downtime_by_area("Grinding", start, end)

        mock_primary_source.get_downtime_by_area.assert_called_once_with("Grinding", start, end)


class TestLiveDataMethodsDelegation:
    """Tests for live data methods delegation to primary."""

    @pytest.mark.asyncio
    async def test_get_live_snapshot_delegates_to_primary(self, composite_source, mock_primary_source):
        """AC#8: get_live_snapshot currently delegates to primary."""
        expected_result = DataResult(
            data=None,
            source_name="supabase",
            table_name="live_snapshots",
        )
        mock_primary_source.get_live_snapshot = AsyncMock(return_value=expected_result)

        result = await composite_source.get_live_snapshot("123")

        mock_primary_source.get_live_snapshot.assert_called_once_with("123")

    @pytest.mark.asyncio
    async def test_get_live_snapshots_by_area_delegates_to_primary(self, composite_source, mock_primary_source):
        """AC#8: get_live_snapshots_by_area currently delegates to primary."""
        expected_result = DataResult(
            data=[],
            source_name="supabase",
            table_name="live_snapshots",
        )
        mock_primary_source.get_live_snapshots_by_area = AsyncMock(return_value=expected_result)

        result = await composite_source.get_live_snapshots_by_area("Grinding")

        mock_primary_source.get_live_snapshots_by_area.assert_called_once_with("Grinding")


class TestShiftTargetMethodsDelegation:
    """Tests for shift target methods delegation to primary."""

    @pytest.mark.asyncio
    async def test_get_shift_target_delegates_to_primary(self, composite_source, mock_primary_source):
        """AC#8: get_shift_target delegates to primary source."""
        expected_result = DataResult(
            data=None,
            source_name="supabase",
            table_name="shift_targets",
        )
        mock_primary_source.get_shift_target = AsyncMock(return_value=expected_result)

        result = await composite_source.get_shift_target("123")

        mock_primary_source.get_shift_target.assert_called_once_with("123")


class TestSafetyEventMethodsDelegation:
    """Tests for safety event methods delegation to primary."""

    @pytest.mark.asyncio
    async def test_get_safety_events_delegates_to_primary(self, composite_source, mock_primary_source):
        """AC#8: get_safety_events delegates to primary source."""
        expected_result = DataResult(
            data=[],
            source_name="supabase",
            table_name="safety_events",
        )
        mock_primary_source.get_safety_events = AsyncMock(return_value=expected_result)

        start = date(2026, 1, 1)
        end = date(2026, 1, 8)

        result = await composite_source.get_safety_events("123", start, end, include_resolved=True)

        mock_primary_source.get_safety_events.assert_called_once_with("123", start, end, True)


class TestFactoryFunction:
    """Tests for get_data_source() factory function (AC#9)."""

    def setup_method(self):
        """Reset singleton before each test."""
        from app.services.agent.data_source import reset_data_source
        reset_data_source()

    def teardown_method(self):
        """Clean up after each test."""
        from app.services.agent.data_source import reset_data_source
        reset_data_source()

    def test_factory_returns_supabase_by_default(self):
        """AC#9: Default data source is SupabaseDataSource."""
        from unittest.mock import patch
        from app.services.agent.data_source import get_data_source
        from app.services.agent.data_source.supabase import SupabaseDataSource

        with patch("app.services.agent.data_source.get_settings") as mock_settings:
            mock_settings.return_value.data_source_type = "supabase"

            ds = get_data_source()

            assert isinstance(ds, SupabaseDataSource)

    def test_factory_returns_composite_when_configured(self):
        """AC#9: Factory returns CompositeDataSource when configured."""
        from unittest.mock import patch
        from app.services.agent.data_source import get_data_source

        with patch("app.services.agent.data_source.get_settings") as mock_settings:
            mock_settings.return_value.data_source_type = "composite"

            ds = get_data_source()

            assert isinstance(ds, CompositeDataSource)

    def test_factory_singleton_pattern(self):
        """AC#9: Factory returns same instance (singleton)."""
        from unittest.mock import patch
        from app.services.agent.data_source import get_data_source

        with patch("app.services.agent.data_source.get_settings") as mock_settings:
            mock_settings.return_value.data_source_type = "supabase"

            ds1 = get_data_source()
            ds2 = get_data_source()

            assert ds1 is ds2

    def test_factory_unknown_type_defaults_to_supabase(self):
        """AC#9: Unknown type falls back to Supabase."""
        from unittest.mock import patch
        from app.services.agent.data_source import get_data_source
        from app.services.agent.data_source.supabase import SupabaseDataSource

        with patch("app.services.agent.data_source.get_settings") as mock_settings:
            mock_settings.return_value.data_source_type = "unknown_type"

            ds = get_data_source()

            assert isinstance(ds, SupabaseDataSource)

    def test_reset_data_source_clears_singleton(self):
        """reset_data_source clears singleton for testing."""
        from unittest.mock import patch
        from app.services.agent.data_source import get_data_source, reset_data_source

        with patch("app.services.agent.data_source.get_settings") as mock_settings:
            mock_settings.return_value.data_source_type = "supabase"

            ds1 = get_data_source()
            reset_data_source()
            ds2 = get_data_source()

            assert ds1 is not ds2


class TestFutureReadyArchitecture:
    """Tests verifying future-ready architecture for MSSQL (AC#8)."""

    def test_composite_architecture_supports_secondary_source(self, mock_primary_source):
        """AC#8: Architecture supports adding MSSQLDataSource later."""
        # The CompositeDataSource has TODO markers for future MSSQL routing
        cs = CompositeDataSource(primary=mock_primary_source)

        # The primary is set and all methods delegate
        assert cs.primary is mock_primary_source
        assert hasattr(cs, "get_asset")
        assert hasattr(cs, "get_oee")
        assert hasattr(cs, "get_live_snapshot")

    def test_tools_work_without_modification(self, mock_primary_source):
        """AC#8: Existing tools continue to work without modification."""
        cs = CompositeDataSource(primary=mock_primary_source)

        # All protocol methods are available
        protocol_methods = [
            "get_asset",
            "get_asset_by_name",
            "get_assets_by_area",
            "get_similar_assets",
            "get_all_assets",
            "get_oee",
            "get_oee_by_area",
            "get_downtime",
            "get_downtime_by_area",
            "get_live_snapshot",
            "get_live_snapshots_by_area",
            "get_shift_target",
            "get_safety_events",
        ]

        for method in protocol_methods:
            assert hasattr(cs, method), f"Missing method: {method}"
