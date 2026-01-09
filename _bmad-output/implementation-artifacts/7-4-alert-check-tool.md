# Story 7.4: Alert Check Tool

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **to quickly check if there are any active alerts or warnings**,
so that I can **respond to emerging issues before they escalate and maintain situational awareness**.

## Acceptance Criteria

1. **Active Alerts Query**
   - Given a user asks "Are there any alerts?"
   - When the Alert Check tool is invoked
   - Then the response includes:
     - Count of active alerts by severity
     - For each alert: type, asset, description, recommended response
     - Time since alert was triggered
     - Escalation status (if applicable)
   - And alerts are sorted by severity (critical first)

2. **Severity Filtering**
   - Given a user asks with a severity filter (e.g., "Any critical alerts?")
   - When the Alert Check tool is invoked
   - Then only alerts matching that severity are returned
   - And response indicates filter applied

3. **No Alerts Scenario**
   - Given no active alerts exist
   - When the Alert Check tool is invoked
   - Then the response states "No active alerts - all systems normal"
   - And shows time since last alert (if any)

4. **Stale Alert Flagging**
   - Given an alert has been active for >1 hour without resolution
   - When the Alert Check tool is invoked
   - Then the alert is flagged as "Requires Attention"
   - And escalation is suggested

5. **Alert Sources**
   - Alert sources include:
     - Safety events (unresolved)
     - Production variance >20%
     - Equipment status changes
   - Severity levels: critical, warning, info

6. **Data Freshness & Caching**
   - Cache TTL: 60 seconds (alerts should be fresh)
   - Data freshness timestamp included in response
   - Support for `force_refresh` parameter

## Tasks / Subtasks

- [ ] Task 1: Define Alert Check Schemas (AC: #1, #2, #5)
  - [ ] 1.1 Create `AlertCheckInput` Pydantic model with fields: `severity_filter` (optional), `area_filter` (optional), `include_resolved` (default: False)
  - [ ] 1.2 Create `Alert` model with fields: `alert_id`, `type`, `severity`, `asset`, `description`, `recommended_response`, `triggered_at`, `duration_minutes`, `requires_attention`, `escalation_status`
  - [ ] 1.3 Create `AlertCheckOutput` model with fields: `alerts`, `count_by_severity`, `summary`, `last_alert_time`, `citations`
  - [ ] 1.4 Add schemas to `apps/api/app/models/agent.py`

- [ ] Task 2: Implement Alert Check Tool (AC: #1, #2, #3)
  - [ ] 2.1 Create `apps/api/app/services/agent/tools/alert_check.py`
  - [ ] 2.2 Query `safety_events` for unresolved safety alerts
  - [ ] 2.3 Query `live_snapshots` for production variance anomalies (>20%)
  - [ ] 2.4 Query equipment status changes from relevant tables
  - [ ] 2.5 Implement severity filtering (critical, warning, info)
  - [ ] 2.6 Implement area filtering
  - [ ] 2.7 Handle "no alerts" scenario with last alert timestamp

- [ ] Task 3: Implement Alert Processing (AC: #4, #5)
  - [ ] 3.1 Calculate duration since alert triggered
  - [ ] 3.2 Flag alerts >1 hour as "Requires Attention"
  - [ ] 3.3 Categorize alerts by severity level
  - [ ] 3.4 Generate recommended responses for each alert type
  - [ ] 3.5 Sort alerts by severity (critical first), then by age

- [ ] Task 4: Integrate with LangChain Agent (AC: #1, #2)
  - [ ] 4.1 Create LangChain Tool wrapper for AlertCheckTool
  - [ ] 4.2 Define tool description for agent selection
  - [ ] 4.3 Register tool with ManufacturingAgent
  - [ ] 4.4 Test tool selection for alert queries

- [ ] Task 5: Implement Caching (AC: #6)
  - [ ] 5.1 Add 60-second cache for alert results
  - [ ] 5.2 Cache key includes: severity_filter, area_filter
  - [ ] 5.3 Include `cached_at` in response metadata
  - [ ] 5.4 Support `force_refresh` parameter

- [ ] Task 6: Testing and Validation (AC: #1-6)
  - [ ] 6.1 Unit tests for alert aggregation from multiple sources
  - [ ] 6.2 Unit tests for severity filtering
  - [ ] 6.3 Unit tests for stale alert flagging
  - [ ] 6.4 Unit tests for "no alerts" scenario
  - [ ] 6.5 Integration tests for LangChain tool registration
  - [ ] 6.6 Performance tests (< 2 second response time)

## Dev Notes

### Architecture Patterns

- **Backend Framework:** Python FastAPI (apps/api)
- **AI Orchestration:** LangChain AgentExecutor with tool registration
- **Alert Sources:** Multiple tables aggregated into unified alert format
- **Citation System:** Integrate with existing citation infrastructure from Story 4-5

### Technical Requirements

**Alert Check Schemas:**
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

class AlertCheckInput(BaseModel):
    """Input schema for Alert Check tool"""
    severity_filter: Optional[Literal["critical", "warning", "info"]] = Field(
        default=None,
        description="Filter by severity level"
    )
    area_filter: Optional[str] = Field(
        default=None,
        description="Filter to specific area (e.g., 'Grinding')"
    )
    include_resolved: bool = Field(
        default=False,
        description="Include recently resolved alerts (last 4 hours)"
    )
    force_refresh: bool = Field(
        default=False,
        description="Bypass cache for fresh data"
    )

class Alert(BaseModel):
    """A single active alert"""
    alert_id: str
    type: str  # "safety", "production_variance", "equipment_status"
    severity: Literal["critical", "warning", "info"]
    asset: str
    area: str
    description: str
    recommended_response: str
    triggered_at: datetime
    duration_minutes: int
    requires_attention: bool  # True if >1 hour unresolved
    escalation_status: Optional[str]  # "none", "notified", "escalated"
    source_table: str  # For citation

class AlertCheckOutput(BaseModel):
    """Output schema for Alert Check tool"""
    alerts: List[Alert]
    count_by_severity: dict  # {"critical": 1, "warning": 2, "info": 0}
    total_count: int
    summary: str
    last_alert_time: Optional[datetime]  # When last alert occurred
    all_clear_since: Optional[datetime]  # When operations became clear
    citations: List[dict]
```

**Alert Check Tool Implementation:**
```python
from langchain.tools import BaseTool
from typing import Type
from datetime import datetime, timedelta

# Thresholds
PRODUCTION_VARIANCE_THRESHOLD = 0.20  # 20% variance triggers alert
STALE_ALERT_MINUTES = 60  # 1 hour = requires attention

class AlertCheckTool(BaseTool):
    name: str = "alert_check"
    description: str = """Check for active alerts and warnings across the plant.
    Use this when the user asks 'Are there any alerts?', 'Any issues right now?',
    'Is anything wrong?', 'Any critical alerts?', or wants real-time status.
    Returns alerts sorted by severity: critical > warning > info."""
    args_schema: Type[AlertCheckInput] = AlertCheckInput

    async def _arun(
        self,
        severity_filter: Optional[str] = None,
        area_filter: Optional[str] = None,
        include_resolved: bool = False,
        force_refresh: bool = False
    ) -> AlertCheckOutput:

        # Check cache (60 second TTL)
        cache_key = f"alerts:{severity_filter or 'all'}:{area_filter or 'all'}"
        if not force_refresh:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        alerts = []
        citations = []

        # Source 1: Safety Events (unresolved)
        safety_alerts = await self._get_safety_alerts(area_filter, include_resolved)
        alerts.extend(safety_alerts)

        # Source 2: Production Variance Anomalies
        variance_alerts = await self._get_variance_alerts(area_filter)
        alerts.extend(variance_alerts)

        # Source 3: Equipment Status Changes
        equipment_alerts = await self._get_equipment_alerts(area_filter)
        alerts.extend(equipment_alerts)

        # Apply severity filter
        if severity_filter:
            alerts = [a for a in alerts if a.severity == severity_filter]

        # Process alerts: calculate duration, flag stale
        for alert in alerts:
            alert.duration_minutes = int(
                (datetime.now() - alert.triggered_at).total_seconds() / 60
            )
            alert.requires_attention = alert.duration_minutes > STALE_ALERT_MINUTES

        # Sort by severity (critical first), then by triggered time (newest first)
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        alerts.sort(key=lambda a: (severity_order[a.severity], -a.duration_minutes))

        # Count by severity
        count_by_severity = {
            "critical": len([a for a in alerts if a.severity == "critical"]),
            "warning": len([a for a in alerts if a.severity == "warning"]),
            "info": len([a for a in alerts if a.severity == "info"])
        }

        # Generate summary
        summary = self._generate_summary(alerts, count_by_severity, severity_filter)

        # Get last alert time for "all clear" message
        last_alert = await self._get_last_alert_time() if not alerts else None

        result = AlertCheckOutput(
            alerts=alerts,
            count_by_severity=count_by_severity,
            total_count=len(alerts),
            summary=summary,
            last_alert_time=alerts[0].triggered_at if alerts else None,
            all_clear_since=last_alert,
            citations=self._generate_citations(alerts)
        )

        # Cache for 60 seconds
        await self.cache.set(cache_key, result, ttl=60)

        return result

    async def _get_safety_alerts(
        self,
        area_filter: Optional[str],
        include_resolved: bool
    ) -> List[Alert]:
        """Get unresolved safety events as alerts"""
        query = """
            SELECT se.id, se.severity, se.description, se.created_at,
                   se.resolution_status, a.name as asset_name, a.area
            FROM safety_events se
            JOIN assets a ON se.asset_id = a.id
            WHERE se.resolution_status != 'resolved'
        """
        if area_filter:
            query += f" AND a.area = '{area_filter}'"
        if include_resolved:
            query += " OR (se.resolution_status = 'resolved' AND se.resolved_at > NOW() - INTERVAL '4 hours')"

        rows = await self.db.execute(query)

        return [
            Alert(
                alert_id=f"safety-{row.id}",
                type="safety",
                severity="critical" if row.severity > 5 else "warning",
                asset=row.asset_name,
                area=row.area,
                description=row.description,
                recommended_response=self._get_safety_response(row.severity),
                triggered_at=row.created_at,
                duration_minutes=0,  # Calculated later
                requires_attention=False,  # Calculated later
                escalation_status=row.resolution_status,
                source_table="safety_events"
            )
            for row in rows
        ]

    async def _get_variance_alerts(
        self,
        area_filter: Optional[str]
    ) -> List[Alert]:
        """Get production variance anomalies from live_snapshots"""
        query = """
            SELECT ls.*, a.name as asset_name, a.area,
                   st.target_output,
                   (st.target_output - ls.actual_output)::float / st.target_output as variance
            FROM live_snapshots ls
            JOIN assets a ON ls.asset_id = a.id
            JOIN shift_targets st ON a.id = st.asset_id
            WHERE ABS((st.target_output - ls.actual_output)::float / st.target_output) > 0.20
            AND ls.snapshot_at > NOW() - INTERVAL '30 minutes'
        """
        if area_filter:
            query += f" AND a.area = '{area_filter}'"

        rows = await self.db.execute(query)

        return [
            Alert(
                alert_id=f"variance-{row.asset_id}",
                type="production_variance",
                severity="warning",
                asset=row.asset_name,
                area=row.area,
                description=f"Production {abs(row.variance)*100:.0f}% {'below' if row.variance > 0 else 'above'} target",
                recommended_response="Investigate production line status and operator availability",
                triggered_at=row.snapshot_at,
                duration_minutes=0,
                requires_attention=False,
                escalation_status="none",
                source_table="live_snapshots"
            )
            for row in rows
        ]

    def _get_safety_response(self, severity: int) -> str:
        """Generate recommended response based on safety severity"""
        if severity >= 8:
            return "IMMEDIATE: Stop operations, confirm lockout/tagout, notify supervisor"
        elif severity >= 5:
            return "Investigate immediately, isolate affected area if necessary"
        else:
            return "Review during next shift handoff, document incident"
```

### Database Tables Referenced

| Table | Usage |
|-------|-------|
| `safety_events` | Unresolved safety incidents |
| `live_snapshots` | Real-time production data for variance detection |
| `assets` | Asset names and area assignments |
| `shift_targets` | Target values for variance calculation |

### Dependencies

**Requires (must be completed):**
- Story 2.6: Safety Alert System (provides safety_events table and alerting)
- Story 2.9: Live Pulse Ticker (provides live_snapshots data)
- Story 5.1: Agent Framework & Tool Registry (provides tool registration pattern)
- Story 5.2: Data Access Abstraction Layer (provides data source interface)
- Story 4.5: Cited Response Generation (provides citation infrastructure)

**Enables:**
- FR7.4: Proactive Action Tools - Alert Check capability
- Real-time situational awareness through natural language
- Quick status checks during shift operations

### Project Structure Notes

```
apps/api/app/
  services/
    agent/
      tools/
        alert_check.py            # Alert Check tool (NEW)
  models/
    agent.py                      # Add AlertCheckInput/Output (MODIFY)

apps/api/tests/
  test_alert_check_tool.py        # Unit and integration tests (NEW)
```

### NFR Compliance

- **NFR1 (Accuracy):** All alerts cite specific source data
- **NFR2 (Latency):** 60-second cache ensures fresh data within latency requirements
- **NFR4 (Agent Honesty):** Clear "all systems normal" when no alerts exist
- **NFR6 (Response Structure):** Alerts sorted by severity with clear status

### Testing Guidance

**Unit Tests:**
```python
import pytest
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_alert_aggregation():
    """Test alerts aggregated from multiple sources"""
    tool = AlertCheckTool(db=mock_db, cache=mock_cache)
    result = await tool._arun()

    # Should have alerts from safety_events and live_snapshots
    source_types = set(a.type for a in result.alerts)
    assert "safety" in source_types or "production_variance" in source_types

@pytest.mark.asyncio
async def test_severity_sorting():
    """Test critical alerts come before warning"""
    tool = AlertCheckTool(db=mock_db_mixed_alerts, cache=mock_cache)
    result = await tool._arun()

    if len(result.alerts) > 1:
        for i in range(len(result.alerts) - 1):
            curr = result.alerts[i]
            next_alert = result.alerts[i + 1]
            severity_order = {"critical": 0, "warning": 1, "info": 2}
            assert severity_order[curr.severity] <= severity_order[next_alert.severity]

@pytest.mark.asyncio
async def test_severity_filtering():
    """Test filtering by severity level"""
    tool = AlertCheckTool(db=mock_db_mixed_alerts, cache=mock_cache)
    result = await tool._arun(severity_filter="critical")

    for alert in result.alerts:
        assert alert.severity == "critical"

@pytest.mark.asyncio
async def test_no_alerts_scenario():
    """Test response when no active alerts"""
    tool = AlertCheckTool(db=mock_db_clear, cache=mock_cache)
    result = await tool._arun()

    assert result.total_count == 0
    assert "normal" in result.summary.lower() or "clear" in result.summary.lower()

@pytest.mark.asyncio
async def test_stale_alert_flagging():
    """Test alerts >1 hour are flagged as requires attention"""
    # Mock alert triggered 90 minutes ago
    mock_db_stale = create_mock_with_old_alert(minutes_ago=90)
    tool = AlertCheckTool(db=mock_db_stale, cache=mock_cache)
    result = await tool._arun()

    stale_alerts = [a for a in result.alerts if a.requires_attention]
    assert len(stale_alerts) > 0
    for alert in stale_alerts:
        assert alert.duration_minutes > 60

@pytest.mark.asyncio
async def test_count_by_severity():
    """Test alert count breakdown by severity"""
    tool = AlertCheckTool(db=mock_db_mixed_alerts, cache=mock_cache)
    result = await tool._arun()

    total_from_counts = sum(result.count_by_severity.values())
    assert total_from_counts == result.total_count

@pytest.mark.asyncio
async def test_cache_60_seconds():
    """Test 60-second cache TTL"""
    tool = AlertCheckTool(db=mock_db, cache=mock_cache)

    # First call
    result1 = await tool._arun()
    assert mock_db.call_count > 0

    initial_calls = mock_db.call_count

    # Second call within 60 seconds - should use cache
    result2 = await tool._arun()
    assert mock_db.call_count == initial_calls  # No new DB calls
```

**Integration Tests:**
```python
@pytest.mark.asyncio
async def test_tool_agent_integration():
    """Test tool is correctly selected by agent"""
    agent = ManufacturingAgent(tools=[alert_check_tool])
    response = await agent.invoke("Are there any alerts?")

    assert "alert_check" in response.tool_calls

@pytest.mark.asyncio
async def test_alert_queries_select_tool():
    """Test various alert queries select this tool"""
    queries = [
        "Are there any alerts?",
        "Any critical alerts?",
        "Is anything wrong?",
        "Any issues right now?",
        "Check for warnings",
        "Status of all alerts"
    ]

    agent = ManufacturingAgent(tools=[alert_check_tool])
    for query in queries:
        response = await agent.invoke(query)
        assert "alert_check" in response.tool_calls
```

### Response Format Examples

**Active Alerts:**
```markdown
## Alert Status
*As of 2:45 PM - Real-time data*

**Active Alerts: 3** (1 Critical, 2 Warning)

### CRITICAL (1)

**Safety Stop - Packaging Line 2**
- Triggered: 45 minutes ago (2:00 PM)
- Description: Safety interlock triggered - operator investigation required
- Action: IMMEDIATE - Confirm lockout/tagout complete, notify supervisor
- Status: Under investigation
[Citation: safety_events @ 14:00:00]

### WARNING (2)

**Production Variance - Grinder 5** [REQUIRES ATTENTION]
- Triggered: 1 hour 15 minutes ago (1:30 PM)
- Description: Production 28% below target
- Action: Investigate production line status and operator availability
- Status: Unresolved (escalation suggested)
[Citation: live_snapshots @ 14:45:00]

**Equipment Status - CAMA 800-1**
- Triggered: 20 minutes ago (2:25 PM)
- Description: Scheduled maintenance mode activated
- Action: Verify maintenance window per schedule
- Status: Expected
[Citation: equipment_status @ 14:25:00]

---
Should I provide more details on any of these alerts?
```

**No Alerts:**
```markdown
## Alert Status
*As of 2:45 PM - Real-time data*

**No active alerts - all systems normal**

Operations have been clear since 11:30 AM (3 hours, 15 minutes ago).

Last resolved alert was a production variance on Grinder 3, resolved at 11:28 AM.

[Citation: safety_events, live_snapshots @ 14:45:00]
```

**Filtered Results:**
```markdown
## Alert Status - Critical Only
*As of 2:45 PM - Filtered by severity: CRITICAL*

**Critical Alerts: 1**

**Safety Stop - Packaging Line 2**
- Triggered: 45 minutes ago
- Description: Safety interlock triggered
- Action: IMMEDIATE - Confirm lockout/tagout complete
[Citation: safety_events @ 14:00:00]

---
*Note: Showing critical alerts only. 2 additional warnings exist.*
Want me to show all alerts?
```

### References

- [Source: _bmad-output/planning-artifacts/epic-7.md#Story 7.4] - Alert Check Tool requirements
- [Source: _bmad-output/planning-artifacts/prd-addendum-ai-agent-tools.md#FR7.4] - Proactive Action Tools specification
- [Source: _bmad/bmm/data/prd.md#FR4] - Safety Alerting requirements
- [Source: _bmad-output/implementation-artifacts/2-6-safety-alert-system.md] - Safety alert infrastructure
- [Source: _bmad-output/implementation-artifacts/2-9-live-pulse-ticker.md] - Live snapshot data
- [Source: _bmad-output/implementation-artifacts/4-5-cited-response-generation.md] - Citation infrastructure

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
