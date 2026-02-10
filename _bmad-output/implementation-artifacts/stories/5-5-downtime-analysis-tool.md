# Story 5.5: Downtime Analysis Tool

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **to ask about downtime reasons and patterns for any asset or area**,
so that **I can identify and address the root causes of lost production time**.

## Acceptance Criteria

1. **Asset Downtime Query**
   - GIVEN a user asks "Why was Grinder 5 down yesterday?"
   - WHEN the Downtime Analysis tool is invoked
   - THEN the response includes total downtime minutes
   - AND downtime reasons ranked by duration (Pareto analysis)
   - AND percentage of total downtime per reason
   - AND specific timestamps if available
   - AND all data points include citations

2. **Area Downtime Query**
   - GIVEN a user asks "What are the top downtime reasons for the Grinding area this week?"
   - WHEN the Downtime Analysis tool is invoked
   - THEN the response aggregates across all assets in the area
   - AND shows which assets contributed most to each reason
   - AND provides Pareto analysis for the entire area
   - AND all data includes citations

3. **Pareto Analysis**
   - GIVEN downtime data is available
   - WHEN presenting results
   - THEN reasons are ranked from highest to lowest duration
   - AND cumulative percentage is shown (80/20 rule)
   - AND the "vital few" causes (top 20% causing 80% of downtime) are highlighted

4. **No Downtime Handling**
   - GIVEN an asset had no downtime in the requested period
   - WHEN the Downtime Analysis tool is invoked
   - THEN the response states "[Asset] had no recorded downtime in [time range]"
   - AND shows total uptime percentage
   - AND congratulates on good performance

5. **Time Range Support**
   - GIVEN a user specifies a time range
   - WHEN the tool processes the query
   - THEN data is retrieved for the specified period
   - AND default time range is yesterday (T-1) if not specified
   - AND citations reflect actual dates queried

6. **Downtime Categories**
   - GIVEN downtime reasons are stored in the database
   - WHEN presenting analysis
   - THEN reasons are grouped by category if applicable
   - AND both category-level and reason-level breakdowns are available
   - AND safety-related downtime is highlighted separately

7. **Tool Registration**
   - GIVEN the agent framework is initialized
   - WHEN tools are auto-discovered
   - THEN DowntimeAnalysisTool is registered with the agent
   - AND its description enables correct intent matching

8. **Caching Support**
   - GIVEN downtime queries return historical data
   - WHEN the tool returns data
   - THEN responses are cached for 15 minutes (daily data tier)
   - AND cache metadata is included in response

## Tasks / Subtasks

- [ ] Task 1: Create DowntimeAnalysisTool Class (AC: #7)
  - [ ] 1.1 Create `apps/api/app/services/agent/tools/downtime_analysis.py`
  - [ ] 1.2 Extend ManufacturingTool base class
  - [ ] 1.3 Define tool name: "downtime_analysis"
  - [ ] 1.4 Define tool description for intent matching
  - [ ] 1.5 Create DowntimeAnalysisInput Pydantic schema
  - [ ] 1.6 Implement _arun() method
  - [ ] 1.7 Create unit tests for tool class

- [ ] Task 2: Define Input/Output Schemas (AC: #1, #3)
  - [ ] 2.1 Add DowntimeAnalysisInput to `apps/api/app/models/agent.py`
  - [ ] 2.2 Define scope field (asset_name OR area)
  - [ ] 2.3 Define time_range field (optional)
  - [ ] 2.4 Add DowntimeAnalysisOutput model
  - [ ] 2.5 Define DowntimeReason model (reason, minutes, percentage, cumulative)
  - [ ] 2.6 Define DowntimeByAsset model for area queries

- [ ] Task 3: Implement Asset Downtime Analysis (AC: #1)
  - [ ] 3.1 Parse asset_name from input
  - [ ] 3.2 Use data_source.get_asset_by_name() to resolve asset
  - [ ] 3.3 Use data_source.get_downtime() for downtime records
  - [ ] 3.4 Aggregate reasons from downtime_reasons JSON field
  - [ ] 3.5 Sort by duration descending
  - [ ] 3.6 Calculate percentages and cumulative
  - [ ] 3.7 Create unit tests

- [ ] Task 4: Implement Area Downtime Analysis (AC: #2)
  - [ ] 4.1 Parse area from input
  - [ ] 4.2 Use data_source.get_downtime_by_area() for all assets
  - [ ] 4.3 Aggregate across all assets
  - [ ] 4.4 Track which asset contributed to each reason
  - [ ] 4.5 Build area-wide Pareto
  - [ ] 4.6 Create unit tests

- [ ] Task 5: Implement Pareto Analysis (AC: #3)
  - [ ] 5.1 Create calculate_pareto() helper function
  - [ ] 5.2 Sort reasons by duration
  - [ ] 5.3 Calculate percentage of total
  - [ ] 5.4 Calculate cumulative percentage
  - [ ] 5.5 Identify "vital few" (reasons until 80% cumulative)
  - [ ] 5.6 Create tests for Pareto calculations

- [ ] Task 6: Implement No Downtime Handling (AC: #4)
  - [ ] 6.1 Detect when total downtime is zero
  - [ ] 6.2 Calculate uptime percentage
  - [ ] 6.3 Generate positive feedback message
  - [ ] 6.4 Include citation for query
  - [ ] 6.5 Create tests for zero downtime scenario

- [ ] Task 7: Implement Time Range Support (AC: #5)
  - [ ] 7.1 Reuse parse_time_range() from OEE tool (or shared utility)
  - [ ] 7.2 Default to yesterday (T-1)
  - [ ] 7.3 Support various time expressions
  - [ ] 7.4 Create tests for time range handling

- [ ] Task 8: Implement Safety Downtime Highlighting (AC: #6)
  - [ ] 8.1 Identify safety-related reason codes
  - [ ] 8.2 Extract and highlight separately
  - [ ] 8.3 Include in response even if small duration
  - [ ] 8.4 Create tests for safety highlighting

- [ ] Task 9: Add Cache Metadata (AC: #8)
  - [ ] 9.1 Set cache_tier to "daily"
  - [ ] 9.2 Set ttl_seconds to 900 (15 minutes)
  - [ ] 9.3 Include date range in cache considerations

## Dev Notes

### Architecture Compliance

This story implements the **Downtime Analysis Tool** from the PRD Addendum (FR7.1 Core Operations Tools). It provides Pareto analysis to help plant managers identify and prioritize downtime causes.

**Location:** `apps/api/` (Python FastAPI Backend)
**Module:** `app/services/agent/tools/downtime_analysis.py`
**Pattern:** ManufacturingTool subclass with DataSource abstraction

### Technical Requirements

**Pareto Principle (80/20 Rule):**
```
The Pareto principle states that roughly 80% of effects come from 20% of causes.
In manufacturing downtime:
- ~20% of downtime reasons typically cause ~80% of total downtime
- Focus improvement efforts on these "vital few" causes
```

**Tool Flow Diagram:**
```
User: "Why was Grinder 5 down yesterday?"
    |
    v
+-------------------+
| Agent (tool       |
| selection)        |
+-------------------+
    |
    v
+------------------------+
| DowntimeAnalysisTool   |
| _arun()                |
+------------------------+
    |
    +---> parse_time_range("yesterday")
    |         --> (2026-01-08, 2026-01-08)
    |
    +---> data_source.get_asset_by_name("Grinder 5")
    |         --> asset record
    |
    +---> data_source.get_downtime(asset_id, start, end)
    |         --> daily_summaries with downtime_reasons
    |
    +---> calculate_pareto(downtime_reasons)
    |         --> sorted reasons with percentages
    |
    v
+-------------------+
| ToolResult        |
| (Pareto + citations)|
+-------------------+
```

### DowntimeAnalysisTool Implementation

**downtime_analysis.py Core Structure:**
```python
from typing import Optional, List, Literal
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field
from app.services.agent.base import ManufacturingTool, ToolResult, Citation
from app.services.agent.data_source import get_data_source
import logging

logger = logging.getLogger(__name__)

class DowntimeAnalysisInput(BaseModel):
    """Input schema for Downtime Analysis tool."""
    scope: str = Field(
        description="Asset name or area name to analyze downtime for"
    )
    time_range: Optional[str] = Field(
        default="yesterday",
        description="Time range like 'yesterday', 'last week', 'last 7 days'"
    )

class DowntimeReason(BaseModel):
    """Single downtime reason with Pareto analysis."""
    reason: str
    minutes: int
    percentage: float  # % of total downtime
    cumulative_percentage: float  # Running total %
    is_vital_few: bool  # Part of 80% threshold
    is_safety_related: bool = False
    contributing_assets: Optional[List[str]] = None  # For area queries

class DowntimeByAsset(BaseModel):
    """Downtime breakdown for a single asset (used in area queries)."""
    asset_name: str
    total_minutes: int
    top_reason: str
    top_reason_minutes: int

class DowntimeAnalysisOutput(BaseModel):
    """Output schema for Downtime Analysis tool."""
    scope_type: Literal["asset", "area"]
    scope_name: str
    date_range: str
    start_date: date
    end_date: date

    # Summary
    total_downtime_minutes: int
    uptime_percentage: float
    has_downtime: bool

    # Pareto analysis
    reasons: List[DowntimeReason]
    vital_few_reasons: List[str]  # Reasons causing 80% of downtime
    vital_few_percentage: float  # What % these vital few cause

    # Safety highlight
    safety_downtime_minutes: int
    safety_reasons: List[str]

    # Area breakdown (if scope is area)
    by_asset: Optional[List[DowntimeByAsset]] = None
    worst_asset: Optional[str] = None

    # Timestamps (if available)
    downtime_events: Optional[List[dict]] = None  # Specific events with times

class DowntimeAnalysisTool(ManufacturingTool):
    name: str = "downtime_analysis"
    description: str = """Analyze downtime reasons and patterns.
    Use this tool when a user asks about downtime, why equipment was down,
    or wants to understand causes of lost production time.
    Provides Pareto analysis showing top downtime reasons ranked by impact.
    Examples: "Why was Grinder 5 down?", "What are the top downtime reasons?",
    "Show me downtime for the Grinding area", "What caused us to lose time yesterday?"
    """
    args_schema: type = DowntimeAnalysisInput
    citations_required: bool = True

    # Safety-related reason codes (case-insensitive)
    SAFETY_REASONS = ["safety", "safety issue", "safety stop", "lockout", "tagout"]

    async def _arun(self, scope: str, time_range: str = "yesterday") -> ToolResult:
        """Execute downtime analysis and return structured results."""
        data_source = get_data_source()
        citations: List[Citation] = []

        # Parse time range
        start_date, end_date = self._parse_time_range(time_range)
        date_range_str = self._format_date_range(start_date, end_date)

        # Determine scope type
        scope_type = self._determine_scope_type(scope)

        if scope_type == "asset":
            return await self._analyze_asset_downtime(
                scope, start_date, end_date, date_range_str, data_source, citations
            )
        else:  # area
            return await self._analyze_area_downtime(
                scope, start_date, end_date, date_range_str, data_source, citations
            )

    async def _analyze_asset_downtime(
        self, asset_name: str, start_date: date, end_date: date,
        date_range_str: str, data_source, citations: List[Citation]
    ) -> ToolResult:
        """Analyze downtime for a single asset."""
        # Find asset
        asset_result = await data_source.get_asset_by_name(asset_name)
        citations.append(asset_result.to_citation())

        if not asset_result.data:
            return self._asset_not_found_response(asset_name, citations)

        asset = asset_result.data
        asset_id = asset["id"]

        # Get downtime data
        downtime_result = await data_source.get_downtime(asset_id, start_date, end_date)
        citations.append(downtime_result.to_citation())

        # Aggregate downtime reasons from all records
        all_reasons = self._aggregate_downtime_reasons(downtime_result.data or [])

        # Calculate total available time (assume 24h/day)
        total_days = (end_date - start_date).days + 1
        total_available_minutes = total_days * 24 * 60
        total_downtime = sum(all_reasons.values())

        if total_downtime == 0:
            return self._no_downtime_response(
                asset["name"], date_range_str, total_available_minutes, citations
            )

        # Perform Pareto analysis
        pareto_reasons = self._calculate_pareto(all_reasons)

        # Identify safety-related downtime
        safety_minutes, safety_reasons = self._extract_safety_downtime(pareto_reasons)

        # Find vital few (causes of 80%)
        vital_few = [r.reason for r in pareto_reasons if r.is_vital_few]
        vital_few_pct = sum(r.percentage for r in pareto_reasons if r.is_vital_few)

        output = DowntimeAnalysisOutput(
            scope_type="asset",
            scope_name=asset["name"],
            date_range=date_range_str,
            start_date=start_date,
            end_date=end_date,
            total_downtime_minutes=total_downtime,
            uptime_percentage=round(100 - (total_downtime / total_available_minutes * 100), 1),
            has_downtime=True,
            reasons=pareto_reasons,
            vital_few_reasons=vital_few,
            vital_few_percentage=round(vital_few_pct, 1),
            safety_downtime_minutes=safety_minutes,
            safety_reasons=safety_reasons
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

    def _aggregate_downtime_reasons(self, records: List[dict]) -> dict:
        """Aggregate downtime reasons from multiple daily records."""
        aggregated = {}
        for record in records:
            reasons = record.get("downtime_reasons", {})
            if isinstance(reasons, dict):
                for reason, minutes in reasons.items():
                    aggregated[reason] = aggregated.get(reason, 0) + minutes
            elif isinstance(reasons, str):
                # Handle case where downtime_reasons is JSON string
                import json
                try:
                    parsed = json.loads(reasons)
                    for reason, minutes in parsed.items():
                        aggregated[reason] = aggregated.get(reason, 0) + minutes
                except json.JSONDecodeError:
                    pass
        return aggregated

    def _calculate_pareto(self, reasons: dict) -> List[DowntimeReason]:
        """Calculate Pareto analysis for downtime reasons."""
        total = sum(reasons.values())
        if total == 0:
            return []

        # Sort by duration descending
        sorted_reasons = sorted(reasons.items(), key=lambda x: x[1], reverse=True)

        result = []
        cumulative = 0

        for reason, minutes in sorted_reasons:
            percentage = (minutes / total) * 100
            cumulative += percentage

            result.append(DowntimeReason(
                reason=reason,
                minutes=minutes,
                percentage=round(percentage, 1),
                cumulative_percentage=round(cumulative, 1),
                is_vital_few=cumulative <= 80,
                is_safety_related=self._is_safety_reason(reason)
            ))

        return result

    def _is_safety_reason(self, reason: str) -> bool:
        """Check if a reason is safety-related."""
        reason_lower = reason.lower()
        return any(safety in reason_lower for safety in self.SAFETY_REASONS)

    def _extract_safety_downtime(
        self, reasons: List[DowntimeReason]
    ) -> tuple[int, List[str]]:
        """Extract safety-related downtime from Pareto analysis."""
        safety_minutes = 0
        safety_reasons = []
        for r in reasons:
            if r.is_safety_related:
                safety_minutes += r.minutes
                safety_reasons.append(r.reason)
        return safety_minutes, safety_reasons

    def _no_downtime_response(
        self, asset_name: str, date_range: str,
        total_minutes: int, citations: List[Citation]
    ) -> ToolResult:
        """Generate response when no downtime recorded."""
        output = DowntimeAnalysisOutput(
            scope_type="asset",
            scope_name=asset_name,
            date_range=date_range,
            start_date=date.today(),
            end_date=date.today(),
            total_downtime_minutes=0,
            uptime_percentage=100.0,
            has_downtime=False,
            reasons=[],
            vital_few_reasons=[],
            vital_few_percentage=0,
            safety_downtime_minutes=0,
            safety_reasons=[]
        )

        return ToolResult(
            data={
                **output.dict(),
                "message": f"Great news! {asset_name} had no recorded downtime in {date_range}.",
                "congratulations": True
            },
            citations=citations,
            metadata={"cache_tier": "daily", "ttl_seconds": 900}
        )

    def _generate_follow_ups(self, output: DowntimeAnalysisOutput) -> List[str]:
        """Generate context-aware follow-up questions."""
        questions = []
        if output.vital_few_reasons:
            questions.append(f"Tell me more about '{output.vital_few_reasons[0]}'")
        if output.safety_reasons:
            questions.append("Show me all safety-related incidents")
        questions.append(f"What's the OEE for {output.scope_name}?")
        questions.append(f"How does {output.scope_name}'s downtime compare to last week?")
        return questions[:3]

    def _parse_time_range(self, time_range: str) -> tuple[date, date]:
        """Parse natural language time range into dates."""
        # Same implementation as OEE tool
        today = date.today()
        yesterday = today - timedelta(days=1)
        time_range_lower = time_range.lower().strip()

        if time_range_lower in ["yesterday", "t-1"]:
            return yesterday, yesterday
        elif time_range_lower in ["last week", "last 7 days", "past week"]:
            return yesterday - timedelta(days=6), yesterday
        elif time_range_lower in ["last 30 days", "last month"]:
            return yesterday - timedelta(days=29), yesterday
        else:
            return yesterday, yesterday

    def _format_date_range(self, start: date, end: date) -> str:
        """Format date range for display."""
        if start == end:
            return start.strftime("%b %d, %Y")
        return f"{start.strftime('%b %d')}-{end.strftime('%d, %Y')}"

    def _determine_scope_type(self, scope: str) -> str:
        """Determine if scope is asset or area."""
        # Simple heuristic - could be improved
        area_keywords = ["area", "line", "department", "zone", "section"]
        if any(kw in scope.lower() for kw in area_keywords):
            return "area"
        return "asset"
```

### Example Response Format

**Asset Downtime Response:**
```json
{
  "data": {
    "scope_type": "asset",
    "scope_name": "Grinder 5",
    "date_range": "Jan 8, 2026",
    "start_date": "2026-01-08",
    "end_date": "2026-01-08",
    "total_downtime_minutes": 152,
    "uptime_percentage": 89.4,
    "has_downtime": true,
    "reasons": [
      {
        "reason": "Material Jam",
        "minutes": 62,
        "percentage": 40.8,
        "cumulative_percentage": 40.8,
        "is_vital_few": true,
        "is_safety_related": false
      },
      {
        "reason": "Blade Change",
        "minutes": 47,
        "percentage": 30.9,
        "cumulative_percentage": 71.7,
        "is_vital_few": true,
        "is_safety_related": false
      },
      {
        "reason": "Operator Break",
        "minutes": 28,
        "percentage": 18.4,
        "cumulative_percentage": 90.1,
        "is_vital_few": false,
        "is_safety_related": false
      },
      {
        "reason": "Safety Stop",
        "minutes": 15,
        "percentage": 9.9,
        "cumulative_percentage": 100.0,
        "is_vital_few": false,
        "is_safety_related": true
      }
    ],
    "vital_few_reasons": ["Material Jam", "Blade Change"],
    "vital_few_percentage": 71.7,
    "safety_downtime_minutes": 15,
    "safety_reasons": ["Safety Stop"]
  },
  "citations": [
    {"source": "supabase.assets", "timestamp": "2026-01-09T10:00:00Z"},
    {"source": "supabase.daily_summaries", "timestamp": "2026-01-09T10:00:00Z"}
  ],
  "metadata": {
    "cache_tier": "daily",
    "ttl_seconds": 900,
    "follow_up_questions": [
      "Tell me more about 'Material Jam'",
      "Show me all safety-related incidents",
      "What's the OEE for Grinder 5?"
    ]
  }
}
```

**No Downtime Response:**
```json
{
  "data": {
    "scope_type": "asset",
    "scope_name": "Grinder 2",
    "date_range": "Jan 8, 2026",
    "total_downtime_minutes": 0,
    "uptime_percentage": 100.0,
    "has_downtime": false,
    "reasons": [],
    "vital_few_reasons": [],
    "vital_few_percentage": 0,
    "safety_downtime_minutes": 0,
    "safety_reasons": [],
    "message": "Great news! Grinder 2 had no recorded downtime in Jan 8, 2026.",
    "congratulations": true
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
│   │           └── downtime_analysis.py  # This tool
│   └── models/
│       └── agent.py                      # Add Downtime schemas
├── tests/
│   └── test_downtime_analysis_tool.py    # Tool tests
```

### Dependencies

**Story Dependencies:**
- Story 5.1 (Agent Framework) - ManufacturingTool base class
- Story 5.2 (Data Access Layer) - DataSource abstraction

**Blocked By:** Stories 5.1, 5.2

**Enables:**
- Story 5.7 (Agent Chat Integration) - Downtime analysis in chat
- Story 5.8 (Tool Response Caching) - Defines cache tier

### Testing Strategy

1. **Unit Tests:**
   - Tool initialization and registration
   - Asset downtime analysis with multiple reasons
   - Area downtime aggregation
   - Pareto calculation accuracy
   - Cumulative percentage calculation
   - Vital few identification (80% threshold)
   - Safety reason detection
   - No downtime handling
   - Time range parsing

2. **Integration Tests:**
   - Full tool execution with mock data source
   - Response schema validation
   - Citation accuracy

3. **Manual Testing:**
   - Test with real Supabase data
   - Verify Pareto calculations are correct
   - Test safety highlighting

### NFR Compliance

- **NFR1 (Accuracy):** Pareto calculations mathematically correct; all values cited
- **NFR4 (Agent Honesty):** Zero downtime handled honestly with congratulations
- **NFR6 (Response Structure):** Structured Pareto analysis with clear ranking

### References

- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#FR7.1 Core Operations Tools] - Downtime Analysis specification
- [Source: _bmad-output/planning-artifacts/epic-5.md#Story 5.5] - Story requirements
- [Source: _bmad/bmm/data/architecture.md#5. Data Models] - daily_summaries.downtime_reasons schema
- [Pareto Analysis](https://en.wikipedia.org/wiki/Pareto_analysis) - 80/20 rule reference

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

