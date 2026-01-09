"""
Tests for Agent API Endpoints (Story 5.1)

AC#7: Agent Chat Endpoint
- POST request to /api/agent/chat
- Authenticated via Supabase JWT
- Response follows AgentResponse schema

AC#8: Error Handling and Logging
- Errors are logged with full context
- User receives helpful error messages
"""

import pytest
import time
from unittest.mock import patch, MagicMock, AsyncMock


class TestAgentChatEndpoint:
    """Tests for POST /api/agent/chat endpoint."""

    def test_chat_requires_authentication(self, client):
        """AC#7: Request is authenticated via Supabase JWT."""
        response = client.post(
            "/api/agent/chat",
            json={"message": "What was the OEE yesterday?"}
        )
        assert response.status_code == 401

    def test_chat_with_valid_auth(self, client, mock_verify_jwt):
        """AC#7: Agent processes the message with valid auth."""
        with patch('app.api.agent.get_manufacturing_agent') as mock_agent:
            # Mock the agent
            agent_instance = MagicMock()
            agent_instance.is_configured = True
            agent_instance.is_initialized = True
            agent_instance.process_message = AsyncMock(return_value=MagicMock(
                content="Grinder 5 had 87% OEE yesterday.",
                tool_used="asset_status",
                citations=[
                    {
                        "source": "daily_summaries",
                        "query": "SELECT * FROM daily_summaries",
                        "timestamp": "2026-01-09T10:00:00Z",
                        "table": "daily_summaries",
                        "confidence": 0.95,
                        "display_text": "[Source: daily_summaries]",
                    }
                ],
                suggested_questions=["What was the downtime?"],
                execution_time_ms=1250.5,
                meta={"model": "gpt-4"},
                error=None,
            ))
            mock_agent.return_value = agent_instance

            response = client.post(
                "/api/agent/chat",
                json={"message": "What was Grinder 5's OEE yesterday?"},
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "content" in data
            assert "citations" in data
            assert "tool_used" in data

    def test_chat_validates_message_length(self, client, mock_verify_jwt):
        """Test message minimum length is enforced."""
        response = client.post(
            "/api/agent/chat",
            json={"message": "ab"},  # Less than 3 chars
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 422

    def test_chat_with_context(self, client, mock_verify_jwt):
        """Test chat with context parameter."""
        with patch('app.api.agent.get_manufacturing_agent') as mock_agent:
            agent_instance = MagicMock()
            agent_instance.is_configured = True
            agent_instance.is_initialized = True
            agent_instance.process_message = AsyncMock(return_value=MagicMock(
                content="Test response",
                tool_used=None,
                citations=[],
                suggested_questions=[],
                execution_time_ms=100,
                meta={},
                error=None,
            ))
            mock_agent.return_value = agent_instance

            response = client.post(
                "/api/agent/chat",
                json={
                    "message": "What about yesterday?",
                    "context": {
                        "asset_focus": "Grinder 5",
                        "time_range": "yesterday"
                    }
                },
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200

    def test_chat_with_history(self, client, mock_verify_jwt):
        """Test chat with conversation history."""
        with patch('app.api.agent.get_manufacturing_agent') as mock_agent:
            agent_instance = MagicMock()
            agent_instance.is_configured = True
            agent_instance.is_initialized = True
            agent_instance.process_message = AsyncMock(return_value=MagicMock(
                content="Based on our discussion...",
                tool_used=None,
                citations=[],
                suggested_questions=[],
                execution_time_ms=100,
                meta={},
                error=None,
            ))
            mock_agent.return_value = agent_instance

            response = client.post(
                "/api/agent/chat",
                json={
                    "message": "What else can you tell me?",
                    "chat_history": [
                        {"role": "user", "content": "What is OEE?"},
                        {"role": "assistant", "content": "OEE stands for..."}
                    ]
                },
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200

    def test_chat_agent_not_configured(self, client, mock_verify_jwt):
        """AC#8: User receives helpful error message when not configured."""
        with patch('app.api.agent.get_manufacturing_agent') as mock_agent:
            agent_instance = MagicMock()
            agent_instance.is_configured = False
            mock_agent.return_value = agent_instance

            response = client.post(
                "/api/agent/chat",
                json={"message": "Test question?"},
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 503
            assert "not configured" in response.json()["detail"].lower()

    def test_chat_expired_token(self, client, mock_verify_jwt_expired):
        """Test chat with expired token."""
        response = client.post(
            "/api/agent/chat",
            json={"message": "Test question?"},
            headers={"Authorization": "Bearer expired-token"}
        )
        assert response.status_code == 401


class TestAgentStatusEndpoint:
    """Tests for GET /api/agent/status endpoint."""

    def test_status_is_public(self, client):
        """Test status endpoint doesn't require authentication."""
        with patch('app.api.agent.get_manufacturing_agent') as mock_agent:
            agent_instance = MagicMock()
            agent_instance.is_configured = True
            agent_instance.is_initialized = False
            mock_agent.return_value = agent_instance

            with patch('app.api.agent.get_tool_registry') as mock_registry:
                mock_registry.return_value.get_tool_names.return_value = []

                response = client.get("/api/agent/status")

                assert response.status_code == 200

    def test_status_when_ready(self, client):
        """Test status when agent is ready."""
        with patch('app.api.agent.get_manufacturing_agent') as mock_agent:
            agent_instance = MagicMock()
            agent_instance.is_configured = True
            agent_instance.is_initialized = True
            mock_agent.return_value = agent_instance

            with patch('app.api.agent.get_tool_registry') as mock_registry:
                mock_registry.return_value.get_tool_names.return_value = ["test_tool"]

                response = client.get("/api/agent/status")

                assert response.status_code == 200
                data = response.json()
                assert data["configured"] is True
                assert data["initialized"] is True
                assert data["status"] == "ready"
                assert "test_tool" in data["available_tools"]

    def test_status_not_configured(self, client):
        """Test status when not configured."""
        with patch('app.api.agent.get_manufacturing_agent') as mock_agent:
            agent_instance = MagicMock()
            agent_instance.is_configured = False
            agent_instance.is_initialized = False
            mock_agent.return_value = agent_instance

            with patch('app.api.agent.get_tool_registry') as mock_registry:
                mock_registry.return_value.get_tool_names.return_value = []

                response = client.get("/api/agent/status")

                assert response.status_code == 200
                data = response.json()
                assert data["configured"] is False
                assert data["status"] == "not_configured"


class TestAgentCapabilitiesEndpoint:
    """Tests for GET /api/agent/capabilities endpoint."""

    def test_capabilities_returns_list(self, client):
        """AC#6: Suggests what types of questions it can answer."""
        with patch('app.api.agent.get_manufacturing_agent') as mock_agent:
            agent_instance = MagicMock()
            agent_instance.is_initialized = True
            mock_agent.return_value = agent_instance

            with patch('app.api.agent.get_tool_registry') as mock_registry:
                mock_tool = MagicMock()
                mock_tool.name = "asset_status"
                mock_tool.description = "Get asset status and performance"
                mock_tool.citations_required = True
                mock_registry.return_value.get_tools.return_value = [mock_tool]

                response = client.get("/api/agent/capabilities")

                assert response.status_code == 200
                data = response.json()
                assert "capabilities" in data
                assert len(data["capabilities"]) == 1
                assert data["capabilities"][0]["name"] == "asset_status"


class TestAgentHealthEndpoint:
    """Tests for GET /api/agent/health endpoint."""

    def test_health_returns_status(self, client):
        """Test health endpoint returns status."""
        with patch('app.api.agent.get_manufacturing_agent') as mock_agent:
            agent_instance = MagicMock()
            agent_instance.is_configured = True
            agent_instance.is_initialized = True
            mock_agent.return_value = agent_instance

            response = client.get("/api/agent/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "manufacturing-agent"

    def test_health_degraded_not_configured(self, client):
        """Test health returns degraded when not configured."""
        with patch('app.api.agent.get_manufacturing_agent') as mock_agent:
            agent_instance = MagicMock()
            agent_instance.is_configured = False
            agent_instance.is_initialized = False
            mock_agent.return_value = agent_instance

            response = client.get("/api/agent/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"


class TestRateLimiting:
    """Tests for rate limiting (AC#7)."""

    def test_rate_limit_blocks_excessive_requests(self, client, mock_verify_jwt, valid_jwt_payload):
        """Test rate limiting blocks after threshold."""
        with patch('app.api.agent.get_manufacturing_agent') as mock_agent:
            agent_instance = MagicMock()
            agent_instance.is_configured = True
            agent_instance.is_initialized = True
            agent_instance.process_message = AsyncMock(return_value=MagicMock(
                content="Test",
                tool_used=None,
                citations=[],
                suggested_questions=[],
                execution_time_ms=100,
                meta={},
                error=None,
            ))
            mock_agent.return_value = agent_instance

            # Clear rate limit store
            from app.api.agent import _rate_limit_store
            _rate_limit_store.clear()

            # Make requests up to limit
            for i in range(10):
                response = client.post(
                    "/api/agent/chat",
                    json={"message": f"Question {i}?"},
                    headers={"Authorization": "Bearer test-token"}
                )
                assert response.status_code == 200

            # Next request should be rate limited
            response = client.post(
                "/api/agent/chat",
                json={"message": "One more question?"},
                headers={"Authorization": "Bearer test-token"}
            )
            assert response.status_code == 429
            assert "Retry-After" in response.headers


class TestResponseFormat:
    """Tests for response format compliance (AC#5, AC#7)."""

    def test_response_includes_required_fields(self, client, mock_verify_jwt):
        """AC#7: Response follows AgentResponse schema."""
        with patch('app.api.agent.get_manufacturing_agent') as mock_agent:
            agent_instance = MagicMock()
            agent_instance.is_configured = True
            agent_instance.is_initialized = True
            agent_instance.process_message = AsyncMock(return_value=MagicMock(
                content="Test response with data",
                tool_used="test_tool",
                citations=[
                    {
                        "source": "test_source",
                        "query": "SELECT *",
                        "timestamp": "2026-01-09T10:00:00Z",
                        "table": "test_table",
                        "record_id": "123",
                        "confidence": 0.95,
                        "display_text": "[Source: test_table/123]",
                    }
                ],
                suggested_questions=["Follow up?"],
                execution_time_ms=500.0,
                meta={"model": "gpt-4"},
                error=None,
            ))
            mock_agent.return_value = agent_instance

            # Clear rate limit
            from app.api.agent import _rate_limit_store
            _rate_limit_store.clear()

            response = client.post(
                "/api/agent/chat",
                json={"message": "Test question?"},
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()

            # Verify required fields
            assert "content" in data
            assert isinstance(data["content"], str)

            assert "tool_used" in data
            # tool_used can be None

            assert "citations" in data
            assert isinstance(data["citations"], list)

            assert "suggested_questions" in data
            assert isinstance(data["suggested_questions"], list)

            assert "execution_time_ms" in data
            assert isinstance(data["execution_time_ms"], (int, float))

            assert "meta" in data
            assert isinstance(data["meta"], dict)

    def test_citation_format(self, client, mock_verify_jwt):
        """AC#5: Citations follow correct format."""
        with patch('app.api.agent.get_manufacturing_agent') as mock_agent:
            agent_instance = MagicMock()
            agent_instance.is_configured = True
            agent_instance.is_initialized = True
            agent_instance.process_message = AsyncMock(return_value=MagicMock(
                content="OEE was 87.5%",
                tool_used="asset_status",
                citations=[
                    {
                        "source": "daily_summaries",
                        "query": "SELECT * FROM daily_summaries",
                        "timestamp": "2026-01-09T10:00:00Z",
                        "table": "daily_summaries",
                        "record_id": "abc123",
                        "asset_id": "grinder-5",
                        "confidence": 0.95,
                        "display_text": "[Source: daily_summaries/abc123]",
                    }
                ],
                suggested_questions=[],
                execution_time_ms=500,
                meta={},
                error=None,
            ))
            mock_agent.return_value = agent_instance

            from app.api.agent import _rate_limit_store
            _rate_limit_store.clear()

            response = client.post(
                "/api/agent/chat",
                json={"message": "What was Grinder 5's OEE?"},
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()

            assert len(data["citations"]) > 0
            citation = data["citations"][0]

            # Verify citation fields
            assert "source" in citation
            assert "query" in citation
            assert "timestamp" in citation
            assert "confidence" in citation
            assert "display_text" in citation
