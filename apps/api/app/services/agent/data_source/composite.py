"""
Composite DataSource Router (Story 5.2)

Routes queries to appropriate data source based on data type.
Currently delegates to Supabase, with architecture for future MSSQL integration.

AC#8: CompositeDataSource Router (Future-Ready)
- Routes queries to appropriate source
- Currently delegates to SupabaseDataSource
- Architecture supports adding MSSQLDataSource later
"""

import logging
from datetime import date
from typing import Optional

from app.services.agent.data_source.protocol import DataResult, DataSource
from app.services.agent.data_source.supabase import SupabaseDataSource

logger = logging.getLogger(__name__)


class CompositeDataSource:
    """
    Routes queries to appropriate data source.

    AC#8: CompositeDataSource Router (Future-Ready)
    - Currently delegates everything to Supabase
    - Future: Add MSSQLDataSource and routing logic based on data type/freshness

    Routing Strategy (Future):
    - Historical data (OEE, downtime) -> Supabase (cached data)
    - Real-time data (live snapshots) -> MSSQL (direct query) or Supabase (polled cache)
    - Assets/configuration -> Supabase (Plant Object Model)

    Example future routing:
        async def get_live_snapshot(self, asset_id: str) -> DataResult:
            if self.mssql and self.use_realtime:
                return await self.mssql.get_live_snapshot(asset_id)
            return await self.primary.get_live_snapshot(asset_id)
    """

    def __init__(
        self,
        primary: Optional[DataSource] = None,
        # TODO: Add MSSQLDataSource for real-time queries when available
        # mssql: Optional[MSSQLDataSource] = None,
    ):
        """
        Initialize CompositeDataSource.

        Args:
            primary: Primary data source (default: SupabaseDataSource)
        """
        self.primary = primary or SupabaseDataSource()
        self.source_name = "composite"

        # TODO: Future MSSQL integration
        # self.mssql = mssql
        # self.use_realtime = settings.use_realtime_mssql

        logger.info("CompositeDataSource initialized with primary source")

    # =========================================================================
    # Asset Methods - Always from Supabase (Plant Object Model)
    # =========================================================================

    async def get_asset(self, asset_id: str) -> DataResult:
        """Assets always come from Supabase (Plant Object Model)."""
        return await self.primary.get_asset(asset_id)

    async def get_asset_by_name(self, name: str) -> DataResult:
        """Assets always come from Supabase (Plant Object Model)."""
        return await self.primary.get_asset_by_name(name)

    async def get_assets_by_area(self, area: str) -> DataResult:
        """Assets always come from Supabase (Plant Object Model)."""
        return await self.primary.get_assets_by_area(area)

    async def get_similar_assets(self, name: str, limit: int = 5) -> DataResult:
        """Assets always come from Supabase (Plant Object Model)."""
        return await self.primary.get_similar_assets(name, limit)

    async def get_all_assets(self) -> DataResult:
        """Assets always come from Supabase (Plant Object Model)."""
        return await self.primary.get_all_assets()

    # =========================================================================
    # OEE Methods - Historical data from Supabase cache
    # =========================================================================

    async def get_oee(
        self,
        asset_id: str,
        start_date: date,
        end_date: date,
    ) -> DataResult:
        """
        Get OEE metrics for an asset.

        Historical data always comes from Supabase cache.
        TODO: Route to MSSQL for real-time OEE calculation if needed.
        """
        return await self.primary.get_oee(asset_id, start_date, end_date)

    async def get_oee_by_area(
        self,
        area: str,
        start_date: date,
        end_date: date,
    ) -> DataResult:
        """
        Get OEE metrics for all assets in an area.

        Historical data always comes from Supabase cache.
        """
        return await self.primary.get_oee_by_area(area, start_date, end_date)

    # =========================================================================
    # Downtime Methods - Historical data from Supabase cache
    # =========================================================================

    async def get_downtime(
        self,
        asset_id: str,
        start_date: date,
        end_date: date,
    ) -> DataResult:
        """
        Get downtime records for an asset.

        Historical data always comes from Supabase cache.
        TODO: Route to MSSQL for real-time downtime if needed.
        """
        return await self.primary.get_downtime(asset_id, start_date, end_date)

    async def get_downtime_by_area(
        self,
        area: str,
        start_date: date,
        end_date: date,
    ) -> DataResult:
        """
        Get downtime records for all assets in an area.

        Historical data always comes from Supabase cache.
        """
        return await self.primary.get_downtime_by_area(area, start_date, end_date)

    # =========================================================================
    # Live Data Methods - May route to MSSQL for real-time in future
    # =========================================================================

    async def get_live_snapshot(self, asset_id: str) -> DataResult:
        """
        Get current live snapshot for an asset.

        Currently from Supabase cache (populated by polling pipeline).
        TODO: Route to MSSQL for direct real-time queries when needed.

        Future implementation:
            if self.mssql and self.use_realtime:
                return await self.mssql.get_live_snapshot(asset_id)
            return await self.primary.get_live_snapshot(asset_id)
        """
        return await self.primary.get_live_snapshot(asset_id)

    async def get_live_snapshots_by_area(self, area: str) -> DataResult:
        """
        Get live snapshots for all assets in an area.

        Currently from Supabase cache (populated by polling pipeline).
        TODO: Route to MSSQL for direct real-time queries when needed.
        """
        return await self.primary.get_live_snapshots_by_area(area)

    # =========================================================================
    # Target Methods - Always from Supabase (configuration data)
    # =========================================================================

    async def get_shift_target(self, asset_id: str) -> DataResult:
        """Shift targets always come from Supabase."""
        return await self.primary.get_shift_target(asset_id)

    # =========================================================================
    # Safety Methods - Always from Supabase (event logging)
    # =========================================================================

    async def get_safety_events(
        self,
        asset_id: Optional[str],
        start_date: date,
        end_date: date,
        include_resolved: bool = False,
    ) -> DataResult:
        """Safety events always come from Supabase."""
        return await self.primary.get_safety_events(
            asset_id, start_date, end_date, include_resolved
        )
