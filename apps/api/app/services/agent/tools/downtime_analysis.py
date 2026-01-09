"""
Downtime Analysis Tool (Story 5.5)

Tool for analyzing downtime reasons and patterns with Pareto analysis.
Helps plant managers identify and address root causes of lost production time.

AC#1: Asset-Level Downtime Query - Returns total downtime, reasons ranked by duration
AC#2: Area-Level Downtime Query - Aggregates across all assets in area
AC#3: No Downtime Handling - Honest messaging when no downtime recorded
AC#4: Time Range Support - Parses natural language time ranges
AC#5: Pareto Analysis - 80/20 rule, cumulative percentages, vital few identification
AC#6: Safety Event Highlighting - Safety-related reasons flagged and shown first
AC#7: Tool Registration - Auto-discovered by agent framework
AC#8: Caching Support - Returns cache metadata (daily tier, 15 min TTL)
"""

import json
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional, Tuple, Type

from pydantic import BaseModel, Field

from app.services.agent.base import Citation, ManufacturingTool, ToolResult
from app.services.agent.data_source import (
    DataResult,
    DataSourceError,
    get_data_source,
)

logger = logging.getLogger(__name__)

# Cache TTL constants (in seconds)
CACHE_TTL_DAILY = 900  # 15 minutes for daily/historical data

# Safety-related keywords for event detection (case-insensitive)
SAFETY_KEYWORDS = [
    "safety",
    "safety issue",
    "safety stop",
    "emergency stop",
    "e-stop",
    "lockout",
    "tagout",
    "loto",
    "hazard",
    "injury",
]


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)


# =============================================================================
# Input/Output Schemas
# =============================================================================


class DowntimeAnalysisInput(BaseModel):
    """
    Input schema for Downtime Analysis tool.

    Story 5.5 AC#1-4: Asset/area scope with time range
    """

    scope: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Asset name or area name to analyze downtime for"
    )
    time_range: Optional[str] = Field(
        default="yesterday",
        description="Time range like 'yesterday', 'last week', 'last 7 days', 'this week'"
    )


class DowntimeReason(BaseModel):
    """Single downtime reason in Pareto analysis."""

    reason_code: str = Field(..., description="Downtime reason code or description")
    total_minutes: int = Field(..., ge=0, description="Total minutes of downtime")
    percentage: float = Field(..., ge=0, le=100, description="Percentage of total downtime")
    cumulative_percentage: float = Field(
        ..., ge=0, le=100, description="Cumulative percentage (running total)"
    )
    is_vital_few: bool = Field(
        default=False, description="Part of vital few (causes 80% of downtime)"
    )
    is_safety_related: bool = Field(default=False, description="Safety-related downtime")
    severity: Optional[str] = Field(None, description="Severity level if available")
    contributing_assets: Optional[List[str]] = Field(
        None, description="Assets contributing to this reason (for area queries)"
    )


class AssetDowntimeBreakdown(BaseModel):
    """Downtime breakdown for a single asset (used in area queries)."""

    asset_name: str = Field(..., description="Asset name")
    total_minutes: int = Field(..., ge=0, description="Total downtime in minutes")
    top_reason: Optional[str] = Field(None, description="Top downtime reason")
    top_reason_minutes: Optional[int] = Field(None, description="Minutes from top reason")
    reason_count: int = Field(default=0, description="Number of unique reasons")


class DowntimeAnalysisOutput(BaseModel):
    """
    Output schema for Downtime Analysis tool.

    Story 5.5 AC#1, AC#5: Complete downtime response with Pareto analysis
    """

    scope_type: Literal["asset", "area"] = Field(
        ..., description="Type of scope queried"
    )
    scope_name: str = Field(..., description="Name of asset or area")
    date_range: str = Field(
        ..., description="Human-readable date range (e.g., 'Jan 2-8, 2026')"
    )
    start_date: date = Field(..., description="Start date of query")
    end_date: date = Field(..., description="End date of query")

    # Downtime summary
    total_downtime_minutes: int = Field(..., ge=0, description="Total downtime in minutes")
    total_downtime_hours: float = Field(..., ge=0, description="Total downtime in hours")
    uptime_percentage: float = Field(
        ..., ge=0, le=100, description="Uptime percentage (0-100)"
    )

    # Pareto analysis
    reasons: List[DowntimeReason] = Field(
        default_factory=list, description="Downtime reasons sorted by duration"
    )
    threshold_80_index: Optional[int] = Field(
        None, description="Index where cumulative percentage >= 80%"
    )
    top_reasons_summary: str = Field(
        ..., description="Summary of top reasons (e.g., '3 reasons account for 82%')"
    )

    # Vital few analysis
    vital_few_reasons: List[str] = Field(
        default_factory=list, description="Reason codes causing 80% of downtime"
    )
    vital_few_percentage: float = Field(
        default=0, description="Percentage of downtime from vital few"
    )

    # Area breakdown (if scope is area)
    asset_breakdown: Optional[List[AssetDowntimeBreakdown]] = Field(
        None, description="Per-asset downtime breakdown (for area scope)"
    )
    worst_asset: Optional[str] = Field(
        None, description="Asset with most downtime in area"
    )

    # Actionable insight
    insight: str = Field(
        ..., description="Actionable message about where to focus"
    )

    # Safety summary
    safety_events_count: int = Field(default=0, description="Number of safety events")
    safety_downtime_minutes: int = Field(
        default=0, description="Total safety-related downtime"
    )
    safety_reasons: List[str] = Field(
        default_factory=list, description="Safety-related reason codes"
    )

    # Metadata
    data_points: int = Field(..., ge=0, description="Number of days/records included")
    no_downtime: bool = Field(default=False, description="True if no downtime recorded")


# =============================================================================
# Downtime Analysis Tool
# =============================================================================


class DowntimeAnalysisTool(ManufacturingTool):
    """
    Analyze downtime reasons and patterns for assets or areas.

    Story 5.5: Downtime Analysis Tool Implementation

    Use this tool when a user asks about downtime, why equipment was down,
    downtime reasons, downtime patterns, or Pareto analysis of downtime.
    Returns Pareto distribution of downtime reasons ranked by duration.

    Examples:
        - "Why was Grinder 5 down yesterday?"
        - "What are the top downtime reasons for the Grinding area?"
        - "Show me downtime patterns for this week"
        - "What's causing the most downtime?"
    """

    name: str = "downtime_analysis"
    description: str = (
        "Analyze downtime reasons and patterns. "
        "Use when user asks about downtime, why equipment was down, "
        "downtime reasons, or Pareto analysis. "
        "Supports querying by asset name or area. "
        "Returns Pareto distribution of downtime reasons ranked by duration. "
        "Examples: 'Why was Grinder 5 down?', 'What are the top downtime reasons?', "
        "'Show me downtime for the Grinding area', 'What caused us to lose time yesterday?'"
    )
    args_schema: Type[BaseModel] = DowntimeAnalysisInput
    citations_required: bool = True

    async def _arun(
        self,
        scope: str,
        time_range: Optional[str] = "yesterday",
        **kwargs,
    ) -> ToolResult:
        """
        Execute downtime analysis and return structured results.

        AC#1-8: Complete downtime analysis implementation

        Args:
            scope: Asset name or area name to analyze
            time_range: Natural language time range (default: yesterday)

        Returns:
            ToolResult with DowntimeAnalysisOutput data and citations
        """
        data_source = get_data_source()
        citations: List[Citation] = []

        logger.info(f"Downtime analysis requested for scope='{scope}', time_range='{time_range}'")

        try:
            # Parse time range (AC#4)
            time_range = time_range or "yesterday"
            start_date, end_date = self._parse_time_range(time_range)
            date_range_str = self._format_date_range(start_date, end_date)

            logger.debug(f"Parsed time range: {start_date} to {end_date}")

            # Determine scope type
            scope_type = self._determine_scope_type(scope, data_source)

            if scope_type == "area":
                return await self._analyze_area_downtime(
                    scope, start_date, end_date, date_range_str, data_source, citations
                )
            else:  # asset
                return await self._analyze_asset_downtime(
                    scope, start_date, end_date, date_range_str, data_source, citations
                )

        except DataSourceError as e:
            logger.error(f"Data source error during downtime analysis: {e}")
            return self._create_error_result(
                f"Unable to retrieve downtime data for '{scope}'. Please try again later."
            )
        except Exception as e:
            logger.exception(f"Unexpected error during downtime analysis for '{scope}': {e}")
            return self._create_error_result(
                "An unexpected error occurred while analyzing downtime. "
                "Please try again or contact support."
            )

    # =========================================================================
    # Query Methods
    # =========================================================================

    async def _analyze_asset_downtime(
        self,
        asset_name: str,
        start_date: date,
        end_date: date,
        date_range_str: str,
        data_source,
        citations: List[Citation],
    ) -> ToolResult:
        """
        Analyze downtime for a single asset.

        AC#1: Asset-Level Downtime Query
        AC#3: No Downtime Handling
        AC#5: Pareto Analysis
        AC#6: Safety Event Highlighting
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

        # Get downtime data from daily_summaries
        downtime_result = await data_source.get_downtime(asset_id, start_date, end_date)
        citations.append(self._result_to_citation(downtime_result))

        # Get OEE data which includes downtime_reasons JSON field
        oee_result = await data_source.get_oee(asset_id, start_date, end_date)
        citations.append(self._result_to_citation(oee_result))

        # Aggregate downtime reasons from OEE metrics (which has full daily_summaries data)
        reasons_aggregated = self._aggregate_downtime_reasons_from_oee(oee_result.data or [])

        # Calculate total downtime
        total_downtime_minutes = sum(reasons_aggregated.values())

        if total_downtime_minutes == 0:
            # AC#3: No downtime handling
            return self._no_downtime_response(
                asset.name, date_range_str, start_date, end_date, citations
            )

        # Calculate Pareto distribution (AC#5)
        pareto_reasons, threshold_index = self._calculate_pareto(reasons_aggregated)

        # Identify safety-related downtime (AC#6)
        safety_minutes, safety_reasons = self._extract_safety_downtime(pareto_reasons)

        # Calculate uptime percentage
        days_in_range = (end_date - start_date).days + 1
        planned_minutes = days_in_range * 24 * 60  # Assume 24-hour operation
        uptime_pct = round((1 - total_downtime_minutes / planned_minutes) * 100, 1)

        # Calculate total downtime hours
        total_hours = round(total_downtime_minutes / 60, 2)

        # Find vital few (AC#5)
        vital_few = [r.reason_code for r in pareto_reasons if r.is_vital_few]
        vital_few_pct = sum(r.percentage for r in pareto_reasons if r.is_vital_few)

        # Generate insight
        insight = self._generate_insight(pareto_reasons, threshold_index, asset.name)
        top_summary = self._generate_top_reasons_summary(pareto_reasons, threshold_index)

        output = DowntimeAnalysisOutput(
            scope_type="asset",
            scope_name=asset.name,
            date_range=date_range_str,
            start_date=start_date,
            end_date=end_date,
            total_downtime_minutes=total_downtime_minutes,
            total_downtime_hours=total_hours,
            uptime_percentage=uptime_pct,
            reasons=pareto_reasons,
            threshold_80_index=threshold_index,
            top_reasons_summary=top_summary,
            vital_few_reasons=vital_few,
            vital_few_percentage=round(vital_few_pct, 1),
            insight=insight,
            safety_events_count=len(safety_reasons),
            safety_downtime_minutes=safety_minutes,
            safety_reasons=safety_reasons,
            data_points=len(oee_result.data or []),
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

    async def _analyze_area_downtime(
        self,
        area: str,
        start_date: date,
        end_date: date,
        date_range_str: str,
        data_source,
        citations: List[Citation],
    ) -> ToolResult:
        """
        Analyze downtime for all assets in an area.

        AC#2: Area-Level Downtime Query
        AC#3: No Downtime Handling
        AC#5: Pareto Analysis
        AC#6: Safety Event Highlighting
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

        # Aggregate downtime across all assets
        all_reasons: Dict[str, int] = defaultdict(int)
        reason_contributors: Dict[str, List[str]] = defaultdict(list)
        asset_breakdowns: List[AssetDowntimeBreakdown] = []
        total_data_points = 0

        for asset in assets:
            # Get OEE data which includes downtime_reasons
            oee_result = await data_source.get_oee(asset.id, start_date, end_date)

            asset_reasons = self._aggregate_downtime_reasons_from_oee(oee_result.data or [])
            total_data_points += len(oee_result.data or [])

            asset_total = sum(asset_reasons.values())

            if asset_total > 0:
                # Track contribution per reason
                for reason, minutes in asset_reasons.items():
                    all_reasons[reason] += minutes
                    if asset.name not in reason_contributors[reason]:
                        reason_contributors[reason].append(asset.name)

                # Find top reason for this asset
                top_reason = max(asset_reasons.items(), key=lambda x: x[1]) if asset_reasons else (None, 0)

                asset_breakdowns.append(AssetDowntimeBreakdown(
                    asset_name=asset.name,
                    total_minutes=asset_total,
                    top_reason=top_reason[0],
                    top_reason_minutes=top_reason[1],
                    reason_count=len(asset_reasons),
                ))

        # Add citation for aggregate query
        citations.append(self._create_citation(
            source="supabase",
            query=f"Aggregated downtime for area '{area}' from {start_date} to {end_date}",
            table="daily_summaries",
        ))

        # Calculate total downtime
        total_downtime_minutes = sum(all_reasons.values())

        if total_downtime_minutes == 0:
            # AC#3: No downtime handling
            return self._no_downtime_response(
                f"area '{area}'", date_range_str, start_date, end_date, citations
            )

        # Sort asset breakdowns by downtime
        asset_breakdowns.sort(key=lambda x: x.total_minutes, reverse=True)
        worst_asset = asset_breakdowns[0].asset_name if asset_breakdowns else None

        # Calculate Pareto distribution (AC#5)
        pareto_reasons, threshold_index = self._calculate_pareto(all_reasons)

        # Add contributing assets to each reason
        for reason in pareto_reasons:
            reason.contributing_assets = reason_contributors.get(reason.reason_code, [])

        # Identify safety-related downtime (AC#6)
        safety_minutes, safety_reasons = self._extract_safety_downtime(pareto_reasons)

        # Calculate uptime percentage
        days_in_range = (end_date - start_date).days + 1
        planned_minutes = days_in_range * 24 * 60 * len(assets)  # Per-asset planned time
        uptime_pct = round((1 - total_downtime_minutes / planned_minutes) * 100, 1) if planned_minutes > 0 else 100.0

        # Calculate total downtime hours
        total_hours = round(total_downtime_minutes / 60, 2)

        # Find vital few (AC#5)
        vital_few = [r.reason_code for r in pareto_reasons if r.is_vital_few]
        vital_few_pct = sum(r.percentage for r in pareto_reasons if r.is_vital_few)

        # Generate insight (mention worst asset)
        insight = self._generate_insight(pareto_reasons, threshold_index, area, worst_asset)
        top_summary = self._generate_top_reasons_summary(pareto_reasons, threshold_index)

        output = DowntimeAnalysisOutput(
            scope_type="area",
            scope_name=area,
            date_range=date_range_str,
            start_date=start_date,
            end_date=end_date,
            total_downtime_minutes=total_downtime_minutes,
            total_downtime_hours=total_hours,
            uptime_percentage=uptime_pct,
            reasons=pareto_reasons,
            threshold_80_index=threshold_index,
            top_reasons_summary=top_summary,
            vital_few_reasons=vital_few,
            vital_few_percentage=round(vital_few_pct, 1),
            asset_breakdown=asset_breakdowns,
            worst_asset=worst_asset,
            insight=insight,
            safety_events_count=len(safety_reasons),
            safety_downtime_minutes=safety_minutes,
            safety_reasons=safety_reasons,
            data_points=total_data_points,
        )

        # Generate follow-up questions
        follow_ups = self._generate_follow_ups(output)

        return self._create_success_result(
            data=output.model_dump(),
            citations=citations,
            metadata={
                "area": area,
                "asset_count": len(assets),
                "cache_tier": "daily",
                "ttl_seconds": CACHE_TTL_DAILY,
                "follow_up_questions": follow_ups,
                "query_timestamp": _utcnow().isoformat(),
            },
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _aggregate_downtime_reasons_from_oee(self, oee_metrics: List) -> Dict[str, int]:
        """
        Aggregate downtime reasons from OEE metrics.

        The daily_summaries table has a downtime_reasons JSON field with
        reason codes and their durations. Falls back to total downtime_minutes
        if no reason breakdown is available.
        """
        aggregated: Dict[str, int] = defaultdict(int)

        for metric in oee_metrics:
            # Get downtime_reasons from the OEEMetrics model
            reasons_data = getattr(metric, 'downtime_reasons', None)

            if reasons_data and isinstance(reasons_data, dict):
                # Aggregate reason codes from the breakdown
                for reason_code, minutes in reasons_data.items():
                    if minutes and minutes > 0:
                        aggregated[reason_code] += int(minutes)
            else:
                # Fall back to using total downtime_minutes without reason breakdown
                downtime = getattr(metric, 'downtime_minutes', 0) or 0
                if downtime > 0:
                    aggregated["Unspecified Downtime"] += downtime

        return dict(aggregated)

    def _calculate_pareto(
        self, reasons: Dict[str, int]
    ) -> Tuple[List[DowntimeReason], Optional[int]]:
        """
        Calculate Pareto distribution from reason aggregates.

        AC#5: Pareto Analysis
        - Sort by descending duration
        - Calculate percentage and cumulative percentage
        - Identify threshold (80% cumulative)
        - Mark vital few
        """
        if not reasons:
            return [], None

        # Sort by descending minutes
        sorted_reasons = sorted(reasons.items(), key=lambda x: x[1], reverse=True)

        total_minutes = sum(m for _, m in sorted_reasons)
        if total_minutes == 0:
            return [], None

        pareto_list: List[DowntimeReason] = []
        cumulative = 0.0
        threshold_index = None

        for i, (reason_code, minutes) in enumerate(sorted_reasons):
            percentage = (minutes / total_minutes) * 100
            cumulative += percentage

            is_safety = self._is_safety_related(reason_code)

            pareto_list.append(DowntimeReason(
                reason_code=reason_code,
                total_minutes=minutes,
                percentage=round(percentage, 1),
                cumulative_percentage=round(cumulative, 1),
                is_vital_few=cumulative <= 80.0 or (threshold_index is None and i == 0),
                is_safety_related=is_safety,
            ))

            if threshold_index is None and cumulative >= 80.0:
                threshold_index = i

        # Move safety events to top while preserving Pareto order within groups (AC#6)
        safety_first = [r for r in pareto_list if r.is_safety_related]
        non_safety = [r for r in pareto_list if not r.is_safety_related]
        pareto_list = safety_first + non_safety

        return pareto_list, threshold_index

    def _is_safety_related(self, reason_code: str) -> bool:
        """Check if a reason code is safety-related."""
        if not reason_code:
            return False
        reason_lower = reason_code.lower()
        return any(keyword in reason_lower for keyword in SAFETY_KEYWORDS)

    def _extract_safety_downtime(
        self, reasons: List[DowntimeReason]
    ) -> Tuple[int, List[str]]:
        """Extract safety-related downtime from Pareto analysis."""
        safety_minutes = 0
        safety_reasons = []
        for r in reasons:
            if r.is_safety_related:
                safety_minutes += r.total_minutes
                safety_reasons.append(r.reason_code)
        return safety_minutes, safety_reasons

    def _generate_insight(
        self,
        reasons: List[DowntimeReason],
        threshold_index: Optional[int],
        scope_name: str,
        worst_asset: Optional[str] = None,
    ) -> str:
        """Generate actionable insight based on Pareto analysis."""
        if not reasons:
            return "No downtime data to analyze."

        if len(reasons) == 1:
            return f"All downtime is from {reasons[0].reason_code}. Focus investigation here."

        # Get non-safety vital few reasons for insight
        vital_few = [r for r in reasons if r.is_vital_few and not r.is_safety_related]

        if threshold_index is not None and vital_few:
            top_reasons = [r.reason_code for r in vital_few[:3]]
            pct = sum(r.percentage for r in vital_few)
            insight = f"Focus on {', '.join(top_reasons)} to address {pct:.0f}% of downtime."

            if worst_asset:
                insight += f" {worst_asset} is your biggest opportunity."

            return insight

        # Default to top reason
        top_reason = reasons[0]
        insight = f"{top_reason.reason_code} is your biggest issue at {top_reason.percentage:.0f}% of total downtime."

        if worst_asset:
            insight += f" Start with {worst_asset}."

        return insight

    def _generate_top_reasons_summary(
        self,
        reasons: List[DowntimeReason],
        threshold_index: Optional[int],
    ) -> str:
        """Generate summary of top reasons."""
        if not reasons:
            return "No downtime reasons found."

        if threshold_index is not None:
            count = threshold_index + 1
            # Find cumulative at threshold
            pct = 0
            for i, r in enumerate(reasons):
                if i <= threshold_index:
                    pct += r.percentage
            return f"{count} reason{'s' if count > 1 else ''} account{'s' if count == 1 else ''} for {pct:.0f}% of downtime"

        return f"{len(reasons)} unique downtime reasons identified"

    def _no_downtime_response(
        self,
        scope: str,
        date_range: str,
        start_date: date,
        end_date: date,
        citations: List[Citation],
    ) -> ToolResult:
        """
        Generate response when no downtime found.

        AC#3: No Downtime Handling
        - Shows uptime percentage (100%)
        - Congratulates on good performance
        - Does NOT fabricate any values
        """
        output = DowntimeAnalysisOutput(
            scope_type="asset" if "asset" in scope.lower() else "area",
            scope_name=scope,
            date_range=date_range,
            start_date=start_date,
            end_date=end_date,
            total_downtime_minutes=0,
            total_downtime_hours=0.0,
            uptime_percentage=100.0,
            reasons=[],
            threshold_80_index=None,
            top_reasons_summary="No downtime reasons - excellent!",
            vital_few_reasons=[],
            vital_few_percentage=0,
            insight=f"Great news! {scope} had no recorded downtime in {date_range}.",
            safety_events_count=0,
            safety_downtime_minutes=0,
            safety_reasons=[],
            data_points=0,
            no_downtime=True,
        )

        return self._create_success_result(
            data={
                **output.model_dump(),
                "message": f"Great news! {scope} had no recorded downtime in {date_range}.",
                "congratulations": True,
            },
            citations=citations,
            metadata={
                "cache_tier": "daily",
                "ttl_seconds": CACHE_TTL_DAILY,
            },
        )

    def _no_data_response(
        self,
        scope: str,
        date_range: str,
        citations: List[Citation],
        message: Optional[str] = None,
    ) -> ToolResult:
        """
        Generate response when asset/area not found.

        AC#3: Honest messaging when data is missing
        - Does NOT fabricate any values
        - Includes citation for query that returned no results
        """
        if message is None:
            message = f"No downtime data available for {scope} in {date_range}"

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

    def _generate_follow_ups(self, output: DowntimeAnalysisOutput) -> List[str]:
        """
        Generate context-aware follow-up questions.

        Args:
            output: The downtime analysis result

        Returns:
            List of suggested questions (max 3)
        """
        questions = []

        # Safety-related questions
        if output.safety_events_count > 0:
            questions.append(f"Tell me more about the safety events on {output.scope_name}")

        # Top reason drill-down
        if output.reasons and len(output.reasons) > 0:
            top_reason = output.reasons[0].reason_code
            questions.append(f"Show me {top_reason} trends over the past month")

        # OEE correlation
        if output.uptime_percentage < 90:
            questions.append(f"What's the OEE for {output.scope_name}?")

        # Area drill-down
        if output.scope_type == "area" and output.worst_asset:
            questions.append(f"Why was {output.worst_asset} down?")

        # Comparison
        questions.append(f"How does {output.scope_name}'s downtime compare to last week?")

        return questions[:3]

    def _determine_scope_type(self, scope: str, data_source) -> str:
        """
        Determine if scope is asset or area.

        Returns 'area' or 'asset' based on the scope string.
        """
        scope_lower = scope.lower().strip()

        # Check for common area names/patterns
        area_keywords = [
            "area", "department", "line", "section", "zone",
            "grinding", "packaging", "assembly", "machining", "welding",
            "painting", "finishing", "fabrication",
        ]

        for keyword in area_keywords:
            if keyword in scope_lower:
                return "area"

        # Default to asset
        return "asset"

    def _parse_time_range(self, time_range: str) -> Tuple[date, date]:
        """
        Parse natural language time range into dates.

        AC#4: Time Range Support
        - Default to yesterday (T-1) if not specified
        - Support various time expressions
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

        # Default to yesterday if we can't parse
        logger.warning(f"Could not parse time range '{time_range}', defaulting to yesterday")
        return yesterday, yesterday

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

    def _result_to_citation(self, result: DataResult) -> Citation:
        """
        Convert DataResult to Citation.

        AC#1: Citation Compliance
        """
        return self._create_citation(
            source=result.source_name,
            query=result.query or f"Query on {result.table_name}",
            table=result.table_name,
        )
