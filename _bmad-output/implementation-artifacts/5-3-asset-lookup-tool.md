# Story 5.3: Asset Lookup Tool

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **to ask about any asset by name and get its current status and recent performance**,
so that **I can quickly understand how a specific machine is doing**.

## Acceptance Criteria

1. **Asset Information Response**
   - GIVEN a user asks "Tell me about Grinder 5"
   - WHEN the Asset Lookup tool is invoked
   - THEN the response includes asset metadata (name, area, cost center)
   - AND current status (running/down/idle)
   - AND current shift output vs target
   - AND 7-day average OEE
   - AND top downtime reason
   - AND all data points include citations

2. **Unknown Asset Handling**
   - GIVEN a user asks about an asset that doesn't exist
   - WHEN the Asset Lookup tool is invoked
   - THEN the response states "I don't have data for [asset name]"
   - AND lists similar assets the user might have meant (max 5)
   - AND does NOT fabricate any data

3. **Missing Production Data Handling**
   - GIVEN the asset exists but has no recent data
   - WHEN the Asset Lookup tool is invoked
   - THEN the response shows available metadata
   - AND indicates "No production data available for the last 7 days"
   - AND still includes citations for the metadata query

4. **Fuzzy Name Matching**
   - GIVEN a user asks about "grinder5" or "Grinder #5" or "grinder 5"
   - WHEN the Asset Lookup tool parses the query
   - THEN the tool normalizes the asset name
   - AND finds the correct asset regardless of formatting
   - AND responds with the canonical asset name

5. **Tool Registration**
   - GIVEN the agent framework is initialized
   - WHEN tools are auto-discovered
   - THEN AssetLookupTool is registered with the agent
   - AND its description enables correct intent matching
   - AND the tool appears in the agent's tool list

6. **Citation Format**
   - GIVEN the tool returns data
   - WHEN citations are generated
   - THEN each data point cites its source table
   - AND includes query timestamp
   - AND follows the Citation schema from Story 5.1

7. **Response Structure**
   - GIVEN the tool successfully retrieves data
   - WHEN formatting the response
   - THEN the response follows ToolResult schema
   - AND includes structured data suitable for chat display
   - AND includes suggested follow-up questions

8. **Caching Support**
   - GIVEN the tool's caching requirements
   - WHEN the tool returns data
   - THEN metadata is cacheable for 1 hour (static data tier)
   - AND live status is cacheable for 60 seconds (live data tier)
   - AND cache metadata is included in response

## Tasks / Subtasks

- [ ] Task 1: Create AssetLookupTool Class (AC: #5)
  - [ ] 1.1 Create `apps/api/app/services/agent/tools/asset_lookup.py`
  - [ ] 1.2 Extend ManufacturingTool base class
  - [ ] 1.3 Define tool name: "asset_lookup"
  - [ ] 1.4 Define tool description for intent matching
  - [ ] 1.5 Create AssetLookupInput Pydantic schema
  - [ ] 1.6 Implement _arun() method
  - [ ] 1.7 Create unit tests for tool class

- [ ] Task 2: Define Input/Output Schemas (AC: #7)
  - [ ] 2.1 Add AssetLookupInput to `apps/api/app/models/agent.py`
  - [ ] 2.2 Define asset_name field (required)
  - [ ] 2.3 Add AssetLookupOutput model
  - [ ] 2.4 Define metadata fields (name, area, cost_center)
  - [ ] 2.5 Define status fields (current_status, output, target)
  - [ ] 2.6 Define performance fields (oee_7day_avg, top_downtime_reason)

- [ ] Task 3: Implement Asset Data Retrieval (AC: #1)
  - [ ] 3.1 Use data_source.get_asset_by_name() for metadata
  - [ ] 3.2 Use data_source.get_live_snapshot() for current status
  - [ ] 3.3 Use data_source.get_shift_target() for target comparison
  - [ ] 3.4 Use data_source.get_oee() for 7-day average
  - [ ] 3.5 Use data_source.get_downtime() for top reason
  - [ ] 3.6 Aggregate citations from all data sources
  - [ ] 3.7 Create integration tests

- [ ] Task 4: Implement Fuzzy Name Matching (AC: #4)
  - [ ] 4.1 Normalize input (lowercase, remove special chars)
  - [ ] 4.2 Try exact match first
  - [ ] 4.3 Fall back to partial match
  - [ ] 4.4 Handle common variations (spaces, #, dashes)
  - [ ] 4.5 Create tests for various input formats

- [ ] Task 5: Implement Unknown Asset Handling (AC: #2)
  - [ ] 5.1 Detect when asset not found
  - [ ] 5.2 Use data_source.get_similar_assets() for suggestions
  - [ ] 5.3 Format helpful response with alternatives
  - [ ] 5.4 Return partial ToolResult (no data, has suggestions)
  - [ ] 5.5 Create tests for unknown asset scenarios

- [ ] Task 6: Implement Missing Data Handling (AC: #3)
  - [ ] 6.1 Detect when asset exists but no production data
  - [ ] 6.2 Return metadata that is available
  - [ ] 6.3 Include clear message about missing data period
  - [ ] 6.4 Still generate citations for what was queried
  - [ ] 6.5 Create tests for partial data scenarios

- [ ] Task 7: Implement Citation Generation (AC: #6)
  - [ ] 7.1 Collect DataResult from each query
  - [ ] 7.2 Convert to Citation objects
  - [ ] 7.3 Include source table and timestamp
  - [ ] 7.4 Aggregate into citations array
  - [ ] 7.5 Verify citation format in tests

- [ ] Task 8: Add Cache Metadata (AC: #8)
  - [ ] 8.1 Define cache tiers for different data types
  - [ ] 8.2 Add cache_tier field to response metadata
  - [ ] 8.3 Add ttl_seconds field for cache duration
  - [ ] 8.4 Prepare for Story 5.8 caching implementation

- [ ] Task 9: Generate Follow-Up Questions (AC: #7)
  - [ ] 9.1 Create follow_up_questions list in response
  - [ ] 9.2 Generate context-aware questions based on data
  - [ ] 9.3 Examples: "Show OEE trend", "What caused downtime?"
  - [ ] 9.4 Create tests for follow-up generation

## Dev Notes

### Architecture Compliance

This story implements the **Asset Lookup Tool** from the PRD Addendum (FR7.1 Core Operations Tools). It's the first tool implementation in Epic 5 and establishes patterns for subsequent tools.

**Location:** `apps/api/` (Python FastAPI Backend)
**Module:** `app/services/agent/tools/asset_lookup.py`
**Pattern:** ManufacturingTool subclass with DataSource abstraction

### Technical Requirements

**Tool Flow Diagram:**
```
User: "Tell me about Grinder 5"
    |
    v
+-------------------+
| Agent (tool       |
| selection)        |
+-------------------+
    |
    v
+-------------------+
| AssetLookupTool   |
| _arun()           |
+-------------------+
    |
    +---> data_source.get_asset_by_name("Grinder 5")
    |         --> assets table
    |
    +---> data_source.get_live_snapshot(asset_id)
    |         --> live_snapshots table
    |
    +---> data_source.get_shift_target(asset_id)
    |         --> shift_targets table
    |
    +---> data_source.get_oee(asset_id, T-7, T-1)
    |         --> daily_summaries table
    |
    +---> data_source.get_downtime(asset_id, T-7, T-1)
              --> daily_summaries table
    |
    v
+-------------------+
| ToolResult        |
| (data + citations)|
+-------------------+
```

### AssetLookupTool Implementation

**asset_lookup.py Core Structure:**
```python
from typing import Optional, List
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field
from app.services.agent.base import ManufacturingTool, ToolResult, Citation
from app.services.agent.data_source import get_data_source
import logging

logger = logging.getLogger(__name__)

class AssetLookupInput(BaseModel):
    """Input schema for Asset Lookup tool."""
    asset_name: str = Field(
        description="Name of the asset to look up (e.g., 'Grinder 5', 'CAMA 800-1')"
    )

class AssetLookupOutput(BaseModel):
    """Output schema for Asset Lookup tool."""
    # Metadata
    name: str
    area: Optional[str] = None
    cost_center: Optional[str] = None

    # Current Status
    current_status: str  # running, down, idle
    current_output: Optional[int] = None
    shift_target: Optional[int] = None
    variance: Optional[int] = None
    variance_percent: Optional[float] = None

    # Performance
    oee_7day_avg: Optional[float] = None
    top_downtime_reason: Optional[str] = None
    top_downtime_minutes: Optional[int] = None

    # Metadata
    data_as_of: datetime
    no_recent_data: bool = False

class AssetLookupTool(ManufacturingTool):
    name: str = "asset_lookup"
    description: str = """Look up information about a specific manufacturing asset.
    Use this tool when a user asks about a specific machine, asset, or equipment
    by name. Returns metadata, current status, recent performance, and top issues.
    Examples: "Tell me about Grinder 5", "How is CAMA 800-1 doing?",
    "What's the status of the packaging line?"
    """
    args_schema: type = AssetLookupInput
    citations_required: bool = True

    async def _arun(self, asset_name: str) -> ToolResult:
        """Execute asset lookup and return structured results."""
        data_source = get_data_source()
        citations: List[Citation] = []

        # Step 1: Find the asset
        asset_result = await data_source.get_asset_by_name(asset_name)
        citations.append(asset_result.to_citation())

        if not asset_result.data:
            # Asset not found - get suggestions
            similar_result = await data_source.get_similar_assets(asset_name)
            citations.append(similar_result.to_citation())

            similar_names = [a["name"] for a in similar_result.data] if similar_result.data else []

            return ToolResult(
                data={
                    "found": False,
                    "message": f"I don't have data for '{asset_name}'",
                    "suggestions": similar_names,
                    "suggestion_message": f"Did you mean one of these? {', '.join(similar_names)}" if similar_names else "No similar assets found."
                },
                citations=citations,
                metadata={"cache_tier": "static", "ttl_seconds": 3600}
            )

        asset = asset_result.data
        asset_id = asset["id"]

        # Step 2: Get current status
        live_result = await data_source.get_live_snapshot(asset_id)
        citations.append(live_result.to_citation())

        # Step 3: Get shift target
        target_result = await data_source.get_shift_target(asset_id)
        citations.append(target_result.to_citation())

        # Step 4: Get 7-day OEE
        end_date = date.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=6)
        oee_result = await data_source.get_oee(asset_id, start_date, end_date)
        citations.append(oee_result.to_citation())

        # Step 5: Get downtime data
        downtime_result = await data_source.get_downtime(asset_id, start_date, end_date)
        citations.append(downtime_result.to_citation())

        # Process results
        output = self._build_output(asset, live_result.data, target_result.data,
                                    oee_result.data, downtime_result.data)

        return ToolResult(
            data=output.dict(),
            citations=citations,
            metadata={
                "cache_tier": "live" if live_result.data else "static",
                "ttl_seconds": 60 if live_result.data else 3600,
                "follow_up_questions": self._generate_follow_ups(output)
            }
        )

    def _build_output(self, asset, live, target, oee_data, downtime_data) -> AssetLookupOutput:
        """Build structured output from query results."""
        # Calculate 7-day OEE average
        oee_avg = None
        if oee_data:
            oee_values = [d["oee"] for d in oee_data if d.get("oee") is not None]
            oee_avg = sum(oee_values) / len(oee_values) if oee_values else None

        # Find top downtime reason
        top_reason, top_minutes = None, None
        if downtime_data:
            # Aggregate downtime by reason
            reasons = {}
            for d in downtime_data:
                if d.get("downtime_reasons"):
                    for reason, minutes in d["downtime_reasons"].items():
                        reasons[reason] = reasons.get(reason, 0) + minutes
            if reasons:
                top_reason = max(reasons, key=reasons.get)
                top_minutes = reasons[top_reason]

        # Calculate variance
        current_output = live.get("output") if live else None
        shift_target = target.get("target_output") if target else None
        variance = None
        variance_percent = None
        if current_output is not None and shift_target:
            variance = current_output - shift_target
            variance_percent = (variance / shift_target) * 100

        return AssetLookupOutput(
            name=asset["name"],
            area=asset.get("area"),
            cost_center=asset.get("cost_center_id"),
            current_status=self._determine_status(live),
            current_output=current_output,
            shift_target=shift_target,
            variance=variance,
            variance_percent=round(variance_percent, 1) if variance_percent else None,
            oee_7day_avg=round(oee_avg, 1) if oee_avg else None,
            top_downtime_reason=top_reason,
            top_downtime_minutes=top_minutes,
            data_as_of=datetime.utcnow(),
            no_recent_data=not bool(oee_data)
        )

    def _determine_status(self, live_data) -> str:
        """Determine current asset status from live snapshot."""
        if not live_data:
            return "unknown"
        # Logic based on live_snapshots schema
        if live_data.get("is_running"):
            return "running"
        elif live_data.get("is_down"):
            return "down"
        return "idle"

    def _generate_follow_ups(self, output: AssetLookupOutput) -> List[str]:
        """Generate context-aware follow-up questions."""
        questions = []
        if output.oee_7day_avg and output.oee_7day_avg < 80:
            questions.append(f"Why is {output.name}'s OEE low?")
        if output.top_downtime_reason:
            questions.append(f"Tell me more about '{output.top_downtime_reason}' downtime")
        if output.variance and output.variance < 0:
            questions.append(f"Why is {output.name} behind target?")
        questions.append(f"Show me {output.name}'s OEE trend")
        return questions[:3]  # Max 3 follow-ups
```

### Example Response Format

**Success Response:**
```json
{
  "data": {
    "name": "Grinder 5",
    "area": "Grinding",
    "cost_center": "GR-001",
    "current_status": "running",
    "current_output": 847,
    "shift_target": 900,
    "variance": -53,
    "variance_percent": -5.9,
    "oee_7day_avg": 78.3,
    "top_downtime_reason": "Material Jam",
    "top_downtime_minutes": 152,
    "data_as_of": "2026-01-09T14:45:00Z",
    "no_recent_data": false
  },
  "citations": [
    {"source": "supabase.assets", "timestamp": "2026-01-09T14:45:00Z"},
    {"source": "supabase.live_snapshots", "timestamp": "2026-01-09T14:45:00Z"},
    {"source": "supabase.shift_targets", "timestamp": "2026-01-09T14:45:00Z"},
    {"source": "supabase.daily_summaries", "timestamp": "2026-01-09T14:45:00Z"}
  ],
  "metadata": {
    "cache_tier": "live",
    "ttl_seconds": 60,
    "follow_up_questions": [
      "Why is Grinder 5 behind target?",
      "Tell me more about 'Material Jam' downtime",
      "Show me Grinder 5's OEE trend"
    ]
  }
}
```

**Asset Not Found Response:**
```json
{
  "data": {
    "found": false,
    "message": "I don't have data for 'Line 12'",
    "suggestions": ["Grinder 1", "Grinder 2", "Grinder 3", "Grinder 5"],
    "suggestion_message": "Did you mean one of these? Grinder 1, Grinder 2, Grinder 3, Grinder 5"
  },
  "citations": [
    {"source": "supabase.assets", "timestamp": "2026-01-09T14:45:00Z"}
  ],
  "metadata": {
    "cache_tier": "static",
    "ttl_seconds": 3600
  }
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
│   │           ├── __init__.py
│   │           └── asset_lookup.py   # This tool
│   └── models/
│       └── agent.py                  # Add AssetLookup schemas
├── tests/
│   └── test_asset_lookup_tool.py     # Tool tests
```

### Dependencies

**Story Dependencies:**
- Story 5.1 (Agent Framework) - ManufacturingTool base class
- Story 5.2 (Data Access Layer) - DataSource abstraction

**Blocked By:** Stories 5.1, 5.2

**Enables:**
- Story 5.7 (Agent Chat Integration) - First tool for chat UI
- Story 5.8 (Tool Response Caching) - Defines cache tiers

### Testing Strategy

1. **Unit Tests:**
   - Tool initialization and registration
   - Input validation
   - Asset found with full data
   - Asset found with partial data
   - Asset not found with suggestions
   - Fuzzy name matching
   - Citation generation
   - Follow-up question generation

2. **Integration Tests:**
   - Full tool execution with mock data source
   - Response schema validation
   - Error handling

3. **Manual Testing:**
   - Test with real Supabase data
   - Verify citations are correct
   - Test various asset name formats

### NFR Compliance

- **NFR1 (Accuracy):** All data points include citations with source and timestamp
- **NFR4 (Agent Honesty):** Unknown assets handled honestly with suggestions
- **NFR5 (Tool Extensibility):** Follows ManufacturingTool pattern
- **NFR6 (Response Structure):** Returns ToolResult with citations array

### References

- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#FR7.1 Core Operations Tools] - Tool requirements
- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#6.1 Example Interactions] - Asset Lookup example
- [Source: _bmad-output/planning-artifacts/epic-5.md#Story 5.3] - Story requirements
- [Source: _bmad/bmm/data/architecture.md#5. Data Models] - Table schemas

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

