"""
Tests for Chat API Endpoints (Story 4.2)

Tests for the /api/chat/* endpoints including authentication,
rate limiting, and query processing.

AC#8: API Endpoint Design Tests
"""

import pytest
import time
from unittest.mock import patch, MagicMock, AsyncMock


class TestChatQueryEndpoint:
    """Tests for POST /api/chat/query endpoint."""

    def test_query_requires_authentication(self, client):
        """Test that query endpoint requires JWT authentication."""
        response = client.post(
            "/api/chat/query",
            json={"question": "What was the OEE yesterday?"}
        )
        assert response.status_code == 401  # HTTPBearer returns 401 for missing auth

    def test_query_with_valid_auth(self, client, mock_verify_jwt):
        """Test query with valid authentication."""
        with patch('app.api.chat.get_text_to_sql_service') as mock_service:
            # Mock the service
            service_instance = MagicMock()
            service_instance.query = AsyncMock(return_value={
                "answer": "Grinder 5 had 87% OEE yesterday.",
                "sql": "SELECT * FROM daily_summaries",
                "data": [{"oee_percentage": 87}],
                "citations": [],
                "executed_at": "2026-01-06T10:00:00Z",
                "execution_time_seconds": 0.5,
                "row_count": 1,
            })
            service_instance.is_configured.return_value = True
            mock_service.return_value = service_instance

            response = client.post(
                "/api/chat/query",
                json={"question": "What was Grinder 5's OEE yesterday?"},
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "answer" in data
            assert "sql" in data
            assert "citations" in data

    def test_query_with_context(self, client, mock_verify_jwt):
        """Test query with context parameter."""
        with patch('app.api.chat.get_text_to_sql_service') as mock_service:
            service_instance = MagicMock()
            service_instance.query = AsyncMock(return_value={
                "answer": "Test answer",
                "sql": "SELECT * FROM assets",
                "data": [],
                "citations": [],
                "executed_at": "2026-01-06T10:00:00Z",
                "execution_time_seconds": 0.1,
                "row_count": 0,
            })
            service_instance.is_configured.return_value = True
            mock_service.return_value = service_instance

            response = client.post(
                "/api/chat/query",
                json={
                    "question": "What about yesterday?",
                    "context": {
                        "asset_focus": "Grinder 5",
                        "previous_queries": ["What is Grinder 5?"]
                    }
                },
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            # Verify context was passed to service
            service_instance.query.assert_called_once()
            call_kwargs = service_instance.query.call_args
            assert call_kwargs[1]["context"] is not None

    def test_query_validates_question_length(self, client, mock_verify_jwt):
        """Test that question minimum length is enforced."""
        with patch('app.api.chat.get_text_to_sql_service') as mock_service:
            service_instance = MagicMock()
            service_instance.is_configured.return_value = True
            mock_service.return_value = service_instance

            # Too short
            response = client.post(
                "/api/chat/query",
                json={"question": "ab"},  # Less than 3 chars
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 422  # Validation error

    def test_query_expired_token(self, client, mock_verify_jwt_expired):
        """Test query with expired token."""
        response = client.post(
            "/api/chat/query",
            json={"question": "What was the OEE?"},
            headers={"Authorization": "Bearer expired-token"}
        )
        assert response.status_code == 401

    def test_query_invalid_token(self, client, mock_verify_jwt_invalid):
        """Test query with invalid token."""
        response = client.post(
            "/api/chat/query",
            json={"question": "What was the OEE?"},
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401


class TestChatTablesEndpoint:
    """Tests for GET /api/chat/tables endpoint."""

    def test_tables_requires_authentication(self, client):
        """Test that tables endpoint requires authentication."""
        response = client.get("/api/chat/tables")
        assert response.status_code == 401  # HTTPBearer returns 401 for missing auth

    def test_tables_returns_list(self, client, mock_verify_jwt):
        """Test tables endpoint returns table list."""
        with patch('app.api.chat.get_text_to_sql_service') as mock_service:
            service_instance = MagicMock()
            service_instance.ALLOWED_TABLES = [
                "assets", "cost_centers", "daily_summaries",
                "live_snapshots", "safety_events"
            ]
            mock_service.return_value = service_instance

            response = client.get(
                "/api/chat/tables",
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "tables" in data
            assert "assets" in data["tables"]
            assert "daily_summaries" in data["tables"]

    def test_tables_includes_descriptions(self, client, mock_verify_jwt):
        """Test tables endpoint includes descriptions."""
        with patch('app.api.chat.get_text_to_sql_service') as mock_service:
            service_instance = MagicMock()
            service_instance.ALLOWED_TABLES = ["assets", "daily_summaries"]
            mock_service.return_value = service_instance

            response = client.get(
                "/api/chat/tables",
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "descriptions" in data
            # Should have descriptions for tables
            assert len(data["descriptions"]) > 0


class TestChatStatusEndpoint:
    """Tests for GET /api/chat/status endpoint."""

    def test_status_is_public(self, client):
        """Test status endpoint doesn't require authentication."""
        with patch('app.api.chat.get_text_to_sql_service') as mock_service:
            service_instance = MagicMock()
            service_instance.is_configured.return_value = True
            service_instance.is_initialized.return_value = False
            service_instance.ALLOWED_TABLES = ["assets"]
            mock_service.return_value = service_instance

            response = client.get("/api/chat/status")

            assert response.status_code == 200

    def test_status_when_configured(self, client):
        """Test status when service is configured."""
        with patch('app.api.chat.get_text_to_sql_service') as mock_service:
            service_instance = MagicMock()
            service_instance.is_configured.return_value = True
            service_instance.is_initialized.return_value = True
            service_instance.ALLOWED_TABLES = ["assets", "daily_summaries"]
            mock_service.return_value = service_instance

            response = client.get("/api/chat/status")

            assert response.status_code == 200
            data = response.json()
            assert data["configured"] is True
            assert data["initialized"] is True
            assert data["status"] == "ready"

    def test_status_when_not_configured(self, client):
        """Test status when service is not configured."""
        with patch('app.api.chat.get_text_to_sql_service') as mock_service:
            service_instance = MagicMock()
            service_instance.is_configured.return_value = False
            service_instance.is_initialized.return_value = False
            service_instance.ALLOWED_TABLES = []
            mock_service.return_value = service_instance

            response = client.get("/api/chat/status")

            assert response.status_code == 200
            data = response.json()
            assert data["configured"] is False
            assert data["status"] == "not_configured"


class TestChatHealthEndpoint:
    """Tests for GET /api/chat/health endpoint."""

    def test_health_returns_status(self, client):
        """Test health endpoint returns status."""
        with patch('app.api.chat.get_text_to_sql_service') as mock_service:
            service_instance = MagicMock()
            service_instance.is_configured.return_value = True
            mock_service.return_value = service_instance

            response = client.get("/api/chat/health")

            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "service" in data


class TestRateLimiting:
    """Tests for rate limiting (AC#8)."""

    def test_rate_limit_blocks_excessive_requests(self, client, mock_verify_jwt, valid_jwt_payload):
        """Test that rate limiting blocks after threshold."""
        with patch('app.api.chat.get_text_to_sql_service') as mock_service:
            service_instance = MagicMock()
            service_instance.query = AsyncMock(return_value={
                "answer": "Test",
                "sql": "SELECT 1",
                "data": [],
                "citations": [],
                "executed_at": "2026-01-06T10:00:00Z",
                "execution_time_seconds": 0.1,
                "row_count": 0,
            })
            service_instance.is_configured.return_value = True
            mock_service.return_value = service_instance

            # Clear rate limit store
            from app.api.chat import _rate_limit_store
            _rate_limit_store.clear()

            # Make requests up to limit
            for i in range(10):
                response = client.post(
                    "/api/chat/query",
                    json={"question": f"Question {i}?"},
                    headers={"Authorization": "Bearer test-token"}
                )
                assert response.status_code == 200

            # Next request should be rate limited
            response = client.post(
                "/api/chat/query",
                json={"question": "One more question?"},
                headers={"Authorization": "Bearer test-token"}
            )
            assert response.status_code == 429
            assert "Retry-After" in response.headers

    def test_rate_limit_resets_after_window(self, client, mock_verify_jwt):
        """Test that rate limit resets after time window."""
        with patch('app.api.chat.get_text_to_sql_service') as mock_service:
            service_instance = MagicMock()
            service_instance.query = AsyncMock(return_value={
                "answer": "Test",
                "sql": "SELECT 1",
                "data": [],
                "citations": [],
                "executed_at": "2026-01-06T10:00:00Z",
                "execution_time_seconds": 0.1,
                "row_count": 0,
            })
            service_instance.is_configured.return_value = True
            mock_service.return_value = service_instance

            # Clear rate limit store and add old timestamps
            from app.api.chat import _rate_limit_store, RATE_LIMIT_WINDOW
            _rate_limit_store.clear()

            # Add old requests (older than window)
            user_id = "123e4567-e89b-12d3-a456-426614174000"
            old_time = time.time() - RATE_LIMIT_WINDOW - 10
            _rate_limit_store[user_id] = [old_time] * 10

            # Should be able to make new request
            response = client.post(
                "/api/chat/query",
                json={"question": "New question after window?"},
                headers={"Authorization": "Bearer test-token"}
            )
            assert response.status_code == 200


class TestResponseFormat:
    """Tests for response format compliance (AC#8)."""

    def test_response_includes_all_required_fields(self, client, mock_verify_jwt):
        """Test response has all required fields per AC#8."""
        with patch('app.api.chat.get_text_to_sql_service') as mock_service:
            service_instance = MagicMock()
            service_instance.query = AsyncMock(return_value={
                "answer": "Test answer",
                "sql": "SELECT * FROM assets",
                "data": [{"name": "Test"}],
                "citations": [
                    {"value": "Test", "field": "name", "table": "assets", "context": "test"}
                ],
                "executed_at": "2026-01-06T10:00:00Z",
                "execution_time_seconds": 0.5,
                "row_count": 1,
            })
            service_instance.is_configured.return_value = True
            mock_service.return_value = service_instance

            # Clear rate limit
            from app.api.chat import _rate_limit_store
            _rate_limit_store.clear()

            response = client.post(
                "/api/chat/query",
                json={"question": "Test question?"},
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()

            # AC#8: Response format { "answer": string, "sql": string, "data": object, "citations": array }
            assert "answer" in data
            assert isinstance(data["answer"], str)

            assert "sql" in data
            # sql can be null on error
            assert data["sql"] is None or isinstance(data["sql"], str)

            assert "data" in data
            assert isinstance(data["data"], list)

            assert "citations" in data
            assert isinstance(data["citations"], list)

            # Also includes execution metadata
            assert "executed_at" in data
            assert "execution_time_seconds" in data
            assert "row_count" in data

    def test_citation_format(self, client, mock_verify_jwt):
        """Test citation objects have correct format per AC#4."""
        with patch('app.api.chat.get_text_to_sql_service') as mock_service:
            service_instance = MagicMock()
            service_instance.query = AsyncMock(return_value={
                "answer": "Grinder 5 had 87% OEE",
                "sql": "SELECT * FROM daily_summaries",
                "data": [{"oee_percentage": 87}],
                "citations": [
                    {
                        "value": "87%",
                        "field": "oee_percentage",
                        "table": "daily_summaries",
                        "context": "Grinder 5 on 2026-01-05"
                    }
                ],
                "executed_at": "2026-01-06T10:00:00Z",
                "execution_time_seconds": 0.3,
                "row_count": 1,
            })
            service_instance.is_configured.return_value = True
            mock_service.return_value = service_instance

            from app.api.chat import _rate_limit_store
            _rate_limit_store.clear()

            response = client.post(
                "/api/chat/query",
                json={"question": "What was Grinder 5's OEE?"},
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()

            # Check citation format
            assert len(data["citations"]) > 0
            citation = data["citations"][0]

            assert "value" in citation
            assert "field" in citation
            assert "table" in citation
            assert "context" in citation
