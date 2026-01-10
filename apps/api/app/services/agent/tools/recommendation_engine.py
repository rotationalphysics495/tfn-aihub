"""
Recommendation Engine Tool (Story 7.5)

Tool for analyzing patterns and suggesting specific improvements for assets
or plant-wide operations. Provides proactive optimization suggestions based
on detected patterns in historical data.

AC#1: Asset-Specific Recommendations - 2-3 specific recommendations with
      what to do, expected impact, supporting evidence, similar past solutions
AC#2: Plant-Wide Analysis - Analyzes plant-wide patterns, ranks by ROI
AC#3: Focus Area Recommendations - Filters recommendations by focus area
AC#4: Insufficient Data Handling - Clear message when insufficient data
AC#5: Recommendation Confidence - High (>80%) and Medium (60-80%) shown,
      Low (<60%) filtered out
AC#6: Data Sources & Caching - Query daily_summaries, cost_centers, memories;
      15-minute cache TTL
"""

import logging
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Type

from pydantic import BaseModel

from app.models.agent import (
    PatternEvidence,
    Recommendation,
    RecommendationCitation,
    RecommendationInput,
    RecommendationOutput,
)
from app.services.agent.base import Citation, ManufacturingTool, ToolResult
from app.services.agent.cache import cached_tool
from app.services.agent.data_source import (
    Asset,
    DataResult,
    DataSourceError,
    get_data_source,
)
from app.services.agent.tools.memory_recall import get_current_user_id
from app.services.memory.mem0_service import MemoryService, get_memory_service

logger = logging.getLogger(__name__)


# Confidence thresholds (AC#5)
CONFIDENCE_HIGH = 0.80
CONFIDENCE_MEDIUM = 0.60  # Filter threshold - patterns below this are excluded

# Minimum data points for reliable pattern detection (AC#4)
MINIMUM_DATA_POINTS = 10

# Maximum recommendations per response (AC#1)
MAX_RECOMMENDATIONS = 3

# Focus area keywords for filtering (AC#3)
FOCUS_AREA_KEYWORDS = {
    "oee": ["oee", "efficiency", "overall equipment effectiveness", "performance"],
    "waste": ["waste", "scrap", "rework", "quality", "defect"],
    "safety": ["safety", "incident", "hazard", "injury", "stop"],
    "cost": ["cost", "loss", "financial", "dollar", "expense", "savings"],
    "downtime": ["downtime", "stoppage", "breakdown", "maintenance", "idle"],
}

# Default hourly cost for ROI calculations (from cost_centers when available)
DEFAULT_HOURLY_COST = 2000.0


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)


class RecommendationEngineTool(ManufacturingTool):
    """
    Analyze patterns and suggest specific improvements for assets or plant-wide.

    Story 7.5: Recommendation Engine Implementation

    Use this tool when the user asks 'How can we improve...?',
    'What should we focus on improving?', 'How do we reduce waste/downtime?',
    or wants proactive optimization suggestions. Returns 2-3 actionable
    recommendations with supporting evidence and expected impact.

    Examples:
        - "How can we improve OEE for Grinder 5?"
        - "What should we focus on improving?"
        - "How do we reduce waste?"
        - "Any suggestions for better performance?"
        - "What improvements would you recommend?"
    """

    name: str = "recommendation_engine"
    description: str = (
        "Analyze patterns and suggest specific improvements for assets "
        "or plant-wide operations. Use this when user asks 'How can we improve...?', "
        "'What should we focus on improving?', 'How do we reduce waste/downtime?', "
        "or wants proactive optimization suggestions. Returns 2-3 actionable "
        "recommendations with supporting evidence and expected impact."
    )
    args_schema: Type[BaseModel] = RecommendationInput
    citations_required: bool = True

    def __init__(self, **kwargs):
        """Initialize the Recommendation Engine tool."""
        super().__init__(**kwargs)
        self._memory_service: Optional[MemoryService] = None

    def _get_memory_service(self) -> MemoryService:
        """Get the memory service (lazy initialization)."""
        if self._memory_service is None:
            self._memory_service = get_memory_service()
        return self._memory_service

    def _get_user_id(self) -> Optional[str]:
        """Get the current user ID from context."""
        return get_current_user_id()

    @cached_tool(tier="daily")  # AC#6: 15-minute cache (daily tier = 900s)
    async def _arun(
        self,
        subject: str,
        focus_area: Optional[str] = None,
        time_range_days: int = 30,
        **kwargs,
    ) -> ToolResult:
        """
        Execute recommendation analysis and return structured results.

        AC#1-6: Complete recommendation engine implementation

        Args:
            subject: Asset name or 'plant-wide' for overall analysis
            focus_area: Optional focus area filter (oee, waste, safety, cost, downtime)
            time_range_days: Days of historical data to analyze (default: 30)

        Returns:
            ToolResult with RecommendationOutput data and citations
        """
        data_source = get_data_source()
        citations: List[Citation] = []

        logger.info(
            f"Recommendation engine requested: subject='{subject}', "
            f"focus_area={focus_area}, time_range_days={time_range_days}"
        )

        try:
            now = _utcnow()
            end_date = now.date()
            start_date = end_date - timedelta(days=time_range_days)
            time_range_str = self._format_date_range(start_date, end_date)

            # Determine if this is plant-wide or asset-specific
            is_plant_wide = subject.lower() == "plant-wide"

            # Fetch analysis data
            if is_plant_wide:
                data, asset_info, data_citations = await self._fetch_plant_wide_data(
                    start_date, end_date, data_source
                )
            else:
                data, asset_info, data_citations = await self._fetch_asset_data(
                    subject, start_date, end_date, data_source
                )

            citations.extend(data_citations)

            # AC#4: Check data sufficiency
            if len(data) < MINIMUM_DATA_POINTS:
                return self._insufficient_data_response(
                    subject=subject,
                    focus_area=focus_area,
                    data_points=len(data),
                    time_range_days=time_range_days,
                    time_range_str=time_range_str,
                    citations=citations,
                )

            # Detect patterns (AC#2, AC#5)
            all_patterns: List[Dict[str, Any]] = []
            all_patterns.extend(
                self._detect_recurring_downtime(data, focus_area)
            )
            all_patterns.extend(
                self._detect_time_patterns(data, focus_area)
            )

            # For plant-wide, also detect cross-asset correlations
            if is_plant_wide:
                all_patterns.extend(
                    self._detect_cross_asset_correlations(data, focus_area)
                )

            # Filter by confidence (AC#5)
            high_confidence = [
                p for p in all_patterns
                if p["confidence_score"] >= CONFIDENCE_HIGH
            ]
            medium_confidence = [
                p for p in all_patterns
                if CONFIDENCE_MEDIUM <= p["confidence_score"] < CONFIDENCE_HIGH
            ]
            filtered_count = len([
                p for p in all_patterns
                if p["confidence_score"] < CONFIDENCE_MEDIUM
            ])

            valid_patterns = high_confidence + medium_confidence

            # Get past solutions from memory (AC#1)
            past_solutions = await self._get_past_solutions(subject, focus_area)

            # Generate recommendations from patterns (AC#1, AC#3)
            recommendations = self._generate_recommendations(
                patterns=valid_patterns,
                past_solutions=past_solutions,
                focus_area=focus_area,
                subject=subject,
                asset_info=asset_info,
            )

            # Rank by ROI and limit to 3 (AC#1)
            recommendations.sort(
                key=lambda r: float(r.estimated_roi or 0),
                reverse=True
            )
            recommendations = recommendations[:MAX_RECOMMENDATIONS]

            # Assign priorities
            for i, rec in enumerate(recommendations):
                rec.priority = i + 1

            # Generate analysis summary
            analysis_summary = self._generate_analysis_summary(
                subject=subject,
                recommendations=recommendations,
                patterns_detected=len(all_patterns),
                patterns_filtered=filtered_count,
            )

            # Build citations (AC#6)
            rec_citations = [
                RecommendationCitation(
                    source_type="daily_summaries",
                    date_range=time_range_str,
                    asset_id=asset_info.get("id") if asset_info else None,
                    pattern_types=list({p["pattern_type"] for p in valid_patterns}),
                    display_text=f"[Source: daily_summaries {time_range_str}]",
                )
            ]

            # Build output
            output = RecommendationOutput(
                recommendations=recommendations,
                analysis_summary=analysis_summary,
                patterns_detected=len(all_patterns),
                patterns_filtered=filtered_count,
                data_coverage=f"{time_range_days} days, {len(data)} data points",
                insufficient_data=False,
                data_gaps=[],
                subject=subject,
                focus_area=focus_area,
                citations=rec_citations,
                data_freshness=now.isoformat(),
            )

            # Generate follow-up suggestions
            follow_ups = self._generate_follow_ups(output)

            return self._create_success_result(
                data=output.model_dump(),
                citations=citations,
                metadata={
                    "cache_tier": "daily",
                    "follow_up_questions": follow_ups,
                    "query_timestamp": now.isoformat(),
                    "patterns_analyzed": len(all_patterns),
                    "recommendations_generated": len(recommendations),
                },
            )

        except DataSourceError as e:
            logger.error(f"Data source error during recommendation analysis: {e}")
            return self._create_error_result(
                "Unable to retrieve data for analysis. Please try again later."
            )
        except Exception as e:
            logger.exception(f"Unexpected error during recommendation analysis: {e}")
            return self._create_error_result(
                "An unexpected error occurred during analysis. "
                "Please try again or contact support."
            )

    # =========================================================================
    # Data Fetching
    # =========================================================================

    async def _fetch_asset_data(
        self,
        asset_name: str,
        start_date: date,
        end_date: date,
        data_source,
    ) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]], List[Citation]]:
        """
        Fetch historical data for a specific asset.

        Returns:
            Tuple of (data_list, asset_info, citations)
        """
        citations: List[Citation] = []
        data: List[Dict[str, Any]] = []
        asset_info: Optional[Dict[str, Any]] = None

        # Look up asset
        asset_result = await data_source.get_asset_by_name(asset_name)
        citations.append(self._result_to_citation(asset_result))

        if not asset_result.has_data:
            # Try fuzzy matching
            return data, None, citations

        asset: Asset = asset_result.data
        asset_info = {
            "id": asset.id,
            "name": asset.name,
            "area": asset.area,
        }

        # Get OEE data
        oee_result = await data_source.get_oee(asset.id, start_date, end_date)
        citations.append(self._result_to_citation(oee_result))

        if oee_result.has_data:
            for oee_metric in oee_result.data:
                data.append({
                    "date": oee_metric.report_date,
                    "asset_id": asset.id,
                    "asset_name": asset.name,
                    "oee": float(oee_metric.oee_percentage or 0),
                    "availability": float(oee_metric.availability or 0),
                    "performance": float(oee_metric.performance or 0),
                    "quality": float(oee_metric.quality or 0),
                    "output": oee_metric.actual_output or 0,
                    "target": oee_metric.target_output or 0,
                    "downtime_minutes": oee_metric.downtime_minutes or 0,
                    "downtime_reasons": oee_metric.downtime_reasons or {},
                    "waste_count": oee_metric.waste_count or 0,
                    "financial_loss": float(oee_metric.financial_loss_dollars or 0),
                })

        return data, asset_info, citations

    async def _fetch_plant_wide_data(
        self,
        start_date: date,
        end_date: date,
        data_source,
    ) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]], List[Citation]]:
        """
        Fetch historical data for all assets (plant-wide).

        Returns:
            Tuple of (data_list, asset_info, citations)
        """
        citations: List[Citation] = []
        data: List[Dict[str, Any]] = []

        # Get all assets
        assets_result = await data_source.get_all_assets()
        citations.append(self._result_to_citation(assets_result))

        if not assets_result.has_data:
            return data, None, citations

        # Fetch OEE for each asset
        for asset in assets_result.data:
            oee_result = await data_source.get_oee(asset.id, start_date, end_date)
            # Don't add individual citations for plant-wide to avoid bloat

            if oee_result.has_data:
                for oee_metric in oee_result.data:
                    data.append({
                        "date": oee_metric.report_date,
                        "asset_id": asset.id,
                        "asset_name": asset.name,
                        "area": asset.area,
                        "oee": float(oee_metric.oee_percentage or 0),
                        "availability": float(oee_metric.availability or 0),
                        "performance": float(oee_metric.performance or 0),
                        "quality": float(oee_metric.quality or 0),
                        "output": oee_metric.actual_output or 0,
                        "target": oee_metric.target_output or 0,
                        "downtime_minutes": oee_metric.downtime_minutes or 0,
                        "downtime_reasons": oee_metric.downtime_reasons or {},
                        "waste_count": oee_metric.waste_count or 0,
                        "financial_loss": float(oee_metric.financial_loss_dollars or 0),
                    })

        # Add one summary citation for plant-wide data
        citations.append(self._create_citation(
            source="daily_summaries",
            query=f"Plant-wide OEE data from {start_date} to {end_date}",
            table="daily_summaries",
        ))

        return data, {"name": "plant-wide", "id": None}, citations

    # =========================================================================
    # Pattern Detection (AC#2, AC#5)
    # =========================================================================

    def _detect_recurring_downtime(
        self,
        data: List[Dict[str, Any]],
        focus_area: Optional[str],
    ) -> List[Dict[str, Any]]:
        """
        Detect recurring downtime reasons.

        AC#5: Calculate confidence scores for each pattern.
        """
        patterns: List[Dict[str, Any]] = []

        # Collect all downtime reasons across data
        all_reasons: List[str] = []
        for d in data:
            reasons = d.get("downtime_reasons", {})
            if isinstance(reasons, dict):
                all_reasons.extend(reasons.keys())
            elif isinstance(reasons, list):
                all_reasons.extend(reasons)

        if not all_reasons:
            return patterns

        # Count reason occurrences
        reason_counts = Counter(all_reasons)
        total_occurrences = len(all_reasons)

        for reason, count in reason_counts.most_common(5):
            if not reason or reason.strip() == "":
                continue

            frequency = count / len(data) if len(data) > 0 else 0

            # Only consider reasons that appear in at least 10% of records
            if frequency < 0.10:
                continue

            # Calculate confidence based on frequency and sample size
            # Higher frequency + more data points = higher confidence
            sample_factor = min(1.0, len(data) / 30)  # Scale up to 30 days
            confidence = min(0.95, (frequency * 1.5 + 0.4) * sample_factor)

            patterns.append({
                "pattern_type": "recurring_downtime",
                "description": f"'{reason}' occurs frequently ({frequency*100:.0f}% of days)",
                "frequency": frequency,
                "affected_periods": [f"{count} occurrences in {len(data)} days"],
                "data_points": count,
                "confidence_score": confidence,
                "reason": reason,
                "focus_relevance": self._get_focus_relevance(reason, focus_area),
            })

        return patterns

    def _detect_time_patterns(
        self,
        data: List[Dict[str, Any]],
        focus_area: Optional[str],
    ) -> List[Dict[str, Any]]:
        """
        Detect time-of-day or day-of-week patterns.

        Looks for days with consistently worse performance.
        """
        patterns: List[Dict[str, Any]] = []

        if len(data) < 7:
            return patterns

        # Group data by day of week
        by_day: Dict[str, List[float]] = {}
        for d in data:
            date_val = d.get("date")
            if not date_val:
                continue

            if isinstance(date_val, str):
                try:
                    date_val = datetime.fromisoformat(date_val).date()
                except ValueError:
                    continue

            day_name = date_val.strftime("%A")
            oee = d.get("oee", 0)
            if oee > 0:
                by_day.setdefault(day_name, []).append(oee)

        if not by_day:
            return patterns

        # Calculate overall average
        all_oee = [oee for d in data if (oee := d.get("oee", 0)) > 0]
        if not all_oee:
            return patterns
        overall_avg = sum(all_oee) / len(all_oee)

        # Find problematic days (>10% worse than average)
        for day, values in by_day.items():
            if len(values) < 2:
                continue

            day_avg = sum(values) / len(values)

            # Check if this day is significantly worse
            if day_avg < overall_avg * 0.90:  # 10% worse than average
                variance = abs(overall_avg - day_avg) / overall_avg if overall_avg > 0 else 0
                sample_factor = min(1.0, len(values) / 4)  # Need at least 4 Mondays
                confidence = min(0.90, (variance + 0.5) * sample_factor)

                patterns.append({
                    "pattern_type": "time_of_day",
                    "description": (
                        f"Performance drops on {day}s "
                        f"(avg {day_avg:.1f}% vs {overall_avg:.1f}% overall)"
                    ),
                    "frequency": 1 / 7,  # Weekly
                    "affected_periods": [f"{day}s"],
                    "data_points": len(values),
                    "confidence_score": confidence,
                    "day": day,
                    "day_avg": day_avg,
                    "overall_avg": overall_avg,
                    "focus_relevance": self._get_focus_relevance("performance", focus_area),
                })

        return patterns

    def _detect_cross_asset_correlations(
        self,
        data: List[Dict[str, Any]],
        focus_area: Optional[str],
    ) -> List[Dict[str, Any]]:
        """
        Detect cross-asset correlation patterns (for plant-wide analysis).

        Finds assets that consistently underperform relative to others.
        """
        patterns: List[Dict[str, Any]] = []

        if len(data) < 20:
            return patterns

        # Group by asset
        by_asset: Dict[str, List[float]] = {}
        for d in data:
            asset_name = d.get("asset_name")
            oee = d.get("oee", 0)
            if asset_name and oee > 0:
                by_asset.setdefault(asset_name, []).append(oee)

        if len(by_asset) < 2:
            return patterns

        # Calculate averages per asset
        asset_avgs = {
            asset: sum(values) / len(values)
            for asset, values in by_asset.items()
            if len(values) >= 3
        }

        if not asset_avgs:
            return patterns

        # Find plant-wide average
        plant_avg = sum(asset_avgs.values()) / len(asset_avgs)

        # Find underperforming assets (>15% below average)
        for asset, avg in asset_avgs.items():
            if avg < plant_avg * 0.85:
                variance = abs(plant_avg - avg) / plant_avg if plant_avg > 0 else 0
                confidence = min(0.85, variance + 0.5)

                patterns.append({
                    "pattern_type": "cross_asset",
                    "description": (
                        f"{asset} consistently underperforms "
                        f"(avg {avg:.1f}% vs plant avg {plant_avg:.1f}%)"
                    ),
                    "frequency": 1.0,  # Consistent pattern
                    "affected_periods": [f"{asset} (all periods)"],
                    "data_points": len(by_asset.get(asset, [])),
                    "confidence_score": confidence,
                    "asset": asset,
                    "asset_avg": avg,
                    "plant_avg": plant_avg,
                    "focus_relevance": self._get_focus_relevance("oee", focus_area),
                })

        return patterns

    def _get_focus_relevance(
        self,
        pattern_topic: str,
        focus_area: Optional[str],
    ) -> float:
        """
        Calculate how relevant a pattern is to the focus area.

        Returns 1.0 if no focus area or pattern matches focus area.
        Returns lower score if pattern doesn't match focus area.
        """
        if not focus_area:
            return 1.0

        focus_keywords = FOCUS_AREA_KEYWORDS.get(focus_area.lower(), [])
        pattern_lower = pattern_topic.lower()

        for keyword in focus_keywords:
            if keyword in pattern_lower:
                return 1.0

        return 0.5  # Partial relevance for non-matching patterns

    # =========================================================================
    # Memory Integration (AC#1)
    # =========================================================================

    async def _get_past_solutions(
        self,
        subject: str,
        focus_area: Optional[str],
    ) -> List[str]:
        """
        Query Mem0 for similar past solutions.

        AC#1: Similar situations where this worked (from memory).
        """
        user_id = self._get_user_id()
        if not user_id:
            return []

        try:
            memory_service = self._get_memory_service()

            if not memory_service.is_configured():
                return []

            # Build search query
            query = f"successful improvements for {subject}"
            if focus_area:
                query += f" related to {focus_area}"

            # Search memories
            memories = await memory_service.search_memory(
                query=query,
                user_id=user_id,
                limit=5,
                threshold=0.6,
            )

            # Extract relevant solutions
            solutions: List[str] = []
            solution_keywords = [
                "improvement", "reduced", "decreased", "fixed", "resolved",
                "implemented", "scheduled", "optimized", "improved"
            ]

            for mem in memories:
                content = mem.get("memory", mem.get("content", ""))
                content_lower = content.lower()

                # Check if memory contains solution indicators
                if any(keyword in content_lower for keyword in solution_keywords):
                    # Truncate if too long
                    if len(content) > 200:
                        content = content[:197] + "..."
                    solutions.append(content)

            return solutions[:5]  # Max 5 solutions

        except Exception as e:
            logger.warning(f"Failed to retrieve past solutions: {e}")
            return []

    # =========================================================================
    # Recommendation Generation (AC#1, AC#3)
    # =========================================================================

    def _generate_recommendations(
        self,
        patterns: List[Dict[str, Any]],
        past_solutions: List[str],
        focus_area: Optional[str],
        subject: str,
        asset_info: Optional[Dict[str, Any]],
    ) -> List[Recommendation]:
        """
        Generate actionable recommendations from detected patterns.

        AC#1: Map detected patterns to actionable recommendations.
        AC#3: Filter by focus area if specified.
        """
        recommendations: List[Recommendation] = []

        # Sort patterns by confidence * focus_relevance
        sorted_patterns = sorted(
            patterns,
            key=lambda p: p["confidence_score"] * p.get("focus_relevance", 1.0),
            reverse=True
        )

        for pattern in sorted_patterns:
            rec = self._pattern_to_recommendation(
                pattern=pattern,
                past_solutions=past_solutions,
                subject=subject,
            )

            if rec:
                # Apply focus area filter (AC#3)
                if focus_area:
                    relevance = pattern.get("focus_relevance", 1.0)
                    if relevance < 0.8:
                        continue  # Skip low-relevance patterns for focus area

                recommendations.append(rec)

        return recommendations

    def _pattern_to_recommendation(
        self,
        pattern: Dict[str, Any],
        past_solutions: List[str],
        subject: str,
    ) -> Optional[Recommendation]:
        """
        Convert a detected pattern to an actionable recommendation.
        """
        pattern_type = pattern.get("pattern_type")
        confidence_score = pattern.get("confidence_score", 0.6)
        confidence = "high" if confidence_score >= CONFIDENCE_HIGH else "medium"

        # Build pattern evidence
        evidence = PatternEvidence(
            pattern_type=pattern_type,
            description=pattern.get("description", ""),
            frequency=pattern.get("frequency", 0),
            affected_periods=pattern.get("affected_periods", []),
            data_points=pattern.get("data_points", 0),
            confidence_score=confidence_score,
        )

        # Find relevant past solutions
        relevant_solutions: List[str] = []
        pattern_desc_lower = pattern.get("description", "").lower()
        for solution in past_solutions:
            solution_lower = solution.lower()
            # Check for keyword overlap
            if any(word in solution_lower for word in pattern_desc_lower.split()[:3]):
                relevant_solutions.append(solution)
                if len(relevant_solutions) >= 2:
                    break

        if pattern_type == "recurring_downtime":
            reason = pattern.get("reason", "Unknown Issue")
            frequency = pattern.get("frequency", 0)

            # Estimate financial impact
            estimated_savings = frequency * 50 * DEFAULT_HOURLY_COST / 60  # Monthly
            estimated_roi = str(round(estimated_savings, 2))

            return Recommendation(
                title=f"Address Recurring Downtime: {reason}",
                description=f"This issue accounts for {frequency*100:.0f}% of downtime events",
                what_to_do=f"Review SOP for '{reason}', schedule preventive action, and monitor results",
                expected_impact=f"Potential {frequency*50:.0f}% reduction in {reason.lower()}-related downtime (${estimated_savings:,.0f}/month savings)",
                estimated_roi=estimated_roi,
                confidence=confidence,
                confidence_score=confidence_score,
                supporting_evidence=[evidence],
                similar_past_solutions=relevant_solutions,
                # priority is set after ranking
            )

        elif pattern_type == "time_of_day":
            day = pattern.get("day", "Unknown")
            day_avg = pattern.get("day_avg", 0)
            overall_avg = pattern.get("overall_avg", 0)
            gap = overall_avg - day_avg

            # Estimate financial impact
            estimated_savings = gap * DEFAULT_HOURLY_COST / 100 * 8  # 8 hours
            estimated_roi = str(round(estimated_savings * 4, 2))  # Monthly

            return Recommendation(
                title=f"Investigate {day} Performance Drop",
                description=f"{day} OEE averages {day_avg:.1f}% vs {overall_avg:.1f}% other days",
                what_to_do=f"Review startup procedures and staffing on {day}s, analyze first-shift variance",
                expected_impact=f"{gap:.1f}% OEE improvement on {day}s (~${estimated_savings*4:,.0f}/month)",
                estimated_roi=estimated_roi,
                confidence=confidence,
                confidence_score=confidence_score,
                supporting_evidence=[evidence],
                similar_past_solutions=relevant_solutions,
                # priority is set after ranking
            )

        elif pattern_type == "cross_asset":
            asset = pattern.get("asset", "Unknown Asset")
            asset_avg = pattern.get("asset_avg", 0)
            plant_avg = pattern.get("plant_avg", 0)
            gap = plant_avg - asset_avg

            # Estimate financial impact
            estimated_savings = gap * DEFAULT_HOURLY_COST / 100 * 8 * 22  # Monthly
            estimated_roi = str(round(estimated_savings, 2))

            return Recommendation(
                title=f"Focus on Underperforming Asset: {asset}",
                description=f"{asset} averages {asset_avg:.1f}% OEE vs plant average {plant_avg:.1f}%",
                what_to_do=f"Conduct root cause analysis on {asset}, apply best practices from higher-performing assets",
                expected_impact=f"Potential {gap:.1f}% OEE improvement on {asset} (~${estimated_savings:,.0f}/month)",
                estimated_roi=estimated_roi,
                confidence=confidence,
                confidence_score=confidence_score,
                supporting_evidence=[evidence],
                similar_past_solutions=relevant_solutions,
                # priority is set after ranking
            )

        return None

    # =========================================================================
    # Summary Generation
    # =========================================================================

    def _generate_analysis_summary(
        self,
        subject: str,
        recommendations: List[Recommendation],
        patterns_detected: int,
        patterns_filtered: int,
    ) -> str:
        """
        Generate analysis summary for the response.
        """
        if not recommendations:
            if patterns_detected > 0:
                return (
                    f"Analyzed data for {subject}. Detected {patterns_detected} patterns, "
                    f"but none met the confidence threshold for actionable recommendations."
                )
            return f"Analyzed data for {subject}. No significant patterns detected."

        rec_count = len(recommendations)
        if patterns_filtered > 0:
            return (
                f"Found {patterns_detected} patterns for {subject}. "
                f"Generated {rec_count} actionable recommendation{'s' if rec_count > 1 else ''} "
                f"({patterns_filtered} low-confidence pattern{'s' if patterns_filtered > 1 else ''} filtered)."
            )

        return (
            f"Found {patterns_detected} patterns for {subject}. "
            f"Generated {rec_count} actionable recommendation{'s' if rec_count > 1 else ''}."
        )

    # =========================================================================
    # Insufficient Data Response (AC#4)
    # =========================================================================

    def _insufficient_data_response(
        self,
        subject: str,
        focus_area: Optional[str],
        data_points: int,
        time_range_days: int,
        time_range_str: str,
        citations: List[Citation],
    ) -> ToolResult:
        """
        Generate response when insufficient data exists.

        AC#4: States 'I need more data to make specific recommendations'
        and suggests what data would help.
        """
        # Identify data gaps
        data_gaps: List[str] = []

        if data_points < 10:
            data_gaps.append(f"At least {MINIMUM_DATA_POINTS} days of operational data required (currently: {data_points})")

        if data_points == 0:
            data_gaps.append("No OEE data recorded for this asset")
            data_gaps.append("Ensure daily summaries are being captured")

        data_gaps.append("Consistent downtime reason logging")
        data_gaps.append("Shift target configuration for accurate variance analysis")

        output = RecommendationOutput(
            recommendations=[],
            analysis_summary=(
                f"I need more data to make specific recommendations for {subject}. "
                f"Current data coverage is insufficient for reliable pattern detection."
            ),
            patterns_detected=0,
            patterns_filtered=0,
            data_coverage=f"{time_range_days} days requested, {data_points} data points available",
            insufficient_data=True,
            data_gaps=data_gaps,
            subject=subject,
            focus_area=focus_area,
            citations=[
                RecommendationCitation(
                    source_type="daily_summaries",
                    date_range=time_range_str,
                    asset_id=None,
                    pattern_types=[],
                    display_text=f"[Source: daily_summaries - limited data for '{subject}']",
                )
            ],
            data_freshness=_utcnow().isoformat(),
        )

        return self._create_success_result(
            data=output.model_dump(),
            citations=citations,
            metadata={
                "cache_tier": "none",  # Don't cache insufficient data responses
                "insufficient_data": True,
                "data_points_available": data_points,
            },
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _format_date_range(self, start_date: date, end_date: date) -> str:
        """Format date range for display."""
        if start_date.year == end_date.year:
            if start_date.month == end_date.month:
                return f"{start_date.strftime('%b %d')} - {end_date.strftime('%d, %Y')}"
            return f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
        return f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"

    def _result_to_citation(self, result: DataResult) -> Citation:
        """Convert DataResult to Citation."""
        return self._create_citation(
            source=result.source_name,
            query=result.query or f"Query on {result.table_name}",
            table=result.table_name,
        )

    def _generate_follow_ups(
        self,
        output: RecommendationOutput,
    ) -> List[str]:
        """Generate context-aware follow-up suggestions."""
        questions: List[str] = []

        if output.recommendations:
            top_rec = output.recommendations[0]
            questions.append(
                f"Would you like more details on '{top_rec.title}'?"
            )

        if output.insufficient_data:
            questions.append(
                "What data sources are available for this asset?"
            )
        elif output.patterns_detected > 0:
            questions.append(
                "Would you like to see the trend analysis for this pattern?"
            )

        if output.focus_area:
            other_areas = ["oee", "waste", "downtime", "cost"]
            other_areas = [a for a in other_areas if a != output.focus_area]
            if other_areas:
                questions.append(
                    f"Should I also analyze {other_areas[0]} improvement opportunities?"
                )
        else:
            questions.append(
                "Would you like me to focus on a specific area (OEE, waste, downtime)?"
            )

        return questions[:3]
