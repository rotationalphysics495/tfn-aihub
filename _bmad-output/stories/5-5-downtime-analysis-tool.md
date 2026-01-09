# Story 5.5: Downtime Analysis Tool

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **to ask about downtime reasons and patterns for any asset or area**,
so that **I can identify and address the root causes of lost production time**.

## Acceptance Criteria

1. **Asset-Level Downtime Query**
   - GIVEN a user asks "Why was Grinder 5 down yesterday?"
   - WHEN the Downtime Analysis tool is invoked
   - THEN the response includes total downtime minutes
   - AND downtime reasons ranked by duration (Pareto distribution)
   - AND percentage of total downtime per reason
   - AND specific timestamps if available
   - AND all data points include citations

2. **Area-Level Downtime Query**
   - GIVEN a user asks "What are the top downtime reasons for the Grinding area this week?"
   - WHEN the Downtime Analysis tool is invoked
   - THEN the response aggregates across all assets in the area
   - AND shows which assets contributed most to each reason
   - AND highlights the top 3 reasons (80/20 Pareto principle)
   - AND all data includes citations

3. **No Downtime Handling**
   - GIVEN an asset had no downtime in the requested period
   - WHEN the Downtime Analysis tool is invoked
   - THEN the response states "[Asset] had no recorded downtime in [time range]"
   - AND shows total uptime percentage
   - AND includes citation for the query that returned no results
   - AND does NOT fabricate any downtime values

4. **Time Range Support**
   - GIVEN a user asks about downtime for a specific time range (e.g., "yesterday", "this week")
   - WHEN the Downtime Analysis tool parses the query
   - THEN the response covers the specified date range
   - AND citations reflect the actual dates queried
   - AND default time range is yesterday (T-1) if not specified

5. **Pareto Analysis**
   - GIVEN downtime data exists for the requested scope
   - WHEN the tool calculates Pareto distribution
   - THEN reasons are sorted by descending duration
   - AND cumulative percentage is calculated for each reason
   - AND the 80% threshold index is identified
   - AND actionable insight is provided (e.g., "Focus on these 3 reasons to address 80% of downtime")

6. **Safety Event Highlighting**
   - GIVEN some downtime events are safety-related
   - WHEN the tool returns results
   - THEN safety-related reasons are flagged prominently
   - AND safety events appear first regardless of duration
   - AND severity level is included if available

7. **Tool Registration**
   - GIVEN the agent framework is initialized
   - WHEN tools are auto-discovered
   - THEN DowntimeAnalysisTool is registered with the agent
   - AND its description enables correct intent matching for downtime questions

8. **Caching Support**
   - GIVEN downtime queries return historical data
   - WHEN the tool returns data
   - THEN responses are cached for 15 minutes (daily data tier)
   - AND cache metadata is included in response

## Tasks / Subtasks

- [ ] Task 1: Create DowntimeAnalysisTool Class (AC: #7)
  - [ ] 1.1 Create `apps/api/app/services/agent/tools/downtime_analysis.py`
  - [ ] 1.2 Extend ManufacturingTool base class from Story 5.1
  - [ ] 1.3 Define tool name: "downtime_analysis"
  - [ ] 1.4 Define tool description for intent matching (downtime, reasons, why down, Pareto)
  - [ ] 1.5 Create DowntimeAnalysisInput Pydantic schema
  - [ ] 1.6 Implement _arun() method with scope detection
  - [ ] 1.7 Create unit tests for tool class initialization

- [ ] Task 2: Define Input/Output Schemas (AC: #1, #5)
  - [ ] 2.1 Add DowntimeAnalysisInput to `apps/api/app/models/agent.py`
  - [ ] 2.2 Define scope field (asset_name OR area)
  - [ ] 2.3 Define time_range field (optional, default: yesterday)
  - [ ] 2.4 Add DowntimeAnalysisOutput model
  - [ ] 2.5 Define DowntimeReason model (reason, minutes, percentage, cumulative_percentage)
  - [ ] 2.6 Define scope_type, total_downtime, uptime_percentage fields
  - [ ] 2.7 Define asset_breakdown for area-level queries

- [ ] Task 3: Implement Asset-Level Downtime Query (AC: #1, #4)
  - [ ] 3.1 Parse asset_name from input
  - [ ] 3.2 Use data_source.get_asset_by_name() to resolve asset
  - [ ] 3.3 Use data_source.get_downtime() for downtime events
  - [ ] 3.4 Parse downtime_reasons JSON field from daily_summaries
  - [ ] 3.5 Build Pareto distribution from aggregated reasons
  - [ ] 3.6 Include timestamps if available
  - [ ] 3.7 Create unit tests for asset-level query

- [ ] Task 4: Implement Area-Level Downtime Query (AC: #2)
  - [ ] 4.1 Parse area from input
  - [ ] 4.2 Use data_source.get_assets_by_area() for asset list
  - [ ] 4.3 Aggregate downtime across all assets in area
  - [ ] 4.4 Calculate area-wide Pareto distribution
  - [ ] 4.5 Track which assets contributed to each reason
  - [ ] 4.6 Highlight top contributors per reason
  - [ ] 4.7 Create unit tests for area-level query

- [ ] Task 5: Implement Pareto Calculation (AC: #5)
  - [ ] 5.1 Leverage existing DowntimeAnalysisService.calculate_pareto() method
  - [ ] 5.2 Sort reasons by descending duration
  - [ ] 5.3 Calculate percentage and cumulative percentage
  - [ ] 5.4 Identify 80% threshold index
  - [ ] 5.5 Generate actionable insight message
  - [ ] 5.6 Create tests for Pareto calculation

- [ ] Task 6: Implement No Downtime Handling (AC: #3)
  - [ ] 6.1 Detect when query returns no downtime events
  - [ ] 6.2 Calculate uptime percentage (1 - downtime/planned time)
  - [ ] 6.3 Generate helpful message with scope and time range
  - [ ] 6.4 Include citation for empty query
  - [ ] 6.5 Create tests for no downtime scenarios

- [ ] Task 7: Implement Safety Event Highlighting (AC: #6)
  - [ ] 7.1 Use existing is_safety_related() check from DowntimeAnalysisService
  - [ ] 7.2 Flag safety-related reasons in output
  - [ ] 7.3 Sort safety events to top regardless of duration
  - [ ] 7.4 Include severity if available
  - [ ] 7.5 Create tests for safety event handling

- [ ] Task 8: Implement Time Range Parsing (AC: #4)
  - [ ] 8.1 Reuse parse_time_range() from OEEQueryTool (Story 5.4)
  - [ ] 8.2 Support "yesterday", "last week", "this week", "last 7 days"
  - [ ] 8.3 Default to yesterday (T-1) if not specified
  - [ ] 8.4 Return (start_date, end_date) tuple
  - [ ] 8.5 Create tests for time range parsing

- [ ] Task 9: Add Cache Metadata (AC: #8)
  - [ ] 9.1 Set cache_tier to "daily"
  - [ ] 9.2 Set ttl_seconds to 900 (15 minutes)
  - [ ] 9.3 Include date range in cache key considerations
  - [ ] 9.4 Add cached_at timestamp to metadata

- [ ] Task 10: Generate Follow-up Questions
  - [ ] 10.1 Generate context-aware follow-up questions
  - [ ] 10.2 Suggest OEE query if downtime is high
  - [ ] 10.3 Suggest specific asset drill-down for area queries
  - [ ] 10.4 Limit to 3 follow-up questions

## Dev Notes

### Architecture Compliance

This story implements the **Downtime Analysis Tool** from the PRD Addendum (FR7.1 Core Operations Tools). It provides Pareto analysis of downtime reasons to help plant managers identify and prioritize root cause elimination.

**Location:** `apps/api/` (Python FastAPI Backend)
**Module:** `app/services/agent/tools/downtime_analysis.py`
**Pattern:** ManufacturingTool subclass with DataSource abstraction

### Technical Requirements

**Pareto Analysis Principle:**
- 80/20 Rule: Typically 20% of causes account for 80% of downtime
- Sort reasons by descending duration
- Calculate cumulative percentage to identify the 80% threshold
- Focus improvement efforts on top reasons

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
+-------------------+
| DowntimeAnalysis  |
| Tool _arun()      |
+-------------------+
    |
    +---> parse_time_range("yesterday")
    |         --> (2026-01-08, 2026-01-08)
    |
    +---> data_source.get_asset_by_name("Grinder 5")
    |         --> asset_id, metadata
    |
    +---> data_source.get_downtime(asset_id, start, end)
    |         --> daily_summaries with downtime_reasons JSON
    |
    +---> Parse downtime_reasons JSON
    |         --> List of (reason_code, minutes)
    |
    +---> calculate_pareto(reasons)
    |         --> Sorted list with percentages
    |
    v
+-------------------+
| ToolResult        |
| (data + citations)|
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

# Safety keywords for event detection
SAFETY_KEYWORDS = ["safety", "safety issue", "emergency stop", "e-stop", "hazard", "injury"]

class DowntimeAnalysisInput(BaseModel):
    """Input schema for Downtime Analysis tool."""
    scope: str = Field(
        description="Asset name or area name to analyze downtime for"
    )
    time_range: Optional[str] = Field(
        default="yesterday",
        description="Time range like 'yesterday', 'last week', 'this week', 'last 7 days'"
    )

class DowntimeReason(BaseModel):
    """Single downtime reason in Pareto analysis."""
    reason_code: str
    total_minutes: int
    percentage: float  # 0-100
    cumulative_percentage: float  # 0-100
    is_safety_related: bool = False
    severity: Optional[str] = None
    contributing_assets: Optional[List[str]] = None  # For area-level queries

class DowntimeAnalysisOutput(BaseModel):
    """Output schema for Downtime Analysis tool."""
    scope_type: Literal["asset", "area"]
    scope_name: str
    date_range: str  # e.g., "Jan 8, 2026" or "Jan 2-8, 2026"
    start_date: date
    end_date: date

    # Downtime summary
    total_downtime_minutes: int
    total_downtime_hours: float
    uptime_percentage: float  # 0-100

    # Pareto analysis
    reasons: List[DowntimeReason]  # Sorted by descending duration
    threshold_80_index: Optional[int] = None  # Index where cumulative >= 80%
    top_reasons_summary: str  # e.g., "3 reasons account for 82% of downtime"

    # Asset breakdown for area queries
    asset_breakdown: Optional[List[dict]] = None  # {asset_name, downtime_minutes, top_reason}

    # Actionable insight
    insight: str  # e.g., "Focus on Material Jam and Blade Change to address 65% of downtime"

    # Safety summary
    safety_events_count: int = 0
    safety_downtime_minutes: int = 0

    # Metadata
    data_points: int  # Number of days/records included
    no_downtime: bool = False

class DowntimeAnalysisTool(ManufacturingTool):
    name: str = "downtime_analysis"
    description: str = """Analyze downtime reasons and patterns for assets or areas.
    Use this tool when a user asks about downtime, why equipment was down,
    downtime reasons, downtime patterns, or Pareto analysis.
    Returns Pareto distribution of downtime reasons ranked by duration.
    Examples: "Why was Grinder 5 down?", "What are the top downtime reasons for Grinding?",
    "Show me downtime patterns for this week", "What's causing the most downtime?"
    """
    args_schema: type = DowntimeAnalysisInput
    citations_required: bool = True

    def _is_safety_related(self, reason_code: str) -> bool:
        """Check if reason code is safety-related."""
        if not reason_code:
            return False
        return any(kw in reason_code.lower() for kw in SAFETY_KEYWORDS)

    async def _arun(self, scope: str, time_range: str = "yesterday") -> ToolResult:
        """Execute downtime analysis and return structured results."""
        data_source = get_data_source()
        citations: List[Citation] = []

        # Parse time range (reuse pattern from OEEQueryTool)
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
            return self._no_data_response(f"asset '{asset_name}'", date_range_str, citations)

        asset = asset_result.data
        asset_id = asset["id"]

        # Get downtime data from daily_summaries
        downtime_result = await data_source.get_downtime(asset_id, start_date, end_date)
        citations.append(downtime_result.to_citation())

        if not downtime_result.data:
            return self._no_downtime_response(asset["name"], date_range_str, citations)

        # Parse downtime_reasons JSON and aggregate
        reasons = self._aggregate_downtime_reasons(downtime_result.data)

        if not reasons:
            return self._no_downtime_response(asset["name"], date_range_str, citations)

        # Calculate Pareto distribution
        pareto_reasons, threshold_index = self._calculate_pareto(reasons)

        # Calculate totals
        total_minutes = sum(r.total_minutes for r in pareto_reasons)
        total_hours = round(total_minutes / 60.0, 2)

        # Calculate uptime (assuming 8-hour shifts, adjust based on actual planned time)
        days_in_range = (end_date - start_date).days + 1
        planned_minutes = days_in_range * 8 * 60  # Simplified
        uptime_pct = round((1 - total_minutes / planned_minutes) * 100, 1) if planned_minutes > 0 else 100.0

        # Safety summary
        safety_reasons = [r for r in pareto_reasons if r.is_safety_related]
        safety_count = len(safety_reasons)
        safety_minutes = sum(r.total_minutes for r in safety_reasons)

        # Generate insight
        insight = self._generate_insight(pareto_reasons, threshold_index)
        top_summary = self._generate_top_reasons_summary(pareto_reasons, threshold_index)

        output = DowntimeAnalysisOutput(
            scope_type="asset",
            scope_name=asset["name"],
            date_range=date_range_str,
            start_date=start_date,
            end_date=end_date,
            total_downtime_minutes=total_minutes,
            total_downtime_hours=total_hours,
            uptime_percentage=uptime_pct,
            reasons=pareto_reasons,
            threshold_80_index=threshold_index,
            top_reasons_summary=top_summary,
            insight=insight,
            safety_events_count=safety_count,
            safety_downtime_minutes=safety_minutes,
            data_points=len(downtime_result.data)
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

    def _aggregate_downtime_reasons(self, records: List[dict]) -> List[tuple]:
        """Aggregate downtime reasons from daily_summaries records."""
        from collections import defaultdict
        aggregates = defaultdict(int)

        for record in records:
            # Parse downtime_reasons JSON field
            reasons_json = record.get("downtime_reasons", {})
            if isinstance(reasons_json, str):
                import json
                try:
                    reasons_json = json.loads(reasons_json)
                except:
                    reasons_json = {}

            # Each key is a reason code, value is minutes
            for reason_code, minutes in reasons_json.items():
                if minutes and minutes > 0:
                    aggregates[reason_code] += minutes

        return list(aggregates.items())

    def _calculate_pareto(self, reasons: List[tuple]) -> tuple[List[DowntimeReason], Optional[int]]:
        """Calculate Pareto distribution from reason aggregates."""
        if not reasons:
            return [], None

        # Sort by descending minutes
        sorted_reasons = sorted(reasons, key=lambda x: x[1], reverse=True)

        total_minutes = sum(m for _, m in sorted_reasons)
        if total_minutes == 0:
            return [], None

        pareto_list = []
        cumulative = 0.0
        threshold_index = None

        for i, (reason_code, minutes) in enumerate(sorted_reasons):
            percentage = (minutes / total_minutes) * 100
            cumulative += percentage

            is_safety = self._is_safety_related(reason_code)

            pareto_list.append(DowntimeReason(
                reason_code=reason_code,
                total_minutes=minutes,
                percentage=round(percentage, 1),
                cumulative_percentage=round(cumulative, 1),
                is_safety_related=is_safety
            ))

            if threshold_index is None and cumulative >= 80.0:
                threshold_index = i

        # Move safety events to top while preserving order within each group
        safety_first = [r for r in pareto_list if r.is_safety_related]
        non_safety = [r for r in pareto_list if not r.is_safety_related]
        pareto_list = safety_first + non_safety

        return pareto_list, threshold_index

    def _generate_insight(self, reasons: List[DowntimeReason], threshold_index: Optional[int]) -> str:
        """Generate actionable insight based on Pareto analysis."""
        if not reasons:
            return "No downtime data to analyze."

        if len(reasons) == 1:
            return f"All downtime is from {reasons[0].reason_code}. Focus investigation here."

        if threshold_index is not None:
            top_reasons = [r.reason_code for r in reasons[:threshold_index + 1] if not r.is_safety_related]
            pct = reasons[threshold_index].cumulative_percentage if threshold_index < len(reasons) else 100
            if top_reasons:
                return f"Focus on {', '.join(top_reasons[:3])} to address {pct:.0f}% of downtime."

        top_reason = reasons[0]
        return f"{top_reason.reason_code} is your biggest issue at {top_reason.percentage:.0f}% of total downtime."

    def _generate_top_reasons_summary(self, reasons: List[DowntimeReason], threshold_index: Optional[int]) -> str:
        """Generate summary of top reasons."""
        if not reasons:
            return "No downtime reasons found."

        if threshold_index is not None:
            count = threshold_index + 1
            pct = reasons[threshold_index].cumulative_percentage
            return f"{count} reason{'s' if count > 1 else ''} account{'s' if count == 1 else ''} for {pct:.0f}% of downtime"

        return f"{len(reasons)} unique downtime reasons identified"

    def _no_downtime_response(self, scope: str, date_range: str, citations: List[Citation]) -> ToolResult:
        """Generate response when no downtime found (good news!)."""
        return ToolResult(
            data={
                "no_downtime": True,
                "message": f"{scope} had no recorded downtime in {date_range}",
                "scope_name": scope,
                "date_range": date_range,
                "uptime_percentage": 100.0,
                "insight": "Great performance! No downtime events recorded."
            },
            citations=citations,
            metadata={"cache_tier": "daily", "ttl_seconds": 900}
        )

    def _no_data_response(self, scope: str, date_range: str, citations: List[Citation]) -> ToolResult:
        """Generate response when asset/area not found."""
        return ToolResult(
            data={
                "no_data": True,
                "message": f"I don't have data for {scope}",
                "scope": scope,
                "date_range": date_range
            },
            citations=citations,
            metadata={"cache_tier": "daily", "ttl_seconds": 900}
        )

    def _generate_follow_ups(self, output: DowntimeAnalysisOutput) -> List[str]:
        """Generate context-aware follow-up questions."""
        questions = []

        if output.safety_events_count > 0:
            questions.append(f"Tell me more about the safety events on {output.scope_name}")

        if output.uptime_percentage < 90:
            questions.append(f"What's the OEE for {output.scope_name}?")

        if output.reasons and len(output.reasons) > 0:
            top_reason = output.reasons[0].reason_code
            questions.append(f"Show me {top_reason} trends over the past month")

        if output.scope_type == "area" and output.asset_breakdown:
            worst_asset = output.asset_breakdown[0]["asset_name"] if output.asset_breakdown else None
            if worst_asset:
                questions.append(f"Why was {worst_asset} down?")

        return questions[:3]

    def _parse_time_range(self, time_range: str) -> tuple[date, date]:
        """Parse natural language time range into dates."""
        today = date.today()
        yesterday = today - timedelta(days=1)

        time_range_lower = time_range.lower().strip()

        if time_range_lower in ["yesterday", "t-1"]:
            return yesterday, yesterday
        elif time_range_lower in ["last week", "last 7 days", "past week"]:
            return yesterday - timedelta(days=6), yesterday
        elif time_range_lower in ["this week"]:
            start_of_week = today - timedelta(days=today.weekday())
            return start_of_week, yesterday
        elif time_range_lower in ["today"]:
            return today, today
        else:
            return yesterday, yesterday

    def _format_date_range(self, start: date, end: date) -> str:
        """Format date range for display."""
        if start == end:
            return start.strftime("%b %d, %Y")
        return f"{start.strftime('%b %d')}-{end.strftime('%d, %Y')}"

    def _determine_scope_type(self, scope: str) -> str:
        """Determine if scope is asset or area."""
        # Known area names (should come from config or database)
        area_keywords = ["grinding", "packaging", "assembly", "machining", "area", "department"]
        scope_lower = scope.lower()

        if any(kw in scope_lower for kw in area_keywords):
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
    "total_downtime_minutes": 127,
    "total_downtime_hours": 2.12,
    "uptime_percentage": 73.5,
    "reasons": [
      {
        "reason_code": "Material Jam",
        "total_minutes": 48,
        "percentage": 37.8,
        "cumulative_percentage": 37.8,
        "is_safety_related": false
      },
      {
        "reason_code": "Blade Change",
        "total_minutes": 35,
        "percentage": 27.6,
        "cumulative_percentage": 65.4,
        "is_safety_related": false
      },
      {
        "reason_code": "Operator Break",
        "total_minutes": 25,
        "percentage": 19.7,
        "cumulative_percentage": 85.0,
        "is_safety_related": false
      },
      {
        "reason_code": "Calibration",
        "total_minutes": 19,
        "percentage": 15.0,
        "cumulative_percentage": 100.0,
        "is_safety_related": false
      }
    ],
    "threshold_80_index": 2,
    "top_reasons_summary": "3 reasons account for 85% of downtime",
    "insight": "Focus on Material Jam, Blade Change to address 65% of downtime.",
    "safety_events_count": 0,
    "safety_downtime_minutes": 0,
    "data_points": 1,
    "no_downtime": false
  },
  "citations": [
    {"source": "supabase.assets", "timestamp": "2026-01-09T10:30:00Z"},
    {"source": "supabase.daily_summaries", "timestamp": "2026-01-09T10:30:00Z", "query": "asset_id=grinder5, date=2026-01-08"}
  ],
  "metadata": {
    "cache_tier": "daily",
    "ttl_seconds": 900,
    "follow_up_questions": [
      "What's the OEE for Grinder 5?",
      "Show me Material Jam trends over the past month",
      "How does Grinder 5 compare to other grinders?"
    ]
  }
}
```

**Area Downtime Response:**
```json
{
  "data": {
    "scope_type": "area",
    "scope_name": "Grinding",
    "date_range": "Jan 2-8, 2026",
    "total_downtime_minutes": 523,
    "total_downtime_hours": 8.72,
    "uptime_percentage": 81.2,
    "reasons": [
      {
        "reason_code": "Material Jam",
        "total_minutes": 198,
        "percentage": 37.9,
        "cumulative_percentage": 37.9,
        "contributing_assets": ["Grinder 5", "Grinder 3"]
      },
      {
        "reason_code": "Blade Change",
        "total_minutes": 145,
        "percentage": 27.7,
        "cumulative_percentage": 65.6,
        "contributing_assets": ["Grinder 5", "Grinder 1", "Grinder 2"]
      }
    ],
    "asset_breakdown": [
      {"asset_name": "Grinder 5", "downtime_minutes": 267, "top_reason": "Material Jam"},
      {"asset_name": "Grinder 3", "downtime_minutes": 142, "top_reason": "Material Jam"},
      {"asset_name": "Grinder 1", "downtime_minutes": 78, "top_reason": "Blade Change"},
      {"asset_name": "Grinder 2", "downtime_minutes": 36, "top_reason": "Calibration"}
    ],
    "threshold_80_index": 1,
    "top_reasons_summary": "2 reasons account for 66% of downtime",
    "insight": "Focus on Material Jam, Blade Change to address 66% of downtime. Grinder 5 is your biggest opportunity."
  }
}
```

### Existing Code to Leverage

This tool should leverage the existing `DowntimeAnalysisService` in `apps/api/app/services/downtime_analysis.py`:

**Reusable Methods:**
- `is_safety_related()` - Safety keyword detection
- `calculate_pareto()` - Pareto distribution calculation
- `get_downtime_from_daily_summaries()` - Query daily_summaries table
- `get_assets_map()` - Asset ID to name mapping with caching
- `calculate_financial_impact()` - Financial loss calculation

**Adapt, Don't Duplicate:**
```python
from app.services.downtime_analysis import DowntimeAnalysisService

# In DowntimeAnalysisTool:
async def _arun(self, scope: str, time_range: str = "yesterday") -> ToolResult:
    # Use existing service for heavy lifting
    service = DowntimeAnalysisService(get_supabase_client())
    downtime_events = await service.transform_to_downtime_events(...)
    pareto_items, threshold = service.calculate_pareto(downtime_events)
    # ... format as ToolResult
```

### Project Structure Notes

**Files to create:**
```
apps/api/
├── app/
│   ├── services/
│   │   └── agent/
│   │       └── tools/
│   │           └── downtime_analysis.py   # This tool
│   └── models/
│       └── agent.py                       # Add Downtime schemas
├── tests/
│   └── test_downtime_analysis_tool.py     # Tool tests
```

**Alignment with existing structure:**
- Follow pattern from existing `downtime_analysis.py` service
- Reuse models from `models/downtime.py` where applicable
- New agent-specific models go in `models/agent.py`

### Dependencies

**Story Dependencies:**
- Story 5.1 (Agent Framework) - ManufacturingTool base class
- Story 5.2 (Data Access Layer) - DataSource abstraction
- Story 5.4 (OEE Query Tool) - Time range parsing pattern

**Blocked By:** Stories 5.1, 5.2

**Enables:**
- Story 5.8 (Tool Response Caching) - Defines cache tier
- Epic 6 tools can reference downtime patterns

### Testing Strategy

1. **Unit Tests:**
   - Tool initialization and registration
   - Asset-level downtime query with various scenarios
   - Area-level downtime query with aggregation
   - Pareto calculation correctness
   - Time range parsing (all variations)
   - No downtime handling
   - Safety event detection and highlighting
   - Follow-up question generation

2. **Integration Tests:**
   - Full tool execution with mock data source
   - Response schema validation
   - Citation accuracy
   - Interaction with DowntimeAnalysisService

3. **Manual Testing:**
   - Test with real Supabase data
   - Verify Pareto percentages are correct
   - Test various time range expressions
   - Confirm safety events appear first

### NFR Compliance

- **NFR1 (Accuracy):** Pareto calculation follows standard 80/20 principle; all values cited
- **NFR4 (Agent Honesty):** Missing data and no-downtime scenarios handled honestly
- **NFR5 (Tool Extensibility):** Follows ManufacturingTool pattern for auto-registration
- **NFR6 (Response Structure):** Structured output with actionable insights
- **NFR7 (Tool Response Caching):** 15-minute TTL for daily data tier

### References

- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#FR7.1 Core Operations Tools] - Downtime Analysis specification
- [Source: _bmad-output/planning-artifacts/epic-5.md#Story 5.5] - Story requirements
- [Source: _bmad/bmm/data/architecture.md#5. Data Models] - daily_summaries schema
- [Source: apps/api/app/services/downtime_analysis.py] - Existing downtime service patterns
- [Source: apps/api/app/models/downtime.py] - Existing downtime models
- [Source: _bmad-output/implementation-artifacts/5-4-oee-query-tool.md] - Previous story patterns

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
