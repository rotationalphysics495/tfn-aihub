# Story 8.6: Voice Number Formatting

Status: Done

## Story

As a **user listening to a voice briefing**,
I want **numbers formatted for natural speech**,
So that **I can easily understand metrics without mental conversion**.

## Acceptance Criteria

1. **AC1: Large Numbers (Millions)**
   - Given a metric value is 2,130,500 units
   - When formatted for voice delivery (FR19)
   - Then it reads as "about 2.1 million units"

2. **AC2: Percentage Formatting**
   - Given a metric value is 87.3%
   - When formatted for voice delivery
   - Then it reads as "87 percent" (not "87.3 percent")

3. **AC3: Currency Formatting**
   - Given a dollar amount is $45,230
   - When formatted for voice delivery
   - Then it reads as "about 45 thousand dollars"

4. **AC4: Duration Conversion**
   - Given a time duration is 4,320 minutes
   - When formatted for voice delivery
   - Then it reads as "about 72 hours" or "3 days"

5. **AC5: Small Precise Values**
   - Given a small precise value is needed (e.g., 5 units)
   - When formatted for voice delivery
   - Then exact value is used: "5 units"

## Tasks / Subtasks

- [x] Task 1: Create voice formatting utilities module (AC: #1-5)
  - [x] 1.1 Create `apps/api/app/services/briefing/formatters.py`
  - [x] 1.2 Implement `format_number_for_voice(value: float, unit: str) -> str`
  - [x] 1.3 Implement `format_percentage_for_voice(value: float) -> str`
  - [x] 1.4 Implement `format_currency_for_voice(value: float) -> str`
  - [x] 1.5 Implement `format_duration_for_voice(minutes: int) -> str`
  - [x] 1.6 Add unit detection logic for automatic formatting selection

- [x] Task 2: Integrate formatters into narrative service (AC: #1-5)
  - [x] 2.1 Add `format_for_voice()` function to `apps/api/app/services/briefing/formatters.py`
  - [x] 2.2 Integrate formatters into narrative text generation in `narrative.py`
  - [x] 2.3 Ensure all numeric metrics pass through voice formatting before TTS

- [x] Task 3: Write unit tests for formatters (AC: #1-5)
  - [x] 3.1 Create `apps/api/tests/services/briefing/test_briefing_formatters.py`
  - [x] 3.2 Test large number formatting (millions, thousands)
  - [x] 3.3 Test percentage rounding
  - [x] 3.4 Test currency formatting
  - [x] 3.5 Test duration conversion (minutes to hours/days)
  - [x] 3.6 Test small value passthrough
  - [x] 3.7 Test edge cases (zero, negative, boundary values)

## Dev Notes

### Formatting Rules Reference

```python
# Number formatting rules (from Epic 8.6 Technical Notes):
# - Numbers >1M: "X.X million" (e.g., 2,130,500 -> "about 2.1 million")
# - Numbers >1K: "X thousand" or "about X thousand" (e.g., 45,230 -> "about 45 thousand")
# - Percentages: round to nearest integer (e.g., 87.3% -> "87 percent")
# - Durations: convert to largest sensible unit (e.g., 4,320 min -> "72 hours" or "3 days")
# - Small numbers (<100): use exact values (e.g., 5 units -> "5 units")
```

### Architecture Integration Points

- **Location**: `apps/api/app/services/briefing/`
- **Pattern**: Utility module (formatters.py) + integration in narrative.py
- **This is NOT a ManufacturingTool** - it's a utility service used by BriefingService
- Formatting applies in narrative.py BEFORE text is sent to ElevenLabs TTS

### Implementation Pattern

```python
# File: apps/api/app/services/briefing/formatters.py
"""
Voice Number Formatting Utilities (Story 8.6)

Provides natural language formatting for numbers in voice briefings.
All metrics pass through these formatters before TTS synthesis.

AC#1: Large numbers -> "about X.X million"
AC#2: Percentages -> rounded to integer
AC#3: Currency -> "about X thousand dollars"
AC#4: Durations -> largest sensible unit
AC#5: Small values -> exact
"""

def format_number_for_voice(value: float, unit: str = "") -> str:
    """Format a numeric value for natural speech."""
    pass

def format_percentage_for_voice(value: float) -> str:
    """Format percentage, rounding to nearest integer."""
    pass

def format_currency_for_voice(value: float) -> str:
    """Format dollar amount for speech."""
    pass

def format_duration_for_voice(minutes: int) -> str:
    """Convert duration to most natural unit (minutes/hours/days)."""
    pass

def format_for_voice(value: Any, value_type: str = "auto") -> str:
    """Auto-detect and format any value for voice delivery."""
    pass
```

### Threshold Values

| Value Range | Output Format | Example |
|-------------|---------------|---------|
| >= 1,000,000 | "about X.X million [unit]" | 2,130,500 -> "about 2.1 million units" |
| >= 10,000 | "about X thousand [unit]" | 45,230 -> "about 45 thousand" |
| >= 1,000 | "about X thousand [unit]" | 1,500 -> "about 1.5 thousand" |
| < 100 | exact value | 5 -> "5" |
| 100-999 | exact value | 250 -> "250" |

### Duration Conversion Logic

```python
# Duration hierarchy (prefer larger units for clarity):
# >= 1440 min (24h): convert to days ("3 days")
# >= 60 min: convert to hours ("72 hours")
# < 60 min: keep as minutes ("45 minutes")
# Edge case: 72 hours could also be "3 days" - prefer days when evenly divisible
```

### Rounding Strategy

- Use "about" prefix when rounding significantly
- Percentages: always round to nearest integer, no "about" prefix
- Currency: round to nearest thousand, use "about" prefix
- Large numbers: round to one decimal place for millions

### Project Structure Notes

- Files align with architecture: `apps/api/app/services/briefing/`
- Test location: `apps/api/tests/services/test_briefing_formatters.py`
- Snake_case filenames per implementation-patterns.md
- This story creates new files; no existing code to extend yet (briefing service not implemented)

### Dependencies

- **Depends on**: Story 8.3 (Briefing Synthesis Engine) should create the narrative.py file
- **Soft dependency**: formatters.py can be created independently and integrated when narrative.py exists
- **No external dependencies**: Pure Python utility functions

### Testing Strategy

```python
# Test cases per AC:

# AC1: Large numbers
assert format_number_for_voice(2130500, "units") == "about 2.1 million units"
assert format_number_for_voice(1000000, "units") == "about 1 million units"

# AC2: Percentages
assert format_percentage_for_voice(87.3) == "87 percent"
assert format_percentage_for_voice(99.9) == "100 percent"
assert format_percentage_for_voice(0.4) == "0 percent"

# AC3: Currency
assert format_currency_for_voice(45230) == "about 45 thousand dollars"
assert format_currency_for_voice(1234567) == "about 1.2 million dollars"

# AC4: Duration
assert format_duration_for_voice(4320) == "about 72 hours" or "3 days"
assert format_duration_for_voice(60) == "1 hour"
assert format_duration_for_voice(30) == "30 minutes"

# AC5: Small values
assert format_number_for_voice(5, "units") == "5 units"
assert format_number_for_voice(99, "items") == "99 items"
```

### Edge Cases to Handle

1. **Zero values**: "0 units" (not "about 0")
2. **Negative values**: Handle or raise error (downtime shouldn't be negative)
3. **Very large numbers**: Billions -> "X.X billion"
4. **Fractional small values**: 0.5 units -> "0.5 units" (keep precision)
5. **Duration edge cases**: 1 day vs 24 hours preference
6. **Percentage boundary**: 100.0% -> "100 percent"

### References

- [Source: epic-8.md#Story-8.6]
- [Source: architecture/voice-briefing.md#BriefingService-Architecture]
- [Source: architecture/implementation-patterns.md#Consistency-Rules]
- [Source: architecture.md#Section-4-Repository-Structure]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Implementation Summary

Implemented comprehensive voice number formatting utilities for natural speech in voice briefings. Created a standalone formatters module with functions for large numbers, percentages, currency, and durations. Integrated formatters into the existing NarrativeGenerator service to ensure all numeric metrics are formatted for voice before TTS synthesis.

### Files Created/Modified

**Created:**
- `apps/api/app/services/briefing/formatters.py` - Voice formatting utilities module (6 functions)
- `apps/api/tests/services/briefing/__init__.py` - Test package init
- `apps/api/tests/services/briefing/test_briefing_formatters.py` - Comprehensive unit tests (74 tests)

**Modified:**
- `apps/api/app/services/briefing/__init__.py` - Export new formatters
- `apps/api/app/services/briefing/narrative.py` - Integrate formatters into narrative generation

### Key Decisions

1. **Formatters as standalone utility module**: Created `formatters.py` as a utility module rather than embedding in NarrativeGenerator, allowing reuse across different services
2. **Threshold constants**: Defined clear thresholds (BILLION_THRESHOLD, MILLION_THRESHOLD, etc.) for maintainability
3. **"About" prefix strategy**: Use "about" for rounded large numbers and currency, never for percentages or small exact values
4. **Duration preference**: Prefer days when evenly divisible (e.g., 3 days vs 72 hours), otherwise use hours
5. **Context-aware detection**: Added `detect_and_format()` for intelligent type detection from string values or context hints

### Tests Added

**Test File:** `apps/api/tests/services/briefing/test_briefing_formatters.py`

**Test Classes (74 tests total):**
- `TestLargeNumberFormatting` (8 tests) - AC#1: Millions, billions, thousands
- `TestPercentageFormatting` (7 tests) - AC#2: Rounding, boundaries
- `TestCurrencyFormatting` (7 tests) - AC#3: Thousands, millions, billions
- `TestDurationConversion` (10 tests) - AC#4: Minutes, hours, days
- `TestSmallPreciseValues` (6 tests) - AC#5: Exact values under 100
- `TestEdgeCases` (11 tests) - Zero, negative, None, very large
- `TestFormatForVoice` (7 tests) - Unified formatting function
- `TestDetectAndFormat` (6 tests) - Context-aware detection
- `TestNarrativeIntegration` (4 tests) - Integration patterns
- `TestRoundingBehavior` (4 tests) - Specific rounding cases
- `TestVoiceOutputQuality` (4 tests) - Output suitable for TTS

### Test Results

```
74 passed, 23 warnings in 0.04s
```

All tests pass. Warnings are from unrelated storage3 Pydantic deprecation.

### Notes for Reviewer

1. **Narrative Integration**: Updated `_prepare_data_summary()`, `_generate_headline_template()`, and `_generate_concerns_template()` to use voice formatters
2. **LLM Prompt Updated**: Modified NARRATIVE_PROMPT to instruct LLM that numbers are already formatted for voice
3. **Export Pattern**: All formatters exported from `__init__.py` for easy import
4. **No Breaking Changes**: All existing narrative functionality preserved; formatters enhance output

### Acceptance Criteria Status

- [x] **AC1: Large Numbers (Millions)** - `format_number_for_voice(2130500, "units")` returns "about 2.1 million units" - `formatters.py:41-93`
- [x] **AC2: Percentage Formatting** - `format_percentage_for_voice(87.3)` returns "87 percent" - `formatters.py:108-133`
- [x] **AC3: Currency Formatting** - `format_currency_for_voice(45230)` returns "about 45 thousand dollars" - `formatters.py:136-183`
- [x] **AC4: Duration Conversion** - `format_duration_for_voice(4320)` returns "3 days" (72 hours) - `formatters.py:186-236`
- [x] **AC5: Small Precise Values** - `format_number_for_voice(5, "units")` returns "5 units" (exact) - `formatters.py:59-66`

### File List

1. `apps/api/app/services/briefing/formatters.py`
2. `apps/api/app/services/briefing/__init__.py`
3. `apps/api/app/services/briefing/narrative.py`
4. `apps/api/tests/services/briefing/__init__.py`
5. `apps/api/tests/services/briefing/test_briefing_formatters.py`

## Code Review Record

**Reviewer**: Code Review Agent
**Date**: 2026-01-16

### Issues Found

| # | Description | Severity | Status |
|---|-------------|----------|--------|
| 1 | Unused `import math` in formatters.py:19 | LOW | Document only |

**Totals**: 0 HIGH, 0 MEDIUM, 1 LOW

### Acceptance Criteria Verification

| AC# | Description | Implemented | Tested | Matches Spec |
|-----|-------------|-------------|--------|--------------|
| AC1 | Large Numbers (2,130,500 → "about 2.1 million units") | ✅ | ✅ | ✅ |
| AC2 | Percentage (87.3% → "87 percent") | ✅ | ✅ | ✅ |
| AC3 | Currency ($45,230 → "about 45 thousand dollars") | ✅ | ✅ | ✅ |
| AC4 | Duration (4,320 min → "3 days") | ✅ | ✅ | ✅ |
| AC5 | Small Values (5 → "5 units") | ✅ | ✅ | ✅ |

### Code Quality Assessment

- **Pattern compliance**: ✅ Follows existing patterns (snake_case, proper module structure, `__all__` exports)
- **Error handling**: ✅ Handles None, negative values, zero, and edge cases gracefully
- **Tests**: ✅ 74 comprehensive tests covering all acceptance criteria and edge cases
- **Security**: ✅ No security vulnerabilities (pure utility functions, no user input risks)
- **Integration**: ✅ Properly integrated into NarrativeGenerator
- **Documentation**: ✅ Good docstrings with examples

### Test Results

```
74 passed, 12 warnings in 0.03s
```

All tests pass. Warnings are from unrelated third-party library deprecation notices.

### Fixes Applied

None required. Total issues (1) ≤ 5 and only LOW severity issues found.

### Remaining Issues

- **LOW**: Unused `import math` in formatters.py:19 - Minor linting issue, does not affect functionality. Can be cleaned up in future refactoring.

### Final Status

**Approved** - All acceptance criteria verified and implemented correctly. Tests comprehensive and passing. Code follows project patterns.
