"""
Mem0 Memory Service (Story 4.1)

Core memory service implementing Mem0 integration with Supabase pgvector.
Provides async methods for storing and retrieving vector memories.

AC#1: Mem0 Python SDK Integration
AC#3: User Session Memory Storage
AC#5: Memory Retrieval for Context
AC#6: Memory Service API
AC#7: OpenAI Embeddings Configuration
AC#8: LangChain Integration Preparation
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from mem0 import Memory

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class MemoryServiceError(Exception):
    """Base exception for Memory Service errors."""
    pass


class MemoryService:
    """
    Memory Service for storing and retrieving user interactions using Mem0.

    Uses Supabase pgvector for vector storage and OpenAI for embeddings.
    Follows singleton pattern with lazy initialization.

    Story 4.1 Implementation:
    - AC#1: Initializes Mem0 with Supabase pgvector configuration
    - AC#3: Stores memories with user_id from JWT claims
    - AC#5: Retrieves memories using semantic similarity search
    - AC#6: Provides async add_memory(), search_memory(), get_all_memories()
    - AC#7: Uses OpenAI text-embedding-ada-002 for embeddings
    - AC#8: Returns context in LangChain-compatible format
    """

    def __init__(self):
        """Initialize the Memory Service (lazy initialization)."""
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

        AC#1: Connects to Supabase pgvector using environment variables.
        AC#7: Configures OpenAI embeddings.

        Returns:
            True if initialization successful, False otherwise

        Raises:
            MemoryServiceError: If configuration is invalid
        """
        if self._initialized and self._memory is not None:
            return True

        settings = self._get_settings()

        if not settings.mem0_configured:
            logger.warning(
                "Memory service not configured. "
                "Set SUPABASE_DB_URL and OPENAI_API_KEY environment variables."
            )
            return False

        try:
            # AC#1: Configure Mem0 with Supabase pgvector
            # AC#7: OpenAI embeddings configuration
            config = {
                "vector_store": {
                    "provider": "supabase",
                    "config": {
                        "connection_string": settings.supabase_db_url,
                        "collection_name": settings.mem0_collection_name,
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

            logger.info(
                f"Memory service initialized with collection: {settings.mem0_collection_name}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize memory service: {e}")
            raise MemoryServiceError(f"Memory service initialization failed: {e}")

    def _ensure_initialized(self) -> None:
        """Ensure the service is initialized before operations."""
        if not self._initialized or self._memory is None:
            if not self.initialize():
                raise MemoryServiceError(
                    "Memory service not configured. "
                    "Check SUPABASE_DB_URL and OPENAI_API_KEY."
                )

    async def add_memory(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Store user interaction in memory.

        AC#3: Stores memory with user_id from JWT claims.
        AC#4: Includes asset_id in metadata when provided.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            user_id: User identifier from JWT claims
            metadata: Optional additional metadata (asset_id, session_id, etc.)

        Returns:
            Dict containing memory storage result with id and status

        Raises:
            MemoryServiceError: If storage fails
        """
        self._ensure_initialized()

        try:
            # AC#3: Build metadata with user_id and timestamp
            meta = metadata.copy() if metadata else {}
            meta["user_id"] = user_id
            meta["timestamp"] = datetime.utcnow().isoformat()

            # Generate a unique memory ID
            memory_id = str(uuid.uuid4())
            meta["memory_id"] = memory_id

            # Store in Mem0
            result = self._memory.add(
                messages,
                user_id=user_id,
                metadata=meta
            )

            logger.info(f"Memory stored for user {user_id}: {memory_id}")
            return {
                "id": memory_id,
                "status": "stored",
                "result": result,
            }

        except Exception as e:
            logger.error(f"Failed to add memory for user {user_id}: {e}")
            raise MemoryServiceError(f"Failed to store memory: {e}")

    async def search_memory(
        self,
        query: str,
        user_id: str,
        limit: Optional[int] = None,
        threshold: Optional[float] = None,
        asset_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for relevant memories.

        AC#5: Searches memories using semantic similarity.
        AC#5: Filters by user_id for personalization.

        Args:
            query: Search query text
            user_id: User identifier for filtering
            limit: Maximum number of results (default from config)
            threshold: Minimum similarity threshold (default from config)
            asset_id: Optional asset_id to filter results

        Returns:
            List of memory dicts with id, memory, similarity, and metadata

        Raises:
            MemoryServiceError: If search fails
        """
        self._ensure_initialized()

        settings = self._get_settings()
        limit = limit or settings.mem0_top_k
        threshold = threshold or settings.mem0_similarity_threshold

        try:
            # AC#5: Search with user_id filter
            results = self._memory.search(
                query,
                user_id=user_id,
                limit=limit
            )

            # Extract memories from results
            memories = results.get("results", []) if isinstance(results, dict) else results

            # Filter by similarity threshold
            filtered = [
                mem for mem in memories
                if mem.get("score", mem.get("similarity", 0)) >= threshold
            ]

            # Optional: Filter by asset_id if provided
            if asset_id:
                filtered = [
                    mem for mem in filtered
                    if mem.get("metadata", {}).get("asset_id") == asset_id
                ]

            logger.debug(
                f"Memory search for user {user_id}: "
                f"query='{query[:50]}...', found={len(filtered)}/{len(memories)}"
            )

            return filtered

        except Exception as e:
            logger.error(f"Memory search failed for user {user_id}: {e}")
            # AC#6: Graceful degradation - return empty on search failure
            return []

    async def get_all_memories(
        self,
        user_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get all memories for a user.

        AC#6: Provides get_all_memories() method.

        Args:
            user_id: User identifier
            limit: Maximum number of memories to retrieve

        Returns:
            List of all user memories
        """
        self._ensure_initialized()

        try:
            # Get all memories for user
            results = self._memory.get_all(user_id=user_id)

            # Extract memories list
            memories = results.get("results", []) if isinstance(results, dict) else results

            # Limit results
            if limit and len(memories) > limit:
                memories = memories[:limit]

            logger.debug(f"Retrieved {len(memories)} memories for user {user_id}")
            return memories

        except Exception as e:
            logger.error(f"Failed to get memories for user {user_id}: {e}")
            return []

    async def get_asset_history(
        self,
        asset_id: str,
        user_id: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get memory history for a specific asset.

        AC#4: Retrieves memories linked to asset_id in metadata.

        Args:
            asset_id: Asset identifier from Plant Object Model
            user_id: User identifier for filtering
            limit: Maximum number of memories to retrieve

        Returns:
            List of memories related to the asset
        """
        self._ensure_initialized()

        try:
            # Get all memories for user, then filter by asset_id
            all_memories = await self.get_all_memories(user_id, limit=100)

            # Filter by asset_id in metadata
            asset_memories = [
                mem for mem in all_memories
                if mem.get("metadata", {}).get("asset_id") == asset_id
            ]

            # Limit results
            if limit and len(asset_memories) > limit:
                asset_memories = asset_memories[:limit]

            logger.debug(
                f"Retrieved {len(asset_memories)} memories for asset {asset_id}"
            )
            return asset_memories

        except Exception as e:
            logger.error(f"Failed to get asset history for {asset_id}: {e}")
            return []

    async def get_context_for_query(
        self,
        query: str,
        user_id: str,
        asset_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        """
        Get relevant context formatted for LangChain integration.

        AC#8: Returns context in LangChain-compatible format.
        AC#5: Combines user memories and asset-specific memories.

        Args:
            query: Current user query
            user_id: User identifier
            asset_id: Optional asset to include asset-specific history
            limit: Maximum number of context items

        Returns:
            List of message dicts with 'role' and 'content' keys
            compatible with LangChain memory interface
        """
        self._ensure_initialized()

        settings = self._get_settings()
        limit = limit or settings.mem0_top_k

        try:
            # AC#5: Search for relevant memories
            memories = await self.search_memory(query, user_id, limit=limit)

            # Include asset-specific history if asset_id provided
            if asset_id:
                asset_memories = await self.get_asset_history(
                    asset_id, user_id, limit=limit
                )
                # Merge, avoiding duplicates
                memory_ids = {m.get("id") for m in memories}
                for am in asset_memories:
                    if am.get("id") not in memory_ids:
                        memories.append(am)

            # AC#8: Format for LangChain compatibility
            context = []
            for mem in memories[:limit]:
                memory_content = mem.get("memory", mem.get("content", ""))
                if memory_content:
                    context.append({
                        "role": "system",
                        "content": f"Previous context: {memory_content}"
                    })

            logger.debug(
                f"Built context for query: {len(context)} messages for user {user_id}"
            )
            return context

        except Exception as e:
            logger.error(f"Failed to build context for user {user_id}: {e}")
            return []

    def clear_cache(self) -> None:
        """Clear any cached data."""
        self._settings = None
        logger.debug("Memory service cache cleared")

    def is_configured(self) -> bool:
        """Check if the memory service is properly configured."""
        settings = self._get_settings()
        return settings.mem0_configured

    def is_initialized(self) -> bool:
        """Check if the memory service is initialized."""
        return self._initialized and self._memory is not None


# Module-level singleton instance
memory_service = MemoryService()


def get_memory_service() -> MemoryService:
    """
    Get the singleton MemoryService instance.

    Returns:
        MemoryService singleton instance
    """
    return memory_service
