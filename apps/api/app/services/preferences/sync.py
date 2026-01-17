"""
Preference Mem0 Sync Service (Story 8.9)

Handles syncing user preferences to Mem0 for AI context enrichment.
Implements semantic formatting and retry logic with exponential backoff.

AC#2: Mem0 context includes semantic descriptions
AC#4: Sync includes semantic context with version history
AC#5: Graceful degradation when Mem0 unavailable

References:
- [Source: architecture/voice-briefing.md#User Preferences Architecture]
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from app.models.preferences import (
    UserPreferencesResponse,
    Mem0PreferenceContext,
)
from app.services.memory.mem0_service import (
    MemoryService,
    MemoryServiceError,
    get_memory_service,
)

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0


def format_preferences_for_mem0(
    preferences: UserPreferencesResponse,
    reason: Optional[str] = None,
) -> str:
    """
    Format user preferences as semantic natural language for Mem0.

    AC#2: Transform structured preferences to semantic descriptions.
    AC#4: Include WHY context when available.

    Args:
        preferences: Structured user preferences
        reason: Optional context about why preferences were set

    Returns:
        Natural language description suitable for AI context
    """
    context = Mem0PreferenceContext.from_preferences(preferences, reason)

    # Build the full semantic context
    parts = []

    # Add timestamp header
    parts.append(f"[User Preferences updated at {context.metadata.get('timestamp', 'unknown')}]")

    # Add all semantic descriptions
    for desc in context.semantic_descriptions:
        parts.append(desc)

    # Add reason if provided
    if context.preference_reason:
        parts.append(f"Context: {context.preference_reason}")

    return " | ".join(parts)


async def _sync_with_retry(
    memory_service: MemoryService,
    user_id: str,
    semantic_context: str,
    metadata: Dict[str, Any],
    max_retries: int = MAX_RETRIES,
) -> bool:
    """
    Sync to Mem0 with exponential backoff retry.

    AC#5: Implements retry logic for Mem0 failures.

    Args:
        memory_service: Initialized memory service
        user_id: User identifier
        semantic_context: Natural language preference context
        metadata: Additional metadata for Mem0 storage
        max_retries: Maximum number of retry attempts

    Returns:
        True if sync succeeded, False otherwise
    """
    backoff = INITIAL_BACKOFF_SECONDS

    for attempt in range(max_retries + 1):
        try:
            # Use add_memory from existing MemoryService
            await memory_service.add_memory(
                messages=[{"role": "system", "content": semantic_context}],
                user_id=user_id,
                metadata=metadata,
            )
            logger.info(f"Preferences synced to Mem0 for user {user_id}")
            return True

        except MemoryServiceError as e:
            logger.warning(
                f"Mem0 sync attempt {attempt + 1}/{max_retries + 1} failed for user {user_id}: {e}"
            )
            if attempt < max_retries:
                await asyncio.sleep(backoff)
                backoff *= 2  # Exponential backoff: 1s, 2s, 4s
            else:
                logger.error(
                    f"Mem0 sync failed after {max_retries + 1} attempts for user {user_id}"
                )
                return False

        except Exception as e:
            logger.error(
                f"Unexpected error syncing preferences to Mem0 for user {user_id}: {e}"
            )
            if attempt < max_retries:
                await asyncio.sleep(backoff)
                backoff *= 2
            else:
                return False

    return False


async def sync_preferences_to_mem0(
    user_id: str,
    preferences: UserPreferencesResponse,
    reason: Optional[str] = None,
) -> bool:
    """
    Sync user preferences to Mem0 as semantic context.

    AC#2: Mem0 context includes semantic descriptions.
    AC#4: Sync includes semantic context about why preferences were set.
    AC#5: Graceful degradation - returns False on failure, doesn't raise.

    This function is designed to be called as a background task,
    so it catches all exceptions and logs them rather than raising.

    Args:
        user_id: User identifier
        preferences: User preferences to sync
        reason: Optional context about why preferences were set

    Returns:
        True if sync succeeded, False otherwise
    """
    logger.debug(f"Starting Mem0 sync for user {user_id}")

    try:
        memory_service = get_memory_service()

        # Check if memory service is configured
        if not memory_service.is_configured():
            logger.warning(
                f"Mem0 not configured, skipping preference sync for user {user_id}"
            )
            return False

        # Format preferences as semantic context
        semantic_context = format_preferences_for_mem0(preferences, reason)

        # Build metadata for version history (AC#4)
        metadata = {
            "preference_type": "user_preferences",
            "preference_version": preferences.updated_at,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "role": preferences.role.value if hasattr(preferences.role, 'value') else str(preferences.role),
            "detail_level": preferences.detail_level.value if hasattr(preferences.detail_level, 'value') else str(preferences.detail_level),
            "voice_enabled": preferences.voice_enabled,
            "area_count": len(preferences.area_order) if preferences.area_order else 0,
        }

        # Sync with retry logic
        return await _sync_with_retry(
            memory_service=memory_service,
            user_id=user_id,
            semantic_context=semantic_context,
            metadata=metadata,
        )

    except Exception as e:
        # AC#5: Graceful degradation - log and return False
        logger.error(
            f"Failed to sync preferences to Mem0 for user {user_id}: {e}",
            exc_info=True,
        )
        return False


async def get_preference_context_from_mem0(
    user_id: str,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Retrieve preference-related memories from Mem0.

    Useful for getting historical preference context for AI personalization.

    Args:
        user_id: User identifier
        limit: Maximum number of memories to retrieve

    Returns:
        List of preference-related memories
    """
    try:
        memory_service = get_memory_service()

        if not memory_service.is_configured():
            logger.warning("Mem0 not configured, returning empty preference context")
            return []

        # Search for preference-related memories
        results = await memory_service.search_memory(
            query="user preferences briefing settings",
            user_id=user_id,
            limit=limit,
        )

        # Filter to only preference-type memories
        preference_memories = [
            mem for mem in results
            if mem.get("metadata", {}).get("preference_type") == "user_preferences"
        ]

        return preference_memories

    except Exception as e:
        logger.error(f"Failed to get preference context from Mem0 for user {user_id}: {e}")
        return []
