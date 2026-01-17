"""
Supervisor Scoped Briefing Tests (Story 8.5)

Tests for supervisor-scoped briefings including:
- AC#1: Only assets from supervisor_assignments are included (FR15)
- AC#2: Areas delivered in user's preferred order (FR39)
- AC#3: No assets assigned → error message, no briefing
- AC#4: Assignment changes reflected immediately (no caching)

References:
- [Source: architecture/voice-briefing.md#Role-Based Access Control]
- [Source: prd/prd-functional-requirements.md#FR15]
- [Source: prd/prd-functional-requirements.md#FR37]
- [Source: prd/prd-functional-requirements.md#FR39]
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from app.services.briefing.morning import (
    MorningBriefingService,
    get_morning_briefing_service,
    PRODUCTION_AREAS,
    DEFAULT_AREA_ORDER,
    AreaBriefingData,
    SupervisorBriefingError,
)
from app.models.briefing import (
    BriefingScope,
    BriefingSectionStatus,
    ToolResultData,
    BriefingSection,
    BriefingResponse,
)
from app.models.user import CurrentUserWithRole, UserRole, UserPreferences


class TestSupervisorScopedBriefings:
    """Tests for supervisor-scoped briefings (Story 8.5)."""

    @pytest.fixture
    def service(self):
        """Create a test service."""
        return MorningBriefingService()

    @pytest.fixture
    def supervisor_user(self):
        """Create a test supervisor user with assigned assets."""
        return CurrentUserWithRole(
            id="supervisor-123",
            email="supervisor@example.com",
            role="authenticated",
            user_role=UserRole.SUPERVISOR,
            assigned_asset_ids=["CAMA", "Grinder 1", "Grinder 2"],
        )

    @pytest.fixture
    def supervisor_user_no_assets(self):
        """Create a test supervisor user with no assigned assets."""
        return CurrentUserWithRole(
            id="supervisor-456",
            email="supervisor2@example.com",
            role="authenticated",
            user_role=UserRole.SUPERVISOR,
            assigned_asset_ids=[],
        )

    @pytest.fixture
    def plant_manager_user(self):
        """Create a test plant manager user."""
        return CurrentUserWithRole(
            id="pm-123",
            email="pm@example.com",
            role="authenticated",
            user_role=UserRole.PLANT_MANAGER,
            assigned_asset_ids=[],  # PMs don't have assigned assets
        )

    @pytest.fixture
    def user_preferences(self):
        """Create test user preferences."""
        return UserPreferences(
            user_id="supervisor-123",
            role="supervisor",
            area_order=["grinding", "packing", "roasting"],
            detail_level="detailed",
            voice_enabled=True,
        )

    @pytest.fixture
    def summary_preferences(self):
        """Create test user preferences with summary detail level."""
        return UserPreferences(
            user_id="supervisor-123",
            role="supervisor",
            area_order=["grinding", "packing"],
            detail_level="summary",
            voice_enabled=True,
        )

    # ==========================================================================
    # AC#1: Only assets from supervisor_assignments are included (FR15)
    # ==========================================================================

    @pytest.mark.asyncio
    async def test_supervisor_gets_scoped_briefing(self, service, supervisor_user):
        """Test supervisor with assigned assets gets scoped data (AC#1)."""
        with patch.object(service, '_generate_area_section') as mock_area:
            mock_area.return_value = BriefingSection(
                section_type="area",
                title="Test Area",
                content="Test content",
                status=BriefingSectionStatus.COMPLETE,
                pause_point=True,
            )

            result = await service.generate_supervisor_briefing(
                user=supervisor_user,
                preferences=None,
            )

            # Should return a briefing (not error)
            assert result is not None
            assert result.scope == BriefingScope.SUPERVISOR.value

            # Should only call area section for areas with assigned assets
            # CAMA is in Packing, Grinder 1/2 are in Grinding
            # So should have sections for Packing and Grinding only
            assert mock_area.call_count == 2

    @pytest.mark.asyncio
    async def test_supervisor_briefing_excludes_unassigned_areas(
        self, service, supervisor_user
    ):
        """Test supervisor briefing excludes areas without assigned assets (AC#1)."""
        # Get supervisor areas based on assigned assets
        areas = service.get_supervisor_areas(supervisor_user.assigned_asset_ids)

        # Should only include Packing (CAMA) and Grinding (Grinder 1, 2)
        area_ids = [a["id"] for a in areas]
        assert "packing" in area_ids
        assert "grinding" in area_ids

        # Should NOT include other areas
        assert "roasting" not in area_ids
        assert "powder" not in area_ids
        assert "rychigers" not in area_ids
        assert "green_bean" not in area_ids
        assert "flavor_room" not in area_ids

    @pytest.mark.asyncio
    async def test_supervisor_briefing_no_plant_wide_headline(
        self, service, supervisor_user
    ):
        """Test supervisor briefing skips plant-wide headline (AC#1)."""
        with patch.object(service, '_generate_area_section') as mock_area:
            mock_area.return_value = BriefingSection(
                section_type="area",
                title="Test Area",
                content="Test content",
                status=BriefingSectionStatus.COMPLETE,
                pause_point=True,
            )

            result = await service.generate_supervisor_briefing(
                user=supervisor_user,
                preferences=None,
            )

            # Should NOT have a headline section
            headline_sections = result.get_sections_by_type("headline")
            assert len(headline_sections) == 0

            # All sections should be area type
            for section in result.sections:
                assert section.section_type == "area"

    def test_filter_areas_by_supervisor_assets(self, service, supervisor_user):
        """Test filtering areas to only include assigned assets."""
        all_areas = service.get_production_areas()

        filtered = service.filter_areas_by_supervisor_assets(
            all_areas,
            supervisor_user.assigned_asset_ids,
        )

        # Should have 2 areas (Packing with CAMA, Grinding with Grinder 1, 2)
        assert len(filtered) == 2

        # Check that each area only contains assigned assets
        for area in filtered:
            for asset in area["assets"]:
                assert asset.lower() in [
                    aid.lower() for aid in supervisor_user.assigned_asset_ids
                ]

    # ==========================================================================
    # AC#2: Areas delivered in user's preferred order (FR39)
    # ==========================================================================

    @pytest.mark.asyncio
    async def test_area_order_preference_applied(
        self, service, supervisor_user, user_preferences
    ):
        """Test area ordering respects user preferences (AC#2, FR39)."""
        section_titles = []

        async def mock_area_section(area, detail_level="detailed"):
            section_titles.append(area["id"])
            return BriefingSection(
                section_type="area",
                title=area["name"],
                content="Test content",
                area_id=area["id"],
                status=BriefingSectionStatus.COMPLETE,
                pause_point=True,
            )

        with patch.object(
            service, '_generate_area_section', side_effect=mock_area_section
        ):
            await service.generate_supervisor_briefing(
                user=supervisor_user,
                preferences=user_preferences,
            )

            # Supervisor has assets in Packing and Grinding
            # Preference order is: grinding, packing, roasting
            # So Grinding should come before Packing
            grinding_idx = section_titles.index("grinding")
            packing_idx = section_titles.index("packing")
            assert grinding_idx < packing_idx

    def test_order_areas_with_preference(self, service, user_preferences):
        """Test areas are ordered by user preference."""
        ordered = service.order_areas(user_preferences.area_order)

        # First areas should match preference order
        assert ordered[0]["id"] == "grinding"
        assert ordered[1]["id"] == "packing"
        assert ordered[2]["id"] == "roasting"

        # All 7 areas should still be present
        assert len(ordered) == 7

    @pytest.mark.asyncio
    async def test_supervisor_with_multiple_areas_ordered(self, service):
        """Test supervisor with 3 assets across 2 areas gets correct ordering (AC#2)."""
        supervisor = CurrentUserWithRole(
            id="sup-multi",
            email="sup@example.com",
            role="authenticated",
            user_role=UserRole.SUPERVISOR,
            # 3 assets across 2 areas: Grinding (2) and Roasting (1)
            assigned_asset_ids=["Grinder 1", "Grinder 2", "Roaster 1"],
        )

        preferences = UserPreferences(
            user_id="sup-multi",
            area_order=["roasting", "grinding"],  # Roasting first
            detail_level="detailed",
        )

        section_order = []

        async def mock_area_section(area, detail_level="detailed"):
            section_order.append(area["id"])
            return BriefingSection(
                section_type="area",
                title=area["name"],
                content="Test content",
                area_id=area["id"],
                status=BriefingSectionStatus.COMPLETE,
                pause_point=True,
            )

        with patch.object(
            service, '_generate_area_section', side_effect=mock_area_section
        ):
            result = await service.generate_supervisor_briefing(
                user=supervisor,
                preferences=preferences,
            )

            # Should have 2 areas
            assert len(section_order) == 2

            # Roasting should come first per preference
            assert section_order[0] == "roasting"
            assert section_order[1] == "grinding"

    # ==========================================================================
    # AC#3: No assets assigned → error message, no briefing
    # ==========================================================================

    @pytest.mark.asyncio
    async def test_supervisor_no_assignments_error(
        self, service, supervisor_user_no_assets
    ):
        """Test supervisor with no assignments gets error message (AC#3)."""
        result = await service.generate_supervisor_briefing(
            user=supervisor_user_no_assets,
            preferences=None,
        )

        # Should return error response, not raise exception
        assert result is not None
        assert result.scope == BriefingScope.SUPERVISOR.value

        # Should have error section with specific message
        assert len(result.sections) == 1
        error_section = result.sections[0]
        assert error_section.section_type == "error"
        assert error_section.status == BriefingSectionStatus.FAILED
        assert "No assets assigned" in error_section.content
        assert "contact your administrator" in error_section.content

    def test_create_no_assets_response(self, service):
        """Test _create_no_assets_response generates correct error."""
        result = service._create_no_assets_response(
            briefing_id="test-id",
            user_id="test-user",
        )

        assert result.id == "test-id"
        assert result.user_id == "test-user"
        assert result.scope == BriefingScope.SUPERVISOR.value
        assert len(result.sections) == 1

        section = result.sections[0]
        assert section.title == "No Assets Assigned"
        assert "No assets assigned - contact your administrator" in section.content
        assert section.status == BriefingSectionStatus.FAILED

        # Metadata should indicate no briefing was generated
        assert result.metadata.completion_percentage == 0
        assert result.total_duration_estimate == 0

    @pytest.mark.asyncio
    async def test_supervisor_empty_areas_after_filtering_error(self, service):
        """Test supervisor with invalid assets gets error message."""
        supervisor = CurrentUserWithRole(
            id="sup-invalid",
            email="sup@example.com",
            role="authenticated",
            user_role=UserRole.SUPERVISOR,
            # Assets that don't match any production area
            assigned_asset_ids=["NonExistent1", "NonExistent2"],
        )

        result = await service.generate_supervisor_briefing(
            user=supervisor,
            preferences=None,
        )

        # Should return error response
        assert result is not None
        assert len(result.sections) == 1
        assert result.sections[0].section_type == "error"
        assert "No assets assigned" in result.sections[0].content

    # ==========================================================================
    # AC#4: Assignment changes reflected immediately (no caching)
    # ==========================================================================

    @pytest.mark.asyncio
    async def test_assignment_change_reflects_immediately(self, service):
        """Test assignment changes are reflected immediately (AC#4)."""
        # Create supervisor with initial assignments
        supervisor = CurrentUserWithRole(
            id="sup-dynamic",
            email="sup@example.com",
            role="authenticated",
            user_role=UserRole.SUPERVISOR,
            assigned_asset_ids=["CAMA"],  # Only Packing area
        )

        areas_requested_1 = []

        async def mock_area_section_1(area, detail_level="detailed"):
            areas_requested_1.append(area["id"])
            return BriefingSection(
                section_type="area",
                title=area["name"],
                content="Test",
                area_id=area["id"],
                status=BriefingSectionStatus.COMPLETE,
                pause_point=True,
            )

        with patch.object(
            service, '_generate_area_section', side_effect=mock_area_section_1
        ):
            await service.generate_supervisor_briefing(user=supervisor, preferences=None)

        # First briefing should only include Packing
        assert "packing" in areas_requested_1
        assert "grinding" not in areas_requested_1

        # Update assignments (simulating database change)
        supervisor_updated = CurrentUserWithRole(
            id="sup-dynamic",
            email="sup@example.com",
            role="authenticated",
            user_role=UserRole.SUPERVISOR,
            assigned_asset_ids=["CAMA", "Grinder 1"],  # Now Packing + Grinding
        )

        areas_requested_2 = []

        async def mock_area_section_2(area, detail_level="detailed"):
            areas_requested_2.append(area["id"])
            return BriefingSection(
                section_type="area",
                title=area["name"],
                content="Test",
                area_id=area["id"],
                status=BriefingSectionStatus.COMPLETE,
                pause_point=True,
            )

        with patch.object(
            service, '_generate_area_section', side_effect=mock_area_section_2
        ):
            await service.generate_supervisor_briefing(
                user=supervisor_updated, preferences=None
            )

        # Second briefing should now include both areas
        assert "packing" in areas_requested_2
        assert "grinding" in areas_requested_2

    def test_no_cached_asset_area_mapping(self, service):
        """Test asset-area mapping is built fresh each time."""
        # Clear any cached mapping
        service._asset_area_map = None

        # First call builds mapping
        map1 = service._get_asset_area_map()
        assert len(map1) > 0

        # Manually clear
        service._asset_area_map = None

        # Second call builds fresh mapping (not cached from previous call)
        map2 = service._get_asset_area_map()
        assert map2 is not None

        # Both should have same content but be built independently
        assert len(map1) == len(map2)

    # ==========================================================================
    # Plant Manager still gets all areas (comparison test)
    # ==========================================================================

    @pytest.mark.asyncio
    async def test_plant_manager_gets_all_areas(self, service, plant_manager_user):
        """Test plant manager still gets all areas (not supervisor scoping)."""
        # Plant managers use generate_plant_briefing, not generate_supervisor_briefing
        with patch.object(service, '_get_briefing_service') as mock_bs:
            mock_briefing = MagicMock()
            mock_briefing.get_sections_by_type.return_value = [
                BriefingSection(
                    section_type="headline",
                    title="Test",
                    content="Test headline",
                    status=BriefingSectionStatus.COMPLETE,
                )
            ]
            mock_bs.return_value.generate_briefing = AsyncMock(return_value=mock_briefing)

            with patch.object(service, '_generate_area_section') as mock_area:
                mock_area.return_value = BriefingSection(
                    section_type="area",
                    title="Test Area",
                    content="Test content",
                    status=BriefingSectionStatus.COMPLETE,
                    pause_point=True,
                )

                result = await service.generate_plant_briefing(
                    user_id=plant_manager_user.id,
                )

                # Should have 8 sections: 1 headline + 7 areas
                assert len(result.sections) == 8

                # Should include headline
                headline = result.get_sections_by_type("headline")
                assert len(headline) == 1

                # Should have all 7 production areas
                assert mock_area.call_count == 7

    # ==========================================================================
    # Detail level preferences (FR37)
    # ==========================================================================

    @pytest.mark.asyncio
    async def test_detail_level_preference_applied(
        self, service, supervisor_user, summary_preferences
    ):
        """Test detail level preference is passed to area generation (FR37)."""
        detail_levels_used = []

        async def mock_area_section(area, detail_level="detailed"):
            detail_levels_used.append(detail_level)
            return BriefingSection(
                section_type="area",
                title=area["name"],
                content="Test content",
                area_id=area["id"],
                status=BriefingSectionStatus.COMPLETE,
                pause_point=True,
            )

        with patch.object(
            service, '_generate_area_section', side_effect=mock_area_section
        ):
            await service.generate_supervisor_briefing(
                user=supervisor_user,
                preferences=summary_preferences,
            )

            # All areas should use summary detail level
            for level in detail_levels_used:
                assert level == "summary"

    @pytest.mark.asyncio
    async def test_default_detail_level_is_detailed(self, service, supervisor_user):
        """Test default detail level is 'detailed' when no preferences."""
        detail_levels_used = []

        async def mock_area_section(area, detail_level="detailed"):
            detail_levels_used.append(detail_level)
            return BriefingSection(
                section_type="area",
                title=area["name"],
                content="Test content",
                area_id=area["id"],
                status=BriefingSectionStatus.COMPLETE,
                pause_point=True,
            )

        with patch.object(
            service, '_generate_area_section', side_effect=mock_area_section
        ):
            await service.generate_supervisor_briefing(
                user=supervisor_user,
                preferences=None,  # No preferences
            )

            # All areas should use default detailed level
            for level in detail_levels_used:
                assert level == "detailed"

    # ==========================================================================
    # Supervisor briefing title
    # ==========================================================================

    def test_supervisor_briefing_title(self, service):
        """Test supervisor briefing title is different from plant briefing."""
        title = service._get_supervisor_briefing_title()

        # Should say "Your Area Briefing" not "Morning Briefing"
        assert "Area Briefing" in title

        # Should include date
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        has_day = any(day in title for day in days)
        assert has_day


class TestCurrentUserWithRoleModel:
    """Tests for CurrentUserWithRole model helpers (Story 8.5)."""

    def test_is_supervisor_property(self):
        """Test is_supervisor property."""
        supervisor = CurrentUserWithRole(
            id="test",
            user_role=UserRole.SUPERVISOR,
        )
        assert supervisor.is_supervisor is True
        assert supervisor.is_plant_manager is False

    def test_is_plant_manager_property(self):
        """Test is_plant_manager property."""
        pm = CurrentUserWithRole(
            id="test",
            user_role=UserRole.PLANT_MANAGER,
        )
        assert pm.is_plant_manager is True
        assert pm.is_supervisor is False

    def test_is_admin_property(self):
        """Test is_admin property."""
        admin = CurrentUserWithRole(
            id="test",
            user_role=UserRole.ADMIN,
        )
        assert admin.is_admin is True
        assert admin.is_supervisor is False

    def test_has_assigned_assets_property(self):
        """Test has_assigned_assets property."""
        with_assets = CurrentUserWithRole(
            id="test",
            user_role=UserRole.SUPERVISOR,
            assigned_asset_ids=["asset1", "asset2"],
        )
        assert with_assets.has_assigned_assets is True

        without_assets = CurrentUserWithRole(
            id="test",
            user_role=UserRole.SUPERVISOR,
            assigned_asset_ids=[],
        )
        assert without_assets.has_assigned_assets is False


class TestUserPreferencesModel:
    """Tests for UserPreferences model (Story 8.5, 8.8)."""

    def test_user_preferences_defaults(self):
        """Test UserPreferences default values."""
        prefs = UserPreferences(user_id="test")

        assert prefs.area_order == []
        assert prefs.detail_level == "detailed"
        assert prefs.voice_enabled is True

    def test_user_preferences_custom_values(self):
        """Test UserPreferences with custom values."""
        prefs = UserPreferences(
            user_id="test",
            area_order=["grinding", "packing"],
            detail_level="summary",
            voice_enabled=False,
        )

        assert prefs.area_order == ["grinding", "packing"]
        assert prefs.detail_level == "summary"
        assert prefs.voice_enabled is False


class TestGetSupervisorAreas:
    """Tests for get_supervisor_areas helper method."""

    @pytest.fixture
    def service(self):
        return MorningBriefingService()

    def test_returns_empty_for_no_assets(self, service):
        """Test returns empty list for no assigned assets."""
        areas = service.get_supervisor_areas([])
        assert areas == []

    def test_returns_correct_areas_for_single_asset(self, service):
        """Test returns correct area for single asset."""
        areas = service.get_supervisor_areas(["CAMA"])

        assert len(areas) == 1
        assert areas[0]["id"] == "packing"

    def test_returns_correct_areas_for_multiple_assets_same_area(self, service):
        """Test returns single area for multiple assets in same area."""
        areas = service.get_supervisor_areas(["Grinder 1", "Grinder 2"])

        assert len(areas) == 1
        assert areas[0]["id"] == "grinding"

    def test_returns_multiple_areas_for_assets_across_areas(self, service):
        """Test returns multiple areas when assets span areas."""
        areas = service.get_supervisor_areas(["CAMA", "Roaster 1"])

        area_ids = [a["id"] for a in areas]
        assert len(area_ids) == 2
        assert "packing" in area_ids
        assert "roasting" in area_ids

    def test_case_insensitive_matching(self, service):
        """Test asset matching is case-insensitive."""
        areas = service.get_supervisor_areas(["cama", "GRINDER 1"])

        area_ids = [a["id"] for a in areas]
        assert "packing" in area_ids
        assert "grinding" in area_ids
