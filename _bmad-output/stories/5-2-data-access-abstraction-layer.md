# Story 5.2: Data Access Abstraction Layer

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want **a data access abstraction layer that tools use instead of direct database queries**,
so that **we can add MSSQL as a data source in the future without modifying tools**.

## Acceptance Criteria

1. **DataSource Protocol Definition**
   - GIVEN the agent module is loaded
   - WHEN a developer needs to fetch data for a tool
   - THEN a DataSource Protocol is available with async methods for all data access
   - AND the protocol defines methods: get_asset(), get_oee(), get_downtime(), get_production_status(), get_safety_events()
   - AND each method returns a DataResult containing data + source metadata

2. **SupabaseDataSource Implementation**
   - GIVEN the DataSource Protocol is defined
   - WHEN a tool calls `data_source.get_asset(asset_id)`
   - THEN the SupabaseDataSource implementation queries the Supabase PostgreSQL database
   - AND returns data formatted according to the DataResult schema
   - AND the tool does not need to know which database was queried

3. **DataResult with Source Metadata**
   - GIVEN any data source method is called
   - WHEN data is returned
   - THEN the response includes a DataResult object with:
     - data: The actual query results
     - source: The data source identifier (e.g., "supabase")
     - table: The primary table queried
     - query_timestamp: When the query was executed
     - row_count: Number of rows returned
   - AND this metadata is available for citation generation

4. **CompositeDataSource for Future Multi-Source Routing**
   - GIVEN a new data source (MSSQL) is implemented in the future
   - WHEN the CompositeDataSource is configured to use multiple sources
   - THEN existing tools continue to work without modification
   - AND queries are routed to the appropriate source based on data type

5. **Factory Function for Data Source Injection**
   - GIVEN the API server is starting
   - WHEN the agent service is initialized
   - THEN a factory function `get_data_source()` returns the configured data source
   - AND the factory reads from environment configuration (DATA_SOURCE_TYPE)
   - AND the default data source is SupabaseDataSource

6. **Asset Data Access Methods**
   - GIVEN a tool needs asset data
   - WHEN `data_source.get_asset(asset_id)` is called
   - THEN it returns asset metadata (name, area, cost_center, source_id)
   - AND when `data_source.get_asset_by_name(name)` is called
   - THEN it performs fuzzy matching and returns the best match or None

7. **OEE Data Access Methods**
   - GIVEN a tool needs OEE data
   - WHEN `data_source.get_oee(asset_id, start_date, end_date)` is called
   - THEN it returns OEE metrics from daily_summaries table
   - AND when `data_source.get_oee_by_area(area, start_date, end_date)` is called
   - THEN it returns aggregated OEE for all assets in that area

8. **Downtime Data Access Methods**
   - GIVEN a tool needs downtime data
   - WHEN `data_source.get_downtime(asset_id, start_date, end_date)` is called
   - THEN it returns downtime events with reasons, durations, and timestamps
   - AND the response includes parsed downtime_reasons JSON from daily_summaries

9. **Production Status Data Access Methods**
   - GIVEN a tool needs live production data
   - WHEN `data_source.get_production_status(asset_id)` is called
   - THEN it returns current output, target, variance from live_snapshots
   - AND the response includes data freshness timestamp
   - AND when `data_source.get_production_status_by_area(area)` is called
   - THEN it returns status for all assets in that area

10. **Error Handling and Graceful Degradation**
    - GIVEN a database query fails
    - WHEN the data source handles the error
    - THEN it raises a DataSourceError with context
    - AND the error message is suitable for logging and user feedback
    - AND partial results are returned if available

## Tasks / Subtasks

- [ ] Task 1: Define DataSource Protocol (AC: #1)
  - [ ] 1.1 Create `apps/api/app/services/agent/data_source/__init__.py`
  - [ ] 1.2 Create `apps/api/app/services/agent/data_source/protocol.py`
  - [ ] 1.3 Define DataResult Pydantic model with data, source, table, query_timestamp, row_count
  - [ ] 1.4 Define DataSource Protocol (typing.Protocol) with all required methods
  - [ ] 1.5 Define type hints for return types (Asset, OEEMetrics, DowntimeEvent, ProductionStatus)
  - [ ] 1.6 Create unit tests for DataResult model

- [ ] Task 2: Create Data Model Types (AC: #3)
  - [ ] 2.1 Create Asset Pydantic model
  - [ ] 2.2 Create OEEMetrics Pydantic model with availability, performance, quality, overall
  - [ ] 2.3 Create DowntimeEvent Pydantic model with reason, duration_minutes, timestamp
  - [ ] 2.4 Create ProductionStatus Pydantic model with output, target, variance, timestamp
  - [ ] 2.5 Create SafetyEvent Pydantic model
  - [ ] 2.6 Add model unit tests

- [ ] Task 3: Implement SupabaseDataSource (AC: #2, #6, #7, #8, #9)
  - [ ] 3.1 Create `apps/api/app/services/agent/data_source/supabase.py`
  - [ ] 3.2 Implement lazy initialization with Supabase client
  - [ ] 3.3 Implement get_asset() method querying assets table
  - [ ] 3.4 Implement get_asset_by_name() with fuzzy matching using ILIKE
  - [ ] 3.5 Implement get_oee() method querying daily_summaries
  - [ ] 3.6 Implement get_oee_by_area() with aggregation
  - [ ] 3.7 Implement get_downtime() method with downtime_reasons parsing
  - [ ] 3.8 Implement get_production_status() querying live_snapshots
  - [ ] 3.9 Implement get_production_status_by_area()
  - [ ] 3.10 Implement get_safety_events() method
  - [ ] 3.11 Add comprehensive unit tests with mocked Supabase client

- [ ] Task 4: Create CompositeDataSource (AC: #4)
  - [ ] 4.1 Create `apps/api/app/services/agent/data_source/composite.py`
  - [ ] 4.2 Define CompositeDataSource class accepting multiple DataSource implementations
  - [ ] 4.3 Implement routing logic (placeholder for future MSSQL)
  - [ ] 4.4 Default to SupabaseDataSource for all methods initially
  - [ ] 4.5 Add configuration for source routing rules
  - [ ] 4.6 Add unit tests for composite routing

- [ ] Task 5: Create Factory Function (AC: #5)
  - [ ] 5.1 Update `apps/api/app/services/agent/data_source/__init__.py` with factory
  - [ ] 5.2 Implement get_data_source() factory function
  - [ ] 5.3 Read DATA_SOURCE_TYPE from environment (default: "supabase")
  - [ ] 5.4 Create singleton instance management
  - [ ] 5.5 Add factory unit tests

- [ ] Task 6: Implement Error Handling (AC: #10)
  - [ ] 6.1 Create DataSourceError exception class
  - [ ] 6.2 Create specific exceptions: ConnectionError, QueryError, NotFoundError
  - [ ] 6.3 Add try/catch blocks in all data source methods
  - [ ] 6.4 Implement logging with full context
  - [ ] 6.5 Add error handling tests

- [ ] Task 7: Add Configuration (AC: #5)
  - [ ] 7.1 Add DATA_SOURCE_TYPE to config.py (default: "supabase")
  - [ ] 7.2 Update .env.example with new variable
  - [ ] 7.3 Create data_source_configured property for validation

- [ ] Task 8: Integration Testing (All ACs)
  - [ ] 8.1 Create integration tests with real Supabase connection (test environment)
  - [ ] 8.2 Test DataResult metadata generation
  - [ ] 8.3 Test error handling scenarios
  - [ ] 8.4 Verify fuzzy matching behavior

## Dev Notes

### Architecture Compliance

This story implements the **Data Access Abstraction Layer** from the PRD Addendum (Section 5.2). It creates a protocol-based abstraction that allows tools to access data without knowing the underlying database, enabling future MSSQL integration without modifying tool implementations.

**Location:** `apps/api/` (Python FastAPI Backend)
**Module:** `app/services/agent/data_source/` for data access abstraction
**Pattern:** Protocol-based dependency injection, async operations, Factory pattern

### Technical Requirements

**Data Access Architecture Diagram:**
```
Tools (Asset Lookup, OEE Query, Downtime Analysis, etc.)
    |
    v
+------------------+
| get_data_source()|
| (Factory)        |
+------------------+
    |
    v
+-------------------+
| DataSource        |
| Protocol          |
| (Interface)       |
+-------------------+
    |
    +---> CompositeDataSource (Router)
              |
              +---> SupabaseDataSource (Active)
              |
              +---> MSSQLDataSource (Future)
```

### DataSource Protocol Definition

**protocol.py Core Structure:**
```python
from typing import Protocol, Optional, List, Any
from datetime import datetime, date
from pydantic import BaseModel, Field


class DataResult(BaseModel):
    """Result wrapper with source metadata for citations."""
    data: Any
    source: str = "supabase"  # Data source identifier
    table: str  # Primary table queried
    query_timestamp: datetime = Field(default_factory=datetime.utcnow)
    row_count: int = 0
    query: Optional[str] = None  # SQL query for debugging/citations


class Asset(BaseModel):
    """Asset metadata model."""
    id: str
    name: str
    source_id: Optional[str] = None
    area: Optional[str] = None
    cost_center_id: Optional[str] = None


class OEEMetrics(BaseModel):
    """OEE breakdown model."""
    asset_id: str
    date: date
    overall: float  # 0-100 percentage
    availability: float
    performance: float
    quality: float
    target: Optional[float] = None


class DowntimeEvent(BaseModel):
    """Downtime event model."""
    asset_id: str
    reason: str
    duration_minutes: float
    timestamp: Optional[datetime] = None
    category: Optional[str] = None  # e.g., "planned", "unplanned"


class ProductionStatus(BaseModel):
    """Real-time production status model."""
    asset_id: str
    asset_name: str
    current_output: int
    target_output: int
    variance: int
    variance_percent: float
    status: str  # "ahead", "on-track", "behind"
    data_timestamp: datetime
    is_stale: bool = False  # True if >30 minutes old


class SafetyEvent(BaseModel):
    """Safety event model."""
    id: str
    asset_id: str
    severity: str  # "critical", "warning", "info"
    description: str
    timestamp: datetime
    status: str  # "open", "investigating", "resolved"
    resolution: Optional[str] = None


class DataSource(Protocol):
    """Protocol defining data access interface for agent tools."""

    async def get_asset(self, asset_id: str) -> DataResult:
        """Get asset by ID."""
        ...

    async def get_asset_by_name(self, name: str) -> DataResult:
        """Get asset by name with fuzzy matching."""
        ...

    async def get_all_assets(self, area: Optional[str] = None) -> DataResult:
        """Get all assets, optionally filtered by area."""
        ...

    async def get_oee(
        self,
        asset_id: str,
        start_date: date,
        end_date: date
    ) -> DataResult:
        """Get OEE metrics for an asset in date range."""
        ...

    async def get_oee_by_area(
        self,
        area: str,
        start_date: date,
        end_date: date
    ) -> DataResult:
        """Get aggregated OEE for an area."""
        ...

    async def get_downtime(
        self,
        asset_id: str,
        start_date: date,
        end_date: date
    ) -> DataResult:
        """Get downtime events for an asset in date range."""
        ...

    async def get_production_status(
        self,
        asset_id: Optional[str] = None
    ) -> DataResult:
        """Get current production status for asset or all assets."""
        ...

    async def get_production_status_by_area(
        self,
        area: str
    ) -> DataResult:
        """Get production status for all assets in an area."""
        ...

    async def get_safety_events(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        severity: Optional[str] = None
    ) -> DataResult:
        """Get safety events with optional filters."""
        ...
```

### SupabaseDataSource Implementation

**supabase.py Core Structure:**
```python
import logging
from datetime import date, datetime
from typing import Optional, List, Any

from supabase import create_client, Client

from app.core.config import get_settings
from app.services.agent.data_source.protocol import (
    DataSource,
    DataResult,
    Asset,
    OEEMetrics,
    DowntimeEvent,
    ProductionStatus,
    SafetyEvent,
)

logger = logging.getLogger(__name__)


class DataSourceError(Exception):
    """Base exception for data source errors."""
    pass


class ConnectionError(DataSourceError):
    """Raised when database connection fails."""
    pass


class QueryError(DataSourceError):
    """Raised when query execution fails."""
    pass


class NotFoundError(DataSourceError):
    """Raised when requested data is not found."""
    pass


class SupabaseDataSource:
    """Supabase implementation of DataSource protocol."""

    def __init__(self):
        self._client: Optional[Client] = None
        self._initialized: bool = False

    def _ensure_initialized(self) -> None:
        """Lazy initialization of Supabase client."""
        if self._initialized and self._client is not None:
            return

        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_key:
            raise ConnectionError(
                "Supabase not configured. Set SUPABASE_URL and SUPABASE_KEY."
            )

        try:
            self._client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            self._initialized = True
            logger.info("SupabaseDataSource initialized")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Supabase: {e}")

    async def get_asset(self, asset_id: str) -> DataResult:
        """Get asset by ID."""
        self._ensure_initialized()

        try:
            response = self._client.table("assets").select("*").eq("id", asset_id).execute()

            if not response.data:
                return DataResult(
                    data=None,
                    source="supabase",
                    table="assets",
                    row_count=0
                )

            asset = Asset(**response.data[0])
            return DataResult(
                data=asset,
                source="supabase",
                table="assets",
                row_count=1
            )
        except Exception as e:
            logger.error(f"Failed to get asset {asset_id}: {e}")
            raise QueryError(f"Failed to get asset: {e}")

    async def get_asset_by_name(self, name: str) -> DataResult:
        """Get asset by name with fuzzy matching using ILIKE."""
        self._ensure_initialized()

        try:
            # Use ILIKE for case-insensitive fuzzy matching
            response = self._client.table("assets").select("*").ilike("name", f"%{name}%").execute()

            if not response.data:
                return DataResult(
                    data=None,
                    source="supabase",
                    table="assets",
                    row_count=0,
                    query=f"SELECT * FROM assets WHERE name ILIKE '%{name}%'"
                )

            # Return best match (first result) and all matches for suggestions
            assets = [Asset(**row) for row in response.data]
            return DataResult(
                data={"best_match": assets[0], "all_matches": assets},
                source="supabase",
                table="assets",
                row_count=len(assets),
                query=f"SELECT * FROM assets WHERE name ILIKE '%{name}%'"
            )
        except Exception as e:
            logger.error(f"Failed to get asset by name {name}: {e}")
            raise QueryError(f"Failed to get asset by name: {e}")

    async def get_oee(
        self,
        asset_id: str,
        start_date: date,
        end_date: date
    ) -> DataResult:
        """Get OEE metrics for an asset in date range."""
        self._ensure_initialized()

        try:
            response = (
                self._client.table("daily_summaries")
                .select("*")
                .eq("asset_id", asset_id)
                .gte("date", start_date.isoformat())
                .lte("date", end_date.isoformat())
                .order("date", desc=True)
                .execute()
            )

            metrics = [
                OEEMetrics(
                    asset_id=row["asset_id"],
                    date=row["date"],
                    overall=row.get("oee", 0),
                    availability=row.get("availability", 0),
                    performance=row.get("performance", 0),
                    quality=row.get("quality", 0),
                    target=row.get("oee_target")
                )
                for row in response.data
            ]

            return DataResult(
                data=metrics,
                source="supabase",
                table="daily_summaries",
                row_count=len(metrics),
                query=f"SELECT * FROM daily_summaries WHERE asset_id='{asset_id}' AND date BETWEEN '{start_date}' AND '{end_date}'"
            )
        except Exception as e:
            logger.error(f"Failed to get OEE for {asset_id}: {e}")
            raise QueryError(f"Failed to get OEE metrics: {e}")

    # ... Additional method implementations follow same pattern
```

### CompositeDataSource Implementation

**composite.py Core Structure:**
```python
from typing import Optional, Dict
from datetime import date

from app.services.agent.data_source.protocol import DataSource, DataResult

import logging

logger = logging.getLogger(__name__)


class CompositeDataSource:
    """
    Routes queries to appropriate data sources.

    Currently defaults all queries to SupabaseDataSource.
    Future: Will route to MSSQL for real-time data when configured.
    """

    def __init__(
        self,
        primary: DataSource,
        secondary: Optional[DataSource] = None,
        routing_config: Optional[Dict[str, str]] = None
    ):
        """
        Initialize composite data source.

        Args:
            primary: Primary data source (Supabase)
            secondary: Secondary data source (future MSSQL)
            routing_config: Mapping of data types to sources
        """
        self.primary = primary
        self.secondary = secondary
        self.routing_config = routing_config or {}

    def _get_source_for(self, data_type: str) -> DataSource:
        """Get appropriate data source for data type."""
        # Future: Route based on config
        # e.g., "live" -> MSSQL, "historical" -> Supabase
        source_name = self.routing_config.get(data_type, "primary")
        if source_name == "secondary" and self.secondary:
            return self.secondary
        return self.primary

    async def get_asset(self, asset_id: str) -> DataResult:
        source = self._get_source_for("asset")
        return await source.get_asset(asset_id)

    async def get_asset_by_name(self, name: str) -> DataResult:
        source = self._get_source_for("asset")
        return await source.get_asset_by_name(name)

    # ... Delegate all other methods to appropriate source
```

### Factory Function

**__init__.py Core Structure:**
```python
from typing import Optional
from app.services.agent.data_source.protocol import DataSource, DataResult
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

    Reads DATA_SOURCE_TYPE from environment:
    - "supabase" (default): Direct Supabase access
    - "composite": CompositeDataSource with routing

    Returns:
        DataSource implementation instance
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
        # Future: Configure with MSSQL secondary
        _data_source = CompositeDataSource(
            primary=SupabaseDataSource()
        )
        logger.info("Initialized CompositeDataSource")
    else:
        logger.warning(f"Unknown data source type: {source_type}, defaulting to Supabase")
        _data_source = SupabaseDataSource()

    return _data_source


def reset_data_source() -> None:
    """Reset singleton for testing."""
    global _data_source
    _data_source = None


# Re-export key classes
__all__ = [
    "DataSource",
    "DataResult",
    "get_data_source",
    "reset_data_source",
    "SupabaseDataSource",
    "CompositeDataSource",
]
```

### Environment Variables

**Add to `apps/api/.env` and config.py:**

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATA_SOURCE_TYPE` | Data source type (supabase, composite) | No | `supabase` |

### Project Structure Notes

**Files to create:**
```
apps/api/
├── app/
│   └── services/
│       └── agent/
│           └── data_source/
│               ├── __init__.py           # Factory function, exports
│               ├── protocol.py           # DataSource Protocol, DataResult, models
│               ├── supabase.py           # SupabaseDataSource implementation
│               └── composite.py          # CompositeDataSource router
```

**Alignment with existing patterns:**
- Follows same async pattern as `text_to_sql/service.py`
- Uses Pydantic models consistent with existing `models/` directory
- Lazy initialization pattern matches `TextToSQLService`
- Factory pattern aligns with `get_text_to_sql_service()`

### Dependencies

**Story Dependencies:**
- Story 5.1 (Agent Framework & Tool Registry) - Tools will inject this data source

**Enables:**
- Stories 5.3-5.6 (Core Tools) - All tools use DataSource instead of direct queries
- Story 5.8 (Tool Response Caching) - Cache key includes DataResult metadata
- Future MSSQL integration without tool modifications

**No new pip dependencies required** - Uses existing `supabase` client already in requirements.txt

### Testing Strategy

1. **Unit Tests:**
   - DataResult model validation
   - Protocol method signatures
   - SupabaseDataSource with mocked client
   - CompositeDataSource routing logic
   - Factory function configuration

2. **Integration Tests:**
   - Real Supabase queries (test environment)
   - DataResult metadata accuracy
   - Error handling scenarios
   - Fuzzy matching behavior

3. **Test Fixtures:**
   ```python
   @pytest.fixture
   def mock_supabase_client():
       client = MagicMock()
       client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
           data=[{"id": "1", "name": "Grinder 5", "area": "Grinding"}]
       )
       return client
   ```

### NFR Compliance

- **NFR3 (Read-Only):** All data access is read-only SELECT queries
- **NFR4 (Agent Honesty):** DataResult includes row_count=0 for no data cases
- **NFR5 (Tool Extensibility):** Protocol allows adding MSSQL without tool changes
- **NFR6 (Response Structure):** DataResult provides consistent metadata for citations

### References

- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#5.2 Data Access Abstraction] - Architecture design
- [Source: _bmad-output/planning-artifacts/epic-5.md#Story 5.2] - Story requirements
- [Source: _bmad/bmm/data/architecture.md#5. Data Models] - Plant Object Model tables
- [Source: apps/api/app/services/ai/text_to_sql/service.py] - Existing service pattern reference
- [Source: _bmad-output/stories/5-1-agent-framework-tool-registry.md] - Previous story context
- [Python typing.Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol) - Protocol pattern reference

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

