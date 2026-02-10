# Story 5.2: Data Access Abstraction Layer

Status: In Review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want **a data access abstraction layer that tools use instead of direct database queries**,
so that **we can add MSSQL as a data source in the future without modifying tools**.

## Acceptance Criteria

1. **DataSource Protocol Definition**
   - GIVEN a developer needs to implement a data source
   - WHEN they reference the DataSource Protocol
   - THEN the protocol defines async methods for all common data operations
   - AND each method returns a DataResult with data + source metadata
   - AND the protocol is compatible with both Supabase and future MSSQL

2. **Supabase DataSource Implementation**
   - GIVEN the Supabase database is configured
   - WHEN the SupabaseDataSource is instantiated
   - THEN it connects using existing Supabase client from config
   - AND all protocol methods are implemented
   - AND queries use existing Supabase table structures

3. **DataResult Response Format**
   - GIVEN any data source method is called
   - WHEN data is returned
   - THEN the response is wrapped in a DataResult object
   - AND includes source_name (e.g., "supabase")
   - AND includes table_name (e.g., "daily_summaries")
   - AND includes query_timestamp (when the query was executed)
   - AND this metadata is available for citation generation

4. **Asset Data Methods**
   - GIVEN a tool needs asset information
   - WHEN calling `data_source.get_asset(asset_id)` or `get_asset_by_name(name)`
   - THEN the asset data is returned from the configured data source
   - AND the tool does not need to know which database was queried
   - AND fuzzy name matching is supported for user queries

5. **OEE Data Methods**
   - GIVEN a tool needs OEE metrics
   - WHEN calling `data_source.get_oee(asset_id, start_date, end_date)`
   - THEN OEE data from daily_summaries is returned
   - AND data can be filtered by asset, area, or plant-wide
   - AND includes availability, performance, quality breakdown

6. **Downtime Data Methods**
   - GIVEN a tool needs downtime information
   - WHEN calling `data_source.get_downtime(asset_id, start_date, end_date)`
   - THEN downtime records are returned with reasons and durations
   - AND Pareto analysis can be performed on the results
   - AND data supports asset or area-level queries

7. **Live Data Methods**
   - GIVEN a tool needs real-time production status
   - WHEN calling `data_source.get_live_snapshot(asset_id)`
   - THEN current production data from live_snapshots is returned
   - AND includes data freshness timestamp
   - AND supports filtering by area

8. **CompositeDataSource Router (Future-Ready)**
   - GIVEN multiple data sources may be configured in the future
   - WHEN the CompositeDataSource is used
   - THEN it can route queries to the appropriate source
   - AND for now, it simply delegates to SupabaseDataSource
   - AND the architecture supports adding MSSQLDataSource later

9. **Factory Function**
   - GIVEN the application needs a data source instance
   - WHEN calling `get_data_source()`
   - THEN a properly configured data source is returned
   - AND the implementation is determined by environment configuration
   - AND the same instance is reused (singleton pattern)

## Tasks / Subtasks

- [x] Task 1: Define DataSource Protocol (AC: #1)
  - [x] 1.1 Create `apps/api/app/services/agent/data_source/__init__.py`
  - [x] 1.2 Create `apps/api/app/services/agent/data_source/protocol.py`
  - [x] 1.3 Define DataSource Protocol with typing.Protocol
  - [x] 1.4 Define async method signatures for all data operations
  - [x] 1.5 Add docstrings explaining expected behavior
  - [x] 1.6 Create unit tests for protocol compliance

- [x] Task 2: Create DataResult Model (AC: #3)
  - [x] 2.1 Add DataResult to protocol.py (kept with protocol for cohesion)
  - [x] 2.2 Define data field (generic Any type)
  - [x] 2.3 Define source_name field (str)
  - [x] 2.4 Define table_name field (str)
  - [x] 2.5 Define query_timestamp field (datetime)
  - [x] 2.6 Define optional query field for debugging

- [x] Task 3: Implement SupabaseDataSource (AC: #2, #4, #5, #6, #7)
  - [x] 3.1 Create `apps/api/app/services/agent/data_source/supabase.py`
  - [x] 3.2 Implement get_asset(asset_id) method
  - [x] 3.3 Implement get_asset_by_name(name) with fuzzy matching
  - [x] 3.4 Implement get_assets_by_area(area) method
  - [x] 3.5 Implement get_oee(asset_id, start, end) method
  - [x] 3.6 Implement get_oee_by_area(area, start, end) method
  - [x] 3.7 Implement get_downtime(asset_id, start, end) method
  - [x] 3.8 Implement get_downtime_by_area(area, start, end) method
  - [x] 3.9 Implement get_live_snapshot(asset_id) method
  - [x] 3.10 Implement get_live_snapshots_by_area(area) method
  - [x] 3.11 Implement get_shift_target(asset_id) method
  - [x] 3.12 Wrap all responses in DataResult
  - [x] 3.13 Create comprehensive unit tests

- [x] Task 4: Implement CompositeDataSource (AC: #8)
  - [x] 4.1 Create `apps/api/app/services/agent/data_source/composite.py`
  - [x] 4.2 Implement CompositeDataSource class
  - [x] 4.3 Add data_sources list for multiple sources
  - [x] 4.4 Implement routing logic (for now, delegate to primary)
  - [x] 4.5 Add TODO comments for future MSSQL routing
  - [x] 4.6 Create unit tests for composite behavior

- [x] Task 5: Create Factory Function (AC: #9)
  - [x] 5.1 Add get_data_source() to data_source/__init__.py
  - [x] 5.2 Implement singleton pattern
  - [x] 5.3 Read configuration from settings
  - [x] 5.4 Return appropriate DataSource implementation
  - [x] 5.5 Create unit tests for factory

- [x] Task 6: Add Fuzzy Name Matching (AC: #4)
  - [x] 6.1 Implement fuzzy matching in get_asset_by_name()
  - [x] 6.2 Use PostgreSQL ILIKE for pattern matching
  - [x] 6.3 Return list of similar assets via get_similar_assets()
  - [x] 6.4 Create tests for fuzzy matching

- [x] Task 7: Integration Testing (AC: All)
  - [x] 7.1 Create integration tests with mock Supabase
  - [x] 7.2 Test all DataSource methods
  - [x] 7.3 Verify DataResult format for citations
  - [x] 7.4 Test error handling and edge cases

## Dev Notes

### Architecture Compliance

This story implements the **Data Access Abstraction** from the PRD Addendum (Section 5.2). It creates the data layer that all tools (Stories 5.3-5.6) will use, ensuring tools are decoupled from specific database implementations.

**Location:** `apps/api/` (Python FastAPI Backend)
**Module:** `app/services/agent/data_source/` for data access logic
**Pattern:** Protocol-based abstraction, adapter pattern

### Technical Requirements

**Data Access Architecture Diagram:**
```
Tool (e.g., AssetLookupTool)
    |
    v
+-------------------+
| get_data_source() |
| (factory)         |
+-------------------+
    |
    v
+-------------------+
| CompositeDataSource|
| (router)          |
+-------------------+
    |
    +---> SupabaseDataSource (primary)
    |         |
    |         v
    |     Supabase PostgreSQL
    |
    +---> MSSQLDataSource (future)
              |
              v
          MSSQL (read-only)
```

### DataSource Protocol Definition

**protocol.py Core Structure:**
```python
from typing import Protocol, Optional, List
from datetime import datetime, date
from app.models.agent import DataResult

class DataSource(Protocol):
    """Protocol defining the interface for all data sources."""

    # Asset methods
    async def get_asset(self, asset_id: str) -> DataResult:
        """Get asset by ID."""
        ...

    async def get_asset_by_name(self, name: str) -> DataResult:
        """Get asset by name with fuzzy matching."""
        ...

    async def get_assets_by_area(self, area: str) -> DataResult:
        """Get all assets in an area."""
        ...

    async def get_similar_assets(self, name: str, limit: int = 5) -> DataResult:
        """Get assets with similar names for suggestions."""
        ...

    # OEE methods
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
        """Get aggregated OEE for all assets in an area."""
        ...

    # Downtime methods
    async def get_downtime(
        self,
        asset_id: str,
        start_date: date,
        end_date: date
    ) -> DataResult:
        """Get downtime records for an asset."""
        ...

    async def get_downtime_by_area(
        self,
        area: str,
        start_date: date,
        end_date: date
    ) -> DataResult:
        """Get downtime records for all assets in an area."""
        ...

    # Live data methods
    async def get_live_snapshot(self, asset_id: str) -> DataResult:
        """Get current live snapshot for an asset."""
        ...

    async def get_live_snapshots_by_area(self, area: str) -> DataResult:
        """Get live snapshots for all assets in an area."""
        ...

    # Target methods
    async def get_shift_target(self, asset_id: str) -> DataResult:
        """Get shift target for an asset."""
        ...
```

### DataResult Model

**models/agent.py Addition:**
```python
from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime

class DataResult(BaseModel):
    """Wrapper for data source responses with metadata for citations."""
    data: Any  # The actual query result
    source_name: str  # e.g., "supabase", "mssql"
    table_name: str  # e.g., "daily_summaries", "assets"
    query_timestamp: datetime = Field(default_factory=datetime.utcnow)
    query: Optional[str] = None  # SQL query for debugging (optional)
    row_count: int = 0  # Number of rows returned

    def to_citation(self) -> "Citation":
        """Convert DataResult to Citation for tool responses."""
        return Citation(
            source=f"{self.source_name}.{self.table_name}",
            query=self.query or f"Query on {self.table_name}",
            timestamp=self.query_timestamp,
            table=self.table_name
        )
```

### SupabaseDataSource Implementation

**supabase.py Core Structure:**
```python
from typing import Optional, List
from datetime import datetime, date
from app.core.database import supabase
from app.models.agent import DataResult
import logging

logger = logging.getLogger(__name__)

class SupabaseDataSource:
    """Supabase implementation of the DataSource protocol."""

    def __init__(self):
        self.client = supabase
        self.source_name = "supabase"

    async def get_asset(self, asset_id: str) -> DataResult:
        """Get asset by ID."""
        result = await self.client.table("assets").select("*").eq(
            "id", asset_id
        ).single().execute()

        return DataResult(
            data=result.data,
            source_name=self.source_name,
            table_name="assets",
            query_timestamp=datetime.utcnow(),
            row_count=1 if result.data else 0
        )

    async def get_asset_by_name(self, name: str) -> DataResult:
        """Get asset by name with fuzzy matching."""
        # Try exact match first
        result = await self.client.table("assets").select("*").ilike(
            "name", name
        ).limit(1).execute()

        if not result.data:
            # Try fuzzy match
            result = await self.client.table("assets").select("*").ilike(
                "name", f"%{name}%"
            ).limit(1).execute()

        return DataResult(
            data=result.data[0] if result.data else None,
            source_name=self.source_name,
            table_name="assets",
            query_timestamp=datetime.utcnow(),
            row_count=len(result.data) if result.data else 0
        )

    async def get_oee(
        self,
        asset_id: str,
        start_date: date,
        end_date: date
    ) -> DataResult:
        """Get OEE metrics for an asset in date range."""
        result = await self.client.table("daily_summaries").select(
            "date, oee, availability, performance, quality"
        ).eq(
            "asset_id", asset_id
        ).gte(
            "date", start_date.isoformat()
        ).lte(
            "date", end_date.isoformat()
        ).order("date", desc=True).execute()

        return DataResult(
            data=result.data,
            source_name=self.source_name,
            table_name="daily_summaries",
            query_timestamp=datetime.utcnow(),
            row_count=len(result.data) if result.data else 0
        )

    async def get_live_snapshot(self, asset_id: str) -> DataResult:
        """Get current live snapshot for an asset."""
        result = await self.client.table("live_snapshots").select(
            "*, assets!inner(name, area)"
        ).eq(
            "asset_id", asset_id
        ).order(
            "snapshot_time", desc=True
        ).limit(1).execute()

        return DataResult(
            data=result.data[0] if result.data else None,
            source_name=self.source_name,
            table_name="live_snapshots",
            query_timestamp=datetime.utcnow(),
            row_count=1 if result.data else 0
        )

    # ... additional methods follow same pattern
```

### CompositeDataSource (Future-Ready)

**composite.py Core Structure:**
```python
from typing import Optional, List
from datetime import date
from app.services.agent.data_source.supabase import SupabaseDataSource
from app.models.agent import DataResult

class CompositeDataSource:
    """
    Routes queries to appropriate data source.

    Currently delegates everything to Supabase.
    Future: Add MSSQLDataSource and routing logic based on data type/freshness.
    """

    def __init__(self):
        self.primary = SupabaseDataSource()
        # TODO: Add MSSQLDataSource for live queries when available
        # self.mssql = MSSQLDataSource()

    async def get_asset(self, asset_id: str) -> DataResult:
        # Assets always come from Supabase (Plant Object Model)
        return await self.primary.get_asset(asset_id)

    async def get_oee(
        self,
        asset_id: str,
        start_date: date,
        end_date: date
    ) -> DataResult:
        # Historical data from Supabase cache
        # TODO: Route to MSSQL for real-time if needed
        return await self.primary.get_oee(asset_id, start_date, end_date)

    async def get_live_snapshot(self, asset_id: str) -> DataResult:
        # Live data from Supabase cache (populated by polling pipeline)
        # TODO: Route to MSSQL for direct real-time queries
        return await self.primary.get_live_snapshot(asset_id)

    # ... delegate all other methods to primary
```

### Factory Function

**__init__.py:**
```python
from typing import Optional
from app.services.agent.data_source.composite import CompositeDataSource
from app.core.config import settings

_data_source_instance: Optional[CompositeDataSource] = None

def get_data_source() -> CompositeDataSource:
    """
    Factory function returning singleton data source instance.

    Returns CompositeDataSource which routes to appropriate backend.
    """
    global _data_source_instance
    if _data_source_instance is None:
        _data_source_instance = CompositeDataSource()
    return _data_source_instance
```

### Supabase Tables Used

| Method | Primary Table | Join Tables |
|--------|--------------|-------------|
| get_asset | `assets` | - |
| get_asset_by_name | `assets` | - |
| get_assets_by_area | `assets` | - |
| get_oee | `daily_summaries` | `assets` |
| get_oee_by_area | `daily_summaries` | `assets` |
| get_downtime | `daily_summaries` | `assets` |
| get_live_snapshot | `live_snapshots` | `assets` |
| get_shift_target | `shift_targets` | `assets` |

### Project Structure Notes

**Files to create:**
```
apps/api/
├── app/
│   ├── services/
│   │   └── agent/
│   │       └── data_source/
│   │           ├── __init__.py       # Factory function
│   │           ├── protocol.py       # DataSource Protocol
│   │           ├── supabase.py       # Supabase implementation
│   │           └── composite.py      # Router (future-ready)
│   └── models/
│       └── agent.py                  # Add DataResult model
```

### Dependencies

**Story Dependencies:**
- Story 1.3 (Plant Object Model Schema) - Assets table structure
- Story 1.4 (Analytical Cache Schema) - daily_summaries, live_snapshots tables
- Story 5.1 (Agent Framework) - Base classes and patterns

**Blocked By:** Story 5.1

**Enables:**
- Story 5.3 (Asset Lookup Tool) - Uses data_source.get_asset()
- Story 5.4 (OEE Query Tool) - Uses data_source.get_oee()
- Story 5.5 (Downtime Analysis Tool) - Uses data_source.get_downtime()
- Story 5.6 (Production Status Tool) - Uses data_source.get_live_snapshot()

### Testing Strategy

1. **Unit Tests:**
   - Protocol compliance verification
   - Each SupabaseDataSource method with mock client
   - DataResult creation and to_citation()
   - Factory singleton behavior
   - Fuzzy name matching

2. **Integration Tests:**
   - Full data retrieval with test database
   - Complex queries (joins, aggregations)
   - Edge cases (no data, null values)
   - Error handling

3. **Manual Testing:**
   - Query real Supabase data
   - Verify citation metadata is correct
   - Test fuzzy matching with various inputs

### Error Handling Patterns

```python
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class SupabaseDataSource:
    async def get_asset(self, asset_id: str) -> DataResult:
        try:
            result = await self.client.table("assets").select("*").eq(
                "id", asset_id
            ).single().execute()
            return DataResult(
                data=result.data,
                source_name=self.source_name,
                table_name="assets",
                query_timestamp=datetime.utcnow(),
                row_count=1 if result.data else 0
            )
        except Exception as e:
            logger.error(f"Failed to get asset {asset_id}: {e}")
            # Return empty result with metadata for citation
            return DataResult(
                data=None,
                source_name=self.source_name,
                table_name="assets",
                query_timestamp=datetime.utcnow(),
                row_count=0,
                query=f"Failed: {str(e)}"
            )
```

### NFR Compliance

- **NFR1 (Accuracy):** DataResult includes source metadata for accurate citations
- **NFR3 (Read-Only):** All methods are read-only queries
- **NFR5 (Tool Extensibility):** Protocol-based design supports adding MSSQL without modifying tools

### References

- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#5.2 Data Access Abstraction] - Design specification
- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#5.4 Supabase Tables Used] - Table mapping
- [Source: _bmad-output/planning-artifacts/epic-5.md#Story 5.2] - Story requirements
- [Source: _bmad/bmm/data/architecture.md#5. Data Models] - Plant Object Model
- [Source: _bmad/bmm/data/architecture.md#Data Layer] - Database architecture

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Implementation Summary

Implemented a complete Data Access Abstraction Layer that enables tools to query manufacturing data without knowing the underlying database implementation. The layer follows a protocol-based design pattern with:

1. **DataSource Protocol**: Defines the interface for all data sources with async methods for assets, OEE, downtime, live snapshots, shift targets, and safety events.

2. **DataResult Model**: Wrapper for all query responses with source metadata (source_name, table_name, query_timestamp) for citation generation.

3. **SupabaseDataSource**: Full implementation of the protocol for Supabase PostgreSQL with:
   - All asset methods including fuzzy name matching via ILIKE
   - OEE and downtime queries with date range filtering
   - Live snapshot retrieval with freshness timestamps
   - Shift target and safety event queries

4. **CompositeDataSource**: Router class that delegates to SupabaseDataSource, with architecture ready for future MSSQL integration.

5. **Factory Function**: `get_data_source()` singleton factory with environment-based configuration.

### Files Created/Modified

**Created:**
- `apps/api/app/services/agent/data_source/protocol.py` - DataSource Protocol, DataResult, domain models
- `apps/api/app/services/agent/data_source/supabase.py` - SupabaseDataSource implementation
- `apps/api/app/services/agent/data_source/composite.py` - CompositeDataSource router
- `apps/api/app/services/agent/data_source/exceptions.py` - Custom exceptions
- `apps/api/tests/services/agent/data_source/__init__.py` - Test package
- `apps/api/tests/services/agent/data_source/test_protocol.py` - Protocol and model tests
- `apps/api/tests/services/agent/data_source/test_supabase.py` - SupabaseDataSource tests
- `apps/api/tests/services/agent/data_source/test_composite.py` - CompositeDataSource tests
- `apps/api/tests/services/agent/data_source/test_factory.py` - Factory function tests
- `apps/api/tests/services/agent/data_source/test_integration.py` - Integration tests

**Modified:**
- `apps/api/app/services/agent/data_source/__init__.py` - Updated with all exports and factory

### Key Decisions

1. **DataResult in protocol.py**: Kept DataResult model in protocol.py alongside the Protocol definition for cohesion, rather than in models/agent.py.

2. **Domain Models**: Created typed domain models (Asset, OEEMetrics, DowntimeEvent, ProductionStatus, ShiftTarget, SafetyEvent) to provide type safety.

3. **Lazy Client Initialization**: SupabaseDataSource uses lazy initialization for the Supabase client to allow dependency injection for testing.

4. **Fuzzy Matching Strategy**: Implemented fuzzy name matching using PostgreSQL ILIKE with fallback from exact match to partial match.

5. **Error Handling**: Raises DataSourceQueryError with context (source_name, table_name) for debuggability.

### Tests Added

83 tests covering:
- DataResult model creation and to_citation_metadata()
- All domain models (Asset, OEEMetrics, DowntimeEvent, etc.)
- Protocol compliance verification
- SupabaseDataSource all methods with mock client
- Fuzzy name matching logic
- CompositeDataSource delegation
- Factory singleton pattern
- Integration flows with mock Supabase

### Test Results

```
============================= test session starts ==============================
collected 83 items

tests/services/agent/data_source/test_composite.py ..................... [ 25%]
tests/services/agent/data_source/test_factory.py .......                 [ 33%]
tests/services/agent/data_source/test_integration.py .........           [ 44%]
tests/services/agent/data_source/test_protocol.py ...................    [ 67%]
tests/services/agent/data_source/test_supabase.py ..................     [100%]

======================= 83 passed, 12 warnings in 0.09s ========================
```

### Notes for Reviewer

1. The implementation follows the same patterns established in Story 5.1 (Agent Framework).

2. DataResult.to_citation_metadata() provides a dict suitable for ManufacturingTool._create_citation().

3. CompositeDataSource includes TODO comments for future MSSQL routing integration.

4. All async methods use the synchronous Supabase client since the `supabase-py` library doesn't have native async support. The methods are still async for consistency with the Protocol definition.

5. Safety events query includes a join to assets table to get asset_name for display.

### Acceptance Criteria Status

- [x] **AC#1: DataSource Protocol Definition** - `protocol.py:161-308`
- [x] **AC#2: Supabase DataSource Implementation** - `supabase.py:53-500`
- [x] **AC#3: DataResult Response Format** - `protocol.py:122-158`
- [x] **AC#4: Asset Data Methods** - `supabase.py:125-220`
- [x] **AC#5: OEE Data Methods** - `supabase.py:226-290`
- [x] **AC#6: Downtime Data Methods** - `supabase.py:296-400`
- [x] **AC#7: Live Data Methods** - `supabase.py:406-470`
- [x] **AC#8: CompositeDataSource Router** - `composite.py:20-160`
- [x] **AC#9: Factory Function** - `__init__.py:50-86`

### File List

```
apps/api/app/services/agent/data_source/
├── __init__.py        # Factory function and exports
├── protocol.py        # DataSource Protocol, DataResult, domain models
├── supabase.py        # SupabaseDataSource implementation
├── composite.py       # CompositeDataSource router
└── exceptions.py      # Custom exceptions

apps/api/tests/services/agent/data_source/
├── __init__.py
├── test_protocol.py   # Protocol and model tests
├── test_supabase.py   # SupabaseDataSource tests
├── test_composite.py  # CompositeDataSource tests
├── test_factory.py    # Factory function tests
└── test_integration.py # Integration tests
```
