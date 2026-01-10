"""
Comparative Analysis Tool (Story 7.2)

Tool for comparing two or more assets or areas side-by-side to identify
best performers, understand differences, and support resource allocation decisions.

AC#1: Two-Asset Comparison - Side-by-side metrics, variance highlighting, recommendations
AC#2: Multi-Asset Comparison - Pattern matching (e.g., "all grinders"), ranking by performance
AC#3: Area-Level Comparison - Aggregated metrics, top/bottom performers per area
AC#4: Incompatible Metrics Handling - Normalization, comparability notes
AC#5: Default Time Range - 7 days default, custom ranges supported
AC#6: Citation & Data Freshness - All metrics include citations, 15-min cache TTL
"""

import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Type

from pydantic import BaseModel

from app.models.agent import (
    AreaPerformerSummary,
    ComparativeAnalysisCitation,
    ComparativeAnalysisInput,
    ComparativeAnalysisOutput,
    ComparisonMetric,
    SubjectSummary,
)
from app.services.agent.base import Citation, ManufacturingTool, ToolResult
from app.services.agent.cache import cached_tool
from app.services.agent.data_source import (
    Asset,
    DataResult,
    DataSourceError,
    OEEMetrics,
    get_data_source,
)

logger = logging.getLogger(__name__)

# Cache TTL: 15 minutes (daily tier)
CACHE_TTL_DAILY = 900

# Default metrics to compare
DEFAULT_METRICS = ["oee", "output", "downtime_hours", "waste_pct"]

# Metric configuration: display name, unit, whether higher is better
METRIC_CONFIG = {
    "oee": {"display_name": "OEE", "unit": "%", "higher_is_better": True},
    "output": {"display_name": "Output", "unit": "units", "higher_is_better": True},
    "downtime_hours": {"display_name": "Downtime", "unit": "hours", "higher_is_better": False},
    "downtime_minutes": {"display_name": "Downtime", "unit": "min", "higher_is_better": False},
    "waste_pct": {"display_name": "Waste", "unit": "%", "higher_is_better": False},
    "availability": {"display_name": "Availability", "unit": "%", "higher_is_better": True},
    "performance": {"display_name": "Performance", "unit": "%", "higher_is_better": True},
    "quality": {"display_name": "Quality", "unit": "%", "higher_is_better": True},
}

# Score gap threshold for declaring a clear winner
WINNER_SCORE_GAP = 5.0

# Score weights for composite ranking
SCORE_WEIGHTS = {
    "oee": 0.40,
    "output_pct_target": 0.25,
    "downtime_score": 0.20,
    "waste_score": 0.15,
}


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)


class ComparativeAnalysisTool(ManufacturingTool):
    """
    Compare two or more assets or areas side-by-side on key metrics.

    Story 7.2: Comparative Analysis Tool Implementation

    Use this tool when a user wants to compare performance between assets,
    find the best performer, or understand differences between assets/areas.
    Supports comparing 2-10 assets or areas with variance highlighting.

    Examples:
        - "Compare Grinder 5 vs Grinder 3"
        - "Compare all grinders this week"
        - "Compare Grinding vs Packaging areas"
        - "Which asset is performing better?"
        - "Show me a side-by-side of Grinder 5 and CAMA 800-1"
    """

    name: str = "comparative_analysis"
    description: str = (
        "Compare two or more assets or areas side-by-side on key metrics "
        "(OEE, output, downtime, waste). Use this when user wants to compare "
        "performance, find best performer, or understand differences between "
        "assets or areas. Supports 2-10 subjects with variance highlighting. "
        "Examples: 'Compare Grinder 5 vs Grinder 3', 'Compare all grinders', "
        "'Compare Grinding vs Packaging areas', 'Which asset performs better?'"
    )
    args_schema: Type[BaseModel] = ComparativeAnalysisInput
    citations_required: bool = True

    @cached_tool(tier="daily")
    async def _arun(
        self,
        subjects: List[str],
        comparison_type: str = "asset",
        metrics: Optional[List[str]] = None,
        time_range_days: int = 7,
        **kwargs,
    ) -> ToolResult:
        """
        Execute comparative analysis and return structured results.

        AC#1-6: Complete comparative analysis implementation

        Args:
            subjects: List of asset names, area names, or patterns to compare
            comparison_type: Type of comparison ('asset' or 'area')
            metrics: Specific metrics to compare (default: all)
            time_range_days: Number of days for comparison period (default: 7)

        Returns:
            ToolResult with ComparativeAnalysisOutput data and citations
        """
        data_source = get_data_source()
        citations: List[Citation] = []

        logger.info(
            f"Comparative analysis requested: subjects={subjects}, "
            f"type={comparison_type}, time_range_days={time_range_days}"
        )

        try:
            # Calculate date range (AC#5)
            now = _utcnow()
            end_date = now.date()
            start_date = end_date - timedelta(days=time_range_days)
            time_range_str = self._format_date_range(start_date, end_date)

            # Resolve subjects to actual assets/areas (AC#2)
            resolved_subjects = await self._resolve_subjects(
                subjects, comparison_type, data_source, citations
            )

            # Handle insufficient subjects
            if len(resolved_subjects) < 2:
                return self._insufficient_subjects_response(
                    subjects, resolved_subjects, time_range_str, citations
                )

            # Limit to 10 subjects
            if len(resolved_subjects) > 10:
                resolved_subjects = resolved_subjects[:10]
                logger.info(f"Limited subjects to first 10")

            # Determine metrics to compare
            metric_names = metrics or DEFAULT_METRICS.copy()

            # Fetch metrics for each subject
            subject_data_list = []
            for subject_info in resolved_subjects:
                if comparison_type == "area":
                    data = await self._fetch_area_metrics(
                        subject_info, start_date, end_date, metric_names,
                        data_source, citations
                    )
                else:
                    data = await self._fetch_asset_metrics(
                        subject_info, start_date, end_date, metric_names,
                        data_source, citations
                    )
                subject_data_list.append(data)

            # Build metric comparisons (AC#1, AC#4)
            comparison_metrics, comparability_notes = self._build_metric_comparisons(
                subject_data_list, metric_names
            )

            # Rank subjects by composite score (AC#2)
            ranked_subjects = self._rank_subjects(
                subject_data_list, comparison_metrics
            )

            # Determine winner if clear (AC#1)
            winner = self._determine_winner(ranked_subjects)

            # Generate summary and recommendations (AC#1)
            summary = self._generate_summary(ranked_subjects, comparison_metrics)
            recommendations = self._generate_recommendations(
                comparison_metrics, ranked_subjects
            )

            # Get area performers for area comparisons (AC#3)
            area_performers = None
            if comparison_type == "area":
                area_performers = await self._get_area_performers(
                    subject_data_list, data_source, start_date, end_date, citations
                )

            # Build analysis citations (AC#6)
            analysis_citations = self._build_analysis_citations(
                ranked_subjects, time_range_str
            )

            # Build output
            output = ComparativeAnalysisOutput(
                subjects=ranked_subjects,
                metrics=comparison_metrics,
                comparison_type=comparison_type,
                time_range=time_range_str,
                summary=summary,
                winner=winner,
                recommendations=recommendations,
                comparability_notes=comparability_notes,
                area_performers=area_performers,
                citations=analysis_citations,
                data_as_of=now.isoformat(),
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
                    "subjects_compared": len(ranked_subjects),
                },
            )

        except DataSourceError as e:
            logger.error(f"Data source error during comparative analysis: {e}")
            return self._create_error_result(
                "Unable to retrieve comparison data. Please try again later."
            )
        except Exception as e:
            logger.exception(f"Unexpected error during comparative analysis: {e}")
            return self._create_error_result(
                "An unexpected error occurred during comparison. "
                "Please try again or contact support."
            )

    # =========================================================================
    # Subject Resolution (AC#2)
    # =========================================================================

    async def _resolve_subjects(
        self,
        subjects: List[str],
        comparison_type: str,
        data_source,
        citations: List[Citation],
    ) -> List[Dict[str, Any]]:
        """
        Resolve subject names to actual assets or areas.

        AC#2: Handles "all grinders" pattern expansion.

        Args:
            subjects: Raw subject names from user
            comparison_type: 'asset' or 'area'
            data_source: Data source instance
            citations: List to append citations to

        Returns:
            List of resolved subject info dicts
        """
        resolved = []

        for subject in subjects:
            subject_lower = subject.lower().strip()

            if comparison_type == "area":
                # Resolve area by name
                assets_result = await data_source.get_assets_by_area(subject)
                citations.append(self._result_to_citation(assets_result))

                if assets_result.has_data and len(assets_result.data) > 0:
                    resolved.append({
                        "name": subject,
                        "type": "area",
                        "assets": assets_result.data,
                    })
            else:
                # Check for pattern match (e.g., "all grinders")
                if subject_lower.startswith("all "):
                    pattern = subject_lower[4:].strip()  # Remove "all "
                    await self._expand_pattern(
                        pattern, data_source, citations, resolved
                    )
                else:
                    # Single asset lookup with fuzzy matching
                    asset_result = await data_source.get_asset_by_name(subject)
                    citations.append(self._result_to_citation(asset_result))

                    if asset_result.has_data:
                        resolved.append({
                            "name": asset_result.data.name,
                            "type": "asset",
                            "asset": asset_result.data,
                        })

        return resolved

    async def _expand_pattern(
        self,
        pattern: str,
        data_source,
        citations: List[Citation],
        resolved: List[Dict[str, Any]],
    ) -> None:
        """
        Expand pattern like "grinders" to all matching assets.

        AC#2: Multi-asset pattern matching.
        """
        all_assets_result = await data_source.get_all_assets()
        citations.append(self._result_to_citation(all_assets_result))

        if not all_assets_result.has_data:
            return

        # Filter assets by pattern (fuzzy match on name)
        pattern_lower = pattern.lower().rstrip("s")  # Remove trailing 's' for plurals
        matching_assets = []

        for asset in all_assets_result.data:
            asset_name_lower = asset.name.lower()
            # Match if pattern is in asset name
            if pattern_lower in asset_name_lower:
                matching_assets.append(asset)

        # Add matching assets (limit to 10)
        for asset in matching_assets[:10]:
            resolved.append({
                "name": asset.name,
                "type": "asset",
                "asset": asset,
            })

    # =========================================================================
    # Metrics Fetching (AC#1, AC#3)
    # =========================================================================

    async def _fetch_asset_metrics(
        self,
        subject_info: Dict[str, Any],
        start_date: date,
        end_date: date,
        metric_names: List[str],
        data_source,
        citations: List[Citation],
    ) -> Dict[str, Any]:
        """
        Fetch metrics for a single asset.

        AC#1: Query daily_summaries for OEE, output, downtime, waste.
        """
        asset: Asset = subject_info["asset"]
        asset_id = asset.id

        # Get OEE data
        oee_result = await data_source.get_oee(asset_id, start_date, end_date)
        citations.append(self._result_to_citation(oee_result))

        # Get target for normalization
        target_result = await data_source.get_shift_target(asset_id)
        citations.append(self._result_to_citation(target_result))

        # Calculate averages from OEE data
        metrics = {}
        target_output = None

        if oee_result.has_data:
            oee_data = oee_result.data
            metrics["oee"] = self._calculate_average(oee_data, "oee_percentage")
            metrics["availability"] = self._calculate_average(oee_data, "availability")
            metrics["performance"] = self._calculate_average(oee_data, "performance")
            metrics["quality"] = self._calculate_average(oee_data, "quality")

            # Sum totals
            total_output = sum(
                getattr(d, "actual_output", 0) or 0 for d in oee_data
            )
            total_downtime = sum(
                getattr(d, "downtime_minutes", 0) or 0 for d in oee_data
            )
            total_waste = sum(
                getattr(d, "waste_count", 0) or 0 for d in oee_data
            )

            metrics["output"] = total_output
            metrics["downtime_hours"] = round(total_downtime / 60, 1)
            metrics["downtime_minutes"] = total_downtime

            # Calculate waste percentage
            if total_output > 0:
                metrics["waste_pct"] = round((total_waste / total_output) * 100, 2)
            else:
                metrics["waste_pct"] = 0.0

            # Get target for output % calculation
            if target_result.has_data:
                target_output = target_result.data.target_output

        return {
            "name": asset.name,
            "type": "asset",
            "id": asset.id,
            "area": asset.area,
            "metrics": metrics,
            "target_output": target_output,
            "data_days": len(oee_result.data) if oee_result.has_data else 0,
        }

    async def _fetch_area_metrics(
        self,
        subject_info: Dict[str, Any],
        start_date: date,
        end_date: date,
        metric_names: List[str],
        data_source,
        citations: List[Citation],
    ) -> Dict[str, Any]:
        """
        Fetch aggregated metrics for an area.

        AC#3: Area-level totals and averages.
        """
        area_name = subject_info["name"]
        assets = subject_info.get("assets", [])

        if not assets:
            return {
                "name": area_name,
                "type": "area",
                "id": None,
                "area": area_name,
                "metrics": {},
                "asset_count": 0,
                "data_days": 0,
            }

        # Get OEE data for all assets in area
        oee_result = await data_source.get_oee_by_area(area_name, start_date, end_date)
        citations.append(self._result_to_citation(oee_result))

        # Aggregate metrics
        metrics = {}
        if oee_result.has_data:
            oee_data = oee_result.data

            # Weighted average OEE (weighted by output)
            total_output = sum(
                getattr(d, "actual_output", 0) or 0 for d in oee_data
            )
            if total_output > 0:
                weighted_oee = sum(
                    (getattr(d, "oee_percentage", 0) or 0) * (getattr(d, "actual_output", 0) or 0)
                    for d in oee_data
                ) / total_output
                metrics["oee"] = round(float(weighted_oee), 1)
            else:
                metrics["oee"] = self._calculate_average(oee_data, "oee_percentage")

            metrics["availability"] = self._calculate_average(oee_data, "availability")
            metrics["performance"] = self._calculate_average(oee_data, "performance")
            metrics["quality"] = self._calculate_average(oee_data, "quality")

            # Sum totals
            total_downtime = sum(
                getattr(d, "downtime_minutes", 0) or 0 for d in oee_data
            )
            total_waste = sum(
                getattr(d, "waste_count", 0) or 0 for d in oee_data
            )

            metrics["output"] = total_output
            metrics["downtime_hours"] = round(total_downtime / 60, 1)
            metrics["downtime_minutes"] = total_downtime

            if total_output > 0:
                metrics["waste_pct"] = round((total_waste / total_output) * 100, 2)
            else:
                metrics["waste_pct"] = 0.0

        return {
            "name": area_name,
            "type": "area",
            "id": None,
            "area": area_name,
            "metrics": metrics,
            "asset_count": len(assets),
            "data_days": len(oee_result.data) if oee_result.has_data else 0,
        }

    # =========================================================================
    # Metric Comparison (AC#1, AC#4)
    # =========================================================================

    def _build_metric_comparisons(
        self,
        subject_data_list: List[Dict[str, Any]],
        metric_names: List[str],
    ) -> Tuple[List[ComparisonMetric], List[str]]:
        """
        Build comparison objects for each metric.

        AC#1: Side-by-side metrics with variance indicators.
        AC#4: Detect incompatible metrics and normalize.
        """
        comparisons = []
        comparability_notes = []

        for metric_name in metric_names:
            config = METRIC_CONFIG.get(
                metric_name,
                {"display_name": metric_name.title(), "unit": "", "higher_is_better": True}
            )

            # Extract values for each subject
            values = {}
            for subject in subject_data_list:
                value = subject.get("metrics", {}).get(metric_name, 0)
                if isinstance(value, Decimal):
                    value = float(value)
                values[subject["name"]] = value or 0

            # Check for all-zero values
            non_zero_values = [v for v in values.values() if v != 0]
            if not non_zero_values:
                comparability_note = f"No data available for {config['display_name']}"
                comparability_notes.append(comparability_note)
                # Still create the comparison with zero values
                best = worst = list(values.keys())[0] if values else ""
                variance = 0.0
            else:
                # Determine best/worst based on metric type
                if config["higher_is_better"]:
                    best = max(values, key=lambda k: values[k])
                    worst = min(values, key=lambda k: values[k])
                else:
                    best = min(values, key=lambda k: values[k])
                    worst = max(values, key=lambda k: values[k])

                # Calculate variance
                max_val = max(values.values())
                min_val = min(values.values())
                if max_val > 0:
                    variance = ((max_val - min_val) / max_val) * 100
                else:
                    variance = 0.0

                comparability_note = None

            # Check if normalization was applied (for output with different targets)
            normalized = False
            if metric_name == "output":
                # Check if subjects have different targets
                targets = set(
                    s.get("target_output") for s in subject_data_list
                    if s.get("target_output") is not None
                )
                if len(targets) > 1:
                    normalized = True
                    comparability_notes.append(
                        "Output targets differ between assets - consider comparing % of target"
                    )

            comparisons.append(ComparisonMetric(
                metric_name=metric_name,
                display_name=config["display_name"],
                unit=config["unit"],
                values=values,
                best_performer=best,
                worst_performer=worst,
                variance_pct=round(variance, 1),
                higher_is_better=config["higher_is_better"],
                normalized=normalized,
                comparability_note=comparability_note,
            ))

        return comparisons, comparability_notes

    # =========================================================================
    # Subject Ranking (AC#2)
    # =========================================================================

    def _rank_subjects(
        self,
        subject_data_list: List[Dict[str, Any]],
        comparison_metrics: List[ComparisonMetric],
    ) -> List[SubjectSummary]:
        """
        Rank subjects by composite performance score.

        AC#2: Ranks by overall performance.
        """
        ranked_data = []

        for subject in subject_data_list:
            metrics = subject.get("metrics", {})

            # Calculate composite score
            # Weight: OEE 40%, Output attainment 25%, Downtime (inverse) 20%, Waste (inverse) 15%
            score = 0.0

            # OEE component (0-100 scale)
            oee = metrics.get("oee", 0)
            score += float(oee) * SCORE_WEIGHTS.get("oee", 0.4)

            # Output vs target (normalize to 0-100)
            target_output = subject.get("target_output")
            actual_output = metrics.get("output", 0)
            if target_output and target_output > 0:
                output_pct = min((actual_output / target_output) * 100, 100)
            else:
                # If no target, use 75 as baseline
                output_pct = 75.0
            score += output_pct * SCORE_WEIGHTS.get("output_pct_target", 0.25)

            # Downtime (inverse, normalized to 0-100)
            # Assume max 168 hours (1 week) of possible downtime
            downtime_hours = metrics.get("downtime_hours", 0)
            max_downtime = 168  # Hours in a week
            downtime_score = max(0, 100 - (downtime_hours / max_downtime * 100))
            score += downtime_score * SCORE_WEIGHTS.get("downtime_score", 0.2)

            # Waste (inverse, normalized)
            waste_pct = metrics.get("waste_pct", 0)
            waste_score = max(0, 100 - waste_pct)
            score += waste_score * SCORE_WEIGHTS.get("waste_score", 0.15)

            # Count wins and losses from comparison metrics
            wins = 0
            losses = 0
            for m in comparison_metrics:
                if m.best_performer == subject["name"]:
                    wins += 1
                if m.worst_performer == subject["name"]:
                    losses += 1

            ranked_data.append({
                **subject,
                "score": round(min(score, 100), 1),
                "wins": wins,
                "losses": losses,
            })

        # Sort by score descending
        ranked_data.sort(key=lambda x: x["score"], reverse=True)

        # Build SubjectSummary objects with rank
        return [
            SubjectSummary(
                name=s["name"],
                subject_type=s["type"],
                subject_id=s.get("id"),
                area=s.get("area"),
                metrics=s.get("metrics", {}),
                rank=i + 1,
                score=s["score"],
                wins=s["wins"],
                losses=s["losses"],
            )
            for i, s in enumerate(ranked_data)
        ]

    def _determine_winner(
        self,
        ranked_subjects: List[SubjectSummary],
    ) -> Optional[str]:
        """
        Determine if there's a clear winner.

        AC#1: Winner/recommendation if one is clearly better.
        """
        if len(ranked_subjects) < 2:
            return None

        score_gap = ranked_subjects[0].score - ranked_subjects[1].score
        if score_gap >= WINNER_SCORE_GAP:
            return ranked_subjects[0].name

        return None

    # =========================================================================
    # Area Performers (AC#3)
    # =========================================================================

    async def _get_area_performers(
        self,
        subject_data_list: List[Dict[str, Any]],
        data_source,
        start_date: date,
        end_date: date,
        citations: List[Citation],
    ) -> List[AreaPerformerSummary]:
        """
        Get best/worst performers within each area.

        AC#3: Identifies top/bottom performers within each area.
        """
        area_performers = []

        for subject in subject_data_list:
            if subject["type"] != "area":
                continue

            area_name = subject["name"]

            # Get all assets in this area
            assets_result = await data_source.get_assets_by_area(area_name)
            if not assets_result.has_data:
                continue

            assets = assets_result.data
            if len(assets) < 1:
                continue

            # Get OEE for each asset
            asset_oee_list = []
            for asset in assets:
                oee_result = await data_source.get_oee(asset.id, start_date, end_date)
                if oee_result.has_data:
                    avg_oee = self._calculate_average(oee_result.data, "oee_percentage")
                    asset_oee_list.append({
                        "name": asset.name,
                        "oee": avg_oee,
                    })

            if len(asset_oee_list) < 1:
                continue

            # Find best and worst
            asset_oee_list.sort(key=lambda x: x["oee"], reverse=True)
            best = asset_oee_list[0]
            worst = asset_oee_list[-1]

            area_performers.append(AreaPerformerSummary(
                area=area_name,
                best_performer=best["name"],
                best_oee=round(best["oee"], 1),
                worst_performer=worst["name"],
                worst_oee=round(worst["oee"], 1),
                asset_count=len(assets),
            ))

        return area_performers if area_performers else None

    # =========================================================================
    # Summary & Recommendations (AC#1)
    # =========================================================================

    def _generate_summary(
        self,
        ranked_subjects: List[SubjectSummary],
        comparison_metrics: List[ComparisonMetric],
    ) -> str:
        """
        Generate natural language summary of comparison.

        AC#1: Summary of key differences.
        """
        if not ranked_subjects:
            return "Unable to compare - no valid subjects found."

        lines = []

        # Overall ranking statement
        if len(ranked_subjects) == 2:
            first = ranked_subjects[0]
            second = ranked_subjects[1]
            if first.score > second.score:
                lines.append(
                    f"**{first.name}** outperforms **{second.name}** overall "
                    f"(score: {first.score} vs {second.score})."
                )
            else:
                lines.append(
                    f"**{first.name}** and **{second.name}** are closely matched "
                    f"(scores: {first.score} vs {second.score})."
                )
        else:
            top3 = [s.name for s in ranked_subjects[:3]]
            lines.append(f"**Top performers:** {', '.join(top3)}")

        # Largest variance
        if comparison_metrics:
            largest_gap = max(comparison_metrics, key=lambda m: m.variance_pct)
            if largest_gap.variance_pct > 10:
                lines.append(
                    f"Largest difference in **{largest_gap.display_name}**: "
                    f"{largest_gap.variance_pct:.0f}% gap between {largest_gap.best_performer} "
                    f"and {largest_gap.worst_performer}."
                )

        return " ".join(lines)

    def _generate_recommendations(
        self,
        comparison_metrics: List[ComparisonMetric],
        ranked_subjects: List[SubjectSummary],
    ) -> List[str]:
        """
        Generate actionable recommendations.

        AC#1: Winner/recommendation based on analysis.
        """
        recommendations = []

        # Find significant gaps
        for m in comparison_metrics:
            if m.variance_pct > 20 and m.worst_performer:
                if m.higher_is_better:
                    recommendations.append(
                        f"Investigate why {m.worst_performer}'s {m.display_name} "
                        f"is {m.variance_pct:.0f}% behind {m.best_performer}."
                    )
                else:
                    recommendations.append(
                        f"Address {m.worst_performer}'s high {m.display_name} - "
                        f"{m.variance_pct:.0f}% higher than {m.best_performer}."
                    )

        # Add recommendation for bottom performer
        if len(ranked_subjects) > 2:
            worst = ranked_subjects[-1]
            if worst.losses > 0:
                recommendations.append(
                    f"Focus improvement efforts on {worst.name} "
                    f"(ranked last, {worst.losses} metric{'s' if worst.losses > 1 else ''} behind)."
                )

        # Add recommendation to apply best practices
        if len(ranked_subjects) >= 2:
            best = ranked_subjects[0]
            if best.wins >= 2:
                recommendations.append(
                    f"Apply {best.name}'s best practices to other assets."
                )

        return recommendations[:3]  # Max 3 recommendations

    # =========================================================================
    # Citation Generation (AC#6)
    # =========================================================================

    def _build_analysis_citations(
        self,
        ranked_subjects: List[SubjectSummary],
        time_range: str,
    ) -> List[ComparativeAnalysisCitation]:
        """
        Build citation objects for the analysis.

        AC#6: All comparison metrics include source citations.
        """
        subject_names = [s.name for s in ranked_subjects]

        return [
            ComparativeAnalysisCitation(
                source_type="daily_summaries",
                date_range=time_range,
                subjects_queried=subject_names,
                display_text=f"[Source: daily_summaries {time_range}]",
            )
        ]

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

    def _calculate_average(
        self,
        data_list: List[Any],
        field_name: str,
    ) -> float:
        """Calculate average of a field from a list of objects."""
        values = []
        for item in data_list:
            value = getattr(item, field_name, None)
            if value is not None:
                if isinstance(value, Decimal):
                    value = float(value)
                values.append(value)

        if not values:
            return 0.0
        return round(sum(values) / len(values), 1)

    def _result_to_citation(self, result: DataResult) -> Citation:
        """Convert DataResult to Citation."""
        return self._create_citation(
            source=result.source_name,
            query=result.query or f"Query on {result.table_name}",
            table=result.table_name,
        )

    def _insufficient_subjects_response(
        self,
        requested: List[str],
        resolved: List[Dict[str, Any]],
        time_range: str,
        citations: List[Citation],
    ) -> ToolResult:
        """
        Generate response when insufficient subjects are found.
        """
        resolved_names = [s["name"] for s in resolved]

        if len(resolved) == 0:
            message = (
                f"Unable to find any of the requested subjects: {', '.join(requested)}. "
                "Please check the asset or area names and try again."
            )
        else:
            message = (
                f"Only found {len(resolved)} subject(s): {', '.join(resolved_names)}. "
                "Comparison requires at least 2 subjects. Please provide additional "
                "asset or area names to compare."
            )

        output = ComparativeAnalysisOutput(
            subjects=[],
            metrics=[],
            comparison_type="asset",
            time_range=time_range,
            summary=message,
            winner=None,
            recommendations=[],
            comparability_notes=[],
            area_performers=None,
            citations=[],
            data_as_of=_utcnow().isoformat(),
        )

        return self._create_success_result(
            data=output.model_dump(),
            citations=citations,
            metadata={
                "cache_tier": "none",  # Don't cache error responses
                "subjects_found": len(resolved),
                "subjects_requested": len(requested),
            },
        )

    def _generate_follow_ups(
        self,
        output: ComparativeAnalysisOutput,
    ) -> List[str]:
        """Generate context-aware follow-up suggestions."""
        questions = []

        if output.winner:
            questions.append(
                f"What makes {output.winner} the best performer?"
            )

        if len(output.subjects) >= 2:
            worst = output.subjects[-1].name
            questions.append(
                f"What's causing {worst}'s lower performance?"
            )

        if output.metrics:
            # Find metric with highest variance
            max_var_metric = max(output.metrics, key=lambda m: m.variance_pct)
            if max_var_metric.variance_pct > 15:
                questions.append(
                    f"Why is there a {max_var_metric.variance_pct:.0f}% gap in "
                    f"{max_var_metric.display_name}?"
                )

        # Default
        if len(questions) < 2:
            questions.append(
                "Would you like to see the trend over a longer period?"
            )

        return questions[:3]
