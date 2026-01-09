# Story 5.3: Asset Lookup Tool

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **to ask about any asset by name and get its current status and recent performance**,
so that **I can quickly understand how a specific machine is doing**.

## Acceptance Criteria

1. **Asset Lookup by Name**
   - GIVEN a user asks "Tell me about Grinder 5"
   - WHEN the Asset Lookup tool is invoked
   - THEN the response includes:
     - Asset metadata (name, area, cost center)
     - Current status (running/down/idle)
     - Current shift output vs target
     - 7-day average OEE
     - Top downtime reason (from last 7 days)
   - AND all data points include citations

2. **Asset Not Found - Fuzzy Suggestions**
   - GIVEN a user asks about an asset that doesn't exist (e.g., "Tell me about Grinder 12")
   - WHEN the Asset Lookup tool is invoked
   - THEN the response states "I don't have data for [asset name]"
   - AND lists similar assets the user might have meant (using fuzzy name matching)
   - AND response does NOT fabricate data

3. **Asset Exists but No Recent Data**
   - GIVEN the asset exists but has no recent production data
   - WHEN the Asset Lookup tool is invoked
   - THEN the response shows available metadata (name, area, cost center)
   - AND indicates "No production data available for the last 7 days"
   - AND includes citation showing last known data timestamp

4. **Live Status Display**
   - GIVEN the asset has current live_snapshots data
   - WHEN the Asset Lookup tool is invoked
   - THEN the response includes:
     - Current status (running/down/idle based on latest snapshot)
     - Data freshness timestamp
     - Warning if data is stale (>30 minutes old)
   - AND cites the live_snapshots table with timestamp

5. **Performance Summary**
   - GIVEN the asset has daily_summaries data for the last 7 days
   - WHEN the Asset Lookup tool is invoked
   - THEN the response includes:
     - 7-day average OEE percentage
     - OEE trend indicator (improving/stable/declining)
     - Total downtime minutes
     - Top downtime reason with percentage contribution
   - AND cites daily_summaries with date range

6. **Citation Compliance (NFR1)**
   - All factual claims in the response include citations
   - Citations follow format: [Source: table_name @ timestamp] or [Source: table_name date_range]
   - Response includes data freshness indicator

7. **Cache TTL Requirements (NFR7)**
   - Asset metadata: 1 hour TTL
   - Live status data: 60 seconds TTL
   - Performance data (OEE, downtime): 15 minutes TTL

8. **Error Handling**
   - GIVEN any database error occurs
   - WHEN the Asset Lookup tool is invoked
   - THEN a user-friendly error message is returned
   - AND the error is logged with full context
   - AND the agent does NOT fabricate data

## Tasks / Subtasks

- [ ] Task 1: Create Asset Lookup Pydantic Schemas (AC: #1, #6)
  - [ ] 1.1 Create/update `apps/api/app/models/agent.py` with AssetLookupInput schema
  - [ ] 1.2 Define AssetLookupInput: asset_name (str, required), include_performance (bool, default=True), days_back (int, default=7)
  - [ ] 1.3 Define AssetMetadata schema: id, name, source_id, area, cost_center
  - [ ] 1.4 Define AssetStatus schema: status (enum: running/down/idle), last_updated, output_current, output_target, variance, variance_percent
  - [ ] 1.5 Define AssetPerformance schema: avg_oee, oee_trend, total_downtime_minutes, top_downtime_reason, top_downtime_percent
  - [ ] 1.6 Define AssetLookupOutput schema: metadata, current_status, performance, suggestions (for not found), citations, data_freshness

- [ ] Task 2: Implement Asset Lookup Tool Class (AC: #1, #2, #3, #4, #5)
  - [ ] 2.1 Create `apps/api/app/services/agent/tools/asset_lookup.py`
  - [ ] 2.2 Inherit from ManufacturingTool base class (from Story 5.1)
  - [ ] 2.3 Set tool name: "asset_lookup"
  - [ ] 2.4 Set tool description for intent matching: "Look up asset information including current status, production output, and recent performance metrics. Use when user asks about a specific machine or asset."
  - [ ] 2.5 Set args_schema to AssetLookupInput
  - [ ] 2.6 Set citations_required = True
  - [ ] 2.7 Implement async `_arun()` method

- [ ] Task 3: Implement Asset Resolution (AC: #1, #2)
  - [ ] 3.1 Call data_source.get_asset_by_name() for fuzzy name matching
  - [ ] 3.2 If exact match found, proceed to data retrieval
  - [ ] 3.3 If no match, call data_source.get_similar_assets() for suggestions
  - [ ] 3.4 Format "not found" response with suggestions list
  - [ ] 3.5 Ensure response never fabricates data for non-existent assets

- [ ] Task 4: Implement Live Status Retrieval (AC: #4)
  - [ ] 4.1 Call data_source.get_live_snapshot(asset_id)
  - [ ] 4.2 Parse snapshot data for current status (running/down/idle)
  - [ ] 4.3 Calculate output vs target and variance
  - [ ] 4.4 Check data freshness (warn if >30 minutes old)
  - [ ] 4.5 Generate citation for live_snapshots table

- [ ] Task 5: Implement Performance Summary (AC: #5)
  - [ ] 5.1 Call data_source.get_oee(asset_id, start_date, end_date) for 7-day range
  - [ ] 5.2 Calculate average OEE from daily_summaries
  - [ ] 5.3 Calculate OEE trend (compare first 3 days vs last 3 days)
  - [ ] 5.4 Get downtime data via data_source.get_downtime(asset_id, start_date, end_date)
  - [ ] 5.5 Parse downtime_reasons JSON and calculate Pareto for top reason
  - [ ] 5.6 Generate citations for daily_summaries with date range

- [ ] Task 6: Implement No Data Handling (AC: #3)
  - [ ] 6.1 Check if daily_summaries returns empty for date range
  - [ ] 6.2 Check if live_snapshots returns null or stale data
  - [ ] 6.3 Format partial response with available metadata
  - [ ] 6.4 Add "No production data available" message with last known timestamp

- [ ] Task 7: Implement Citation Generation (AC: #6)
  - [ ] 7.1 Generate citation for asset metadata from assets table
  - [ ] 7.2 Generate citation for live status from live_snapshots with timestamp
  - [ ] 7.3 Generate citation for performance from daily_summaries with date range
  - [ ] 7.4 Follow Citation model from Story 4.5 (apps/api/app/models/citation.py)
  - [ ] 7.5 Ensure all factual claims have supporting citations

- [ ] Task 8: Implement Caching (AC: #7)
  - [ ] 8.1 Apply cache decorator from Story 5.8 (or implement inline if 5.8 not complete)
  - [ ] 8.2 Set cache key pattern: `asset_lookup:{user_id}:{asset_name_normalized}`
  - [ ] 8.3 Implement tiered TTL: metadata (1hr), live (60s), performance (15min)
  - [ ] 8.4 Include `cached_at` in response metadata
  - [ ] 8.5 Support force_refresh parameter for cache bypass

- [ ] Task 9: Error Handling (AC: #8)
  - [ ] 9.1 Wrap all data source calls in try/except
  - [ ] 9.2 Log errors with full context (asset_name, operation, error details)
  - [ ] 9.3 Return user-friendly error message (not raw exception)
  - [ ] 9.4 Ensure partial failures still return available data

- [ ] Task 10: Unit Tests
  - [ ] 10.1 Test asset found with full data
  - [ ] 10.2 Test asset not found with suggestions
  - [ ] 10.3 Test asset found but no recent data
  - [ ] 10.4 Test stale live data warning
  - [ ] 10.5 Test OEE trend calculation (improving/stable/declining)
  - [ ] 10.6 Test downtime Pareto calculation
  - [ ] 10.7 Test citation generation
  - [ ] 10.8 Test error handling scenarios

- [ ] Task 11: Integration Tests
  - [ ] 11.1 Test full asset lookup flow with mock data source
  - [ ] 11.2 Test tool registration and discovery
  - [ ] 11.3 Test agent intent matching (verify tool is selected for asset queries)
  - [ ] 11.4 Test cache behavior

## Dev Notes

### Architecture Compliance

This story implements the **Asset Lookup Tool** from the PRD Addendum (FR7.1: Core Operations Tools). It is the first concrete tool implementation that uses the Agent Framework (Story 5.1) and Data Access Layer (Story 5.2).

**Location:** `apps/api/` (Python FastAPI Backend)
**Module:** `app/services/agent/tools/` for tool implementation
**Pattern:** ManufacturingTool inheritance, async operations, structured responses with citations

### Technical Requirements

**Asset Lookup Flow Diagram:**
```
User: "Tell me about Grinder 5"
    |
    v
+-------------------+
| AssetLookupTool   |
| (_arun method)    |
+-------------------+
    |
    +---> 1. Resolve asset name (fuzzy match)
    |         |
    |         v
    |     data_source.get_asset_by_name("Grinder 5")
    |         |
    |         +---> Found? Yes -> Continue
    |         +---> Not Found? -> get_similar_assets() -> Return suggestions
    |
    +---> 2. Get live status
    |         |
    |         v
    |     data_source.get_live_snapshot(asset_id)
    |         |
    |         +---> Parse status, output, target
    |         +---> Check freshness (warn if >30min)
    |
    +---> 3. Get performance (7 days)
    |         |
    |         v
    |     data_source.get_oee(asset_id, T-7, T-0)
    |     data_source.get_downtime(asset_id, T-7, T-0)
    |         |
    |         +---> Calculate avg OEE
    |         +---> Calculate trend
    |         +---> Find top downtime reason
    |
    +---> 4. Build response with citations
              |
              v
          AssetLookupOutput
```

### Tool Implementation Pattern

**asset_lookup.py Core Structure:**
```python
from typing import Type
from pydantic import BaseModel, Field
from datetime import datetime, date, timedelta
from app.services.agent.base import ManufacturingTool, ToolResult
from app.services.agent.data_source import get_data_source
from app.models.agent import AssetLookupInput, AssetLookupOutput
import logging

logger = logging.getLogger(__name__)

class AssetLookupTool(ManufacturingTool):
    """
    Look up asset information including current status and performance.

    Use this tool when the user asks about a specific machine or asset,
    wants to know how an asset is doing, or asks for asset status.
    """

    name: str = "asset_lookup"
    description: str = (
        "Look up asset information including current status, production output, "
        "and recent performance metrics. Use when user asks about a specific "
        "machine or asset like 'How is Grinder 5 doing?' or 'Tell me about [asset name]'."
    )
    args_schema: Type[BaseModel] = AssetLookupInput
    citations_required: bool = True

    async def _arun(
        self,
        asset_name: str,
        include_performance: bool = True,
        days_back: int = 7,
        **kwargs
    ) -> ToolResult:
        """Execute asset lookup and return structured results."""
        data_source = get_data_source()
        citations = []

        try:
            # Step 1: Resolve asset name
            asset_result = await data_source.get_asset_by_name(asset_name)
            citations.append(asset_result.to_citation())

            if not asset_result.data:
                # Asset not found - get suggestions
                similar_result = await data_source.get_similar_assets(asset_name, limit=5)
                return self._not_found_response(asset_name, similar_result.data)

            asset = asset_result.data
            asset_id = asset["id"]

            # Step 2: Get live status
            live_result = await data_source.get_live_snapshot(asset_id)
            citations.append(live_result.to_citation())
            current_status = self._parse_live_status(live_result.data)

            # Step 3: Get performance (if requested)
            performance = None
            if include_performance:
                end_date = date.today()
                start_date = end_date - timedelta(days=days_back)

                oee_result = await data_source.get_oee(asset_id, start_date, end_date)
                citations.append(oee_result.to_citation())

                downtime_result = await data_source.get_downtime(asset_id, start_date, end_date)
                citations.append(downtime_result.to_citation())

                performance = self._calculate_performance(
                    oee_result.data,
                    downtime_result.data,
                    days_back
                )

            # Step 4: Build response
            return ToolResult(
                data={
                    "metadata": self._format_metadata(asset),
                    "current_status": current_status,
                    "performance": performance,
                    "suggestions": None
                },
                citations=citations,
                metadata={
                    "asset_id": asset_id,
                    "days_analyzed": days_back,
                    "query_timestamp": datetime.utcnow().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"Asset lookup failed for '{asset_name}': {e}")
            return self._error_response(str(e))

    def _parse_live_status(self, snapshot_data: dict | None) -> dict:
        """Parse live snapshot into status information."""
        if not snapshot_data:
            return {
                "status": "unknown",
                "output_current": None,
                "output_target": None,
                "variance": None,
                "variance_percent": None,
                "last_updated": None,
                "data_stale": True,
                "stale_warning": "No live data available"
            }

        # Check data freshness
        last_updated = snapshot_data.get("snapshot_time")
        is_stale = False
        stale_warning = None

        if last_updated:
            # Parse timestamp and check if >30 minutes old
            # Implementation depends on timestamp format
            pass

        return {
            "status": snapshot_data.get("status", "unknown"),
            "output_current": snapshot_data.get("output"),
            "output_target": snapshot_data.get("target"),
            "variance": (snapshot_data.get("output", 0) - snapshot_data.get("target", 0)),
            "variance_percent": self._calc_variance_percent(snapshot_data),
            "last_updated": last_updated,
            "data_stale": is_stale,
            "stale_warning": stale_warning
        }

    def _calculate_performance(
        self,
        oee_data: list,
        downtime_data: list,
        days_back: int
    ) -> dict:
        """Calculate performance summary from historical data."""
        if not oee_data:
            return {
                "avg_oee": None,
                "oee_trend": "unknown",
                "total_downtime_minutes": 0,
                "top_downtime_reason": None,
                "top_downtime_percent": None,
                "no_data": True,
                "message": f"No performance data available for the last {days_back} days"
            }

        # Calculate average OEE
        oee_values = [d.get("oee", 0) for d in oee_data if d.get("oee") is not None]
        avg_oee = sum(oee_values) / len(oee_values) if oee_values else 0

        # Calculate trend (compare first half vs second half)
        oee_trend = self._calculate_oee_trend(oee_values)

        # Calculate downtime
        total_downtime = sum(d.get("downtime_minutes", 0) for d in downtime_data)
        top_reason, top_percent = self._get_top_downtime_reason(downtime_data)

        return {
            "avg_oee": round(avg_oee, 1),
            "oee_trend": oee_trend,
            "total_downtime_minutes": total_downtime,
            "top_downtime_reason": top_reason,
            "top_downtime_percent": top_percent,
            "no_data": False,
            "message": None
        }

    def _calculate_oee_trend(self, oee_values: list) -> str:
        """Calculate OEE trend from values (oldest to newest)."""
        if len(oee_values) < 4:
            return "insufficient_data"

        mid = len(oee_values) // 2
        first_half_avg = sum(oee_values[:mid]) / mid
        second_half_avg = sum(oee_values[mid:]) / (len(oee_values) - mid)

        diff = second_half_avg - first_half_avg
        if diff > 2:
            return "improving"
        elif diff < -2:
            return "declining"
        else:
            return "stable"

    def _get_top_downtime_reason(self, downtime_data: list) -> tuple:
        """Find top downtime reason from data."""
        reason_totals = {}
        total_downtime = 0

        for record in downtime_data:
            reasons = record.get("downtime_reasons", {})
            if isinstance(reasons, str):
                import json
                try:
                    reasons = json.loads(reasons)
                except:
                    reasons = {}

            for reason, minutes in reasons.items():
                reason_totals[reason] = reason_totals.get(reason, 0) + minutes
                total_downtime += minutes

        if not reason_totals or total_downtime == 0:
            return None, None

        top_reason = max(reason_totals, key=reason_totals.get)
        top_percent = round(100 * reason_totals[top_reason] / total_downtime, 1)

        return top_reason, top_percent

    def _not_found_response(self, asset_name: str, similar_assets: list) -> ToolResult:
        """Build response for asset not found."""
        suggestions = [a.get("name") for a in similar_assets] if similar_assets else []

        return ToolResult(
            data={
                "metadata": None,
                "current_status": None,
                "performance": None,
                "suggestions": suggestions,
                "not_found": True,
                "message": f"I don't have data for '{asset_name}'."
            },
            citations=[],
            metadata={"asset_not_found": True}
        )

    def _format_metadata(self, asset: dict) -> dict:
        """Format asset metadata for response."""
        return {
            "id": asset.get("id"),
            "name": asset.get("name"),
            "source_id": asset.get("source_id"),
            "area": asset.get("area"),
            "cost_center": asset.get("cost_center_id")
        }

    def _calc_variance_percent(self, snapshot: dict) -> float | None:
        """Calculate variance percentage."""
        target = snapshot.get("target", 0)
        output = snapshot.get("output", 0)
        if target and target > 0:
            return round(100 * (output - target) / target, 1)
        return None

    def _error_response(self, error_msg: str) -> ToolResult:
        """Build error response."""
        return ToolResult(
            data={
                "error": True,
                "message": "Unable to retrieve asset information. Please try again."
            },
            citations=[],
            metadata={"error": error_msg}
        )
```

### Pydantic Models Addition

**models/agent.py - Add these models:**
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class AssetStatus(str, Enum):
    RUNNING = "running"
    DOWN = "down"
    IDLE = "idle"
    UNKNOWN = "unknown"

class OEETrend(str, Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    INSUFFICIENT_DATA = "insufficient_data"

class AssetLookupInput(BaseModel):
    """Input schema for Asset Lookup tool."""
    asset_name: str = Field(
        ...,
        description="Name of the asset to look up (e.g., 'Grinder 5')"
    )
    include_performance: bool = Field(
        default=True,
        description="Include 7-day performance summary"
    )
    days_back: int = Field(
        default=7,
        ge=1,
        le=90,
        description="Number of days to analyze for performance"
    )

class AssetMetadata(BaseModel):
    """Asset metadata from Plant Object Model."""
    id: str
    name: str
    source_id: Optional[str] = None
    area: Optional[str] = None
    cost_center: Optional[str] = None

class AssetCurrentStatus(BaseModel):
    """Current live status of an asset."""
    status: AssetStatus
    output_current: Optional[int] = None
    output_target: Optional[int] = None
    variance: Optional[int] = None
    variance_percent: Optional[float] = None
    last_updated: Optional[str] = None
    data_stale: bool = False
    stale_warning: Optional[str] = None

class AssetPerformance(BaseModel):
    """Performance summary for an asset."""
    avg_oee: Optional[float] = None
    oee_trend: OEETrend = OEETrend.INSUFFICIENT_DATA
    total_downtime_minutes: int = 0
    top_downtime_reason: Optional[str] = None
    top_downtime_percent: Optional[float] = None
    no_data: bool = False
    message: Optional[str] = None

class AssetLookupOutput(BaseModel):
    """Output schema for Asset Lookup tool."""
    metadata: Optional[AssetMetadata] = None
    current_status: Optional[AssetCurrentStatus] = None
    performance: Optional[AssetPerformance] = None
    suggestions: Optional[List[str]] = None
    not_found: bool = False
    message: Optional[str] = None
```

### Data Source Methods Required

The following methods from Story 5.2 Data Access Layer are used:

| Method | Table(s) | Purpose |
|--------|----------|---------|
| `get_asset_by_name(name)` | assets | Fuzzy match asset by name |
| `get_similar_assets(name, limit)` | assets | Get suggestions when not found |
| `get_live_snapshot(asset_id)` | live_snapshots, assets | Current status |
| `get_oee(asset_id, start, end)` | daily_summaries | OEE metrics |
| `get_downtime(asset_id, start, end)` | daily_summaries | Downtime analysis |

### Supabase Tables Used

| Table | Columns Used | Purpose |
|-------|--------------|---------|
| `assets` | id, name, source_id, area, cost_center_id | Asset metadata |
| `live_snapshots` | asset_id, snapshot_time, status, output, target | Current status |
| `daily_summaries` | asset_id, date, oee, availability, performance, quality, downtime_minutes, downtime_reasons | Performance metrics |
| `cost_centers` | id, asset_id, standard_hourly_rate | Cost center lookup |

### Project Structure Notes

**Files to create/modify:**
```
apps/api/
├── app/
│   ├── services/
│   │   └── agent/
│   │       └── tools/
│   │           ├── __init__.py       # Update to export AssetLookupTool
│   │           └── asset_lookup.py   # NEW - Tool implementation
│   └── models/
│       └── agent.py                  # UPDATE - Add Asset schemas
```

### Dependencies

**Story Dependencies:**
- Story 5.1 (Agent Framework & Tool Registry) - ManufacturingTool base class, ToolResult model, tool registry
- Story 5.2 (Data Access Abstraction Layer) - DataSource protocol, get_data_source(), DataResult model
- Story 4.5 (Cited Response Generation) - Citation model pattern

**Blocked By:** Stories 5.1 and 5.2 must be complete

**Enables:**
- Story 5.4 (OEE Query Tool) - Similar pattern, can reuse OEE calculation logic
- Story 5.5 (Downtime Analysis Tool) - Similar pattern, can reuse downtime parsing
- Story 5.6 (Production Status Tool) - Similar pattern for live data
- Story 5.7 (Agent Chat Integration) - Tool will be available for agent selection

### Example Interactions

**Full Asset Response:**
```
User: "Tell me about Grinder 5"

Agent: Here's the current status for Grinder 5:

**Asset Details**
- Area: Grinding
- Cost Center: GR-001
- Status: Running

**Current Shift (as of 2:45 PM)**
- Output: 847 units (Target: 900)
- Variance: -53 units (-5.9%)

**Last 7 Days Performance**
- Avg OEE: 78.3%
- Trend: Stable
- Total Downtime: 4.2 hours
- Top Issue: Material Jam (38% of downtime)

[Citations: assets @ 2026-01-09, live_snapshots @ 14:45:00, daily_summaries 01/02-01/08]

Would you like me to dig into the downtime details or compare this to other assets?
```

**Asset Not Found Response:**
```
User: "How is Grinder 12 doing?"

Agent: I don't have data for "Grinder 12" in the system.

The assets I can see in the Grinding area are:
- Grinder 1
- Grinder 2
- Grinder 3
- Grinder 5

Did you mean one of these?
```

**No Recent Data Response:**
```
User: "Tell me about Test Machine"

Agent: Here's what I know about Test Machine:

**Asset Details**
- Area: Testing
- Cost Center: TST-001

**Performance**
No production data available for the last 7 days.
Last known data: 2025-12-15

Would you like me to look at an older time range?
```

### Testing Strategy

1. **Unit Tests:**
   - Asset name resolution (exact match, fuzzy match, not found)
   - Live status parsing (running, down, idle, stale)
   - OEE trend calculation (improving, stable, declining, insufficient data)
   - Downtime Pareto calculation
   - Citation generation for each data source
   - Error handling (data source errors, partial failures)

2. **Integration Tests:**
   - Full tool flow with mock DataSource
   - Tool registration and auto-discovery
   - Agent intent matching (verify tool selection)
   - Cache behavior (TTL, force_refresh)

3. **Manual Testing:**
   - Query real assets via API
   - Verify citation accuracy
   - Test edge cases (new assets, inactive assets)
   - Test intent matching with various phrasings

### NFR Compliance

- **NFR1 (Accuracy):** All factual claims include citations; no data fabrication
- **NFR3 (Read-Only):** All queries are read-only via DataSource abstraction
- **NFR4 (Agent Honesty):** Clear "I don't have data" responses when asset not found
- **NFR5 (Tool Extensibility):** Follows ManufacturingTool pattern for auto-registration
- **NFR6 (Response Structure):** Returns ToolResult with structured data + citations
- **NFR7 (Tool Response Caching):** Tiered caching (metadata: 1hr, live: 60s, daily: 15min)

### References

- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#FR7.1] - Core Operations Tools specification
- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#5.4] - Supabase Tables Used
- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#6.1] - Example Interactions (Asset Lookup)
- [Source: _bmad-output/planning-artifacts/epic-5.md#Story 5.3] - Story requirements
- [Source: _bmad-output/implementation-artifacts/5-1-agent-framework-tool-registry.md] - ManufacturingTool base class
- [Source: _bmad-output/implementation-artifacts/5-2-data-access-abstraction-layer.md] - DataSource Protocol
- [Source: _bmad/bmm/data/architecture.md#5. Data Models] - Plant Object Model
- [Source: apps/api/app/models/citation.py] - Citation model patterns

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
