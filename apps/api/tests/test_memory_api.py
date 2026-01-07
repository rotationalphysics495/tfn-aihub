"""
Tests for Memory API Endpoints (Story 4.1)

AC#6: Memory Service API
AC#7: Protected endpoints with Supabase JWT authentication
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import status

from app.models.memory import (
    MemoryInput,
    MemoryMessage,
    MemoryMetadata,
)


@pytest.fixture
def mock_memory_service():
    """Mock MemoryService for API tests."""
    with patch('app.api.memory.get_memory_service') as mock_get:
        mock_service = MagicMock()
        mock_service.add_memory = AsyncMock(return_value={
            "id": "mem-123",
            "status": "stored",
        })
        mock_service.search_memory = AsyncMock(return_value=[
            {"id": "mem-1", "memory": "Test memory", "score": 0.9, "metadata": {}},
        ])
        mock_service.get_all_memories = AsyncMock(return_value=[
            {"id": "mem-1", "memory": "Memory 1", "metadata": {}},
            {"id": "mem-2", "memory": "Memory 2", "metadata": {}},
        ])
        mock_service.get_asset_history = AsyncMock(return_value=[
            {"id": "mem-1", "memory": "Asset memory", "metadata": {"asset_id": "asset-456"}},
        ])
        mock_service.get_context_for_query = AsyncMock(return_value=[
            {"role": "system", "content": "Previous context: test"},
        ])
        mock_service.is_configured = MagicMock(return_value=True)
        mock_service.is_initialized = MagicMock(return_value=True)
        mock_get.return_value = mock_service
        yield mock_service


@pytest.fixture
def mock_asset_detector():
    """Mock AssetDetector for API tests."""
    with patch('app.api.memory.extract_asset_from_message') as mock_extract:
        mock_extract.return_value = None
        yield mock_extract


class TestStoreMemoryEndpoint:
    """Tests for POST /api/memory endpoint."""

    def test_store_memory_requires_auth(self, client):
        """AC#7: Store memory requires authentication."""
        response = client.post(
            "/api/memory",
            json={
                "messages": [
                    {"role": "user", "content": "Test message"}
                ]
            }
        )

        # 401 Unauthorized when no token provided
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_store_memory_with_auth(
        self, client, mock_verify_jwt, mock_memory_service, mock_asset_detector
    ):
        """AC#6: Store memory with valid auth."""
        response = client.post(
            "/api/memory",
            headers={"Authorization": "Bearer valid-token"},
            json={
                "messages": [
                    {"role": "user", "content": "Why is Grinder 5 slow?"},
                    {"role": "assistant", "content": "Grinder 5 shows issues..."}
                ],
                "metadata": {
                    "session_id": "session-123"
                }
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["status"] == "stored"
        assert "id" in data

    def test_store_memory_validates_messages(
        self, client, mock_verify_jwt, mock_memory_service, mock_asset_detector
    ):
        """AC#6: Store memory validates message format."""
        response = client.post(
            "/api/memory",
            headers={"Authorization": "Bearer valid-token"},
            json={
                "messages": []  # Empty messages should fail
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestSearchMemoriesEndpoint:
    """Tests for GET /api/memory/search endpoint."""

    def test_search_memories_requires_auth(self, client):
        """AC#7: Search memories requires authentication."""
        response = client.get("/api/memory/search?query=test")

        # 401 Unauthorized when no token provided
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_search_memories_with_auth(
        self, client, mock_verify_jwt, mock_memory_service
    ):
        """AC#5: Search memories returns results."""
        response = client.get(
            "/api/memory/search?query=Grinder%205",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "query" in data
        assert "count" in data
        assert "memories" in data
        assert data["query"] == "Grinder 5"

    def test_search_memories_with_limit(
        self, client, mock_verify_jwt, mock_memory_service
    ):
        """AC#5: Search respects limit parameter."""
        response = client.get(
            "/api/memory/search?query=test&limit=10",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == status.HTTP_200_OK
        mock_memory_service.search_memory.assert_called()

    def test_search_memories_with_threshold(
        self, client, mock_verify_jwt, mock_memory_service
    ):
        """AC#5: Search respects threshold parameter."""
        response = client.get(
            "/api/memory/search?query=test&threshold=0.8",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == status.HTTP_200_OK

    def test_search_memories_with_asset_filter(
        self, client, mock_verify_jwt, mock_memory_service
    ):
        """AC#4: Search can filter by asset_id."""
        response = client.get(
            "/api/memory/search?query=test&asset_id=asset-456",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == status.HTTP_200_OK


class TestGetAllMemoriesEndpoint:
    """Tests for GET /api/memory endpoint."""

    def test_get_all_memories_requires_auth(self, client):
        """AC#7: Get all memories requires authentication."""
        response = client.get("/api/memory")

        # 401 Unauthorized when no token provided
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_all_memories_with_auth(
        self, client, mock_verify_jwt, mock_memory_service
    ):
        """AC#6: Get all memories returns user memories."""
        response = client.get(
            "/api/memory",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "user_id" in data
        assert "count" in data
        assert "memories" in data
        assert data["count"] == 2

    def test_get_all_memories_with_limit(
        self, client, mock_verify_jwt, mock_memory_service
    ):
        """AC#6: Get all memories respects limit."""
        response = client.get(
            "/api/memory?limit=10",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == status.HTTP_200_OK


class TestGetAssetHistoryEndpoint:
    """Tests for GET /api/memory/asset/{asset_id} endpoint."""

    def test_get_asset_history_requires_auth(self, client):
        """AC#7: Get asset history requires authentication."""
        response = client.get("/api/memory/asset/asset-456")

        # 401 Unauthorized when no token provided
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_asset_history_with_auth(
        self, client, mock_verify_jwt, mock_memory_service
    ):
        """AC#4: Get asset history returns asset-specific memories."""
        with patch('app.api.memory.get_asset_detector') as mock_get_detector:
            mock_detector = MagicMock()
            mock_detector.get_asset_info = AsyncMock(return_value={"name": "Grinder 5"})
            mock_get_detector.return_value = mock_detector

            response = client.get(
                "/api/memory/asset/asset-456",
                headers={"Authorization": "Bearer valid-token"},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["asset_id"] == "asset-456"
        assert "count" in data
        assert "memories" in data


class TestGetContextEndpoint:
    """Tests for GET /api/memory/context endpoint."""

    def test_get_context_requires_auth(self, client):
        """AC#7: Get context requires authentication."""
        response = client.get("/api/memory/context?query=test")

        # 401 Unauthorized when no token provided
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_context_with_auth(
        self, client, mock_verify_jwt, mock_memory_service
    ):
        """AC#8: Get context returns LangChain-compatible format."""
        response = client.get(
            "/api/memory/context?query=What%20about%20Grinder%205",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "query" in data
        assert "context" in data

        # Verify LangChain format
        if data["context"]:
            msg = data["context"][0]
            assert "role" in msg
            assert "content" in msg

    def test_get_context_with_asset_id(
        self, client, mock_verify_jwt, mock_memory_service
    ):
        """AC#8: Get context can include asset-specific memories."""
        response = client.get(
            "/api/memory/context?query=test&asset_id=asset-456",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == status.HTTP_200_OK


class TestMemoryStatusEndpoint:
    """Tests for GET /api/memory/status endpoint."""

    def test_get_memory_status(self, client, mock_memory_service):
        """Status endpoint returns service status."""
        response = client.get("/api/memory/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "configured" in data
        assert "initialized" in data
        assert "status" in data


class TestErrorHandling:
    """Tests for error handling in API endpoints."""

    def test_store_memory_handles_service_error(
        self, client, mock_verify_jwt, mock_asset_detector
    ):
        """AC#6: Store memory handles service errors gracefully."""
        from app.services.memory import MemoryServiceError

        with patch('app.api.memory.get_memory_service') as mock_get:
            mock_service = MagicMock()
            mock_service.add_memory = AsyncMock(
                side_effect=MemoryServiceError("Service error")
            )
            mock_get.return_value = mock_service

            response = client.post(
                "/api/memory",
                headers={"Authorization": "Bearer valid-token"},
                json={
                    "messages": [
                        {"role": "user", "content": "Test"}
                    ]
                }
            )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_search_returns_empty_on_error(
        self, client, mock_verify_jwt
    ):
        """AC#6: Search returns empty results on error (graceful degradation)."""
        with patch('app.api.memory.get_memory_service') as mock_get:
            mock_service = MagicMock()
            mock_service.search_memory = AsyncMock(side_effect=Exception("Error"))
            mock_get.return_value = mock_service

            response = client.get(
                "/api/memory/search?query=test",
                headers={"Authorization": "Bearer valid-token"},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] == 0
        assert data["memories"] == []


class TestDataValidation:
    """Tests for request/response data validation."""

    def test_store_memory_validates_role(
        self, client, mock_verify_jwt, mock_memory_service, mock_asset_detector
    ):
        """Validates message role format."""
        response = client.post(
            "/api/memory",
            headers={"Authorization": "Bearer valid-token"},
            json={
                "messages": [
                    {"role": "user", "content": "Valid message"}
                ]
            }
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_store_memory_rejects_empty_content(
        self, client, mock_verify_jwt, mock_memory_service, mock_asset_detector
    ):
        """Rejects messages with empty content."""
        response = client.post(
            "/api/memory",
            headers={"Authorization": "Bearer valid-token"},
            json={
                "messages": [
                    {"role": "user", "content": ""}  # Empty content
                ]
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_validates_query_length(self, client, mock_verify_jwt):
        """Validates query minimum length."""
        response = client.get(
            "/api/memory/search?query=",  # Empty query
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_validates_limit_range(self, client, mock_verify_jwt):
        """Validates limit is within range."""
        response = client.get(
            "/api/memory/search?query=test&limit=100",  # Too high
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_validates_threshold_range(self, client, mock_verify_jwt):
        """Validates threshold is within range."""
        response = client.get(
            "/api/memory/search?query=test&threshold=1.5",  # Too high
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
