"""
Pytest configuration and fixtures for API tests.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import os

# Set test environment variables before importing app
os.environ["SUPABASE_URL"] = "https://test-project.supabase.co"
os.environ["SUPABASE_KEY"] = "test-key"
# Disable scheduler startup on test to avoid blocking
os.environ["POLL_RUN_ON_STARTUP"] = "false"

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    # Mock the database initialization to avoid actual connection attempts
    with patch("app.core.database.mssql_db") as mock_db:
        mock_db.initialize = MagicMock()
        mock_db.dispose = MagicMock()
        mock_db.check_health.return_value = {
            "status": "not_configured",
            "message": "MSSQL connection not configured",
            "connected": False,
        }
        # Mock the scheduler to avoid starting it during tests
        with patch("app.services.scheduler.get_scheduler") as mock_sched:
            mock_scheduler = MagicMock()
            mock_scheduler.start = AsyncMock()
            mock_scheduler.shutdown = AsyncMock()
            mock_scheduler.status.to_dict.return_value = {
                "status": "stopped",
                "last_poll_timestamp": None,
                "last_poll_success": True,
                "last_poll_duration_seconds": None,
                "last_error_message": None,
                "polls_executed": 0,
                "polls_failed": 0,
                "next_poll_scheduled": None,
            }
            mock_sched.return_value = mock_scheduler
            with TestClient(app) as test_client:
                yield test_client


@pytest.fixture
def valid_jwt_payload():
    """Sample JWT payload for testing."""
    return {
        "sub": "123e4567-e89b-12d3-a456-426614174000",
        "email": "test@example.com",
        "role": "authenticated",
        "aud": "authenticated",
        "exp": 9999999999,  # Far future
    }


@pytest.fixture
def mock_verify_jwt(valid_jwt_payload):
    """Mock the JWT verification to return a valid payload."""
    with patch("app.core.security.verify_supabase_jwt", new_callable=AsyncMock) as mock:
        mock.return_value = valid_jwt_payload
        yield mock


@pytest.fixture
def mock_verify_jwt_expired():
    """Mock the JWT verification to raise an expired token error."""
    from fastapi import HTTPException, status

    with patch("app.core.security.verify_supabase_jwt", new_callable=AsyncMock) as mock:
        mock.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
        yield mock


@pytest.fixture
def mock_verify_jwt_invalid():
    """Mock the JWT verification to raise an invalid token error."""
    from fastapi import HTTPException, status

    with patch("app.core.security.verify_supabase_jwt", new_callable=AsyncMock) as mock:
        mock.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        yield mock


@pytest.fixture
def mock_action_engine():
    """Mock ActionEngine for API tests."""
    with patch('app.api.actions.get_action_engine') as mock_get:
        mock_engine = MagicMock()
        mock_get.return_value = mock_engine
        yield mock_engine
