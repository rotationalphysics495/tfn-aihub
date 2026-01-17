"""
Preference Service Module (Story 8.9)

Provides dual storage for user preferences:
- Supabase for structured queries (role filtering, area order sorting)
- Mem0 for AI context enrichment (semantic preference descriptions)

AC#1: Preferences written to user_preferences table
AC#2: Mem0 context includes semantic descriptions
AC#5: Graceful degradation when Mem0 unavailable

References:
- [Source: architecture/voice-briefing.md#User Preferences Architecture]
"""

from app.services.preferences.service import (
    PreferenceService,
    get_preference_service,
)
from app.services.preferences.sync import (
    sync_preferences_to_mem0,
    format_preferences_for_mem0,
)

__all__ = [
    "PreferenceService",
    "get_preference_service",
    "sync_preferences_to_mem0",
    "format_preferences_for_mem0",
]
