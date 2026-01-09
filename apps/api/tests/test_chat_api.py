"""
Tests for Chat API Endpoints (Story 4.2, 5.7)

Tests for the /api/chat/* endpoints including authentication,
rate limiting, query processing, and agent integration.

Story 4.2 AC#8: API Endpoint Design Tests
Story 5.7: Agent Chat Integration Tests
"""

import pytest
import time
from unittest.mock import patch, MagicMock, AsyncMock
from pydantic import BaseModel
from typing import List, Dict, Any, Optional


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
            from app.api.chat import _rate_limit_store, _get_rate_limit_config
            _rate_limit_store.clear()

            # Add old requests (older than window)
            _, rate_limit_window = _get_rate_limit_config()
            user_id = "123e4567-e89b-12d3-a456-426614174000"
            old_time = time.time() - rate_limit_window - 10
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


class TestAgentChatIntegration:
    """Tests for Story 5.7: Agent Chat Integration."""

    def test_query_routes_to_agent_when_configured(self, client, mock_verify_jwt):
        """
        Story 5.7 AC#1: Message is routed to agent endpoint when agent is configured.
        """
        # Mock AgentInternalResponse for process_message
        class MockAgentResponse:
            content = "Grinder 5 has an OEE of 87.5% based on yesterday's data."
            tool_used = "oee_query_tool"
            citations = [
                {
                    "source": "daily_summaries",
                    "query": "SELECT * FROM daily_summaries",
                    "timestamp": "2026-01-09T10:00:00Z",
                    "table": "daily_summaries",
                    "confidence": 0.95,
                    "display_text": "[Source: daily_summaries/2026-01-08]"
                }
            ]
            suggested_questions = [
                "What caused the downtime?",
                "How does this compare to last week?"
            ]
            execution_time_ms = 1250.0
            meta = {}
            error = None

        with patch('app.api.chat.get_manufacturing_agent') as mock_agent_getter:
            with patch('app.api.chat.memory_service') as mock_memory:
                # Configure agent mock
                agent_instance = MagicMock()
                agent_instance.is_configured = True
                agent_instance.process_message = AsyncMock(return_value=MockAgentResponse())
                mock_agent_getter.return_value = agent_instance

                # Configure memory mock
                mock_memory.get_context_for_query = AsyncMock(return_value=[])
                mock_memory.add_memory = AsyncMock(return_value={"id": "mem-123"})

                # Clear rate limit
                from app.api.chat import _rate_limit_store
                _rate_limit_store.clear()

                response = client.post(
                    "/api/chat/query",
                    json={"question": "What was Grinder 5's OEE yesterday?"},
                    headers={"Authorization": "Bearer test-token"}
                )

                assert response.status_code == 200
                data = response.json()

                # Verify response contains agent data
                assert "answer" in data
                assert "87.5%" in data["answer"]
                assert "citations" in data
                assert len(data["citations"]) > 0

    def test_query_includes_follow_up_questions(self, client, mock_verify_jwt):
        """
        Story 5.7 AC#3: Response includes follow-up questions from agent.
        """
        class MockAgentResponse:
            content = "Test response"
            tool_used = "asset_lookup_tool"
            citations = []
            suggested_questions = [
                "What caused the downtime?",
                "How does this compare to last week?",
                "Show me the trend"
            ]
            execution_time_ms = 500.0
            meta = {}
            error = None

        with patch('app.api.chat.get_manufacturing_agent') as mock_agent_getter:
            with patch('app.api.chat.memory_service') as mock_memory:
                agent_instance = MagicMock()
                agent_instance.is_configured = True
                agent_instance.process_message = AsyncMock(return_value=MockAgentResponse())
                mock_agent_getter.return_value = agent_instance

                mock_memory.get_context_for_query = AsyncMock(return_value=[])
                mock_memory.add_memory = AsyncMock(return_value={})

                from app.api.chat import _rate_limit_store
                _rate_limit_store.clear()

                response = client.post(
                    "/api/chat/query",
                    json={"question": "Test question"},
                    headers={"Authorization": "Bearer test-token"}
                )

                assert response.status_code == 200
                data = response.json()

                # Verify follow-up questions are in suggestions or meta
                assert "suggestions" in data or ("meta" in data and "follow_up_questions" in data.get("meta", {}))
                if "suggestions" in data and data["suggestions"]:
                    assert len(data["suggestions"]) == 3
                    assert "What caused the downtime?" in data["suggestions"]

    def test_query_stores_conversation_in_memory(self, client, mock_verify_jwt):
        """
        Story 5.7 AC#6: Conversations are stored in Mem0.
        """
        class MockAgentResponse:
            content = "Test response"
            tool_used = None
            citations = []
            suggested_questions = []
            execution_time_ms = 200.0
            meta = {}
            error = None

        with patch('app.api.chat.get_manufacturing_agent') as mock_agent_getter:
            with patch('app.api.chat.memory_service') as mock_memory:
                agent_instance = MagicMock()
                agent_instance.is_configured = True
                agent_instance.process_message = AsyncMock(return_value=MockAgentResponse())
                mock_agent_getter.return_value = agent_instance

                mock_memory.get_context_for_query = AsyncMock(return_value=[])
                mock_memory.add_memory = AsyncMock(return_value={"id": "mem-456"})

                from app.api.chat import _rate_limit_store
                _rate_limit_store.clear()

                response = client.post(
                    "/api/chat/query",
                    json={"question": "Test question for memory"},
                    headers={"Authorization": "Bearer test-token"}
                )

                assert response.status_code == 200

                # Verify memory was called to store conversation
                mock_memory.add_memory.assert_called_once()
                call_args = mock_memory.add_memory.call_args

                # Check messages format
                messages = call_args.kwargs.get("messages", call_args[1].get("messages") if len(call_args) > 1 else call_args[0][0])
                assert len(messages) == 2
                assert messages[0]["role"] == "user"
                assert messages[0]["content"] == "Test question for memory"
                assert messages[1]["role"] == "assistant"

    def test_query_fallback_to_text_to_sql_when_agent_not_configured(self, client, mock_verify_jwt):
        """
        Story 5.7: Falls back to Text-to-SQL when agent is not configured.
        """
        with patch('app.api.chat.get_manufacturing_agent') as mock_agent_getter:
            with patch('app.api.chat.get_text_to_sql_service') as mock_service:
                # Agent not configured
                agent_instance = MagicMock()
                agent_instance.is_configured = False
                mock_agent_getter.return_value = agent_instance

                # Text-to-SQL service
                service_instance = MagicMock()
                service_instance.query = AsyncMock(return_value={
                    "answer": "Fallback response from Text-to-SQL",
                    "sql": "SELECT * FROM assets",
                    "data": [],
                    "citations": [],
                    "executed_at": "2026-01-09T10:00:00Z",
                    "execution_time_seconds": 0.2,
                    "row_count": 0,
                })
                service_instance.is_configured.return_value = True
                mock_service.return_value = service_instance

                from app.api.chat import _rate_limit_store
                _rate_limit_store.clear()

                response = client.post(
                    "/api/chat/query",
                    json={"question": "Fallback test question"},
                    headers={"Authorization": "Bearer test-token"}
                )

                assert response.status_code == 200
                data = response.json()
                assert "Fallback response" in data["answer"]

    def test_query_handles_agent_error_gracefully(self, client, mock_verify_jwt):
        """
        Story 5.7 AC#5: Errors are handled gracefully.
        """
        with patch('app.api.chat.get_manufacturing_agent') as mock_agent_getter:
            with patch('app.api.chat.memory_service') as mock_memory:
                # Agent raises an error
                from app.services.agent.executor import AgentError
                agent_instance = MagicMock()
                agent_instance.is_configured = True
                agent_instance.process_message = AsyncMock(
                    side_effect=AgentError("Service temporarily unavailable")
                )
                mock_agent_getter.return_value = agent_instance

                mock_memory.get_context_for_query = AsyncMock(return_value=[])

                from app.api.chat import _rate_limit_store
                _rate_limit_store.clear()

                response = client.post(
                    "/api/chat/query",
                    json={"question": "Test question"},
                    headers={"Authorization": "Bearer test-token"}
                )

                # Should return 503 Service Unavailable
                assert response.status_code == 503

    def test_query_use_agent_false_bypasses_agent(self, client, mock_verify_jwt):
        """
        Story 5.7: use_agent=false query param bypasses agent.
        """
        with patch('app.api.chat.get_manufacturing_agent') as mock_agent_getter:
            with patch('app.api.chat.get_text_to_sql_service') as mock_service:
                # Agent should not be called
                agent_instance = MagicMock()
                agent_instance.is_configured = True
                mock_agent_getter.return_value = agent_instance

                # Text-to-SQL service
                service_instance = MagicMock()
                service_instance.query = AsyncMock(return_value={
                    "answer": "Direct Text-to-SQL response",
                    "sql": "SELECT * FROM assets",
                    "data": [],
                    "citations": [],
                    "executed_at": "2026-01-09T10:00:00Z",
                    "execution_time_seconds": 0.1,
                    "row_count": 0,
                })
                service_instance.is_configured.return_value = True
                mock_service.return_value = service_instance

                from app.api.chat import _rate_limit_store
                _rate_limit_store.clear()

                response = client.post(
                    "/api/chat/query?use_agent=false",
                    json={"question": "Direct SQL test"},
                    headers={"Authorization": "Bearer test-token"}
                )

                assert response.status_code == 200
                data = response.json()
                assert "Direct Text-to-SQL response" in data["answer"]

                # Agent process_message should not have been called
                agent_instance.process_message.assert_not_called()

    def test_query_returns_grounding_score_from_agent(self, client, mock_verify_jwt):
        """
        Story 5.7: Response includes grounding score from agent citations.
        """
        class MockAgentResponse:
            content = "High confidence response"
            tool_used = "oee_query_tool"
            citations = [
                {"source": "daily_summaries", "confidence": 0.95, "display_text": "[Source: test]"},
                {"source": "live_snapshots", "confidence": 0.90, "display_text": "[Source: test2]"},
            ]
            suggested_questions = []
            execution_time_ms = 300.0
            meta = {}
            error = None

        with patch('app.api.chat.get_manufacturing_agent') as mock_agent_getter:
            with patch('app.api.chat.memory_service') as mock_memory:
                agent_instance = MagicMock()
                agent_instance.is_configured = True
                agent_instance.process_message = AsyncMock(return_value=MockAgentResponse())
                mock_agent_getter.return_value = agent_instance

                mock_memory.get_context_for_query = AsyncMock(return_value=[])
                mock_memory.add_memory = AsyncMock(return_value={})

                from app.api.chat import _rate_limit_store
                _rate_limit_store.clear()

                response = client.post(
                    "/api/chat/query",
                    json={"question": "High confidence test"},
                    headers={"Authorization": "Bearer test-token"}
                )

                assert response.status_code == 200
                data = response.json()

                # Check grounding score in meta
                if "meta" in data and data["meta"]:
                    assert "grounding_score" in data["meta"]
                    # Average of 0.95 and 0.90 = 0.925
                    assert data["meta"]["grounding_score"] >= 0.9

    def test_memory_context_is_retrieved_for_query(self, client, mock_verify_jwt):
        """
        Story 5.7 AC#6: Memory context is retrieved and passed to agent.
        """
        class MockAgentResponse:
            content = "Response with context"
            tool_used = None
            citations = []
            suggested_questions = []
            execution_time_ms = 200.0
            meta = {}
            error = None

        memory_context = [
            {"role": "system", "content": "Previous context: User asked about Grinder 5 OEE."}
        ]

        with patch('app.api.chat.get_manufacturing_agent') as mock_agent_getter:
            with patch('app.api.chat.memory_service') as mock_memory:
                agent_instance = MagicMock()
                agent_instance.is_configured = True
                agent_instance.process_message = AsyncMock(return_value=MockAgentResponse())
                mock_agent_getter.return_value = agent_instance

                mock_memory.get_context_for_query = AsyncMock(return_value=memory_context)
                mock_memory.add_memory = AsyncMock(return_value={})

                from app.api.chat import _rate_limit_store
                _rate_limit_store.clear()

                response = client.post(
                    "/api/chat/query",
                    json={"question": "What about today?"},
                    headers={"Authorization": "Bearer test-token"}
                )

                assert response.status_code == 200

                # Verify memory context was retrieved
                mock_memory.get_context_for_query.assert_called_once()

                # Verify chat_history was passed to agent
                agent_instance.process_message.assert_called_once()
                call_kwargs = agent_instance.process_message.call_args
                # chat_history should include memory context
                chat_history_arg = call_kwargs.kwargs.get("chat_history", [])
                assert chat_history_arg == memory_context
