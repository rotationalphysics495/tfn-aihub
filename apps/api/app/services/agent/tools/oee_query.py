"""
OEE Query Tool (Story 5.4)

Tool for querying OEE (Overall Equipment Effectiveness) metrics
for assets, areas, or plant-wide with component breakdown.

AC#1: Asset-Level OEE Query - Returns OEE with A/P/Q breakdown and target comparison
AC#2: Area-Level OEE Query - Returns aggregated OEE with asset ranking
AC#3: Time Range Support - Parses natural language time ranges
AC#4: Target Comparison - Shows variance from target
AC#5: No Data Handling - Honest messaging when data is missing
AC#6: OEE Component Breakdown - Identifies biggest opportunity
AC#7: Tool Registration - Auto-discovered by agent framework
AC#8: Caching Support - Returns cache metadata (daily tier, 15 min TTL)
"""

import logging
import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional, Tuple, Type

from pydantic import BaseModel, Field

from app.models.agent import OEETrend
from app.services.agent.base import Citation, ManufacturingTool, ToolResult
from app.services.agent.cache import cached_tool
from app.services.agent.data_source import (
    DataResult,
    DataSourceError,
    get_data_source,
)

logger = logging.getLogger(__name__)

# Cache TTL constants (in seconds)
CACHE_TTL_DAILY = 900  # 15 minutes for daily/historical data

# Default target OEE percentage when no target is configured
DEFAULT_TARGET_OEE = 85.0


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)


# =============================================================================
# Input/Output Schemas
# =============================================================================


class OEEQueryInput(BaseModel):
    """
    Input schema for OEE Query tool.

    Story 5.4 AC#1-3: Asset/area/plant scope with time range
    """

    scope: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Asset name, area name, or 'plant' for plant-wide OEE"
    )
    time_range: Optional[str] = Field(
        default="yesterday",
        description="Time range like 'yesterday', 'last week', 'last 7 days', 'this month'"
    )


class OEEComponentBreakdown(BaseModel):
    """OEE component breakdown."""

    availability: float = Field(..., ge=0, le=100, description="Availability component (0-100)")
    performance: float = Field(..., ge=0, le=100, description="Performance component (0-100)")
    quality: float = Field(..., ge=0, le=100, description="Quality component (0-100)")


class OEEAssetResult(BaseModel):
    """OEE result for a single asset (used in area breakdown)."""

    name: str = Field(..., description="Asset name")
    oee: float = Field(..., ge=0, le=100, description="Overall OEE percentage")
    components: OEEComponentBreakdown = Field(..., description="OEE component breakdown")
    target: Optional[float] = Field(None, description="Target OEE if configured")
    variance: Optional[float] = Field(None, description="Variance from target (percentage points)")
    status: Optional[str] = Field(None, description="above_target, below_target, or no_target")


class OEEQueryOutput(BaseModel):
    """
    Output schema for OEE Query tool.

    Story 5.4 AC#1, AC#6: Complete OEE response with breakdown
    """

    scope_type: Literal["asset", "area", "plant"] = Field(
        ..., description="Type of scope queried"
    )
    scope_name: str = Field(..., description="Name of asset/area or 'Plant'")
    date_range: str = Field(..., description="Human-readable date range (e.g., 'Jan 2-8, 2026')")
    start_date: date = Field(..., description="Start date of query")
    end_date: date = Field(..., description="End date of query")

    # Main result
    overall_oee: float = Field(..., ge=0, le=100, description="Overall OEE percentage")
    components: OEEComponentBreakdown = Field(..., description="OEE component breakdown")

    # OEE formula display
    oee_formula: str = Field(
        default="OEE = Availability x Performance x Quality",
        description="OEE calculation formula"
    )

    # Target comparison (if available)
    target_oee: Optional[float] = Field(None, description="Target OEE percentage")
    variance_from_target: Optional[float] = Field(
        None, description="Variance from target (percentage points)"
    )
    target_status: Optional[str] = Field(
        None, description="above_target, below_target, or no_target"
    )

    # Area/Plant breakdown (if scope is area or plant)
    asset_breakdown: Optional[List[OEEAssetResult]] = Field(
        None, description="Per-asset OEE breakdown (for area/plant scope)"
    )
    bottom_performers: Optional[List[str]] = Field(
        None, description="Assets pulling down the average"
    )

    # Analysis
    biggest_opportunity: str = Field(
        ..., description="Which component has most improvement opportunity"
    )
    opportunity_insight: str = Field(
        ..., description="Actionable message about where to focus"
    )
    potential_improvement: float = Field(
        ..., description="Percentage points improvement potential"
    )

    # Metadata
    data_points: int = Field(..., ge=0, description="Number of days/records included")
    no_data: bool = Field(default=False, description="True if no OEE data available")


# =============================================================================
# OEE Query Tool
# =============================================================================


class OEEQueryTool(ManufacturingTool):
    """
    Query OEE (Overall Equipment Effectiveness) metrics.

    Story 5.4: OEE Query Tool Implementation

    Use this tool when a user asks about OEE, efficiency, or equipment effectiveness.
    Supports querying by asset name, area, or plant-wide.
    Returns OEE breakdown (Availability x Performance x Quality) with target comparison.

    Examples:
        - "What's the OEE for Grinder 5?"
        - "Show me OEE for the Grinding area"
        - "How was plant OEE last week?"
        - "Why is our efficiency low?"
    """

    name: str = "oee_query"
    description: str = (
        "Query OEE (Overall Equipment Effectiveness) metrics. "
        "Use when user asks about OEE, efficiency, or equipment effectiveness. "
        "Supports querying by asset name, area, or plant-wide. "
        "Returns OEE breakdown (Availability x Performance x Quality) with target comparison. "
        "Examples: 'What's the OEE for Grinder 5?', 'Show me OEE for the Grinding area', "
        "'How was plant OEE last week?', 'Why is our efficiency low?'"
    )
    args_schema: Type[BaseModel] = OEEQueryInput
    citations_required: bool = True

    # Story 5.8: Apply caching with daily tier (15 minute TTL)
    # OEE data is T-1 (yesterday) based, so daily tier is appropriate
    @cached_tool(tier="daily")
    async def _arun(
        self,
        scope: str,
        time_range: Optional[str] = "yesterday",
        **kwargs,
    ) -> ToolResult:
        """
        Execute OEE query and return structured results.

        AC#1-8: Complete OEE query implementation

        Args:
            scope: Asset name, area name, or 'plant' for plant-wide
            time_range: Natural language time range (default: yesterday)

        Returns:
            ToolResult with OEEQueryOutput data and citations
        """
        data_source = get_data_source()
        citations: List[Citation] = []

        logger.info(f"OEE query requested for scope='{scope}', time_range='{time_range}'")

        try:
            # Parse time range (AC#3)
            time_range = time_range or "yesterday"
            start_date, end_date = self._parse_time_range(time_range)
            date_range_str = self._format_date_range(start_date, end_date)

            logger.debug(f"Parsed time range: {start_date} to {end_date}")

            # Determine scope type and execute appropriate query
            scope_type = self._determine_scope_type(scope, data_source)

            if scope_type == "plant":
                return await self._query_plant_oee(
                    start_date, end_date, date_range_str, data_source, citations
                )
            elif scope_type == "area":
                return await self._query_area_oee(
                    scope, start_date, end_date, date_range_str, data_source, citations
                )
            else:  # asset
                return await self._query_asset_oee(
                    scope, start_date, end_date, date_range_str, data_source, citations
                )

        except DataSourceError as e:
            logger.error(f"Data source error during OEE query: {e}")
            return self._create_error_result(
                f"Unable to retrieve OEE data for '{scope}'. Please try again later."
            )
        except Exception as e:
            logger.exception(f"Unexpected error during OEE query for '{scope}': {e}")
            return self._create_error_result(
                "An unexpected error occurred while querying OEE. "
                "Please try again or contact support."
            )

    # =========================================================================
    # Query Methods
    # =========================================================================

    async def _query_asset_oee(
        self,
        asset_name: str,
        start_date: date,
        end_date: date,
        date_range_str: str,
        data_source,
        citations: List[Citation],
    ) -> ToolResult:
        """
        Query OEE for a single asset.

        AC#1: Asset-Level OEE Query
        AC#4: Target Comparison
        """
        # Find asset
        asset_result = await data_source.get_asset_by_name(asset_name)
        citations.append(self._result_to_citation(asset_result))

        if not asset_result.has_data:
            return self._no_data_response(
                f"asset '{asset_name}'", date_range_str, citations,
                message=f"Asset '{asset_name}' not found. Please check the asset name."
            )

        asset = asset_result.data
        asset_id = asset.id

        logger.debug(f"Found asset: {asset.name} (id: {asset_id})")

        # Get OEE data
        oee_result = await data_source.get_oee(asset_id, start_date, end_date)
        citations.append(self._result_to_citation(oee_result))

        if not oee_result.has_data:
            return self._no_data_response(
                f"asset '{asset.name}'", date_range_str, citations
            )

        # Get target (AC#4)
        target_result = await data_source.get_shift_target(asset_id)
        citations.append(self._result_to_citation(target_result))

        # Calculate averages
        oee_data = oee_result.data
        avg_oee = self._calculate_average_oee(oee_data)
        avg_avail = self._calculate_average(oee_data, "availability")
        avg_perf = self._calculate_average(oee_data, "performance")
        avg_qual = self._calculate_average(oee_data, "quality")

        components = OEEComponentBreakdown(
            availability=round(avg_avail, 1),
            performance=round(avg_perf, 1),
            quality=round(avg_qual, 1),
        )

        # Target comparison (AC#4)
        target_oee = None
        if target_result.has_data and target_result.data.target_oee is not None:
            target_oee = target_result.data.target_oee
        variance = round(avg_oee - target_oee, 1) if target_oee else None
        target_status = self._get_target_status(avg_oee, target_oee)

        # Analysis (AC#6)
        opportunity, insight, potential = self._analyze_opportunity(components, asset.name)

        output = OEEQueryOutput(
            scope_type="asset",
            scope_name=asset.name,
            date_range=date_range_str,
            start_date=start_date,
            end_date=end_date,
            overall_oee=round(avg_oee, 1),
            components=components,
            target_oee=target_oee,
            variance_from_target=variance,
            target_status=target_status,
            biggest_opportunity=opportunity,
            opportunity_insight=insight,
            potential_improvement=potential,
            data_points=len(oee_data),
        )

        # Generate follow-up questions
        follow_ups = self._generate_follow_ups(output)

        return self._create_success_result(
            data=output.model_dump(),
            citations=citations,
            metadata={
                "asset_id": asset_id,
                "asset_name": asset.name,
                "cache_tier": "daily",
                "ttl_seconds": CACHE_TTL_DAILY,
                "follow_up_questions": follow_ups,
                "query_timestamp": _utcnow().isoformat(),
            },
        )

    async def _query_area_oee(
        self,
        area: str,
        start_date: date,
        end_date: date,
        date_range_str: str,
        data_source,
        citations: List[Citation],
    ) -> ToolResult:
        """
        Query OEE for all assets in an area.

        AC#2: Area-Level OEE Query
        """
        # Get assets in area
        assets_result = await data_source.get_assets_by_area(area)
        citations.append(self._result_to_citation(assets_result))

        if not assets_result.has_data:
            return self._no_data_response(
                f"area '{area}'", date_range_str, citations,
                message=f"No assets found in area '{area}'. Please check the area name."
            )

        assets = assets_result.data
        logger.debug(f"Found {len(assets)} assets in area '{area}'")

        # Get OEE data for area
        oee_result = await data_source.get_oee_by_area(area, start_date, end_date)
        citations.append(self._result_to_citation(oee_result))

        if not oee_result.has_data:
            return self._no_data_response(f"area '{area}'", date_range_str, citations)

        # Group OEE data by asset and calculate per-asset averages
        asset_oee_map: Dict[str, List] = {}
        for metric in oee_result.data:
            asset_id = metric.asset_id
            if asset_id not in asset_oee_map:
                asset_oee_map[asset_id] = []
            asset_oee_map[asset_id].append(metric)

        # Build per-asset breakdown
        asset_breakdown: List[OEEAssetResult] = []
        all_oee_values: List[float] = []
        all_avail_values: List[float] = []
        all_perf_values: List[float] = []
        all_qual_values: List[float] = []

        for asset in assets:
            asset_metrics = asset_oee_map.get(asset.id, [])
            if not asset_metrics:
                continue

            avg_oee = self._calculate_average_oee(asset_metrics)
            avg_avail = self._calculate_average(asset_metrics, "availability")
            avg_perf = self._calculate_average(asset_metrics, "performance")
            avg_qual = self._calculate_average(asset_metrics, "quality")

            all_oee_values.append(avg_oee)
            all_avail_values.append(avg_avail)
            all_perf_values.append(avg_perf)
            all_qual_values.append(avg_qual)

            # Get target for this asset
            target_result = await data_source.get_shift_target(asset.id)
            target_oee = None
            if target_result.has_data and target_result.data.target_oee is not None:
                target_oee = target_result.data.target_oee

            variance = round(avg_oee - target_oee, 1) if target_oee else None
            status = self._get_target_status(avg_oee, target_oee)

            asset_breakdown.append(OEEAssetResult(
                name=asset.name,
                oee=round(avg_oee, 1),
                components=OEEComponentBreakdown(
                    availability=round(avg_avail, 1),
                    performance=round(avg_perf, 1),
                    quality=round(avg_qual, 1),
                ),
                target=target_oee,
                variance=variance,
                status=status,
            ))

        if not asset_breakdown:
            return self._no_data_response(f"area '{area}'", date_range_str, citations)

        # Sort by OEE (highest first) for ranking
        asset_breakdown.sort(key=lambda x: x.oee, reverse=True)

        # Calculate area-wide averages
        area_avg_oee = sum(all_oee_values) / len(all_oee_values) if all_oee_values else 0
        area_avg_avail = sum(all_avail_values) / len(all_avail_values) if all_avail_values else 0
        area_avg_perf = sum(all_perf_values) / len(all_perf_values) if all_perf_values else 0
        area_avg_qual = sum(all_qual_values) / len(all_qual_values) if all_qual_values else 0

        components = OEEComponentBreakdown(
            availability=round(area_avg_avail, 1),
            performance=round(area_avg_perf, 1),
            quality=round(area_avg_qual, 1),
        )

        # Identify bottom performers (below average)
        bottom_performers = [
            asset.name for asset in asset_breakdown
            if asset.oee < area_avg_oee
        ][-3:]  # Get up to 3 worst performers

        # Analysis (AC#6)
        opportunity, insight, potential = self._analyze_opportunity(components, area)

        output = OEEQueryOutput(
            scope_type="area",
            scope_name=area,
            date_range=date_range_str,
            start_date=start_date,
            end_date=end_date,
            overall_oee=round(area_avg_oee, 1),
            components=components,
            target_oee=DEFAULT_TARGET_OEE,  # Use default for area-level
            variance_from_target=round(area_avg_oee - DEFAULT_TARGET_OEE, 1),
            target_status=self._get_target_status(area_avg_oee, DEFAULT_TARGET_OEE),
            asset_breakdown=asset_breakdown,
            bottom_performers=bottom_performers if bottom_performers else None,
            biggest_opportunity=opportunity,
            opportunity_insight=insight,
            potential_improvement=potential,
            data_points=len(oee_result.data),
        )

        follow_ups = self._generate_follow_ups(output)

        return self._create_success_result(
            data=output.model_dump(),
            citations=citations,
            metadata={
                "area": area,
                "asset_count": len(asset_breakdown),
                "cache_tier": "daily",
                "ttl_seconds": CACHE_TTL_DAILY,
                "follow_up_questions": follow_ups,
                "query_timestamp": _utcnow().isoformat(),
            },
        )

    async def _query_plant_oee(
        self,
        start_date: date,
        end_date: date,
        date_range_str: str,
        data_source,
        citations: List[Citation],
    ) -> ToolResult:
        """
        Query plant-wide OEE.

        Similar to area query but for all assets.
        """
        # Get all assets
        assets_result = await data_source.get_all_assets()
        citations.append(self._result_to_citation(assets_result))

        if not assets_result.has_data:
            return self._no_data_response("plant", date_range_str, citations)

        assets = assets_result.data
        logger.debug(f"Found {len(assets)} assets in plant")

        # Get OEE data for each asset and aggregate
        all_oee_values: List[float] = []
        all_avail_values: List[float] = []
        all_perf_values: List[float] = []
        all_qual_values: List[float] = []
        asset_breakdown: List[OEEAssetResult] = []
        total_data_points = 0

        for asset in assets:
            oee_result = await data_source.get_oee(asset.id, start_date, end_date)
            if not oee_result.has_data:
                continue

            total_data_points += len(oee_result.data)

            avg_oee = self._calculate_average_oee(oee_result.data)
            avg_avail = self._calculate_average(oee_result.data, "availability")
            avg_perf = self._calculate_average(oee_result.data, "performance")
            avg_qual = self._calculate_average(oee_result.data, "quality")

            all_oee_values.append(avg_oee)
            all_avail_values.append(avg_avail)
            all_perf_values.append(avg_perf)
            all_qual_values.append(avg_qual)

            # Get target for this asset
            target_result = await data_source.get_shift_target(asset.id)
            target_oee = None
            if target_result.has_data and target_result.data.target_oee is not None:
                target_oee = target_result.data.target_oee

            variance = round(avg_oee - target_oee, 1) if target_oee else None
            status = self._get_target_status(avg_oee, target_oee)

            asset_breakdown.append(OEEAssetResult(
                name=asset.name,
                oee=round(avg_oee, 1),
                components=OEEComponentBreakdown(
                    availability=round(avg_avail, 1),
                    performance=round(avg_perf, 1),
                    quality=round(avg_qual, 1),
                ),
                target=target_oee,
                variance=variance,
                status=status,
            ))

        # Add a citation for the aggregate query
        citations.append(self._create_citation(
            source="supabase",
            query=f"Aggregated OEE for all assets from {start_date} to {end_date}",
            table="daily_summaries",
        ))

        if not asset_breakdown:
            return self._no_data_response("plant", date_range_str, citations)

        # Sort by OEE
        asset_breakdown.sort(key=lambda x: x.oee, reverse=True)

        # Calculate plant-wide averages
        plant_avg_oee = sum(all_oee_values) / len(all_oee_values) if all_oee_values else 0
        plant_avg_avail = sum(all_avail_values) / len(all_avail_values) if all_avail_values else 0
        plant_avg_perf = sum(all_perf_values) / len(all_perf_values) if all_perf_values else 0
        plant_avg_qual = sum(all_qual_values) / len(all_qual_values) if all_qual_values else 0

        components = OEEComponentBreakdown(
            availability=round(plant_avg_avail, 1),
            performance=round(plant_avg_perf, 1),
            quality=round(plant_avg_qual, 1),
        )

        # Identify bottom performers
        bottom_performers = [
            asset.name for asset in asset_breakdown
            if asset.oee < plant_avg_oee
        ][-3:]

        # Analysis
        opportunity, insight, potential = self._analyze_opportunity(components, "Plant")

        output = OEEQueryOutput(
            scope_type="plant",
            scope_name="Plant",
            date_range=date_range_str,
            start_date=start_date,
            end_date=end_date,
            overall_oee=round(plant_avg_oee, 1),
            components=components,
            target_oee=DEFAULT_TARGET_OEE,
            variance_from_target=round(plant_avg_oee - DEFAULT_TARGET_OEE, 1),
            target_status=self._get_target_status(plant_avg_oee, DEFAULT_TARGET_OEE),
            asset_breakdown=asset_breakdown,
            bottom_performers=bottom_performers if bottom_performers else None,
            biggest_opportunity=opportunity,
            opportunity_insight=insight,
            potential_improvement=potential,
            data_points=total_data_points,
        )

        follow_ups = self._generate_follow_ups(output)

        return self._create_success_result(
            data=output.model_dump(),
            citations=citations,
            metadata={
                "asset_count": len(asset_breakdown),
                "cache_tier": "daily",
                "ttl_seconds": CACHE_TTL_DAILY,
                "follow_up_questions": follow_ups,
                "query_timestamp": _utcnow().isoformat(),
            },
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _determine_scope_type(self, scope: str, data_source) -> str:
        """
        Determine if scope is asset, area, or plant.

        Returns 'plant', 'area', or 'asset' based on the scope string.
        """
        scope_lower = scope.lower().strip()

        # Check for plant-wide keywords
        if scope_lower in ["plant", "plant-wide", "all", "overall", "total", "factory"]:
            return "plant"

        # Check for common area names
        # This is a heuristic - areas typically end in common patterns
        area_keywords = ["area", "department", "line", "section", "zone"]
        for keyword in area_keywords:
            if keyword in scope_lower:
                return "area"

        # Default to asset - the query will determine if it's actually an area
        # if no asset is found but assets exist in that "area"
        return "asset"

    def _parse_time_range(self, time_range: str) -> Tuple[date, date]:
        """
        Parse natural language time range into dates.

        AC#3: Time Range Support
        - Default to yesterday (T-1) if not specified
        - Support various time expressions

        Args:
            time_range: Natural language time range

        Returns:
            Tuple of (start_date, end_date)
        """
        today = date.today()
        yesterday = today - timedelta(days=1)

        time_range_lower = time_range.lower().strip()

        if time_range_lower in ["yesterday", "t-1", ""]:
            return yesterday, yesterday

        elif time_range_lower in ["today", "t0", "now"]:
            return today, today

        elif time_range_lower in ["last week", "last 7 days", "past week", "previous week"]:
            return yesterday - timedelta(days=6), yesterday

        elif time_range_lower in ["this week"]:
            # Monday of current week to yesterday
            start_of_week = today - timedelta(days=today.weekday())
            return start_of_week, yesterday

        elif time_range_lower in ["last 30 days", "last month", "past month", "previous month"]:
            return yesterday - timedelta(days=29), yesterday

        elif time_range_lower in ["this month"]:
            # First of current month to yesterday
            first_of_month = today.replace(day=1)
            return first_of_month, yesterday

        elif time_range_lower in ["last 14 days", "past 2 weeks", "last 2 weeks"]:
            return yesterday - timedelta(days=13), yesterday

        # Try to parse specific date patterns (e.g., "January 5th", "Jan 5")
        parsed_date = self._try_parse_date(time_range_lower)
        if parsed_date:
            return parsed_date, parsed_date

        # Default to yesterday if we can't parse
        logger.warning(f"Could not parse time range '{time_range}', defaulting to yesterday")
        return yesterday, yesterday

    def _try_parse_date(self, date_str: str) -> Optional[date]:
        """Try to parse a specific date from a string."""
        today = date.today()

        # Month name patterns
        month_pattern = r"(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)"
        day_pattern = r"(\d{1,2})"

        # Try "Month Day" pattern
        match = re.search(f"{month_pattern}\\s*{day_pattern}", date_str, re.IGNORECASE)
        if match:
            month_str = match.group(1).lower()
            day = int(match.group(2))

            month_map = {
                "january": 1, "jan": 1,
                "february": 2, "feb": 2,
                "march": 3, "mar": 3,
                "april": 4, "apr": 4,
                "may": 5,
                "june": 6, "jun": 6,
                "july": 7, "jul": 7,
                "august": 8, "aug": 8,
                "september": 9, "sep": 9,
                "october": 10, "oct": 10,
                "november": 11, "nov": 11,
                "december": 12, "dec": 12,
            }

            month = month_map.get(month_str)
            if month:
                try:
                    # Assume current year if month is in the past or current month
                    year = today.year
                    if month > today.month:
                        year -= 1  # Assume previous year
                    return date(year, month, day)
                except ValueError:
                    pass

        return None

    def _format_date_range(self, start_date: date, end_date: date) -> str:
        """Format date range for display."""
        if start_date == end_date:
            return start_date.strftime("%b %d, %Y")

        if start_date.year == end_date.year:
            if start_date.month == end_date.month:
                return f"{start_date.strftime('%b %d')}-{end_date.strftime('%d')}, {start_date.year}"
            else:
                return f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}, {start_date.year}"
        else:
            return f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"

    def _calculate_average_oee(self, metrics: List) -> float:
        """Calculate average OEE from metrics list."""
        values = []
        for m in metrics:
            if m.oee_percentage is not None:
                val = float(m.oee_percentage) if isinstance(m.oee_percentage, Decimal) else m.oee_percentage
                values.append(val)
        return sum(values) / len(values) if values else 0

    def _calculate_average(self, metrics: List, field: str) -> float:
        """Calculate average of a field across metrics."""
        values = []
        for m in metrics:
            val = getattr(m, field, None)
            if val is not None:
                val = float(val) if isinstance(val, Decimal) else val
                values.append(val)
        return sum(values) / len(values) if values else 0

    def _get_target_status(self, oee: float, target: Optional[float]) -> str:
        """Determine status relative to target."""
        if target is None:
            return "no_target"
        elif oee >= target:
            return "above_target"
        else:
            return "below_target"

    def _analyze_opportunity(
        self,
        components: OEEComponentBreakdown,
        scope_name: str,
    ) -> Tuple[str, str, float]:
        """
        Analyze which OEE component has the most improvement opportunity.

        AC#6: OEE Component Breakdown

        Returns:
            Tuple of (biggest_opportunity, insight_message, potential_improvement)
        """
        gaps = {
            "availability": 100 - components.availability,
            "performance": 100 - components.performance,
            "quality": 100 - components.quality,
        }

        biggest = max(gaps, key=gaps.get)
        potential = gaps[biggest]

        insights = {
            "availability": (
                f"Availability ({components.availability}%) is your biggest gap for {scope_name}. "
                "Focus on reducing unplanned downtime and improving changeover times."
            ),
            "performance": (
                f"Performance ({components.performance}%) is holding back {scope_name}. "
                "Check for speed losses, minor stops, and cycle time variations."
            ),
            "quality": (
                f"Quality ({components.quality}%) needs attention for {scope_name}. "
                "Investigate scrap, rework, and first-pass yield issues."
            ),
        }

        return biggest, insights[biggest], round(potential, 1)

    def _no_data_response(
        self,
        scope: str,
        date_range: str,
        citations: List[Citation],
        message: Optional[str] = None,
    ) -> ToolResult:
        """
        Generate response when no data is available.

        AC#5: No Data Handling
        - Does NOT fabricate any values
        - Includes citation for query that returned no results
        """
        if message is None:
            message = f"No OEE data available for {scope} in {date_range}"

        return self._create_success_result(
            data={
                "no_data": True,
                "message": message,
                "scope": scope,
                "date_range": date_range,
            },
            citations=citations,
            metadata={
                "cache_tier": "daily",
                "ttl_seconds": CACHE_TTL_DAILY,
            },
        )

    def _generate_follow_ups(self, output: OEEQueryOutput) -> List[str]:
        """
        Generate context-aware follow-up questions.

        Args:
            output: The OEE query result

        Returns:
            List of suggested questions (max 3)
        """
        questions = []

        # Target-based questions
        if output.target_status == "below_target" and output.variance_from_target:
            questions.append(
                f"Why is {output.scope_name} {abs(output.variance_from_target):.1f}% below OEE target?"
            )

        # Component-based questions
        if output.biggest_opportunity == "availability":
            questions.append(f"What's causing downtime on {output.scope_name}?")
        elif output.biggest_opportunity == "performance":
            questions.append(f"What's slowing down {output.scope_name}?")
        elif output.biggest_opportunity == "quality":
            questions.append(f"What's causing quality issues on {output.scope_name}?")

        # Bottom performers (for area/plant)
        if output.bottom_performers and len(output.bottom_performers) > 0:
            questions.append(f"What's wrong with {output.bottom_performers[0]}?")

        # Always offer trend view
        questions.append(f"Show me {output.scope_name}'s OEE trend over time")

        # Return max 3 unique questions
        return list(dict.fromkeys(questions))[:3]

    def _result_to_citation(self, result: DataResult) -> Citation:
        """
        Convert DataResult to Citation.

        AC#6: Citation Compliance
        """
        return self._create_citation(
            source=result.source_name,
            query=result.query or f"Query on {result.table_name}",
            table=result.table_name,
        )
