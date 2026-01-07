"""
Tests for Asset Detector Utility (Story 4.1)

AC#4: Asset History Memory Storage - asset detection patterns
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.memory.asset_detector import (
    AssetDetector,
    extract_asset_from_message,
    get_asset_detector,
)


@pytest.fixture
def detector():
    """Create a fresh AssetDetector instance for testing."""
    det = AssetDetector()
    det.clear_cache()
    return det


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    mock = MagicMock()
    return mock


@pytest.fixture
def sample_assets():
    """Sample asset data from Supabase."""
    return [
        {"id": "asset-1", "name": "Grinder 5", "source_id": "GRD-005", "area": "Grinding"},
        {"id": "asset-2", "name": "Lathe 3", "source_id": "LTH-003", "area": "Machining"},
        {"id": "asset-3", "name": "Mill 7 - Main", "source_id": "MLL-007", "area": "Milling"},
        {"id": "asset-4", "name": "Press 12", "source_id": "PRS-012", "area": "Pressing"},
        {"id": "asset-5", "name": "Line A", "source_id": "LINE-A", "area": "Assembly"},
    ]


class TestAssetDetectorPatterns:
    """Tests for asset detection regex patterns."""

    def test_pattern_grinder_number(self, detector):
        """Pattern: 'Grinder 5' format."""
        references = detector._extract_references("What's wrong with Grinder 5?")
        assert len(references) > 0
        assert any("grinder 5" in ref[1].lower() for ref in references)

    def test_pattern_machine_number(self, detector):
        """Pattern: 'Machine 7' format."""
        references = detector._extract_references("Check Machine 7 status")
        assert len(references) > 0
        assert any("machine 7" in ref[1].lower() for ref in references)

    def test_pattern_asset_hash(self, detector):
        """Pattern: 'Asset #123' format."""
        references = detector._extract_references("Look at Asset #123")
        assert len(references) > 0
        assert any("asset" in ref[1].lower() and "123" in ref[1] for ref in references)

    def test_pattern_press_number(self, detector):
        """Pattern: 'Press 3' format."""
        references = detector._extract_references("Press 3 is running slow")
        assert len(references) > 0
        assert any("press 3" in ref[1].lower() for ref in references)

    def test_pattern_mixer_number(self, detector):
        """Pattern: 'Mixer 2' format."""
        references = detector._extract_references("Mixer 2 needs maintenance")
        assert len(references) > 0
        assert any("mixer 2" in ref[1].lower() for ref in references)

    def test_pattern_line_letter(self, detector):
        """Pattern: 'Line A' format."""
        references = detector._extract_references("How is Line A performing?")
        assert len(references) > 0
        assert any("line a" in ref[1].lower() for ref in references)

    def test_pattern_lathe_number(self, detector):
        """Pattern: 'Lathe 3' format."""
        references = detector._extract_references("Lathe 3 has issues")
        assert len(references) > 0
        assert any("lathe 3" in ref[1].lower() for ref in references)

    def test_pattern_mill_number(self, detector):
        """Pattern: 'Mill 7' format."""
        references = detector._extract_references("Mill 7 OEE is low")
        assert len(references) > 0
        assert any("mill 7" in ref[1].lower() for ref in references)

    def test_pattern_case_insensitive(self, detector):
        """Pattern matching is case insensitive."""
        references1 = detector._extract_references("GRINDER 5")
        references2 = detector._extract_references("grinder 5")
        references3 = detector._extract_references("Grinder 5")

        assert len(references1) > 0
        assert len(references2) > 0
        assert len(references3) > 0

    def test_no_match_for_unrelated_text(self, detector):
        """No matches for text without asset references."""
        references = detector._extract_references("How is the weather today?")
        assert len(references) == 0

    def test_multiple_assets_in_message(self, detector):
        """Multiple asset references in one message."""
        references = detector._extract_references(
            "Compare Grinder 5 with Lathe 3 performance"
        )
        assert len(references) >= 2


class TestAssetDetectorResolution:
    """Tests for resolving references to asset_id."""

    @pytest.mark.asyncio
    async def test_detect_asset_by_name(self, detector, mock_supabase_client, sample_assets):
        """AC#4: Detect asset by name match."""
        mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = sample_assets
        detector._client = mock_supabase_client

        await detector.load_assets()
        asset_id = await detector.detect_asset("What's wrong with Grinder 5?")

        assert asset_id == "asset-1"

    @pytest.mark.asyncio
    async def test_detect_asset_by_source_id(self, detector, mock_supabase_client, sample_assets):
        """AC#4: Detect asset by source_id match."""
        mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = sample_assets
        detector._client = mock_supabase_client

        await detector.load_assets()

        # Direct source_id reference
        detector._source_id_map["grd-005"] = "asset-1"
        result = detector._resolve_reference("GRD-005")

        assert result == "asset-1"

    @pytest.mark.asyncio
    async def test_detect_asset_partial_name_match(self, detector, mock_supabase_client, sample_assets):
        """AC#4: Partial name matching works."""
        mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = sample_assets
        detector._client = mock_supabase_client

        await detector.load_assets()

        # "Mill 7" should match "Mill 7 - Main"
        asset_id = await detector.detect_asset("Check Mill 7 status")

        assert asset_id == "asset-3"

    @pytest.mark.asyncio
    async def test_detect_returns_none_when_no_match(self, detector, mock_supabase_client, sample_assets):
        """AC#4: Returns None when no asset matches."""
        mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = sample_assets
        detector._client = mock_supabase_client

        await detector.load_assets()
        asset_id = await detector.detect_asset("Some random text without asset")

        assert asset_id is None

    @pytest.mark.asyncio
    async def test_detect_returns_none_when_no_assets(self, detector, mock_supabase_client):
        """AC#4: Returns None when no assets loaded."""
        mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = []
        detector._client = mock_supabase_client

        await detector.load_assets()
        asset_id = await detector.detect_asset("Grinder 5")

        assert asset_id is None


class TestAssetDetectorCaching:
    """Tests for asset caching."""

    @pytest.mark.asyncio
    async def test_load_assets_caches_data(self, detector, mock_supabase_client, sample_assets):
        """Assets are cached after first load."""
        mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = sample_assets
        detector._client = mock_supabase_client

        await detector.load_assets()
        await detector.load_assets()  # Second call

        # Should only query once
        assert mock_supabase_client.table.call_count == 1

    @pytest.mark.asyncio
    async def test_load_assets_force_reload(self, detector, mock_supabase_client, sample_assets):
        """Force reload refreshes cache."""
        mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = sample_assets
        detector._client = mock_supabase_client

        await detector.load_assets()
        await detector.load_assets(force=True)

        # Should query twice
        assert mock_supabase_client.table.call_count == 2

    def test_clear_cache(self, detector):
        """clear_cache clears all cached data."""
        detector._assets_cache = {"test": {}}
        detector._source_id_map = {"test": "id"}
        detector._name_map = {"test": "id"}

        detector.clear_cache()

        assert len(detector._assets_cache) == 0
        assert len(detector._source_id_map) == 0
        assert len(detector._name_map) == 0


class TestAssetDetectorHelpers:
    """Tests for helper methods."""

    @pytest.mark.asyncio
    async def test_get_asset_info(self, detector, mock_supabase_client, sample_assets):
        """get_asset_info returns asset details."""
        mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = sample_assets
        detector._client = mock_supabase_client

        await detector.load_assets()
        asset_info = await detector.get_asset_info("asset-1")

        assert asset_info["name"] == "Grinder 5"
        assert asset_info["area"] == "Grinding"

    @pytest.mark.asyncio
    async def test_get_asset_info_returns_none(self, detector, mock_supabase_client, sample_assets):
        """get_asset_info returns None for unknown asset."""
        mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = sample_assets
        detector._client = mock_supabase_client

        await detector.load_assets()
        asset_info = await detector.get_asset_info("unknown-asset")

        assert asset_info is None


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_asset_detector_returns_singleton(self):
        """get_asset_detector returns singleton."""
        det1 = get_asset_detector()
        det2 = get_asset_detector()

        assert det1 is det2

    @pytest.mark.asyncio
    async def test_extract_asset_from_message(self):
        """extract_asset_from_message convenience function."""
        with patch('app.services.memory.asset_detector.get_asset_detector') as mock_get:
            mock_detector = MagicMock()
            mock_detector.detect_asset = AsyncMock(return_value="asset-123")
            mock_get.return_value = mock_detector

            result = await extract_asset_from_message("Check Grinder 5")

            assert result == "asset-123"
            mock_detector.detect_asset.assert_called_once_with("Check Grinder 5")
