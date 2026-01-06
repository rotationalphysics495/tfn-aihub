"""
OEE (Overall Equipment Effectiveness) Calculator Service

Provides calculation logic for OEE metrics from daily_summaries and live_snapshots data.

Story: 2.4 - OEE Metrics View
AC: #2 - OEE metrics computed from daily_summaries (T-1) and live_snapshots (T-15m)
AC: #10 - Proper error handling and data validation
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


# OEE Status thresholds per story requirements
OEE_GREEN_THRESHOLD = 85.0   # >= 85%
OEE_YELLOW_THRESHOLD = 70.0  # >= 70% and < 85%
# Red: < 70%


@dataclass
class OEEComponents:
    """Container for OEE component calculations."""

    availability: Optional[float]
    performance: Optional[float]
    quality: Optional[float]
    overall: Optional[float]
    status: str

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "availability": self.availability,
            "performance": self.performance,
            "quality": self.quality,
            "overall": self.overall,
            "status": self.status,
        }


@dataclass
class AssetOEE:
    """OEE data for a single asset."""

    asset_id: str
    name: str
    area: Optional[str]
    oee: Optional[float]
    availability: Optional[float]
    performance: Optional[float]
    quality: Optional[float]
    target: Optional[float]
    status: str

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "asset_id": self.asset_id,
            "name": self.name,
            "area": self.area,
            "oee": self.oee,
            "availability": self.availability,
            "performance": self.performance,
            "quality": self.quality,
            "target": self.target,
            "status": self.status,
        }


def get_oee_status(oee_value: Optional[float]) -> str:
    """
    Determine OEE status based on threshold values.

    Per AC #8:
    - Green: >= 85%
    - Yellow: 70-84%
    - Red: < 70%

    Args:
        oee_value: OEE percentage value or None

    Returns:
        Status string: "green", "yellow", "red", or "unknown"
    """
    if oee_value is None:
        return "unknown"

    if oee_value >= OEE_GREEN_THRESHOLD:
        return "green"
    elif oee_value >= OEE_YELLOW_THRESHOLD:
        return "yellow"
    else:
        return "red"


def calculate_availability(
    run_time_minutes: Optional[int],
    planned_time_minutes: Optional[int],
) -> Optional[float]:
    """
    Calculate Availability component of OEE.

    Formula: (Run Time / Planned Production Time) x 100

    Args:
        run_time_minutes: Actual machine run time in minutes
        planned_time_minutes: Planned production time in minutes

    Returns:
        Availability percentage (0-100) or None if data is invalid
    """
    if run_time_minutes is None or planned_time_minutes is None:
        return None

    if planned_time_minutes <= 0:
        logger.warning("Planned time is zero or negative, cannot calculate availability")
        return None

    availability = (run_time_minutes / planned_time_minutes) * 100

    # Cap at 100% (run time shouldn't exceed planned time, but handle data issues)
    return min(round(availability, 1), 100.0)


def calculate_performance(
    actual_output: Optional[int],
    target_output: Optional[int],
) -> Optional[float]:
    """
    Calculate Performance component of OEE.

    Formula: (Actual Output / Target Output) x 100

    Note: Original formula is (Total Units / Run Time) / Ideal Rate
    We simplify using target_output which represents the expected output
    for the planned time at ideal rate.

    Args:
        actual_output: Actual units produced
        target_output: Target/ideal units expected

    Returns:
        Performance percentage (0-100+) or None if data is invalid
    """
    if actual_output is None or target_output is None:
        return None

    if target_output <= 0:
        logger.warning("Target output is zero or negative, cannot calculate performance")
        return None

    performance = (actual_output / target_output) * 100

    # Don't cap at 100% - performance can exceed target
    return round(performance, 1)


def calculate_quality(
    good_output: Optional[int],
    total_output: Optional[int],
) -> Optional[float]:
    """
    Calculate Quality component of OEE.

    Formula: (Good Units / Total Units) x 100

    Args:
        good_output: Number of good units produced
        total_output: Total units produced (good + waste)

    Returns:
        Quality percentage (0-100) or None if data is invalid
    """
    if good_output is None or total_output is None:
        return None

    if total_output <= 0:
        logger.warning("Total output is zero or negative, cannot calculate quality")
        return None

    quality = (good_output / total_output) * 100

    # Cap at 100% (good units shouldn't exceed total)
    return min(round(quality, 1), 100.0)


def calculate_overall_oee(
    availability: Optional[float],
    performance: Optional[float],
    quality: Optional[float],
) -> Optional[float]:
    """
    Calculate Overall OEE from its components.

    Formula: (Availability x Performance x Quality) / 10000
    (Dividing by 10000 because each component is already a percentage)

    Args:
        availability: Availability percentage
        performance: Performance percentage
        quality: Quality percentage

    Returns:
        Overall OEE percentage or None if any component is missing
    """
    if availability is None or performance is None or quality is None:
        return None

    # Formula: A * P * Q / 10000 (since each is already a percentage)
    oee = (availability * performance * quality) / 10000

    return round(oee, 1)


def calculate_oee_from_daily_summary(
    daily_summary: dict,
    shift_target: Optional[dict] = None,
) -> OEEComponents:
    """
    Calculate OEE components from a daily_summary record.

    Uses data from the daily_summaries table which contains:
    - actual_output: Total units produced
    - target_output: Expected units
    - waste_count: Rejected/waste units
    - downtime_minutes: Downtime during the period

    Args:
        daily_summary: Record from daily_summaries table
        shift_target: Optional record from shift_targets for ideal values

    Returns:
        OEEComponents with all calculated values
    """
    # Extract values with safe defaults
    actual_output = daily_summary.get("actual_output")
    target_output = daily_summary.get("target_output")
    waste_count = daily_summary.get("waste_count", 0) or 0
    downtime_minutes = daily_summary.get("downtime_minutes", 0) or 0

    # Calculate good output (total - waste)
    good_output = None
    if actual_output is not None:
        good_output = actual_output - waste_count

    # For availability, we need run time and planned time
    # Assume standard 8-hour shift (480 minutes) if not specified
    planned_time_minutes = 480  # Default 8-hour shift
    if shift_target and shift_target.get("planned_time"):
        planned_time_minutes = shift_target["planned_time"]

    # Run time = Planned time - Downtime
    run_time_minutes = planned_time_minutes - downtime_minutes

    # Calculate components
    availability = calculate_availability(run_time_minutes, planned_time_minutes)
    performance = calculate_performance(actual_output, target_output)
    quality = calculate_quality(good_output, actual_output)

    # Calculate overall OEE
    overall = calculate_overall_oee(availability, performance, quality)

    # Determine status
    status = get_oee_status(overall)

    return OEEComponents(
        availability=availability,
        performance=performance,
        quality=quality,
        overall=overall,
        status=status,
    )


def calculate_oee_from_live_snapshot(
    live_snapshot: dict,
    shift_target: Optional[dict] = None,
) -> OEEComponents:
    """
    Calculate OEE components from a live_snapshot record.

    Live snapshots have limited data compared to daily summaries:
    - current_output: Current units produced
    - target_output: Expected units at this point

    We estimate OEE based on available data.

    Args:
        live_snapshot: Record from live_snapshots table
        shift_target: Optional record from shift_targets

    Returns:
        OEEComponents with calculated values (some may be None)
    """
    current_output = live_snapshot.get("current_output")
    target_output = live_snapshot.get("target_output")

    # Calculate performance (only metric we can reliably compute from live data)
    performance = calculate_performance(current_output, target_output)

    # For live snapshots, we don't have availability/quality data
    # We can estimate overall based on performance alone with assumed values
    # Or return None for unavailable components

    # Use assumed availability and quality for live OEE estimation
    # This gives a rough estimate based on current throughput
    assumed_availability = 95.0  # Assume high availability unless we know otherwise
    assumed_quality = 98.0  # Assume high quality unless we know otherwise

    # Calculate estimated overall OEE using performance and assumed values
    if performance is not None:
        estimated_overall = calculate_overall_oee(
            assumed_availability, performance, assumed_quality
        )
    else:
        estimated_overall = None

    # Determine status
    status = get_oee_status(estimated_overall)

    return OEEComponents(
        availability=assumed_availability if performance is not None else None,
        performance=performance,
        quality=assumed_quality if performance is not None else None,
        overall=estimated_overall,
        status=status,
    )


def calculate_plant_wide_oee(
    asset_oee_list: List[AssetOEE],
) -> OEEComponents:
    """
    Calculate plant-wide OEE by averaging individual asset OEE values.

    Args:
        asset_oee_list: List of AssetOEE objects with individual metrics

    Returns:
        OEEComponents representing plant-wide averages
    """
    if not asset_oee_list:
        return OEEComponents(
            availability=None,
            performance=None,
            quality=None,
            overall=None,
            status="unknown",
        )

    # Collect non-None values for each component
    availability_values = [a.availability for a in asset_oee_list if a.availability is not None]
    performance_values = [a.performance for a in asset_oee_list if a.performance is not None]
    quality_values = [a.quality for a in asset_oee_list if a.quality is not None]
    overall_values = [a.oee for a in asset_oee_list if a.oee is not None]

    # Calculate averages
    avg_availability = round(sum(availability_values) / len(availability_values), 1) if availability_values else None
    avg_performance = round(sum(performance_values) / len(performance_values), 1) if performance_values else None
    avg_quality = round(sum(quality_values) / len(quality_values), 1) if quality_values else None
    avg_overall = round(sum(overall_values) / len(overall_values), 1) if overall_values else None

    # Determine status
    status = get_oee_status(avg_overall)

    return OEEComponents(
        availability=avg_availability,
        performance=avg_performance,
        quality=avg_quality,
        overall=avg_overall,
        status=status,
    )


def get_default_oee_target() -> float:
    """
    Get the default OEE target percentage.

    Returns:
        Default target of 85% (world-class OEE benchmark)
    """
    return 85.0
