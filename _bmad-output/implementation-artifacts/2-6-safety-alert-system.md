# Story 2.6: Safety Alert System

Status: ready-for-dev

## Story

As a **Plant Manager or Line Supervisor**,
I want **immediate "Red" visual alerting whenever a "Safety Issue" reason code is detected in the Live Pulse polling data**,
so that **I can take immediate action on safety incidents without delay, ensuring zero-incident visibility across the plant floor**.

## Acceptance Criteria

1. System detects any `reason_code = 'Safety Issue'` (or equivalent safety-related codes) during the Live Pulse 15-minute polling cycle
2. Safety events are immediately persisted to the `safety_events` table in Supabase with timestamp, asset reference, and raw event details
3. Frontend displays a "Safety Red" visual indicator that is distinct from all other status colors and reserved exclusively for safety incidents
4. Safety alerts appear prominently in the Live Pulse view with "glanceability" - readable from 3 feet away on a tablet
5. Safety alerts link directly to the specific asset that triggered the alert
6. Alert banner/indicator persists until explicitly acknowledged or the polling window passes without recurrence
7. Safety event detection operates within the 60-second latency requirement (NFR2)
8. All safety event queries use the read-only MSSQL connection (NFR3)
9. Safety alert count is visible in the Command Center UI header/status area
10. Safety events include financial impact context when available from `cost_centers` (FR5 integration)

## Tasks / Subtasks

- [ ] Task 1: Extend Live Pulse Pipeline for Safety Detection (AC: #1, #7, #8)
  - [ ] 1.1 Add safety reason code detection logic to polling service
  - [ ] 1.2 Define safety reason code patterns (exact match or pattern matching)
  - [ ] 1.3 Add read-only MSSQL query for safety-related downtime codes
  - [ ] 1.4 Ensure polling cycle completes within 60-second latency window

- [ ] Task 2: Safety Events Database Integration (AC: #2)
  - [ ] 2.1 Create/verify `safety_events` table schema in Supabase
  - [ ] 2.2 Implement safety event persistence service in FastAPI
  - [ ] 2.3 Add asset_id foreign key reference to link events to assets
  - [ ] 2.4 Add timestamp, raw event data, and source MSSQL reference fields

- [ ] Task 3: Safety Alert API Endpoints (AC: #5, #9)
  - [ ] 3.1 Create `GET /api/safety/events` endpoint for recent safety events
  - [ ] 3.2 Create `GET /api/safety/active` endpoint for currently active (unacknowledged) alerts
  - [ ] 3.3 Create `POST /api/safety/acknowledge/{event_id}` endpoint for dismissing alerts
  - [ ] 3.4 Add safety event count to dashboard status endpoint

- [ ] Task 4: Frontend Safety Alert UI Components (AC: #3, #4, #6)
  - [ ] 4.1 Create SafetyAlertBanner component with "Safety Red" exclusive color
  - [ ] 4.2 Implement high-contrast, glanceable design (readable from 3 feet)
  - [ ] 4.3 Add alert persistence logic until acknowledged
  - [ ] 4.4 Create SafetyAlertCard for individual event display

- [ ] Task 5: Live Pulse Integration (AC: #4, #5, #9)
  - [ ] 5.1 Integrate safety alerts into Live Pulse ticker view
  - [ ] 5.2 Add safety count indicator to Command Center header
  - [ ] 5.3 Link safety alerts to Asset Detail View navigation
  - [ ] 5.4 Add real-time polling/refresh for safety alert status

- [ ] Task 6: Financial Context Integration (AC: #10)
  - [ ] 6.1 Join safety events with `cost_centers` data for financial impact
  - [ ] 6.2 Display estimated financial impact on safety alert cards
  - [ ] 6.3 Calculate downtime cost using `standard_hourly_rate`

## Dev Notes

### Technical Stack Requirements

| Component | Technology | Version | Notes |
|-----------|-----------|---------|-------|
| Backend | Python | 3.11+ | FastAPI async endpoints |
| API Framework | FastAPI | 0.109+ | RESTful safety endpoints |
| Database | PostgreSQL | 15+ (Supabase) | safety_events table |
| MSSQL Driver | pyodbc/SQLAlchemy | Latest | Read-only connection (NFR3) |
| Frontend | Next.js | 14+ (App Router) | Safety alert components |
| Styling | Tailwind CSS | 3.x | "Safety Red" color theme |
| UI Components | Shadcn/UI | Latest | Alert/banner components |

### Architecture Patterns

#### Pipeline B: Live Pulse Safety Detection
The safety detection integrates into the existing 15-minute polling pipeline:

```
Live Pulse Poll (every 15 min)
    └── Fetch last 30 min rolling window from MSSQL
    └── Check for reason_code = 'Safety Issue'
        └── IF FOUND: Create entry in safety_events table
    └── Calculate Output vs Target (existing logic)
    └── Update live_snapshots
```

#### Safety Events Data Model

```sql
-- safety_events table (Supabase)
CREATE TABLE safety_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID REFERENCES assets(id),
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source_timestamp TIMESTAMP WITH TIME ZONE,
    reason_code VARCHAR(255),
    reason_description TEXT,
    source_record_id VARCHAR(255),  -- Reference to MSSQL record
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by UUID,
    financial_impact DECIMAL(12,2),  -- From cost_centers calculation
    metadata JSONB
);
```

#### API Endpoint Specifications

```
GET /api/safety/events
  Query params: ?limit=50&since=<ISO8601>&asset_id=<uuid>
  Response: { events: SafetyEvent[], count: number }

GET /api/safety/active
  Response: { events: SafetyEvent[], count: number }

POST /api/safety/acknowledge/{event_id}
  Body: { acknowledged_by?: string }
  Response: { success: boolean, event: SafetyEvent }

GET /api/dashboard/status
  Response includes: { safety_alert_count: number, ... }
```

### UX Design Requirements

#### "Safety Red" Color Specification
- **CRITICAL**: "Safety Red" is reserved EXCLUSIVELY for safety incidents
- Color: `#DC2626` (Tailwind red-600) or equivalent high-visibility red
- Must contrast with all other status colors in the system
- No other UI element should use this exact red shade

#### Glanceability Requirements
- Alert banner must be readable from 3 feet away on a tablet
- Minimum font size: 18px for alert text
- Use iconography (warning triangle) alongside text
- High contrast: white text on red background

#### Alert Banner Layout
```
+---------------------------------------------------------------+
| [!] SAFETY ALERT: Safety Issue detected on Grinder 5      [X] |
|     Detected 2 min ago | Estimated Impact: $1,240/hr          |
+---------------------------------------------------------------+
```

### File Structure

```text
apps/
├── api/
│   └── app/
│       ├── api/
│       │   ├── safety.py           # NEW: Safety alert endpoints
│       │   └── dashboard.py        # MODIFY: Add safety count
│       ├── services/
│       │   ├── safety_service.py   # NEW: Safety detection logic
│       │   └── ingestion.py        # MODIFY: Add safety detection to polling
│       └── models/
│           └── safety.py           # NEW: SafetyEvent Pydantic models
├── web/
│   └── src/
│       ├── components/
│       │   └── safety/
│       │       ├── SafetyAlertBanner.tsx   # NEW
│       │       ├── SafetyAlertCard.tsx     # NEW
│       │       └── SafetyIndicator.tsx     # NEW: Header count badge
│       ├── hooks/
│       │   └── useSafetyAlerts.ts          # NEW: Safety data fetching
│       └── app/
│           └── (dashboard)/
│               └── live-pulse/
│                   └── page.tsx             # MODIFY: Add safety section
```

### Dependencies

#### Required from Previous Stories
- **Story 2.2: Polling Data Pipeline (T-15m)** - Must be complete for Live Pulse infrastructure
- **Story 1.3: Plant Object Model Schema** - Provides `assets` table for linking
- **Story 1.4: Analytical Cache Schema** - Provides `safety_events` table schema
- **Story 2.7: Financial Impact Calculator** - Provides financial context (can be parallel)

#### Tables Required
- `assets` (from Story 1.3) - for linking safety events to specific machines
- `cost_centers` (from Story 1.3) - for financial impact calculation
- `safety_events` (from Story 1.4) - persistent safety event log

### MSSQL Query Pattern

```python
# Example safety detection query (read-only per NFR3)
SAFETY_QUERY = """
SELECT
    location_name,
    reason_code,
    reason_description,
    start_time,
    record_id
FROM downtime_events
WHERE reason_code LIKE '%Safety%'
   OR reason_code = 'Safety Issue'
AND start_time >= :window_start
ORDER BY start_time DESC
"""
```

### NFR Compliance

| NFR | Requirement | Implementation |
|-----|-------------|----------------|
| NFR2 | 60-second latency | Poll cycle + detection + persistence < 60s |
| NFR3 | Read-only MSSQL | All source queries use RO_User connection |

### Anti-Patterns to Avoid

1. **DO NOT** use "Safety Red" color for any non-safety UI elements
2. **DO NOT** write to the source MSSQL database - read-only only
3. **DO NOT** block the polling loop on safety event persistence - use async/background
4. **DO NOT** rely on frontend-only state for alert persistence - persist to database
5. **DO NOT** skip financial context - FR5 requires integrated financial visibility
6. **DO NOT** create duplicate safety events for the same incident - use source_record_id for deduplication

### Testing Verification

After implementation, verify:
1. Inject a mock "Safety Issue" reason code into test data
2. Verify safety event appears in `safety_events` table within 60 seconds
3. Verify Safety Alert Banner displays in Live Pulse view
4. Verify banner is readable from 3+ feet distance on tablet
5. Verify "Safety Red" color is distinct from all other colors
6. Verify acknowledgement dismisses the alert
7. Verify safety count appears in Command Center header
8. Verify asset link navigates to correct Asset Detail View
9. Verify financial impact displays when cost_center data available

### Project Structure Notes

- Safety components go in `apps/web/src/components/safety/` following component organization pattern
- Safety endpoints go in `apps/api/app/api/safety.py` following existing API module pattern
- Safety service logic goes in `apps/api/app/services/safety_service.py`
- Follow existing Pydantic model patterns for `SafetyEvent` schema

### References

- [Source: architecture.md#6-data-pipelines] - Pipeline B Live Pulse specification
- [Source: architecture.md#5-data-models] - safety_events table definition
- [Source: prd.md#2-requirements] - FR4 Safety Alerting requirement
- [Source: ux-design.md#2-design-principles] - "Safety Red" exclusive color principle
- [Source: ux-design.md#2-usability-goals] - Glanceability requirement (3 feet)
- [Source: epics.md#epic-2] - Epic 2 goal and FR coverage
- [Source: prd.md#2-requirements] - NFR2 60-second latency, NFR3 Read-Only

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
