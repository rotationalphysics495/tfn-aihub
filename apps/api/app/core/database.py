"""
MSSQL Database Connection Module

Provides secure read-only connection to the source manufacturing MSSQL database
using SQLAlchemy ORM with pyodbc driver.

Security Note: The MSSQL user MUST be configured with read-only permissions
at the database level. Application-level enforcement is not sufficient.
"""

import logging
from typing import Generator, Optional
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import create_engine, text, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.pool import QueuePool

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Base exception for database-related errors."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    pass


class DatabaseNotConfiguredError(DatabaseError):
    """Raised when database is not properly configured."""
    pass


class MSSQLDatabase:
    """
    MSSQL Database connection manager with connection pooling and health checks.

    This class manages the SQLAlchemy engine and session factory for the
    read-only MSSQL connection.
    """

    def __init__(self):
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._initialized: bool = False

    def initialize(self) -> None:
        """
        Initialize the database engine and session factory.

        Raises:
            DatabaseNotConfiguredError: If required MSSQL settings are missing.
            DatabaseConnectionError: If initial connection test fails.
        """
        settings = get_settings()

        if not settings.mssql_configured:
            logger.warning(
                "MSSQL connection not configured. "
                "Set MSSQL_SERVER, MSSQL_DATABASE, MSSQL_USER, and MSSQL_PASSWORD."
            )
            self._initialized = False
            return

        try:
            self._engine = create_engine(
                settings.mssql_connection_string,
                poolclass=QueuePool,
                pool_size=settings.mssql_pool_size,
                max_overflow=settings.mssql_max_overflow,
                pool_timeout=settings.mssql_pool_timeout,
                pool_pre_ping=True,  # Verify connections before use
                echo=settings.debug,  # Log SQL in debug mode
            )

            # Register event listener for connection checkout
            @event.listens_for(self._engine, "checkout")
            def receive_checkout(dbapi_connection, connection_record, connection_proxy):
                """Log connection checkout events in debug mode."""
                if settings.debug:
                    logger.debug("Database connection checked out from pool")

            self._session_factory = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False,
            )

            # Test the connection
            self._test_connection()

            self._initialized = True
            logger.info("MSSQL database connection initialized successfully")

        except OperationalError as e:
            # Sanitize error message to remove any potential credential exposure
            sanitized_error = self._sanitize_error_message(str(e))
            logger.error(f"Failed to initialize MSSQL connection: {sanitized_error}")
            raise DatabaseConnectionError(
                f"Failed to connect to MSSQL database: {sanitized_error}"
            ) from None
        except Exception as e:
            sanitized_error = self._sanitize_error_message(str(e))
            logger.error(f"Unexpected error initializing MSSQL: {sanitized_error}")
            raise DatabaseConnectionError(
                f"Unexpected database error: {sanitized_error}"
            ) from None

    def _test_connection(self) -> None:
        """Test database connectivity with a simple query."""
        if self._engine is None:
            raise DatabaseNotConfiguredError("Database engine not initialized")

        with self._engine.connect() as conn:
            conn.execute(text("SELECT 1"))

    def _sanitize_error_message(self, message: str) -> str:
        """Remove sensitive information from error messages."""
        settings = get_settings()
        sanitized = message

        # Remove password if present
        if settings.mssql_password:
            sanitized = sanitized.replace(settings.mssql_password, "***")

        # Remove user if present
        if settings.mssql_user:
            sanitized = sanitized.replace(settings.mssql_user, "[USER]")

        return sanitized

    @property
    def is_initialized(self) -> bool:
        """Check if database is initialized."""
        return self._initialized

    @property
    def is_configured(self) -> bool:
        """Check if database settings are configured."""
        return get_settings().mssql_configured

    @property
    def engine(self) -> Optional[Engine]:
        """Get the SQLAlchemy engine."""
        return self._engine

    def get_session(self) -> Session:
        """
        Get a new database session.

        Returns:
            Session: A new SQLAlchemy session.

        Raises:
            DatabaseNotConfiguredError: If database is not initialized.
        """
        if not self._initialized or self._session_factory is None:
            raise DatabaseNotConfiguredError(
                "Database not initialized. Call initialize() first or check configuration."
            )
        return self._session_factory()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.

        Usage:
            with mssql_db.session_scope() as session:
                result = session.execute(text("SELECT * FROM table"))

        Yields:
            Session: A database session that will be automatically closed.

        Raises:
            DatabaseNotConfiguredError: If database is not initialized.
            DatabaseError: If a database operation fails.
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            sanitized_error = self._sanitize_error_message(str(e))
            logger.error(f"Database error in session: {sanitized_error}")
            raise DatabaseError(f"Database operation failed: {sanitized_error}") from None
        finally:
            session.close()

    def check_health(self) -> dict:
        """
        Check database health and return status information.

        Returns:
            dict: Health check result with status and details.
        """
        if not self.is_configured:
            return {
                "status": "not_configured",
                "message": "MSSQL connection not configured",
                "connected": False,
            }

        if not self._initialized:
            return {
                "status": "not_initialized",
                "message": "MSSQL connection not initialized",
                "connected": False,
            }

        try:
            self._test_connection()

            # Get pool status if available
            pool_status = {}
            if self._engine is not None and hasattr(self._engine.pool, 'status'):
                pool_status = {
                    "pool_size": self._engine.pool.size(),
                    "checked_out": self._engine.pool.checkedout(),
                    "overflow": self._engine.pool.overflow(),
                }

            return {
                "status": "healthy",
                "message": "MSSQL connection is healthy",
                "connected": True,
                "pool": pool_status,
            }
        except OperationalError as e:
            sanitized_error = self._sanitize_error_message(str(e))
            return {
                "status": "unhealthy",
                "message": f"Connection failed: {sanitized_error}",
                "connected": False,
            }
        except Exception as e:
            sanitized_error = self._sanitize_error_message(str(e))
            return {
                "status": "error",
                "message": f"Health check error: {sanitized_error}",
                "connected": False,
            }

    def dispose(self) -> None:
        """Dispose of the engine and all connections in the pool."""
        if self._engine is not None:
            self._engine.dispose()
            logger.info("MSSQL database connections disposed")
        self._initialized = False


# Global database instance
mssql_db = MSSQLDatabase()


def get_mssql_db() -> MSSQLDatabase:
    """Get the global MSSQL database instance."""
    return mssql_db


def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.

    Usage:
        @router.get("/data")
        async def get_data(db: Session = Depends(get_db_session)):
            result = db.execute(text("SELECT * FROM table"))
            return result.fetchall()

    Yields:
        Session: A database session that will be automatically closed.

    Raises:
        DatabaseNotConfiguredError: If database is not initialized.
    """
    db = mssql_db.get_session()
    try:
        yield db
    finally:
        db.close()


def initialize_database() -> None:
    """
    Initialize the MSSQL database connection.

    This function should be called during application startup.
    It will log a warning if the database is not configured but
    will not raise an exception, allowing the application to run
    without MSSQL connectivity.
    """
    try:
        mssql_db.initialize()
    except DatabaseConnectionError as e:
        logger.warning(f"MSSQL database initialization failed: {e}")
    except Exception as e:
        logger.warning(f"Unexpected error during MSSQL initialization: {e}")


def shutdown_database() -> None:
    """
    Shutdown the MSSQL database connection.

    This function should be called during application shutdown
    to properly dispose of all database connections.
    """
    mssql_db.dispose()
