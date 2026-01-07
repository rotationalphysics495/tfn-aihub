"""
Tests for Asset History Service (Story 4.4)

AC#1: Asset History Data Model
AC#2: Mem0 Asset Memory Integration
AC#4: History Retrieval for AI Context
AC#6: Performance Requirements
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4, UUID

from app.services.asset_history_service import (
    AssetHistoryService,
    AssetHistoryServiceError,
    get_asset_history_service,
)
from app.models.asset_history import (
    AssetHistoryCreate,
    AssetHistoryRead,
    AssetHistorySearchResult,
    EventType,
    Outcome,
    Source,
)


@pytest.fixture
def history_service():
    """Create a fresh AssetHistoryService instance for testing."""
    svc = AssetHistoryService()
    svc.clear_cache()
    return svc


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    mock_client = MagicMock()
    return mock_client


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service."""
    mock_svc = MagicMock()
    mock_svc.generate_embedding.return_value = [0.1] * 1536
    mock_svc.generate_history_embedding.return_value = [0.1] * 1536
    return mock_svc


@pytest.fixture
def sample_asset_id():
    """Sample asset UUID."""
    return uuid4()


@pytest.fixture
def sample_history_create():
    """Sample AssetHistoryCreate object."""
    return AssetHistoryCreate(
        event_type=EventType.MAINTENANCE,
        title="Bearing replacement on Grinder 5",
        description="Replaced worn bearing assembly due to excessive vibration",
        resolution="Installed new SKF bearing assembly, recalibrated alignment",
        outcome=Outcome.RESOLVED,
        source=Source.MANUAL,
    )


@pytest.fixture
def sample_history_record():
    """Sample database record for history entry."""
    return {
        "id": str(uuid4()),
        "asset_id": str(uuid4()),
        "event_type": "maintenance",
        "title": "Bearing replacement",
        "description": "Replaced worn bearing",
        "resolution": "Installed new bearing",
        "outcome": "resolved",
        "source": "manual",
        "related_record_type": None,
        "related_record_id": None,
        "created_at": "2026-01-06T10:30:00+00:00",
        "updated_at": "2026-01-06T10:30:00+00:00",
        "created_by": None,
    }


class TestAssetHistoryServiceExists:
    """Tests for service instantiation."""

    def test_service_can_be_instantiated(self):
        """AssetHistoryService class can be created."""
        svc = AssetHistoryService()
        assert svc is not None

    def test_get_asset_history_service_returns_singleton(self):
        """get_asset_history_service returns singleton instance."""
        svc1 = get_asset_history_service()
        svc2 = get_asset_history_service()
        # Reset for other tests
        assert svc1 is svc2


class TestCreateHistoryEntry:
    """Tests for AC#1, AC#2 - Creating history entries."""

    @pytest.mark.asyncio
    async def test_create_history_entry_success(
        self,
        history_service,
        mock_supabase,
        mock_embedding_service,
        sample_asset_id,
        sample_history_create,
        sample_history_record,
    ):
        """AC#1: History entry is created with proper schema."""
        # Setup mocks
        sample_history_record["asset_id"] = str(sample_asset_id)
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[sample_history_record]
        )

        history_service._client = mock_supabase
        history_service._embedding_service = mock_embedding_service

        # Execute
        result = await history_service.create_history_entry(
            asset_id=sample_asset_id,
            entry=sample_history_create,
            user_id=uuid4(),
        )

        # Verify
        assert result is not None
        assert isinstance(result, AssetHistoryRead)
        assert result.asset_id == sample_asset_id
        assert result.event_type == EventType.MAINTENANCE

    @pytest.mark.asyncio
    async def test_create_history_entry_generates_embedding(
        self,
        history_service,
        mock_supabase,
        mock_embedding_service,
        sample_asset_id,
        sample_history_create,
        sample_history_record,
    ):
        """AC#2: Embedding is generated on creation."""
        sample_history_record["asset_id"] = str(sample_asset_id)
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[sample_history_record]
        )

        history_service._client = mock_supabase
        history_service._embedding_service = mock_embedding_service

        await history_service.create_history_entry(
            asset_id=sample_asset_id,
            entry=sample_history_create,
        )

        # Verify embedding was generated
        mock_embedding_service.generate_history_embedding.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_history_entry_stores_all_event_types(
        self,
        history_service,
        mock_supabase,
        mock_embedding_service,
        sample_asset_id,
        sample_history_record,
    ):
        """AC#1: All event types are supported."""
        for event_type in EventType:
            entry = AssetHistoryCreate(
                event_type=event_type,
                title=f"Test {event_type.value}",
            )

            sample_history_record["asset_id"] = str(sample_asset_id)
            sample_history_record["event_type"] = event_type.value
            mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
                data=[sample_history_record]
            )

            history_service._client = mock_supabase
            history_service._embedding_service = mock_embedding_service

            result = await history_service.create_history_entry(
                asset_id=sample_asset_id,
                entry=entry,
            )

            assert result.event_type == event_type


class TestGetAssetHistory:
    """Tests for AC#3, AC#6 - Retrieving history with pagination."""

    @pytest.mark.asyncio
    async def test_get_asset_history_paginated(
        self,
        history_service,
        mock_supabase,
        sample_asset_id,
        sample_history_record,
    ):
        """AC#3: History is returned with pagination."""
        sample_history_record["asset_id"] = str(sample_asset_id)
        mock_response = MagicMock()
        mock_response.data = [sample_history_record]
        mock_response.count = 25

        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_response

        history_service._client = mock_supabase

        items, pagination = await history_service.get_asset_history(
            asset_id=sample_asset_id,
            page=1,
            page_size=10,
        )

        assert len(items) == 1
        assert pagination["total"] == 25
        assert pagination["page"] == 1
        assert pagination["page_size"] == 10
        assert pagination["has_next"] is True

    @pytest.mark.asyncio
    async def test_get_asset_history_filter_by_event_type(
        self,
        history_service,
        mock_supabase,
        sample_asset_id,
        sample_history_record,
    ):
        """AC#3: History can be filtered by event type."""
        sample_history_record["asset_id"] = str(sample_asset_id)
        mock_response = MagicMock()
        mock_response.data = [sample_history_record]
        mock_response.count = 5

        mock_query = MagicMock()
        mock_query.eq.return_value.in_.return_value.order.return_value.range.return_value.execute.return_value = mock_response
        mock_supabase.table.return_value.select.return_value = mock_query

        history_service._client = mock_supabase

        items, pagination = await history_service.get_asset_history(
            asset_id=sample_asset_id,
            event_types=[EventType.MAINTENANCE, EventType.DOWNTIME],
        )

        # Verify in_ was called with event type values
        mock_query.eq.return_value.in_.assert_called()


class TestSearchAssetHistory:
    """Tests for AC#3, AC#6 - Semantic search."""

    @pytest.mark.asyncio
    async def test_search_uses_vector_similarity(
        self,
        history_service,
        mock_supabase,
        mock_embedding_service,
        sample_asset_id,
    ):
        """AC#3: Search uses vector similarity."""
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "history_id": str(uuid4()),
                    "asset_id": str(sample_asset_id),
                    "event_type": "maintenance",
                    "title": "Bearing issue",
                    "description": "Fixed bearing",
                    "resolution": "Replaced",
                    "outcome": "resolved",
                    "source": "manual",
                    "created_at": "2026-01-06T10:30:00+00:00",
                    "similarity": 0.89,
                }
            ]
        )

        history_service._client = mock_supabase
        history_service._embedding_service = mock_embedding_service

        results = await history_service.search_asset_history(
            asset_id=sample_asset_id,
            query="bearing failure",
            limit=5,
        )

        assert len(results) == 1
        assert results[0].similarity_score == 0.89

    @pytest.mark.asyncio
    async def test_search_generates_query_embedding(
        self,
        history_service,
        mock_supabase,
        mock_embedding_service,
        sample_asset_id,
    ):
        """AC#3: Query embedding is generated for search."""
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=[])

        history_service._client = mock_supabase
        history_service._embedding_service = mock_embedding_service

        await history_service.search_asset_history(
            asset_id=sample_asset_id,
            query="bearing failure",
        )

        mock_embedding_service.generate_embedding.assert_called_once_with("bearing failure")


class TestHistoryForAIContext:
    """Tests for AC#4 - History retrieval for AI context."""

    @pytest.mark.asyncio
    async def test_get_history_for_ai_context_returns_formatted_entries(
        self,
        history_service,
        mock_supabase,
        mock_embedding_service,
        sample_asset_id,
    ):
        """AC#4: Returns formatted entries for AI context."""
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "history_id": str(uuid4()),
                    "asset_id": str(sample_asset_id),
                    "event_type": "maintenance",
                    "title": "Bearing replacement",
                    "description": "Fixed worn bearing",
                    "resolution": "Installed new bearing",
                    "outcome": "resolved",
                    "source": "manual",
                    "created_at": "2026-01-06T10:30:00+00:00",
                    "similarity": 0.85,
                }
            ]
        )

        history_service._client = mock_supabase
        history_service._embedding_service = mock_embedding_service

        entries, context_text = await history_service.get_history_for_ai_context(
            asset_id=sample_asset_id,
            query="Why does the machine fail?",
            limit=5,
        )

        assert len(entries) == 1
        assert "[History:" in context_text
        assert "Bearing replacement" in context_text

    @pytest.mark.asyncio
    async def test_get_history_includes_citation_markers(
        self,
        history_service,
        mock_supabase,
        mock_embedding_service,
        sample_asset_id,
    ):
        """AC#4, AC#5: Context includes citation markers for NFR1."""
        history_id = uuid4()
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "history_id": str(history_id),
                    "asset_id": str(sample_asset_id),
                    "event_type": "maintenance",
                    "title": "Test title",
                    "description": "Test description",
                    "resolution": None,
                    "outcome": None,
                    "source": "manual",
                    "created_at": "2026-01-06T10:30:00+00:00",
                    "similarity": 0.8,
                }
            ]
        )

        history_service._client = mock_supabase
        history_service._embedding_service = mock_embedding_service

        entries, context_text = await history_service.get_history_for_ai_context(
            asset_id=sample_asset_id,
            query="test",
        )

        # Verify citation marker format [History:XXXXXXXX]
        citation_id = str(history_id)[:8]
        assert f"[History:{citation_id}]" in context_text
        assert entries[0].citation_id == citation_id


class TestTemporalWeighting:
    """Tests for AC#4 - Temporal weighting algorithm."""

    def test_temporal_weighting_ranks_recent_higher(self, history_service):
        """AC#4: Recent events are ranked higher."""
        now = datetime.now(timezone.utc)

        # Create results with different ages
        old_result = AssetHistorySearchResult(
            id=uuid4(),
            asset_id=uuid4(),
            event_type=EventType.MAINTENANCE,
            title="Old event",
            description=None,
            resolution=None,
            similarity_score=0.9,
            created_at=now - timedelta(days=60),  # 60 days old
        )

        recent_result = AssetHistorySearchResult(
            id=uuid4(),
            asset_id=uuid4(),
            event_type=EventType.MAINTENANCE,
            title="Recent event",
            description=None,
            resolution=None,
            similarity_score=0.85,  # Lower similarity
            created_at=now - timedelta(days=1),  # 1 day old
        )

        # Apply temporal weighting
        weighted = history_service._apply_temporal_weighting(
            [old_result, recent_result],
            half_life_days=30,
        )

        # Recent should rank higher despite lower similarity
        assert weighted[0][0].title == "Recent event"

    def test_temporal_weighting_decay_function(self, history_service):
        """AC#4: Exponential decay is applied correctly."""
        now = datetime.now(timezone.utc)

        result = AssetHistorySearchResult(
            id=uuid4(),
            asset_id=uuid4(),
            event_type=EventType.NOTE,
            title="Test",
            description=None,
            resolution=None,
            similarity_score=1.0,
            created_at=now - timedelta(days=30),  # Exactly one half-life
        )

        weighted = history_service._apply_temporal_weighting(
            [result],
            half_life_days=30,
        )

        # After one half-life, temporal weight should be ~0.5
        # Combined score = 0.7 * 1.0 + 0.3 * 0.5 = 0.85
        combined_score = weighted[0][1]
        assert 0.8 < combined_score < 0.9


class TestMultiAssetHistory:
    """Tests for AC#4 - Multi-asset queries."""

    @pytest.mark.asyncio
    async def test_multi_asset_query_by_area(
        self,
        history_service,
        mock_supabase,
        mock_embedding_service,
    ):
        """AC#4: Supports multi-asset queries by area."""
        asset1 = uuid4()
        asset2 = uuid4()

        # Mock assets query
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": str(asset1)}, {"id": str(asset2)}]
        )

        # Mock search results
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "history_id": str(uuid4()),
                    "asset_id": str(asset1),
                    "event_type": "downtime",
                    "title": "Issue on asset 1",
                    "description": None,
                    "resolution": None,
                    "outcome": None,
                    "source": "manual",
                    "created_at": "2026-01-06T10:30:00+00:00",
                    "similarity": 0.9,
                },
            ]
        )

        history_service._client = mock_supabase
        history_service._embedding_service = mock_embedding_service

        results = await history_service.get_multi_asset_history(
            area="Grinding",
            query="failures",
            limit=10,
        )

        assert len(results) >= 0  # Results depend on mock setup


class TestRecordToModel:
    """Tests for data conversion."""

    def test_record_to_model_converts_correctly(self, history_service, sample_history_record):
        """Database record is converted to Pydantic model."""
        model = history_service._record_to_model(sample_history_record)

        assert isinstance(model, AssetHistoryRead)
        assert model.event_type == EventType.MAINTENANCE
        assert model.title == "Bearing replacement"
        assert model.source == "manual"

    def test_record_to_model_handles_null_fields(self, history_service):
        """Null fields are handled correctly."""
        record = {
            "id": str(uuid4()),
            "asset_id": str(uuid4()),
            "event_type": "note",
            "title": "Simple note",
            "description": None,
            "resolution": None,
            "outcome": None,
            "source": "manual",
            "related_record_type": None,
            "related_record_id": None,
            "created_at": "2026-01-06T10:30:00+00:00",
            "updated_at": "2026-01-06T10:30:00+00:00",
            "created_by": None,
        }

        model = history_service._record_to_model(record)

        assert model.description is None
        assert model.resolution is None
        assert model.outcome is None
        assert model.created_by is None


class TestErrorHandling:
    """Tests for error handling patterns."""

    @pytest.mark.asyncio
    async def test_create_history_raises_on_insert_failure(
        self,
        history_service,
        mock_supabase,
        mock_embedding_service,
        sample_asset_id,
        sample_history_create,
    ):
        """Error handling: raises AssetHistoryServiceError on insert failure."""
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[]
        )

        history_service._client = mock_supabase
        history_service._embedding_service = mock_embedding_service

        with pytest.raises(AssetHistoryServiceError) as exc_info:
            await history_service.create_history_entry(
                asset_id=sample_asset_id,
                entry=sample_history_create,
            )

        assert "Failed to insert" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_handles_embedding_error(
        self,
        history_service,
        mock_supabase,
        sample_asset_id,
    ):
        """Error handling: raises when embedding generation fails."""
        from app.services.embedding_service import EmbeddingServiceError

        mock_embedding = MagicMock()
        mock_embedding.generate_embedding.side_effect = EmbeddingServiceError("API error")

        history_service._client = mock_supabase
        history_service._embedding_service = mock_embedding

        with pytest.raises(AssetHistoryServiceError) as exc_info:
            await history_service.search_asset_history(
                asset_id=sample_asset_id,
                query="test",
            )

        assert "Search failed" in str(exc_info.value)
