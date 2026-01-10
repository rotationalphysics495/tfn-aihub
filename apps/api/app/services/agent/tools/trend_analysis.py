"""
Trend Analysis Tool (Story 6.4)

Tool for analyzing performance trends over time with anomaly detection.
Helps plant managers identify patterns, anomalies, and the impact of changes.

AC#1: Basic Trend Query - Returns trend direction, statistics, anomalies, baseline comparison
AC#2: Metric-Specific Trend Query - Supports OEE, output, downtime, waste, etc.
AC#3: Custom Time Range Query - Supports 7-90 days with granularity adjustment
AC#4: Insufficient Data Handling - Honest response when <7 days of data
AC#5: Anomaly Detection - Values >2 std dev from mean with possible causes
AC#6: Citation Compliance - All responses include citations with source and date range
AC#7: Performance Requirements - <2s response time, 15-minute cache TTL
"""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Type

import numpy as np
from pydantic import BaseModel

from app.models.agent import (
    MetricType,
    MinMaxValue,
    TrendAnalysisDirection,
    TrendAnalysisInput,
    TrendAnalysisOutput,
    TrendAnomaly,
    TrendBaselineComparison,
    TrendBaselinePeriod,
    TrendStatistics,
)
from app.services.agent.base import Citation, ManufacturingTool, ToolResult
from app.services.agent.cache import cached_tool
from app.services.agent.data_source import (
    DataResult,
    DataSourceError,
    get_data_source,
)

logger = logging.getLogger(__name__)

# Cache TTL for daily data (15 minutes)
CACHE_TTL_DAILY = 900  # 15 minutes

# Trend threshold: 5% change for stable classification
TREND_THRESHOLD = 0.05

# Anomaly threshold: 2 standard deviations from mean
ANOMALY_THRESHOLD_STD_DEV = 2.0

# Maximum number of anomalies to return
MAX_ANOMALIES = 5

# Minimum data points required for trend analysis
MIN_DATA_POINTS = 7


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)


class TrendAnalysisTool(ManufacturingTool):
    """
    Analyze performance trends over time with anomaly detection.

    Story 6.4: Trend Analysis Tool Implementation

    Use this tool when a user asks about:
    - How an asset has performed over time
    - Performance trends (improving/declining)
    - Historical performance patterns
    - Anomalies or unusual performance
    - Comparison to baseline

    Examples:
        - "How has Grinder 5 performed over the last 30 days?"
        - "What's the OEE trend for the Grinding area?"
        - "Show me any anomalies in Packaging performance"
        - "Compare current performance to baseline"
    """

    name: str = "trend_analysis"
    description: str = (
        "Analyze performance trends over time with anomaly detection. "
        "Use this tool when user asks about performance trends, historical patterns, "
        "how an asset has performed over time, anomalies, or baseline comparison. "
        "Supports metrics: OEE, output, downtime, waste, availability, performance, quality. "
        "Time ranges: 7, 14, 30, 60, or 90 days. "
        "Returns trend direction (improving/declining/stable), statistics (mean, min, max), "
        "anomalies (>2 std dev), and baseline comparison (first week vs current). "
        "Examples: 'How has Grinder 5 performed over the last 30 days?', "
        "'OEE trend for Grinding area', 'Show me anomalies in performance'"
    )
    args_schema: Type[BaseModel] = TrendAnalysisInput
    citations_required: bool = True

    # Story 5.8 / 6.4 AC#7: Apply caching with daily tier (15 minute TTL)
    @cached_tool(tier="daily")
    async def _arun(
        self,
        asset_id: Optional[str] = None,
        area: Optional[str] = None,
        metric: str = "oee",
        time_range_days: int = 30,
        **kwargs,
    ) -> ToolResult:
        """
        Execute trend analysis query and return structured results.

        AC#1-7: Complete trend analysis implementation

        Args:
            asset_id: Optional asset UUID to analyze
            area: Optional area name to analyze
            metric: Metric to analyze (default: "oee")
            time_range_days: Number of days to analyze (default: 30)

        Returns:
            ToolResult with TrendAnalysisOutput data and citations
        """
        data_source = get_data_source()
        citations: List[Citation] = []

        # Build scope description for messages
        scope = self._build_scope_description(asset_id, area)

        logger.info(
            f"Trend analysis requested: asset_id='{asset_id}', "
            f"area='{area}', metric='{metric}', days={time_range_days}"
        )

        try:
            # Calculate date range
            end_date = date.today()
            start_date = end_date - timedelta(days=time_range_days)

            # Query trend data
            result = await data_source.get_trend_data(
                start_date=start_date,
                end_date=end_date,
                metric=metric,
                asset_id=asset_id,
                area=area,
            )
            citations.append(self._result_to_citation(result, start_date, end_date))

            # Extract values and dates from data
            data_points = result.data if result.has_data else []

            # Filter out None values
            valid_data = [d for d in data_points if d.get("value") is not None]

            # Check minimum data requirement (AC#4)
            if len(valid_data) < MIN_DATA_POINTS:
                return self._insufficient_data_response(
                    scope=scope,
                    metric=metric,
                    time_range_days=time_range_days,
                    available_data=valid_data,
                    citations=citations,
                )

            # Extract values as numpy array for calculations
            values = np.array([float(d["value"]) for d in valid_data])
            dates = [d["date"] for d in valid_data]

            # Calculate statistics (AC#1)
            statistics = self._calculate_statistics(values, dates)

            # Determine trend direction (AC#1)
            trend_direction = self._determine_trend_direction(values, metric)

            # Detect anomalies (AC#5)
            anomalies = self._detect_anomalies(values, dates, valid_data)

            # Calculate baseline comparison (AC#1)
            baseline = self._calculate_baseline_comparison(values, dates)

            # Determine granularity (AC#3)
            granularity = "daily" if time_range_days <= 30 else "weekly"

            # Generate conclusion text
            conclusion = self._generate_conclusion(
                scope=scope,
                metric=metric,
                time_range_days=time_range_days,
                trend_direction=trend_direction,
                statistics=statistics,
                anomalies=anomalies,
                baseline=baseline,
            )

            # Build output
            output = TrendAnalysisOutput(
                scope=scope,
                metric=metric,
                time_range_days=time_range_days,
                trend_direction=trend_direction.value if trend_direction else None,
                statistics=statistics,
                anomalies=anomalies,
                baseline_comparison=baseline,
                conclusion_text=conclusion,
                granularity=granularity,
                data_freshness=_utcnow().isoformat(),
            )

            # Generate follow-up questions
            follow_ups = self._generate_follow_ups(output, asset_id, area)

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
            logger.error(f"Data source error during trend analysis: {e}")
            return self._create_error_result(
                f"Unable to retrieve trend data for {scope}. Please try again later."
            )
        except Exception as e:
            logger.exception(f"Unexpected error during trend analysis: {e}")
            return self._create_error_result(
                "An unexpected error occurred while analyzing trends. "
                "Please try again or contact support."
            )

    # =========================================================================
    # Statistical Calculations (AC#1, AC#5)
    # =========================================================================

    def _calculate_statistics(
        self,
        values: np.ndarray,
        dates: List[str],
    ) -> TrendStatistics:
        """
        Calculate descriptive statistics for time series.

        AC#1: Returns mean, min/max with dates, std dev, and trend slope.
        """
        mean = float(np.mean(values))
        std_dev = float(np.std(values))
        min_idx = int(np.argmin(values))
        max_idx = int(np.argmax(values))

        # Calculate trend slope using numpy polyfit (linear regression)
        x = np.arange(len(values))
        # polyfit returns [slope, intercept] for degree 1
        slope, _ = np.polyfit(x, values, 1)

        return TrendStatistics(
            mean=round(mean, 2),
            min=MinMaxValue(
                value=round(float(values[min_idx]), 2),
                date=dates[min_idx],
            ),
            max=MinMaxValue(
                value=round(float(values[max_idx]), 2),
                date=dates[max_idx],
            ),
            std_dev=round(std_dev, 2),
            trend_slope=round(float(slope), 4),
        )

    def _determine_trend_direction(
        self,
        values: np.ndarray,
        metric: str,
    ) -> TrendAnalysisDirection:
        """
        Determine trend direction based on linear regression slope.

        Uses 5% threshold normalized by mean to determine stability.
        For downtime and waste metrics, inverse the direction (increasing = declining).
        """
        x = np.arange(len(values))
        # polyfit returns [slope, intercept] for degree 1
        slope, _ = np.polyfit(x, values, 1)

        # Normalize slope by mean for percentage-based threshold
        mean = float(np.mean(values))
        if mean == 0:
            return TrendAnalysisDirection.STABLE

        # Total change over period as percentage of mean
        total_change = slope * len(values)
        change_percent = total_change / mean

        # For downtime and waste, increasing is bad (declining performance)
        inverse_metrics = {"downtime", "waste"}
        if metric.lower() in inverse_metrics:
            change_percent = -change_percent

        if change_percent > TREND_THRESHOLD:
            return TrendAnalysisDirection.IMPROVING
        elif change_percent < -TREND_THRESHOLD:
            return TrendAnalysisDirection.DECLINING
        else:
            return TrendAnalysisDirection.STABLE

    def _detect_anomalies(
        self,
        values: np.ndarray,
        dates: List[str],
        raw_data: List[Dict[str, Any]],
    ) -> List[TrendAnomaly]:
        """
        Detect anomalies as values >2 standard deviations from mean.

        AC#5: Each anomaly includes date, value, deviation, and possible cause.
        """
        mean = float(np.mean(values))
        std_dev = float(np.std(values))

        if std_dev == 0:
            return []

        anomalies = []
        for i, (value, date_str) in enumerate(zip(values, dates)):
            deviation = abs(float(value) - mean)
            std_devs_away = deviation / std_dev

            if std_devs_away > ANOMALY_THRESHOLD_STD_DEV:
                # Try to find possible cause from downtime_reasons
                possible_cause = None
                if i < len(raw_data) and raw_data[i].get("downtime_reasons"):
                    reasons = raw_data[i]["downtime_reasons"]
                    if reasons and isinstance(reasons, dict):
                        # Get top downtime reason for that day
                        top_reason = max(reasons, key=reasons.get)
                        possible_cause = top_reason

                anomalies.append(
                    TrendAnomaly(
                        date=date_str,
                        value=round(float(value), 2),
                        expected_value=round(mean, 2),
                        deviation=round(deviation, 2),
                        deviation_std_devs=round(std_devs_away, 2),
                        possible_cause=possible_cause,
                    )
                )

        # Return top N most significant anomalies (AC#5: limit to top 5)
        anomalies.sort(key=lambda x: x.deviation_std_devs, reverse=True)
        return anomalies[:MAX_ANOMALIES]

    def _calculate_baseline_comparison(
        self,
        values: np.ndarray,
        dates: List[str],
    ) -> Optional[TrendBaselineComparison]:
        """
        Compare current performance to baseline (first 7 days).

        AC#1: Returns baseline period, baseline value, current value, change.
        """
        if len(values) < MIN_DATA_POINTS:
            return None

        # Baseline is first 7 days
        baseline_values = values[:7]
        baseline_dates = dates[:7]

        # Current is last 7 days (or remaining days if 7-14 total)
        if len(values) >= 14:
            current_values = values[-7:]
        else:
            current_values = values[7:]

        if len(current_values) == 0:
            return None

        baseline_avg = float(np.mean(baseline_values))
        current_avg = float(np.mean(current_values))

        change_amount = current_avg - baseline_avg
        change_percent = (change_amount / baseline_avg * 100) if baseline_avg > 0 else 0

        return TrendBaselineComparison(
            baseline_period=TrendBaselinePeriod(
                start=baseline_dates[0],
                end=baseline_dates[min(6, len(baseline_dates) - 1)],
            ),
            baseline_value=round(baseline_avg, 2),
            current_value=round(current_avg, 2),
            change_amount=round(change_amount, 2),
            change_percent=round(change_percent, 1),
        )

    # =========================================================================
    # Insufficient Data Handling (AC#4)
    # =========================================================================

    def _insufficient_data_response(
        self,
        scope: str,
        metric: str,
        time_range_days: int,
        available_data: List[Dict[str, Any]],
        citations: List[Citation],
    ) -> ToolResult:
        """
        Generate response when insufficient data for trend analysis.

        AC#4: Returns honest message with available point-in-time data.
        """
        data_count = len(available_data)
        message = (
            f"Not enough data for trend analysis - need at least {MIN_DATA_POINTS} days "
            f"(found {data_count} days). Here's the available point-in-time data:"
        )

        # Format available data for display
        formatted_data = []
        for point in available_data:
            formatted_data.append({
                "date": point.get("date"),
                "value": point.get("value"),
                "asset_name": point.get("asset_name"),
            })

        output = TrendAnalysisOutput(
            scope=scope,
            metric=metric,
            time_range_days=time_range_days,
            trend_direction=None,
            statistics=None,
            anomalies=[],
            baseline_comparison=None,
            conclusion_text=message,
            granularity="daily",
            available_data=formatted_data if formatted_data else None,
            suggestion="Try requesting a longer time range to enable trend analysis.",
            data_freshness=_utcnow().isoformat(),
        )

        return self._create_success_result(
            data=output.model_dump(),
            citations=citations,
            metadata={
                "cache_tier": "daily",
                "ttl_seconds": CACHE_TTL_DAILY,
                "insufficient_data": True,
                "available_days": data_count,
            },
        )

    # =========================================================================
    # Conclusion Generation
    # =========================================================================

    def _generate_conclusion(
        self,
        scope: str,
        metric: str,
        time_range_days: int,
        trend_direction: TrendAnalysisDirection,
        statistics: TrendStatistics,
        anomalies: List[TrendAnomaly],
        baseline: Optional[TrendBaselineComparison],
    ) -> str:
        """
        Generate human-readable conclusion about the trend.
        """
        # Metric display name
        metric_name = metric.upper() if metric.lower() == "oee" else metric.title()

        # Build base conclusion
        trend_word = trend_direction.value
        conclusion = f"{scope}'s {metric_name} has been {trend_word} over the last {time_range_days} days"

        # Add baseline comparison if available
        if baseline and baseline.change_percent != 0:
            change_direction = "up" if baseline.change_percent > 0 else "down"
            conclusion += (
                f", {change_direction} from an average of {baseline.baseline_value} "
                f"in the first week to {baseline.current_value} recently "
                f"({baseline.change_percent:+.1f}%)"
            )
        conclusion += "."

        # Add anomaly info
        if anomalies:
            if len(anomalies) == 1:
                a = anomalies[0]
                cause_text = f" likely due to {a.possible_cause}" if a.possible_cause else ""
                conclusion += (
                    f" One anomaly was detected on {a.date} "
                    f"({a.value} {metric_name}){cause_text}."
                )
            else:
                conclusion += f" {len(anomalies)} anomalies were detected."

        return conclusion

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _build_scope_description(
        self,
        asset_id: Optional[str],
        area: Optional[str],
    ) -> str:
        """Build human-readable scope description."""
        if asset_id:
            return f"Asset {asset_id}"
        elif area:
            return f"The {area} area"
        else:
            return "Plant-wide"

    def _generate_follow_ups(
        self,
        output: TrendAnalysisOutput,
        asset_id: Optional[str],
        area: Optional[str],
    ) -> List[str]:
        """
        Generate context-aware follow-up questions.
        """
        questions = []

        # If there are anomalies, suggest drilling down
        if output.anomalies:
            questions.append("What caused the anomalies in performance?")

        # If trend is declining, suggest investigation
        if output.trend_direction == "declining":
            questions.append(f"What's driving the decline in {output.metric}?")

        # Suggest comparing different metrics
        if output.metric == "oee":
            questions.append("What's the downtime trend for this period?")
        else:
            questions.append("How does OEE trend compare?")

        # Suggest area comparison if viewing plant-wide
        if not area and not asset_id:
            questions.append("Which area has the worst trend?")
        elif area and not asset_id:
            questions.append("Which asset in this area is performing worst?")

        # Time range suggestions
        if output.time_range_days == 30:
            questions.append("Show me the 90-day trend")

        return questions[:3]

    def _result_to_citation(
        self,
        result: DataResult,
        start_date: date,
        end_date: date,
    ) -> Citation:
        """
        Convert DataResult to Citation with date range.

        AC#6: Citation Compliance - includes source table and date range.
        """
        return self._create_citation(
            source=result.source_name,
            query=result.query or f"Query on {result.table_name}",
            table=result.table_name,
            record_id=f"{start_date} to {end_date}",
        )
