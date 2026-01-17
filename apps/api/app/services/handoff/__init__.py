"""
Handoff Service Module (Story 9.1, 9.4, 9.6)

Services for shift handoff management including:
- Shift detection (Story 9.1)
- Handoff creation and supervisor assignment checks (Story 9.1)
- Persistent handoff storage with immutability guarantees (Story 9.4)
- Handoff Q&A processing with context injection (Story 9.6)

References:
- [Source: architecture/voice-briefing.md#Shift-Handoff-Workflow]
- [Source: prd/prd-non-functional-requirements.md#NFR24]
- [Source: prd/prd-functional-requirements.md#FR26,FR52]
"""

from app.services.handoff.shift_detection import (
    detect_current_shift,
    get_shift_time_range,
    get_shift_for_handoff,
    SHIFT_WINDOWS,
)

from app.services.handoff.storage import (
    HandoffStorageService,
    HandoffPersistenceError,
    HandoffImmutabilityError,
    get_handoff_storage_service,
)

from app.services.handoff.qa import (
    HandoffQAService,
    HandoffQAError,
    get_handoff_qa_service,
)

__all__ = [
    # Shift detection (Story 9.1)
    "detect_current_shift",
    "get_shift_time_range",
    "get_shift_for_handoff",
    "SHIFT_WINDOWS",
    # Storage service (Story 9.4)
    "HandoffStorageService",
    "HandoffPersistenceError",
    "HandoffImmutabilityError",
    "get_handoff_storage_service",
    # Q&A service (Story 9.6)
    "HandoffQAService",
    "HandoffQAError",
    "get_handoff_qa_service",
]
