"""
Morning Briefing Service (Story 8.4, 8.5)

Orchestrates morning briefing generation for Plant Managers and Supervisors.
Covers all 7 production areas with user-preferred ordering.

Story 8.4:
- AC#1: Cover all 7 production areas in user's preferred order
- AC#2: Pause prompts between sections
- AC#5: Q&A integration during pauses

Story 8.5 (Supervisor Scoped Briefings):
- AC#1: Only assets from supervisor_assignments are included (FR15)
- AC#2: Areas delivered in user's preferred order (FR39)
- AC#3: No assets assigned → error message, no briefing
- AC#4: Assignment changes reflected immediately

References:
- [Source: architecture/voice-briefing.md#BriefingService Architecture]
- [Source: architecture/voice-briefing.md#Role-Based Access Control]
- [Source: prd/prd-functional-requirements.md#FR15]
- [Source: prd/prd-functional-requirements.md#FR36]
- [Source: prd/prd-functional-requirements.md#FR37]
- [Source: prd/prd-functional-requirements.md#FR39]
"""

import logging
import asyncio
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Set

# Python 3.11+ has asyncio.timeout, earlier versions need async_timeout
if sys.version_info >= (3, 11):
    from asyncio import timeout as async_timeout
else:
    try:
        from async_timeout import timeout as async_timeout
    except ImportError:
        # Fallback implementation for older Python without async_timeout
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def async_timeout(seconds):
            """Simple timeout context manager fallback."""
            try:
                yield
            except asyncio.CancelledError:
                raise asyncio.TimeoutError()

from app.models.briefing import (
    BriefingResponse,
    BriefingSection,
    BriefingSectionStatus,
    BriefingResponseMetadata,
    BriefingData,
    ToolResultData,
    BriefingCitation,
    BriefingScope,
)
from app.models.user import CurrentUserWithRole, UserRole, UserPreferences
from app.services.briefing.service import (
    BriefingService,
    get_briefing_service,
    TOTAL_TIMEOUT_SECONDS,
    PER_TOOL_TIMEOUT_SECONDS,
)
from app.services.briefing.narrative import get_narrative_generator

logger = logging.getLogger(__name__)


class SupervisorBriefingError(Exception):
    """Raised when supervisor briefing generation fails due to assignment issues."""
    pass


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)


# Production Areas (Plant Object Model - AC#1)
PRODUCTION_AREAS = [
    {
        "id": "packing",
        "name": "Packing",
        "assets": ["CAMA", "Pack Cells", "Variety Pack", "Bag Lines", "Nuspark"],
        "description": "Packing operations including CAMA, Pack Cells, and Bag Lines",
    },
    {
        "id": "rychigers",
        "name": "Rychigers",
        "assets": ["Rychiger 101", "Rychiger 102", "Rychiger 103", "Rychiger 104",
                   "Rychiger 105", "Rychiger 106", "Rychiger 107", "Rychiger 108",
                   "Rychiger 109", "Rychiger 1009"],
        "description": "Rychiger packaging lines 101-109 and 1009",
    },
    {
        "id": "grinding",
        "name": "Grinding",
        "assets": ["Grinder 1", "Grinder 2", "Grinder 3", "Grinder 4", "Grinder 5"],
        "description": "Coffee grinding operations",
    },
    {
        "id": "powder",
        "name": "Powder",
        "assets": ["1002 Fill & Pack", "1003 Fill & Pack", "1004 Fill & Pack", "Manual Bulk"],
        "description": "Powder fill and pack lines",
    },
    {
        "id": "roasting",
        "name": "Roasting",
        "assets": ["Roaster 1", "Roaster 2", "Roaster 3", "Roaster 4"],
        "description": "Coffee roasting operations",
    },
    {
        "id": "green_bean",
        "name": "Green Bean",
        "assets": ["Manual", "Silo Transfer"],
        "description": "Green bean receiving and silo operations",
    },
    {
        "id": "flavor_room",
        "name": "Flavor Room",
        "assets": ["Coffee Flavor Room"],
        "description": "Flavor addition operations",
    },
]

# Default area order (FR36)
DEFAULT_AREA_ORDER = ["packing", "rychigers", "grinding", "powder", "roasting", "green_bean", "flavor_room"]

# Timeout for area briefing generation
AREA_TIMEOUT_SECONDS = 4


class AreaBriefingData:
    """Data for a single production area briefing."""

    def __init__(
        self,
        area_id: str,
        area_name: str,
        description: str,
        assets: List[str],
    ):
        self.area_id = area_id
        self.area_name = area_name
        self.description = description
        self.assets = assets
        self.production_status: Optional[ToolResultData] = None
        self.oee_data: Optional[ToolResultData] = None
        self.downtime_analysis: Optional[ToolResultData] = None
        self.safety_events: Optional[ToolResultData] = None


class MorningBriefingService:
    """
    Morning briefing orchestration service.

    Story 8.4 Implementation:
    - AC#1: Orchestrates briefings for all 7 production areas
    - AC#2: Adds pause prompts between sections
    - Respects user's preferred area order (FR36)

    Story 8.5 Implementation (Supervisor Scoped Briefings):
    - AC#1: Filters assets based on supervisor_assignments (FR15)
    - AC#2: Areas delivered in user's preferred order (FR39)
    - AC#3: Returns error for supervisors with no assignments
    - AC#4: No caching - assignment changes reflected immediately

    This is NOT a ManufacturingTool - it's an orchestration layer.

    Usage:
        service = get_morning_briefing_service()

        # For Plant Managers (all areas)
        briefing = await service.generate_plant_briefing(
            user_id="user123",
            area_order=["roasting", "grinding", ...]
        )

        # For Supervisors (scoped to assigned assets)
        briefing = await service.generate_supervisor_briefing(
            user=current_user_with_role,
            preferences=user_preferences,
        )
    """

    def __init__(self, briefing_service: Optional[BriefingService] = None):
        """
        Initialize the morning briefing service.

        Args:
            briefing_service: Optional BriefingService instance (for testing)
        """
        self._briefing_service = briefing_service
        self._narrative_generator = None
        # Cache for asset-to-area mapping (built on first use)
        self._asset_area_map: Optional[Dict[str, str]] = None

    def _get_briefing_service(self) -> BriefingService:
        """Get the base briefing service."""
        if self._briefing_service is None:
            self._briefing_service = get_briefing_service()
        return self._briefing_service

    def _get_narrative_generator(self):
        """Get narrative generator (lazy init)."""
        if self._narrative_generator is None:
            self._narrative_generator = get_narrative_generator()
        return self._narrative_generator

    def get_production_areas(self) -> List[Dict[str, Any]]:
        """
        Get list of all production areas.

        Returns:
            List of production area definitions
        """
        return PRODUCTION_AREAS.copy()

    def get_default_area_order(self) -> List[str]:
        """
        Get the default area order.

        Returns:
            List of area IDs in default order
        """
        return DEFAULT_AREA_ORDER.copy()

    def order_areas(
        self,
        preferred_order: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Order production areas based on user preference.

        AC#1: Areas delivered in user's preferred order (FR36)

        Args:
            preferred_order: Optional list of area IDs in preferred order

        Returns:
            List of production area definitions in order
        """
        if not preferred_order:
            preferred_order = DEFAULT_AREA_ORDER

        # Build ordered list
        areas_by_id = {area["id"]: area for area in PRODUCTION_AREAS}
        ordered_areas = []

        # Add areas in preferred order
        for area_id in preferred_order:
            if area_id in areas_by_id:
                ordered_areas.append(areas_by_id[area_id])

        # Add any missing areas at the end
        for area in PRODUCTION_AREAS:
            if area not in ordered_areas:
                ordered_areas.append(area)

        return ordered_areas

    def _get_asset_area_map(self) -> Dict[str, str]:
        """
        Build mapping from asset names to area IDs.

        Used to determine which areas contain supervisor's assigned assets.
        """
        if self._asset_area_map is None:
            self._asset_area_map = {}
            for area in PRODUCTION_AREAS:
                for asset_name in area["assets"]:
                    # Map asset name to area ID
                    self._asset_area_map[asset_name.lower()] = area["id"]
        return self._asset_area_map

    def get_supervisor_areas(
        self,
        assigned_asset_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Get production areas that contain supervisor's assigned assets.

        Story 8.5 AC#1: Only include areas with assigned assets (FR15).

        Args:
            assigned_asset_ids: List of asset IDs assigned to supervisor

        Returns:
            List of area definitions containing at least one assigned asset
        """
        if not assigned_asset_ids:
            return []

        # For MVP, we match by asset ID or asset name
        # In production, this would query the database to map asset_id to area
        assigned_set = set(str(aid).lower() for aid in assigned_asset_ids)

        areas_with_assets = []
        for area in PRODUCTION_AREAS:
            # Check if any asset in this area is assigned
            for asset_name in area["assets"]:
                # Match by name (lowercase) or ID
                if asset_name.lower() in assigned_set:
                    areas_with_assets.append(area)
                    break

        return areas_with_assets

    def filter_areas_by_supervisor_assets(
        self,
        areas: List[Dict[str, Any]],
        assigned_asset_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Filter areas to only include those with supervisor's assigned assets.

        Each area dict is modified to include only the assigned assets.

        Args:
            areas: List of area definitions
            assigned_asset_ids: List of asset IDs assigned to supervisor

        Returns:
            Filtered list of areas with only assigned assets
        """
        if not assigned_asset_ids:
            return []

        assigned_set = set(str(aid).lower() for aid in assigned_asset_ids)
        filtered_areas = []

        for area in areas:
            # Find which assets in this area are assigned
            assigned_in_area = [
                asset for asset in area["assets"]
                if asset.lower() in assigned_set
            ]

            if assigned_in_area:
                # Create new area dict with only assigned assets
                filtered_area = area.copy()
                filtered_area["assets"] = assigned_in_area
                filtered_areas.append(filtered_area)

        return filtered_areas

    async def generate_supervisor_briefing(
        self,
        user: CurrentUserWithRole,
        preferences: Optional[UserPreferences] = None,
        include_audio: bool = True,
    ) -> BriefingResponse:
        """
        Generate a morning briefing scoped to supervisor's assigned assets.

        Story 8.5 Implementation:
        - AC#1: Only assets from supervisor_assignments are included (FR15)
        - AC#2: Areas delivered in user's preferred order (FR39)
        - AC#3: No assets assigned → error message, no briefing
        - AC#4: Assignment changes reflected immediately (no caching)

        Args:
            user: CurrentUserWithRole with assigned_asset_ids populated
            preferences: Optional user preferences for area order and detail level
            include_audio: Whether to generate TTS audio

        Returns:
            BriefingResponse scoped to supervisor's assets

        Raises:
            SupervisorBriefingError: If supervisor has no assets assigned
        """
        start_time = _utcnow()
        briefing_id = str(uuid.uuid4())

        logger.info(
            f"Generating supervisor briefing {briefing_id} for user {user.id} "
            f"with {len(user.assigned_asset_ids)} assigned assets"
        )

        # AC#3: Check for no assets assigned
        if not user.has_assigned_assets:
            logger.warning(f"Supervisor {user.id} has no assets assigned")
            return self._create_no_assets_response(briefing_id, user.id)

        # Get preferred area order from preferences (AC#2, FR39)
        area_order = None
        detail_level = "detailed"
        if preferences:
            area_order = preferences.area_order if preferences.area_order else None
            detail_level = preferences.detail_level

        # Get areas ordered by preference
        ordered_areas = self.order_areas(area_order)

        # Filter to only areas with supervisor's assigned assets (AC#1, FR15)
        supervisor_areas = self.filter_areas_by_supervisor_assets(
            ordered_areas,
            user.assigned_asset_ids,
        )

        if not supervisor_areas:
            logger.warning(
                f"No areas found for supervisor {user.id} with assigned assets: {user.assigned_asset_ids}"
            )
            return self._create_no_assets_response(briefing_id, user.id)

        logger.info(
            f"Supervisor briefing will cover {len(supervisor_areas)} areas: "
            f"{[a['name'] for a in supervisor_areas]}"
        )

        sections: List[BriefingSection] = []
        tool_failures: List[str] = []
        timed_out = False

        try:
            # Total 30-second timeout (NFR8)
            async with async_timeout(TOTAL_TIMEOUT_SECONDS):
                # AC#1: Skip plant-wide headline for supervisors - go straight to their areas
                # No headline section generated

                # Generate area sections in parallel for performance
                area_tasks = [
                    self._generate_area_section(
                        area,
                        detail_level=detail_level,
                    )
                    for area in supervisor_areas
                ]

                area_results = await asyncio.gather(*area_tasks, return_exceptions=True)

                # Process results
                for i, result in enumerate(area_results):
                    if isinstance(result, Exception):
                        logger.error(f"Area {supervisor_areas[i]['name']} failed: {result}")
                        tool_failures.append(supervisor_areas[i]["id"])
                        sections.append(self._create_error_section(supervisor_areas[i]))
                    elif isinstance(result, BriefingSection):
                        sections.append(result)
                    else:
                        logger.warning(f"Unexpected result for {supervisor_areas[i]['name']}: {type(result)}")

        except asyncio.TimeoutError:
            logger.warning(f"Supervisor briefing {briefing_id} timed out after {TOTAL_TIMEOUT_SECONDS}s")
            timed_out = True
            for section in sections:
                if section.status == BriefingSectionStatus.PENDING:
                    section.status = BriefingSectionStatus.TIMED_OUT
                    section.error_message = "Generation timed out"

        except Exception as e:
            logger.error(f"Supervisor briefing generation failed: {e}", exc_info=True)
            return self._create_error_response(briefing_id, user.id, str(e))

        # Calculate completion
        completed_count = len([s for s in sections if s.is_complete])
        total_count = len(sections) if sections else 1
        completion_pct = (completed_count / total_count) * 100 if total_count > 0 else 0

        # Calculate duration
        end_time = _utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # Estimate audio duration
        total_chars = sum(len(s.content) for s in sections)
        # Supervisor briefings are shorter, min 30s
        duration_estimate_seconds = max(int(total_chars / 12.5), 30)

        # Build response
        return BriefingResponse(
            id=briefing_id,
            title=self._get_supervisor_briefing_title(),
            scope=BriefingScope.SUPERVISOR.value,
            user_id=user.id,
            sections=sections,
            audio_stream_url=None,
            total_duration_estimate=duration_estimate_seconds,
            metadata=BriefingResponseMetadata(
                generated_at=start_time,
                generation_duration_ms=duration_ms,
                completion_percentage=completion_pct,
                timed_out=timed_out,
                tool_failures=tool_failures,
                cache_hit=False,
            ),
        )

    def _create_no_assets_response(
        self,
        briefing_id: str,
        user_id: str,
    ) -> BriefingResponse:
        """
        Create response for supervisor with no assigned assets.

        Story 8.5 AC#3: Display error message, no briefing generated.
        """
        return BriefingResponse(
            id=briefing_id,
            title="Morning Briefing",
            scope=BriefingScope.SUPERVISOR.value,
            user_id=user_id,
            sections=[
                BriefingSection(
                    section_type="error",
                    title="No Assets Assigned",
                    content="No assets assigned - contact your administrator",
                    status=BriefingSectionStatus.FAILED,
                    error_message="Supervisor has no assets assigned",
                    pause_point=False,
                )
            ],
            total_duration_estimate=0,
            metadata=BriefingResponseMetadata(
                generated_at=_utcnow(),
                completion_percentage=0,
                timed_out=False,
                tool_failures=[],
            ),
        )

    def _get_supervisor_briefing_title(self) -> str:
        """Get the supervisor briefing title."""
        now = _utcnow()
        date_str = now.strftime("%A, %B %d")
        return f"Your Area Briefing - {date_str}"

    async def generate_plant_briefing(
        self,
        user_id: str,
        area_order: Optional[List[str]] = None,
        include_audio: bool = True,
    ) -> BriefingResponse:
        """
        Generate a complete morning briefing covering all production areas.

        AC#1: Covers all 7 production areas in user's preferred order
        AC#2: Each area section has pause_point=True for Q&A

        Args:
            user_id: User requesting the briefing
            area_order: Optional list of area IDs in preferred order
            include_audio: Whether to generate TTS audio

        Returns:
            BriefingResponse with sections for each area
        """
        start_time = _utcnow()
        briefing_id = str(uuid.uuid4())

        logger.info(f"Generating morning briefing {briefing_id} for user {user_id}")

        # Get ordered areas
        areas = self.order_areas(area_order)

        sections: List[BriefingSection] = []
        tool_failures: List[str] = []
        timed_out = False

        try:
            # Total 30-second timeout (NFR8)
            async with async_timeout(TOTAL_TIMEOUT_SECONDS):
                # Generate headline section first
                headline_section = await self._generate_headline_section(user_id)
                sections.append(headline_section)

                # Generate area sections in parallel for performance
                area_tasks = [
                    self._generate_area_section(area)
                    for area in areas
                ]

                area_results = await asyncio.gather(*area_tasks, return_exceptions=True)

                # Process results
                for i, result in enumerate(area_results):
                    if isinstance(result, Exception):
                        logger.error(f"Area {areas[i]['name']} failed: {result}")
                        tool_failures.append(areas[i]["id"])
                        # Create partial section for failed area
                        sections.append(self._create_error_section(areas[i]))
                    elif isinstance(result, BriefingSection):
                        sections.append(result)
                    else:
                        logger.warning(f"Unexpected result for {areas[i]['name']}: {type(result)}")

        except asyncio.TimeoutError:
            logger.warning(f"Morning briefing {briefing_id} timed out after {TOTAL_TIMEOUT_SECONDS}s")
            timed_out = True
            # Mark pending sections as timed out
            for section in sections:
                if section.status == BriefingSectionStatus.PENDING:
                    section.status = BriefingSectionStatus.TIMED_OUT
                    section.error_message = "Generation timed out"

        except Exception as e:
            logger.error(f"Morning briefing generation failed: {e}", exc_info=True)
            return self._create_error_response(briefing_id, user_id, str(e))

        # Calculate completion
        completed_count = len([s for s in sections if s.is_complete])
        total_count = len(sections) if sections else 1
        completion_pct = (completed_count / total_count) * 100 if total_count > 0 else 0

        # Calculate duration
        end_time = _utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # Estimate audio duration (~150 words/min, ~5 chars/word = 750 chars/min)
        total_chars = sum(len(s.content) for s in sections)
        duration_estimate_seconds = max(int(total_chars / 12.5), 75)  # Min 75s for full briefing

        # Build response
        return BriefingResponse(
            id=briefing_id,
            title=self._get_briefing_title(),
            scope=BriefingScope.PLANT_WIDE.value,
            user_id=user_id,
            sections=sections,
            audio_stream_url=None,  # TTS integration handled separately
            total_duration_estimate=duration_estimate_seconds,
            metadata=BriefingResponseMetadata(
                generated_at=start_time,
                generation_duration_ms=duration_ms,
                completion_percentage=completion_pct,
                timed_out=timed_out,
                tool_failures=tool_failures,
                cache_hit=False,
            ),
        )

    async def _generate_headline_section(self, user_id: str) -> BriefingSection:
        """
        Generate the opening headline section.

        Provides plant-wide summary before diving into areas.
        """
        # Get plant-wide briefing data for headline
        service = self._get_briefing_service()

        try:
            # Get plant-wide briefing (uses existing service)
            plant_briefing = await service.generate_briefing(
                user_id=user_id,
                scope=BriefingScope.PLANT_WIDE,
            )

            # Extract headline from plant-wide briefing
            headlines = plant_briefing.get_sections_by_type("headline")
            if headlines:
                headline = headlines[0]
                return BriefingSection(
                    section_type="headline",
                    title="Morning Briefing Overview",
                    content=headline.content,
                    citations=headline.citations,
                    status=BriefingSectionStatus.COMPLETE,
                    pause_point=True,  # AC#2: Pause after headline
                )

            # Fallback headline
            return BriefingSection(
                section_type="headline",
                title="Morning Briefing Overview",
                content="Good morning! Here's your plant-wide production briefing. I'll cover each area with key metrics and any issues that need attention.",
                status=BriefingSectionStatus.COMPLETE,
                pause_point=True,
            )

        except Exception as e:
            logger.warning(f"Headline generation failed: {e}")
            return BriefingSection(
                section_type="headline",
                title="Morning Briefing Overview",
                content="Good morning! Let's review each production area. I'll highlight key metrics and any issues requiring attention.",
                status=BriefingSectionStatus.PARTIAL,
                pause_point=True,
            )

    async def _generate_area_section(
        self,
        area: Dict[str, Any],
        detail_level: str = "detailed",
    ) -> BriefingSection:
        """
        Generate a briefing section for a single production area.

        AC#1: Area-level section with key metrics
        AC#2: pause_point=True for Q&A prompt
        FR37: detail_level preference applied

        Args:
            area: Area definition dict
            detail_level: "summary" or "detailed" (FR37)

        Returns:
            BriefingSection for the area
        """
        area_id = area["id"]
        area_name = area["name"]
        assets = area.get("assets", [])

        try:
            async with async_timeout(AREA_TIMEOUT_SECONDS):
                # Get area-level data
                area_data = await self._get_area_data(area_id, assets)

                # Generate narrative for the area (FR37: detail level)
                content = await self._generate_area_narrative(
                    area_name,
                    area_data,
                    detail_level=detail_level,
                )

                return BriefingSection(
                    section_type="area",
                    title=f"{area_name}",
                    content=content,
                    area_id=area_id,
                    citations=self._extract_citations(area_data),
                    status=BriefingSectionStatus.COMPLETE,
                    pause_point=True,  # AC#2: Pause for Q&A after each area
                )

        except asyncio.TimeoutError:
            logger.warning(f"Area {area_name} section timed out")
            return BriefingSection(
                section_type="area",
                title=f"{area_name}",
                content=f"{area_name} data is taking longer than expected. Moving on for now.",
                area_id=area_id,
                status=BriefingSectionStatus.TIMED_OUT,
                error_message="Section timed out",
                pause_point=True,
            )

        except Exception as e:
            logger.error(f"Area {area_name} section failed: {e}")
            return BriefingSection(
                section_type="area",
                title=f"{area_name}",
                content=f"Unable to retrieve complete data for {area_name}. Please check the dashboard for details.",
                area_id=area_id,
                status=BriefingSectionStatus.PARTIAL,
                error_message=str(e),
                pause_point=True,
            )

    async def _get_area_data(
        self,
        area_id: str,
        assets: List[str],
    ) -> AreaBriefingData:
        """
        Get briefing data for a specific area.

        Queries tools scoped to the area's assets.
        """
        area_def = next((a for a in PRODUCTION_AREAS if a["id"] == area_id), None)
        if not area_def:
            raise ValueError(f"Unknown area: {area_id}")

        area_data = AreaBriefingData(
            area_id=area_id,
            area_name=area_def["name"],
            description=area_def["description"],
            assets=assets,
        )

        # Import tools here to avoid circular imports
        from app.services.agent.tools.production_status import ProductionStatusTool
        from app.services.agent.tools.oee_query import OEEQueryTool
        from app.services.agent.tools.downtime_analysis import DowntimeAnalysisTool
        from app.services.agent.tools.safety_events import SafetyEventsTool

        # Run tools in parallel for this area
        tasks = [
            self._get_production_for_area(ProductionStatusTool(), area_id),
            self._get_oee_for_area(OEEQueryTool(), area_id),
            self._get_downtime_for_area(DowntimeAnalysisTool(), area_id),
            self._get_safety_for_area(SafetyEventsTool(), area_id),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Map results
        if not isinstance(results[0], Exception):
            area_data.production_status = results[0]
        if not isinstance(results[1], Exception):
            area_data.oee_data = results[1]
        if not isinstance(results[2], Exception):
            area_data.downtime_analysis = results[2]
        if not isinstance(results[3], Exception):
            area_data.safety_events = results[3]

        return area_data

    async def _get_production_for_area(self, tool, area_id: str) -> ToolResultData:
        """Get production status for area."""
        try:
            result = await tool._arun(area=area_id)
            return ToolResultData(
                tool_name="production_status",
                success=result.success,
                data=result.data if result.success else None,
                citations=[BriefingCitation(source=c.source, table=c.table, timestamp=c.timestamp)
                           for c in result.citations] if hasattr(result, 'citations') else [],
                error_message=result.error_message if not result.success else None,
            )
        except Exception as e:
            return ToolResultData(tool_name="production_status", success=False, error_message=str(e))

    async def _get_oee_for_area(self, tool, area_id: str) -> ToolResultData:
        """Get OEE data for area."""
        try:
            result = await tool._arun(scope="area", area=area_id, days=1)
            return ToolResultData(
                tool_name="oee_data",
                success=result.success,
                data=result.data if result.success else None,
                citations=[BriefingCitation(source=c.source, table=c.table, timestamp=c.timestamp)
                           for c in result.citations] if hasattr(result, 'citations') else [],
                error_message=result.error_message if not result.success else None,
            )
        except Exception as e:
            return ToolResultData(tool_name="oee_data", success=False, error_message=str(e))

    async def _get_downtime_for_area(self, tool, area_id: str) -> ToolResultData:
        """Get downtime analysis for area."""
        try:
            result = await tool._arun(area=area_id, days=1)
            return ToolResultData(
                tool_name="downtime_analysis",
                success=result.success,
                data=result.data if result.success else None,
                citations=[BriefingCitation(source=c.source, table=c.table, timestamp=c.timestamp)
                           for c in result.citations] if hasattr(result, 'citations') else [],
                error_message=result.error_message if not result.success else None,
            )
        except Exception as e:
            return ToolResultData(tool_name="downtime_analysis", success=False, error_message=str(e))

    async def _get_safety_for_area(self, tool, area_id: str) -> ToolResultData:
        """Get safety events for area."""
        try:
            result = await tool._arun(area=area_id, days=1)
            return ToolResultData(
                tool_name="safety_events",
                success=result.success,
                data=result.data if result.success else None,
                citations=[BriefingCitation(source=c.source, table=c.table, timestamp=c.timestamp)
                           for c in result.citations] if hasattr(result, 'citations') else [],
                error_message=result.error_message if not result.success else None,
            )
        except Exception as e:
            return ToolResultData(tool_name="safety_events", success=False, error_message=str(e))

    async def _generate_area_narrative(
        self,
        area_name: str,
        area_data: AreaBriefingData,
        detail_level: str = "detailed",
    ) -> str:
        """
        Generate narrative content for an area section.

        Uses template-based generation for consistent, fast output.
        FR37: detail_level preference applied (summary vs detailed).

        Args:
            area_name: Name of the production area
            area_data: Data collected from tools
            detail_level: "summary" for concise, "detailed" for full info
        """
        parts = []

        # Production status
        if area_data.production_status and area_data.production_status.success:
            data = area_data.production_status.data or {}
            summary = data.get("summary", {})

            output = summary.get("total_output")
            target = summary.get("total_target")
            variance = summary.get("total_variance_percent", 0)

            if output is not None and target is not None:
                if variance >= 0:
                    parts.append(f"{area_name} is performing well at {abs(variance):.1f}% ahead of target.")
                else:
                    parts.append(f"{area_name} is tracking {abs(variance):.1f}% behind target.")

                # Detailed mode: add assets needing attention
                if detail_level == "detailed":
                    behind_count = summary.get("behind_count", 0)
                    if behind_count > 0:
                        attention = summary.get("assets_needing_attention", [])[:2]
                        if attention:
                            parts.append(f"{', '.join(attention)} need attention.")
            else:
                parts.append(f"Production data for {area_name} is being updated.")
        else:
            parts.append(f"Production status for {area_name} is currently unavailable.")

        # OEE
        if area_data.oee_data and area_data.oee_data.success:
            data = area_data.oee_data.data or {}
            oee = data.get("oee_percentage", data.get("oee"))
            if oee is not None:
                parts.append(f"OEE is at {oee}%. [Source: daily_summaries]")

        # Safety (mention only if there are events) - always include for safety
        if area_data.safety_events and area_data.safety_events.success:
            data = area_data.safety_events.data or {}
            total = data.get("total_events", 0)
            if total > 0:
                parts.append(f"Note: {total} safety event(s) recorded in this area. [Source: safety_incidents]")

        # Downtime (mention top reason if significant) - detailed mode only
        if detail_level == "detailed":
            if area_data.downtime_analysis and area_data.downtime_analysis.success:
                data = area_data.downtime_analysis.data or {}
                reasons = data.get("top_reasons", [])
                if reasons:
                    top = reasons[0]
                    duration = top.get("duration_minutes", 0)
                    if duration > 15:  # Only mention if > 15 min
                        reason = top.get("reason", "unplanned downtime")
                        parts.append(f"Top downtime: {reason} at {duration} minutes. [Source: downtime_events]")

        # Default if no data available
        if not parts:
            parts.append(f"{area_name} data is being refreshed. Check the dashboard for current status.")

        return " ".join(parts)

    def _extract_citations(self, area_data: AreaBriefingData) -> List[BriefingCitation]:
        """Extract all citations from area data."""
        citations = []
        for tool_data in [area_data.production_status, area_data.oee_data,
                          area_data.downtime_analysis, area_data.safety_events]:
            if tool_data and tool_data.citations:
                citations.extend(tool_data.citations)
        return citations

    def _create_error_section(self, area: Dict[str, Any]) -> BriefingSection:
        """Create an error section for a failed area."""
        return BriefingSection(
            section_type="area",
            title=area["name"],
            content=f"Unable to retrieve data for {area['name']}. Please check the dashboard.",
            area_id=area["id"],
            status=BriefingSectionStatus.FAILED,
            error_message="Area data retrieval failed",
            pause_point=True,
        )

    def _create_error_response(
        self,
        briefing_id: str,
        user_id: str,
        error_message: str,
    ) -> BriefingResponse:
        """Create error response when generation fails completely."""
        return BriefingResponse(
            id=briefing_id,
            title="Morning Briefing Unavailable",
            scope="error",
            user_id=user_id,
            sections=[
                BriefingSection(
                    section_type="error",
                    title="Unable to Generate Morning Briefing",
                    content=(
                        "We encountered an error generating your morning briefing. "
                        "Please try again in a few minutes. "
                        f"Error: {error_message}"
                    ),
                    status=BriefingSectionStatus.FAILED,
                    error_message=error_message,
                )
            ],
            metadata=BriefingResponseMetadata(
                completion_percentage=0,
                timed_out=False,
                tool_failures=["all"],
            ),
        )

    def _get_briefing_title(self) -> str:
        """Get the morning briefing title."""
        now = _utcnow()
        date_str = now.strftime("%A, %B %d")
        return f"Morning Briefing - {date_str}"

    async def process_qa_question(
        self,
        briefing_id: str,
        area_id: Optional[str],
        question: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Process a Q&A question during briefing pause.

        AC#5: Q&A response with citations

        Args:
            briefing_id: ID of the active briefing
            area_id: Optional area context for the question
            question: User's question text
            user_id: User ID

        Returns:
            Dict with answer, citations, and follow_up_prompt
        """
        # Import chat service for Q&A
        try:
            from app.services.agent.service import get_agent_service

            agent = get_agent_service()

            # Build context-aware prompt
            context = f"During morning briefing"
            if area_id:
                area = next((a for a in PRODUCTION_AREAS if a["id"] == area_id), None)
                if area:
                    context = f"During morning briefing, in {area['name']} section"

            # Query the agent
            result = await agent.query(
                query=question,
                user_id=user_id,
                context=context,
            )

            return {
                "answer": result.get("response", "I couldn't find an answer to that question."),
                "citations": result.get("citations", []),
                "follow_up_prompt": f"Anything else on {area['name'] if area_id else 'this topic'}?",
                "area_id": area_id,
            }

        except Exception as e:
            logger.error(f"Q&A processing failed: {e}")
            return {
                "answer": "I couldn't process that question. Please try again.",
                "citations": [],
                "follow_up_prompt": "Any other questions?",
                "area_id": area_id,
                "error": str(e),
            }


# Module-level singleton
_morning_briefing_service: Optional[MorningBriefingService] = None


def get_morning_briefing_service() -> MorningBriefingService:
    """
    Get the singleton MorningBriefingService instance.

    Returns:
        MorningBriefingService singleton instance
    """
    global _morning_briefing_service
    if _morning_briefing_service is None:
        _morning_briefing_service = MorningBriefingService()
    return _morning_briefing_service
