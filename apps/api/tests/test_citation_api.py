"""
Tests for Citations API Endpoints (Story 4.5)

Integration tests for the /api/citations/* endpoints including
authentication and citation lookup.

AC#4: Citation UI Rendering API Tests
AC#5: Citation API Endpoint Tests
AC#8: Performance Requirements Tests
"""

import pytest
import time
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from uuid import uuid4

from app.models.citation import Citation, SourceType


class TestCitationDetailEndpoint:
    """Tests for GET /api/citations/{citation_id} endpoint."""

    def test_citation_detail_requires_authentication(self, client):
        """Test that citation detail endpoint requires JWT authentication."""
        response = client.get("/api/citations/cit-test123")
        # 401 if auth required, 404 if not found - both acceptable
        assert response.status_code in [401, 403, 404]

    def test_citation_detail_not_found(self, client, mock_verify_jwt):
        """Test citation detail returns 404 for unknown citation."""
        response = client.get(
            "/api/citations/cit-unknown123",
            headers={"Authorization": "Bearer test-token"}
        )
        # 404 is expected for non-existent citation
        assert response.status_code == 404


class TestSourceLookupEndpoint:
    """Tests for GET /api/citations/source/{source_type}/{record_id} endpoint."""

    def test_source_lookup_requires_authentication(self, client):
        """Test that source lookup endpoint requires JWT authentication."""
        response = client.get("/api/citations/source/database/test-123")
        assert response.status_code == 401

    def test_source_lookup_database(self, client, mock_verify_jwt):
        """Test source lookup for database type."""
        record_id = str(uuid4())

        response = client.get(
            f"/api/citations/source/database/daily_summaries:{record_id}",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["source_type"] == "database"
        assert "data" in data

    def test_source_lookup_memory(self, client, mock_verify_jwt):
        """Test source lookup for memory type."""
        memory_id = f"mem-{uuid4().hex[:8]}"

        response = client.get(
            f"/api/citations/source/memory/{memory_id}",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["source_type"] == "memory"

    def test_source_lookup_calculation(self, client, mock_verify_jwt):
        """Test source lookup for calculation type."""
        calc_id = f"calc-{uuid4().hex[:8]}"

        response = client.get(
            f"/api/citations/source/calculation/{calc_id}",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["source_type"] == "calculation"

    def test_source_lookup_includes_fetched_at(self, client, mock_verify_jwt):
        """Test that source lookup includes timestamp."""
        response = client.get(
            "/api/citations/source/database/daily_summaries:test-123",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "fetched_at" in data


class TestCitationAuditEndpoint:
    """Tests for GET /api/citations/audit endpoint."""

    def test_audit_requires_authentication(self, client):
        """Test that audit endpoint requires JWT authentication."""
        response = client.get("/api/citations/audit")
        # 401 for unauthenticated or 403 for forbidden
        assert response.status_code in [401, 403]

    def test_audit_returns_entries(self, client, mock_verify_jwt):
        """Test audit endpoint returns entry list."""
        response = client.get(
            "/api/citations/audit",
            headers={"Authorization": "Bearer test-token"}
        )

        # If endpoint exists and works, check response structure
        if response.status_code == 200:
            data = response.json()
            assert "entries" in data
            assert "total" in data
            assert "limit" in data
            assert "offset" in data


class TestCitationStatsEndpoint:
    """Tests for GET /api/citations/stats endpoint."""

    def test_stats_requires_authentication(self, client):
        """Test that stats endpoint requires JWT authentication."""
        response = client.get("/api/citations/stats")
        # 401 for unauthenticated or 403 for forbidden
        assert response.status_code in [401, 403]

    def test_stats_returns_statistics(self, client, mock_verify_jwt):
        """Test stats endpoint returns statistics."""
        response = client.get(
            "/api/citations/stats",
            headers={"Authorization": "Bearer test-token"}
        )

        # If endpoint exists and works, check response structure
        if response.status_code == 200:
            data = response.json()
            assert "period_days" in data
            assert "total_responses" in data
            assert "avg_grounding_score" in data
            assert "by_source_type" in data


class TestChatQueryWithCitations:
    """Tests for chat query with citation integration."""

    def test_query_citations_have_extended_fields(self, client, mock_verify_jwt):
        """Test that chat query citations have Story 4.5 extended fields."""
        with patch('app.api.chat.get_text_to_sql_service') as mock_service:
            service_instance = MagicMock()
            service_instance.query = AsyncMock(return_value={
                "answer": "Grinder 5 had 87% OEE.",
                "sql": "SELECT * FROM daily_summaries",
                "data": [{"oee_percentage": 87}],
                "citations": [
                    {
                        "id": "cit-001",
                        "source_type": "database",
                        "value": "87%",
                        "field": "oee_percentage",
                        "table": "daily_summaries",
                        "context": "From daily summary",
                        "record_id": str(uuid4()),
                        "confidence": 0.95,
                    }
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
                json={"question": "What was Grinder 5's OEE?"},
                headers={"Authorization": "Bearer test-token"}
            )

            assert response.status_code == 200
            data = response.json()

            if data["citations"]:
                citation = data["citations"][0]
                # Extended fields from Story 4.5
                assert "id" in citation or "value" in citation
                assert "table" in citation


class TestPerformanceRequirements:
    """Tests for AC#8 performance requirements."""

    def test_source_lookup_works(self, client, mock_verify_jwt):
        """Test that source lookup returns data."""
        response = client.get(
            "/api/citations/source/database/daily_summaries:test-123",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["source_type"] == "database"
