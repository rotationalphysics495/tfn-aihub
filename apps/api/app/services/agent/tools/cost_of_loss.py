"""
Cost of Loss Tool (Story 6.3)

Tool for ranking financial losses and identifying cost drivers.
Helps plant managers prioritize improvement efforts by ranking losses.

AC#1: Basic Cost of Loss Query - Ranked list with category, amount, root cause, percentage
AC#2: Top N Cost Drivers Query - Limit to top N items with trend comparison
AC#3: Area-Filtered Query - Filter by area and compare to plant-wide average
AC#4: Category Grouping - Group by downtime, waste, quality with subtotals
AC#5: Citation Compliance - All responses include citations
AC#6: Performance Requirements - <2s response time, 15-minute cache TTL
"""

import logging
import re
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Type

from pydantic import BaseModel

from app.models.agent import (
    AreaComparison,
    CategorySummary,
    CostOfLossInput,
    CostOfLossOutput,
    LossItem,
    TrendComparison,
)
from app.services.agent.base import Citation, ManufacturingTool, ToolResult
from app.services.agent.cache import cached_tool
from app.services.agent.data_source import (
    DataResult,
    DataSourceError,
    FinancialMetrics,
    get_data_source,
)

logger = logging.getLogger(__name__)

# Cache TTL for daily data (15 minutes)
CACHE_TTL_DAILY = 900

# Trend direction threshold (5%)
TREND_THRESHOLD = 0.05


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)


def determine_trend_direction(
    current: float,
    previous: float,
    threshold: float = TREND_THRESHOLD
) -> str:
    """
    Determine trend direction with threshold for stability.

    Story 6.3 AC#2: Trend direction logic with 5% threshold.

    Args:
        current: Current period total loss
        previous: Previous period total loss
        threshold: Percentage threshold for stability (default: 5%)

    Returns:
        "up", "down", or "stable"
    """
    if previous == 0:
        return "up" if current > 0 else "stable"

    change_percent = (current - previous) / previous

    if change_percent > threshold:
        return "up"
    elif change_percent < -threshold:
        return "down"
    else:
        return "stable"


def calculate_downtime_cost(
    downtime_minutes: int,
    standard_hourly_rate: float
) -> tuple[float, str]:
    """
    Calculate cost of downtime.

    Args:
        downtime_minutes: Total downtime in minutes
        standard_hourly_rate: $/hour rate for this asset

    Returns:
        (cost, formula_string) for transparency
    """
    cost = downtime_minutes * standard_hourly_rate / 60
    formula = f"{downtime_minutes} min * ${standard_hourly_rate:.2f}/hr / 60 = ${cost:.2f}"
    return round(cost, 2), formula


def calculate_waste_cost(
    waste_count: int,
    cost_per_unit: float
) -> tuple[float, str]:
    """
    Calculate cost of waste/scrap.

    Args:
        waste_count: Number of waste items
        cost_per_unit: $/unit cost

    Returns:
        (cost, formula_string) for transparency
    """
    cost = waste_count * cost_per_unit
    formula = f"{waste_count} units * ${cost_per_unit:.2f}/unit = ${cost:.2f}"
    return round(cost, 2), formula


class TimeRange:
    """Parsed time range with start and end dates."""

    def __init__(self, start: date, end: date, description: str):
        self.start = start
        self.end = end
        self.description = description


class CostOfLossTool(ManufacturingTool):
    """
    Rank and analyze financial losses to identify cost drivers.

    Story 6.3: Cost of Loss Tool Implementation

    Use this tool when a user asks about what's costing them money,
    top cost drivers, biggest financial impacts, or cost of loss breakdown.

    Examples:
        - "What are we losing money on?"
        - "What are the top 3 cost drivers this week?"
        - "What's the cost of loss for Grinding area?"
        - "Where are we losing the most money?"
    """

    name: str = "cost_of_loss"
    description: str = (
        "Rank and analyze financial losses to identify cost drivers. "
        "Use this tool when users ask about: what's costing us money, "
        "top cost drivers or loss leaders, where we're losing money, "
        "biggest financial impacts, or cost of loss breakdown. "
        "Returns ranked list of losses (highest first) grouped by category "
        "(downtime, waste, quality) with root causes and percentages. "
        "Supports queries for specific areas ('cost of loss for Grinding'), "
        "top N items ('top 3 cost drivers'), "
        "and time ranges ('yesterday', 'this week', 'last 7 days'). "
        "Examples: 'What are we losing money on?', "
        "'What are the top 3 cost drivers this week?'"
    )
    args_schema: Type[BaseModel] = CostOfLossInput
    citations_required: bool = True

    # Story 5.8 / 6.3 AC#6: Apply caching with daily tier (15-minute TTL)
    @cached_tool(tier="daily")
    async def _arun(
        self,
        time_range: str = "yesterday",
        area: Optional[str] = None,
        limit: int = 10,
        include_trends: bool = False,
        **kwargs,
    ) -> ToolResult:
        """
        Execute cost of loss query and return structured results.

        AC#1-6: Complete cost of loss implementation

        Args:
            time_range: Time range to query (default: "yesterday")
            area: Optional area name to filter by
            limit: Maximum number of ranked items (default: 10)
            include_trends: Include trend comparison to previous period

        Returns:
            ToolResult with CostOfLossOutput data and citations
        """
        data_source = get_data_source()
        citations: List[Citation] = []

        # Build scope description for messages
        scope = self._build_scope_description(area)

        logger.info(
            f"Cost of loss requested: time_range='{time_range}', "
            f"area='{area}', limit={limit}, include_trends={include_trends}"
        )

        try:
            # Parse time range (AC#1, default: yesterday for T-1 data)
            parsed_range = self._parse_time_range(time_range)

            # Query cost of loss data
            result = await data_source.get_cost_of_loss(
                start_date=parsed_range.start,
                end_date=parsed_range.end,
                area=area,
            )
            citations.append(self._result_to_citation(result))

            # Handle no data case
            if not result.has_data:
                return self._no_data_response(scope, parsed_range.description, citations)

            # Check if we have cost center data for financial calculations
            metrics_list: List[FinancialMetrics] = result.data
            has_any_cost_data = any(m.has_cost_data for m in metrics_list)

            # AC#3: Handle missing cost center data
            if not has_any_cost_data:
                return self._missing_cost_center_response(
                    scope, parsed_range.description, citations
                )

            # Calculate all loss items (AC#1, AC#4, AC#5)
            loss_items = self._calculate_all_losses(metrics_list)

            # Calculate total loss
            total_loss = sum(item.amount for item in loss_items)

            # Calculate percentages for each item
            for item in loss_items:
                item.percentage_of_total = (
                    round(item.amount / total_loss * 100, 1) if total_loss > 0 else 0.0
                )

            # Rank by amount (highest first) (AC#1)
            ranked_items = sorted(loss_items, key=lambda x: x.amount, reverse=True)

            # Apply limit (AC#2)
            ranked_items = ranked_items[:limit]

            # Generate category summaries (AC#4)
            category_summaries = self._generate_category_summaries(loss_items, total_loss)

            # Calculate trend if requested (AC#2)
            trend = None
            if include_trends:
                trend = await self._calculate_trend(
                    data_source, parsed_range, area, total_loss
                )

            # Calculate area comparison if area filter applied (AC#3)
            area_comparison = None
            if area:
                area_comparison = await self._calculate_area_comparison(
                    data_source, parsed_range, area, total_loss
                )

            # Add calculation citation
            citations.append(self._create_calculation_citation(total_loss))

            # Build output
            output = CostOfLossOutput(
                scope=scope,
                time_range=parsed_range.description,
                total_loss=round(total_loss, 2),
                ranked_items=ranked_items,
                category_summaries=category_summaries,
                trend_comparison=trend,
                area_comparison=area_comparison,
                message=None,
                data_freshness=_utcnow().isoformat(),
            )

            # Generate follow-up questions
            follow_ups = self._generate_follow_ups(output, area)

            return self._create_success_result(
                data=output.model_dump(),
                citations=citations,
                metadata={
                    "cache_tier": "daily",
                    "ttl_seconds": CACHE_TTL_DAILY,
                    "follow_up_questions": follow_ups,
                    "query_timestamp": _utcnow().isoformat(),
                },
            )

        except DataSourceError as e:
            logger.error(f"Data source error during cost of loss query: {e}")
            return self._create_error_result(
                f"Unable to retrieve cost of loss data for {scope}. Please try again later."
            )
        except Exception as e:
            logger.exception(f"Unexpected error during cost of loss query: {e}")
            return self._create_error_result(
                "An unexpected error occurred while calculating cost of loss. "
                "Please try again or contact support."
            )

    # =========================================================================
    # Time Range Parsing (AC#1)
    # =========================================================================

    def _parse_time_range(self, time_range: str) -> TimeRange:
        """
        Parse time range string into start and end dates.

        Default: "yesterday" for T-1 data (most common use case for daily summaries).

        Supports:
        - "today" / "now"
        - "yesterday" (default)
        - "this week"
        - "last 7 days" / "last N days"
        - "2026-01-01 to 2026-01-09" (explicit range)
        """
        today = date.today()
        time_range_lower = time_range.lower().strip()

        # Today
        if time_range_lower in ("today", "now"):
            return TimeRange(today, today, "today")

        # Yesterday (default for financial data - T-1)
        if time_range_lower == "yesterday":
            yesterday = today - timedelta(days=1)
            return TimeRange(yesterday, yesterday, "yesterday")

        # This week (Monday to today)
        if time_range_lower == "this week":
            monday = today - timedelta(days=today.weekday())
            return TimeRange(monday, today, "this week")

        # Last N days pattern
        last_n_match = re.match(r"last\s+(\d+)\s+days?", time_range_lower)
        if last_n_match:
            n_days = int(last_n_match.group(1))
            start = today - timedelta(days=n_days)
            return TimeRange(start, today, f"last {n_days} days")

        # Date range pattern: "YYYY-MM-DD to YYYY-MM-DD"
        range_match = re.match(
            r"(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})",
            time_range_lower
        )
        if range_match:
            start = date.fromisoformat(range_match.group(1))
            end = date.fromisoformat(range_match.group(2))
            return TimeRange(start, end, f"{start} to {end}")

        # Default to yesterday if unrecognized
        logger.warning(f"Unrecognized time range '{time_range}', defaulting to 'yesterday'")
        yesterday = today - timedelta(days=1)
        return TimeRange(yesterday, yesterday, "yesterday")

    # =========================================================================
    # Loss Calculation (AC#1, AC#4, AC#5)
    # =========================================================================

    def _calculate_all_losses(self, metrics: List[FinancialMetrics]) -> List[LossItem]:
        """
        Calculate all loss items from financial metrics.

        AC#1: Returns loss items with asset, category, amount, root cause.
        AC#4: Groups by category (downtime, waste, quality).
        AC#5: Extracts root causes from downtime_reasons.
        """
        loss_items: List[LossItem] = []

        for m in metrics:
            asset_name = m.asset_name or "Unknown"

            # Extract downtime losses with root causes
            if m.downtime_minutes > 0 and m.standard_hourly_rate:
                hourly_rate = float(m.standard_hourly_rate)
                cost_per_minute = hourly_rate / 60

                # Check for downtime_reasons JSONB for root cause extraction
                if m.downtime_reasons and isinstance(m.downtime_reasons, dict):
                    # Extract individual loss items from downtime_reasons
                    for reason, minutes in m.downtime_reasons.items():
                        if isinstance(minutes, (int, float)) and minutes > 0:
                            cost = round(minutes * cost_per_minute, 2)
                            loss_items.append(LossItem(
                                asset_id=m.asset_id,
                                asset_name=asset_name,
                                category="downtime",
                                amount=cost,
                                root_cause=reason,
                                percentage_of_total=0.0,  # Calculated later
                                duration_minutes=int(minutes),
                            ))
                else:
                    # No breakdown available - add aggregate downtime
                    cost, _ = calculate_downtime_cost(m.downtime_minutes, hourly_rate)
                    loss_items.append(LossItem(
                        asset_id=m.asset_id,
                        asset_name=asset_name,
                        category="downtime",
                        amount=cost,
                        root_cause=None,
                        percentage_of_total=0.0,
                        duration_minutes=m.downtime_minutes,
                    ))

            # Extract waste losses
            if m.waste_count > 0 and m.cost_per_unit:
                cost, _ = calculate_waste_cost(m.waste_count, float(m.cost_per_unit))
                loss_items.append(LossItem(
                    asset_id=m.asset_id,
                    asset_name=asset_name,
                    category="waste",
                    amount=cost,
                    root_cause=None,
                    percentage_of_total=0.0,
                    duration_minutes=None,
                ))

        return loss_items

    def _generate_category_summaries(
        self, loss_items: List[LossItem], total_loss: float
    ) -> List[CategorySummary]:
        """
        Generate category summaries from loss items.

        AC#4: Each category shows subtotal and percentage of total loss.
        """
        # Group items by category
        by_category: Dict[str, List[LossItem]] = defaultdict(list)
        for item in loss_items:
            by_category[item.category].append(item)

        summaries: List[CategorySummary] = []

        # Define category order
        category_order = ["downtime", "waste", "quality"]

        for category in category_order:
            items = by_category.get(category, [])
            if not items:
                continue

            category_total = sum(item.amount for item in items)
            percentage = round(category_total / total_loss * 100, 1) if total_loss > 0 else 0.0

            # Get top contributors (reasons or assets)
            top_contributors: List[str] = []
            if category == "downtime":
                # Get top reasons
                reason_costs: Dict[str, float] = defaultdict(float)
                for item in items:
                    if item.root_cause:
                        reason_costs[item.root_cause] += item.amount
                # Sort by cost and take top 3
                sorted_reasons = sorted(
                    reason_costs.items(), key=lambda x: x[1], reverse=True
                )
                top_contributors = [reason for reason, _ in sorted_reasons[:3]]
            else:
                # Get top assets for waste/quality
                asset_costs: Dict[str, float] = defaultdict(float)
                for item in items:
                    asset_costs[item.asset_name] += item.amount
                sorted_assets = sorted(
                    asset_costs.items(), key=lambda x: x[1], reverse=True
                )
                top_contributors = [asset for asset, _ in sorted_assets[:3]]

            summaries.append(CategorySummary(
                category=category,
                total_amount=round(category_total, 2),
                item_count=len(items),
                percentage_of_total=percentage,
                top_contributors=top_contributors,
            ))

        # Sort by amount descending
        summaries.sort(key=lambda x: x.total_amount, reverse=True)
        return summaries

    # =========================================================================
    # Trend Comparison (AC#2)
    # =========================================================================

    async def _calculate_trend(
        self,
        data_source,
        current_range: TimeRange,
        area: Optional[str],
        current_total: float,
    ) -> Optional[TrendComparison]:
        """
        Calculate trend comparison vs previous period.

        AC#2: Includes trend vs previous week (up/down/stable).
        """
        try:
            # Calculate previous period with same duration
            duration = (current_range.end - current_range.start).days + 1
            prev_end = current_range.start - timedelta(days=1)
            prev_start = prev_end - timedelta(days=duration - 1)

            # Get previous period data
            prev_result = await data_source.get_cost_of_loss(
                start_date=prev_start,
                end_date=prev_end,
                area=area,
            )

            if not prev_result.has_data:
                return None

            # Calculate previous period total
            prev_metrics: List[FinancialMetrics] = prev_result.data
            prev_items = self._calculate_all_losses(prev_metrics)
            prev_total = sum(item.amount for item in prev_items)

            # Calculate change
            change_amount = current_total - prev_total
            change_percent = (
                round((change_amount / prev_total * 100), 1)
                if prev_total > 0 else 0.0
            )

            # Determine trend direction
            trend_direction = determine_trend_direction(current_total, prev_total)

            return TrendComparison(
                previous_period_total=round(prev_total, 2),
                current_period_total=round(current_total, 2),
                change_amount=round(change_amount, 2),
                change_percent=change_percent,
                trend_direction=trend_direction,
            )

        except Exception as e:
            logger.warning(f"Could not calculate trend comparison: {e}")
            return None

    # =========================================================================
    # Area Comparison (AC#3)
    # =========================================================================

    async def _calculate_area_comparison(
        self,
        data_source,
        current_range: TimeRange,
        area: str,
        area_total: float,
    ) -> Optional[AreaComparison]:
        """
        Calculate area comparison vs plant-wide average.

        AC#3: Compares area loss to plant-wide average.
        """
        try:
            # Get plant-wide data (no area filter)
            plant_result = await data_source.get_cost_of_loss(
                start_date=current_range.start,
                end_date=current_range.end,
                area=None,
            )

            if not plant_result.has_data:
                return None

            # Calculate plant-wide totals
            plant_metrics: List[FinancialMetrics] = plant_result.data
            plant_items = self._calculate_all_losses(plant_metrics)
            plant_total = sum(item.amount for item in plant_items)

            # Get unique areas for average calculation
            areas = set()
            for m in plant_metrics:
                if m.area:
                    areas.add(m.area)

            num_areas = len(areas) if areas else 1
            plant_wide_average = plant_total / num_areas if num_areas > 0 else plant_total

            # Calculate variance
            variance = area_total - plant_wide_average
            variance_percent = round(
                (variance / plant_wide_average * 100) if plant_wide_average > 0 else 0.0,
                1
            )

            # Build comparison text
            if variance > 0:
                comparison_text = f"{area} area is {abs(variance_percent):.1f}% above plant average"
            elif variance < 0:
                comparison_text = f"{area} area is {abs(variance_percent):.1f}% below plant average"
            else:
                comparison_text = f"{area} area is at plant average"

            return AreaComparison(
                area_loss=round(area_total, 2),
                plant_wide_average=round(plant_wide_average, 2),
                variance=round(variance, 2),
                variance_percent=variance_percent,
                comparison_text=comparison_text,
            )

        except Exception as e:
            logger.warning(f"Could not calculate area comparison: {e}")
            return None

    # =========================================================================
    # Missing Data Handling
    # =========================================================================

    def _missing_cost_center_response(
        self,
        scope: str,
        time_range: str,
        citations: List[Citation],
    ) -> ToolResult:
        """
        Format response when cost center data is missing.
        """
        output = CostOfLossOutput(
            scope=scope,
            time_range=time_range,
            total_loss=0.0,
            ranked_items=[],
            category_summaries=[],
            trend_comparison=None,
            area_comparison=None,
            message=(
                f"Unable to calculate cost of loss for {scope} - "
                "no cost center data configured for these assets. "
                "Cost center data is required to convert downtime and waste into dollar amounts."
            ),
            data_freshness=_utcnow().isoformat(),
        )

        return self._create_success_result(
            data=output.model_dump(),
            citations=citations,
            metadata={
                "cache_tier": "daily",
                "ttl_seconds": CACHE_TTL_DAILY,
                "follow_up_questions": [
                    "Show me downtime by asset",
                    "What was the total waste count?",
                ],
            },
        )

    def _no_data_response(
        self,
        scope: str,
        time_range: str,
        citations: List[Citation],
    ) -> ToolResult:
        """
        Generate response when no data found for the query.
        """
        output = CostOfLossOutput(
            scope=scope,
            time_range=time_range,
            total_loss=0.0,
            ranked_items=[],
            category_summaries=[],
            trend_comparison=None,
            area_comparison=None,
            message=f"No data found for {scope} in {time_range}.",
            data_freshness=_utcnow().isoformat(),
        )

        return self._create_success_result(
            data=output.model_dump(),
            citations=citations,
            metadata={
                "cache_tier": "daily",
                "ttl_seconds": CACHE_TTL_DAILY,
                "follow_up_questions": [
                    "Try a different time range",
                    "Show me plant-wide cost of loss",
                ],
            },
        )

    # =========================================================================
    # Citation Generation (AC#5)
    # =========================================================================

    def _result_to_citation(self, result: DataResult) -> Citation:
        """
        Convert DataResult to Citation.

        AC#5: Citation Compliance - includes source table and timestamp.
        """
        return self._create_citation(
            source=result.source_name,
            query=result.query or f"Query on {result.table_name}",
            table=result.table_name,
        )

    def _create_calculation_citation(self, total_loss: float) -> Citation:
        """
        Create citation for calculation evidence.

        AC#5: Citations reference calculation basis.
        """
        return self._create_citation(
            source="calculation",
            query=(
                f"Cost of loss calculation using cost_centers rates. "
                f"Total calculated: ${total_loss:.2f}"
            ),
            table="cost_centers",
            confidence=1.0,
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _build_scope_description(self, area: Optional[str]) -> str:
        """Build human-readable scope description."""
        if area:
            return f"the {area} area"
        else:
            return "plant-wide"

    def _generate_follow_ups(
        self,
        output: CostOfLossOutput,
        area: Optional[str],
    ) -> List[str]:
        """
        Generate context-aware follow-up questions.

        Args:
            output: The cost of loss result
            area: Area filter if used

        Returns:
            List of suggested questions (max 3)
        """
        questions = []

        if output.total_loss > 0:
            # Suggest drilling into specific category
            if output.category_summaries:
                highest_category = output.category_summaries[0]
                if highest_category.category == "downtime":
                    questions.append("What are the main causes of downtime?")
                elif highest_category.category == "waste":
                    questions.append("Which assets have the most waste?")

            # For plant-wide queries, suggest area drill-down
            if not area and output.ranked_items:
                questions.append("Show me cost of loss for Grinding area")

            # For area queries, suggest comparison
            if area:
                questions.append("How does this compare to other areas?")

        # Suggest time comparisons
        if output.time_range == "yesterday":
            questions.append("What was the cost of loss this week?")
        elif output.time_range == "this week":
            questions.append("Show me the trend over the last month")

        return questions[:3]
