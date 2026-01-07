"""
Tests for Memory Service (Story 4.1)

AC#1: Mem0 Python SDK Integration
AC#3: User Session Memory Storage
AC#4: Asset History Memory Storage
AC#5: Memory Retrieval for Context
AC#6: Memory Service API
AC#7: OpenAI Embeddings Configuration
AC#8: LangChain Integration Preparation
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4

from app.services.memory.mem0_service import (
    MemoryService,
    MemoryServiceError,
    get_memory_service,
    memory_service,
)


@pytest.fixture
def memory_svc():
    """Create a fresh MemoryService instance for testing."""
    svc = MemoryService()
    svc.clear_cache()
    return svc


@pytest.fixture
def mock_settings():
    """Mock settings with valid Mem0 configuration."""
    mock = MagicMock()
    mock.supabase_db_url = "postgresql://test:test@localhost:5432/test"
    mock.openai_api_key = "sk-test-key"
    mock.mem0_collection_name = "memories"
    mock.mem0_embedding_dims = 1536
    mock.mem0_top_k = 5
    mock.mem0_similarity_threshold = 0.7
    mock.mem0_configured = True
    return mock


@pytest.fixture
def mock_settings_unconfigured():
    """Mock settings without Mem0 configuration."""
    mock = MagicMock()
    mock.supabase_db_url = ""
    mock.openai_api_key = ""
    mock.mem0_configured = False
    return mock


@pytest.fixture
def sample_messages():
    """Sample message list for testing."""
    return [
        {"role": "user", "content": "Why is Grinder 5 running slow?"},
        {"role": "assistant", "content": "Grinder 5 shows a 15% OEE gap..."},
    ]


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing."""
    return {
        "session_id": "session-123",
        "asset_id": "asset-456",
    }


class TestMemoryServiceExists:
    """Tests for AC#1 - Mem0 Python SDK Integration."""

    def test_memory_service_can_be_instantiated(self):
        """AC#1: MemoryService class can be created."""
        svc = MemoryService()
        assert svc is not None

    def test_get_memory_service_returns_singleton(self):
        """AC#1: get_memory_service returns singleton instance."""
        svc1 = get_memory_service()
        svc2 = get_memory_service()
        assert svc1 is svc2

    def test_module_level_singleton_exists(self):
        """AC#1: Module-level memory_service singleton exists."""
        assert memory_service is not None
        assert isinstance(memory_service, MemoryService)


class TestMemoryServiceConfiguration:
    """Tests for AC#1, AC#7 - Configuration."""

    def test_is_configured_returns_true_when_configured(self, memory_svc, mock_settings):
        """AC#1: is_configured returns True when properly configured."""
        with patch('app.services.memory.mem0_service.get_settings', return_value=mock_settings):
            assert memory_svc.is_configured() is True

    def test_is_configured_returns_false_when_unconfigured(self, memory_svc, mock_settings_unconfigured):
        """AC#1: is_configured returns False when not configured."""
        with patch('app.services.memory.mem0_service.get_settings', return_value=mock_settings_unconfigured):
            assert memory_svc.is_configured() is False

    def test_is_initialized_false_before_init(self, memory_svc):
        """AC#1: is_initialized returns False before initialization."""
        assert memory_svc.is_initialized() is False

    def test_initialize_fails_gracefully_when_unconfigured(self, memory_svc, mock_settings_unconfigured):
        """AC#1: Initialize returns False when not configured."""
        with patch('app.services.memory.mem0_service.get_settings', return_value=mock_settings_unconfigured):
            result = memory_svc.initialize()
            assert result is False
            assert memory_svc.is_initialized() is False

    @patch('app.services.memory.mem0_service.Memory')
    def test_initialize_creates_mem0_instance(self, mock_memory_class, memory_svc, mock_settings):
        """AC#1: Initialize creates Mem0 Memory instance."""
        mock_memory_instance = MagicMock()
        mock_memory_class.from_config.return_value = mock_memory_instance

        with patch('app.services.memory.mem0_service.get_settings', return_value=mock_settings):
            result = memory_svc.initialize()

        assert result is True
        assert memory_svc.is_initialized() is True
        mock_memory_class.from_config.assert_called_once()

    @patch('app.services.memory.mem0_service.Memory')
    def test_initialize_with_correct_config(self, mock_memory_class, memory_svc, mock_settings):
        """AC#1, AC#7: Initialize uses correct Supabase and OpenAI config."""
        mock_memory_class.from_config.return_value = MagicMock()

        with patch('app.services.memory.mem0_service.get_settings', return_value=mock_settings):
            memory_svc.initialize()

        # Verify the config passed to Mem0
        call_args = mock_memory_class.from_config.call_args
        config = call_args[0][0]

        # Check vector store config
        assert config["vector_store"]["provider"] == "supabase"
        assert config["vector_store"]["config"]["connection_string"] == mock_settings.supabase_db_url
        assert config["vector_store"]["config"]["collection_name"] == mock_settings.mem0_collection_name

        # Check embedder config (AC#7)
        assert config["embedder"]["provider"] == "openai"
        assert config["embedder"]["config"]["model"] == "text-embedding-ada-002"
        assert config["embedder"]["config"]["api_key"] == mock_settings.openai_api_key


class TestUserSessionMemoryStorage:
    """Tests for AC#3 - User Session Memory Storage."""

    @pytest.mark.asyncio
    @patch('app.services.memory.mem0_service.Memory')
    async def test_add_memory_stores_with_user_id(
        self, mock_memory_class, memory_svc, mock_settings, sample_messages
    ):
        """AC#3: Memory is stored with user_id from JWT claims."""
        mock_memory_instance = MagicMock()
        mock_memory_instance.add.return_value = {"id": "mem-123"}
        mock_memory_class.from_config.return_value = mock_memory_instance

        with patch('app.services.memory.mem0_service.get_settings', return_value=mock_settings):
            memory_svc.initialize()
            result = await memory_svc.add_memory(
                messages=sample_messages,
                user_id="user-123",
            )

        # Verify user_id was passed to Mem0
        mock_memory_instance.add.assert_called_once()
        call_kwargs = mock_memory_instance.add.call_args[1]
        assert call_kwargs["user_id"] == "user-123"

        # Verify result
        assert result["status"] == "stored"
        assert "id" in result

    @pytest.mark.asyncio
    @patch('app.services.memory.mem0_service.Memory')
    async def test_add_memory_includes_timestamp(
        self, mock_memory_class, memory_svc, mock_settings, sample_messages
    ):
        """AC#3: Memory metadata includes timestamp."""
        mock_memory_instance = MagicMock()
        mock_memory_instance.add.return_value = {"id": "mem-123"}
        mock_memory_class.from_config.return_value = mock_memory_instance

        with patch('app.services.memory.mem0_service.get_settings', return_value=mock_settings):
            memory_svc.initialize()
            await memory_svc.add_memory(
                messages=sample_messages,
                user_id="user-123",
            )

        # Verify timestamp in metadata
        call_kwargs = mock_memory_instance.add.call_args[1]
        assert "timestamp" in call_kwargs["metadata"]

    @pytest.mark.asyncio
    @patch('app.services.memory.mem0_service.Memory')
    async def test_add_memory_preserves_metadata(
        self, mock_memory_class, memory_svc, mock_settings, sample_messages, sample_metadata
    ):
        """AC#3: Custom metadata is preserved."""
        mock_memory_instance = MagicMock()
        mock_memory_instance.add.return_value = {"id": "mem-123"}
        mock_memory_class.from_config.return_value = mock_memory_instance

        with patch('app.services.memory.mem0_service.get_settings', return_value=mock_settings):
            memory_svc.initialize()
            await memory_svc.add_memory(
                messages=sample_messages,
                user_id="user-123",
                metadata=sample_metadata,
            )

        # Verify metadata includes custom fields
        call_kwargs = mock_memory_instance.add.call_args[1]
        assert call_kwargs["metadata"]["session_id"] == "session-123"
        assert call_kwargs["metadata"]["asset_id"] == "asset-456"


class TestAssetHistoryMemoryStorage:
    """Tests for AC#4 - Asset History Memory Storage."""

    @pytest.mark.asyncio
    @patch('app.services.memory.mem0_service.Memory')
    async def test_add_memory_with_asset_id(
        self, mock_memory_class, memory_svc, mock_settings, sample_messages
    ):
        """AC#4: Memory can be stored with asset_id in metadata."""
        mock_memory_instance = MagicMock()
        mock_memory_instance.add.return_value = {"id": "mem-123"}
        mock_memory_class.from_config.return_value = mock_memory_instance

        with patch('app.services.memory.mem0_service.get_settings', return_value=mock_settings):
            memory_svc.initialize()
            await memory_svc.add_memory(
                messages=sample_messages,
                user_id="user-123",
                metadata={"asset_id": "asset-456"},
            )

        # Verify asset_id in metadata
        call_kwargs = mock_memory_instance.add.call_args[1]
        assert call_kwargs["metadata"]["asset_id"] == "asset-456"

    @pytest.mark.asyncio
    @patch('app.services.memory.mem0_service.Memory')
    async def test_get_asset_history(
        self, mock_memory_class, memory_svc, mock_settings
    ):
        """AC#4: Asset-specific memories can be retrieved."""
        mock_memory_instance = MagicMock()
        mock_memory_instance.get_all.return_value = {
            "results": [
                {"id": "mem-1", "memory": "About Grinder 5", "metadata": {"asset_id": "asset-456"}},
                {"id": "mem-2", "memory": "About Lathe 3", "metadata": {"asset_id": "asset-789"}},
                {"id": "mem-3", "memory": "Also about Grinder 5", "metadata": {"asset_id": "asset-456"}},
            ]
        }
        mock_memory_class.from_config.return_value = mock_memory_instance

        with patch('app.services.memory.mem0_service.get_settings', return_value=mock_settings):
            memory_svc.initialize()
            results = await memory_svc.get_asset_history(
                asset_id="asset-456",
                user_id="user-123",
            )

        # Should only return memories for asset-456
        assert len(results) == 2
        assert all(m["metadata"]["asset_id"] == "asset-456" for m in results)


class TestMemoryRetrievalForContext:
    """Tests for AC#5 - Memory Retrieval for Context."""

    @pytest.mark.asyncio
    @patch('app.services.memory.mem0_service.Memory')
    async def test_search_memory_uses_semantic_similarity(
        self, mock_memory_class, memory_svc, mock_settings
    ):
        """AC#5: Memory search uses semantic similarity."""
        mock_memory_instance = MagicMock()
        mock_memory_instance.search.return_value = {
            "results": [
                {"id": "mem-1", "memory": "Grinder 5 issue", "score": 0.9},
                {"id": "mem-2", "memory": "Grinder performance", "score": 0.85},
            ]
        }
        mock_memory_class.from_config.return_value = mock_memory_instance

        with patch('app.services.memory.mem0_service.get_settings', return_value=mock_settings):
            memory_svc.initialize()
            results = await memory_svc.search_memory(
                query="Grinder 5 problems",
                user_id="user-123",
            )

        # Verify search was called with query
        mock_memory_instance.search.assert_called_once()
        call_args = mock_memory_instance.search.call_args
        assert call_args[0][0] == "Grinder 5 problems"

        # Verify results returned
        assert len(results) == 2

    @pytest.mark.asyncio
    @patch('app.services.memory.mem0_service.Memory')
    async def test_search_memory_filters_by_user_id(
        self, mock_memory_class, memory_svc, mock_settings
    ):
        """AC#5: Memory search filters by user_id."""
        mock_memory_instance = MagicMock()
        mock_memory_instance.search.return_value = {"results": []}
        mock_memory_class.from_config.return_value = mock_memory_instance

        with patch('app.services.memory.mem0_service.get_settings', return_value=mock_settings):
            memory_svc.initialize()
            await memory_svc.search_memory(
                query="test",
                user_id="user-123",
            )

        # Verify user_id was passed
        call_kwargs = mock_memory_instance.search.call_args[1]
        assert call_kwargs["user_id"] == "user-123"

    @pytest.mark.asyncio
    @patch('app.services.memory.mem0_service.Memory')
    async def test_search_memory_respects_limit(
        self, mock_memory_class, memory_svc, mock_settings
    ):
        """AC#5: Top-k retrieval is configurable."""
        mock_memory_instance = MagicMock()
        mock_memory_instance.search.return_value = {"results": []}
        mock_memory_class.from_config.return_value = mock_memory_instance

        with patch('app.services.memory.mem0_service.get_settings', return_value=mock_settings):
            memory_svc.initialize()
            await memory_svc.search_memory(
                query="test",
                user_id="user-123",
                limit=10,
            )

        # Verify limit was passed
        call_kwargs = mock_memory_instance.search.call_args[1]
        assert call_kwargs["limit"] == 10

    @pytest.mark.asyncio
    @patch('app.services.memory.mem0_service.Memory')
    async def test_search_memory_filters_by_threshold(
        self, mock_memory_class, memory_svc, mock_settings
    ):
        """AC#5: Results are filtered by similarity threshold."""
        mock_memory_instance = MagicMock()
        mock_memory_instance.search.return_value = {
            "results": [
                {"id": "mem-1", "memory": "High match", "score": 0.9},
                {"id": "mem-2", "memory": "Medium match", "score": 0.6},  # Below threshold
            ]
        }
        mock_memory_class.from_config.return_value = mock_memory_instance

        with patch('app.services.memory.mem0_service.get_settings', return_value=mock_settings):
            memory_svc.initialize()
            results = await memory_svc.search_memory(
                query="test",
                user_id="user-123",
                threshold=0.7,
            )

        # Only high match should be returned
        assert len(results) == 1
        assert results[0]["score"] == 0.9

    @pytest.mark.asyncio
    @patch('app.services.memory.mem0_service.Memory')
    async def test_search_memory_graceful_degradation(
        self, mock_memory_class, memory_svc, mock_settings
    ):
        """AC#5: Search returns empty list on error (graceful degradation)."""
        mock_memory_instance = MagicMock()
        mock_memory_instance.search.side_effect = Exception("Search failed")
        mock_memory_class.from_config.return_value = mock_memory_instance

        with patch('app.services.memory.mem0_service.get_settings', return_value=mock_settings):
            memory_svc.initialize()
            results = await memory_svc.search_memory(
                query="test",
                user_id="user-123",
            )

        # Should return empty list, not raise exception
        assert results == []


class TestMemoryServiceAPI:
    """Tests for AC#6 - Memory Service API."""

    @pytest.mark.asyncio
    @patch('app.services.memory.mem0_service.Memory')
    async def test_get_all_memories(
        self, mock_memory_class, memory_svc, mock_settings
    ):
        """AC#6: get_all_memories() method works."""
        mock_memory_instance = MagicMock()
        mock_memory_instance.get_all.return_value = {
            "results": [
                {"id": "mem-1", "memory": "Memory 1"},
                {"id": "mem-2", "memory": "Memory 2"},
            ]
        }
        mock_memory_class.from_config.return_value = mock_memory_instance

        with patch('app.services.memory.mem0_service.get_settings', return_value=mock_settings):
            memory_svc.initialize()
            results = await memory_svc.get_all_memories(user_id="user-123")

        assert len(results) == 2
        mock_memory_instance.get_all.assert_called_once_with(user_id="user-123")

    @pytest.mark.asyncio
    async def test_add_memory_raises_when_not_initialized(self, memory_svc, mock_settings_unconfigured):
        """AC#6: add_memory raises MemoryServiceError when not configured."""
        with patch('app.services.memory.mem0_service.get_settings', return_value=mock_settings_unconfigured):
            with pytest.raises(MemoryServiceError):
                await memory_svc.add_memory(
                    messages=[{"role": "user", "content": "test"}],
                    user_id="user-123",
                )

    def test_clear_cache(self, memory_svc):
        """AC#6: clear_cache works."""
        memory_svc._settings = MagicMock()
        memory_svc.clear_cache()
        assert memory_svc._settings is None


class TestLangChainIntegrationPreparation:
    """Tests for AC#8 - LangChain Integration Preparation."""

    @pytest.mark.asyncio
    @patch('app.services.memory.mem0_service.Memory')
    async def test_get_context_for_query_returns_langchain_format(
        self, mock_memory_class, memory_svc, mock_settings
    ):
        """AC#8: Context is returned in LangChain-compatible format."""
        mock_memory_instance = MagicMock()
        mock_memory_instance.search.return_value = {
            "results": [
                {"id": "mem-1", "memory": "Previous question about Grinder", "score": 0.9},
            ]
        }
        mock_memory_instance.get_all.return_value = {"results": []}
        mock_memory_class.from_config.return_value = mock_memory_instance

        with patch('app.services.memory.mem0_service.get_settings', return_value=mock_settings):
            memory_svc.initialize()
            context = await memory_svc.get_context_for_query(
                query="What about Grinder 5?",
                user_id="user-123",
            )

        # Should be list of message dicts
        assert isinstance(context, list)
        assert len(context) == 1

        # Each message should have role and content
        msg = context[0]
        assert "role" in msg
        assert "content" in msg
        assert msg["role"] == "system"
        assert "Previous context:" in msg["content"]

    @pytest.mark.asyncio
    @patch('app.services.memory.mem0_service.Memory')
    async def test_get_context_includes_asset_memories(
        self, mock_memory_class, memory_svc, mock_settings
    ):
        """AC#8: Context includes asset-specific memories when asset_id provided."""
        mock_memory_instance = MagicMock()
        mock_memory_instance.search.return_value = {
            "results": [
                {"id": "mem-1", "memory": "General memory", "score": 0.9},
            ]
        }
        mock_memory_instance.get_all.return_value = {
            "results": [
                {"id": "mem-2", "memory": "Asset memory", "metadata": {"asset_id": "asset-456"}},
            ]
        }
        mock_memory_class.from_config.return_value = mock_memory_instance

        with patch('app.services.memory.mem0_service.get_settings', return_value=mock_settings):
            memory_svc.initialize()
            context = await memory_svc.get_context_for_query(
                query="What about Grinder 5?",
                user_id="user-123",
                asset_id="asset-456",
            )

        # Should include both general and asset-specific memories
        assert len(context) == 2


class TestErrorHandling:
    """Tests for error handling patterns."""

    @pytest.mark.asyncio
    @patch('app.services.memory.mem0_service.Memory')
    async def test_add_memory_handles_mem0_error(
        self, mock_memory_class, memory_svc, mock_settings, sample_messages
    ):
        """Error handling: add_memory raises MemoryServiceError on failure."""
        mock_memory_instance = MagicMock()
        mock_memory_instance.add.side_effect = Exception("Mem0 error")
        mock_memory_class.from_config.return_value = mock_memory_instance

        with patch('app.services.memory.mem0_service.get_settings', return_value=mock_settings):
            memory_svc.initialize()
            with pytest.raises(MemoryServiceError) as exc_info:
                await memory_svc.add_memory(
                    messages=sample_messages,
                    user_id="user-123",
                )

        assert "Failed to store memory" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch('app.services.memory.mem0_service.Memory')
    async def test_get_all_memories_handles_error(
        self, mock_memory_class, memory_svc, mock_settings
    ):
        """Error handling: get_all_memories returns empty on error."""
        mock_memory_instance = MagicMock()
        mock_memory_instance.get_all.side_effect = Exception("Error")
        mock_memory_class.from_config.return_value = mock_memory_instance

        with patch('app.services.memory.mem0_service.get_settings', return_value=mock_settings):
            memory_svc.initialize()
            results = await memory_svc.get_all_memories(user_id="user-123")

        # Should return empty list, not raise
        assert results == []
