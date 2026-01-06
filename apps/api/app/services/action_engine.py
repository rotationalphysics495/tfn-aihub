"""
Action Engine Service

Core prioritization engine for generating the Daily Action List.
Implements FR3 (Action Engine) from PRD - prioritizes issues by
Safety > OEE Gap > Financial Loss.

Story: 3.1 - Action Engine Logic
AC: #1 - Action Engine Service Exists
AC: #2 - Safety Priority Filter (Tier 1)
AC: #3 - OEE Below Target Filter (Tier 2)
AC: #4 - Financial Loss Above Threshold Filter (Tier 3)
AC: #5 - Combined Sorting Logic
AC: #9 - Integration with Daily Pipeline
AC: #10 - Empty State Handling
"""

import logging
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from supabase import create_client, Client

from app.core.config import get_settings
from app.schemas.action import (
    ActionCategory,
    ActionEngineConfig,
    ActionItem,
    ActionListResponse,
    EvidenceRef,
    PriorityLevel,
)

logger = logging.getLogger(__name__)


class ActionEngineError(Exception):
    """Base exception for Action Engine errors."""
    pass


class ActionEngine:
    """
    Action Engine for prioritizing operational issues.

    Processes daily_summaries, safety_events, and cost_centers data
    to generate a prioritized action list.

    Priority tiers (absolute ordering):
    1. Safety events (always first, all marked critical)
    2. OEE below target (sorted by gap magnitude)
    3. Financial loss above threshold (sorted by loss amount)

    Within each tier, items are sorted by their respective severity/impact.
    Assets appearing in multiple categories are deduplicated, keeping
    the highest priority category with evidence refs from other categories.
    """

    def __init__(
        self,
        supabase_client: Optional[Client] = None,
        config: Optional[ActionEngineConfig] = None,
    ):
        """
        Initialize the Action Engine.

        Args:
            supabase_client: Optional Supabase client (created if not provided)
            config: Optional configuration overrides
        """
        self._client = supabase_client
        self._config = config
        self._assets_cache: Dict[str, dict] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_seconds: int = 300  # 5 minute cache

        # Action list cache for day-long consistency (AC #9)
        self._action_list_cache: Dict[str, ActionListResponse] = {}

    def _get_client(self) -> Client:
        """Get or create Supabase client."""
        if self._client is None:
            settings = get_settings()
            if not settings.supabase_url or not settings.supabase_key:
                raise ActionEngineError("Supabase not configured")
            self._client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
        return self._client

    def _get_config(self) -> ActionEngineConfig:
        """Get configuration with defaults from settings."""
        if self._config is not None:
            return self._config

        settings = get_settings()
        return ActionEngineConfig(
            target_oee_percentage=settings.target_oee_percentage,
            financial_loss_threshold=settings.financial_loss_threshold,
            oee_high_gap_threshold=settings.oee_high_gap_threshold,
            oee_medium_gap_threshold=settings.oee_medium_gap_threshold,
            financial_high_threshold=settings.financial_high_threshold,
            financial_medium_threshold=settings.financial_medium_threshold,
        )

    def _is_cache_valid(self) -> bool:
        """Check if the assets cache is still valid."""
        if self._cache_timestamp is None:
            return False
        elapsed = (datetime.utcnow() - self._cache_timestamp).total_seconds()
        return elapsed < self._cache_ttl_seconds

    async def _load_assets(self, force: bool = False) -> Dict[str, dict]:
        """
        Load asset information from Supabase with caching.

        Returns:
            Dictionary mapping asset_id to asset info
        """
        if not force and self._is_cache_valid() and self._assets_cache:
            return self._assets_cache

        try:
            client = self._get_client()
            response = client.table("assets").select(
                "id, name, source_id, area, cost_center_id"
            ).execute()

            self._assets_cache = {}
            for asset in response.data or []:
                asset_id = asset.get("id")
                if asset_id:
                    self._assets_cache[asset_id] = {
                        "name": asset.get("name", "Unknown"),
                        "source_id": asset.get("source_id"),
                        "area": asset.get("area"),
                        "cost_center_id": asset.get("cost_center_id"),
                    }

            self._cache_timestamp = datetime.utcnow()
            logger.debug(f"Loaded {len(self._assets_cache)} assets for Action Engine")
            return self._assets_cache

        except Exception as e:
            logger.error(f"Failed to load assets: {e}")
            return {}

    def _generate_action_id(self, category: ActionCategory, asset_id: str) -> str:
        """Generate a unique action item ID."""
        return f"action-{category.value}-{uuid.uuid4().hex[:12]}"

    def _get_safety_priority(self, severity: str) -> int:
        """Get sort priority for safety severity (lower = higher priority)."""
        severity_order = {
            "critical": 1,
            "high": 2,
            "medium": 3,
            "low": 4,
        }
        return severity_order.get(severity.lower(), 5)

    async def _get_safety_actions(
        self,
        target_date: date,
        assets_map: Dict[str, dict]
    ) -> List[ActionItem]:
        """
        Get action items for unresolved safety events (Tier 1).

        AC #2: Safety events are always placed at TOP, marked critical.

        Args:
            target_date: The report date to query
            assets_map: Asset ID to info mapping

        Returns:
            List of ActionItems for safety events, sorted by severity
        """
        try:
            client = self._get_client()

            # Query unresolved safety events for the target date
            # is_resolved = FALSE means event needs attention
            query = client.table("safety_events").select("*")
            query = query.eq("is_resolved", False)

            # Filter by date - events from target_date onwards
            start_of_day = datetime.combine(target_date, datetime.min.time())
            query = query.gte("event_timestamp", start_of_day.isoformat())

            response = query.execute()
            records = response.data or []

            if not records:
                logger.debug(f"No unresolved safety events for {target_date}")
                return []

            actions = []
            for record in records:
                asset_id = record.get("asset_id")
                asset_info = assets_map.get(asset_id, {"name": "Unknown"})

                severity = record.get("severity", "critical").lower()
                reason_code = record.get("reason_code", "Safety Issue")
                description = record.get("description", "")
                event_timestamp = record.get("event_timestamp", "")

                # Build evidence reference
                evidence_ref = EvidenceRef(
                    source_table="safety_events",
                    record_id=str(record.get("id", "")),
                    metric_name="severity",
                    metric_value=severity,
                    context=description or f"Safety event: {reason_code}",
                )

                # Format timestamp for display
                try:
                    ts = datetime.fromisoformat(event_timestamp.replace("Z", "+00:00"))
                    time_str = ts.strftime("%H:%M")
                except (ValueError, AttributeError):
                    time_str = ""

                action = ActionItem(
                    id=self._generate_action_id(ActionCategory.SAFETY, asset_id),
                    asset_id=str(asset_id),
                    asset_name=asset_info.get("name", "Unknown"),
                    priority_level=PriorityLevel.CRITICAL,  # AC #2: Safety always critical
                    category=ActionCategory.SAFETY,
                    primary_metric_value=f"Safety Event: {reason_code}",
                    recommendation_text=f"Investigate {reason_code.lower()} on {asset_info.get('name', 'Unknown')}",
                    evidence_summary=f"Unresolved safety event{' at ' + time_str if time_str else ''}",
                    evidence_refs=[evidence_ref],
                    created_at=datetime.utcnow(),
                )
                actions.append((action, self._get_safety_priority(severity), event_timestamp))

            # Sort by severity (critical first), then by timestamp (newest first within same severity)
            # x[1] = severity priority (lower = higher priority), x[2] = ISO timestamp string
            # Reverse timestamp to get newest first (higher timestamp = later = first)
            actions.sort(key=lambda x: (x[1], x[2] if x[2] else ""), reverse=False)
            # Stable sort: first by severity (ascending), then within same severity by timestamp (descending)
            from itertools import groupby
            sorted_actions = []
            for severity, group in groupby(sorted(actions, key=lambda x: x[1]), key=lambda x: x[1]):
                group_list = list(group)
                # Sort by timestamp descending (newest first) within each severity group
                group_list.sort(key=lambda x: x[2] if x[2] else "", reverse=True)
                sorted_actions.extend(group_list)
            actions = sorted_actions

            result = [a[0] for a in actions]
            logger.info(f"Found {len(result)} safety action items for {target_date}")
            return result

        except Exception as e:
            logger.error(f"Failed to get safety actions: {e}")
            return []

    async def _get_oee_actions(
        self,
        target_date: date,
        assets_map: Dict[str, dict],
        config: Optional[ActionEngineConfig] = None,
    ) -> List[ActionItem]:
        """
        Get action items for assets with OEE below target (Tier 2).

        AC #3: Assets with OEE below target are included, sorted by gap magnitude.

        Args:
            target_date: The report date to query
            assets_map: Asset ID to info mapping
            config: Optional config to use (defaults to instance config)

        Returns:
            List of ActionItems for OEE gaps, sorted by gap (worst first)
        """
        try:
            client = self._get_client()
            config = config if config is not None else self._get_config()
            target_oee = config.target_oee_percentage

            # Query daily_summaries for the target date with OEE below target
            query = client.table("daily_summaries").select(
                "id, asset_id, report_date, oee_percentage, actual_output, target_output"
            )
            query = query.eq("report_date", target_date.isoformat())
            query = query.lt("oee_percentage", target_oee)

            response = query.execute()
            records = response.data or []

            if not records:
                logger.debug(f"No OEE below target for {target_date}")
                return []

            actions = []
            for record in records:
                asset_id = record.get("asset_id")
                asset_info = assets_map.get(asset_id, {"name": "Unknown"})

                oee_pct = record.get("oee_percentage", 0) or 0
                gap = target_oee - oee_pct
                actual_output = record.get("actual_output", 0)
                target_output = record.get("target_output", 0)

                # Determine priority based on gap severity (AC #3)
                if gap >= config.oee_high_gap_threshold:
                    priority = PriorityLevel.HIGH
                elif gap >= config.oee_medium_gap_threshold:
                    priority = PriorityLevel.MEDIUM
                else:
                    priority = PriorityLevel.LOW

                # Build evidence reference
                evidence_ref = EvidenceRef(
                    source_table="daily_summaries",
                    record_id=str(record.get("id", "")),
                    metric_name="oee_gap",
                    metric_value=f"{gap:.1f}%",
                    context=f"OEE {oee_pct:.1f}% vs target {target_oee:.1f}%",
                )

                action = ActionItem(
                    id=self._generate_action_id(ActionCategory.OEE, asset_id),
                    asset_id=str(asset_id),
                    asset_name=asset_info.get("name", "Unknown"),
                    priority_level=priority,
                    category=ActionCategory.OEE,
                    primary_metric_value=f"OEE: {oee_pct:.1f}%",
                    recommendation_text=f"Review performance on {asset_info.get('name', 'Unknown')} - {gap:.1f}% below target",
                    evidence_summary=f"OEE {gap:.1f}% below {target_oee:.1f}% target",
                    evidence_refs=[evidence_ref],
                    created_at=datetime.utcnow(),
                )
                actions.append((action, gap))

            # Sort by gap descending (worst performers first) - AC #3
            actions.sort(key=lambda x: x[1], reverse=True)

            result = [a[0] for a in actions]
            logger.info(f"Found {len(result)} OEE action items for {target_date}")
            return result

        except Exception as e:
            logger.error(f"Failed to get OEE actions: {e}")
            return []

    async def _get_financial_actions(
        self,
        target_date: date,
        assets_map: Dict[str, dict],
        config: Optional[ActionEngineConfig] = None,
    ) -> List[ActionItem]:
        """
        Get action items for assets with financial loss above threshold (Tier 3).

        AC #4: Assets with financial loss above threshold are included,
        sorted by loss amount descending.

        Args:
            target_date: The report date to query
            assets_map: Asset ID to info mapping
            config: Optional config to use (defaults to instance config)

        Returns:
            List of ActionItems for financial losses, sorted by amount (highest first)
        """
        try:
            client = self._get_client()
            config = config if config is not None else self._get_config()
            threshold = config.financial_loss_threshold

            # Query daily_summaries for the target date with financial loss above threshold
            query = client.table("daily_summaries").select(
                "id, asset_id, report_date, financial_loss_dollars, downtime_minutes, waste_count"
            )
            query = query.eq("report_date", target_date.isoformat())
            query = query.gt("financial_loss_dollars", threshold)

            response = query.execute()
            records = response.data or []

            if not records:
                logger.debug(f"No financial loss above threshold for {target_date}")
                return []

            actions = []
            for record in records:
                asset_id = record.get("asset_id")
                asset_info = assets_map.get(asset_id, {"name": "Unknown"})

                loss = record.get("financial_loss_dollars", 0) or 0
                downtime = record.get("downtime_minutes", 0) or 0
                waste = record.get("waste_count", 0) or 0

                # Determine priority based on loss amount (AC #4)
                if loss >= config.financial_high_threshold:
                    priority = PriorityLevel.HIGH
                elif loss >= config.financial_medium_threshold:
                    priority = PriorityLevel.MEDIUM
                else:
                    priority = PriorityLevel.LOW

                # Build evidence reference
                evidence_ref = EvidenceRef(
                    source_table="daily_summaries",
                    record_id=str(record.get("id", "")),
                    metric_name="financial_loss",
                    metric_value=f"${loss:,.2f}",
                    context=f"Downtime: {downtime}min, Waste: {waste} units",
                )

                action = ActionItem(
                    id=self._generate_action_id(ActionCategory.FINANCIAL, asset_id),
                    asset_id=str(asset_id),
                    asset_name=asset_info.get("name", "Unknown"),
                    priority_level=priority,
                    category=ActionCategory.FINANCIAL,
                    primary_metric_value=f"Loss: ${loss:,.2f}",
                    recommendation_text=f"Reduce losses on {asset_info.get('name', 'Unknown')}",
                    evidence_summary=f"Financial loss ${loss:,.2f} above ${threshold:,.2f} threshold",
                    evidence_refs=[evidence_ref],
                    created_at=datetime.utcnow(),
                )
                actions.append((action, loss))

            # Sort by financial loss descending (highest first) - AC #4
            actions.sort(key=lambda x: x[1], reverse=True)

            result = [a[0] for a in actions]
            logger.info(f"Found {len(result)} financial action items for {target_date}")
            return result

        except Exception as e:
            logger.error(f"Failed to get financial actions: {e}")
            return []

    def _merge_and_prioritize(
        self,
        safety: List[ActionItem],
        oee: List[ActionItem],
        financial: List[ActionItem]
    ) -> List[ActionItem]:
        """
        Merge action lists with tier-based priority and deduplication.

        AC #5: Combined sorting logic with deduplication.
        - Order: Safety > OEE > Financial
        - Duplicate assets keep highest priority category
        - Evidence from lower priority categories added to evidence_refs

        Args:
            safety: Safety action items (Tier 1)
            oee: OEE action items (Tier 2)
            financial: Financial action items (Tier 3)

        Returns:
            Merged and deduplicated action list
        """
        seen_assets: Dict[str, ActionItem] = {}
        result = []

        # Process in priority order: Safety > OEE > Financial
        for actions in [safety, oee, financial]:
            for action in actions:
                if action.asset_id not in seen_assets:
                    # First occurrence - add to result
                    result.append(action)
                    seen_assets[action.asset_id] = action
                else:
                    # Duplicate asset - add evidence_refs to existing item
                    existing = seen_assets[action.asset_id]
                    existing.evidence_refs.extend(action.evidence_refs)
                    logger.debug(
                        f"Deduplicated asset {action.asset_id}: "
                        f"kept {existing.category.value}, added evidence from {action.category.value}"
                    )

        return result

    async def generate_action_list(
        self,
        target_date: Optional[date] = None,
        limit: Optional[int] = None,
        category_filter: Optional[ActionCategory] = None,
        use_cache: bool = True,
        config_override: Optional[ActionEngineConfig] = None,
    ) -> ActionListResponse:
        """
        Generate the prioritized daily action list.

        AC #1: Main entry point for action prioritization.
        AC #9: Results can be cached for fast retrieval.
        AC #10: Returns empty list with metadata on empty state.

        Args:
            target_date: Report date (defaults to T-1)
            limit: Optional limit on number of items returned
            category_filter: Optional filter to single category
            use_cache: Whether to use cached results (default True)
            config_override: Optional config for this request (thread-safe override)

        Returns:
            ActionListResponse with prioritized actions and metadata
        """
        # Default to T-1 (yesterday)
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        cache_key = f"{target_date.isoformat()}-{category_filter.value if category_filter else 'all'}"

        # Check cache (AC #9) - only when no config override
        if use_cache and config_override is None and cache_key in self._action_list_cache:
            cached = self._action_list_cache[cache_key]
            logger.debug(f"Returning cached action list for {cache_key}")
            # Apply limit if needed
            if limit and len(cached.actions) > limit:
                cached_copy = ActionListResponse(
                    actions=cached.actions[:limit],
                    generated_at=cached.generated_at,
                    report_date=cached.report_date,
                    total_count=cached.total_count,
                    counts_by_category=cached.counts_by_category,
                )
                return cached_copy
            return cached

        # Use config_override if provided, otherwise get default config
        effective_config = config_override if config_override is not None else self._get_config()

        try:
            # Load assets
            assets_map = await self._load_assets()

            # Gather actions from each category (pass effective config)
            safety_actions = await self._get_safety_actions(target_date, assets_map)
            oee_actions = await self._get_oee_actions(target_date, assets_map, effective_config)
            financial_actions = await self._get_financial_actions(target_date, assets_map, effective_config)

            # Apply category filter if specified
            if category_filter:
                if category_filter == ActionCategory.SAFETY:
                    merged = safety_actions
                elif category_filter == ActionCategory.OEE:
                    merged = oee_actions
                else:
                    merged = financial_actions
            else:
                # Merge with tier-based priority and deduplication
                merged = self._merge_and_prioritize(
                    safety_actions,
                    oee_actions,
                    financial_actions
                )

            # Count by category (before limiting)
            counts = {
                "safety": sum(1 for a in merged if a.category == ActionCategory.SAFETY),
                "oee": sum(1 for a in merged if a.category == ActionCategory.OEE),
                "financial": sum(1 for a in merged if a.category == ActionCategory.FINANCIAL),
            }

            total_count = len(merged)

            # Apply limit
            if limit and len(merged) > limit:
                merged = merged[:limit]

            response = ActionListResponse(
                actions=merged,
                generated_at=datetime.utcnow(),
                report_date=target_date,
                total_count=total_count,
                counts_by_category=counts,
            )

            # Cache the full result (AC #9)
            if not category_filter:
                self._action_list_cache[cache_key] = response

            logger.info(
                f"Generated action list for {target_date}: "
                f"{total_count} items (safety={counts['safety']}, "
                f"oee={counts['oee']}, financial={counts['financial']})"
            )

            return response

        except Exception as e:
            logger.error(f"Failed to generate action list: {e}")
            # AC #10: Return empty list on error, don't raise
            return ActionListResponse(
                actions=[],
                generated_at=datetime.utcnow(),
                report_date=target_date,
                total_count=0,
                counts_by_category={"safety": 0, "oee": 0, "financial": 0},
            )

    def invalidate_cache(self, target_date: Optional[date] = None) -> None:
        """
        Invalidate cached action list(s).

        AC #9: Cache invalidation on new data ingestion.

        Args:
            target_date: Specific date to invalidate, or None for all
        """
        if target_date:
            keys_to_remove = [
                k for k in self._action_list_cache.keys()
                if k.startswith(target_date.isoformat())
            ]
            for key in keys_to_remove:
                del self._action_list_cache[key]
            logger.debug(f"Invalidated cache for {target_date}")
        else:
            self._action_list_cache.clear()
            logger.debug("Invalidated all action list cache")

    def clear_cache(self) -> None:
        """Clear all caches."""
        self._assets_cache.clear()
        self._action_list_cache.clear()
        self._cache_timestamp = None
        logger.debug("Action engine caches cleared")


# Module-level singleton
_action_engine: Optional[ActionEngine] = None


def get_action_engine() -> ActionEngine:
    """Get or create the singleton ActionEngine instance."""
    global _action_engine
    if _action_engine is None:
        _action_engine = ActionEngine()
    return _action_engine
