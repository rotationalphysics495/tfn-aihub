"""
Context Builder for Smart Summary Generation

Assembles data from multiple tables into a structured context for LLM processing.

Story: 3.5 - Smart Summary Generator
AC: #2 - Data Context Assembly
"""

import logging
from datetime import date as date_type, datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from supabase import create_client, Client

from app.core.config import get_settings
from app.services.action_engine import ActionEngine, get_action_engine
from app.schemas.action import ActionListResponse

logger = logging.getLogger(__name__)


class SummaryContext(BaseModel):
    """
    Structured context object for LLM prompt generation.

    AC#2: Data is formatted into a structured context object for the LLM.
    """

    target_date: date_type = Field(..., description="The report date")
    daily_summaries: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Daily summary records with OEE and financial data"
    )
    safety_events: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Safety event records"
    )
    cost_centers: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Cost center data keyed by asset_id"
    )
    action_items: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Prioritized action items from Action Engine"
    )
    assets: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Asset reference data keyed by asset_id"
    )
    target_oee: float = Field(
        default=85.0,
        description="Target OEE percentage"
    )
    assembled_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When context was assembled"
    )

    @property
    def has_data(self) -> bool:
        """Check if context has any meaningful data."""
        return bool(
            self.daily_summaries or
            self.safety_events or
            self.action_items
        )

    @property
    def safety_event_count(self) -> int:
        """Count of unresolved safety events."""
        return sum(
            1 for e in self.safety_events
            if not e.get("is_resolved", False)
        )

    @property
    def total_financial_loss(self) -> float:
        """Total financial loss from daily summaries."""
        return sum(
            s.get("financial_loss_dollars", 0) or 0
            for s in self.daily_summaries
        )


class ContextBuilderError(Exception):
    """Raised when context building fails."""
    pass


class ContextBuilder:
    """
    Builds structured context for Smart Summary generation.

    AC#2: Retrieves and assembles data from:
    - daily_summaries table
    - safety_events table
    - cost_centers table
    - Action Engine (Story 3.1)
    """

    def __init__(
        self,
        supabase_client: Optional[Client] = None,
        action_engine: Optional[ActionEngine] = None,
    ):
        """
        Initialize the Context Builder.

        Args:
            supabase_client: Optional Supabase client
            action_engine: Optional ActionEngine instance
        """
        self._client = supabase_client
        self._action_engine = action_engine

    def _get_client(self) -> Client:
        """Get or create Supabase client."""
        if self._client is None:
            settings = get_settings()
            if not settings.supabase_url or not settings.supabase_key:
                raise ContextBuilderError("Supabase not configured")
            self._client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
        return self._client

    def _get_action_engine(self) -> ActionEngine:
        """Get or create ActionEngine instance."""
        if self._action_engine is None:
            self._action_engine = get_action_engine()
        return self._action_engine

    async def fetch_daily_summaries(self, target_date: date_type) -> List[Dict[str, Any]]:
        """
        Fetch daily_summaries for the target date.

        AC#2: Retrieves data from daily_summaries table.

        Args:
            target_date: Date to query

        Returns:
            List of daily summary records
        """
        try:
            client = self._get_client()

            response = client.table("daily_summaries").select(
                "id, asset_id, report_date, oee_percentage, actual_output, "
                "target_output, financial_loss_dollars, downtime_minutes, "
                "waste_count, created_at, updated_at"
            ).eq("report_date", target_date.isoformat()).execute()

            logger.debug(
                f"Fetched {len(response.data or [])} daily summaries for {target_date}"
            )
            return response.data or []

        except Exception as e:
            logger.error(f"Failed to fetch daily summaries: {e}")
            return []

    async def fetch_safety_events(self, target_date: date_type) -> List[Dict[str, Any]]:
        """
        Fetch safety_events for the target date.

        AC#2: Retrieves data from safety_events table.

        Args:
            target_date: Date to query (includes events from this date)

        Returns:
            List of safety event records
        """
        try:
            client = self._get_client()

            # Query events from start of target_date
            start_of_day = datetime.combine(target_date, datetime.min.time())
            end_of_day = datetime.combine(
                target_date + timedelta(days=1),
                datetime.min.time()
            )

            response = client.table("safety_events").select(
                "id, asset_id, event_timestamp, duration_minutes, reason_code, "
                "severity, description, is_resolved, created_at"
            ).gte(
                "event_timestamp", start_of_day.isoformat()
            ).lt(
                "event_timestamp", end_of_day.isoformat()
            ).execute()

            logger.debug(
                f"Fetched {len(response.data or [])} safety events for {target_date}"
            )
            return response.data or []

        except Exception as e:
            logger.error(f"Failed to fetch safety events: {e}")
            return []

    async def fetch_cost_centers(self) -> Dict[str, Dict[str, Any]]:
        """
        Fetch cost_centers for financial context.

        AC#2: Retrieves data from cost_centers table.

        Returns:
            Dictionary mapping asset_id to cost center data
        """
        try:
            client = self._get_client()

            response = client.table("cost_centers").select(
                "id, asset_id, standard_hourly_rate, cost_per_unit"
            ).execute()

            result = {}
            for center in response.data or []:
                asset_id = center.get("asset_id")
                if asset_id:
                    result[asset_id] = center

            logger.debug(f"Fetched {len(result)} cost centers")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch cost centers: {e}")
            return {}

    async def fetch_assets(self) -> Dict[str, Dict[str, Any]]:
        """
        Fetch asset reference data.

        Returns:
            Dictionary mapping asset_id to asset info
        """
        try:
            client = self._get_client()

            response = client.table("assets").select(
                "id, name, source_id, area"
            ).execute()

            result = {}
            for asset in response.data or []:
                asset_id = asset.get("id")
                if asset_id:
                    result[asset_id] = asset

            logger.debug(f"Fetched {len(result)} assets")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch assets: {e}")
            return {}

    async def fetch_action_items(self, target_date: date_type) -> List[Dict[str, Any]]:
        """
        Fetch action items from Action Engine (Story 3.1).

        AC#2: Retrieves action items from Action Engine.

        Args:
            target_date: Date to query

        Returns:
            List of action item dictionaries
        """
        try:
            engine = self._get_action_engine()
            response: ActionListResponse = await engine.generate_action_list(
                target_date=target_date,
                use_cache=True,
            )

            # Convert ActionItem objects to dictionaries
            items = []
            for action in response.actions:
                items.append({
                    "id": action.id,
                    "asset_id": action.asset_id,
                    "asset_name": action.asset_name,
                    "category": action.category.value,
                    "priority_level": action.priority_level.value,
                    "primary_metric_value": action.primary_metric_value,
                    "recommendation_text": action.recommendation_text,
                    "evidence_summary": action.evidence_summary,
                    "financial_impact_usd": action.financial_impact_usd,
                })

            logger.debug(f"Fetched {len(items)} action items for {target_date}")
            return items

        except Exception as e:
            logger.error(f"Failed to fetch action items: {e}")
            return []

    def _enrich_with_asset_names(
        self,
        records: List[Dict[str, Any]],
        assets: Dict[str, Dict[str, Any]],
        asset_id_field: str = "asset_id",
    ) -> List[Dict[str, Any]]:
        """
        Enrich records with asset names for display.

        Args:
            records: List of records to enrich
            assets: Asset mapping
            asset_id_field: Field name for asset ID

        Returns:
            Enriched records
        """
        enriched = []
        for record in records:
            asset_id = record.get(asset_id_field)
            asset_info = assets.get(asset_id, {})
            enriched_record = {
                **record,
                "asset_name": asset_info.get("name", "Unknown Asset"),
            }
            enriched.append(enriched_record)
        return enriched

    async def build_context(
        self,
        target_date: Optional[date_type] = None,
    ) -> SummaryContext:
        """
        Build complete context for Smart Summary generation.

        AC#2: Assembles data from all sources into structured context.

        Args:
            target_date: Date to build context for (defaults to T-1)

        Returns:
            SummaryContext with all assembled data

        Raises:
            ContextBuilderError: If context building fails completely
        """
        if target_date is None:
            target_date = date_type.today() - timedelta(days=1)

        logger.info(f"Building context for Smart Summary: {target_date}")

        try:
            # Fetch all data sources concurrently
            assets = await self.fetch_assets()
            cost_centers = await self.fetch_cost_centers()
            daily_summaries = await self.fetch_daily_summaries(target_date)
            safety_events = await self.fetch_safety_events(target_date)
            action_items = await self.fetch_action_items(target_date)

            # Enrich records with asset names
            enriched_summaries = self._enrich_with_asset_names(
                daily_summaries, assets
            )
            enriched_events = self._enrich_with_asset_names(
                safety_events, assets
            )

            # Get target OEE from settings
            settings = get_settings()
            target_oee = settings.target_oee_percentage

            context = SummaryContext(
                target_date=target_date,
                daily_summaries=enriched_summaries,
                safety_events=enriched_events,
                cost_centers=cost_centers,
                action_items=action_items,
                assets=assets,
                target_oee=target_oee,
            )

            logger.info(
                f"Context built: {len(enriched_summaries)} summaries, "
                f"{len(enriched_events)} safety events, "
                f"{len(action_items)} action items"
            )

            return context

        except Exception as e:
            logger.error(f"Failed to build context: {e}")
            raise ContextBuilderError(f"Context building failed: {e}") from e


# Module-level singleton
_context_builder: Optional[ContextBuilder] = None


def get_context_builder() -> ContextBuilder:
    """Get or create singleton ContextBuilder instance."""
    global _context_builder
    if _context_builder is None:
        _context_builder = ContextBuilder()
    return _context_builder
