"""
Mem0 Asset Service (Story 4.4)

Integration with Mem0 for storing asset history as memories.
This provides an alternative memory storage mechanism that complements
the native pgvector-based asset_history tables.

AC#2: Mem0 Asset Memory Integration
AC#5: Integrate with Mem0 vector storage
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from mem0 import Memory

from app.core.config import get_settings
from app.models.asset_history import EventType

logger = logging.getLogger(__name__)


class Mem0AssetServiceError(Exception):
    """Base exception for Mem0 Asset Service errors."""
    pass


class Mem0AssetService:
    """
    Service for storing and retrieving asset history as Mem0 memories.

    Story 4.4 Implementation:
    - AC#2: Stores asset history entries as Mem0 memories
    - AC#5 Task 5.3: Tags memories with asset metadata
    - AC#5 Task 5.4: Retrieves asset memories for context
    """

    def __init__(self):
        """Initialize the Mem0 Asset Service (lazy initialization)."""
        self._memory: Optional[Memory] = None
        self._initialized: bool = False
        self._settings = None

    def _get_settings(self):
        """Get cached settings."""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    def initialize(self) -> bool:
        """
        Initialize Mem0 with Supabase pgvector configuration.

        AC#5 Task 5.5: Handles Mem0 API integration with Supabase pgvector.

        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized and self._memory is not None:
            return True

        settings = self._get_settings()

        if not settings.mem0_configured:
            logger.warning(
                "Mem0 Asset Service not configured. "
                "Set SUPABASE_DB_URL and OPENAI_API_KEY environment variables."
            )
            return False

        try:
            # Configure Mem0 with Supabase pgvector and OpenAI embeddings
            config = {
                "vector_store": {
                    "provider": "supabase",
                    "config": {
                        "connection_string": settings.supabase_db_url,
                        "collection_name": "asset_memories",  # Separate from user memories
                        "embedding_model_dims": settings.mem0_embedding_dims,
                    }
                },
                "embedder": {
                    "provider": "openai",
                    "config": {
                        "model": "text-embedding-ada-002",
                        "api_key": settings.openai_api_key,
                    }
                },
                "llm": {
                    "provider": "openai",
                    "config": {
                        "model": "gpt-4o-mini",
                        "api_key": settings.openai_api_key,
                    }
                }
            }

            self._memory = Memory.from_config(config)
            self._initialized = True

            logger.info("Mem0 Asset Service initialized with collection: asset_memories")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Mem0 Asset Service: {e}")
            return False

    def _ensure_initialized(self) -> None:
        """Ensure the service is initialized before operations."""
        if not self._initialized or self._memory is None:
            if not self.initialize():
                raise Mem0AssetServiceError(
                    "Mem0 Asset Service not configured. "
                    "Check SUPABASE_DB_URL and OPENAI_API_KEY."
                )

    async def add_asset_memory(
        self,
        asset_id: UUID,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Add asset history to Mem0 memory.

        AC#5 Task 5.2: Implements add_asset_memory() to store history as Mem0 memory.
        AC#5 Task 5.3: Tags memories with asset metadata.

        Args:
            asset_id: Asset identifier
            content: History content to store
            metadata: Additional metadata (asset_name, area, event_type, etc.)

        Returns:
            Dict containing memory storage result

        Raises:
            Mem0AssetServiceError: If storage fails
        """
        self._ensure_initialized()

        try:
            # Build complete metadata with asset identifiers
            meta = metadata.copy() if metadata else {}
            meta["asset_id"] = str(asset_id)
            meta["timestamp"] = datetime.utcnow().isoformat()
            meta["memory_type"] = "asset_history"

            # Use asset_id as user_id for Mem0 (enables asset-scoped retrieval)
            user_id = f"asset:{asset_id}"

            # Store in Mem0 as a message
            messages = [
                {"role": "system", "content": content}
            ]

            result = self._memory.add(
                messages,
                user_id=user_id,
                metadata=meta
            )

            logger.info(f"Asset memory stored for asset {asset_id}")
            return {
                "status": "stored",
                "asset_id": str(asset_id),
                "result": result,
            }

        except Exception as e:
            logger.error(f"Failed to add asset memory for {asset_id}: {e}")
            raise Mem0AssetServiceError(f"Failed to store asset memory: {e}")

    async def add_history_entry_to_mem0(
        self,
        asset_id: UUID,
        event_type: EventType,
        title: str,
        description: Optional[str] = None,
        resolution: Optional[str] = None,
        asset_name: Optional[str] = None,
        area: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add an asset history entry to Mem0 as a formatted memory.

        Convenience method that formats history entry content properly.

        Args:
            asset_id: Asset identifier
            event_type: Type of event
            title: Event title
            description: Event description
            resolution: Resolution text
            asset_name: Human-readable asset name
            area: Plant area

        Returns:
            Dict containing memory storage result
        """
        # Format content for storage
        parts = [f"[{event_type.value.upper()}]", title]

        if description:
            parts.append(description)

        if resolution:
            parts.append(f"Resolution: {resolution}")

        content = " | ".join(parts)

        # Build metadata
        metadata = {
            "event_type": event_type.value,
            "title": title,
        }

        if asset_name:
            metadata["asset_name"] = asset_name

        if area:
            metadata["area"] = area

        return await self.add_asset_memory(
            asset_id=asset_id,
            content=content,
            metadata=metadata,
        )

    async def retrieve_asset_memories(
        self,
        asset_id: UUID,
        query: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories for an asset.

        AC#5 Task 5.4: Implements retrieve_asset_memories() for context retrieval.

        Args:
            asset_id: Asset identifier
            query: Search query
            limit: Maximum number of results

        Returns:
            List of relevant memories

        Raises:
            Mem0AssetServiceError: If retrieval fails
        """
        self._ensure_initialized()

        try:
            user_id = f"asset:{asset_id}"

            results = self._memory.search(
                query,
                user_id=user_id,
                limit=limit
            )

            # Extract memories from results
            memories = results.get("results", []) if isinstance(results, dict) else results

            logger.debug(
                f"Retrieved {len(memories)} memories for asset {asset_id} "
                f"with query '{query[:50]}...'"
            )

            return memories

        except Exception as e:
            logger.error(f"Failed to retrieve asset memories: {e}")
            # Graceful degradation - return empty list
            return []

    async def retrieve_area_memories(
        self,
        area: str,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories for all assets in an area.

        Supports multi-asset queries like "all grinding area machines".

        Args:
            area: Plant area name
            query: Search query
            limit: Maximum number of results

        Returns:
            List of relevant memories across the area
        """
        self._ensure_initialized()

        try:
            # For area-wide search, we search across all asset memories
            # and filter by area in metadata
            results = self._memory.search(
                query,
                limit=limit * 2,  # Get more for filtering
            )

            memories = results.get("results", []) if isinstance(results, dict) else results

            # Filter by area in metadata
            area_memories = [
                m for m in memories
                if m.get("metadata", {}).get("area", "").lower() == area.lower()
            ]

            logger.debug(
                f"Retrieved {len(area_memories)} memories for area '{area}'"
            )

            return area_memories[:limit]

        except Exception as e:
            logger.error(f"Failed to retrieve area memories: {e}")
            return []

    async def get_all_asset_memories(
        self,
        asset_id: UUID,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get all memories for a specific asset.

        Args:
            asset_id: Asset identifier
            limit: Maximum number of memories

        Returns:
            List of all asset memories
        """
        self._ensure_initialized()

        try:
            user_id = f"asset:{asset_id}"

            results = self._memory.get_all(user_id=user_id)

            memories = results.get("results", []) if isinstance(results, dict) else results

            if len(memories) > limit:
                memories = memories[:limit]

            logger.debug(f"Retrieved {len(memories)} total memories for asset {asset_id}")
            return memories

        except Exception as e:
            logger.error(f"Failed to get all asset memories: {e}")
            return []

    def is_configured(self) -> bool:
        """Check if the service is properly configured."""
        settings = self._get_settings()
        return settings.mem0_configured

    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._initialized and self._memory is not None

    def clear_cache(self) -> None:
        """Clear any cached data."""
        self._settings = None
        logger.debug("Mem0 Asset Service cache cleared")


# Module-level singleton instance
_mem0_asset_service: Optional[Mem0AssetService] = None


def get_mem0_asset_service() -> Mem0AssetService:
    """
    Get the singleton Mem0AssetService instance.

    Returns:
        Mem0AssetService singleton instance
    """
    global _mem0_asset_service
    if _mem0_asset_service is None:
        _mem0_asset_service = Mem0AssetService()
    return _mem0_asset_service
