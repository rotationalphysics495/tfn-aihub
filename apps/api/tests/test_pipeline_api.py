"""
Tests for Pipeline API Endpoints.

Story: 2.1 - Batch Data Pipeline (T-1)
AC: #8 - Pipeline Execution Logging
AC: #10 - API Endpoints
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi.testclient import TestClient

from app.main import app
from app.models.pipeline import (
    PipelineExecutionLog,
    PipelineResult,
    PipelineStatus,
)


@pytest.fixture
def client():
    """Create a test client."""
    with patch("app.core.database.mssql_db") as mock_db:
        mock_db.initialize = MagicMock()
        mock_db.dispose = MagicMock()
        mock_db.check_health.return_value = {
            "status": "not_configured",
            "connected": False,
        }
        with TestClient(app) as test_client:
            yield test_client


@pytest.fixture
def mock_verify_jwt():
    """Mock JWT verification."""
    with patch("app.core.security.verify_supabase_jwt", new_callable=AsyncMock) as mock:
        mock.return_value = {
            "sub": "123e4567-e89b-12d3-a456-426614174000",
            "email": "test@example.com",
            "role": "authenticated",
            "aud": "authenticated",
            "exp": 9999999999,
        }
        yield mock


@pytest.fixture
def mock_pipeline():
    """Mock the pipeline instance."""
    with patch("app.api.pipelines.get_pipeline") as mock_get:
        mock_instance = MagicMock()
        mock_instance.get_last_execution.return_value = None
        mock_instance.get_execution_logs.return_value = []
        mock_get.return_value = mock_instance
        yield mock_instance


class TestTriggerEndpoint:
    """Tests for POST /api/pipelines/morning-report/trigger."""

    def test_trigger_requires_authentication(self, client):
        """AC#10: Endpoint requires authentication."""
        response = client.post("/api/pipelines/morning-report/trigger")
        assert response.status_code == 401

    def test_trigger_success(self, client, mock_verify_jwt, mock_pipeline):
        """AC#10: Successfully trigger pipeline."""
        with patch.dict("app.api.pipelines._pipeline_state", {"is_running": False}):
            response = client.post(
                "/api/pipelines/morning-report/trigger",
                headers={"Authorization": "Bearer valid-token"},
                json={"target_date": "2026-01-05", "force": False},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "running"
            assert data["target_date"] == "2026-01-05"

    def test_trigger_default_date(self, client, mock_verify_jwt, mock_pipeline):
        """AC#10: Default to yesterday if no date provided."""
        with patch.dict("app.api.pipelines._pipeline_state", {"is_running": False}):
            response = client.post(
                "/api/pipelines/morning-report/trigger",
                headers={"Authorization": "Bearer valid-token"},
            )

            assert response.status_code == 200
            data = response.json()
            yesterday = (date.today() - timedelta(days=1)).isoformat()
            assert data["target_date"] == yesterday

    def test_trigger_conflict_when_running(self, client, mock_verify_jwt, mock_pipeline):
        """AC#10: Return 409 if pipeline already running."""
        with patch.dict("app.api.pipelines._pipeline_state", {"is_running": True}):
            response = client.post(
                "/api/pipelines/morning-report/trigger",
                headers={"Authorization": "Bearer valid-token"},
            )

            assert response.status_code == 409
            assert "already running" in response.json()["detail"].lower()


class TestStatusEndpoint:
    """Tests for GET /api/pipelines/morning-report/status."""

    def test_status_requires_authentication(self, client):
        """AC#10: Endpoint requires authentication."""
        response = client.get("/api/pipelines/morning-report/status")
        assert response.status_code == 401

    def test_status_returns_last_run(self, client, mock_verify_jwt, mock_pipeline):
        """AC#10: Return last run information."""
        mock_log = PipelineExecutionLog(
            pipeline_name="morning_report",
            target_date=date(2026, 1, 5),
            status=PipelineStatus.SUCCESS,
            started_at=datetime(2026, 1, 6, 6, 0, 0),
            completed_at=datetime(2026, 1, 6, 6, 2, 30),
            records_processed=15,
        )
        mock_pipeline.get_last_execution.return_value = mock_log

        with patch.dict("app.api.pipelines._pipeline_state", {"is_running": False}):
            response = client.get(
                "/api/pipelines/morning-report/status",
                headers={"Authorization": "Bearer valid-token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["is_running"] is False
            assert data["last_run"] is not None
            assert data["last_run"]["status"] == "success"

    def test_status_no_previous_run(self, client, mock_verify_jwt, mock_pipeline):
        """AC#10: Handle case with no previous runs."""
        mock_pipeline.get_last_execution.return_value = None

        with patch.dict("app.api.pipelines._pipeline_state", {"is_running": False}):
            response = client.get(
                "/api/pipelines/morning-report/status",
                headers={"Authorization": "Bearer valid-token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["last_run"] is None
            assert data["is_running"] is False


class TestLogsEndpoint:
    """Tests for GET /api/pipelines/morning-report/logs."""

    def test_logs_requires_authentication(self, client):
        """AC#10: Endpoint requires authentication."""
        response = client.get("/api/pipelines/morning-report/logs")
        assert response.status_code == 401

    def test_logs_returns_history(self, client, mock_verify_jwt, mock_pipeline):
        """AC#8, AC#10: Return execution history."""
        mock_logs = [
            PipelineExecutionLog(
                pipeline_name="morning_report",
                target_date=date(2026, 1, 5),
                status=PipelineStatus.SUCCESS,
                started_at=datetime(2026, 1, 6, 6, 0, 0),
                records_processed=15,
            ),
            PipelineExecutionLog(
                pipeline_name="morning_report",
                target_date=date(2026, 1, 4),
                status=PipelineStatus.SUCCESS,
                started_at=datetime(2026, 1, 5, 6, 0, 0),
                records_processed=12,
            ),
        ]
        mock_pipeline.get_execution_logs.return_value = mock_logs

        response = client.get(
            "/api/pipelines/morning-report/logs",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_logs_respects_limit(self, client, mock_verify_jwt, mock_pipeline):
        """AC#10: Limit parameter respected."""
        mock_pipeline.get_execution_logs.return_value = []

        response = client.get(
            "/api/pipelines/morning-report/logs?limit=5",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        mock_pipeline.get_execution_logs.assert_called_with(5)

    def test_logs_caps_limit_at_100(self, client, mock_verify_jwt, mock_pipeline):
        """AC#10: Limit capped at 100."""
        mock_pipeline.get_execution_logs.return_value = []

        response = client.get(
            "/api/pipelines/morning-report/logs?limit=500",
            headers={"Authorization": "Bearer valid-token"},
        )

        assert response.status_code == 200
        mock_pipeline.get_execution_logs.assert_called_with(100)


class TestSyncRunEndpoint:
    """Tests for POST /api/pipelines/morning-report/run-sync."""

    def test_run_sync_requires_authentication(self, client):
        """AC#10: Endpoint requires authentication."""
        response = client.post("/api/pipelines/morning-report/run-sync")
        assert response.status_code == 401

    def test_run_sync_success(self, client, mock_verify_jwt):
        """AC#10: Successfully run pipeline synchronously."""
        mock_result = PipelineResult(
            status=PipelineStatus.SUCCESS,
            execution_log=PipelineExecutionLog(
                pipeline_name="morning_report",
                target_date=date(2026, 1, 5),
                status=PipelineStatus.SUCCESS,
                started_at=datetime(2026, 1, 6, 6, 0, 0),
            ),
            summaries_updated=5,
        )

        with patch.dict("app.api.pipelines._pipeline_state", {"is_running": False}):
            with patch("app.api.pipelines.run_morning_report", new_callable=AsyncMock) as mock_run:
                mock_run.return_value = mock_result

                response = client.post(
                    "/api/pipelines/morning-report/run-sync",
                    headers={"Authorization": "Bearer valid-token"},
                    json={"target_date": "2026-01-05"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert data["summaries_updated"] == 5

    def test_run_sync_conflict_when_running(self, client, mock_verify_jwt):
        """AC#10: Return 409 if pipeline already running."""
        with patch.dict("app.api.pipelines._pipeline_state", {"is_running": True}):
            response = client.post(
                "/api/pipelines/morning-report/run-sync",
                headers={"Authorization": "Bearer valid-token"},
            )

            assert response.status_code == 409


class TestEndpointDocumentation:
    """Tests for API documentation."""

    def test_openapi_includes_pipeline_endpoints(self, client):
        """Verify pipeline endpoints are in OpenAPI spec."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi = response.json()
        paths = openapi.get("paths", {})

        assert "/api/pipelines/morning-report/trigger" in paths
        assert "/api/pipelines/morning-report/status" in paths
        assert "/api/pipelines/morning-report/logs" in paths
