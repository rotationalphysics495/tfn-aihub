"""
Handoff Service Module (Story 9.1)

Services for shift handoff management including shift detection,
handoff creation, and supervisor assignment checks.

References:
- [Source: architecture/voice-briefing.md#Shift-Handoff-Workflow]
"""

from app.services.handoff.shift_detection import (
    detect_current_shift,
    get_shift_time_range,
    get_shift_for_handoff,
    SHIFT_WINDOWS,
)

__all__ = [
    "detect_current_shift",
    "get_shift_time_range",
    "get_shift_for_handoff",
    "SHIFT_WINDOWS",
]
