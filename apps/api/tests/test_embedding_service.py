"""
Tests for Embedding Service (Story 4.4)

AC#1: Vector embeddings generated for semantic search
AC#7: Integrate OpenAI text-embedding-3-small
"""

import pytest
from unittest.mock import patch, MagicMock

from app.services.embedding_service import (
    EmbeddingService,
    EmbeddingServiceError,
    get_embedding_service,
    embedding_service,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSIONS,
)


@pytest.fixture
def emb_service():
    """Create a fresh EmbeddingService instance for testing."""
    svc = EmbeddingService()
    svc.clear_cache()
    return svc


@pytest.fixture
def mock_settings():
    """Mock settings with valid OpenAI configuration."""
    mock = MagicMock()
    mock.openai_api_key = "sk-test-key"
    return mock


@pytest.fixture
def mock_settings_unconfigured():
    """Mock settings without OpenAI configuration."""
    mock = MagicMock()
    mock.openai_api_key = ""
    return mock


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI embeddings response."""
    mock_data = MagicMock()
    mock_data.embedding = [0.1] * 1536

    mock_response = MagicMock()
    mock_response.data = [mock_data]

    return mock_response


class TestEmbeddingServiceExists:
    """Tests for AC#7 - Service instantiation."""

    def test_service_can_be_instantiated(self):
        """EmbeddingService class can be created."""
        svc = EmbeddingService()
        assert svc is not None

    def test_get_embedding_service_returns_singleton(self):
        """get_embedding_service returns singleton instance."""
        svc1 = get_embedding_service()
        svc2 = get_embedding_service()
        assert svc1 is svc2

    def test_module_level_singleton_exists(self):
        """Module-level embedding_service singleton exists."""
        assert embedding_service is not None
        assert isinstance(embedding_service, EmbeddingService)


class TestEmbeddingServiceConfiguration:
    """Tests for AC#7 - Configuration."""

    def test_is_configured_returns_true_when_api_key_set(self, emb_service, mock_settings):
        """is_configured returns True when OpenAI API key is set."""
        with patch('app.services.embedding_service.get_settings', return_value=mock_settings):
            assert emb_service.is_configured() is True

    def test_is_configured_returns_false_when_no_api_key(self, emb_service, mock_settings_unconfigured):
        """is_configured returns False when no API key."""
        with patch('app.services.embedding_service.get_settings', return_value=mock_settings_unconfigured):
            assert emb_service.is_configured() is False

    def test_uses_correct_embedding_model(self):
        """AC#7: Uses text-embedding-3-small model."""
        assert EMBEDDING_MODEL == "text-embedding-3-small"
        assert EMBEDDING_DIMENSIONS == 1536


class TestGenerateEmbedding:
    """Tests for AC#1, AC#7 - Embedding generation."""

    @patch('app.services.embedding_service.OpenAI')
    def test_generate_embedding_calls_openai(
        self, mock_openai_class, emb_service, mock_settings, mock_openai_response
    ):
        """AC#7: Calls OpenAI embeddings API."""
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_openai_response
        mock_openai_class.return_value = mock_client

        with patch('app.services.embedding_service.get_settings', return_value=mock_settings):
            result = emb_service.generate_embedding("Test text")

        mock_client.embeddings.create.assert_called_once()
        call_kwargs = mock_client.embeddings.create.call_args[1]
        assert call_kwargs["model"] == "text-embedding-3-small"
        assert call_kwargs["input"] == "Test text"

    @patch('app.services.embedding_service.OpenAI')
    def test_generate_embedding_returns_1536_dimensions(
        self, mock_openai_class, emb_service, mock_settings, mock_openai_response
    ):
        """AC#7: Returns 1536-dimensional vector."""
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_openai_response
        mock_openai_class.return_value = mock_client

        with patch('app.services.embedding_service.get_settings', return_value=mock_settings):
            result = emb_service.generate_embedding("Test text")

        assert len(result) == 1536
        assert all(isinstance(x, float) for x in result)

    def test_generate_embedding_fails_on_empty_text(self, emb_service):
        """Raises error for empty text."""
        with pytest.raises(EmbeddingServiceError) as exc_info:
            emb_service.generate_embedding("")

        assert "empty text" in str(exc_info.value).lower()

    def test_generate_embedding_fails_on_whitespace_only(self, emb_service):
        """Raises error for whitespace-only text."""
        with pytest.raises(EmbeddingServiceError) as exc_info:
            emb_service.generate_embedding("   \n\t  ")

        assert "empty text" in str(exc_info.value).lower()

    @patch('app.services.embedding_service.OpenAI')
    def test_generate_embedding_raises_on_unconfigured(
        self, mock_openai_class, emb_service, mock_settings_unconfigured
    ):
        """Raises error when not configured."""
        with patch('app.services.embedding_service.get_settings', return_value=mock_settings_unconfigured):
            with pytest.raises(EmbeddingServiceError) as exc_info:
                emb_service.generate_embedding("Test text")

        assert "not configured" in str(exc_info.value).lower()


class TestGenerateHistoryEmbedding:
    """Tests for AC#1 - History-specific embeddings."""

    @patch('app.services.embedding_service.OpenAI')
    def test_generate_history_embedding_combines_fields(
        self, mock_openai_class, emb_service, mock_settings, mock_openai_response
    ):
        """AC#1: Combines title + description + resolution for embedding."""
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_openai_response
        mock_openai_class.return_value = mock_client

        with patch('app.services.embedding_service.get_settings', return_value=mock_settings):
            emb_service.generate_history_embedding(
                title="Bearing replacement",
                description="Fixed worn bearing assembly",
                resolution="Installed new SKF bearing",
                event_type="maintenance",
            )

        call_kwargs = mock_client.embeddings.create.call_args[1]
        input_text = call_kwargs["input"]

        assert "[MAINTENANCE]" in input_text
        assert "Bearing replacement" in input_text
        assert "Fixed worn bearing" in input_text
        assert "Resolution: Installed new SKF bearing" in input_text

    @patch('app.services.embedding_service.OpenAI')
    def test_generate_history_embedding_handles_missing_fields(
        self, mock_openai_class, emb_service, mock_settings, mock_openai_response
    ):
        """Handles missing optional fields gracefully."""
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_openai_response
        mock_openai_class.return_value = mock_client

        with patch('app.services.embedding_service.get_settings', return_value=mock_settings):
            result = emb_service.generate_history_embedding(
                title="Simple note",
                description=None,
                resolution=None,
                event_type=None,
            )

        assert len(result) == 1536


class TestBatchEmbeddings:
    """Tests for batch embedding generation."""

    @patch('app.services.embedding_service.OpenAI')
    def test_generate_batch_embeddings_processes_multiple(
        self, mock_openai_class, emb_service, mock_settings
    ):
        """Batch generation processes multiple texts."""
        mock_data1 = MagicMock()
        mock_data1.embedding = [0.1] * 1536
        mock_data2 = MagicMock()
        mock_data2.embedding = [0.2] * 1536

        mock_response = MagicMock()
        mock_response.data = [mock_data1, mock_data2]

        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        with patch('app.services.embedding_service.get_settings', return_value=mock_settings):
            results = emb_service.generate_batch_embeddings(["Text 1", "Text 2"])

        assert len(results) == 2
        assert results[0][0] == 0.1
        assert results[1][0] == 0.2

    def test_generate_batch_embeddings_handles_empty_list(self, emb_service):
        """Returns empty list for empty input."""
        result = emb_service.generate_batch_embeddings([])
        assert result == []

    def test_generate_batch_embeddings_raises_on_all_empty_texts(self, emb_service):
        """Raises error when all texts are empty."""
        with pytest.raises(EmbeddingServiceError) as exc_info:
            emb_service.generate_batch_embeddings(["", "   ", "\n"])

        assert "No valid texts" in str(exc_info.value)


class TestErrorHandling:
    """Tests for error handling patterns."""

    @patch('app.services.embedding_service.OpenAI')
    def test_handles_openai_api_error(self, mock_openai_class, emb_service, mock_settings):
        """Handles OpenAI API errors gracefully."""
        from openai import OpenAIError

        mock_client = MagicMock()
        mock_client.embeddings.create.side_effect = OpenAIError("API rate limit")
        mock_openai_class.return_value = mock_client

        with patch('app.services.embedding_service.get_settings', return_value=mock_settings):
            with pytest.raises(EmbeddingServiceError) as exc_info:
                emb_service.generate_embedding("Test text")

        assert "OpenAI API error" in str(exc_info.value)

    def test_clear_cache_resets_state(self, emb_service):
        """clear_cache resets internal state."""
        emb_service._settings = MagicMock()
        emb_service._client = MagicMock()

        emb_service.clear_cache()

        assert emb_service._settings is None
        assert emb_service._client is None
