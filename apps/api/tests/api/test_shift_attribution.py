"""
Tests for Shift Attribution Logic in Action Engine.

Story: 17.4 - Shift Breakdown API & UI
AC: #3 - Single-shift attribution when one shift dominates
AC: #4 - Systemic issue remains daily-level without shift attribution
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import date
from uuid import uuid4

from app.services.action_engine import ActionEngine


# =============================================================================
# Fixtures
# =============================================================================

ASSET_1_ID = str(uuid4())
ASSET_2_ID = str(uuid4())


@pytest.fixture
def engine():
    """Create an ActionEngine with a mock Supabase client."""
    mock_client = MagicMock()
    return ActionEngine(supabase_client=mock_client)


# =============================================================================
# Tests: _get_shift_attribution
# =============================================================================


class TestGetShiftAttribution:
    """Tests for _get_shift_attribution method."""

    def test_single_shift_dominant_returns_attribution(self, engine):
        """17-4-UNIT-020: AC#3: When one shift has >60% of downtime, returns attribution string."""
        shift_data = [
            {"shift": "morning", "downtime_minutes": 10, "units_produced": 100, "oee": 90.0},
            {"shift": "afternoon", "downtime_minutes": 58, "units_produced": 70, "oee": 65.0},
            {"shift": "night", "downtime_minutes": 12, "units_produced": 90, "oee": 85.0},
        ]
        # afternoon: 58/80 = 72.5% > 60%

        result = engine._get_shift_attribution(ASSET_1_ID, shift_data)
        assert result is not None
        assert "afternoon shift" in result
        assert "58 min" in result

    def test_systemic_issue_returns_none(self, engine):
        """17-4-UNIT-021: AC#4: When no shift exceeds 60%, returns None (systemic issue)."""
        shift_data = [
            {"shift": "morning", "downtime_minutes": 30, "units_produced": 100, "oee": 80.0},
            {"shift": "afternoon", "downtime_minutes": 35, "units_produced": 90, "oee": 75.0},
            {"shift": "night", "downtime_minutes": 25, "units_produced": 95, "oee": 78.0},
        ]
        # max is afternoon: 35/90 = 38.9% < 60%

        result = engine._get_shift_attribution(ASSET_1_ID, shift_data)
        assert result is None

    def test_no_shift_data_returns_none(self, engine):
        """17-4-UNIT-022: When no shift data available, returns None."""
        result = engine._get_shift_attribution(ASSET_1_ID, [])
        assert result is None

    def test_single_shift_record_returns_none(self, engine):
        """17-4-UNIT-023: With only one shift record, cannot determine attribution."""
        shift_data = [
            {"shift": "morning", "downtime_minutes": 60, "units_produced": 100, "oee": 80.0},
        ]
        result = engine._get_shift_attribution(ASSET_1_ID, shift_data)
        assert result is None

    def test_zero_downtime_returns_none(self, engine):
        """17-4-UNIT-024: When total downtime is zero, returns None."""
        shift_data = [
            {"shift": "morning", "downtime_minutes": 0, "units_produced": 100, "oee": 95.0},
            {"shift": "afternoon", "downtime_minutes": 0, "units_produced": 100, "oee": 95.0},
            {"shift": "night", "downtime_minutes": 0, "units_produced": 100, "oee": 95.0},
        ]
        result = engine._get_shift_attribution(ASSET_1_ID, shift_data)
        assert result is None

    def test_exactly_60_pct_returns_none(self, engine):
        """17-4-UNIT-025: Exactly 60% (not >) does not trigger attribution."""
        shift_data = [
            {"shift": "morning", "downtime_minutes": 60, "units_produced": 100, "oee": 80.0},
            {"shift": "afternoon", "downtime_minutes": 20, "units_produced": 90, "oee": 85.0},
            {"shift": "night", "downtime_minutes": 20, "units_produced": 95, "oee": 87.0},
        ]
        # morning: 60/100 = exactly 60% — should NOT trigger

        result = engine._get_shift_attribution(ASSET_1_ID, shift_data)
        assert result is None

    def test_attribution_string_format(self, engine):
        """17-4-UNIT-026: AC#3: Attribution string includes shift name and downtime."""
        shift_data = [
            {"shift": "night", "downtime_minutes": 70, "units_produced": 50, "oee": 60.0},
            {"shift": "morning", "downtime_minutes": 10, "units_produced": 100, "oee": 90.0},
            {"shift": "afternoon", "downtime_minutes": 5, "units_produced": 100, "oee": 92.0},
        ]
        # night: 70/85 = 82.4% > 60%

        result = engine._get_shift_attribution(ASSET_1_ID, shift_data)
        assert result == "night shift — 70 min downtime"


# =============================================================================
# Tests: _load_shift_summaries
# =============================================================================


class TestLoadShiftSummaries:
    """Tests for _load_shift_summaries batch loading."""

    @pytest.mark.asyncio
    async def test_load_returns_grouped_data(self, engine):
        """17-4-UNIT-027: _load_shift_summaries groups results by asset_id."""
        mock_response = MagicMock()
        mock_response.data = [
            {"asset_id": ASSET_1_ID, "shift": "morning", "oee": 88.0, "downtime_minutes": 15, "units_produced": 120},
            {"asset_id": ASSET_1_ID, "shift": "afternoon", "oee": 84.0, "downtime_minutes": 25, "units_produced": 100},
            {"asset_id": ASSET_2_ID, "shift": "morning", "oee": 78.0, "downtime_minutes": 20, "units_produced": 100},
        ]

        mock_client = engine._get_client()
        table_mock = MagicMock()
        mock_client.table.return_value = table_mock
        table_mock.select.return_value.in_.return_value.eq.return_value.execute.return_value = mock_response

        result = await engine._load_shift_summaries(date(2026, 2, 10), [ASSET_1_ID, ASSET_2_ID])

        assert ASSET_1_ID in result
        assert len(result[ASSET_1_ID]) == 2
        assert ASSET_2_ID in result
        assert len(result[ASSET_2_ID]) == 1

    @pytest.mark.asyncio
    async def test_load_empty_asset_ids(self, engine):
        """17-4-UNIT-028: Empty asset_ids returns empty dict."""
        result = await engine._load_shift_summaries(date(2026, 2, 10), [])
        assert result == {}

    @pytest.mark.asyncio
    async def test_load_handles_error(self, engine):
        """17-4-UNIT-029: Errors return empty dict gracefully."""
        mock_client = engine._get_client()
        mock_client.table.side_effect = Exception("DB error")

        result = await engine._load_shift_summaries(date(2026, 2, 10), [ASSET_1_ID])
        assert result == {}
