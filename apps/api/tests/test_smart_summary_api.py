"""
Tests for Smart Summary API Endpoints

Story: 3.5 - Smart Summary Generator
AC: #7 - API Endpoint for Summary Retrieval
"""

import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_smart_summary_service():
    """Mock SmartSummaryService for API tests."""
    with patch('app.api.summaries.get_smart_summary_service') as mock_get:
        mock_service = MagicMock()
        mock_get.return_value = mock_service
        yield mock_service


@pytest.fixture
def sample_smart_summary():
    """Sample SmartSummary for testing."""
    from app.services.ai.smart_summary import SmartSummary
    return SmartSummary(
        id="sum-123",
        date=date(2024, 1, 15),
        summary_text="## Executive Summary\n\nTest summary content",
        citations_json=[
            {
                "asset_name": "Grinder 5",
                "metric_name": "OEE",
                "metric_value": "72%",
                "source_table": "daily_summaries",
            }
        ],
        model_used="gpt-4-turbo-preview",
        prompt_tokens=1000,
        completion_tokens=500,
        generation_duration_ms=2500,
        is_fallback=False,
        created_at=datetime(2024, 1, 16, 6, 30, 0),
    )


# =============================================================================
# AC#7: API Endpoint Tests
# =============================================================================

class TestSmartSummaryAPI:
    """Tests for smart summary API endpoints (AC#7)."""

    def test_get_smart_summary_returns_cached(
        self,
        client,
        mock_verify_jwt,
        mock_smart_summary_service,
        sample_smart_summary
    ):
        """Test GET /api/summaries/smart/{date} returns cached summary."""
        mock_smart_summary_service.get_cached_summary = AsyncMock(
            return_value=sample_smart_summary
        )

        response = client.get(
            "/api/summaries/smart/2024-01-15",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["date"] == "2024-01-15"
        assert "Executive Summary" in data["summary_text"]
        assert len(data["citations"]) == 1
        assert data["model_used"] == "gpt-4-turbo-preview"
        assert data["is_fallback"] is False

    def test_get_smart_summary_returns_404_when_not_found(
        self,
        client,
        mock_verify_jwt,
        mock_smart_summary_service
    ):
        """Test GET returns 404 when no summary exists (AC#7)."""
        mock_smart_summary_service.get_cached_summary = AsyncMock(return_value=None)

        response = client.get(
            "/api/summaries/smart/2024-01-15",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 404
        assert "No smart summary found" in response.json()["detail"]

    def test_get_smart_summary_regenerate_param(
        self,
        client,
        mock_verify_jwt,
        mock_smart_summary_service,
        sample_smart_summary
    ):
        """Test ?regenerate=true forces new generation (AC#7)."""
        mock_smart_summary_service.generate_smart_summary = AsyncMock(
            return_value=sample_smart_summary
        )

        response = client.get(
            "/api/summaries/smart/2024-01-15?regenerate=true",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        mock_smart_summary_service.generate_smart_summary.assert_called_once()

    def test_get_smart_summary_requires_auth(self, client):
        """Test endpoint requires authentication (AC#7)."""
        response = client.get("/api/summaries/smart/2024-01-15")

        # Should return 403 (Forbidden) or 401 (Unauthorized)
        assert response.status_code in [401, 403]

    def test_generate_smart_summary_creates_new(
        self,
        client,
        mock_verify_jwt,
        mock_smart_summary_service,
        sample_smart_summary
    ):
        """Test POST /api/summaries/generate creates summary."""
        mock_smart_summary_service.generate_smart_summary = AsyncMock(
            return_value=sample_smart_summary
        )

        response = client.post(
            "/api/summaries/generate",
            json={"target_date": "2024-01-15", "regenerate": False},
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["date"] == "2024-01-15"

    def test_generate_smart_summary_defaults_to_t1(
        self,
        client,
        mock_verify_jwt,
        mock_smart_summary_service,
        sample_smart_summary
    ):
        """Test POST defaults to T-1 when no date specified."""
        mock_smart_summary_service.generate_smart_summary = AsyncMock(
            return_value=sample_smart_summary
        )

        response = client.post(
            "/api/summaries/generate",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 201
        # Verify generate was called (date will be T-1)
        mock_smart_summary_service.generate_smart_summary.assert_called_once()

    def test_invalidate_smart_summary(
        self,
        client,
        mock_verify_jwt,
        mock_smart_summary_service
    ):
        """Test DELETE /api/summaries/smart/{date} invalidates cache (AC#6)."""
        mock_smart_summary_service.invalidate_cache = AsyncMock(return_value=True)

        response = client.delete(
            "/api/summaries/smart/2024-01-15",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 204
        mock_smart_summary_service.invalidate_cache.assert_called_once()


class TestTokenUsageAPI:
    """Tests for token usage API endpoints (AC#10)."""

    def test_get_token_usage(
        self,
        client,
        mock_verify_jwt,
        mock_smart_summary_service
    ):
        """Test GET /api/summaries/usage returns usage summary."""
        mock_smart_summary_service.get_token_usage_summary = AsyncMock(
            return_value={
                "period_start": "2024-01-01",
                "period_end": "2024-01-31",
                "total_generations": 31,
                "total_prompt_tokens": 37200,
                "total_completion_tokens": 15500,
                "total_tokens": 52700,
                "estimated_cost_usd": 1.23,
            }
        )

        response = client.get(
            "/api/summaries/usage",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_generations"] == 31
        assert data["total_tokens"] == 52700

    def test_get_token_usage_with_date_range(
        self,
        client,
        mock_verify_jwt,
        mock_smart_summary_service
    ):
        """Test usage endpoint accepts date range parameters."""
        mock_smart_summary_service.get_token_usage_summary = AsyncMock(
            return_value={
                "period_start": "2024-01-15",
                "period_end": "2024-01-20",
                "total_generations": 6,
                "total_prompt_tokens": 6000,
                "total_completion_tokens": 3000,
                "total_tokens": 9000,
                "estimated_cost_usd": 0.15,
            }
        )

        response = client.get(
            "/api/summaries/usage?start_date=2024-01-15&end_date=2024-01-20",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["period_start"] == "2024-01-15"


class TestLLMHealthAPI:
    """Tests for LLM health check endpoint (AC#1)."""

    def test_llm_health_check_public(self, client):
        """Test health check endpoint is public."""
        with patch('app.api.summaries.check_llm_health') as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "provider": "openai",
                "model": "gpt-4-turbo-preview",
                "message": "LLM service is responding",
                "healthy": True,
            }

            response = client.get("/api/summaries/health/llm")

            assert response.status_code == 200
            data = response.json()
            assert data["healthy"] is True

    def test_llm_health_check_not_configured(self, client):
        """Test health check when LLM not configured."""
        with patch('app.api.summaries.check_llm_health') as mock_health:
            mock_health.return_value = {
                "status": "not_configured",
                "provider": "openai",
                "message": "API key not configured",
                "healthy": False,
            }

            response = client.get("/api/summaries/health/llm")

            assert response.status_code == 200
            data = response.json()
            assert data["healthy"] is False
            assert data["status"] == "not_configured"


class TestResponseSchemas:
    """Tests for API response schemas (AC#7)."""

    def test_smart_summary_response_includes_all_fields(
        self,
        client,
        mock_verify_jwt,
        mock_smart_summary_service,
        sample_smart_summary
    ):
        """Test response includes all required fields per AC#7."""
        mock_smart_summary_service.get_cached_summary = AsyncMock(
            return_value=sample_smart_summary
        )

        response = client.get(
            "/api/summaries/smart/2024-01-15",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()

        # Required fields per AC#6
        assert "id" in data
        assert "date" in data
        assert "summary_text" in data
        assert "citations" in data
        assert "model_used" in data
        assert "prompt_tokens" in data
        assert "completion_tokens" in data
        assert "generation_duration_ms" in data
        assert "is_fallback" in data

    def test_fallback_summary_clearly_indicates_ai_unavailable(
        self,
        client,
        mock_verify_jwt,
        mock_smart_summary_service
    ):
        """Test fallback summary indicates AI unavailable (AC#8)."""
        from app.services.ai.smart_summary import SmartSummary

        fallback_summary = SmartSummary(
            date=date(2024, 1, 15),
            summary_text="## Executive Summary\n\n**AI summary unavailable - showing key metrics**",
            citations_json=[],
            model_used="fallback_template",
            is_fallback=True,
        )

        mock_smart_summary_service.get_cached_summary = AsyncMock(
            return_value=fallback_summary
        )

        response = client.get(
            "/api/summaries/smart/2024-01-15",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_fallback"] is True
        assert "AI summary unavailable" in data["summary_text"]
