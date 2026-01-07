"""
Asset History Service (Story 4.4)

Business logic for storing and retrieving asset history entries.

AC#2: Mem0 Asset Memory Integration
AC#4: History Retrieval for AI Context
AC#6: Performance Requirements
"""

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from supabase import create_client, Client

from app.core.config import get_settings
from app.models.asset_history import (
    AssetHistoryCreate,
    AssetHistoryRead,
    AssetHistorySearchResult,
    AssetHistoryForAI,
    EventType,
)
from app.services.embedding_service import (
    EmbeddingService,
    EmbeddingServiceError,
    get_embedding_service,
)

logger = logging.getLogger(__name__)


class AssetHistoryServiceError(Exception):
    """Base exception for Asset History Service errors."""
    pass


class AssetHistoryService:
    """
    Service for managing asset history entries and semantic search.

    Story 4.4 Implementation:
    - AC#2: Stores and indexes asset history with Mem0/pgvector
    - AC#4: Retrieves relevant history for AI context
    - AC#6: Performance-optimized queries
    """

    def __init__(
        self,
        supabase_client: Optional[Client] = None,
        embedding_service: Optional[EmbeddingService] = None
    ):
        """
        Initialize the Asset History Service.

        Args:
            supabase_client: Optional Supabase client
            embedding_service: Optional embedding service
        """
        self._client = supabase_client
        self._embedding_service = embedding_service
        self._settings = None

    def _get_settings(self):
        """Get cached settings."""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    def _get_client(self) -> Client:
        """Get or create Supabase client."""
        if self._client is None:
            settings = self._get_settings()
            if not settings.supabase_url or not settings.supabase_key:
                raise AssetHistoryServiceError("Supabase not configured")
            self._client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
        return self._client

    def _get_embedding_service(self) -> EmbeddingService:
        """Get or use provided embedding service."""
        if self._embedding_service is None:
            self._embedding_service = get_embedding_service()
        return self._embedding_service

    async def create_history_entry(
        self,
        asset_id: UUID,
        entry: AssetHistoryCreate,
        user_id: Optional[UUID] = None,
    ) -> AssetHistoryRead:
        """
        Create a new asset history entry with embedding generation.

        AC#2 Task 4.2: Implements create_history_entry() with embedding generation.
        AC#3: History entries automatically generate Mem0 memories on creation.

        Args:
            asset_id: Asset to add history for
            entry: History entry data
            user_id: Optional user who created the entry

        Returns:
            Created AssetHistoryRead

        Raises:
            AssetHistoryServiceError: If creation fails
        """
        try:
            client = self._get_client()

            # Build the insert data
            insert_data = {
                "asset_id": str(asset_id),
                "event_type": entry.event_type.value,
                "title": entry.title,
                "description": entry.description,
                "resolution": entry.resolution,
                "outcome": entry.outcome.value if entry.outcome else None,
                "source": entry.source.value,
                "related_record_type": entry.related_record_type,
                "related_record_id": str(entry.related_record_id) if entry.related_record_id else None,
            }

            if user_id:
                insert_data["created_by"] = str(user_id)

            # Insert the history entry
            response = client.table("asset_history").insert(insert_data).execute()

            if not response.data or len(response.data) == 0:
                raise AssetHistoryServiceError("Failed to insert history entry")

            history_record = response.data[0]
            history_id = history_record["id"]

            # Generate and store embedding
            await self._generate_and_store_embedding(
                history_id=history_id,
                title=entry.title,
                description=entry.description,
                resolution=entry.resolution,
                event_type=entry.event_type.value,
            )

            logger.info(f"Created history entry {history_id} for asset {asset_id}")

            return self._record_to_model(history_record)

        except AssetHistoryServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to create history entry: {e}")
            raise AssetHistoryServiceError(f"Failed to create history entry: {e}")

    async def _generate_and_store_embedding(
        self,
        history_id: str,
        title: str,
        description: Optional[str],
        resolution: Optional[str],
        event_type: str,
    ) -> None:
        """
        Generate embedding for history entry and store in database.

        AC#1: Vector embeddings generated for semantic search.
        AC#7: Uses embedding service for text-embedding-3-small.
        """
        try:
            embedding_svc = self._get_embedding_service()

            # Generate embedding
            embedding = embedding_svc.generate_history_embedding(
                title=title,
                description=description,
                resolution=resolution,
                event_type=event_type,
            )

            # Store embedding
            client = self._get_client()
            client.table("asset_history_embeddings").insert({
                "history_id": history_id,
                "embedding": embedding,
            }).execute()

            logger.debug(f"Stored embedding for history {history_id}")

        except EmbeddingServiceError as e:
            # Log but don't fail the entire operation
            logger.warning(f"Failed to generate embedding for {history_id}: {e}")
        except Exception as e:
            logger.warning(f"Failed to store embedding for {history_id}: {e}")

    async def get_asset_history(
        self,
        asset_id: UUID,
        page: int = 1,
        page_size: int = 10,
        event_types: Optional[List[EventType]] = None,
    ) -> Tuple[List[AssetHistoryRead], Dict[str, Any]]:
        """
        Get paginated history for an asset.

        AC#3 Task 4.3: Implements get_asset_history() with pagination.
        AC#6: Support for assets with 1000+ history entries.

        Args:
            asset_id: Asset to get history for
            page: Page number (1-indexed)
            page_size: Items per page
            event_types: Optional filter by event types

        Returns:
            Tuple of (list of history entries, pagination info)
        """
        try:
            client = self._get_client()

            # Build query
            query = client.table("asset_history").select(
                "*", count="exact"
            ).eq("asset_id", str(asset_id))

            # Apply event type filter
            if event_types:
                type_values = [et.value for et in event_types]
                query = query.in_("event_type", type_values)

            # Apply pagination
            offset = (page - 1) * page_size
            query = query.order("created_at", desc=True).range(
                offset, offset + page_size - 1
            )

            response = query.execute()

            total = response.count or 0
            items = [self._record_to_model(r) for r in response.data or []]

            pagination = {
                "total": total,
                "page": page,
                "page_size": page_size,
                "has_next": offset + page_size < total,
            }

            return items, pagination

        except Exception as e:
            logger.error(f"Failed to get asset history: {e}")
            raise AssetHistoryServiceError(f"Failed to get asset history: {e}")

    async def search_asset_history(
        self,
        asset_id: UUID,
        query: str,
        limit: int = 5,
        event_types: Optional[List[EventType]] = None,
    ) -> List[AssetHistorySearchResult]:
        """
        Search asset history using vector similarity.

        AC#3 Task 4.4: Implements search_asset_history() with vector similarity.
        AC#6: Semantic search returns results within 1 second.

        Args:
            asset_id: Asset to search history for
            query: Search query text
            limit: Maximum number of results
            event_types: Optional filter by event types

        Returns:
            List of search results with similarity scores
        """
        try:
            # Generate query embedding
            embedding_svc = self._get_embedding_service()
            query_embedding = embedding_svc.generate_embedding(query)

            client = self._get_client()

            # Use the search_asset_history function we created in the migration
            response = client.rpc(
                "search_asset_history",
                {
                    "query_embedding": query_embedding,
                    "p_asset_id": str(asset_id),
                    "p_limit": limit * 2,  # Get more to filter by event_type
                }
            ).execute()

            results = []
            for row in response.data or []:
                # Apply event type filter if specified
                if event_types:
                    type_values = [et.value for et in event_types]
                    if row.get("event_type") not in type_values:
                        continue

                results.append(AssetHistorySearchResult(
                    id=UUID(row["history_id"]),
                    asset_id=UUID(row["asset_id"]),
                    event_type=EventType(row["event_type"]),
                    title=row["title"],
                    description=row.get("description"),
                    resolution=row.get("resolution"),
                    similarity_score=row.get("similarity", 0.0),
                    created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
                ))

                if len(results) >= limit:
                    break

            logger.debug(f"Search returned {len(results)} results for asset {asset_id}")
            return results

        except EmbeddingServiceError as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise AssetHistoryServiceError(f"Search failed: {e}")
        except Exception as e:
            logger.error(f"Failed to search asset history: {e}")
            raise AssetHistoryServiceError(f"Search failed: {e}")

    async def get_history_for_ai_context(
        self,
        asset_id: UUID,
        query: str,
        limit: int = 5,
        include_temporal_weighting: bool = True,
        half_life_days: int = 30,
    ) -> Tuple[List[AssetHistoryForAI], str]:
        """
        Get relevant asset history formatted for AI context.

        AC#4 Task 4.5: Implements get_history_for_ai_context() with temporal weighting.
        AC#4: Returns top-k most relevant history entries.
        AC#8: Formatted output suitable for LLM context injection.

        Args:
            asset_id: Asset to get history for
            query: Query for semantic matching
            limit: Maximum number of entries
            include_temporal_weighting: Apply temporal weighting
            half_life_days: Days for weight to decay to 50%

        Returns:
            Tuple of (list of formatted entries, formatted context text)
        """
        try:
            # Get search results
            search_results = await self.search_asset_history(
                asset_id=asset_id,
                query=query,
                limit=limit * 2,  # Get more for re-ranking
            )

            if not search_results:
                return [], ""

            # Apply temporal weighting if enabled
            if include_temporal_weighting:
                ranked_results = self._apply_temporal_weighting(
                    search_results,
                    half_life_days=half_life_days,
                )
            else:
                ranked_results = [
                    (r, r.similarity_score) for r in search_results
                ]

            # Take top-k after re-ranking
            ranked_results = ranked_results[:limit]

            # Format for AI context
            entries = []
            context_parts = []

            for result, combined_score in ranked_results:
                # Create short citation ID
                citation_id = str(result.id)[:8]

                # Build summary
                summary_parts = []
                if result.description:
                    summary_parts.append(result.description)
                if result.resolution:
                    summary_parts.append(f"Resolution: {result.resolution}")
                summary = " ".join(summary_parts) if summary_parts else result.title

                entry = AssetHistoryForAI(
                    citation_id=citation_id,
                    date=result.created_at.strftime("%Y-%m-%d"),
                    event_type=result.event_type,
                    title=result.title,
                    summary=summary,
                    relevance_score=combined_score,
                )
                entries.append(entry)

                # Build context text with citation markers (AC#8 Task 8.3)
                context_parts.append(
                    f"[History:{citation_id}] {result.created_at.strftime('%Y-%m-%d')}: "
                    f"{result.title}. {summary}"
                )

            context_text = "\n".join(context_parts)

            logger.debug(f"Generated AI context with {len(entries)} entries for asset {asset_id}")
            return entries, context_text

        except AssetHistoryServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to get AI context: {e}")
            raise AssetHistoryServiceError(f"Failed to get AI context: {e}")

    def _apply_temporal_weighting(
        self,
        results: List[AssetHistorySearchResult],
        half_life_days: int = 30,
        similarity_weight: float = 0.7,
        temporal_weight: float = 0.3,
    ) -> List[Tuple[AssetHistorySearchResult, float]]:
        """
        Apply temporal weighting to search results.

        AC#4 Task 8.4: Implements temporal weighting algorithm.

        Recent events are ranked higher using exponential decay.

        Args:
            results: Search results to re-rank
            half_life_days: Time for weight to decay to 50%
            similarity_weight: Weight for similarity score (default 70%)
            temporal_weight: Weight for recency (default 30%)

        Returns:
            List of (result, combined_score) tuples, sorted by score
        """
        now = datetime.now(timezone.utc)
        decay_constant = math.log(2) / half_life_days

        weighted_results = []
        for result in results:
            # Calculate age in days
            age_days = (now - result.created_at).total_seconds() / 86400

            # Exponential decay for temporal score
            temporal_score = math.exp(-decay_constant * age_days)

            # Combined score (AC#8 Task 8.4)
            combined_score = (
                similarity_weight * result.similarity_score +
                temporal_weight * temporal_score
            )

            weighted_results.append((result, combined_score))

        # Sort by combined score descending
        weighted_results.sort(key=lambda x: x[1], reverse=True)
        return weighted_results

    async def get_multi_asset_history(
        self,
        area: Optional[str] = None,
        asset_ids: Optional[List[UUID]] = None,
        query: str = "",
        limit: int = 10,
    ) -> List[AssetHistorySearchResult]:
        """
        Search history across multiple assets.

        AC#4 Task 4.6: Implements multi-asset query support.

        Args:
            area: Plant area to filter by
            asset_ids: Specific asset IDs to include
            query: Search query text
            limit: Maximum results

        Returns:
            List of search results across assets
        """
        try:
            client = self._get_client()

            # First, get the assets to search
            if asset_ids:
                target_asset_ids = [str(aid) for aid in asset_ids]
            elif area:
                # Get assets in the specified area
                assets_response = client.table("assets").select("id").eq("area", area).execute()
                target_asset_ids = [a["id"] for a in assets_response.data or []]
            else:
                # No filter - search all assets
                target_asset_ids = None

            if target_asset_ids is not None and not target_asset_ids:
                return []

            # If we have a search query, use vector search
            if query.strip():
                embedding_svc = self._get_embedding_service()
                query_embedding = embedding_svc.generate_embedding(query)

                # Search without asset filter, then filter results
                response = client.rpc(
                    "search_asset_history",
                    {
                        "query_embedding": query_embedding,
                        "p_asset_id": None,
                        "p_limit": limit * 3 if target_asset_ids else limit,
                    }
                ).execute()

                results = []
                for row in response.data or []:
                    # Apply asset filter if specified
                    if target_asset_ids and row["asset_id"] not in target_asset_ids:
                        continue

                    results.append(AssetHistorySearchResult(
                        id=UUID(row["history_id"]),
                        asset_id=UUID(row["asset_id"]),
                        event_type=EventType(row["event_type"]),
                        title=row["title"],
                        description=row.get("description"),
                        resolution=row.get("resolution"),
                        similarity_score=row.get("similarity", 0.0),
                        created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
                    ))

                    if len(results) >= limit:
                        break

                return results

            else:
                # No search query - return recent entries
                query_builder = client.table("asset_history").select("*")

                if target_asset_ids:
                    query_builder = query_builder.in_("asset_id", target_asset_ids)

                response = query_builder.order(
                    "created_at", desc=True
                ).limit(limit).execute()

                return [
                    AssetHistorySearchResult(
                        id=UUID(row["id"]),
                        asset_id=UUID(row["asset_id"]),
                        event_type=EventType(row["event_type"]),
                        title=row["title"],
                        description=row.get("description"),
                        resolution=row.get("resolution"),
                        similarity_score=1.0,  # No similarity for non-search results
                        created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
                    )
                    for row in response.data or []
                ]

        except Exception as e:
            logger.error(f"Failed to get multi-asset history: {e}")
            raise AssetHistoryServiceError(f"Multi-asset search failed: {e}")

    def _record_to_model(self, record: Dict[str, Any]) -> AssetHistoryRead:
        """Convert database record to Pydantic model."""
        return AssetHistoryRead(
            id=UUID(record["id"]),
            asset_id=UUID(record["asset_id"]),
            event_type=EventType(record["event_type"]),
            title=record["title"],
            description=record.get("description"),
            resolution=record.get("resolution"),
            outcome=record.get("outcome"),
            source=record.get("source", "manual"),
            related_record_type=record.get("related_record_type"),
            related_record_id=UUID(record["related_record_id"]) if record.get("related_record_id") else None,
            created_at=datetime.fromisoformat(record["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(record["updated_at"].replace("Z", "+00:00")),
            created_by=UUID(record["created_by"]) if record.get("created_by") else None,
        )

    def clear_cache(self) -> None:
        """Clear any cached data."""
        self._settings = None
        self._client = None
        logger.debug("Asset history service cache cleared")


# Module-level singleton instance
_asset_history_service: Optional[AssetHistoryService] = None


def get_asset_history_service() -> AssetHistoryService:
    """
    Get the singleton AssetHistoryService instance.

    Returns:
        AssetHistoryService singleton instance
    """
    global _asset_history_service
    if _asset_history_service is None:
        _asset_history_service = AssetHistoryService()
    return _asset_history_service
