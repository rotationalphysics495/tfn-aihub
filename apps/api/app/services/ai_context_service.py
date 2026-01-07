"""
AI Context Service (Story 4.4)

Service for formatting asset history into LLM-ready context.
Provides citation markers for NFR1 compliance.

AC#4: History Retrieval for AI Context
AC#5: Data Citation and Provenance
AC#8: Formatted output suitable for LLM context injection
"""

import logging
import math
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from supabase import create_client, Client

from app.core.config import get_settings
from app.models.asset_history import (
    AssetHistoryForAI,
    AIContextResponse,
)
from app.services.asset_history_service import (
    AssetHistoryService,
    AssetHistoryServiceError,
    get_asset_history_service,
)

logger = logging.getLogger(__name__)

# Token estimation constants
CHARS_PER_TOKEN = 4  # Rough estimate for English text


class AIContextServiceError(Exception):
    """Base exception for AI Context Service errors."""
    pass


class AIContextService:
    """
    Service for formatting asset history for LLM context injection.

    Story 4.4 Implementation:
    - AC#4: Service function retrieves relevant asset history for AI prompts
    - AC#5: Includes citation markers for NFR1 compliance
    - AC#8: Formatted output suitable for LLM context injection
    """

    def __init__(
        self,
        history_service: Optional[AssetHistoryService] = None,
        supabase_client: Optional[Client] = None,
    ):
        """
        Initialize the AI Context Service.

        Args:
            history_service: Optional asset history service
            supabase_client: Optional Supabase client for asset lookups
        """
        self._history_service = history_service
        self._client = supabase_client
        self._settings = None
        self._assets_cache = {}

    def _get_settings(self):
        """Get cached settings."""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    def _get_history_service(self) -> AssetHistoryService:
        """Get or use provided history service."""
        if self._history_service is None:
            self._history_service = get_asset_history_service()
        return self._history_service

    def _get_client(self) -> Client:
        """Get or create Supabase client."""
        if self._client is None:
            settings = self._get_settings()
            if not settings.supabase_url or not settings.supabase_key:
                raise AIContextServiceError("Supabase not configured")
            self._client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
        return self._client

    async def get_asset_name(self, asset_id: UUID) -> Optional[str]:
        """
        Get human-readable name for an asset.

        Args:
            asset_id: Asset UUID

        Returns:
            Asset name or None
        """
        asset_id_str = str(asset_id)

        if asset_id_str in self._assets_cache:
            return self._assets_cache[asset_id_str]

        try:
            client = self._get_client()
            response = client.table("assets").select("name").eq(
                "id", asset_id_str
            ).single().execute()

            if response.data:
                name = response.data.get("name")
                self._assets_cache[asset_id_str] = name
                return name

        except Exception as e:
            logger.warning(f"Failed to get asset name for {asset_id}: {e}")

        return None

    async def get_context_for_asset(
        self,
        asset_id: UUID,
        query: str,
        limit: int = 5,
        max_tokens: int = 2000,
        include_temporal_weighting: bool = True,
    ) -> AIContextResponse:
        """
        Get formatted context for a specific asset.

        AC#4: Retrieves relevant asset history for AI prompts.
        AC#8 Task 8.2: Creates LLM-ready context with citation markers.

        Args:
            asset_id: Asset to get context for
            query: Query for semantic matching
            limit: Maximum number of history entries
            max_tokens: Maximum tokens for context (AC#8 Task 8.5)
            include_temporal_weighting: Apply temporal ranking

        Returns:
            AIContextResponse with formatted context
        """
        try:
            history_service = self._get_history_service()

            # Get formatted entries and context text
            entries, context_text = await history_service.get_history_for_ai_context(
                asset_id=asset_id,
                query=query,
                limit=limit,
                include_temporal_weighting=include_temporal_weighting,
            )

            # Get asset name
            asset_name = await self.get_asset_name(asset_id)

            # Limit context size to avoid token overflow (AC#8 Task 8.5)
            context_text = self._limit_context_size(context_text, max_tokens)

            return AIContextResponse(
                asset_id=asset_id,
                asset_name=asset_name,
                query=query,
                context_text=context_text,
                entries=entries,
                entry_count=len(entries),
            )

        except AssetHistoryServiceError as e:
            logger.error(f"History service error: {e}")
            raise AIContextServiceError(f"Failed to get context: {e}")
        except Exception as e:
            logger.error(f"Failed to get context for asset {asset_id}: {e}")
            raise AIContextServiceError(f"Failed to get context: {e}")

    def _limit_context_size(
        self,
        context_text: str,
        max_tokens: int,
    ) -> str:
        """
        Limit context text to specified token count.

        AC#8 Task 8.5: Limit context size to avoid token overflow.

        Args:
            context_text: Original context text
            max_tokens: Maximum tokens allowed

        Returns:
            Truncated context text if needed
        """
        estimated_tokens = len(context_text) // CHARS_PER_TOKEN

        if estimated_tokens <= max_tokens:
            return context_text

        # Truncate to max tokens
        max_chars = max_tokens * CHARS_PER_TOKEN
        truncated = context_text[:max_chars]

        # Try to end at a newline for cleaner truncation
        last_newline = truncated.rfind("\n")
        if last_newline > max_chars * 0.8:  # Keep at least 80%
            truncated = truncated[:last_newline]

        return truncated + "\n[...context truncated for length]"

    def format_history_for_prompt(
        self,
        entries: List[AssetHistoryForAI],
        max_tokens: int = 2000,
    ) -> str:
        """
        Format history entries for LLM context injection.

        AC#8 Task 8.2: Implements format_history_for_prompt().
        AC#5: Includes citation markers for NFR1 compliance.

        Args:
            entries: List of formatted history entries
            max_tokens: Maximum tokens for output

        Returns:
            Formatted context text with citations
        """
        if not entries:
            return ""

        context_parts = []

        for entry in entries:
            # Include citation marker for NFR1 compliance (AC#8 Task 8.3)
            citation = f"[History:{entry.citation_id}]"

            context_parts.append(
                f"{citation} {entry.date}: {entry.title}. {entry.summary}"
            )

        context_text = "\n".join(context_parts)

        # Limit size
        return self._limit_context_size(context_text, max_tokens)

    async def build_full_context(
        self,
        asset_id: UUID,
        query: str,
        include_asset_info: bool = True,
        include_history: bool = True,
        history_limit: int = 5,
        max_tokens: int = 2000,
    ) -> str:
        """
        Build complete context for AI prompt.

        Combines asset information and history into a single context block.

        Args:
            asset_id: Asset to build context for
            query: User query for semantic matching
            include_asset_info: Include asset metadata
            include_history: Include history entries
            history_limit: Max history entries
            max_tokens: Max total tokens

        Returns:
            Complete formatted context string
        """
        context_parts = []

        # Add asset info header if requested
        if include_asset_info:
            asset_name = await self.get_asset_name(asset_id)
            if asset_name:
                context_parts.append(f"Asset: {asset_name}")

        # Add history if requested
        if include_history:
            history_service = self._get_history_service()
            entries, history_text = await history_service.get_history_for_ai_context(
                asset_id=asset_id,
                query=query,
                limit=history_limit,
            )

            if history_text:
                context_parts.append("\nRelevant History:")
                context_parts.append(history_text)

        full_context = "\n".join(context_parts)
        return self._limit_context_size(full_context, max_tokens)

    async def get_multi_asset_context(
        self,
        query: str,
        area: Optional[str] = None,
        asset_ids: Optional[List[UUID]] = None,
        limit: int = 10,
        max_tokens: int = 3000,
    ) -> str:
        """
        Get context across multiple assets.

        Supports queries like "Why do grinding machines keep having issues?"

        Args:
            query: User query
            area: Optional area filter
            asset_ids: Optional specific assets
            limit: Max history entries total
            max_tokens: Max total tokens

        Returns:
            Combined context string
        """
        try:
            history_service = self._get_history_service()

            # Get multi-asset search results
            results = await history_service.get_multi_asset_history(
                area=area,
                asset_ids=asset_ids,
                query=query,
                limit=limit,
            )

            if not results:
                return ""

            # Group by asset for organized output
            by_asset = {}
            for r in results:
                aid = str(r.asset_id)
                if aid not in by_asset:
                    by_asset[aid] = []
                by_asset[aid].append(r)

            # Format context
            context_parts = []

            for asset_id_str, entries in by_asset.items():
                asset_name = await self.get_asset_name(UUID(asset_id_str))
                header = f"\n{asset_name or asset_id_str}:"
                context_parts.append(header)

                for entry in entries:
                    citation_id = str(entry.id)[:8]
                    summary_parts = []
                    if entry.description:
                        summary_parts.append(entry.description)
                    if entry.resolution:
                        summary_parts.append(f"Resolution: {entry.resolution}")
                    summary = " ".join(summary_parts) if summary_parts else entry.title

                    context_parts.append(
                        f"  [History:{citation_id}] {entry.created_at.strftime('%Y-%m-%d')}: "
                        f"{entry.title}. {summary}"
                    )

            context_text = "\n".join(context_parts)
            return self._limit_context_size(context_text, max_tokens)

        except Exception as e:
            logger.error(f"Failed to get multi-asset context: {e}")
            return ""

    def clear_cache(self) -> None:
        """Clear any cached data."""
        self._assets_cache.clear()
        self._settings = None
        self._client = None
        logger.debug("AI Context Service cache cleared")


# Module-level singleton instance
_ai_context_service: Optional[AIContextService] = None


def get_ai_context_service() -> AIContextService:
    """
    Get the singleton AIContextService instance.

    Returns:
        AIContextService singleton instance
    """
    global _ai_context_service
    if _ai_context_service is None:
        _ai_context_service = AIContextService()
    return _ai_context_service
