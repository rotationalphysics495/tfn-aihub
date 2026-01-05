# Story 2.9: Live Pulse Ticker

Status: ready-for-dev

## Story

As a **Plant Manager or Line Supervisor**,
I want a **15-minute real-time status ticker displaying current production status with integrated financial context**,
so that I can **monitor live factory performance at a glance and immediately understand the financial impact of ongoing operations**.

## Acceptance Criteria

1. **Live Pulse Ticker Component**
   - Ticker component displays in the "Live Pulse" section of Command Center (from Story 1.7 placeholder)
   - Shows last-updated timestamp with visual indication of data freshness
   - Updates automatically every 15 minutes (matching Pipeline B polling cycle)
   - Uses "Live" mode visual styling per Industrial Clarity design system (vibrant/pulsing indicators)

2. **Production Status Display**
   - Shows current shift's throughput vs target as percentage and absolute values
   - Displays current OEE metric (calculated from live_snapshots data)
   - Shows active/total machine count with status breakdown (running, idle, down)
   - Indicates any active downtime events with reason codes

3. **Financial Context Integration**
   - Displays real-time "Cost of Loss" calculation based on current downtime and waste
   - Shows financial impact in dollars ($) using cost_centers hourly rates
   - Financial values update with each 15-minute data refresh
   - Clearly distinguishes between "shift-to-date" and "rolling 15-min" financial figures

4. **Safety Alert Integration**
   - Displays prominent "Safety Red" indicator if any active safety_events exist
   - Safety alerts take visual priority over all other metrics (per FR4)
   - Links to Safety Alert System (Story 2.6) for details when safety incident is active
   - "Safety Red" color ONLY used for actual safety incidents (per UX design principle)

5. **Data Source Integration**
   - Consumes data from `live_snapshots` table (populated by Story 2.2 Polling Pipeline)
   - Consumes data from `safety_events` table (populated by Story 2.6)
   - Uses `cost_centers` data for financial calculations (Story 2.7 Financial Impact Calculator)
   - Displays "Data Stale" warning if last_updated exceeds 20 minutes (NFR2 compliance)

6. **Performance Requirements**
   - Ticker renders within 500ms of page load
   - Data refresh completes within 2 seconds of API response
   - Meets NFR2: Live views reflect SQL data within 60 seconds of ingestion

7. **Industrial Clarity Compliance**
   - High-contrast colors readable from 3 feet on tablet (per UX "Glanceability" requirement)
   - Clear visual distinction between "Live Pulse" mode and "Retrospective" sections
   - Large metric displays (minimum 24px for key values, 48px+ for primary metrics)
   - Pulsing/animated indicator showing "live" status

## Tasks / Subtasks

- [ ] Task 1: Create LivePulseTicker React component (AC: #1, #7)
  - [ ] 1.1 Create `apps/web/src/components/dashboard/LivePulseTicker.tsx`
  - [ ] 1.2 Implement component with "Live" mode styling from Industrial Clarity design system
  - [ ] 1.3 Add pulsing animation indicator for live status
  - [ ] 1.4 Add last-updated timestamp with freshness indicator
  - [ ] 1.5 Replace placeholder in LivePulseSection from Story 1.7

- [ ] Task 2: Create API endpoint for live pulse data (AC: #5, #6)
  - [ ] 2.1 Create `apps/api/app/api/live_pulse.py` router
  - [ ] 2.2 Implement `GET /api/live-pulse` endpoint
  - [ ] 2.3 Query `live_snapshots` for latest production data
  - [ ] 2.4 Query `safety_events` for any active safety incidents
  - [ ] 2.5 Join with `cost_centers` for financial calculations
  - [ ] 2.6 Return aggregated ticker data with timestamp
  - [ ] 2.7 Register router in `apps/api/app/main.py`

- [ ] Task 3: Implement production status metrics (AC: #2)
  - [ ] 3.1 Create ProductionStatusMetric subcomponent
  - [ ] 3.2 Display throughput vs target (percentage + absolute)
  - [ ] 3.3 Display OEE metric from live_snapshots
  - [ ] 3.4 Display machine status breakdown (running/idle/down counts)
  - [ ] 3.5 Show active downtime events with reason codes

- [ ] Task 4: Implement financial context display (AC: #3)
  - [ ] 4.1 Create FinancialContextWidget subcomponent
  - [ ] 4.2 Calculate cost-of-loss from downtime_minutes * hourly_rate
  - [ ] 4.3 Calculate waste cost from waste_quantity * unit_cost
  - [ ] 4.4 Display total financial impact in dollars
  - [ ] 4.5 Add labels distinguishing "shift-to-date" vs "rolling 15-min"

- [ ] Task 5: Implement safety alert indicator (AC: #4)
  - [ ] 5.1 Create SafetyAlertIndicator subcomponent
  - [ ] 5.2 Query safety_events for any active (unresolved) incidents
  - [ ] 5.3 Display "Safety Red" indicator when incidents exist
  - [ ] 5.4 Ensure safety indicator takes visual priority
  - [ ] 5.5 Link to Safety Alert System detail view

- [ ] Task 6: Implement auto-refresh and data freshness (AC: #1, #5, #6)
  - [ ] 6.1 Implement 15-minute polling interval using React hooks (useEffect + setInterval)
  - [ ] 6.2 Add data staleness detection (warning if > 20 min old)
  - [ ] 6.3 Display "Data Stale" warning indicator when threshold exceeded
  - [ ] 6.4 Add manual refresh button

- [ ] Task 7: Integration testing (AC: #6)
  - [ ] 7.1 Test ticker renders with mock live_snapshots data
  - [ ] 7.2 Test financial calculations with mock cost_centers data
  - [ ] 7.3 Test safety alert display with mock safety_events
  - [ ] 7.4 Test data staleness warning
  - [ ] 7.5 Test auto-refresh interval

## Dev Notes

### Architecture Patterns

- **Frontend Framework:** Next.js 14+ with App Router
- **Backend Framework:** Python FastAPI (apps/api)
- **Styling:** Tailwind CSS + Shadcn/UI with Industrial Clarity theme (Story 1.6)
- **Data Source:** Supabase PostgreSQL (analytical cache tables)
- **API Pattern:** REST endpoints under `/api/` prefix

### Technical Requirements

**Frontend (apps/web):**
- Use React Server Components where possible, Client Components for real-time updates
- Implement polling with `useEffect` + `setInterval` (15-min = 900000ms)
- Use `swr` or React Query for data fetching and caching (preferred for real-time data)
- Apply "Live" mode color variants from Industrial Clarity palette:
  - `live-primary: #8B5CF6` (vibrant purple)
  - `live-pulse: #7C3AED` (for animations)
  - `safety-red: #DC2626` (ONLY for safety incidents)

**Backend (apps/api):**
- FastAPI router pattern per existing codebase
- Use SQLAlchemy ORM for database queries
- Protect endpoint with Supabase Auth JWT validation
- Return Pydantic models for type safety

**Database Schema (from Stories 1.3, 1.4):**
```sql
-- live_snapshots (from Analytical Cache - Story 1.4)
live_snapshots:
  id: UUID
  asset_id: FK -> assets.id
  timestamp: DateTime
  output_count: Integer
  target_output: Integer
  oee_percentage: Decimal
  downtime_minutes: Integer
  downtime_reason: String
  created_at: DateTime

-- safety_events (from Story 2.6)
safety_events:
  id: UUID
  asset_id: FK -> assets.id
  detected_at: DateTime
  reason_code: String (= 'Safety Issue')
  resolved_at: DateTime (nullable)
  severity: String

-- cost_centers (from Plant Object Model - Story 1.3)
cost_centers:
  id: UUID
  asset_id: FK -> assets.id
  standard_hourly_rate: Decimal
```

### Financial Calculation Logic (from Story 2.7)

```python
# Cost of Loss Calculation
downtime_cost = downtime_minutes / 60 * standard_hourly_rate
waste_cost = waste_quantity * unit_cost  # if waste tracking available
total_cost_of_loss = downtime_cost + waste_cost
```

### UX Design Compliance

| Principle | Implementation |
|-----------|----------------|
| Glanceability | Large metric text (48px+ primary, 24px+ secondary) |
| Industrial Clarity | High-contrast live-mode colors, factory-floor readable |
| Action First | Safety alerts take visual priority over all other metrics |
| Visual Context | Pulsing animation indicates "live" mode vs static retrospective |
| Safety Red Reserved | ONLY use #DC2626 for actual safety incidents |

### Project Structure Notes

```
apps/web/src/
  components/
    dashboard/
      LivePulseTicker.tsx        # Main ticker component (NEW)
      ProductionStatusMetric.tsx # Production metrics subcomponent (NEW)
      FinancialContextWidget.tsx # Financial display subcomponent (NEW)
      SafetyAlertIndicator.tsx   # Safety alert subcomponent (NEW)
      LivePulseSection.tsx       # Update placeholder from Story 1.7

apps/api/app/
  api/
    live_pulse.py               # Live pulse endpoint router (NEW)
  services/
    live_pulse_service.py       # Business logic for live pulse (NEW)
```

### Dependencies

**Requires (must be completed):**
- Story 1.4: Analytical Cache Schema (provides live_snapshots table)
- Story 1.5: MSSQL Read-Only Connection (data source for polling)
- Story 1.6: Industrial Clarity Design System (styling components)
- Story 1.7: Command Center UI Shell (provides LivePulseSection placeholder)
- Story 2.2: Polling Data Pipeline T-15m (populates live_snapshots)
- Story 2.6: Safety Alert System (populates safety_events)
- Story 2.7: Financial Impact Calculator (provides calculation logic)

**Enables:**
- Epic 3: Action Engine will use live_snapshots for real-time synthesis
- Epic 4: AI Chat can query live production status

### NFR Compliance

- **NFR2 (Latency):** Live views must reflect SQL data within 60 seconds - ticker refreshes every 15 minutes, data staleness warning at 20 minutes ensures this is visible
- **NFR3 (Read-Only):** All source data flows through Pipeline B polling - no direct MSSQL writes from ticker

### Testing Guidance

**Unit Tests:**
- Test financial calculation logic with various downtime/cost scenarios
- Test data freshness detection logic
- Test safety alert priority logic

**Integration Tests:**
- Test API endpoint returns correct aggregated data
- Test ticker component renders with realistic mock data
- Test auto-refresh mechanism

**Visual Tests:**
- Verify high-contrast readability on tablet viewport (768px-1024px)
- Verify pulsing animation renders correctly
- Verify safety red only appears with active safety incidents

### API Response Schema

```typescript
interface LivePulseData {
  timestamp: string;               // ISO 8601 timestamp
  production: {
    currentOutput: number;
    targetOutput: number;
    outputPercentage: number;      // currentOutput / targetOutput * 100
    oeePercentage: number;
    machineStatus: {
      running: number;
      idle: number;
      down: number;
      total: number;
    };
    activeDowntime: Array<{
      assetName: string;
      reasonCode: string;
      durationMinutes: number;
    }>;
  };
  financial: {
    shiftToDateLoss: number;       // Total $ loss for current shift
    rolling15MinLoss: number;      // $ loss in last 15 min window
    currency: string;              // "USD"
  };
  safety: {
    hasActiveIncident: boolean;
    activeIncidents: Array<{
      id: string;
      assetName: string;
      detectedAt: string;
      severity: string;
    }>;
  };
  meta: {
    dataAge: number;               // seconds since last update
    isStale: boolean;              // true if dataAge > 1200 (20 min)
  };
}
```

### References

- [Source: _bmad/bmm/data/architecture.md#6. Data Pipelines] - Pipeline B "Live Pulse" 15-minute polling
- [Source: _bmad/bmm/data/architecture.md#5. Data Models] - live_snapshots, safety_events, cost_centers schemas
- [Source: _bmad/bmm/data/prd.md#2. Requirements] - FR4 Safety Alerting, FR5 Financial Context, NFR2 Latency
- [Source: _bmad/bmm/data/ux-design.md#2. Overall UX Goals] - Glanceability, Industrial Clarity, Safety Red rules
- [Source: _bmad/bmm/data/ux-design.md#3. Information Architecture] - Live Pulse Ticker in Command Center
- [Source: _bmad-output/planning-artifacts/epic-2.md] - Epic 2 scope and Story 2.9 definition
- [Source: _bmad-output/implementation-artifacts/1-6-industrial-clarity-design-system.md] - Industrial Clarity color palette and typography
- [Source: _bmad-output/implementation-artifacts/1-7-command-center-ui-shell.md] - LivePulseSection placeholder to replace

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
