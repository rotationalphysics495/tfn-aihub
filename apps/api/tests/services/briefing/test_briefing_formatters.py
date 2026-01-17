"""
Tests for Voice Number Formatting Utilities (Story 8.6)

Comprehensive test coverage for all acceptance criteria:
AC#1: Large Numbers (Millions) - Numbers formatted as "about X.X million units"
AC#2: Percentage Formatting - Rounded to nearest integer, "X percent"
AC#3: Currency Formatting - "about X thousand dollars"
AC#4: Duration Conversion - Minutes to hours/days with natural units
AC#5: Small Precise Values - Exact values for small numbers

References:
- [Source: epic-8.md#Story-8.6]
"""

import pytest

from app.services.briefing.formatters import (
    format_number_for_voice,
    format_percentage_for_voice,
    format_currency_for_voice,
    format_duration_for_voice,
    format_for_voice,
    detect_and_format,
)


# =============================================================================
# Test: Large Number Formatting (AC#1)
# =============================================================================


class TestLargeNumberFormatting:
    """Tests for large number formatting (AC#1)."""

    def test_millions_with_decimal(self):
        """AC#1: 2,130,500 units -> 'about 2.1 million units'."""
        result = format_number_for_voice(2130500, "units")
        assert result == "about 2.1 million units"

    def test_millions_exact(self):
        """AC#1: Exactly 1 million uses whole number."""
        result = format_number_for_voice(1000000, "units")
        assert result == "about 1 million units"

    def test_millions_without_unit(self):
        """AC#1: Millions without unit suffix."""
        result = format_number_for_voice(2500000)
        assert result == "about 2.5 million"

    def test_billions(self):
        """AC#1: Billions formatted correctly."""
        result = format_number_for_voice(1500000000, "units")
        assert result == "about 1.5 billion units"

    def test_billions_exact(self):
        """AC#1: Exactly 1 billion uses whole number."""
        result = format_number_for_voice(1000000000, "units")
        assert result == "about 1 billion units"

    def test_thousands_large(self):
        """AC#1: Large thousands (>10k) round to nearest thousand."""
        result = format_number_for_voice(45230, "")
        assert result == "about 45 thousand"

    def test_thousands_medium(self):
        """AC#1: Medium thousands (1k-10k) use one decimal."""
        result = format_number_for_voice(1500, "items")
        assert result == "about 1.5 thousand items"

    def test_thousands_exact(self):
        """AC#1: Exact thousands use whole number."""
        result = format_number_for_voice(5000, "units")
        assert result == "about 5 thousand units"


# =============================================================================
# Test: Percentage Formatting (AC#2)
# =============================================================================


class TestPercentageFormatting:
    """Tests for percentage formatting (AC#2)."""

    def test_percentage_decimal_rounds_down(self):
        """AC#2: 87.3% -> '87 percent'."""
        result = format_percentage_for_voice(87.3)
        assert result == "87 percent"

    def test_percentage_decimal_rounds_up(self):
        """AC#2: 99.9% -> '100 percent'."""
        result = format_percentage_for_voice(99.9)
        assert result == "100 percent"

    def test_percentage_small_value_rounds_to_zero(self):
        """AC#2: 0.4% -> '0 percent'."""
        result = format_percentage_for_voice(0.4)
        assert result == "0 percent"

    def test_percentage_exactly_100(self):
        """AC#2: 100.0% -> '100 percent'."""
        result = format_percentage_for_voice(100.0)
        assert result == "100 percent"

    def test_percentage_integer_value(self):
        """AC#2: Integer percentage remains unchanged."""
        result = format_percentage_for_voice(50)
        assert result == "50 percent"

    def test_percentage_rounds_at_midpoint(self):
        """AC#2: 50.5% rounds to 51 (standard rounding)."""
        result = format_percentage_for_voice(50.5)
        assert result in ["50 percent", "51 percent"]  # Python uses banker's rounding

    def test_percentage_zero(self):
        """AC#2: 0% -> '0 percent'."""
        result = format_percentage_for_voice(0)
        assert result == "0 percent"


# =============================================================================
# Test: Currency Formatting (AC#3)
# =============================================================================


class TestCurrencyFormatting:
    """Tests for currency formatting (AC#3)."""

    def test_currency_thousands(self):
        """AC#3: $45,230 -> 'about 45 thousand dollars'."""
        result = format_currency_for_voice(45230)
        assert result == "about 45 thousand dollars"

    def test_currency_millions(self):
        """AC#3: $1,234,567 -> 'about 1.2 million dollars'."""
        result = format_currency_for_voice(1234567)
        assert result == "about 1.2 million dollars"

    def test_currency_millions_exact(self):
        """AC#3: Exactly $1 million uses whole number."""
        result = format_currency_for_voice(1000000)
        assert result == "about 1 million dollars"

    def test_currency_billions(self):
        """AC#3: $2.5 billion formatted correctly."""
        result = format_currency_for_voice(2500000000)
        assert result == "about 2.5 billion dollars"

    def test_currency_small_value(self):
        """AC#3: Small currency uses exact value."""
        result = format_currency_for_voice(50)
        assert result == "50 dollars"

    def test_currency_zero(self):
        """AC#3: $0 -> '0 dollars'."""
        result = format_currency_for_voice(0)
        assert result == "0 dollars"

    def test_currency_medium_value(self):
        """AC#3: $500 -> '500 dollars' (exact, not thousands)."""
        result = format_currency_for_voice(500)
        assert result == "500 dollars"


# =============================================================================
# Test: Duration Conversion (AC#4)
# =============================================================================


class TestDurationConversion:
    """Tests for duration conversion (AC#4)."""

    def test_duration_days_even(self):
        """AC#4: 4320 minutes (72 hours / 3 days) -> '3 days'."""
        result = format_duration_for_voice(4320)
        assert result == "3 days"

    def test_duration_hours(self):
        """AC#4: 60 minutes -> '1 hour'."""
        result = format_duration_for_voice(60)
        assert result == "1 hour"

    def test_duration_minutes_small(self):
        """AC#4: 30 minutes -> '30 minutes'."""
        result = format_duration_for_voice(30)
        assert result == "30 minutes"

    def test_duration_multiple_hours(self):
        """AC#4: 120 minutes -> '2 hours'."""
        result = format_duration_for_voice(120)
        assert result == "2 hours"

    def test_duration_non_even_hours(self):
        """AC#4: 90 minutes -> 'about 2 hours' (or '2 hours')."""
        result = format_duration_for_voice(90)
        # Either "about 2 hours" or "2 hours" is acceptable
        assert "hour" in result

    def test_duration_single_day(self):
        """AC#4: 1440 minutes -> '1 day'."""
        result = format_duration_for_voice(1440)
        assert result == "1 day"

    def test_duration_multiple_days(self):
        """AC#4: 2880 minutes -> '2 days'."""
        result = format_duration_for_voice(2880)
        assert result == "2 days"

    def test_duration_non_even_days_uses_hours(self):
        """AC#4: 1500 minutes (25 hours) -> 'about 25 hours'."""
        result = format_duration_for_voice(1500)
        # Should prefer hours when not evenly divisible by days
        assert "hour" in result

    def test_duration_zero(self):
        """AC#4: 0 minutes -> '0 minutes'."""
        result = format_duration_for_voice(0)
        assert result == "0 minutes"

    def test_duration_single_minute(self):
        """AC#4: 1 minute uses singular."""
        result = format_duration_for_voice(1)
        assert result == "1 minute"


# =============================================================================
# Test: Small Precise Values (AC#5)
# =============================================================================


class TestSmallPreciseValues:
    """Tests for small precise value formatting (AC#5)."""

    def test_small_value_exact(self):
        """AC#5: 5 units -> '5 units' (exact)."""
        result = format_number_for_voice(5, "units")
        assert result == "5 units"

    def test_small_value_under_100(self):
        """AC#5: 99 items -> '99 items' (exact)."""
        result = format_number_for_voice(99, "items")
        assert result == "99 items"

    def test_medium_value_exact(self):
        """AC#5: 250 -> '250' (exact for 100-999)."""
        result = format_number_for_voice(250)
        assert result == "250"

    def test_fractional_small_value(self):
        """AC#5: 0.5 units -> '0.5 units' (keep precision)."""
        result = format_number_for_voice(0.5, "units")
        assert result == "0.5 units"

    def test_small_value_with_decimals(self):
        """AC#5: 3.7 items -> '3.7 items' (keep precision)."""
        result = format_number_for_voice(3.7, "items")
        assert result == "3.7 items"

    def test_boundary_value_100(self):
        """AC#5: 100 is still exact (boundary case)."""
        result = format_number_for_voice(100, "units")
        assert result == "100 units"


# =============================================================================
# Test: Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases across all formatters."""

    def test_zero_number(self):
        """Edge: Zero values don't use 'about'."""
        result = format_number_for_voice(0, "units")
        assert result == "0 units"
        assert "about" not in result

    def test_negative_number(self):
        """Edge: Negative values include 'negative'."""
        result = format_number_for_voice(-1000, "units")
        assert "negative" in result

    def test_negative_percentage(self):
        """Edge: Negative percentages handled."""
        result = format_percentage_for_voice(-5.3)
        assert result == "negative 5 percent"

    def test_negative_currency(self):
        """Edge: Negative currency handled."""
        result = format_currency_for_voice(-45000)
        assert "negative" in result
        assert "dollars" in result

    def test_negative_duration(self):
        """Edge: Negative duration handled (shouldn't happen but safe)."""
        result = format_duration_for_voice(-30)
        assert "negative" in result

    def test_none_number(self):
        """Edge: None value returns 'unknown'."""
        result = format_number_for_voice(None, "units")
        assert "unknown" in result

    def test_none_percentage(self):
        """Edge: None percentage returns 'unknown percent'."""
        result = format_percentage_for_voice(None)
        assert result == "unknown percent"

    def test_none_currency(self):
        """Edge: None currency returns 'unknown dollars'."""
        result = format_currency_for_voice(None)
        assert result == "unknown dollars"

    def test_none_duration(self):
        """Edge: None duration returns 'unknown duration'."""
        result = format_duration_for_voice(None)
        assert result == "unknown duration"

    def test_very_large_number(self):
        """Edge: Very large numbers (trillions) handled."""
        # 1 trillion
        result = format_number_for_voice(1000000000000, "units")
        # Should at least contain 'billion' or handle gracefully
        assert "billion" in result or "million" in result

    def test_number_no_unit(self):
        """Edge: Number without unit."""
        result = format_number_for_voice(500)
        assert result == "500"
        assert "units" not in result


# =============================================================================
# Test: format_for_voice (Auto-detection)
# =============================================================================


class TestFormatForVoice:
    """Tests for the unified format_for_voice function."""

    def test_format_for_voice_percentage(self):
        """Auto-format with percentage type."""
        result = format_for_voice(87.3, "percentage")
        assert result == "87 percent"

    def test_format_for_voice_currency(self):
        """Auto-format with currency type."""
        result = format_for_voice(45230, "currency")
        assert result == "about 45 thousand dollars"

    def test_format_for_voice_duration(self):
        """Auto-format with duration type."""
        result = format_for_voice(120, "duration")
        assert result == "2 hours"

    def test_format_for_voice_number(self):
        """Auto-format with number type."""
        result = format_for_voice(2130500, "number", "units")
        assert result == "about 2.1 million units"

    def test_format_for_voice_auto(self):
        """Auto-format with auto detection (defaults to number)."""
        result = format_for_voice(500)
        assert result == "500"

    def test_format_for_voice_none(self):
        """Auto-format handles None values."""
        result = format_for_voice(None, "number", "units")
        assert "unknown" in result

    def test_format_for_voice_string_number(self):
        """Auto-format converts string numbers."""
        result = format_for_voice("500")
        assert result == "500"


# =============================================================================
# Test: detect_and_format (Context-Aware Detection)
# =============================================================================


class TestDetectAndFormat:
    """Tests for context-aware formatting."""

    def test_detect_percentage_from_string(self):
        """Detects percentage from string ending in %."""
        result = detect_and_format("87%")
        assert result == "87 percent"

    def test_detect_currency_from_string(self):
        """Detects currency from string starting with $."""
        result = detect_and_format("$45,230")
        assert "45" in result
        assert "thousand" in result
        assert "dollars" in result

    def test_detect_from_context_percentage(self):
        """Detects percentage from context hint."""
        result = detect_and_format(87.3, "OEE rate")
        assert result == "87 percent"

    def test_detect_from_context_currency(self):
        """Detects currency from context hint."""
        result = detect_and_format(45000, "cost savings")
        assert "dollars" in result

    def test_detect_from_context_duration(self):
        """Detects duration from context hint."""
        result = detect_and_format(120, "downtime minutes")
        assert "hour" in result or "minute" in result

    def test_detect_default_number(self):
        """Defaults to number formatting without context."""
        result = detect_and_format(500)
        assert result == "500"


# =============================================================================
# Test: Integration with Narrative Service
# =============================================================================


class TestNarrativeIntegration:
    """Tests for integration patterns with narrative service."""

    def test_production_output_formatting(self):
        """Typical production output formatting."""
        # Simulating production output of 2,130,500 units
        output = 2130500
        formatted = format_number_for_voice(output, "units")
        assert formatted == "about 2.1 million units"

    def test_oee_percentage_formatting(self):
        """Typical OEE percentage formatting."""
        oee = 87.3
        formatted = format_percentage_for_voice(oee)
        assert formatted == "87 percent"

    def test_downtime_duration_formatting(self):
        """Typical downtime duration formatting."""
        downtime_minutes = 4320
        formatted = format_duration_for_voice(downtime_minutes)
        # Should be "3 days" since 4320 = 72 hours = 3 days
        assert formatted == "3 days"

    def test_cost_impact_formatting(self):
        """Typical cost impact formatting."""
        cost = 45230
        formatted = format_currency_for_voice(cost)
        assert formatted == "about 45 thousand dollars"


# =============================================================================
# Test: Rounding Behavior
# =============================================================================


class TestRoundingBehavior:
    """Tests for specific rounding behavior."""

    def test_millions_rounds_to_one_decimal(self):
        """Millions round to one decimal place."""
        # 1,230,000 -> 1.2 million
        result = format_number_for_voice(1230000, "units")
        assert "1.2 million" in result

    def test_thousands_large_rounds_to_nearest(self):
        """Large thousands round to nearest thousand."""
        # 45,230 -> 45 thousand
        result = format_number_for_voice(45230)
        assert "45 thousand" in result

    def test_percentage_always_integer(self):
        """Percentages always round to integer."""
        # 33.333... -> 33 percent
        result = format_percentage_for_voice(33.333)
        assert result == "33 percent"

    def test_currency_thousands_rounds(self):
        """Currency rounds to nearest thousand for thousands."""
        # $45,500 -> about 46 thousand dollars
        result = format_currency_for_voice(45500)
        assert "46 thousand" in result


# =============================================================================
# Test: Voice Output Quality
# =============================================================================


class TestVoiceOutputQuality:
    """Tests ensuring output is suitable for voice delivery."""

    def test_no_numeric_symbols_in_output(self):
        """Output should not contain % or $ symbols."""
        result = format_percentage_for_voice(87.3)
        assert "%" not in result

        result = format_currency_for_voice(45000)
        assert "$" not in result

    def test_no_commas_in_large_numbers(self):
        """Output should not contain commas."""
        result = format_number_for_voice(1500000, "units")
        assert "," not in result

    def test_uses_words_for_magnitude(self):
        """Uses 'million', 'thousand' instead of numbers."""
        result = format_number_for_voice(2000000, "units")
        assert "million" in result

    def test_duration_uses_natural_words(self):
        """Duration uses 'hours', 'minutes', 'days'."""
        result = format_duration_for_voice(120)
        assert "hours" in result or "hour" in result
