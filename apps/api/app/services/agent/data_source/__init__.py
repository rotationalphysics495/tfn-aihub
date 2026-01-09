"""
Data Source Abstraction Layer (Story 5.2)

Provides a protocol-based abstraction for data access, allowing tools
to query data without knowing the underlying database implementation.

Components:
- DataSource: Protocol defining the data access interface
- DataResult: Response wrapper with source metadata for citations
- SupabaseDataSource: Supabase PostgreSQL implementation
- CompositeDataSource: Router for multi-source configurations
- get_data_source(): Factory function for dependency injection

AC#1: DataSource Protocol Definition
AC#2: SupabaseDataSource Implementation
AC#3: DataResult with Source Metadata
AC#4: CompositeDataSource for Future Multi-Source Routing
AC#5: Factory Function for Data Source Injection
"""

from typing import Optional

from app.services.agent.data_source.protocol import (
    DataSource,
    DataResult,
    Asset,
    OEEMetrics,
    DowntimeEvent,
    ProductionStatus,
    SafetyEvent,
    ShiftTarget,
    FinancialMetrics,
)
from app.services.agent.data_source.exceptions import (
    DataSourceError,
    DataSourceConnectionError,
    DataSourceQueryError,
    DataSourceNotFoundError,
    DataSourceConfigurationError,
)
from app.services.agent.data_source.supabase import SupabaseDataSource
from app.services.agent.data_source.composite import CompositeDataSource
from app.core.config import get_settings

import logging

logger = logging.getLogger(__name__)

# Module-level singleton
_data_source: Optional[DataSource] = None


def get_data_source() -> DataSource:
    """
    Factory function returning configured data source.

    AC#5: Factory Function for Data Source Injection
    - Reads DATA_SOURCE_TYPE from environment
    - Default: "supabase" for direct Supabase access
    - "composite": CompositeDataSource with routing capability

    Returns:
        DataSource implementation instance (singleton)
    """
    global _data_source

    if _data_source is not None:
        return _data_source

    settings = get_settings()
    source_type = getattr(settings, 'data_source_type', 'supabase')

    if source_type == "supabase":
        _data_source = SupabaseDataSource()
        logger.info("Initialized SupabaseDataSource")
    elif source_type == "composite":
        # Future: Configure with MSSQL secondary source
        _data_source = CompositeDataSource(
            primary=SupabaseDataSource()
        )
        logger.info("Initialized CompositeDataSource")
    else:
        logger.warning(
            f"Unknown data source type: {source_type}, defaulting to Supabase"
        )
        _data_source = SupabaseDataSource()

    return _data_source


def reset_data_source() -> None:
    """
    Reset singleton for testing.

    Allows tests to reset the global instance to ensure
    clean state between test runs.
    """
    global _data_source
    _data_source = None


# Re-export key classes for convenient imports
__all__ = [
    # Protocol and models
    "DataSource",
    "DataResult",
    "Asset",
    "OEEMetrics",
    "DowntimeEvent",
    "ProductionStatus",
    "SafetyEvent",
    "ShiftTarget",
    "FinancialMetrics",
    # Exceptions
    "DataSourceError",
    "DataSourceConnectionError",
    "DataSourceQueryError",
    "DataSourceNotFoundError",
    "DataSourceConfigurationError",
    # Implementations
    "SupabaseDataSource",
    "CompositeDataSource",
    # Factory
    "get_data_source",
    "reset_data_source",
]
