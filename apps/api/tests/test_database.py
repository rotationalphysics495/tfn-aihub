"""
Tests for MSSQL database connection module.

These tests cover:
- Configuration parsing and validation
- Connection string building
- Health check functionality
- Error handling scenarios
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from sqlalchemy.exc import OperationalError

from app.core.config import Settings


class TestMSSQLSettings:
    """Tests for MSSQL configuration settings."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        with patch.dict("os.environ", {}, clear=True):
            settings = Settings(
                _env_file=None,
                mssql_server="",
                mssql_database="",
                mssql_user="",
                mssql_password="",
            )
            assert settings.mssql_port == 1433
            assert settings.mssql_driver == "ODBC Driver 18 for SQL Server"
            assert settings.mssql_pool_size == 5
            assert settings.mssql_max_overflow == 10
            assert settings.mssql_pool_timeout == 30

    def test_mssql_configured_returns_false_when_missing_required(self):
        """Test that mssql_configured returns False when required settings are missing."""
        settings = Settings(
            _env_file=None,
            mssql_server="server",
            mssql_database="db",
            mssql_user="",  # Missing
            mssql_password="pass",
        )
        assert settings.mssql_configured is False

    def test_mssql_configured_returns_true_when_all_set(self):
        """Test that mssql_configured returns True when all required settings are provided."""
        settings = Settings(
            _env_file=None,
            mssql_server="server",
            mssql_database="db",
            mssql_user="user",
            mssql_password="pass",
        )
        assert settings.mssql_configured is True

    def test_connection_string_empty_when_not_configured(self):
        """Test that connection string is empty when settings are not configured."""
        settings = Settings(
            _env_file=None,
            mssql_server="",
            mssql_database="",
            mssql_user="",
            mssql_password="",
        )
        assert settings.mssql_connection_string == ""

    def test_connection_string_format(self):
        """Test that connection string is properly formatted."""
        settings = Settings(
            _env_file=None,
            mssql_server="myserver",
            mssql_database="mydb",
            mssql_user="myuser",
            mssql_password="mypassword",
            mssql_port=1433,
            mssql_driver="ODBC Driver 18 for SQL Server",
        )
        conn_str = settings.mssql_connection_string
        assert "mssql+pyodbc://" in conn_str
        assert "myserver:1433" in conn_str
        assert "mydb" in conn_str
        assert "TrustServerCertificate=yes" in conn_str

    def test_connection_string_encodes_special_characters(self):
        """Test that special characters in password are URL-encoded."""
        settings = Settings(
            _env_file=None,
            mssql_server="server",
            mssql_database="db",
            mssql_user="user",
            mssql_password="pass@word!#$%",
            mssql_port=1433,
        )
        conn_str = settings.mssql_connection_string
        # @ should be encoded as %40
        assert "%40" in conn_str or "@" not in conn_str.split("://")[1].split("@")[0]
        # The password should be URL encoded
        assert "pass@word" not in conn_str  # Original password should not appear as-is

    def test_connection_string_custom_port(self):
        """Test that custom port is included in connection string."""
        settings = Settings(
            _env_file=None,
            mssql_server="server",
            mssql_database="db",
            mssql_user="user",
            mssql_password="pass",
            mssql_port=1434,
        )
        conn_str = settings.mssql_connection_string
        assert ":1434/" in conn_str

    def test_connection_string_custom_driver(self):
        """Test that custom driver is included in connection string."""
        settings = Settings(
            _env_file=None,
            mssql_server="server",
            mssql_database="db",
            mssql_user="user",
            mssql_password="pass",
            mssql_driver="ODBC Driver 17 for SQL Server",
        )
        conn_str = settings.mssql_connection_string
        # Driver name should be URL encoded
        assert "ODBC+Driver+17" in conn_str


class TestMSSQLDatabase:
    """Tests for MSSQLDatabase class."""

    def test_initial_state(self):
        """Test that database starts uninitialized."""
        from app.core.database import MSSQLDatabase

        db = MSSQLDatabase()
        assert db.is_initialized is False
        assert db.engine is None

    def test_is_configured_checks_settings(self):
        """Test that is_configured property checks settings."""
        from app.core.database import MSSQLDatabase

        db = MSSQLDatabase()

        with patch("app.core.database.get_settings") as mock_settings:
            mock_settings.return_value.mssql_configured = True
            assert db.is_configured is True

            mock_settings.return_value.mssql_configured = False
            assert db.is_configured is False

    def test_initialize_logs_warning_when_not_configured(self):
        """Test that initialize logs warning when MSSQL is not configured."""
        from app.core.database import MSSQLDatabase

        db = MSSQLDatabase()

        with patch("app.core.database.get_settings") as mock_settings:
            mock_settings.return_value.mssql_configured = False
            with patch("app.core.database.logger") as mock_logger:
                db.initialize()
                mock_logger.warning.assert_called_once()
                assert db.is_initialized is False

    def test_get_session_raises_when_not_initialized(self):
        """Test that get_session raises error when not initialized."""
        from app.core.database import MSSQLDatabase, DatabaseNotConfiguredError

        db = MSSQLDatabase()
        with pytest.raises(DatabaseNotConfiguredError):
            db.get_session()

    def test_sanitize_error_message_removes_password(self):
        """Test that error messages are sanitized to remove credentials."""
        from app.core.database import MSSQLDatabase

        db = MSSQLDatabase()

        with patch("app.core.database.get_settings") as mock_settings:
            mock_settings.return_value.mssql_password = "secretpass123"
            mock_settings.return_value.mssql_user = "myuser"

            error_msg = "Connection failed for myuser with password secretpass123"
            sanitized = db._sanitize_error_message(error_msg)

            assert "secretpass123" not in sanitized
            assert "***" in sanitized
            assert "myuser" not in sanitized
            assert "[USER]" in sanitized

    def test_check_health_returns_not_configured(self):
        """Test health check when database is not configured."""
        from app.core.database import MSSQLDatabase

        db = MSSQLDatabase()

        with patch("app.core.database.get_settings") as mock_settings:
            mock_settings.return_value.mssql_configured = False

            health = db.check_health()
            assert health["status"] == "not_configured"
            assert health["connected"] is False

    def test_check_health_returns_not_initialized(self):
        """Test health check when database is configured but not initialized."""
        from app.core.database import MSSQLDatabase

        db = MSSQLDatabase()
        db._initialized = False

        with patch("app.core.database.get_settings") as mock_settings:
            mock_settings.return_value.mssql_configured = True

            health = db.check_health()
            assert health["status"] == "not_initialized"
            assert health["connected"] is False

    def test_dispose_resets_initialized_state(self):
        """Test that dispose resets initialized state."""
        from app.core.database import MSSQLDatabase

        db = MSSQLDatabase()
        db._initialized = True
        db._engine = MagicMock()

        db.dispose()

        assert db.is_initialized is False
        db._engine.dispose.assert_called_once()


class TestHealthEndpoint:
    """Tests for health check endpoint with database status."""

    def test_health_endpoint_returns_database_status(self, client):
        """Test that health endpoint includes database status."""
        with patch("app.api.health.get_mssql_db") as mock_db:
            mock_db.return_value.check_health.return_value = {
                "status": "not_configured",
                "message": "MSSQL connection not configured",
                "connected": False,
            }

            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert "database" in data
            assert data["database"]["status"] == "not_configured"
            assert data["database"]["connected"] is False

    def test_health_endpoint_returns_503_when_db_unhealthy(self, client):
        """Test that health endpoint returns 503 when database is unhealthy."""
        with patch("app.api.health.get_mssql_db") as mock_db:
            mock_db.return_value.check_health.return_value = {
                "status": "unhealthy",
                "message": "Connection failed",
                "connected": False,
            }

            response = client.get("/health")
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "degraded"

    def test_api_health_endpoint_exists(self, client):
        """Test that /api/health endpoint exists and works."""
        with patch("app.api.health.get_mssql_db") as mock_db:
            mock_db.return_value.check_health.return_value = {
                "status": "not_configured",
                "message": "MSSQL connection not configured",
                "connected": False,
            }

            response = client.get("/api/health")
            assert response.status_code == 200


class TestDatabaseModule:
    """Tests for database module functions."""

    def test_get_mssql_db_returns_singleton(self):
        """Test that get_mssql_db returns the global instance."""
        from app.core.database import get_mssql_db, mssql_db

        assert get_mssql_db() is mssql_db

    def test_initialize_database_handles_connection_error(self):
        """Test that initialize_database handles connection errors gracefully."""
        from app.core.database import initialize_database, mssql_db, DatabaseConnectionError

        with patch.object(mssql_db, "initialize") as mock_init:
            mock_init.side_effect = DatabaseConnectionError("Connection failed")

            with patch("app.core.database.logger") as mock_logger:
                # Should not raise
                initialize_database()
                mock_logger.warning.assert_called()

    def test_shutdown_database_disposes_connections(self):
        """Test that shutdown_database properly disposes connections."""
        from app.core.database import shutdown_database, mssql_db

        with patch.object(mssql_db, "dispose") as mock_dispose:
            shutdown_database()
            mock_dispose.assert_called_once()


class TestEnvironmentVariables:
    """Tests for environment variable handling."""

    def test_settings_reads_from_environment(self):
        """Test that settings reads MSSQL config from environment variables."""
        env_vars = {
            "MSSQL_SERVER": "test-server",
            "MSSQL_DATABASE": "test-db",
            "MSSQL_USER": "test-user",
            "MSSQL_PASSWORD": "test-pass",
            "MSSQL_PORT": "1434",
            "MSSQL_DRIVER": "Test Driver",
            "MSSQL_POOL_SIZE": "10",
            "MSSQL_MAX_OVERFLOW": "20",
            "MSSQL_POOL_TIMEOUT": "60",
        }

        with patch.dict("os.environ", env_vars, clear=False):
            settings = Settings(_env_file=None)
            assert settings.mssql_server == "test-server"
            assert settings.mssql_database == "test-db"
            assert settings.mssql_user == "test-user"
            assert settings.mssql_password == "test-pass"
            assert settings.mssql_port == 1434
            assert settings.mssql_driver == "Test Driver"
            assert settings.mssql_pool_size == 10
            assert settings.mssql_max_overflow == 20
            assert settings.mssql_pool_timeout == 60

    def test_settings_uses_defaults_for_optional_vars(self):
        """Test that settings uses defaults when optional vars are not set."""
        env_vars = {
            "MSSQL_SERVER": "test-server",
            "MSSQL_DATABASE": "test-db",
            "MSSQL_USER": "test-user",
            "MSSQL_PASSWORD": "test-pass",
        }

        with patch.dict("os.environ", env_vars, clear=False):
            settings = Settings(_env_file=None)
            assert settings.mssql_port == 1433
            assert settings.mssql_driver == "ODBC Driver 18 for SQL Server"


class TestErrorHandling:
    """Tests for error handling in database module."""

    def test_database_error_base_exception(self):
        """Test DatabaseError base exception."""
        from app.core.database import DatabaseError

        error = DatabaseError("Test error")
        assert str(error) == "Test error"

    def test_database_connection_error(self):
        """Test DatabaseConnectionError exception."""
        from app.core.database import DatabaseConnectionError

        error = DatabaseConnectionError("Connection failed")
        assert str(error) == "Connection failed"

    def test_database_not_configured_error(self):
        """Test DatabaseNotConfiguredError exception."""
        from app.core.database import DatabaseNotConfiguredError

        error = DatabaseNotConfiguredError("Not configured")
        assert str(error) == "Not configured"

    def test_session_scope_handles_sqlalchemy_error(self):
        """Test that session_scope handles SQLAlchemy errors properly."""
        from app.core.database import MSSQLDatabase, DatabaseError
        from sqlalchemy.exc import SQLAlchemyError

        db = MSSQLDatabase()
        db._initialized = True

        mock_session = MagicMock()
        mock_session.commit.side_effect = SQLAlchemyError("DB Error")

        mock_factory = MagicMock(return_value=mock_session)
        db._session_factory = mock_factory

        with patch("app.core.database.get_settings") as mock_settings:
            mock_settings.return_value.mssql_password = ""
            mock_settings.return_value.mssql_user = ""

            with pytest.raises(DatabaseError):
                with db.session_scope() as session:
                    pass  # The error occurs on commit

            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()
