"""
Production Status Tool (Story 5.6)

Tool for querying real-time production status across assets vs targets.
Helps plant managers see at a glance how production is tracking against targets.

AC#1: Plant-Wide Production Status - Returns output vs target, variance, status for all assets
AC#2: Area-Filtered Production Status - Filters to assets in a specific area with totals
AC#3: Data Freshness Warning - Warns when data is stale (>30 minutes old)
AC#4: Status Indicators - ahead/on-track/behind based on 5% thresholds
AC#5: Summary Statistics - Total assets, counts by status, overall variance
AC#6: No Live Data Handling - Honest messaging when no data available
AC#7: Tool Registration - Auto-discovered by agent framework
AC#8: Caching Support - Returns cache metadata (live tier, 60 second TTL)
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple, Type

from pydantic import BaseModel, Field

from app.services.agent.base import Citation, ManufacturingTool, ToolResult
from app.services.agent.cache import cached_tool
from app.services.agent.data_source import (
    DataResult,
    DataSourceError,
    get_data_source,
)

logger = logging.getLogger(__name__)

# Cache TTL constants (in seconds)
CACHE_TTL_LIVE = 60  # 60 seconds for live data

# Status thresholds
AHEAD_THRESHOLD = 5.0   # >= +5% = ahead
BEHIND_THRESHOLD = -5.0  # <= -5% = behind

# Data freshness threshold
STALE_MINUTES = 30  # Data older than 30 minutes triggers warning


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)


# =============================================================================
# Input/Output Schemas
# =============================================================================


class ProductionStatusInput(BaseModel):
    """
    Input schema for Production Status tool.

    Story 5.6 AC#1-2: Optional area filter
    """

    area: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Area name to filter by (e.g., 'Grinding'). If not specified, shows all assets."
    )


class AssetProductionStatus(BaseModel):
    """Production status for a single asset."""

    asset_name: str = Field(..., description="Asset name")
    area: str = Field(..., description="Plant area")
    current_output: int = Field(..., ge=0, description="Current production count")
    shift_target: int = Field(..., ge=0, description="Target production count for shift")
    variance_units: int = Field(..., description="Units variance from target (can be negative)")
    variance_percent: float = Field(..., description="Percentage variance from target")
    status: Literal["ahead", "on_track", "behind"] = Field(
        ..., description="Status indicator: ahead/on_track/behind"
    )
    status_color: str = Field(..., description="Suggested color: green/yellow/red")
    snapshot_time: datetime = Field(..., description="When snapshot was taken")
    is_stale: bool = Field(default=False, description="True if >30 min old")


class ProductionStatusSummary(BaseModel):
    """Summary statistics for production status."""

    total_assets: int = Field(..., ge=0, description="Total number of assets")
    ahead_count: int = Field(..., ge=0, description="Assets ahead of target")
    on_track_count: int = Field(..., ge=0, description="Assets on track")
    behind_count: int = Field(..., ge=0, description="Assets behind target")
    total_output: int = Field(..., ge=0, description="Sum of all output")
    total_target: int = Field(..., ge=0, description="Sum of all targets")
    total_variance_units: int = Field(..., description="Total variance in units")
    total_variance_percent: float = Field(..., description="Total variance percentage")
    assets_needing_attention: List[str] = Field(
        default_factory=list, description="Names of assets behind target (up to 5)"
    )


class ProductionStatusOutput(BaseModel):
    """
    Output schema for Production Status tool.

    Story 5.6 AC#1, AC#5: Complete production status response
    """

    scope: str = Field(..., description="'all' or area name")
    timestamp: datetime = Field(..., description="When this query was run")
    data_freshness: str = Field(
        ..., description="Freshness status: 'live', 'stale (X min old)', etc."
    )
    has_stale_warning: bool = Field(
        default=False, description="True if data freshness warning should be shown"
    )
    stale_warning_message: Optional[str] = Field(
        None, description="Warning message if data is stale"
    )

    # Summary
    summary: ProductionStatusSummary = Field(..., description="Summary statistics")

    # Asset details (sorted by variance, worst first)
    assets: List[AssetProductionStatus] = Field(
        default_factory=list, description="Per-asset status sorted by variance"
    )

    # Area totals (if area-filtered)
    area_output: Optional[int] = Field(
        None, description="Total output for area (if area-filtered)"
    )
    area_target: Optional[int] = Field(
        None, description="Total target for area (if area-filtered)"
    )
    area_variance_percent: Optional[float] = Field(
        None, description="Area variance percentage (if area-filtered)"
    )


# =============================================================================
# Production Status Tool
# =============================================================================


class ProductionStatusTool(ManufacturingTool):
    """
    Get real-time production status vs targets.

    Story 5.6: Production Status Tool Implementation

    Use this tool when a user asks about current production, how they're doing today,
    or wants to know output vs target for assets.
    Returns current output, target, variance, and status for each asset.

    Examples:
        - "How are we doing today?"
        - "What's our production status?"
        - "How is the Grinding area tracking?"
        - "Which machines are behind?"
    """

    name: str = "production_status"
    description: str = (
        "Get real-time production status vs targets. "
        "Use when user asks about current production, how they're doing today, "
        "or wants to know output vs target for assets. "
        "Returns current output, target, variance, and status for each asset. "
        "Examples: 'How are we doing today?', 'What's our production status?', "
        "'How is the Grinding area tracking?', 'Which machines are behind?'"
    )
    args_schema: Type[BaseModel] = ProductionStatusInput
    citations_required: bool = True

    # Story 5.8: Apply caching with live tier (60 second TTL)
    # Production status is real-time data, so live tier is appropriate
    @cached_tool(tier="live")
    async def _arun(
        self,
        area: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        """
        Execute production status query and return structured results.

        AC#1-8: Complete production status implementation

        Args:
            area: Optional area name to filter by

        Returns:
            ToolResult with ProductionStatusOutput data and citations
        """
        data_source = get_data_source()
        citations: List[Citation] = []

        logger.info(f"Production status requested for area='{area or 'all'}'")

        try:
            # Get live snapshots (AC#1, AC#2)
            if area:
                snapshots_result = await data_source.get_live_snapshots_by_area(area)
            else:
                snapshots_result = await data_source.get_all_live_snapshots()
            citations.append(self._result_to_citation(snapshots_result))

            if not snapshots_result.has_data:
                return self._no_data_response(area, citations)

            # Get shift targets
            targets_result = await data_source.get_all_shift_targets()
            citations.append(self._result_to_citation(targets_result))

            # Build targets map for quick lookup
            targets_map: Dict[str, Any] = {}
            if targets_result.data:
                for target in targets_result.data:
                    targets_map[target.asset_id] = target

            # Process each asset snapshot
            assets: List[AssetProductionStatus] = []
            for snapshot in snapshots_result.data:
                asset_status = self._process_snapshot(snapshot, targets_map)
                if asset_status:
                    assets.append(asset_status)

            if not assets:
                return self._no_data_response(area, citations)

            # Sort by variance (worst first) - most negative at top
            assets.sort(key=lambda x: x.variance_percent)

            # Check for stale data (AC#3)
            has_stale, stale_message, freshness = self._check_data_freshness(assets)

            # Calculate summary (AC#5)
            summary = self._calculate_summary(assets)

            # Build output
            output = ProductionStatusOutput(
                scope=area or "all",
                timestamp=_utcnow(),
                data_freshness=freshness,
                has_stale_warning=has_stale,
                stale_warning_message=stale_message,
                summary=summary,
                assets=assets,
            )

            # Add area totals if filtered (AC#2)
            if area and assets:
                output.area_output = sum(a.current_output for a in assets)
                output.area_target = sum(a.shift_target for a in assets)
                if output.area_target > 0:
                    output.area_variance_percent = round(
                        (output.area_output - output.area_target) / output.area_target * 100, 1
                    )

            # Generate follow-up questions
            follow_ups = self._generate_follow_ups(output)

            return self._create_success_result(
                data=output.model_dump(),
                citations=citations,
                metadata={
                    "cache_tier": "live",
                    "ttl_seconds": CACHE_TTL_LIVE,
                    "follow_up_questions": follow_ups,
                    "query_timestamp": _utcnow().isoformat(),
                },
            )

        except DataSourceError as e:
            logger.error(f"Data source error during production status query: {e}")
            scope = f"area '{area}'" if area else "the plant"
            return self._create_error_result(
                f"Unable to retrieve production data for {scope}. Please try again later."
            )
        except Exception as e:
            logger.exception(f"Unexpected error during production status query: {e}")
            return self._create_error_result(
                "An unexpected error occurred while querying production status. "
                "Please try again or contact support."
            )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _process_snapshot(
        self, snapshot: Any, targets_map: Dict[str, Any]
    ) -> Optional[AssetProductionStatus]:
        """
        Process a single snapshot into production status.

        AC#4: Status Indicators
        - >= +5% variance = ahead (green)
        - within 5% = on_track (yellow)
        - <= -5% variance = behind (red)
        """
        asset_id = snapshot.asset_id
        target = targets_map.get(asset_id)

        # Get target output from shift_targets or fall back to snapshot target
        target_output = 0
        if target and target.target_output:
            target_output = target.target_output
        elif snapshot.target_output:
            target_output = snapshot.target_output

        if target_output == 0:
            return None  # Skip assets without targets

        current_output = snapshot.current_output or 0
        variance_units = current_output - target_output
        variance_percent = (variance_units / target_output) * 100

        # Determine status (AC#4)
        if variance_percent >= AHEAD_THRESHOLD:
            status, color = "ahead", "green"
        elif variance_percent <= BEHIND_THRESHOLD:
            status, color = "behind", "red"
        else:
            status, color = "on_track", "yellow"

        # Check staleness
        snapshot_time = snapshot.snapshot_timestamp
        if isinstance(snapshot_time, str):
            snapshot_time = datetime.fromisoformat(snapshot_time.replace('Z', '+00:00'))

        # Ensure timezone-aware comparison
        now = _utcnow()
        if snapshot_time.tzinfo is None:
            snapshot_time = snapshot_time.replace(tzinfo=timezone.utc)

        is_stale = (now - snapshot_time) > timedelta(minutes=STALE_MINUTES)

        return AssetProductionStatus(
            asset_name=snapshot.asset_name or "Unknown",
            area=snapshot.area or "Unknown",
            current_output=current_output,
            shift_target=target_output,
            variance_units=variance_units,
            variance_percent=round(variance_percent, 1),
            status=status,
            status_color=color,
            snapshot_time=snapshot_time,
            is_stale=is_stale,
        )

    def _check_data_freshness(
        self, assets: List[AssetProductionStatus]
    ) -> Tuple[bool, Optional[str], str]:
        """
        Check if any data is stale and generate warning.

        AC#3: Data Freshness Warning
        - If >30 minutes old, include warning message
        - Still show data with the warning
        """
        if not assets:
            return False, None, "no_data"

        stale_assets = [a for a in assets if a.is_stale]

        if not stale_assets:
            return False, None, "live"

        # Find oldest stale timestamp
        oldest = min(a.snapshot_time for a in stale_assets)
        now = _utcnow()

        # Handle timezone awareness
        if oldest.tzinfo is None:
            oldest = oldest.replace(tzinfo=timezone.utc)

        age_minutes = int((now - oldest).total_seconds() / 60)

        if len(stale_assets) == len(assets):
            message = (
                f"Warning: All data is from {age_minutes} minutes ago "
                f"and may not reflect current status."
            )
            freshness = f"stale ({age_minutes} min old)"
        else:
            stale_names = [a.asset_name for a in stale_assets[:3]]
            if len(stale_assets) > 3:
                stale_names.append(f"and {len(stale_assets) - 3} more")
            message = (
                f"Warning: Data for {', '.join(stale_names)} is {age_minutes}+ minutes old."
            )
            freshness = "mixed (some stale)"

        return True, message, freshness

    def _calculate_summary(
        self, assets: List[AssetProductionStatus]
    ) -> ProductionStatusSummary:
        """
        Calculate summary statistics.

        AC#5: Summary Statistics
        - Total assets, count by status
        - Overall variance
        - Assets needing attention
        """
        ahead = [a for a in assets if a.status == "ahead"]
        on_track = [a for a in assets if a.status == "on_track"]
        behind = [a for a in assets if a.status == "behind"]

        total_output = sum(a.current_output for a in assets)
        total_target = sum(a.shift_target for a in assets)
        total_variance = total_output - total_target
        total_variance_pct = (total_variance / total_target * 100) if total_target > 0 else 0

        # Get top 5 worst performers (most behind)
        assets_needing_attention = [a.asset_name for a in behind[:5]]

        return ProductionStatusSummary(
            total_assets=len(assets),
            ahead_count=len(ahead),
            on_track_count=len(on_track),
            behind_count=len(behind),
            total_output=total_output,
            total_target=total_target,
            total_variance_units=total_variance,
            total_variance_percent=round(total_variance_pct, 1),
            assets_needing_attention=assets_needing_attention,
        )

    def _no_data_response(
        self, area: Optional[str], citations: List[Citation]
    ) -> ToolResult:
        """
        Generate response when no live data available.

        AC#6: No Live Data Handling
        - States "No real-time production data available"
        - Suggests checking polling pipeline
        - Does NOT fabricate any values
        """
        scope = area or "the plant"
        return self._create_success_result(
            data={
                "no_data": True,
                "message": f"No real-time production data available for {scope}.",
                "suggestion": (
                    "Please verify the polling pipeline is running "
                    "and live_snapshots table has recent data."
                ),
                "troubleshooting": [
                    "Check Railway worker logs for polling errors",
                    "Verify MSSQL connection is active",
                    "Check if live_snapshots table has recent records",
                ],
            },
            citations=citations,
            metadata={
                "cache_tier": "live",
                "ttl_seconds": CACHE_TTL_LIVE,
            },
        )

    def _generate_follow_ups(self, output: ProductionStatusOutput) -> List[str]:
        """
        Generate context-aware follow-up questions.

        Args:
            output: The production status result

        Returns:
            List of suggested questions (max 3)
        """
        questions = []

        if output.summary.behind_count > 0 and output.summary.assets_needing_attention:
            worst = output.summary.assets_needing_attention[0]
            questions.append(f"Why is {worst} behind target?")
            questions.append(f"What's causing downtime on {worst}?")

        if output.scope != "all":
            questions.append(f"Show me OEE for {output.scope}")

        questions.append("What should I focus on today?")

        return questions[:3]

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
