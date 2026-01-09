# Story 5.2: Data Access Abstraction Layer

Status: ready-for-dev

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

- [ ] Task 1: Define DataSource Protocol (AC: #1)
  - [ ] 1.1 Create `apps/api/app/services/agent/data_source/__init__.py`
  - [ ] 1.2 Create `apps/api/app/services/agent/data_source/protocol.py`
  - [ ] 1.3 Define DataSource Protocol with typing.Protocol
  - [ ] 1.4 Define async method signatures for all data operations
  - [ ] 1.5 Add docstrings explaining expected behavior
  - [ ] 1.6 Create unit tests for protocol compliance

- [ ] Task 2: Create DataResult Model (AC: #3)
  - [ ] 2.1 Add DataResult to `apps/api/app/models/agent.py`
  - [ ] 2.2 Define data field (generic Any type)
  - [ ] 2.3 Define source_name field (str)
  - [ ] 2.4 Define table_name field (str)
  - [ ] 2.5 Define query_timestamp field (datetime)
  - [ ] 2.6 Define optional query field for debugging

- [ ] Task 3: Implement SupabaseDataSource (AC: #2, #4, #5, #6, #7)
  - [ ] 3.1 Create `apps/api/app/services/agent/data_source/supabase.py`
  - [ ] 3.2 Implement get_asset(asset_id) method
  - [ ] 3.3 Implement get_asset_by_name(name) with fuzzy matching
  - [ ] 3.4 Implement get_assets_by_area(area) method
  - [ ] 3.5 Implement get_oee(asset_id, start, end) method
  - [ ] 3.6 Implement get_oee_by_area(area, start, end) method
  - [ ] 3.7 Implement get_downtime(asset_id, start, end) method
  - [ ] 3.8 Implement get_downtime_by_area(area, start, end) method
  - [ ] 3.9 Implement get_live_snapshot(asset_id) method
  - [ ] 3.10 Implement get_live_snapshots_by_area(area) method
  - [ ] 3.11 Implement get_shift_target(asset_id) method
  - [ ] 3.12 Wrap all responses in DataResult
  - [ ] 3.13 Create comprehensive unit tests

- [ ] Task 4: Implement CompositeDataSource (AC: #8)
  - [ ] 4.1 Create `apps/api/app/services/agent/data_source/composite.py`
  - [ ] 4.2 Implement CompositeDataSource class
  - [ ] 4.3 Add data_sources list for multiple sources
  - [ ] 4.4 Implement routing logic (for now, delegate to primary)
  - [ ] 4.5 Add TODO comments for future MSSQL routing
  - [ ] 4.6 Create unit tests for composite behavior

- [ ] Task 5: Create Factory Function (AC: #9)
  - [ ] 5.1 Add get_data_source() to data_source/__init__.py
  - [ ] 5.2 Implement singleton pattern
  - [ ] 5.3 Read configuration from settings
  - [ ] 5.4 Return appropriate DataSource implementation
  - [ ] 5.5 Create unit tests for factory

- [ ] Task 6: Add Fuzzy Name Matching (AC: #4)
  - [ ] 6.1 Implement fuzzy_match_asset() helper function
  - [ ] 6.2 Use PostgreSQL ILIKE for pattern matching
  - [ ] 6.3 Return list of similar assets when exact match fails
  - [ ] 6.4 Create tests for fuzzy matching

- [ ] Task 7: Integration Testing (AC: All)
  - [ ] 7.1 Create integration tests with mock Supabase
  - [ ] 7.2 Test all DataSource methods
  - [ ] 7.3 Verify DataResult format for citations
  - [ ] 7.4 Test error handling and edge cases

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

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

