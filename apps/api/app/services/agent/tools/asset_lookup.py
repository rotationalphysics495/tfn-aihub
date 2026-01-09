"""
Asset Lookup Tool (Story 5.3)

Tool for looking up asset information including metadata, current status,
and recent performance metrics.

AC#1: Asset Lookup by Name - Returns metadata, status, OEE, downtime
AC#2: Asset Not Found - Provides fuzzy suggestions
AC#3: No Recent Data - Shows available metadata with message
AC#4: Live Status Display - Includes freshness tracking
AC#5: Performance Summary - OEE trend, downtime analysis
AC#6: Citation Compliance - All data points include citations
AC#7: Cache TTL Requirements - Tiered caching metadata
AC#8: Error Handling - User-friendly errors, logging
"""

import logging
import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from app.models.agent import (
    AssetCurrentStatus,
    AssetLookupInput,
    AssetLookupOutput,
    AssetMetadata,
    AssetPerformance,
    AssetStatus,
    OEETrend,
)
from app.services.agent.base import Citation, ManufacturingTool, ToolResult
from app.services.agent.data_source import (
    DataResult,
    DataSourceError,
    get_data_source,
)

logger = logging.getLogger(__name__)

# Cache TTL constants (in seconds)
CACHE_TTL_METADATA = 3600  # 1 hour for static metadata
CACHE_TTL_LIVE = 60  # 60 seconds for live data
CACHE_TTL_PERFORMANCE = 900  # 15 minutes for performance data

# Data freshness threshold (30 minutes)
STALE_DATA_THRESHOLD_MINUTES = 30


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)


def _normalize_asset_name(name: str) -> str:
    """
    Normalize asset name for fuzzy matching.

    AC#2 (Story 5.3): Handles variations like 'grinder5', 'Grinder #5', 'grinder 5'

    Args:
        name: Raw asset name from user input

    Returns:
        Normalized name suitable for database search
    """
    # Convert to lowercase
    normalized = name.lower().strip()

    # Remove common separators and special characters
    # Keep alphanumeric and spaces
    normalized = re.sub(r'[#\-_]', ' ', normalized)

    # Collapse multiple spaces
    normalized = re.sub(r'\s+', ' ', normalized)

    # Add space before trailing numbers (grinder5 -> grinder 5)
    normalized = re.sub(r'([a-z])(\d)', r'\1 \2', normalized)

    return normalized.strip()


class AssetLookupTool(ManufacturingTool):
    """
    Look up information about a specific manufacturing asset.

    Story 5.3: Asset Lookup Tool Implementation

    Use this tool when a user asks about a specific machine, asset, or equipment
    by name. Returns metadata, current status, recent performance, and top issues.

    Examples:
        - "Tell me about Grinder 5"
        - "How is CAMA 800-1 doing?"
        - "What's the status of the packaging line?"
        - "Show me info on Grinder #5"
    """

    name: str = "asset_lookup"
    description: str = (
        "Look up asset information including current status, production output, "
        "and recent performance metrics. Use when user asks about a specific "
        "machine or asset like 'How is Grinder 5 doing?' or 'Tell me about [asset name]'. "
        "Returns metadata, live status, OEE average, and top downtime reasons."
    )
    args_schema: Type[BaseModel] = AssetLookupInput
    citations_required: bool = True

    async def _arun(
        self,
        asset_name: str,
        include_performance: bool = True,
        days_back: int = 7,
        **kwargs,
    ) -> ToolResult:
        """
        Execute asset lookup and return structured results.

        AC#1: Asset lookup with metadata, status, OEE, downtime
        AC#6: All data points include citations
        AC#8: Error handling with user-friendly messages

        Args:
            asset_name: Name of the asset to look up
            include_performance: Whether to include 7-day performance
            days_back: Number of days for performance analysis

        Returns:
            ToolResult with AssetLookupOutput data and citations
        """
        data_source = get_data_source()
        citations: List[Citation] = []

        logger.info(f"Asset lookup requested for: '{asset_name}'")

        try:
            # Step 1: Normalize and resolve asset name
            normalized_name = _normalize_asset_name(asset_name)
            logger.debug(f"Normalized asset name: '{normalized_name}'")

            # Try to find the asset with fuzzy matching
            asset_result = await data_source.get_asset_by_name(normalized_name)
            citations.append(self._result_to_citation(asset_result))

            if not asset_result.has_data:
                # AC#2: Asset not found - get suggestions
                logger.info(f"Asset not found: '{asset_name}', fetching suggestions")
                return await self._handle_asset_not_found(
                    asset_name, normalized_name, citations
                )

            asset = asset_result.data
            asset_id = asset.id

            logger.debug(f"Found asset: {asset.name} (id: {asset_id})")

            # Step 2: Get current live status
            live_result = await data_source.get_live_snapshot(asset_id)
            citations.append(self._result_to_citation(live_result))
            current_status = self._parse_live_status(live_result.data)

            # Step 3: Get shift target for variance calculation
            target_result = await data_source.get_shift_target(asset_id)
            citations.append(self._result_to_citation(target_result))

            # Update current status with target-based variance
            if target_result.has_data and live_result.has_data:
                current_status = self._update_status_with_target(
                    current_status, live_result.data, target_result.data
                )

            # Step 4: Get performance data (if requested)
            performance = None
            if include_performance:
                performance = await self._get_performance_summary(
                    asset_id, days_back, citations
                )

            # Step 5: Build response
            metadata = self._parse_metadata(asset)
            output = AssetLookupOutput(
                found=True,
                metadata=metadata,
                current_status=current_status,
                performance=performance,
                suggestions=None,
                message=None,
            )

            # Determine cache tier based on data
            cache_tier = "live" if live_result.has_data else "static"
            ttl = CACHE_TTL_LIVE if live_result.has_data else CACHE_TTL_METADATA

            # Generate follow-up questions
            follow_ups = self._generate_follow_up_questions(output)

            return self._create_success_result(
                data=output.model_dump(),
                citations=citations,
                metadata={
                    "asset_id": asset_id,
                    "asset_name": asset.name,
                    "days_analyzed": days_back,
                    "cache_tier": cache_tier,
                    "ttl_seconds": ttl,
                    "follow_up_questions": follow_ups,
                    "query_timestamp": _utcnow().isoformat(),
                },
            )

        except DataSourceError as e:
            # AC#8: User-friendly error for data source issues
            logger.error(f"Data source error during asset lookup: {e}")
            return self._create_error_result(
                f"Unable to retrieve data for '{asset_name}'. Please try again later."
            )
        except Exception as e:
            # AC#8: Generic error handling
            logger.exception(f"Unexpected error during asset lookup for '{asset_name}': {e}")
            return self._create_error_result(
                "An unexpected error occurred while looking up the asset. "
                "Please try again or contact support."
            )

    async def _handle_asset_not_found(
        self,
        original_name: str,
        normalized_name: str,
        citations: List[Citation],
    ) -> ToolResult:
        """
        Handle case when asset is not found.

        AC#2: Asset Not Found - Fuzzy Suggestions
        - States "I don't have data for [asset name]"
        - Lists similar assets (max 5)
        - Does NOT fabricate data

        Args:
            original_name: Original user input
            normalized_name: Normalized search term
            citations: List to append citation to

        Returns:
            ToolResult with suggestions
        """
        data_source = get_data_source()

        # Get similar assets for suggestions
        similar_result = await data_source.get_similar_assets(normalized_name, limit=5)
        citations.append(self._result_to_citation(similar_result))

        suggestions = []
        if similar_result.has_data:
            suggestions = [asset.name for asset in similar_result.data]

        # Build suggestion message
        suggestion_message = None
        if suggestions:
            suggestion_message = f"Did you mean one of these? {', '.join(suggestions)}"

        output = AssetLookupOutput(
            found=False,
            metadata=None,
            current_status=None,
            performance=None,
            suggestions=suggestions,
            message=f"I don't have data for '{original_name}'.",
        )

        return self._create_success_result(
            data=output.model_dump(),
            citations=citations,
            metadata={
                "asset_not_found": True,
                "search_term": original_name,
                "normalized_search": normalized_name,
                "cache_tier": "static",
                "ttl_seconds": CACHE_TTL_METADATA,
                "suggestion_message": suggestion_message,
            },
        )

    async def _get_performance_summary(
        self,
        asset_id: str,
        days_back: int,
        citations: List[Citation],
    ) -> AssetPerformance:
        """
        Get performance summary for the asset.

        AC#3: No Recent Data - Shows message if no data
        AC#5: Performance Summary - OEE trend, downtime analysis

        Args:
            asset_id: Asset UUID
            days_back: Number of days to analyze
            citations: List to append citations to

        Returns:
            AssetPerformance with OEE and downtime data
        """
        data_source = get_data_source()

        # Calculate date range (today-1 back to avoid incomplete today data)
        end_date = date.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=days_back - 1)

        # Get OEE data
        oee_result = await data_source.get_oee(asset_id, start_date, end_date)
        citations.append(self._result_to_citation(oee_result))

        # Get downtime data
        downtime_result = await data_source.get_downtime(asset_id, start_date, end_date)
        citations.append(self._result_to_citation(downtime_result))

        # AC#3: Handle no recent data
        if not oee_result.has_data:
            return AssetPerformance(
                avg_oee=None,
                oee_trend=OEETrend.INSUFFICIENT_DATA,
                total_downtime_minutes=0,
                top_downtime_reason=None,
                top_downtime_percent=None,
                days_analyzed=days_back,
                no_data=True,
                message=f"No production data available for the last {days_back} days",
            )

        # Calculate average OEE
        oee_values = [
            float(m.oee_percentage)
            for m in oee_result.data
            if m.oee_percentage is not None
        ]
        avg_oee = sum(oee_values) / len(oee_values) if oee_values else None

        # Calculate OEE trend
        oee_trend = self._calculate_oee_trend(oee_values)

        # Calculate total downtime
        total_downtime = sum(
            m.downtime_minutes or 0 for m in oee_result.data
        )

        # Find top downtime reason from downtime events
        top_reason, top_percent = self._get_top_downtime_reason(downtime_result.data)

        return AssetPerformance(
            avg_oee=round(avg_oee, 1) if avg_oee is not None else None,
            oee_trend=oee_trend,
            total_downtime_minutes=total_downtime,
            top_downtime_reason=top_reason,
            top_downtime_percent=top_percent,
            days_analyzed=days_back,
            no_data=False,
            message=None,
        )

    def _parse_metadata(self, asset: Any) -> AssetMetadata:
        """
        Parse asset data into AssetMetadata.

        AC#1: Returns asset metadata (name, area, cost center)

        Args:
            asset: Asset object from data source

        Returns:
            AssetMetadata model
        """
        return AssetMetadata(
            id=asset.id,
            name=asset.name,
            source_id=asset.source_id,
            area=asset.area,
            cost_center=None,  # Cost center not directly on asset model
        )

    def _parse_live_status(self, snapshot_data: Any) -> AssetCurrentStatus:
        """
        Parse live snapshot into current status.

        AC#4: Live Status Display with freshness tracking

        Args:
            snapshot_data: ProductionStatus from data source or None

        Returns:
            AssetCurrentStatus model
        """
        if snapshot_data is None:
            return AssetCurrentStatus(
                status=AssetStatus.UNKNOWN,
                output_current=None,
                output_target=None,
                variance=None,
                variance_percent=None,
                last_updated=None,
                data_stale=True,
                stale_warning="No live data available for this asset",
            )

        # Determine status from snapshot
        status = self._determine_status_from_snapshot(snapshot_data)

        # Check data freshness
        is_stale = False
        stale_warning = None
        last_updated = None

        if snapshot_data.snapshot_timestamp:
            last_updated = snapshot_data.snapshot_timestamp.isoformat()

            # Check if data is stale (>30 minutes old)
            if isinstance(snapshot_data.snapshot_timestamp, datetime):
                ts = snapshot_data.snapshot_timestamp
                # Make naive datetime timezone-aware for comparison
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                age_minutes = (_utcnow() - ts).total_seconds() / 60
                if age_minutes > STALE_DATA_THRESHOLD_MINUTES:
                    is_stale = True
                    stale_warning = f"Data is {int(age_minutes)} minutes old"

        return AssetCurrentStatus(
            status=status,
            output_current=snapshot_data.current_output,
            output_target=snapshot_data.target_output,
            variance=snapshot_data.output_variance,
            variance_percent=None,  # Will be calculated with target
            last_updated=last_updated,
            data_stale=is_stale,
            stale_warning=stale_warning,
        )

    def _update_status_with_target(
        self,
        status: AssetCurrentStatus,
        live_data: Any,
        target_data: Any,
    ) -> AssetCurrentStatus:
        """
        Update status with target-based variance calculations.

        Args:
            status: Current status object
            live_data: ProductionStatus from live snapshot
            target_data: ShiftTarget from targets table

        Returns:
            Updated AssetCurrentStatus
        """
        target_output = target_data.target_output if target_data else None
        current_output = live_data.current_output if live_data else None

        if target_output and current_output is not None:
            variance = current_output - target_output
            variance_percent = round(100 * variance / target_output, 1) if target_output else None

            return AssetCurrentStatus(
                status=status.status,
                output_current=current_output,
                output_target=target_output,
                variance=variance,
                variance_percent=variance_percent,
                last_updated=status.last_updated,
                data_stale=status.data_stale,
                stale_warning=status.stale_warning,
            )

        return status

    def _determine_status_from_snapshot(self, snapshot: Any) -> AssetStatus:
        """
        Determine asset status from live snapshot data.

        AC#4: Status (running/down/idle based on latest snapshot)

        Args:
            snapshot: ProductionStatus object

        Returns:
            AssetStatus enum value
        """
        if not snapshot:
            return AssetStatus.UNKNOWN

        # Use the status field from ProductionStatus
        status_str = snapshot.status.lower() if snapshot.status else "unknown"

        if status_str in ("on_target", "ahead", "behind", "running"):
            return AssetStatus.RUNNING
        elif status_str == "down":
            return AssetStatus.DOWN
        elif status_str == "idle":
            return AssetStatus.IDLE
        else:
            return AssetStatus.UNKNOWN

    def _calculate_oee_trend(self, oee_values: List[float]) -> OEETrend:
        """
        Calculate OEE trend from historical values.

        AC#5: OEE trend indicator (improving/stable/declining)

        Compares average of first half vs second half of values.
        Requires at least 4 data points.

        Args:
            oee_values: List of OEE percentages (oldest to newest)

        Returns:
            OEETrend enum value
        """
        if len(oee_values) < 4:
            return OEETrend.INSUFFICIENT_DATA

        # Values come in reverse chronological order, so reverse for trend calc
        values = list(reversed(oee_values))

        mid = len(values) // 2
        first_half_avg = sum(values[:mid]) / mid
        second_half_avg = sum(values[mid:]) / (len(values) - mid)

        diff = second_half_avg - first_half_avg

        # Use 2% threshold for trend determination
        if diff > 2:
            return OEETrend.IMPROVING
        elif diff < -2:
            return OEETrend.DECLINING
        else:
            return OEETrend.STABLE

    def _get_top_downtime_reason(
        self,
        downtime_events: Optional[List[Any]],
    ) -> tuple[Optional[str], Optional[float]]:
        """
        Find the top downtime reason from events.

        AC#5: Top downtime reason with percentage contribution

        Args:
            downtime_events: List of DowntimeEvent objects

        Returns:
            Tuple of (reason, percentage) or (None, None)
        """
        if not downtime_events:
            return None, None

        # Aggregate downtime by reason
        reason_totals: Dict[str, int] = {}
        total_downtime = 0

        for event in downtime_events:
            reason = event.reason_description or event.reason_code or "Unknown"
            minutes = event.downtime_minutes or 0
            reason_totals[reason] = reason_totals.get(reason, 0) + minutes
            total_downtime += minutes

        if not reason_totals or total_downtime == 0:
            return None, None

        # Find top reason
        top_reason = max(reason_totals, key=reason_totals.get)
        top_percent = round(100 * reason_totals[top_reason] / total_downtime, 1)

        return top_reason, top_percent

    def _result_to_citation(self, result: DataResult) -> Citation:
        """
        Convert DataResult to Citation.

        AC#6: Citation Compliance - All data points include citations

        Args:
            result: DataResult from data source

        Returns:
            Citation object
        """
        return self._create_citation(
            source=result.source_name,
            query=result.query or f"Query on {result.table_name}",
            table=result.table_name,
        )

    def _generate_follow_up_questions(
        self,
        output: AssetLookupOutput,
    ) -> List[str]:
        """
        Generate context-aware follow-up questions.

        AC#7 (Story 5.7): Suggested follow-up questions

        Args:
            output: The asset lookup result

        Returns:
            List of suggested questions (max 3)
        """
        questions = []

        if not output.found or not output.metadata:
            return ["Show me all available assets"]

        asset_name = output.metadata.name

        # Performance-based questions
        if output.performance:
            perf = output.performance

            if perf.avg_oee is not None and perf.avg_oee < 80:
                questions.append(f"Why is {asset_name}'s OEE low?")

            if perf.top_downtime_reason:
                questions.append(
                    f"Tell me more about '{perf.top_downtime_reason}' downtime on {asset_name}"
                )

            if perf.oee_trend == OEETrend.DECLINING:
                questions.append(f"What's causing {asset_name}'s OEE to decline?")

        # Status-based questions
        if output.current_status:
            status = output.current_status

            if status.variance and status.variance < 0:
                questions.append(f"Why is {asset_name} behind target?")

            if status.status == AssetStatus.DOWN:
                questions.append(f"What's wrong with {asset_name}?")

        # Always offer OEE trend
        questions.append(f"Show me {asset_name}'s OEE trend")

        # Return max 3 unique questions
        return list(dict.fromkeys(questions))[:3]
