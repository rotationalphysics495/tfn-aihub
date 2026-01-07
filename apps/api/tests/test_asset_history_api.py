"""
Tests for Asset History API Endpoints (Story 4.4)

AC#3: History Storage API
AC#5: Protected by Supabase Auth JWT validation
AC#6: Performance Requirements
"""

import pytest
from uuid import uuid4, UUID
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from fastapi import status


@pytest.fixture
def sample_asset_id():
    """Sample asset UUID."""
    return str(uuid4())


@pytest.fixture
def sample_history_entry():
    """Sample history entry request payload."""
    return {
        "event_type": "maintenance",
        "title": "Bearing replacement on Grinder 5",
        "description": "Replaced worn bearing assembly due to excessive vibration",
        "resolution": "Installed new SKF bearing assembly",
        "outcome": "resolved",
        "source": "manual",
    }


@pytest.fixture
def mock_history_service():
    """Mock AssetHistoryService."""
    with patch('app.api.asset_history.get_asset_history_service') as mock_get:
        mock_service = MagicMock()
        mock_get.return_value = mock_service
        yield mock_service


@pytest.fixture
def mock_context_service():
    """Mock AIContextService."""
    with patch('app.api.asset_history.get_ai_context_service') as mock_get:
        mock_service = MagicMock()
        mock_get.return_value = mock_service
        yield mock_service


@pytest.fixture
def mock_mem0_service():
    """Mock Mem0AssetService."""
    with patch('app.api.asset_history.get_mem0_asset_service') as mock_get:
        mock_service = MagicMock()
        mock_service.is_configured.return_value = False
        mock_get.return_value = mock_service
        yield mock_service


class TestCreateHistoryEntry:
    """Tests for POST /api/assets/{asset_id}/history"""

    def test_create_history_requires_authentication(
        self,
        client,
        sample_asset_id,
        sample_history_entry,
    ):
        """AC#5: Endpoint requires JWT authentication."""
        response = client.post(
            f"/api/assets/{sample_asset_id}/history",
            json=sample_history_entry,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_history_success(
        self,
        client,
        mock_verify_jwt,
        sample_asset_id,
        sample_history_entry,
        mock_history_service,
        mock_mem0_service,
    ):
        """AC#3: Creates history entry successfully."""
        from app.models.asset_history import AssetHistoryRead, EventType, Source

        created_id = uuid4()
        mock_history_service.create_history_entry = AsyncMock(
            return_value=AssetHistoryRead(
                id=created_id,
                asset_id=UUID(sample_asset_id),
                event_type=EventType.MAINTENANCE,
                title="Bearing replacement",
                description="Test",
                resolution="Fixed",
                outcome="resolved",
                source=Source.MANUAL,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )

        response = client.post(
            f"/api/assets/{sample_asset_id}/history",
            json=sample_history_entry,
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["status"] == "created"
        assert "id" in data

    def test_create_history_validates_event_type(
        self,
        client,
        mock_verify_jwt,
        sample_asset_id,
        mock_history_service,
        mock_mem0_service,
    ):
        """AC#3: Validates event_type enum."""
        invalid_entry = {
            "event_type": "invalid_type",
            "title": "Test",
        }

        response = client.post(
            f"/api/assets/{sample_asset_id}/history",
            json=invalid_entry,
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetAssetHistory:
    """Tests for GET /api/assets/{asset_id}/history"""

    def test_get_history_requires_authentication(
        self,
        client,
        sample_asset_id,
    ):
        """AC#5: Endpoint requires JWT authentication."""
        response = client.get(f"/api/assets/{sample_asset_id}/history")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_history_returns_paginated_results(
        self,
        client,
        mock_verify_jwt,
        sample_asset_id,
        mock_history_service,
    ):
        """AC#3: Returns paginated history entries."""
        from app.models.asset_history import AssetHistoryRead, EventType, Source

        mock_history_service.get_asset_history = AsyncMock(
            return_value=(
                [
                    AssetHistoryRead(
                        id=uuid4(),
                        asset_id=UUID(sample_asset_id),
                        event_type=EventType.MAINTENANCE,
                        title="Test entry",
                        description=None,
                        resolution=None,
                        outcome=None,
                        source=Source.MANUAL,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                ],
                {"total": 25, "page": 1, "page_size": 10, "has_next": True},
            )
        )

        response = client.get(
            f"/api/assets/{sample_asset_id}/history",
            headers={"Authorization": "Bearer test-token"},
            params={"page": 1, "page_size": 10},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "pagination" in data
        assert data["pagination"]["total"] == 25
        assert data["pagination"]["has_next"] is True

    def test_get_history_supports_event_type_filter(
        self,
        client,
        mock_verify_jwt,
        sample_asset_id,
        mock_history_service,
    ):
        """AC#3: Supports filtering by event type."""
        mock_history_service.get_asset_history = AsyncMock(
            return_value=([], {"total": 0, "page": 1, "page_size": 10, "has_next": False})
        )

        response = client.get(
            f"/api/assets/{sample_asset_id}/history",
            headers={"Authorization": "Bearer test-token"},
            params={"event_type": ["maintenance", "downtime"]},
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify filter was passed to service
        call_kwargs = mock_history_service.get_asset_history.call_args[1]
        assert "event_types" in call_kwargs


class TestSearchAssetHistory:
    """Tests for GET /api/assets/{asset_id}/history/search"""

    def test_search_requires_authentication(
        self,
        client,
        sample_asset_id,
    ):
        """AC#5: Endpoint requires JWT authentication."""
        response = client.get(
            f"/api/assets/{sample_asset_id}/history/search",
            params={"q": "bearing failure"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_search_returns_ranked_results(
        self,
        client,
        mock_verify_jwt,
        sample_asset_id,
        mock_history_service,
    ):
        """AC#3: Returns results with similarity scores."""
        from app.models.asset_history import AssetHistorySearchResult, EventType

        mock_history_service.search_asset_history = AsyncMock(
            return_value=[
                AssetHistorySearchResult(
                    id=uuid4(),
                    asset_id=UUID(sample_asset_id),
                    event_type=EventType.MAINTENANCE,
                    title="Bearing issue",
                    description="Fixed bearing",
                    resolution="Replaced",
                    similarity_score=0.89,
                    created_at=datetime.now(timezone.utc),
                )
            ]
        )

        response = client.get(
            f"/api/assets/{sample_asset_id}/history/search",
            headers={"Authorization": "Bearer test-token"},
            params={"q": "bearing failure"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["query"] == "bearing failure"
        assert len(data["results"]) == 1
        assert data["results"][0]["similarity_score"] == 0.89

    def test_search_requires_query_parameter(
        self,
        client,
        mock_verify_jwt,
        sample_asset_id,
    ):
        """AC#3: Query parameter is required."""
        response = client.get(
            f"/api/assets/{sample_asset_id}/history/search",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetAIContext:
    """Tests for GET /api/assets/{asset_id}/history/context"""

    def test_context_requires_authentication(
        self,
        client,
        sample_asset_id,
    ):
        """AC#5: Endpoint requires JWT authentication."""
        response = client.get(
            f"/api/assets/{sample_asset_id}/history/context",
            params={"query": "Why does it fail?"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_context_returns_formatted_output(
        self,
        client,
        mock_verify_jwt,
        sample_asset_id,
        mock_context_service,
    ):
        """AC#4: Returns formatted context for LLM."""
        from app.models.asset_history import AIContextResponse, AssetHistoryForAI, EventType

        mock_context_service.get_context_for_asset = AsyncMock(
            return_value=AIContextResponse(
                asset_id=UUID(sample_asset_id),
                asset_name="Grinder 5",
                query="Why does it fail?",
                context_text="[History:a1b2c3d4] 2026-01-06: Bearing issue...",
                entries=[
                    AssetHistoryForAI(
                        citation_id="a1b2c3d4",
                        date="2026-01-06",
                        event_type=EventType.MAINTENANCE,
                        title="Bearing issue",
                        summary="Fixed bearing problem",
                        relevance_score=0.85,
                    )
                ],
                entry_count=1,
            )
        )

        response = client.get(
            f"/api/assets/{sample_asset_id}/history/context",
            headers={"Authorization": "Bearer test-token"},
            params={"query": "Why does it fail?"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["asset_name"] == "Grinder 5"
        assert "[History:" in data["context_text"]
        assert data["entry_count"] == 1


class TestMultiAssetSearch:
    """Tests for GET /api/assets/history/multi-asset"""

    def test_multi_asset_requires_authentication(
        self,
        client,
    ):
        """AC#5: Endpoint requires JWT authentication."""
        response = client.get(
            "/api/assets/history/multi-asset",
            params={"q": "failures"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_multi_asset_supports_area_filter(
        self,
        client,
        mock_verify_jwt,
        mock_history_service,
    ):
        """AC#4: Supports filtering by area."""
        mock_history_service.get_multi_asset_history = AsyncMock(return_value=[])

        response = client.get(
            "/api/assets/history/multi-asset",
            headers={"Authorization": "Bearer test-token"},
            params={"q": "failures", "area": "Grinding"},
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify area was passed
        call_kwargs = mock_history_service.get_multi_asset_history.call_args[1]
        assert call_kwargs["area"] == "Grinding"


class TestHistoryStatus:
    """Tests for GET /api/assets/history/status"""

    def test_status_endpoint_works(
        self,
        client,
        mock_history_service,
        mock_mem0_service,
    ):
        """Status endpoint returns service status."""
        response = client.get("/api/assets/history/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ready"
        assert "mem0_configured" in data


class TestErrorHandling:
    """Tests for error handling in API."""

    def test_handles_service_error(
        self,
        client,
        mock_verify_jwt,
        sample_asset_id,
        sample_history_entry,
        mock_history_service,
        mock_mem0_service,
    ):
        """Returns 503 on service error."""
        from app.services.asset_history_service import AssetHistoryServiceError

        mock_history_service.create_history_entry = AsyncMock(
            side_effect=AssetHistoryServiceError("Database error")
        )

        response = client.post(
            f"/api/assets/{sample_asset_id}/history",
            json=sample_history_entry,
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_graceful_degradation_on_get_history_error(
        self,
        client,
        mock_verify_jwt,
        sample_asset_id,
        mock_history_service,
    ):
        """Returns empty result on get_history error."""
        mock_history_service.get_asset_history = AsyncMock(
            side_effect=Exception("Unexpected error")
        )

        response = client.get(
            f"/api/assets/{sample_asset_id}/history",
            headers={"Authorization": "Bearer test-token"},
        )

        # Should return empty result, not error
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["items"] == []

    def test_graceful_degradation_on_search_error(
        self,
        client,
        mock_verify_jwt,
        sample_asset_id,
        mock_history_service,
    ):
        """Returns empty result on search error."""
        mock_history_service.search_asset_history = AsyncMock(
            side_effect=Exception("Search failed")
        )

        response = client.get(
            f"/api/assets/{sample_asset_id}/history/search",
            headers={"Authorization": "Bearer test-token"},
            params={"q": "test"},
        )

        # Should return empty result, not error
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["results"] == []
