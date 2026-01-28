"""
Financial Impact Calculator Service

Core service for calculating financial impact of downtime and waste events.
Uses cost_centers data from Supabase for standard hourly rates.

Story: 2.7 - Financial Impact Calculator
AC: #1 - Financial Impact Service Exists
AC: #2 - Downtime Financial Calculation
AC: #3 - Waste/Scrap Financial Calculation
AC: #4 - Combined Financial Impact
AC: #8 - Error Handling for Missing Cost Data
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from supabase import create_client, Client

from app.core.config import get_settings
from app.schemas.financial import (
    AssetFinancialContext,
    FinancialImpactBreakdown,
    FinancialImpactResponse,
    LiveFinancialImpact,
)

logger = logging.getLogger(__name__)


class FinancialServiceError(Exception):
    """Base exception for financial service errors."""
    pass


class FinancialService:
    """
    Service for calculating financial impact of operational losses.

    Calculates dollar values for:
    - Downtime: (downtime_minutes / 60) * standard_hourly_rate
    - Waste: waste_count * cost_per_unit
    - Total: downtime_loss + waste_loss

    Uses cost_centers table for asset-specific rates with fallback
    to configurable defaults when data is missing.
    """

    def __init__(self):
        """Initialize the financial service."""
        self._supabase_client: Optional[Client] = None
        self._cost_center_cache: Dict[str, Dict] = {}  # asset_id -> cost center data
        self._asset_cache: Dict[str, Dict] = {}  # asset_id -> asset info
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_seconds: int = 300  # 5 minute cache

    def _get_supabase_client(self) -> Client:
        """Get or create Supabase client."""
        if self._supabase_client is None:
            settings = get_settings()
            if not settings.supabase_url or not settings.supabase_key:
                raise FinancialServiceError("Supabase not configured")
            self._supabase_client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
        return self._supabase_client

    def _is_cache_valid(self) -> bool:
        """Check if the cache is still valid."""
        if self._cache_timestamp is None:
            return False
        elapsed = (datetime.utcnow() - self._cache_timestamp).total_seconds()
        return elapsed < self._cache_ttl_seconds

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cost_center_cache.clear()
        self._asset_cache.clear()
        self._cache_timestamp = None
        logger.debug("Financial service cache cleared")

    def load_cost_centers(self, force: bool = False) -> Dict[str, Dict]:
        """
        Load cost center data from Supabase with caching.

        Args:
            force: Force reload even if cache is valid

        Returns:
            Dictionary mapping asset_id to cost center info

        Raises:
            FinancialServiceError: If loading fails
        """
        if not force and self._is_cache_valid() and self._cost_center_cache:
            return self._cost_center_cache

        try:
            client = self._get_supabase_client()
            response = client.table("cost_centers").select(
                "id, asset_id, standard_hourly_rate"
            ).execute()

            self._cost_center_cache = {}
            for cc in response.data:
                asset_id = cc.get("asset_id")
                if asset_id:
                    hourly_rate = cc.get("standard_hourly_rate")
                    self._cost_center_cache[asset_id] = {
                        "id": cc.get("id"),
                        "hourly_rate": Decimal(str(hourly_rate)) if hourly_rate is not None else None,
                        "cost_per_unit": None,  # Not in schema - will use default
                    }

            self._cache_timestamp = datetime.utcnow()
            logger.info(f"Loaded {len(self._cost_center_cache)} cost centers")
            return self._cost_center_cache

        except Exception as e:
            logger.error(f"Failed to load cost centers: {e}")
            raise FinancialServiceError(f"Failed to load cost centers: {e}") from e

    def load_assets(self, force: bool = False) -> Dict[str, Dict]:
        """
        Load asset information from Supabase with caching.

        Args:
            force: Force reload even if cache is valid

        Returns:
            Dictionary mapping asset_id to asset info
        """
        if not force and self._is_cache_valid() and self._asset_cache:
            return self._asset_cache

        try:
            client = self._get_supabase_client()
            response = client.table("assets").select("id, name, source_id, area").execute()

            self._asset_cache = {}
            for asset in response.data:
                asset_id = asset.get("id")
                if asset_id:
                    self._asset_cache[asset_id] = {
                        "name": asset.get("name"),
                        "source_id": asset.get("source_id"),
                        "area": asset.get("area"),
                    }

            logger.debug(f"Loaded {len(self._asset_cache)} assets")
            return self._asset_cache

        except Exception as e:
            logger.warning(f"Failed to load assets: {e}")
            return {}

    def get_hourly_rate(self, asset_id: str) -> Tuple[Decimal, bool]:
        """
        Get the hourly rate for an asset from its cost center.

        Args:
            asset_id: UUID of the asset (as string)

        Returns:
            Tuple of (hourly_rate, is_estimated)
            is_estimated is True if using default rate
        """
        settings = get_settings()

        if not self._cost_center_cache:
            self.load_cost_centers()

        cost_center = self._cost_center_cache.get(asset_id, {})
        hourly_rate = cost_center.get("hourly_rate")

        if hourly_rate is not None and hourly_rate > 0:
            return hourly_rate, False

        # Use default rate
        default_rate = Decimal(str(settings.default_hourly_rate))
        logger.warning(f"Using default hourly rate ${default_rate} for asset {asset_id}")
        return default_rate, True

    def get_cost_per_unit(self, asset_id: str) -> Tuple[Decimal, bool]:
        """
        Get the cost per unit for an asset from its cost center.

        Args:
            asset_id: UUID of the asset (as string)

        Returns:
            Tuple of (cost_per_unit, is_estimated)
            is_estimated is True if using default rate
        """
        settings = get_settings()

        if not self._cost_center_cache:
            self.load_cost_centers()

        cost_center = self._cost_center_cache.get(asset_id, {})
        cost_per_unit = cost_center.get("cost_per_unit")

        if cost_per_unit is not None and cost_per_unit > 0:
            return cost_per_unit, False

        # Use default rate
        default_cost = Decimal(str(settings.default_cost_per_unit))
        logger.debug(f"Using default cost per unit ${default_cost} for asset {asset_id}")
        return default_cost, True

    def calculate_downtime_loss(
        self,
        downtime_minutes: int,
        hourly_rate: Decimal
    ) -> Decimal:
        """
        Calculate financial loss from downtime.

        Formula: financial_loss = (downtime_minutes / 60) * standard_hourly_rate

        Args:
            downtime_minutes: Duration of downtime in minutes
            hourly_rate: Standard hourly rate for the asset

        Returns:
            Financial loss in dollars as Decimal
        """
        if downtime_minutes <= 0 or hourly_rate <= 0:
            return Decimal("0.00")

        hours = Decimal(downtime_minutes) / Decimal(60)
        loss = hours * hourly_rate
        return loss.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_waste_loss(
        self,
        waste_count: int,
        cost_per_unit: Decimal
    ) -> Decimal:
        """
        Calculate financial loss from waste/scrap.

        Formula: waste_loss = waste_count * cost_per_unit

        Args:
            waste_count: Number of waste/scrap units
            cost_per_unit: Cost per unit

        Returns:
            Financial loss in dollars as Decimal
        """
        if waste_count <= 0 or cost_per_unit <= 0:
            return Decimal("0.00")

        loss = Decimal(waste_count) * cost_per_unit
        return loss.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_total_impact(
        self,
        asset_id: str,
        downtime_minutes: int,
        waste_count: int,
        hourly_rate: Optional[Decimal] = None,
        cost_per_unit: Optional[Decimal] = None
    ) -> FinancialImpactBreakdown:
        """
        Calculate total financial impact combining downtime and waste.

        Args:
            asset_id: UUID of the asset (as string)
            downtime_minutes: Duration of downtime in minutes
            waste_count: Number of waste/scrap units
            hourly_rate: Override hourly rate (uses cost_centers if None)
            cost_per_unit: Override cost per unit (uses cost_centers if None)

        Returns:
            FinancialImpactBreakdown with all components
        """
        is_estimated = False

        # Get rates if not provided
        if hourly_rate is None:
            hourly_rate, hourly_estimated = self.get_hourly_rate(asset_id)
            is_estimated = is_estimated or hourly_estimated
        else:
            hourly_rate = Decimal(str(hourly_rate))

        if cost_per_unit is None:
            cost_per_unit, cost_estimated = self.get_cost_per_unit(asset_id)
            is_estimated = is_estimated or cost_estimated
        else:
            cost_per_unit = Decimal(str(cost_per_unit))

        # Calculate losses
        downtime_loss = self.calculate_downtime_loss(downtime_minutes, hourly_rate)
        waste_loss = self.calculate_waste_loss(waste_count, cost_per_unit)
        total_loss = downtime_loss + waste_loss

        return FinancialImpactBreakdown(
            downtime_minutes=downtime_minutes,
            downtime_hours=round(downtime_minutes / 60, 2),
            hourly_rate=float(hourly_rate),
            downtime_loss=float(downtime_loss),
            waste_count=waste_count,
            cost_per_unit=float(cost_per_unit),
            waste_loss=float(waste_loss),
            total_loss=float(total_loss.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        )

    async def get_financial_impact(
        self,
        asset_id: str,
        start_date: date,
        end_date: Optional[date] = None
    ) -> FinancialImpactResponse:
        """
        Get financial impact for an asset over a date range.

        Fetches data from daily_summaries and calculates financial impact.

        Args:
            asset_id: UUID of the asset (as string)
            start_date: Start date of the period
            end_date: End date of the period (defaults to start_date)

        Returns:
            FinancialImpactResponse with full impact details
        """
        settings = get_settings()

        if end_date is None:
            end_date = start_date

        try:
            client = self._get_supabase_client()

            # Load cost centers and assets
            self.load_cost_centers()
            self.load_assets()

            # Get asset info
            asset_info = self._asset_cache.get(asset_id, {})
            asset_name = asset_info.get("name")

            # Query daily_summaries for the date range
            query = client.table("daily_summaries").select(
                "asset_id, date, downtime_minutes, waste, financial_loss"
            ).eq("asset_id", asset_id)

            if start_date == end_date:
                query = query.eq("date", start_date.isoformat())
            else:
                query = query.gte("date", start_date.isoformat())
                query = query.lte("date", end_date.isoformat())

            response = query.execute()

            # Aggregate data
            total_downtime = 0
            total_waste = 0

            for record in response.data or []:
                total_downtime += record.get("downtime_minutes") or 0
                total_waste += record.get("waste") or 0

            # Calculate financial impact
            hourly_rate, hourly_estimated = self.get_hourly_rate(asset_id)
            cost_per_unit, cost_estimated = self.get_cost_per_unit(asset_id)
            is_estimated = hourly_estimated or cost_estimated

            downtime_loss = self.calculate_downtime_loss(total_downtime, hourly_rate)
            waste_loss = self.calculate_waste_loss(total_waste, cost_per_unit)
            total_loss = downtime_loss + waste_loss

            return FinancialImpactResponse(
                asset_id=asset_id,
                asset_name=asset_name,
                period_start=start_date,
                period_end=end_date,
                downtime_minutes=total_downtime,
                downtime_loss=float(downtime_loss),
                waste_count=total_waste,
                waste_loss=float(waste_loss),
                total_loss=float(total_loss.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                currency=settings.financial_currency,
                standard_hourly_rate=float(hourly_rate),
                cost_per_unit=float(cost_per_unit),
                is_estimated=is_estimated,
            )

        except Exception as e:
            logger.error(f"Failed to get financial impact for asset {asset_id}: {e}")
            raise FinancialServiceError(f"Failed to get financial impact: {e}") from e

    async def get_live_financial_impact(
        self,
        asset_id: str
    ) -> LiveFinancialImpact:
        """
        Get live financial impact for current shift from live_snapshots.

        Args:
            asset_id: UUID of the asset (as string)

        Returns:
            LiveFinancialImpact with accumulated values
        """
        settings = get_settings()

        try:
            client = self._get_supabase_client()

            # Load data
            self.load_cost_centers()
            self.load_assets()

            asset_info = self._asset_cache.get(asset_id, {})
            asset_name = asset_info.get("name")

            # Get latest live snapshot for this asset
            response = client.table("live_snapshots").select(
                "asset_id, snapshot_timestamp, output_actual, output_target, variance_percent, financial_loss_dollars"
            ).eq("asset_id", asset_id).order(
                "snapshot_timestamp", desc=True
            ).limit(1).execute()

            if not response.data:
                # No live data available
                hourly_rate, hourly_estimated = self.get_hourly_rate(asset_id)
                cost_per_unit, cost_estimated = self.get_cost_per_unit(asset_id)
                return LiveFinancialImpact(
                    asset_id=asset_id,
                    asset_name=asset_name,
                    shift_start=None,
                    accumulated_downtime_minutes=0,
                    accumulated_downtime_loss=0.0,
                    accumulated_waste_count=0,
                    accumulated_waste_loss=0.0,
                    accumulated_total_loss=0.0,
                    currency=settings.financial_currency,
                    is_estimated=hourly_estimated or cost_estimated,
                )

            snapshot = response.data[0]
            snapshot_time = snapshot.get("snapshot_timestamp")
            financial_loss = snapshot.get("financial_loss_dollars") or 0.0

            hourly_rate, hourly_estimated = self.get_hourly_rate(asset_id)
            cost_per_unit, cost_estimated = self.get_cost_per_unit(asset_id)

            return LiveFinancialImpact(
                asset_id=asset_id,
                asset_name=asset_name,
                shift_start=snapshot_time,
                accumulated_downtime_minutes=0,  # Would need to aggregate from multiple snapshots
                accumulated_downtime_loss=0.0,
                accumulated_waste_count=0,
                accumulated_waste_loss=0.0,
                accumulated_total_loss=float(financial_loss),
                currency=settings.financial_currency,
                is_estimated=hourly_estimated or cost_estimated,
            )

        except Exception as e:
            logger.error(f"Failed to get live financial impact for asset {asset_id}: {e}")
            raise FinancialServiceError(f"Failed to get live financial impact: {e}") from e

    def calculate_for_daily_summary(
        self,
        asset_id: str,
        downtime_minutes: int,
        waste_count: int
    ) -> Tuple[Decimal, bool]:
        """
        Calculate financial loss for a daily summary record.

        Used by Pipeline A (Morning Report) for batch processing.

        Args:
            asset_id: UUID of the asset (as string)
            downtime_minutes: Total downtime in minutes
            waste_count: Total waste/scrap count

        Returns:
            Tuple of (total_financial_loss, is_estimated)
        """
        breakdown = self.calculate_total_impact(
            asset_id=asset_id,
            downtime_minutes=downtime_minutes,
            waste_count=waste_count
        )

        hourly_rate, hourly_estimated = self.get_hourly_rate(asset_id)
        cost_per_unit, cost_estimated = self.get_cost_per_unit(asset_id)
        is_estimated = hourly_estimated or cost_estimated

        return Decimal(str(breakdown.total_loss)), is_estimated

    def calculate_for_live_snapshot(
        self,
        asset_id: str,
        downtime_minutes: int,
        waste_count: int
    ) -> Tuple[Decimal, bool]:
        """
        Calculate financial loss for a live snapshot record.

        Used by Pipeline B (Live Pulse) for real-time processing.

        Args:
            asset_id: UUID of the asset (as string)
            downtime_minutes: Accumulated downtime this shift
            waste_count: Accumulated waste this shift

        Returns:
            Tuple of (total_financial_loss, is_estimated)
        """
        return self.calculate_for_daily_summary(asset_id, downtime_minutes, waste_count)


# Module-level singleton
_financial_service: Optional[FinancialService] = None


def get_financial_service() -> FinancialService:
    """Get or create the singleton financial service instance."""
    global _financial_service
    if _financial_service is None:
        _financial_service = FinancialService()
    return _financial_service
