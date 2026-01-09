"""
Financial Impact Tool (Story 6.2)

Tool for calculating financial impact of downtime and waste for assets or areas.
Helps plant managers prioritize issues by business impact (dollar cost).

AC#1: Asset-Level Financial Impact Query - Returns total loss, breakdown, hourly rate, average comparison
AC#2: Area-Level Financial Impact Query - Aggregates across assets, shows per-asset breakdown, identifies highest-cost asset
AC#3: Missing Cost Center Data Handling - Honest response with available non-financial metrics
AC#4: Transparent Calculations - All responses show calculation formulas
AC#5: Citation Compliance - All responses include citations with source tables
AC#6: Performance Requirements - <2s response time, 15-minute cache TTL
"""

import logging
import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Type

from pydantic import BaseModel

from app.models.agent import (
    AssetFinancialSummary,
    AverageComparison,
    CostBreakdown,
    FinancialImpactInput,
    FinancialImpactOutput,
    HighestCostAsset,
    NonFinancialMetric,
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

# Cache TTL for financial data (daily summaries - 15 minutes)
CACHE_TTL_DAILY = 900  # 15 minutes


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)


class TimeRange:
    """Parsed time range with start and end dates."""

    def __init__(self, start: date, end: date, description: str):
        self.start = start
        self.end = end
        self.description = description


def calculate_downtime_cost(
    downtime_minutes: int,
    standard_hourly_rate: float
) -> tuple[float, str]:
    """
    Calculate cost of downtime.

    Story 6.2 AC#4: Transparent calculations with formula.

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

    Story 6.2 AC#4: Transparent calculations with formula.

    Args:
        waste_count: Number of waste items
        cost_per_unit: $/unit cost

    Returns:
        (cost, formula_string) for transparency
    """
    cost = waste_count * cost_per_unit
    formula = f"{waste_count} units * ${cost_per_unit:.2f}/unit = ${cost:.2f}"
    return round(cost, 2), formula


class FinancialImpactTool(ManufacturingTool):
    """
    Calculate financial impact of downtime and waste.

    Story 6.2: Financial Impact Tool Implementation

    Use this tool when a user asks about the cost or financial impact of
    downtime, waste, or production issues. Returns dollar amounts with
    transparent calculation formulas.

    Examples:
        - "What's the cost of downtime for Grinder 5 yesterday?"
        - "What's the financial impact for the Grinding area this week?"
        - "How much is downtime costing us?"
        - "What's the financial loss from waste?"
    """

    name: str = "financial_impact"
    description: str = (
        "Calculate the financial impact of downtime and waste. "
        "Use this tool when users ask about cost of downtime, financial impact, "
        "dollar loss from production issues, or what something is 'costing us'. "
        "Returns total loss with breakdown by category (downtime cost, waste cost) "
        "and transparent calculation formulas. "
        "Supports queries for specific assets ('cost for Grinder 5'), "
        "areas ('financial impact for Grinding area'), "
        "and time ranges ('yesterday', 'this week', 'last 7 days'). "
        "Examples: 'What's the cost of downtime for Grinder 5 yesterday?', "
        "'What's the financial impact for Grinding this week?'"
    )
    args_schema: Type[BaseModel] = FinancialImpactInput
    citations_required: bool = True

    # Story 5.8 / 6.2 AC#6: Apply caching with daily tier (15-minute TTL)
    @cached_tool(tier="daily")
    async def _arun(
        self,
        time_range: str = "yesterday",
        asset_id: Optional[str] = None,
        area: Optional[str] = None,
        include_breakdown: bool = True,
        **kwargs,
    ) -> ToolResult:
        """
        Execute financial impact query and return structured results.

        AC#1-6: Complete financial impact implementation

        Args:
            time_range: Time range to query (default: "yesterday")
            asset_id: Optional specific asset UUID
            area: Optional area name to filter by
            include_breakdown: Whether to include detailed breakdown

        Returns:
            ToolResult with FinancialImpactOutput data and citations
        """
        data_source = get_data_source()
        citations: List[Citation] = []

        # Build scope description for messages
        scope = self._build_scope_description(area, asset_id)

        logger.info(
            f"Financial impact requested: time_range='{time_range}', "
            f"area='{area}', asset_id='{asset_id}'"
        )

        try:
            # Parse time range (AC#1, default: yesterday for T-1 data)
            parsed_range = self._parse_time_range(time_range)

            # Query financial metrics with cost_centers data
            result = await data_source.get_financial_metrics(
                start_date=parsed_range.start,
                end_date=parsed_range.end,
                asset_id=asset_id,
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
                    metrics_list, scope, parsed_range.description, citations
                )

            # Calculate financial impact (AC#1, AC#4)
            breakdown = self._calculate_breakdown(metrics_list)
            total_loss = sum(b.amount for b in breakdown)

            # For area queries, calculate per-asset breakdown (AC#2)
            per_asset_breakdown = None
            highest_cost_asset = None
            if area and len(metrics_list) > 0:
                per_asset_breakdown = self._calculate_per_asset_breakdown(metrics_list)
                if per_asset_breakdown:
                    # Find highest cost asset
                    highest = max(per_asset_breakdown, key=lambda x: x.total_loss)
                    highest_cost_asset = HighestCostAsset(
                        asset_id=highest.asset_id,
                        asset_name=highest.asset_name,
                        total_loss=highest.total_loss,
                    )

            # Calculate average comparison (AC#1)
            avg_comparison = await self._calculate_average_comparison(
                data_source, metrics_list, asset_id, area, parsed_range
            )

            # Add calculation citation
            citations.append(self._create_calculation_citation(breakdown))

            # Build output
            output = FinancialImpactOutput(
                scope=scope,
                time_range=parsed_range.description,
                total_loss=total_loss,
                breakdown=breakdown if include_breakdown else [],
                per_asset_breakdown=per_asset_breakdown,
                highest_cost_asset=highest_cost_asset,
                average_comparison=avg_comparison,
                message=None,
                non_financial_metrics=None,
                data_freshness=_utcnow().isoformat(),
            )

            # Generate follow-up questions
            follow_ups = self._generate_follow_ups(output, area, asset_id)

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
            logger.error(f"Data source error during financial impact query: {e}")
            return self._create_error_result(
                f"Unable to retrieve financial data for {scope}. Please try again later."
            )
        except Exception as e:
            logger.exception(f"Unexpected error during financial impact query: {e}")
            return self._create_error_result(
                "An unexpected error occurred while calculating financial impact. "
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
    # Financial Calculations (AC#1, AC#4)
    # =========================================================================

    def _calculate_breakdown(self, metrics: List[FinancialMetrics]) -> List[CostBreakdown]:
        """
        Calculate total cost breakdown by category.

        AC#4: Include transparent calculations with formulas.
        """
        # Aggregate totals across all records
        total_downtime_minutes = 0
        total_waste_count = 0
        avg_hourly_rate = 0.0
        avg_cost_per_unit = 0.0
        rate_count = 0
        unit_cost_count = 0

        for m in metrics:
            total_downtime_minutes += m.downtime_minutes
            total_waste_count += m.waste_count
            if m.standard_hourly_rate:
                avg_hourly_rate += float(m.standard_hourly_rate)
                rate_count += 1
            if m.cost_per_unit:
                avg_cost_per_unit += float(m.cost_per_unit)
                unit_cost_count += 1

        # Calculate averages for rates
        if rate_count > 0:
            avg_hourly_rate = avg_hourly_rate / rate_count
        if unit_cost_count > 0:
            avg_cost_per_unit = avg_cost_per_unit / unit_cost_count

        breakdown = []

        # Downtime cost
        if total_downtime_minutes > 0 and avg_hourly_rate > 0:
            cost, formula = calculate_downtime_cost(total_downtime_minutes, avg_hourly_rate)
            breakdown.append(CostBreakdown(
                category="downtime",
                amount=cost,
                calculation_basis={
                    "downtime_minutes": total_downtime_minutes,
                    "standard_hourly_rate": round(avg_hourly_rate, 2),
                },
                formula_used=formula,
            ))

        # Waste cost
        if total_waste_count > 0 and avg_cost_per_unit > 0:
            cost, formula = calculate_waste_cost(total_waste_count, avg_cost_per_unit)
            breakdown.append(CostBreakdown(
                category="waste",
                amount=cost,
                calculation_basis={
                    "waste_count": total_waste_count,
                    "cost_per_unit": round(avg_cost_per_unit, 2),
                },
                formula_used=formula,
            ))

        return breakdown

    def _calculate_per_asset_breakdown(
        self, metrics: List[FinancialMetrics]
    ) -> List[AssetFinancialSummary]:
        """
        Calculate per-asset financial breakdown for area queries.

        AC#2: Shows per-asset breakdown for area queries.
        """
        # Group by asset
        asset_data: Dict[str, Dict] = {}

        for m in metrics:
            if m.asset_id not in asset_data:
                asset_data[m.asset_id] = {
                    "asset_id": m.asset_id,
                    "asset_name": m.asset_name or "Unknown",
                    "downtime_minutes": 0,
                    "waste_count": 0,
                    "hourly_rate": None,
                    "cost_per_unit": None,
                }

            asset_data[m.asset_id]["downtime_minutes"] += m.downtime_minutes
            asset_data[m.asset_id]["waste_count"] += m.waste_count

            # Keep the rate if available
            if m.standard_hourly_rate:
                asset_data[m.asset_id]["hourly_rate"] = float(m.standard_hourly_rate)
            if m.cost_per_unit:
                asset_data[m.asset_id]["cost_per_unit"] = float(m.cost_per_unit)

        # Calculate costs for each asset
        summaries = []
        for asset_id, data in asset_data.items():
            downtime_cost = 0.0
            waste_cost = 0.0

            if data["downtime_minutes"] > 0 and data["hourly_rate"]:
                downtime_cost, _ = calculate_downtime_cost(
                    data["downtime_minutes"], data["hourly_rate"]
                )

            if data["waste_count"] > 0 and data["cost_per_unit"]:
                waste_cost, _ = calculate_waste_cost(
                    data["waste_count"], data["cost_per_unit"]
                )

            summaries.append(AssetFinancialSummary(
                asset_id=data["asset_id"],
                asset_name=data["asset_name"],
                total_loss=downtime_cost + waste_cost,
                downtime_cost=downtime_cost,
                waste_cost=waste_cost,
                hourly_rate=data["hourly_rate"],
                cost_per_unit=data["cost_per_unit"],
                downtime_minutes=data["downtime_minutes"],
                waste_count=data["waste_count"],
            ))

        # Sort by total loss descending
        summaries.sort(key=lambda x: x.total_loss, reverse=True)
        return summaries

    async def _calculate_average_comparison(
        self,
        data_source,
        metrics: List[FinancialMetrics],
        asset_id: Optional[str],
        area: Optional[str],
        current_range: TimeRange,
    ) -> Optional[AverageComparison]:
        """
        Calculate comparison to historical average.

        AC#1: Comparison to average loss for this asset.
        """
        try:
            # Get 30-day historical data for average calculation
            today = date.today()
            start_date = today - timedelta(days=30)
            end_date = today - timedelta(days=1)

            historical_result = await data_source.get_financial_metrics(
                start_date=start_date,
                end_date=end_date,
                asset_id=asset_id,
                area=area,
            )

            if not historical_result.has_data:
                return None

            historical_metrics: List[FinancialMetrics] = historical_result.data

            # Calculate average daily loss from historical data
            # Group by date to get daily totals
            daily_totals: Dict[date, float] = {}
            for m in historical_metrics:
                if m.report_date not in daily_totals:
                    daily_totals[m.report_date] = 0.0

                if m.downtime_minutes > 0 and m.standard_hourly_rate:
                    cost, _ = calculate_downtime_cost(
                        m.downtime_minutes, float(m.standard_hourly_rate)
                    )
                    daily_totals[m.report_date] += cost

                if m.waste_count > 0 and m.cost_per_unit:
                    cost, _ = calculate_waste_cost(m.waste_count, float(m.cost_per_unit))
                    daily_totals[m.report_date] += cost

            if not daily_totals:
                return None

            average_daily_loss = sum(daily_totals.values()) / len(daily_totals)

            # Calculate current period loss
            current_breakdown = self._calculate_breakdown(metrics)
            current_loss = sum(b.amount for b in current_breakdown)

            # Calculate number of days in current period for comparison
            num_days = (current_range.end - current_range.start).days + 1
            current_daily_avg = current_loss / num_days if num_days > 0 else current_loss

            # Calculate variance
            variance = current_daily_avg - average_daily_loss
            variance_percent = (
                (variance / average_daily_loss * 100)
                if average_daily_loss > 0
                else 0.0
            )

            # Build comparison text
            if variance > 0:
                comparison_text = f"${abs(variance):.2f} ({abs(variance_percent):.1f}%) above average"
            elif variance < 0:
                comparison_text = f"${abs(variance):.2f} ({abs(variance_percent):.1f}%) below average"
            else:
                comparison_text = "On average"

            return AverageComparison(
                average_daily_loss=round(average_daily_loss, 2),
                current_loss=round(current_daily_avg, 2),
                variance=round(variance, 2),
                variance_percent=round(variance_percent, 1),
                comparison_text=comparison_text,
            )

        except Exception as e:
            logger.warning(f"Could not calculate average comparison: {e}")
            return None

    # =========================================================================
    # Missing Data Handling (AC#3)
    # =========================================================================

    def _missing_cost_center_response(
        self,
        metrics: List[FinancialMetrics],
        scope: str,
        time_range: str,
        citations: List[Citation],
    ) -> ToolResult:
        """
        Format honest response when cost center data is missing.

        AC#3: Returns available non-financial metrics with clear message.
        """
        non_financial = []
        for m in metrics:
            non_financial.append(NonFinancialMetric(
                asset_id=m.asset_id,
                asset_name=m.asset_name or "Unknown",
                downtime_minutes=m.downtime_minutes if m.downtime_minutes > 0 else None,
                waste_count=m.waste_count if m.waste_count > 0 else None,
                note="Unable to calculate financial impact - no cost center data",
            ))

        output = FinancialImpactOutput(
            scope=scope,
            time_range=time_range,
            total_loss=None,
            breakdown=[],
            per_asset_breakdown=None,
            highest_cost_asset=None,
            average_comparison=None,
            message=(
                f"Unable to calculate financial impact for {scope} - "
                "no cost center data configured for these assets. "
                "Available metrics: downtime and waste counts."
            ),
            non_financial_metrics=non_financial,
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
        output = FinancialImpactOutput(
            scope=scope,
            time_range=time_range,
            total_loss=0.0,
            breakdown=[],
            per_asset_breakdown=None,
            highest_cost_asset=None,
            average_comparison=None,
            message=f"No data found for {scope} in {time_range}.",
            non_financial_metrics=None,
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
                    "Show me plant-wide financial impact",
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

    def _create_calculation_citation(self, breakdown: List[CostBreakdown]) -> Citation:
        """
        Create citation for calculation evidence.

        AC#5: Citations reference both source data and calculation basis.
        """
        # Summarize rates used
        rates_used = []
        for b in breakdown:
            if b.category == "downtime":
                rate = b.calculation_basis.get("standard_hourly_rate")
                if rate:
                    rates_used.append(f"standard_hourly_rate: ${rate}/hr")
            elif b.category == "waste":
                rate = b.calculation_basis.get("cost_per_unit")
                if rate:
                    rates_used.append(f"cost_per_unit: ${rate}/unit")

        excerpt = "; ".join(rates_used) if rates_used else "calculation basis"

        return self._create_citation(
            source="calculation",
            query=f"Financial calculation using cost_centers rates: {excerpt}",
            table="cost_centers",
            confidence=1.0,
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _build_scope_description(
        self,
        area: Optional[str],
        asset_id: Optional[str],
    ) -> str:
        """Build human-readable scope description."""
        if asset_id:
            return f"asset {asset_id}"
        elif area:
            return f"the {area} area"
        else:
            return "the plant"

    def _generate_follow_ups(
        self,
        output: FinancialImpactOutput,
        area: Optional[str],
        asset_id: Optional[str],
    ) -> List[str]:
        """
        Generate context-aware follow-up questions.

        Args:
            output: The financial impact result
            area: Area filter if used
            asset_id: Asset filter if used

        Returns:
            List of suggested questions (max 3)
        """
        questions = []

        if output.total_loss and output.total_loss > 0:
            # Suggest drilling into specific costs
            if output.breakdown:
                highest_category = max(output.breakdown, key=lambda x: x.amount)
                if highest_category.category == "downtime":
                    questions.append("What are the main causes of downtime?")
                elif highest_category.category == "waste":
                    questions.append("What's causing the waste issues?")

            # For area queries, suggest asset drill-down
            if area and output.per_asset_breakdown:
                questions.append("Show me more details on the highest cost asset")

            # For asset queries, suggest area comparison
            if asset_id and not area:
                questions.append("How does this compare to other assets in the area?")

        # Suggest time comparisons
        if output.time_range == "yesterday":
            questions.append("What was the financial impact this week?")
        elif output.time_range == "this week":
            questions.append("Show me the trend over the last month")

        return questions[:3]
