"""
OEE and Financial Calculator Service

Calculates OEE (Overall Equipment Effectiveness) metrics and financial impact
from cleaned production data.

Story: 2.1 - Batch Data Pipeline (T-1)
AC: #4 - OEE Calculation
AC: #5 - Financial Loss Calculation
"""

import logging
import os
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from supabase import create_client, Client

from app.core.config import get_settings
from app.models.pipeline import (
    CleanedProductionData,
    OEEMetrics,
    FinancialMetrics,
)

logger = logging.getLogger(__name__)


class CalculationError(Exception):
    """Raised when calculation fails."""
    pass


# Default values for edge cases
DEFAULT_SHIFT_HOURS = 8  # 8-hour shift
DEFAULT_IDEAL_CYCLE_RATE = 100  # units per hour (override per asset if needed)

# Get defaults from settings (AC #8 - configurable defaults)
def _get_default_hourly_rate() -> Decimal:
    """Get default hourly rate from settings."""
    settings = get_settings()
    return Decimal(str(settings.default_hourly_rate))

def _get_default_unit_cost() -> Decimal:
    """Get default cost per unit from settings."""
    settings = get_settings()
    return Decimal(str(settings.default_cost_per_unit))

# Keep for backwards compatibility
DEFAULT_UNIT_COST = Decimal("10.00")  # Will use settings-based function where needed


class Calculator:
    """
    Calculates OEE metrics and financial impact.

    OEE Formula:
        OEE = Availability x Performance x Quality

        Availability = Run Time / Planned Production Time
        Performance = Actual Output / (Run Time x Ideal Cycle Rate)
        Quality = Good Units / Total Units Produced

    Financial Impact:
        Downtime Cost = Downtime Minutes x (Hourly Rate / 60)
        Waste Cost = Scrap Units x Unit Cost
        Total Loss = Downtime Cost + Waste Cost
    """

    def __init__(self):
        """Initialize the calculator."""
        self._supabase_client: Optional[Client] = None
        self._cost_center_cache: Dict[UUID, Dict] = {}  # asset_id -> cost center data

    def _get_supabase_client(self) -> Client:
        """Get or create Supabase client."""
        if self._supabase_client is None:
            settings = get_settings()
            if not settings.supabase_url or not settings.supabase_key:
                raise CalculationError("Supabase not configured")
            self._supabase_client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
        return self._supabase_client

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cost_center_cache.clear()

    def load_cost_centers(self) -> Dict[UUID, Dict]:
        """
        Load all cost center data from Supabase.

        Returns:
            Dictionary mapping asset_id to cost center info

        Raises:
            CalculationError: If loading fails
        """
        try:
            client = self._get_supabase_client()
            response = client.table("cost_centers").select(
                "id, asset_id, standard_hourly_rate, cost_per_unit"
            ).execute()

            self._cost_center_cache = {}
            for cc in response.data:
                asset_id = cc.get("asset_id")
                if asset_id:
                    hourly_rate = cc.get("standard_hourly_rate")
                    cost_per_unit = cc.get("cost_per_unit")
                    self._cost_center_cache[UUID(asset_id)] = {
                        "id": UUID(cc.get("id")),
                        "hourly_rate": Decimal(str(hourly_rate)) if hourly_rate is not None else None,
                        "cost_per_unit": Decimal(str(cost_per_unit)) if cost_per_unit is not None else None,
                    }

            logger.info(f"Loaded {len(self._cost_center_cache)} cost centers")
            return self._cost_center_cache

        except Exception as e:
            logger.error(f"Failed to load cost centers: {e}")
            raise CalculationError(f"Failed to load cost centers: {e}") from e

    def get_hourly_rate(self, asset_id: UUID) -> Tuple[Decimal, bool]:
        """
        Get the hourly rate for an asset from its cost center.

        Args:
            asset_id: UUID of the asset

        Returns:
            Tuple of (hourly_rate, is_estimated)
            is_estimated is True if using default rate (AC #8)
        """
        if not self._cost_center_cache:
            self.load_cost_centers()

        cost_center = self._cost_center_cache.get(asset_id, {})
        hourly_rate = cost_center.get("hourly_rate")

        if hourly_rate is not None and hourly_rate > 0:
            return hourly_rate, False

        # Use configurable default rate (AC #8)
        default_rate = _get_default_hourly_rate()
        logger.warning(f"Using default hourly rate ${default_rate} for asset {asset_id}")
        return default_rate, True

    def get_cost_per_unit(self, asset_id: UUID) -> Tuple[Decimal, bool]:
        """
        Get the cost per unit for an asset from its cost center.

        Args:
            asset_id: UUID of the asset

        Returns:
            Tuple of (cost_per_unit, is_estimated)
            is_estimated is True if using default rate (AC #8)
        """
        if not self._cost_center_cache:
            self.load_cost_centers()

        cost_center = self._cost_center_cache.get(asset_id, {})
        cost_per_unit = cost_center.get("cost_per_unit")

        if cost_per_unit is not None and cost_per_unit > 0:
            return cost_per_unit, False

        # Use configurable default rate (AC #8)
        default_cost = _get_default_unit_cost()
        logger.debug(f"Using default cost per unit ${default_cost} for asset {asset_id}")
        return default_cost, True

    def _safe_divide(
        self,
        numerator: Decimal,
        denominator: Decimal,
        default: Decimal = Decimal("0")
    ) -> Decimal:
        """
        Safely divide two decimals, handling zero denominator.

        Args:
            numerator: Dividend
            denominator: Divisor
            default: Value to return if denominator is zero

        Returns:
            Result of division or default
        """
        if denominator == 0:
            return default
        return numerator / denominator

    def calculate_availability(
        self,
        planned_production_time_minutes: int,
        downtime_minutes: int
    ) -> Tuple[Decimal, int]:
        """
        Calculate availability component of OEE.

        Availability = Run Time / Planned Production Time
        Run Time = Planned Production Time - Downtime

        Args:
            planned_production_time_minutes: Total planned production time in minutes
            downtime_minutes: Total downtime in minutes

        Returns:
            Tuple of (availability ratio 0-1, run_time_minutes)
        """
        if planned_production_time_minutes <= 0:
            return Decimal("0"), 0

        run_time = max(0, planned_production_time_minutes - downtime_minutes)
        availability = self._safe_divide(
            Decimal(run_time),
            Decimal(planned_production_time_minutes)
        )

        # Cap at 1.0 (100%)
        availability = min(Decimal("1"), availability)

        return availability, run_time

    def calculate_performance(
        self,
        actual_output: int,
        run_time_minutes: int,
        ideal_cycle_rate_per_hour: int = DEFAULT_IDEAL_CYCLE_RATE
    ) -> Tuple[Decimal, int]:
        """
        Calculate performance component of OEE.

        Performance = Actual Output / Theoretical Maximum Output
        Theoretical Maximum = Run Time (hours) x Ideal Cycle Rate

        Args:
            actual_output: Actual units produced
            run_time_minutes: Run time in minutes
            ideal_cycle_rate_per_hour: Maximum units per hour at ideal rate

        Returns:
            Tuple of (performance ratio 0-1, theoretical_max_output)
        """
        if run_time_minutes <= 0 or ideal_cycle_rate_per_hour <= 0:
            return Decimal("0"), 0

        run_time_hours = Decimal(run_time_minutes) / Decimal(60)
        theoretical_max = int(run_time_hours * ideal_cycle_rate_per_hour)

        if theoretical_max == 0:
            return Decimal("0"), 0

        performance = self._safe_divide(
            Decimal(actual_output),
            Decimal(theoretical_max)
        )

        # Cap at 1.0 (100%) - can exceed if output higher than theoretical
        performance = min(Decimal("1"), performance)

        return performance, theoretical_max

    def calculate_quality(
        self,
        good_units: int,
        total_units: int
    ) -> Decimal:
        """
        Calculate quality component of OEE.

        Quality = Good Units / Total Units Produced

        Args:
            good_units: Number of good (non-defective) units
            total_units: Total units produced

        Returns:
            Quality ratio 0-1
        """
        if total_units <= 0:
            return Decimal("0")

        quality = self._safe_divide(
            Decimal(good_units),
            Decimal(total_units)
        )

        # Cap at 1.0 (100%)
        quality = min(Decimal("1"), quality)

        return quality

    def calculate_oee(
        self,
        data: CleanedProductionData,
        planned_production_time_minutes: Optional[int] = None,
        ideal_cycle_rate: Optional[int] = None
    ) -> OEEMetrics:
        """
        Calculate complete OEE metrics for a cleaned production data record.

        OEE = Availability x Performance x Quality

        Args:
            data: Cleaned production data
            planned_production_time_minutes: Override for planned time.
                Defaults to DEFAULT_SHIFT_HOURS * 60.
            ideal_cycle_rate: Override for ideal cycle rate per hour.
                Defaults to DEFAULT_IDEAL_CYCLE_RATE.

        Returns:
            OEEMetrics with all components calculated
        """
        # Set defaults
        if planned_production_time_minutes is None:
            planned_production_time_minutes = DEFAULT_SHIFT_HOURS * 60  # 480 minutes

        if ideal_cycle_rate is None:
            ideal_cycle_rate = DEFAULT_IDEAL_CYCLE_RATE

        # Calculate components
        availability, run_time = self.calculate_availability(
            planned_production_time_minutes,
            data.total_downtime_minutes
        )

        performance, theoretical_max = self.calculate_performance(
            data.units_produced,
            run_time,
            ideal_cycle_rate
        )

        quality = self.calculate_quality(
            data.good_units,
            data.total_units
        )

        # Calculate overall OEE
        oee_overall = availability * performance * quality

        # Round to 4 decimal places
        def round_decimal(d: Decimal) -> Decimal:
            return d.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        metrics = OEEMetrics(
            availability=round_decimal(availability),
            performance=round_decimal(performance),
            quality=round_decimal(quality),
            oee_overall=round_decimal(oee_overall),
            run_time_minutes=run_time,
            planned_production_time_minutes=planned_production_time_minutes,
            actual_output=data.units_produced,
            theoretical_max_output=theoretical_max,
            good_units=data.good_units,
            total_units=data.total_units,
        )

        return metrics

    def calculate_financial_impact(
        self,
        data: CleanedProductionData,
        hourly_rate: Optional[Decimal] = None,
        unit_cost: Optional[Decimal] = None
    ) -> FinancialMetrics:
        """
        Calculate financial impact for a cleaned production data record.

        Downtime Cost = Downtime Minutes x (Hourly Rate / 60)
        Waste Cost = Scrap Units x Unit Cost
        Total Loss = Downtime Cost + Waste Cost

        Uses cost_centers table for rates with fallback to configurable defaults (AC #8).

        Args:
            data: Cleaned production data
            hourly_rate: Override for hourly rate. If None, loaded from cost center.
            unit_cost: Override for unit cost. If None, loaded from cost center.

        Returns:
            FinancialMetrics with cost breakdown
        """
        # Get hourly rate from cost center if not provided (AC #2)
        if hourly_rate is None:
            hourly_rate, _ = self.get_hourly_rate(data.asset_id)

        # Get cost per unit from cost center if not provided (AC #3)
        if unit_cost is None:
            unit_cost, _ = self.get_cost_per_unit(data.asset_id)

        # Calculate downtime cost (AC #2)
        # Formula: financial_loss = (downtime_minutes / 60) * standard_hourly_rate
        downtime_cost = (Decimal(data.total_downtime_minutes) / Decimal(60)) * hourly_rate

        # Calculate waste cost (AC #3)
        # Formula: waste_loss = waste_count * cost_per_unit
        waste_cost = Decimal(data.units_scrapped) * unit_cost

        # Total loss (AC #4)
        total_loss = downtime_cost + waste_cost

        # Round to 2 decimal places for currency
        def round_currency(d: Decimal) -> Decimal:
            return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        metrics = FinancialMetrics(
            downtime_cost_dollars=round_currency(downtime_cost),
            waste_cost_dollars=round_currency(waste_cost),
            total_financial_loss_dollars=round_currency(total_loss),
            downtime_minutes=data.total_downtime_minutes,
            hourly_rate=hourly_rate,
            scrap_units=data.units_scrapped,
            unit_cost=unit_cost,
        )

        return metrics

    def calculate_all(
        self,
        cleaned_data: List[CleanedProductionData]
    ) -> List[Tuple[CleanedProductionData, OEEMetrics, FinancialMetrics]]:
        """
        Calculate OEE and financial metrics for all cleaned data records.

        Args:
            cleaned_data: List of cleaned production data

        Returns:
            List of tuples containing (data, oee_metrics, financial_metrics)
        """
        # Load cost centers for financial calculations
        self.load_cost_centers()

        results = []
        for data in cleaned_data:
            try:
                oee = self.calculate_oee(data)
                financial = self.calculate_financial_impact(data)
                results.append((data, oee, financial))
            except Exception as e:
                logger.error(f"Calculation failed for asset {data.asset_id}: {e}")
                # Create zero metrics for failed calculations
                oee = OEEMetrics()
                financial = FinancialMetrics()
                results.append((data, oee, financial))

        logger.info(f"Calculated metrics for {len(results)} assets")
        return results


# Module-level singleton
calculator = Calculator()
