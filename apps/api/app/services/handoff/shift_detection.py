"""
Shift Detection Utilities (Story 9.1, Task 6)

Utilities for detecting the current shift and calculating shift time ranges.

AC#1: Auto-detect shift time range (last 8 hours)

Shift Windows:
- Morning: 6:00 AM - 2:00 PM
- Afternoon: 2:00 PM - 10:00 PM
- Night: 10:00 PM - 6:00 AM

References:
- [Source: architecture/voice-briefing.md#Shift-Handoff-Workflow]
"""

from datetime import datetime, date, time, timedelta, timezone
from typing import Optional, Tuple

from app.models.handoff import ShiftType, ShiftTimeRange


# Shift window definitions (hour of day in 24-hour format)
# Each tuple is (start_hour, end_hour)
SHIFT_WINDOWS = {
    ShiftType.MORNING: (6, 14),      # 6:00 AM - 2:00 PM
    ShiftType.AFTERNOON: (14, 22),   # 2:00 PM - 10:00 PM
    ShiftType.NIGHT: (22, 6),        # 10:00 PM - 6:00 AM (crosses midnight)
}


def detect_current_shift(current_time: Optional[datetime] = None) -> ShiftType:
    """
    Detect the current shift type based on the time of day.

    Args:
        current_time: The time to check (defaults to current UTC time)

    Returns:
        ShiftType: The detected shift type

    Examples:
        >>> detect_current_shift(datetime(2024, 1, 15, 8, 0))  # 8:00 AM
        ShiftType.MORNING
        >>> detect_current_shift(datetime(2024, 1, 15, 16, 0))  # 4:00 PM
        ShiftType.AFTERNOON
        >>> detect_current_shift(datetime(2024, 1, 15, 23, 0))  # 11:00 PM
        ShiftType.NIGHT
    """
    if current_time is None:
        current_time = datetime.now(timezone.utc)

    hour = current_time.hour

    # Morning shift: 6:00 AM - 2:00 PM (6 <= hour < 14)
    if 6 <= hour < 14:
        return ShiftType.MORNING

    # Afternoon shift: 2:00 PM - 10:00 PM (14 <= hour < 22)
    if 14 <= hour < 22:
        return ShiftType.AFTERNOON

    # Night shift: 10:00 PM - 6:00 AM (hour >= 22 or hour < 6)
    return ShiftType.NIGHT


def get_shift_time_range(
    current_time: Optional[datetime] = None,
    shift_type: Optional[ShiftType] = None
) -> ShiftTimeRange:
    """
    Calculate the shift time range for handoff data collection.

    This determines the time window for which shift data should be collected.
    The range is the last 8 hours from the current time, aligned to shift boundaries.

    Args:
        current_time: The reference time (defaults to current UTC time)
        shift_type: Optional shift type override (auto-detected if not provided)

    Returns:
        ShiftTimeRange: The calculated shift time range

    Examples:
        >>> # At 2:30 PM, this would return the morning shift range
        >>> get_shift_time_range(datetime(2024, 1, 15, 14, 30))
        ShiftTimeRange(
            shift_type=ShiftType.MORNING,
            start_time=datetime(2024, 1, 15, 6, 0),
            end_time=datetime(2024, 1, 15, 14, 0),
            shift_date=date(2024, 1, 15)
        )
    """
    if current_time is None:
        current_time = datetime.now(timezone.utc)

    if shift_type is None:
        shift_type = detect_current_shift(current_time)

    # Get the shift window boundaries
    start_hour, end_hour = SHIFT_WINDOWS[shift_type]

    # Calculate the shift date
    # For night shifts that start before midnight, the shift date is the previous day
    # For night shifts after midnight, the shift date is the current day
    current_date = current_time.date()
    current_hour = current_time.hour

    if shift_type == ShiftType.NIGHT:
        # Night shift handling (crosses midnight)
        if current_hour >= 22:
            # We're in the first part of the night shift (before midnight)
            shift_date = current_date
            start_time = datetime.combine(
                current_date,
                time(start_hour, 0),
                tzinfo=timezone.utc
            )
            end_time = datetime.combine(
                current_date + timedelta(days=1),
                time(end_hour, 0),
                tzinfo=timezone.utc
            )
        else:
            # We're in the second part of the night shift (after midnight)
            shift_date = current_date - timedelta(days=1)
            start_time = datetime.combine(
                current_date - timedelta(days=1),
                time(start_hour, 0),
                tzinfo=timezone.utc
            )
            end_time = datetime.combine(
                current_date,
                time(end_hour, 0),
                tzinfo=timezone.utc
            )
    else:
        # Morning or Afternoon shift (same day)
        shift_date = current_date
        start_time = datetime.combine(
            current_date,
            time(start_hour, 0),
            tzinfo=timezone.utc
        )
        end_time = datetime.combine(
            current_date,
            time(end_hour, 0),
            tzinfo=timezone.utc
        )

    return ShiftTimeRange(
        shift_type=shift_type,
        start_time=start_time,
        end_time=end_time,
        shift_date=shift_date,
    )


def get_shift_for_handoff(current_time: Optional[datetime] = None) -> Tuple[ShiftType, date]:
    """
    Get the shift type and date for creating a new handoff.

    When a supervisor creates a handoff, they're handing off the shift they just
    completed. This function returns the just-completed shift information.

    Args:
        current_time: The reference time (defaults to current UTC time)

    Returns:
        Tuple of (ShiftType, date): The shift type and date for the handoff

    Note:
        At shift boundaries (e.g., exactly 2:00 PM), this returns the ending shift.
    """
    if current_time is None:
        current_time = datetime.now(timezone.utc)

    shift_range = get_shift_time_range(current_time)
    return shift_range.shift_type, shift_range.shift_date
