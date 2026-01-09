# Story 5.4: OEE Query Tool

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **to ask about OEE for any asset, area, or plant-wide with a breakdown**,
so that **I can understand where we're losing efficiency**.

## Acceptance Criteria

1. **Asset-Level OEE Query**
   - GIVEN a user asks "What's the OEE for Grinder 5?"
   - WHEN the OEE Query tool is invoked
   - THEN the response includes overall OEE percentage
   - AND availability component (planned vs actual runtime)
   - AND performance component (actual vs theoretical speed)
   - AND quality component (good units vs total units)
   - AND comparison to target (if shift_targets exists)
   - AND all values include citations with date range

2. **Area-Level OEE Query**
   - GIVEN a user asks "What's the OEE for the Grinding area?"
   - WHEN the OEE Query tool is invoked
   - THEN the response includes aggregated OEE across all assets in that area
   - AND lists individual asset OEE values ranked by performance
   - AND highlights which assets are pulling down the average
   - AND all data includes citations

3. **Time Range Support**
   - GIVEN a user asks about OEE for a specific time range (e.g., "last week", "yesterday")
   - WHEN the OEE Query tool parses the query
   - THEN the response covers the specified date range
   - AND citations reflect the actual dates queried
   - AND default time range is yesterday (T-1) if not specified

4. **Target Comparison**
   - GIVEN an asset has a configured target OEE
   - WHEN OEE data is returned
   - THEN the response includes the target value
   - AND variance from target (percentage points)
   - AND status indicator (above/below target)

5. **No Data Handling**
   - GIVEN no OEE data exists for the requested scope/time
   - WHEN the OEE Query tool is invoked
   - THEN the response states "No OEE data available for [scope] in [time range]"
   - AND does NOT fabricate any values
   - AND includes citation for the query that returned no results

6. **OEE Component Breakdown**
   - GIVEN the tool calculates OEE
   - WHEN presenting results
   - THEN the response shows the OEE formula: OEE = A x P x Q
   - AND explains which component is the biggest opportunity
   - AND provides actionable insight on where to focus

7. **Tool Registration**
   - GIVEN the agent framework is initialized
   - WHEN tools are auto-discovered
   - THEN OEEQueryTool is registered with the agent
   - AND its description enables correct intent matching for OEE questions

8. **Caching Support**
   - GIVEN OEE queries return historical data
   - WHEN the tool returns data
   - THEN responses are cached for 15 minutes (daily data tier)
   - AND cache metadata is included in response

## Tasks / Subtasks

- [ ] Task 1: Create OEEQueryTool Class (AC: #7)
  - [ ] 1.1 Create `apps/api/app/services/agent/tools/oee_query.py`
  - [ ] 1.2 Extend ManufacturingTool base class
  - [ ] 1.3 Define tool name: "oee_query"
  - [ ] 1.4 Define tool description for intent matching
  - [ ] 1.5 Create OEEQueryInput Pydantic schema
  - [ ] 1.6 Implement _arun() method
  - [ ] 1.7 Create unit tests for tool class

- [ ] Task 2: Define Input/Output Schemas (AC: #1, #6)
  - [ ] 2.1 Add OEEQueryInput to `apps/api/app/models/agent.py`
  - [ ] 2.2 Define scope field (asset_name OR area)
  - [ ] 2.3 Define time_range field (optional, default: yesterday)
  - [ ] 2.4 Add OEEQueryOutput model
  - [ ] 2.5 Define OEE components (availability, performance, quality)
  - [ ] 2.6 Define target and variance fields

- [ ] Task 3: Implement Asset-Level OEE Query (AC: #1, #4)
  - [ ] 3.1 Parse asset_name from input
  - [ ] 3.2 Use data_source.get_asset_by_name() to resolve asset
  - [ ] 3.3 Use data_source.get_oee() for OEE metrics
  - [ ] 3.4 Use data_source.get_shift_target() for target comparison
  - [ ] 3.5 Calculate averages for date range
  - [ ] 3.6 Build response with all components
  - [ ] 3.7 Create unit tests

- [ ] Task 4: Implement Area-Level OEE Query (AC: #2)
  - [ ] 4.1 Parse area from input
  - [ ] 4.2 Use data_source.get_assets_by_area() for asset list
  - [ ] 4.3 Use data_source.get_oee_by_area() for aggregated data
  - [ ] 4.4 Calculate area-wide average
  - [ ] 4.5 Rank assets by OEE
  - [ ] 4.6 Identify underperformers
  - [ ] 4.7 Create unit tests

- [ ] Task 5: Implement Time Range Parsing (AC: #3)
  - [ ] 5.1 Create parse_time_range() helper function
  - [ ] 5.2 Support "yesterday", "last week", "last 7 days", "this month"
  - [ ] 5.3 Support specific dates (e.g., "January 5th")
  - [ ] 5.4 Default to yesterday (T-1) if not specified
  - [ ] 5.5 Return (start_date, end_date) tuple
  - [ ] 5.6 Create tests for various time expressions

- [ ] Task 6: Implement No Data Handling (AC: #5)
  - [ ] 6.1 Detect empty query results
  - [ ] 6.2 Generate helpful message with scope and time range
  - [ ] 6.3 Include citation for empty query
  - [ ] 6.4 Do not fabricate any values
  - [ ] 6.5 Create tests for no data scenarios

- [ ] Task 7: Implement OEE Analysis (AC: #6)
  - [ ] 7.1 Calculate which component has most opportunity
  - [ ] 7.2 Generate insight message (e.g., "Availability is your biggest gap")
  - [ ] 7.3 Include specific improvement percentage
  - [ ] 7.4 Create follow-up questions based on analysis

- [ ] Task 8: Add Cache Metadata (AC: #8)
  - [ ] 8.1 Set cache_tier to "daily"
  - [ ] 8.2 Set ttl_seconds to 900 (15 minutes)
  - [ ] 8.3 Include date range in cache key considerations

## Dev Notes

### Architecture Compliance

This story implements the **OEE Query Tool** from the PRD Addendum (FR7.1 Core Operations Tools). It provides the most requested metric for plant managers - Overall Equipment Effectiveness.

**Location:** `apps/api/` (Python FastAPI Backend)
**Module:** `app/services/agent/tools/oee_query.py`
**Pattern:** ManufacturingTool subclass with DataSource abstraction

### Technical Requirements

**OEE Formula:**
```
OEE = Availability x Performance x Quality

Availability = (Run Time / Planned Production Time)
Performance = (Actual Output / Theoretical Output at Run Time)
Quality = (Good Units / Total Units)
```

**Tool Flow Diagram:**
```
User: "What's the OEE for the Grinding area last week?"
    |
    v
+-------------------+
| Agent (tool       |
| selection)        |
+-------------------+
    |
    v
+-------------------+
| OEEQueryTool      |
| _arun()           |
+-------------------+
    |
    +---> parse_time_range("last week")
    |         --> (2026-01-02, 2026-01-08)
    |
    +---> data_source.get_assets_by_area("Grinding")
    |         --> [asset1, asset2, asset3, asset4]
    |
    +---> data_source.get_oee_by_area("Grinding", start, end)
    |         --> daily_summaries with OEE data
    |
    +---> Calculate aggregates and rankings
    |
    v
+-------------------+
| ToolResult        |
| (data + citations)|
+-------------------+
```

### OEEQueryTool Implementation

**oee_query.py Core Structure:**
```python
from typing import Optional, List, Literal
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field
from app.services.agent.base import ManufacturingTool, ToolResult, Citation
from app.services.agent.data_source import get_data_source
import logging

logger = logging.getLogger(__name__)

class OEEQueryInput(BaseModel):
    """Input schema for OEE Query tool."""
    scope: str = Field(
        description="Asset name, area name, or 'plant' for plant-wide OEE"
    )
    time_range: Optional[str] = Field(
        default="yesterday",
        description="Time range like 'yesterday', 'last week', 'last 7 days', 'this month'"
    )

class OEEComponentBreakdown(BaseModel):
    """OEE component breakdown."""
    availability: float  # 0-100
    performance: float   # 0-100
    quality: float       # 0-100

class OEEResult(BaseModel):
    """OEE result for a single asset or aggregate."""
    name: str
    oee: float  # 0-100
    components: OEEComponentBreakdown
    target: Optional[float] = None
    variance: Optional[float] = None  # percentage points
    status: Optional[str] = None  # above_target, below_target, no_target

class OEEQueryOutput(BaseModel):
    """Output schema for OEE Query tool."""
    scope_type: Literal["asset", "area", "plant"]
    scope_name: str
    date_range: str  # e.g., "Jan 2-8, 2026"
    start_date: date
    end_date: date

    # Main result
    overall_oee: float
    components: OEEComponentBreakdown

    # Target comparison (if available)
    target_oee: Optional[float] = None
    variance_from_target: Optional[float] = None

    # Area/Plant breakdown (if scope is area or plant)
    asset_breakdown: Optional[List[OEEResult]] = None
    bottom_performers: Optional[List[str]] = None  # Assets pulling down average

    # Analysis
    biggest_opportunity: str  # "availability", "performance", "quality"
    opportunity_insight: str  # Actionable message
    potential_improvement: float  # % points if fixed

    # Metadata
    data_points: int  # Number of days/records included
    no_data: bool = False

class OEEQueryTool(ManufacturingTool):
    name: str = "oee_query"
    description: str = """Query OEE (Overall Equipment Effectiveness) metrics.
    Use this tool when a user asks about OEE, efficiency, or equipment effectiveness.
    Supports querying by asset name, area, or plant-wide.
    Returns OEE breakdown (Availability x Performance x Quality) with target comparison.
    Examples: "What's the OEE for Grinder 5?", "Show me OEE for the Grinding area",
    "How was plant OEE last week?", "Why is our efficiency low?"
    """
    args_schema: type = OEEQueryInput
    citations_required: bool = True

    async def _arun(self, scope: str, time_range: str = "yesterday") -> ToolResult:
        """Execute OEE query and return structured results."""
        data_source = get_data_source()
        citations: List[Citation] = []

        # Parse time range
        start_date, end_date = self._parse_time_range(time_range)
        date_range_str = self._format_date_range(start_date, end_date)

        # Determine scope type
        scope_type = self._determine_scope_type(scope)

        if scope_type == "asset":
            return await self._query_asset_oee(
                scope, start_date, end_date, date_range_str, data_source, citations
            )
        elif scope_type == "area":
            return await self._query_area_oee(
                scope, start_date, end_date, date_range_str, data_source, citations
            )
        else:  # plant
            return await self._query_plant_oee(
                start_date, end_date, date_range_str, data_source, citations
            )

    async def _query_asset_oee(
        self, asset_name: str, start_date: date, end_date: date,
        date_range_str: str, data_source, citations: List[Citation]
    ) -> ToolResult:
        """Query OEE for a single asset."""
        # Find asset
        asset_result = await data_source.get_asset_by_name(asset_name)
        citations.append(asset_result.to_citation())

        if not asset_result.data:
            return self._no_data_response(f"asset '{asset_name}'", date_range_str, citations)

        asset = asset_result.data
        asset_id = asset["id"]

        # Get OEE data
        oee_result = await data_source.get_oee(asset_id, start_date, end_date)
        citations.append(oee_result.to_citation())

        if not oee_result.data:
            return self._no_data_response(f"asset '{asset_name}'", date_range_str, citations)

        # Get target
        target_result = await data_source.get_shift_target(asset_id)
        citations.append(target_result.to_citation())

        # Calculate averages
        oee_data = oee_result.data
        avg_oee = self._calculate_average(oee_data, "oee")
        avg_avail = self._calculate_average(oee_data, "availability")
        avg_perf = self._calculate_average(oee_data, "performance")
        avg_qual = self._calculate_average(oee_data, "quality")

        components = OEEComponentBreakdown(
            availability=round(avg_avail, 1),
            performance=round(avg_perf, 1),
            quality=round(avg_qual, 1)
        )

        # Target comparison
        target_oee = target_result.data.get("target_oee") if target_result.data else None
        variance = round(avg_oee - target_oee, 1) if target_oee else None

        # Analysis
        opportunity, insight, potential = self._analyze_opportunity(components)

        output = OEEQueryOutput(
            scope_type="asset",
            scope_name=asset["name"],
            date_range=date_range_str,
            start_date=start_date,
            end_date=end_date,
            overall_oee=round(avg_oee, 1),
            components=components,
            target_oee=target_oee,
            variance_from_target=variance,
            biggest_opportunity=opportunity,
            opportunity_insight=insight,
            potential_improvement=potential,
            data_points=len(oee_data)
        )

        return ToolResult(
            data=output.dict(),
            citations=citations,
            metadata={
                "cache_tier": "daily",
                "ttl_seconds": 900,
                "follow_up_questions": self._generate_follow_ups(output)
            }
        )

    def _parse_time_range(self, time_range: str) -> tuple[date, date]:
        """Parse natural language time range into dates."""
        today = date.today()
        yesterday = today - timedelta(days=1)

        time_range_lower = time_range.lower().strip()

        if time_range_lower in ["yesterday", "t-1"]:
            return yesterday, yesterday
        elif time_range_lower in ["last week", "last 7 days", "past week"]:
            return yesterday - timedelta(days=6), yesterday
        elif time_range_lower in ["last 30 days", "last month", "past month"]:
            return yesterday - timedelta(days=29), yesterday
        elif time_range_lower in ["this week"]:
            # Monday of current week
            start_of_week = today - timedelta(days=today.weekday())
            return start_of_week, yesterday
        elif time_range_lower in ["today"]:
            return today, today
        else:
            # Default to yesterday
            return yesterday, yesterday

    def _analyze_opportunity(
        self, components: OEEComponentBreakdown
    ) -> tuple[str, str, float]:
        """Analyze which OEE component has the most improvement opportunity."""
        gaps = {
            "availability": 100 - components.availability,
            "performance": 100 - components.performance,
            "quality": 100 - components.quality
        }

        biggest = max(gaps, key=gaps.get)
        potential = gaps[biggest]

        insights = {
            "availability": f"Availability ({components.availability}%) is your biggest gap. Focus on reducing unplanned downtime.",
            "performance": f"Performance ({components.performance}%) is holding you back. Check for speed losses and minor stops.",
            "quality": f"Quality ({components.quality}%) needs attention. Investigate scrap and rework causes."
        }

        return biggest, insights[biggest], round(potential, 1)

    def _calculate_average(self, data: List[dict], field: str) -> float:
        """Calculate average of a field across records."""
        values = [d[field] for d in data if d.get(field) is not None]
        return sum(values) / len(values) if values else 0

    def _no_data_response(
        self, scope: str, date_range: str, citations: List[Citation]
    ) -> ToolResult:
        """Generate response when no data is available."""
        return ToolResult(
            data={
                "no_data": True,
                "message": f"No OEE data available for {scope} in {date_range}",
                "scope": scope,
                "date_range": date_range
            },
            citations=citations,
            metadata={"cache_tier": "daily", "ttl_seconds": 900}
        )

    def _generate_follow_ups(self, output: OEEQueryOutput) -> List[str]:
        """Generate context-aware follow-up questions."""
        questions = []
        if output.variance_from_target and output.variance_from_target < 0:
            questions.append(f"Why is {output.scope_name} below OEE target?")
        if output.biggest_opportunity == "availability":
            questions.append(f"What's causing downtime on {output.scope_name}?")
        if output.bottom_performers:
            questions.append(f"What's wrong with {output.bottom_performers[0]}?")
        questions.append(f"Show me {output.scope_name}'s OEE trend over time")
        return questions[:3]
```

### Example Response Format

**Asset OEE Response:**
```json
{
  "data": {
    "scope_type": "asset",
    "scope_name": "Grinder 5",
    "date_range": "Jan 2-8, 2026",
    "start_date": "2026-01-02",
    "end_date": "2026-01-08",
    "overall_oee": 78.3,
    "components": {
      "availability": 85.2,
      "performance": 94.1,
      "quality": 97.8
    },
    "target_oee": 85.0,
    "variance_from_target": -6.7,
    "biggest_opportunity": "availability",
    "opportunity_insight": "Availability (85.2%) is your biggest gap. Focus on reducing unplanned downtime.",
    "potential_improvement": 14.8,
    "data_points": 7,
    "no_data": false
  },
  "citations": [
    {"source": "supabase.assets", "timestamp": "2026-01-09T10:30:00Z"},
    {"source": "supabase.daily_summaries", "timestamp": "2026-01-09T10:30:00Z", "table": "daily_summaries"},
    {"source": "supabase.shift_targets", "timestamp": "2026-01-09T10:30:00Z"}
  ],
  "metadata": {
    "cache_tier": "daily",
    "ttl_seconds": 900,
    "follow_up_questions": [
      "Why is Grinder 5 below OEE target?",
      "What's causing downtime on Grinder 5?",
      "Show me Grinder 5's OEE trend over time"
    ]
  }
}
```

**Area OEE Response:**
```json
{
  "data": {
    "scope_type": "area",
    "scope_name": "Grinding",
    "date_range": "Jan 2-8, 2026",
    "overall_oee": 74.5,
    "components": {
      "availability": 82.1,
      "performance": 92.3,
      "quality": 98.2
    },
    "asset_breakdown": [
      {"name": "Grinder 1", "oee": 82.5, "status": "above_target"},
      {"name": "Grinder 2", "oee": 79.1, "status": "below_target"},
      {"name": "Grinder 3", "oee": 76.4, "status": "below_target"},
      {"name": "Grinder 5", "oee": 60.0, "status": "below_target"}
    ],
    "bottom_performers": ["Grinder 5", "Grinder 3"],
    "biggest_opportunity": "availability",
    "opportunity_insight": "Availability (82.1%) is your biggest gap. Focus on reducing unplanned downtime.",
    "potential_improvement": 17.9,
    "data_points": 28
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
│   │           └── oee_query.py       # This tool
│   └── models/
│       └── agent.py                   # Add OEE schemas
├── tests/
│   └── test_oee_query_tool.py         # Tool tests
```

### Dependencies

**Story Dependencies:**
- Story 5.1 (Agent Framework) - ManufacturingTool base class
- Story 5.2 (Data Access Layer) - DataSource abstraction

**Blocked By:** Stories 5.1, 5.2

**Enables:**
- Story 5.5 (Downtime Analysis) - Can reference OEE gaps
- Story 5.8 (Tool Response Caching) - Defines cache tier

### Testing Strategy

1. **Unit Tests:**
   - Tool initialization and registration
   - Asset-level OEE query
   - Area-level OEE query with aggregation
   - Time range parsing (all variations)
   - No data handling
   - OEE component analysis
   - Follow-up question generation

2. **Integration Tests:**
   - Full tool execution with mock data source
   - Response schema validation
   - Citation accuracy

3. **Manual Testing:**
   - Test with real Supabase data
   - Verify OEE calculations are correct
   - Test various time range expressions

### NFR Compliance

- **NFR1 (Accuracy):** OEE calculation follows standard formula; all values cited
- **NFR4 (Agent Honesty):** Missing data handled honestly
- **NFR6 (Response Structure):** Structured breakdown with actionable insights

### References

- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#FR7.1 Core Operations Tools] - OEE Query specification
- [Source: _bmad-output/planning-artifacts/epic-5.md#Story 5.4] - Story requirements
- [Source: _bmad/bmm/data/architecture.md#5. Data Models] - daily_summaries schema
- [OEE Standard Definition](https://www.oee.com/) - OEE formula reference

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

