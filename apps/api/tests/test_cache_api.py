"""
Tests for Cache API Endpoints (Story 5.8)

AC#7: Cache Statistics Endpoint
- GET /api/cache/stats returns cache statistics
- Endpoint is admin-only
"""

import pytest
from unittest.mock import patch, MagicMock


class TestCacheStatsEndpoint:
    """Tests for GET /api/cache/stats endpoint."""

    def test_cache_stats_requires_auth(self, client, mock_verify_jwt_invalid):
        """Endpoint requires authentication."""
        response = client.get(
            "/api/cache/stats",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    def test_cache_stats_requires_admin(self, client, mock_verify_jwt):
        """Endpoint requires admin role - regular users get 403."""
        response = client.get(
            "/api/cache/stats",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]

    def test_cache_stats_success(self, client, mock_verify_jwt_admin):
        """AC#7: Returns cache statistics for admin user."""
        mock_stats = {
            "enabled": True,
            "max_size_per_tier": 1000,
            "total_entries": 5,
            "entries_by_tier": {"live": 1, "daily": 3, "static": 1},
            "tier_ttls": {"live": 60, "daily": 900, "static": 3600},
            "hits": 100,
            "misses": 20,
            "hit_rate_percent": 83.33,
            "invalidations": 5,
        }

        with patch("app.api.cache.get_tool_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.get_stats.return_value = mock_stats
            mock_get_cache.return_value = mock_cache

            response = client.get(
                "/api/cache/stats",
                headers={"Authorization": "Bearer valid-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True
        assert data["total_entries"] == 5
        assert data["hits"] == 100
        assert data["misses"] == 20
        assert data["hit_rate_percent"] == 83.33
        assert "entries_by_tier" in data


class TestCacheInvalidateEndpoint:
    """Tests for POST /api/cache/invalidate endpoint."""

    def test_invalidate_requires_auth(self, client, mock_verify_jwt_invalid):
        """Endpoint requires authentication."""
        response = client.post(
            "/api/cache/invalidate?tier=daily",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    def test_invalidate_requires_admin(self, client, mock_verify_jwt):
        """Endpoint requires admin role - regular users get 403."""
        response = client.post(
            "/api/cache/invalidate?tier=daily",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]

    def test_invalidate_by_tier(self, client, mock_verify_jwt_admin):
        """AC#4: Can invalidate by tier (admin only)."""
        with patch("app.api.cache.get_tool_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.invalidate.return_value = 10
            mock_get_cache.return_value = mock_cache

            response = client.post(
                "/api/cache/invalidate?tier=daily",
                headers={"Authorization": "Bearer valid-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["invalidated"] == 10
        assert "daily" in data["message"]

    def test_invalidate_by_tool_name(self, client, mock_verify_jwt_admin):
        """AC#4: Can invalidate by tool name (admin only)."""
        with patch("app.api.cache.get_tool_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.invalidate.return_value = 5
            mock_get_cache.return_value = mock_cache

            response = client.post(
                "/api/cache/invalidate?tool_name=oee_query",
                headers={"Authorization": "Bearer valid-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["invalidated"] == 5
        assert "oee_query" in data["message"]

    def test_invalidate_by_pattern(self, client, mock_verify_jwt_admin):
        """AC#4: Can invalidate by pattern (admin only)."""
        with patch("app.api.cache.get_tool_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.invalidate.return_value = 3
            mock_get_cache.return_value = mock_cache

            response = client.post(
                "/api/cache/invalidate?pattern=oee_query:*",
                headers={"Authorization": "Bearer valid-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["invalidated"] == 3

    def test_invalidate_requires_filter(self, client, mock_verify_jwt_admin):
        """Invalidate endpoint requires at least one filter."""
        response = client.post(
            "/api/cache/invalidate",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 400
        assert "Must provide at least one of" in response.json()["detail"]

    def test_invalidate_invalid_tier(self, client, mock_verify_jwt_admin):
        """Invalid tier returns 400."""
        response = client.post(
            "/api/cache/invalidate?tier=invalid_tier",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 400
        assert "Invalid tier" in response.json()["detail"]


class TestCacheClearEndpoint:
    """Tests for POST /api/cache/clear endpoint."""

    def test_clear_requires_auth(self, client, mock_verify_jwt_invalid):
        """Endpoint requires authentication."""
        response = client.post(
            "/api/cache/clear",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    def test_clear_requires_admin(self, client, mock_verify_jwt):
        """Endpoint requires admin role - regular users get 403."""
        response = client.post(
            "/api/cache/clear",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]

    def test_clear_all_caches(self, client, mock_verify_jwt_admin):
        """Can clear all cache entries (admin only)."""
        with patch("app.api.cache.get_tool_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.invalidate_all.return_value = 25
            mock_get_cache.return_value = mock_cache

            response = client.post(
                "/api/cache/clear",
                headers={"Authorization": "Bearer valid-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["invalidated"] == 25
        assert "25" in data["message"]


class TestAgentChatForceRefresh:
    """Tests for force_refresh in agent chat endpoint (AC#5)."""

    def test_force_refresh_parameter_accepted(self, client, mock_verify_jwt):
        """AC#5: force_refresh parameter is accepted in chat request."""
        with patch("app.api.agent.get_agent") as mock_get_agent:
            mock_agent = MagicMock()
            mock_agent.is_configured = True
            mock_agent.is_initialized = True

            # Create an async mock for process_message
            async def mock_process(*args, **kwargs):
                from app.services.agent.executor import AgentResponse
                return AgentResponse(
                    content="Test response",
                    citations=[],
                    suggested_questions=[],
                    execution_time_ms=100.0,
                    meta={},
                )

            mock_agent.process_message = mock_process
            mock_get_agent.return_value = mock_agent

            response = client.post(
                "/api/agent/chat",
                json={
                    "message": "What is the OEE for Grinder 5?",
                    "force_refresh": True,
                },
                headers={"Authorization": "Bearer valid-token"},
            )

        # Should succeed (not fail due to unrecognized field)
        assert response.status_code == 200
