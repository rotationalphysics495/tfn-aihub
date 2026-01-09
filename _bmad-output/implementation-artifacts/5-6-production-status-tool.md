# Story 5.6: Production Status Tool

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **to ask about real-time production status across assets**,
so that **I can see at a glance how we're tracking against targets right now**.

## Acceptance Criteria

1. **Plant-Wide Production Status**
   - GIVEN a user asks "How are we doing today?"
   - WHEN the Production Status tool is invoked
   - THEN the response includes for each asset:
     - Current output vs target
     - Variance (units and percentage)
     - Status indicator (ahead/on-track/behind)
     - Data freshness timestamp
   - AND assets are sorted by variance (worst first)
   - AND all data includes citations

2. **Area-Filtered Production Status**
   - GIVEN a user asks "How is the Grinding area doing?"
   - WHEN the Production Status tool is invoked
   - THEN the response filters to assets in that area only
   - AND shows area-level totals (total output, total target, variance)
   - AND ranks assets within the area by performance

3. **Data Freshness Warning**
   - GIVEN a user asks about production status
   - WHEN live_snapshots data is stale (>30 minutes old)
   - THEN the response includes a warning: "Data is from [timestamp], may not reflect current status"
   - AND still shows the available data with the warning

4. **Status Indicators**
   - GIVEN production data is available
   - WHEN determining status
   - THEN assets >=5% ahead of target are marked "ahead"
   - AND assets within 5% of target are marked "on-track"
   - AND assets >5% behind target are marked "behind"
   - AND color coding is suggested for UI display

5. **Summary Statistics**
   - GIVEN multiple assets are returned
   - WHEN formatting the response
   - THEN summary includes total assets, count by status
   - AND overall variance (sum of all output vs sum of all targets)
   - AND highlights assets needing attention

6. **No Live Data Handling**
   - GIVEN no live snapshot data is available
   - WHEN the Production Status tool is invoked
   - THEN the response states "No real-time production data available"
   - AND suggests checking if the polling pipeline is running
   - AND does NOT fabricate any values

7. **Tool Registration**
   - GIVEN the agent framework is initialized
   - WHEN tools are auto-discovered
   - THEN ProductionStatusTool is registered with the agent
   - AND its description enables correct intent matching

8. **Caching Support**
   - GIVEN production status queries return live data
   - WHEN the tool returns data
   - THEN responses are cached for 60 seconds (live data tier)
   - AND cache metadata is included in response

## Tasks / Subtasks

- [ ] Task 1: Create ProductionStatusTool Class (AC: #7)
  - [ ] 1.1 Create `apps/api/app/services/agent/tools/production_status.py`
  - [ ] 1.2 Extend ManufacturingTool base class
  - [ ] 1.3 Define tool name: "production_status"
  - [ ] 1.4 Define tool description for intent matching
  - [ ] 1.5 Create ProductionStatusInput Pydantic schema
  - [ ] 1.6 Implement _arun() method
  - [ ] 1.7 Create unit tests for tool class

- [ ] Task 2: Define Input/Output Schemas (AC: #1, #4, #5)
  - [ ] 2.1 Add ProductionStatusInput to `apps/api/app/models/agent.py`
  - [ ] 2.2 Define area field (optional, default: all)
  - [ ] 2.3 Add ProductionStatusOutput model
  - [ ] 2.4 Define AssetStatus model (asset, output, target, variance, status)
  - [ ] 2.5 Define StatusSummary model

- [ ] Task 3: Implement Plant-Wide Query (AC: #1, #5)
  - [ ] 3.1 Use data_source.get_all_live_snapshots() for all assets
  - [ ] 3.2 Join with shift_targets for target comparison
  - [ ] 3.3 Calculate variance for each asset
  - [ ] 3.4 Sort by variance (worst first)
  - [ ] 3.5 Calculate summary statistics
  - [ ] 3.6 Create unit tests

- [ ] Task 4: Implement Area-Filtered Query (AC: #2)
  - [ ] 4.1 Parse area from input
  - [ ] 4.2 Use data_source.get_live_snapshots_by_area()
  - [ ] 4.3 Calculate area-level totals
  - [ ] 4.4 Rank assets within area
  - [ ] 4.5 Create unit tests

- [ ] Task 5: Implement Status Determination (AC: #4)
  - [ ] 5.1 Create determine_status() helper function
  - [ ] 5.2 Calculate variance percentage
  - [ ] 5.3 Apply thresholds (+/-5%)
  - [ ] 5.4 Return status and suggested color
  - [ ] 5.5 Create tests for status determination

- [ ] Task 6: Implement Data Freshness Check (AC: #3)
  - [ ] 6.1 Check timestamp of live_snapshots data
  - [ ] 6.2 Calculate age from current time
  - [ ] 6.3 Add warning if >30 minutes old
  - [ ] 6.4 Include freshness in response metadata
  - [ ] 6.5 Create tests for freshness warning

- [ ] Task 7: Implement No Data Handling (AC: #6)
  - [ ] 7.1 Detect when no live snapshots available
  - [ ] 7.2 Generate helpful error message
  - [ ] 7.3 Suggest troubleshooting steps
  - [ ] 7.4 Create tests for no data scenario

- [ ] Task 8: Add Cache Metadata (AC: #8)
  - [ ] 8.1 Set cache_tier to "live"
  - [ ] 8.2 Set ttl_seconds to 60
  - [ ] 8.3 Include data freshness in cache considerations

## Dev Notes

### Architecture Compliance

This story implements the **Production Status Tool** from the PRD Addendum (FR7.1 Core Operations Tools). It provides real-time visibility into production performance vs targets.

**Location:** `apps/api/` (Python FastAPI Backend)
**Module:** `app/services/agent/tools/production_status.py`
**Pattern:** ManufacturingTool subclass with DataSource abstraction

### Technical Requirements

**Status Thresholds:**
```
AHEAD:    variance >= +5%  (green)
ON_TRACK: -5% < variance < +5%  (yellow)
BEHIND:   variance <= -5%  (red)
```

**Tool Flow Diagram:**
```
User: "How are we doing today?"
    |
    v
+-------------------+
| Agent (tool       |
| selection)        |
+-------------------+
    |
    v
+------------------------+
| ProductionStatusTool   |
| _arun()                |
+------------------------+
    |
    +---> data_source.get_all_live_snapshots()
    |         --> live_snapshots for all assets
    |
    +---> data_source.get_all_shift_targets()
    |         --> shift_targets for comparison
    |
    +---> Check data freshness (< 30 min?)
    |
    +---> Calculate variance for each asset
    |
    +---> Sort by variance (worst first)
    |
    +---> Generate summary statistics
    |
    v
+-------------------+
| ToolResult        |
| (status + citations)|
+-------------------+
```

### ProductionStatusTool Implementation

**production_status.py Core Structure:**
```python
from typing import Optional, List, Literal
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from app.services.agent.base import ManufacturingTool, ToolResult, Citation
from app.services.agent.data_source import get_data_source
import logging

logger = logging.getLogger(__name__)

class ProductionStatusInput(BaseModel):
    """Input schema for Production Status tool."""
    area: Optional[str] = Field(
        default=None,
        description="Area name to filter by (e.g., 'Grinding'). If not specified, shows all assets."
    )

class AssetProductionStatus(BaseModel):
    """Production status for a single asset."""
    asset_name: str
    area: str
    current_output: int
    shift_target: int
    variance_units: int
    variance_percent: float
    status: Literal["ahead", "on_track", "behind"]
    status_color: str  # "green", "yellow", "red"
    snapshot_time: datetime
    is_stale: bool  # True if >30 min old

class ProductionStatusSummary(BaseModel):
    """Summary statistics for production status."""
    total_assets: int
    ahead_count: int
    on_track_count: int
    behind_count: int
    total_output: int
    total_target: int
    total_variance_units: int
    total_variance_percent: float
    assets_needing_attention: List[str]  # Names of assets behind target

class ProductionStatusOutput(BaseModel):
    """Output schema for Production Status tool."""
    scope: str  # "all" or area name
    timestamp: datetime  # When this query was run
    data_freshness: str  # "live", "stale (X min old)", etc.
    has_stale_warning: bool
    stale_warning_message: Optional[str] = None

    # Summary
    summary: ProductionStatusSummary

    # Asset details (sorted by variance, worst first)
    assets: List[AssetProductionStatus]

    # Area totals (if area-filtered)
    area_output: Optional[int] = None
    area_target: Optional[int] = None
    area_variance_percent: Optional[float] = None

class ProductionStatusTool(ManufacturingTool):
    name: str = "production_status"
    description: str = """Get real-time production status vs targets.
    Use this tool when a user asks about current production, how they're doing today,
    or wants to know output vs target for assets.
    Returns current output, target, variance, and status for each asset.
    Examples: "How are we doing today?", "What's our production status?",
    "How is the Grinding area tracking?", "Which machines are behind?"
    """
    args_schema: type = ProductionStatusInput
    citations_required: bool = True

    # Status thresholds
    AHEAD_THRESHOLD = 5.0   # >= +5% = ahead
    BEHIND_THRESHOLD = -5.0  # <= -5% = behind
    STALE_MINUTES = 30       # Data older than this triggers warning

    async def _arun(self, area: Optional[str] = None) -> ToolResult:
        """Execute production status query and return structured results."""
        data_source = get_data_source()
        citations: List[Citation] = []

        # Get live snapshots
        if area:
            snapshots_result = await data_source.get_live_snapshots_by_area(area)
        else:
            snapshots_result = await data_source.get_all_live_snapshots()
        citations.append(snapshots_result.to_citation())

        if not snapshots_result.data:
            return self._no_data_response(area, citations)

        # Get shift targets
        targets_result = await data_source.get_all_shift_targets()
        citations.append(targets_result.to_citation())

        targets_map = {t["asset_id"]: t for t in targets_result.data or []}

        # Process each asset
        assets = []
        for snapshot in snapshots_result.data:
            asset_status = self._process_asset_snapshot(snapshot, targets_map)
            if asset_status:
                assets.append(asset_status)

        # Sort by variance (worst first)
        assets.sort(key=lambda x: x.variance_percent)

        # Check for stale data
        has_stale, stale_message, freshness = self._check_data_freshness(assets)

        # Calculate summary
        summary = self._calculate_summary(assets)

        # Build output
        output = ProductionStatusOutput(
            scope=area or "all",
            timestamp=datetime.utcnow(),
            data_freshness=freshness,
            has_stale_warning=has_stale,
            stale_warning_message=stale_message,
            summary=summary,
            assets=assets
        )

        # Add area totals if filtered
        if area and assets:
            output.area_output = sum(a.current_output for a in assets)
            output.area_target = sum(a.shift_target for a in assets)
            if output.area_target > 0:
                output.area_variance_percent = round(
                    (output.area_output - output.area_target) / output.area_target * 100, 1
                )

        return ToolResult(
            data=output.dict(),
            citations=citations,
            metadata={
                "cache_tier": "live",
                "ttl_seconds": 60,
                "follow_up_questions": self._generate_follow_ups(output)
            }
        )

    def _process_asset_snapshot(
        self, snapshot: dict, targets_map: dict
    ) -> Optional[AssetProductionStatus]:
        """Process a single asset snapshot into status."""
        asset_id = snapshot.get("asset_id")
        target = targets_map.get(asset_id, {})
        target_output = target.get("target_output", 0)

        if target_output == 0:
            return None  # Skip assets without targets

        current_output = snapshot.get("output", 0)
        variance_units = current_output - target_output
        variance_percent = (variance_units / target_output) * 100

        # Determine status
        if variance_percent >= self.AHEAD_THRESHOLD:
            status, color = "ahead", "green"
        elif variance_percent <= self.BEHIND_THRESHOLD:
            status, color = "behind", "red"
        else:
            status, color = "on_track", "yellow"

        # Check staleness
        snapshot_time = datetime.fromisoformat(
            snapshot.get("snapshot_time", datetime.utcnow().isoformat())
        )
        is_stale = (datetime.utcnow() - snapshot_time) > timedelta(minutes=self.STALE_MINUTES)

        return AssetProductionStatus(
            asset_name=snapshot.get("asset_name", snapshot.get("assets", {}).get("name", "Unknown")),
            area=snapshot.get("area", snapshot.get("assets", {}).get("area", "Unknown")),
            current_output=current_output,
            shift_target=target_output,
            variance_units=variance_units,
            variance_percent=round(variance_percent, 1),
            status=status,
            status_color=color,
            snapshot_time=snapshot_time,
            is_stale=is_stale
        )

    def _check_data_freshness(
        self, assets: List[AssetProductionStatus]
    ) -> tuple[bool, Optional[str], str]:
        """Check if any data is stale and generate warning."""
        if not assets:
            return False, None, "no_data"

        stale_assets = [a for a in assets if a.is_stale]

        if not stale_assets:
            return False, None, "live"

        oldest = min(a.snapshot_time for a in stale_assets)
        age_minutes = int((datetime.utcnow() - oldest).total_seconds() / 60)

        if len(stale_assets) == len(assets):
            message = f"Warning: All data is from {age_minutes} minutes ago and may not reflect current status."
            freshness = f"stale ({age_minutes} min old)"
        else:
            stale_names = [a.asset_name for a in stale_assets[:3]]
            message = f"Warning: Data for {', '.join(stale_names)} is {age_minutes}+ minutes old."
            freshness = f"mixed (some stale)"

        return True, message, freshness

    def _calculate_summary(
        self, assets: List[AssetProductionStatus]
    ) -> ProductionStatusSummary:
        """Calculate summary statistics."""
        ahead = [a for a in assets if a.status == "ahead"]
        on_track = [a for a in assets if a.status == "on_track"]
        behind = [a for a in assets if a.status == "behind"]

        total_output = sum(a.current_output for a in assets)
        total_target = sum(a.shift_target for a in assets)
        total_variance = total_output - total_target
        total_variance_pct = (total_variance / total_target * 100) if total_target > 0 else 0

        return ProductionStatusSummary(
            total_assets=len(assets),
            ahead_count=len(ahead),
            on_track_count=len(on_track),
            behind_count=len(behind),
            total_output=total_output,
            total_target=total_target,
            total_variance_units=total_variance,
            total_variance_percent=round(total_variance_pct, 1),
            assets_needing_attention=[a.asset_name for a in behind[:5]]  # Top 5 worst
        )

    def _no_data_response(
        self, area: Optional[str], citations: List[Citation]
    ) -> ToolResult:
        """Generate response when no live data available."""
        scope = area or "the plant"
        return ToolResult(
            data={
                "no_data": True,
                "message": f"No real-time production data available for {scope}.",
                "suggestion": "Please verify the polling pipeline is running and live_snapshots table has recent data.",
                "troubleshooting": [
                    "Check Railway worker logs for polling errors",
                    "Verify MSSQL connection is active",
                    "Check if live_snapshots table has recent records"
                ]
            },
            citations=citations,
            metadata={"cache_tier": "live", "ttl_seconds": 60}
        )

    def _generate_follow_ups(self, output: ProductionStatusOutput) -> List[str]:
        """Generate context-aware follow-up questions."""
        questions = []
        if output.summary.behind_count > 0:
            worst = output.summary.assets_needing_attention[0]
            questions.append(f"Why is {worst} behind target?")
            questions.append(f"What's causing downtime on {worst}?")
        if output.scope != "all":
            questions.append(f"Show me OEE for {output.scope}")
        questions.append("What should I focus on today?")
        return questions[:3]
```

### Example Response Format

**Plant-Wide Status Response:**
```json
{
  "data": {
    "scope": "all",
    "timestamp": "2026-01-09T14:45:00Z",
    "data_freshness": "live",
    "has_stale_warning": false,
    "stale_warning_message": null,
    "summary": {
      "total_assets": 8,
      "ahead_count": 2,
      "on_track_count": 3,
      "behind_count": 3,
      "total_output": 6847,
      "total_target": 7200,
      "total_variance_units": -353,
      "total_variance_percent": -4.9,
      "assets_needing_attention": ["Grinder 5", "CAMA 800-1", "Press 2"]
    },
    "assets": [
      {
        "asset_name": "Grinder 5",
        "area": "Grinding",
        "current_output": 847,
        "shift_target": 1000,
        "variance_units": -153,
        "variance_percent": -15.3,
        "status": "behind",
        "status_color": "red",
        "snapshot_time": "2026-01-09T14:42:00Z",
        "is_stale": false
      },
      {
        "asset_name": "CAMA 800-1",
        "area": "Packaging",
        "current_output": 1240,
        "shift_target": 1400,
        "variance_units": -160,
        "variance_percent": -11.4,
        "status": "behind",
        "status_color": "red",
        "snapshot_time": "2026-01-09T14:43:00Z",
        "is_stale": false
      },
      {
        "asset_name": "Grinder 1",
        "area": "Grinding",
        "current_output": 1050,
        "shift_target": 1000,
        "variance_units": 50,
        "variance_percent": 5.0,
        "status": "on_track",
        "status_color": "yellow",
        "snapshot_time": "2026-01-09T14:44:00Z",
        "is_stale": false
      }
    ]
  },
  "citations": [
    {"source": "supabase.live_snapshots", "timestamp": "2026-01-09T14:45:00Z"},
    {"source": "supabase.shift_targets", "timestamp": "2026-01-09T14:45:00Z"}
  ],
  "metadata": {
    "cache_tier": "live",
    "ttl_seconds": 60,
    "follow_up_questions": [
      "Why is Grinder 5 behind target?",
      "What's causing downtime on Grinder 5?",
      "What should I focus on today?"
    ]
  }
}
```

**Stale Data Warning Response:**
```json
{
  "data": {
    "scope": "all",
    "data_freshness": "stale (45 min old)",
    "has_stale_warning": true,
    "stale_warning_message": "Warning: All data is from 45 minutes ago and may not reflect current status.",
    "summary": {...},
    "assets": [...]
  },
  "citations": [...]
}
```

### Project Structure Notes

**Files to create:**
```
apps/api/
├── app/
│   ├── services/
│   │   └── agent/
│   │       └── tools/
│   │           └── production_status.py  # This tool
│   └── models/
│       └── agent.py                      # Add Production schemas
├── tests/
│   └── test_production_status_tool.py    # Tool tests
```

### Dependencies

**Story Dependencies:**
- Story 5.1 (Agent Framework) - ManufacturingTool base class
- Story 5.2 (Data Access Layer) - DataSource abstraction

**Blocked By:** Stories 5.1, 5.2

**Enables:**
- Story 5.7 (Agent Chat Integration) - Production status in chat
- Story 5.8 (Tool Response Caching) - Defines live data cache tier

### Testing Strategy

1. **Unit Tests:**
   - Tool initialization and registration
   - Plant-wide status query
   - Area-filtered query
   - Status determination (ahead/on-track/behind)
   - Data freshness detection
   - Stale data warning generation
   - Summary calculation
   - No data handling
   - Sorting by variance

2. **Integration Tests:**
   - Full tool execution with mock data source
   - Response schema validation
   - Citation accuracy

3. **Manual Testing:**
   - Test with real Supabase data
   - Verify status thresholds are correct
   - Test stale data detection

### NFR Compliance

- **NFR1 (Accuracy):** Live data with timestamps; all values cited
- **NFR2 (Latency):** 60-second cache for fast repeated queries
- **NFR4 (Agent Honesty):** Stale data clearly warned; no data handled gracefully

### References

- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#FR7.1 Core Operations Tools] - Production Status specification
- [Source: _bmad-output/planning-artifacts/epic-5.md#Story 5.6] - Story requirements
- [Source: _bmad/bmm/data/architecture.md#5. Data Models] - live_snapshots schema
- [Source: _bmad/bmm/data/architecture.md#6. Data Pipelines] - Polling pipeline for live data

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

