"""
Voice Number Formatting Utilities (Story 8.6)

Provides natural language formatting for numbers in voice briefings.
All metrics pass through these formatters before TTS synthesis.

AC#1: Large numbers -> "about X.X million"
AC#2: Percentages -> rounded to integer
AC#3: Currency -> "about X thousand dollars"
AC#4: Durations -> largest sensible unit
AC#5: Small values -> exact

References:
- [Source: epic-8.md#Story-8.6]
- [Source: architecture/voice-briefing.md#BriefingService-Architecture]
"""

from typing import Any, Optional, Union
import math

# Threshold constants
BILLION_THRESHOLD = 1_000_000_000
MILLION_THRESHOLD = 1_000_000
THOUSAND_THRESHOLD = 1_000
SMALL_VALUE_THRESHOLD = 100

# Duration constants (in minutes)
MINUTES_PER_HOUR = 60
MINUTES_PER_DAY = 1440  # 24 * 60


def format_number_for_voice(value: Union[int, float], unit: str = "") -> str:
    """
    Format a numeric value for natural speech.

    AC#1: Large Numbers (Millions)
    AC#5: Small Precise Values

    Args:
        value: The numeric value to format
        unit: Optional unit string (e.g., "units", "items")

    Returns:
        A natural language string suitable for voice delivery

    Examples:
        >>> format_number_for_voice(2130500, "units")
        'about 2.1 million units'
        >>> format_number_for_voice(5, "units")
        '5 units'
        >>> format_number_for_voice(45230, "")
        'about 45 thousand'
    """
    # Handle None
    if value is None:
        return "unknown" + (f" {unit}" if unit else "")

    # Handle zero - no "about" prefix
    if value == 0:
        return _append_unit("0", unit)

    # Handle negative values - format absolute value and prepend "negative"
    if value < 0:
        formatted = format_number_for_voice(abs(value), "")
        # Remove "about" for negative values to keep it cleaner
        if formatted.startswith("about "):
            formatted = formatted[6:]
        result = f"negative {formatted}"
        return _append_unit(result, unit)

    # Small values (< 100): use exact value
    if value < SMALL_VALUE_THRESHOLD:
        # Keep precision for fractional values
        if isinstance(value, float) and value != int(value):
            formatted = f"{value:g}"  # Remove trailing zeros
        else:
            formatted = str(int(value))
        return _append_unit(formatted, unit)

    # Medium values (100-999): use exact value
    if value < THOUSAND_THRESHOLD:
        return _append_unit(str(int(round(value))), unit)

    # Billions
    if value >= BILLION_THRESHOLD:
        billions = value / BILLION_THRESHOLD
        # Round to one decimal place
        rounded = round(billions, 1)
        # Check if we can use a whole number
        if rounded == int(rounded):
            formatted = f"about {int(rounded)} billion"
        else:
            formatted = f"about {rounded} billion"
        return _append_unit(formatted, unit)

    # Millions
    if value >= MILLION_THRESHOLD:
        millions = value / MILLION_THRESHOLD
        # Round to one decimal place
        rounded = round(millions, 1)
        # Check if we can use a whole number
        if rounded == int(rounded):
            formatted = f"about {int(rounded)} million"
        else:
            formatted = f"about {rounded} million"
        return _append_unit(formatted, unit)

    # Thousands (1,000 - 999,999)
    thousands = value / THOUSAND_THRESHOLD
    # For >= 10,000, round to nearest thousand
    if value >= 10_000:
        rounded = round(thousands)
        formatted = f"about {int(rounded)} thousand"
    else:
        # For 1,000 - 9,999, use one decimal place
        rounded = round(thousands, 1)
        if rounded == int(rounded):
            formatted = f"about {int(rounded)} thousand"
        else:
            formatted = f"about {rounded} thousand"

    return _append_unit(formatted, unit)


def _append_unit(formatted: str, unit: str) -> str:
    """Append unit to formatted string if provided."""
    if unit:
        return f"{formatted} {unit}"
    return formatted


def format_percentage_for_voice(value: Union[int, float]) -> str:
    """
    Format percentage, rounding to nearest integer.

    AC#2: Percentage Formatting
    - No "about" prefix
    - Always round to nearest integer

    Args:
        value: The percentage value (e.g., 87.3 for 87.3%)

    Returns:
        A natural language string like "87 percent"

    Examples:
        >>> format_percentage_for_voice(87.3)
        '87 percent'
        >>> format_percentage_for_voice(99.9)
        '100 percent'
        >>> format_percentage_for_voice(0.4)
        '0 percent'
    """
    if value is None:
        return "unknown percent"

    # Round to nearest integer
    rounded = int(round(value))

    # Handle negative percentages
    if rounded < 0:
        return f"negative {abs(rounded)} percent"

    return f"{rounded} percent"


def format_currency_for_voice(value: Union[int, float]) -> str:
    """
    Format dollar amount for speech.

    AC#3: Currency Formatting
    - Round to nearest thousand for thousands
    - Round to one decimal for millions/billions
    - Use "about" prefix when rounding

    Args:
        value: The dollar amount (e.g., 45230 for $45,230)

    Returns:
        A natural language string like "about 45 thousand dollars"

    Examples:
        >>> format_currency_for_voice(45230)
        'about 45 thousand dollars'
        >>> format_currency_for_voice(1234567)
        'about 1.2 million dollars'
        >>> format_currency_for_voice(50)
        '50 dollars'
    """
    if value is None:
        return "unknown dollars"

    # Handle zero
    if value == 0:
        return "0 dollars"

    # Handle negative values
    if value < 0:
        formatted = format_currency_for_voice(abs(value))
        # Insert "negative" after "about" if present
        if formatted.startswith("about "):
            return f"about negative {formatted[6:]}"
        return f"negative {formatted}"

    # Small values (< 1000): use exact dollars
    if value < THOUSAND_THRESHOLD:
        return f"{int(round(value))} dollars"

    # Billions
    if value >= BILLION_THRESHOLD:
        billions = value / BILLION_THRESHOLD
        rounded = round(billions, 1)
        if rounded == int(rounded):
            return f"about {int(rounded)} billion dollars"
        return f"about {rounded} billion dollars"

    # Millions
    if value >= MILLION_THRESHOLD:
        millions = value / MILLION_THRESHOLD
        rounded = round(millions, 1)
        if rounded == int(rounded):
            return f"about {int(rounded)} million dollars"
        return f"about {rounded} million dollars"

    # Thousands
    thousands = value / THOUSAND_THRESHOLD
    rounded = round(thousands)
    return f"about {int(rounded)} thousand dollars"


def format_duration_for_voice(minutes: Union[int, float]) -> str:
    """
    Convert duration to most natural unit (minutes/hours/days).

    AC#4: Duration Conversion
    - >= 1440 min (24h): prefer days when evenly divisible, else hours
    - >= 60 min: convert to hours
    - < 60 min: keep as minutes

    Args:
        minutes: Duration in minutes

    Returns:
        A natural language duration string

    Examples:
        >>> format_duration_for_voice(4320)  # 72 hours / 3 days
        '3 days'
        >>> format_duration_for_voice(60)
        '1 hour'
        >>> format_duration_for_voice(30)
        '30 minutes'
    """
    if minutes is None:
        return "unknown duration"

    # Handle zero
    if minutes == 0:
        return "0 minutes"

    # Handle negative - shouldn't happen for duration but handle gracefully
    if minutes < 0:
        formatted = format_duration_for_voice(abs(minutes))
        return f"negative {formatted}"

    # Convert to float for calculations
    minutes = float(minutes)

    # For values >= 24 hours, check if evenly divisible by days
    if minutes >= MINUTES_PER_DAY:
        days = minutes / MINUTES_PER_DAY
        # Check if evenly divisible (within small tolerance)
        if abs(days - round(days)) < 0.001:
            days_int = int(round(days))
            unit = "day" if days_int == 1 else "days"
            return f"{days_int} {unit}"
        # Otherwise use hours
        hours = minutes / MINUTES_PER_HOUR
        rounded_hours = int(round(hours))
        # Use "about" if rounding is significant
        if abs(hours - rounded_hours) > 0.1:
            return f"about {rounded_hours} hours"
        unit = "hour" if rounded_hours == 1 else "hours"
        return f"{rounded_hours} {unit}"

    # For values >= 60 minutes, use hours
    if minutes >= MINUTES_PER_HOUR:
        hours = minutes / MINUTES_PER_HOUR
        rounded_hours = int(round(hours))
        # Use "about" if rounding is significant (more than 6 minutes off)
        if abs(hours - rounded_hours) > 0.1:
            return f"about {rounded_hours} hours"
        unit = "hour" if rounded_hours == 1 else "hours"
        return f"{rounded_hours} {unit}"

    # Less than 60 minutes - keep as minutes
    rounded_minutes = int(round(minutes))
    unit = "minute" if rounded_minutes == 1 else "minutes"
    return f"{rounded_minutes} {unit}"


def format_for_voice(
    value: Any,
    value_type: str = "auto",
    unit: str = "",
) -> str:
    """
    Auto-detect and format any value for voice delivery.

    This is the main entry point for voice formatting that automatically
    selects the appropriate formatter based on value_type or auto-detection.

    Args:
        value: The value to format
        value_type: One of "auto", "number", "percentage", "currency", "duration"
        unit: Optional unit string (only used for "number" type)

    Returns:
        A natural language string suitable for voice delivery

    Examples:
        >>> format_for_voice(87.3, "percentage")
        '87 percent'
        >>> format_for_voice(45230, "currency")
        'about 45 thousand dollars'
        >>> format_for_voice(2130500, "number", "units")
        'about 2.1 million units'
    """
    # Handle None or non-numeric types
    if value is None:
        if value_type == "percentage":
            return "unknown percent"
        elif value_type == "currency":
            return "unknown dollars"
        elif value_type == "duration":
            return "unknown duration"
        return "unknown" + (f" {unit}" if unit else "")

    # Handle string values
    if isinstance(value, str):
        try:
            # Try to convert to number
            value = float(value)
        except (ValueError, TypeError):
            # Return string as-is
            return value

    # Select formatter based on type
    if value_type == "percentage":
        return format_percentage_for_voice(value)
    elif value_type == "currency":
        return format_currency_for_voice(value)
    elif value_type == "duration":
        return format_duration_for_voice(int(value))
    elif value_type == "number":
        return format_number_for_voice(value, unit)
    else:
        # Auto-detect (default to number formatting)
        return format_number_for_voice(value, unit)


def detect_and_format(
    value: Any,
    context_hint: Optional[str] = None,
) -> str:
    """
    Intelligent formatting based on value characteristics and optional context hint.

    Uses heuristics to determine the best formatting approach:
    - Values ending in '%' or context containing 'percent' -> percentage
    - Context containing 'dollar', 'cost', 'price', '$' -> currency
    - Context containing 'minute', 'hour', 'day', 'duration', 'time' -> duration
    - Otherwise -> general number formatting

    Args:
        value: The value to format
        context_hint: Optional string providing context (e.g., "87% OEE", "cost savings")

    Returns:
        Formatted string suitable for voice delivery

    Examples:
        >>> detect_and_format("87%")
        '87 percent'
        >>> detect_and_format(45230, "cost savings")
        'about 45 thousand dollars'
    """
    # Handle string values that include type indicators
    if isinstance(value, str):
        value_str = value.strip()

        # Check for percentage
        if value_str.endswith('%'):
            try:
                num_value = float(value_str[:-1])
                return format_percentage_for_voice(num_value)
            except (ValueError, TypeError):
                pass

        # Check for currency prefix
        if value_str.startswith('$'):
            try:
                # Remove $ and any commas
                num_str = value_str[1:].replace(',', '')
                num_value = float(num_str)
                return format_currency_for_voice(num_value)
            except (ValueError, TypeError):
                pass

        # Try to convert to number
        try:
            value = float(value_str.replace(',', ''))
        except (ValueError, TypeError):
            return value_str

    # Use context hint for type detection
    if context_hint:
        hint_lower = context_hint.lower()

        # Check for percentage context
        if any(word in hint_lower for word in ['percent', '%', 'oee', 'rate', 'ratio']):
            return format_percentage_for_voice(value)

        # Check for currency context
        if any(word in hint_lower for word in ['dollar', 'cost', 'price', '$', 'revenue', 'savings', 'loss']):
            return format_currency_for_voice(value)

        # Check for duration context
        if any(word in hint_lower for word in ['minute', 'hour', 'day', 'duration', 'time', 'downtime']):
            return format_duration_for_voice(int(value))

    # Default to number formatting
    return format_number_for_voice(value)
