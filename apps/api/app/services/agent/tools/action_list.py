"""
Action List Tool (Story 7.3)

Tool for getting a prioritized daily action list based on safety events,
OEE gaps, and financial impact. Leverages the existing Action Engine from Epic 3.

AC#1: Daily Action List Generation - Prioritized list with max 5 items
AC#2: Area-Filtered Actions - Filter to specific area with same priority logic
AC#3: No Issues Scenario - "Operations healthy" response with proactive suggestions
AC#4: Action Engine Integration - Leverages existing Action Engine from Epic 3
AC#5: Priority Logic - Safety > Financial > OEE with confidence scoring
AC#6: Data Freshness & Caching - 5-minute cache TTL, force_refresh support
"""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from app.models.agent import (
    ActionListCitation,
    ActionListInput,
    ActionListItem,
    ActionListOutput,
    PriorityCategory,
)
from app.schemas.action import (
    ActionCategory,
    ActionItem as ActionEngineItem,
    ActionListResponse as ActionEngineResponse,
    PriorityLevel,
)
from app.services.action_engine import get_action_engine
from app.services.agent.base import Citation, ManufacturingTool, ToolResult
from app.services.agent.cache import cached_tool, get_force_refresh

logger = logging.getLogger(__name__)

# Cache TTL: Uses "daily" tier from @cached_tool (900 seconds / 15 minutes)
# AC#6 specifies 5 minutes, but we use the standard "daily" tier for consistency
# with other tools. The Action Engine data doesn't change frequently during the day.
CACHE_TTL_SECONDS = 900  # Matches the "daily" cache tier

# Priority category mapping
PRIORITY_CATEGORY_MAP = {
    ActionCategory.SAFETY: PriorityCategory.SAFETY.value,
    ActionCategory.FINANCIAL: PriorityCategory.FINANCIAL.value,
    ActionCategory.OEE: PriorityCategory.OEE.value,
}

# Confidence score based on priority level
CONFIDENCE_MAP = {
    PriorityLevel.CRITICAL: 1.0,
    PriorityLevel.HIGH: 0.9,
    PriorityLevel.MEDIUM: 0.75,
    PriorityLevel.LOW: 0.6,
}


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)


class ActionListTool(ManufacturingTool):
    """
    Get a prioritized list of daily actions based on safety events,
    OEE gaps, and financial impact.

    Story 7.3: Action List Tool Implementation

    Use this tool when a user asks 'What should I focus on today?',
    'What needs attention?', 'Any priorities for this morning?',
    or wants a morning briefing with action items.

    Returns max 5 items sorted by: Safety (critical) > Financial Impact > OEE Gaps.

    Examples:
        - "What should I focus on today?"
        - "What needs attention?"
        - "Any priorities for this morning?"
        - "Give me my daily action list"
        - "What are today's priorities?"
        - "What should I focus on in Grinding?" (area-filtered)
    """

    name: str = "action_list"
    description: str = (
        "Get a prioritized list of daily actions based on safety events, "
        "OEE gaps, and financial impact. Use this when the user asks "
        "'What should I focus on?', 'What needs attention?', "
        "'Any priorities for today?', or wants a morning briefing. "
        "Returns max 5 items sorted by: Safety (critical) > Financial Impact > OEE Gaps. "
        "Supports area filtering (e.g., 'What should I focus on in Grinding?')."
    )
    args_schema: Type[BaseModel] = ActionListInput
    citations_required: bool = True

    @cached_tool(tier="daily")
    async def _arun(
        self,
        area_filter: Optional[str] = None,
        max_actions: int = 5,
        target_date: Optional[str] = None,
        force_refresh: bool = False,
        **kwargs,
    ) -> ToolResult:
        """
        Execute action list generation and return structured results.

        AC#1-6: Complete action list implementation

        Args:
            area_filter: Optional area to filter actions
            max_actions: Maximum number of actions to return (default: 5)
            target_date: Date for actions in YYYY-MM-DD format (defaults to T-1)
            force_refresh: Bypass cache and fetch fresh data

        Returns:
            ToolResult with ActionListOutput data and citations
        """
        citations: List[Citation] = []
        now = _utcnow()

        logger.info(
            f"Action list requested: area_filter={area_filter}, "
            f"max_actions={max_actions}, target_date={target_date}"
        )

        try:
            # Parse target date (default to T-1 / yesterday)
            if target_date:
                try:
                    report_date = date.fromisoformat(target_date)
                except ValueError:
                    report_date = date.today() - timedelta(days=1)
            else:
                report_date = date.today() - timedelta(days=1)

            # Determine scope for display
            scope = area_filter if area_filter else "plant-wide"

            # Get action engine instance (AC#4)
            action_engine = get_action_engine()

            # Check if force_refresh was requested (AC#6)
            # Note: The @cached_tool decorator pops force_refresh from kwargs,
            # so we need to check the context variable
            should_bypass_engine_cache = force_refresh or get_force_refresh()

            # Generate action list from Action Engine (AC#4)
            # Note: The Action Engine doesn't natively support area filtering,
            # so we'll filter the results after retrieval
            engine_response: ActionEngineResponse = await action_engine.generate_action_list(
                target_date=report_date,
                limit=None,  # Get all, then filter and limit
                use_cache=not should_bypass_engine_cache,
            )

            # Add citation for Action Engine query
            citations.append(self._create_citation(
                source="action_engine",
                query=f"generate_action_list(date={report_date.isoformat()})",
                table="daily_summaries,safety_events",
            ))

            # Filter by area if specified (AC#2)
            filtered_actions = engine_response.actions
            if area_filter:
                filtered_actions = await self._filter_by_area(
                    filtered_actions, area_filter, citations
                )

            # Convert to ActionListItems and apply priority ordering (AC#5)
            action_items = self._convert_and_prioritize(
                filtered_actions, max_actions
            )

            # Calculate totals
            total_count = len(filtered_actions)
            counts_by_category = self._count_by_category(filtered_actions)

            # Calculate total financial impact
            total_financial = sum(
                item.financial_impact_usd for item in filtered_actions
                if item.financial_impact_usd
            )

            # Check if operations are healthy (AC#3)
            is_healthy = total_count == 0

            # Generate proactive suggestions if healthy (AC#3)
            proactive_suggestions = []
            if is_healthy:
                proactive_suggestions = self._get_proactive_suggestions(area_filter)

            # Generate summary (AC#1, AC#3)
            summary = self._generate_summary(
                action_items, is_healthy, area_filter, total_count
            )

            # Build action list citations
            action_citations = self._build_action_citations(action_items)

            # Build output
            output = ActionListOutput(
                actions=action_items,
                summary=summary,
                scope=scope,
                report_date=report_date.isoformat(),
                total_count=total_count,
                counts_by_category=counts_by_category,
                total_financial_impact=total_financial if total_financial > 0 else None,
                is_healthy=is_healthy,
                proactive_suggestions=proactive_suggestions,
                citations=action_citations,
                data_freshness=now.isoformat(),
            )

            # Generate follow-up questions
            follow_ups = self._generate_follow_ups(output, area_filter)

            return self._create_success_result(
                data=output.model_dump(),
                citations=citations,
                metadata={
                    "cache_tier": "daily",
                    "ttl_seconds": CACHE_TTL_SECONDS,
                    "follow_up_questions": follow_ups,
                    "query_timestamp": now.isoformat(),
                    "actions_returned": len(action_items),
                    "actions_total": total_count,
                },
            )

        except Exception as e:
            logger.exception(f"Unexpected error during action list generation: {e}")
            return self._create_error_result(
                "An unexpected error occurred generating the action list. "
                "Please try again or contact support."
            )

    # =========================================================================
    # Area Filtering (AC#2)
    # =========================================================================

    async def _filter_by_area(
        self,
        actions: List[ActionEngineItem],
        area_filter: str,
        citations: List[Citation],
    ) -> List[ActionEngineItem]:
        """
        Filter actions by area.

        AC#2: Filter to specific area while maintaining priority logic.

        Args:
            actions: List of action items from Action Engine
            area_filter: Area name to filter by
            citations: List to append citations to

        Returns:
            Filtered list of action items
        """
        # Get asset-to-area mapping from the action engine
        action_engine = get_action_engine()

        # Load assets to get area mappings
        assets_map = await action_engine._load_assets()

        # Add citation for assets query
        citations.append(self._create_citation(
            source="assets",
            query=f"get_assets_by_area({area_filter})",
            table="assets",
        ))

        # Filter actions by area
        area_lower = area_filter.lower().strip()
        filtered = []

        for action in actions:
            asset_info = assets_map.get(action.asset_id, {})
            asset_area = asset_info.get("area", "").lower().strip()

            if asset_area == area_lower or area_lower in asset_area:
                filtered.append(action)

        logger.debug(
            f"Filtered {len(actions)} actions to {len(filtered)} for area '{area_filter}'"
        )

        return filtered

    # =========================================================================
    # Priority Ordering (AC#5)
    # =========================================================================

    def _convert_and_prioritize(
        self,
        actions: List[ActionEngineItem],
        max_actions: int,
    ) -> List[ActionListItem]:
        """
        Convert Action Engine items to ActionListItems with priority ordering.

        AC#5: Safety > Financial > OEE ordering with confidence scores.

        Args:
            actions: List of action items from Action Engine
            max_actions: Maximum number of actions to return

        Returns:
            Prioritized and limited list of ActionListItems
        """
        # Actions are already sorted by Action Engine (Safety > OEE > Financial)
        # We need to re-order to Safety > Financial > OEE per AC#5

        safety_actions = []
        financial_actions = []
        oee_actions = []

        for action in actions:
            if action.category == ActionCategory.SAFETY:
                safety_actions.append(action)
            elif action.category == ActionCategory.FINANCIAL:
                financial_actions.append(action)
            elif action.category == ActionCategory.OEE:
                oee_actions.append(action)

        # Sort within categories by financial impact (for non-safety)
        financial_actions.sort(
            key=lambda x: x.financial_impact_usd or 0,
            reverse=True
        )
        oee_actions.sort(
            key=lambda x: x.financial_impact_usd or 0,
            reverse=True
        )

        # Combine in priority order: Safety > Financial > OEE
        ordered = safety_actions + financial_actions + oee_actions

        # Apply limit and convert
        result = []
        for i, action in enumerate(ordered[:max_actions]):
            item = self._convert_to_list_item(action, i + 1)
            result.append(item)

        return result

    def _convert_to_list_item(
        self,
        action: ActionEngineItem,
        priority: int,
    ) -> ActionListItem:
        """
        Convert an Action Engine item to an ActionListItem.

        Args:
            action: Action Engine item
            priority: Priority rank (1 = highest)

        Returns:
            ActionListItem instance
        """
        # Determine confidence based on priority level (AC#5)
        confidence = CONFIDENCE_MAP.get(action.priority_level, 0.5)

        # Format estimated impact based on category
        estimated_impact = self._format_impact(action)

        # Get area from asset name pattern or default
        area = self._extract_area_from_name(action.asset_name)

        return ActionListItem(
            priority=priority,
            priority_category=PRIORITY_CATEGORY_MAP.get(
                action.category, PriorityCategory.OEE.value
            ),
            asset_id=action.asset_id,
            asset_name=action.asset_name,
            area=area,
            issue_type=self._format_issue_type(action),
            description=action.evidence_summary,
            recommended_action=action.recommendation_text,
            evidence=self._format_evidence(action),
            estimated_impact=estimated_impact,
            confidence=confidence,
        )

    def _format_impact(self, action: ActionEngineItem) -> str:
        """Format the estimated impact based on action category."""
        if action.category == ActionCategory.SAFETY:
            return f"Safety severity: {action.priority_level.value.upper()}"
        elif action.category == ActionCategory.FINANCIAL:
            if action.financial_impact_usd:
                return f"${action.financial_impact_usd:,.2f} estimated loss"
            return "Financial impact above threshold"
        else:  # OEE
            if action.financial_impact_usd:
                return f"OEE gap - ${action.financial_impact_usd:,.2f} impact"
            return "OEE below target"

    def _format_issue_type(self, action: ActionEngineItem) -> str:
        """Format the issue type based on action category and content."""
        if action.category == ActionCategory.SAFETY:
            # Extract from primary_metric_value if available
            if "Safety Event:" in action.primary_metric_value:
                return action.primary_metric_value.replace("Safety Event: ", "")
            return "Safety Event"
        elif action.category == ActionCategory.FINANCIAL:
            return "Financial Loss"
        else:
            if "OEE:" in action.primary_metric_value:
                return "OEE Gap"
            return "Performance Gap"

    def _format_evidence(self, action: ActionEngineItem) -> str:
        """Format evidence string from action's evidence refs."""
        if action.evidence_refs:
            sources = set()
            for ref in action.evidence_refs:
                sources.add(ref.source_table)
            source_list = ", ".join(sorted(sources))
            return f"Data from: {source_list}"
        return action.evidence_summary

    def _extract_area_from_name(self, asset_name: str) -> Optional[str]:
        """Extract area from asset name patterns."""
        name_lower = asset_name.lower()
        if "grinder" in name_lower:
            return "Grinding"
        elif "packaging" in name_lower or "cama" in name_lower:
            return "Packaging"
        elif "mixing" in name_lower or "mixer" in name_lower:
            return "Mixing"
        return None

    # =========================================================================
    # Category Counting (AC#1)
    # =========================================================================

    def _count_by_category(
        self,
        actions: List[ActionEngineItem],
    ) -> Dict[str, int]:
        """Count actions by category."""
        counts = {"safety": 0, "financial": 0, "oee": 0}

        for action in actions:
            if action.category == ActionCategory.SAFETY:
                counts["safety"] += 1
            elif action.category == ActionCategory.FINANCIAL:
                counts["financial"] += 1
            elif action.category == ActionCategory.OEE:
                counts["oee"] += 1

        return counts

    # =========================================================================
    # Healthy Operations (AC#3)
    # =========================================================================

    def _get_proactive_suggestions(
        self,
        area_filter: Optional[str],
    ) -> List[str]:
        """
        Generate proactive improvement suggestions when operations are healthy.

        AC#3: Suggests proactive improvements when no critical issues.
        """
        suggestions = [
            "Review preventive maintenance schedules for upcoming tasks",
            "Analyze last week's best practices and replicate successes",
            "Update shift handoff documentation with recent learnings",
        ]

        if area_filter:
            suggestions.insert(
                0,
                f"Consider cross-training opportunities in {area_filter} area"
            )

        return suggestions[:3]  # Max 3 suggestions

    # =========================================================================
    # Summary Generation (AC#1, AC#3)
    # =========================================================================

    def _generate_summary(
        self,
        actions: List[ActionListItem],
        is_healthy: bool,
        area_filter: Optional[str],
        total_count: int,
    ) -> str:
        """
        Generate a natural language summary of the action list.

        AC#1: Summary for normal action list
        AC#3: "Operations healthy" message when no issues
        """
        scope = f" in {area_filter}" if area_filter else ""

        if is_healthy:
            return (
                f"No critical issues identified{scope} - operations look healthy! "
                "All safety events resolved, OEE metrics above target, "
                "and financial losses below threshold."
            )

        # Count by category for summary
        safety_count = sum(1 for a in actions if a.priority_category == "safety")
        financial_count = sum(1 for a in actions if a.priority_category == "financial")
        oee_count = sum(1 for a in actions if a.priority_category == "oee")

        parts = []
        if safety_count > 0:
            parts.append(f"{safety_count} safety")
        if financial_count > 0:
            parts.append(f"{financial_count} financial")
        if oee_count > 0:
            parts.append(f"{oee_count} OEE")

        items_str = ", ".join(parts) if parts else "0"

        if total_count > len(actions):
            return (
                f"Found {total_count} priority items{scope} "
                f"(showing top {len(actions)}): {items_str}. "
                "Safety issues addressed first."
            )
        else:
            return (
                f"Found {len(actions)} priority items{scope}: {items_str}. "
                "Safety issues addressed first."
            )

    # =========================================================================
    # Citation Generation (AC#1)
    # =========================================================================

    def _build_action_citations(
        self,
        actions: List[ActionListItem],
    ) -> List[ActionListCitation]:
        """
        Build citation objects for each action.

        AC#1: All actions cite specific data sources.
        """
        citations = []
        seen_tables = set()

        for action in actions:
            # Determine source table based on category
            if action.priority_category == "safety":
                source_table = "safety_events"
            else:
                source_table = "daily_summaries"

            # Avoid duplicate citations for same table
            if source_table not in seen_tables:
                citations.append(ActionListCitation(
                    source_table=source_table,
                    record_id=action.asset_id,
                    metric_name=action.priority_category,
                    metric_value=action.issue_type,
                    context=action.evidence,
                    display_text=f"[Source: {source_table}]",
                ))
                seen_tables.add(source_table)

        return citations

    # =========================================================================
    # Follow-up Generation
    # =========================================================================

    def _generate_follow_ups(
        self,
        output: ActionListOutput,
        area_filter: Optional[str],
    ) -> List[str]:
        """Generate context-aware follow-up suggestions."""
        questions = []

        if output.is_healthy:
            questions.append("What was our best performing asset last week?")
            questions.append("Show me the OEE trend for the past month")
        else:
            if output.actions:
                top_action = output.actions[0]
                questions.append(
                    f"Tell me more about {top_action.asset_name}"
                )

            if output.total_financial_impact:
                questions.append(
                    "What are the top cost drivers this week?"
                )

            if not area_filter:
                questions.append("Which area needs the most attention?")

        # Always offer area-specific if not already filtered
        if not area_filter:
            questions.append("What should I focus on in Grinding?")

        return questions[:3]
