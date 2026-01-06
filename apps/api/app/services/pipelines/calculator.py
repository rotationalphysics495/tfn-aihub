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
DEFAULT_UNIT_COST = Decimal("10.00")  # Default cost per unit for waste


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
                "id, asset_id, standard_hourly_rate"
            ).execute()

            self._cost_center_cache = {}
            for cc in response.data:
                asset_id = cc.get("asset_id")
                if asset_id:
                    self._cost_center_cache[UUID(asset_id)] = {
                        "id": UUID(cc.get("id")),
                        "hourly_rate": Decimal(str(cc.get("standard_hourly_rate", 0))),
                    }

            logger.info(f"Loaded {len(self._cost_center_cache)} cost centers")
            return self._cost_center_cache

        except Exception as e:
            logger.error(f"Failed to load cost centers: {e}")
            raise CalculationError(f"Failed to load cost centers: {e}") from e

    def get_hourly_rate(self, asset_id: UUID) -> Decimal:
        """
        Get the hourly rate for an asset from its cost center.

        Args:
            asset_id: UUID of the asset

        Returns:
            Hourly rate as Decimal, or 0 if not found
        """
        if not self._cost_center_cache:
            self.load_cost_centers()

        cost_center = self._cost_center_cache.get(asset_id, {})
        return cost_center.get("hourly_rate", Decimal("0"))

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

        Args:
            data: Cleaned production data
            hourly_rate: Override for hourly rate. If None, loaded from cost center.
            unit_cost: Override for unit cost. Defaults to DEFAULT_UNIT_COST.

        Returns:
            FinancialMetrics with cost breakdown
        """
        # Get hourly rate from cost center if not provided
        if hourly_rate is None:
            hourly_rate = self.get_hourly_rate(data.asset_id)

        if unit_cost is None:
            unit_cost = DEFAULT_UNIT_COST

        # Calculate downtime cost
        # Cost = (minutes / 60) * hourly_rate
        downtime_cost = (Decimal(data.total_downtime_minutes) / Decimal(60)) * hourly_rate

        # Calculate waste cost
        waste_cost = Decimal(data.units_scrapped) * unit_cost

        # Total loss
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
