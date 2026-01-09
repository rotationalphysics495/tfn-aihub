"""
DataSource Exceptions (Story 5.2)

Custom exceptions for data source operations.
"""


class DataSourceError(Exception):
    """Base exception for data source operations."""

    def __init__(self, message: str, source_name: str = None):
        self.source_name = source_name
        super().__init__(message)


class DataSourceConnectionError(DataSourceError):
    """Raised when connection to data source fails."""

    pass


class DataSourceQueryError(DataSourceError):
    """Raised when a query fails to execute."""

    def __init__(
        self,
        message: str,
        source_name: str = None,
        table_name: str = None,
        query: str = None,
    ):
        self.table_name = table_name
        self.query = query
        super().__init__(message, source_name)


class DataSourceNotFoundError(DataSourceError):
    """Raised when requested data is not found."""

    def __init__(
        self,
        message: str,
        source_name: str = None,
        entity_type: str = None,
        entity_id: str = None,
    ):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(message, source_name)


class DataSourceConfigurationError(DataSourceError):
    """Raised when data source is not properly configured."""

    pass
