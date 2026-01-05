# Story 2.3: Throughput Dashboard

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want **a visual dashboard showing Actual vs Target production throughput for all assets**,
so that **I can quickly identify which machines are behind target and prioritize my attention during shift reviews**.

## Acceptance Criteria

1. **Dashboard Route and Navigation**
   - GIVEN an authenticated user navigates to the Production Intelligence section
   - WHEN they access the Throughput Dashboard
   - THEN a dedicated page/view displays at route `/dashboard/production/throughput` or integrated within Command Center
   - AND the page is accessible from main navigation

2. **Actual vs Target Visualization**
   - GIVEN throughput data exists in the `live_snapshots` table
   - WHEN the dashboard loads
   - THEN each asset displays:
     - Asset name (from `assets` table)
     - Current actual output (numeric)
     - Target output (numeric)
     - Variance (actual - target) with visual indicator
     - Percentage of target achieved (actual/target * 100)
   - AND the display uses a visual format (bar chart, gauge, or card grid) that supports "glanceability"

3. **Status Indicators**
   - GIVEN an asset's throughput data
   - WHEN displaying the variance
   - THEN visual status indicators show:
     - **On Target** (green/success): Actual >= Target
     - **Behind** (amber/warning): Actual < Target by < 10%
     - **Critical** (amber-dark/warning): Actual < Target by >= 10%
   - AND "Safety Red" is NOT used for production status (reserved for safety incidents per UX guidelines)

4. **Data Freshness Indicator**
   - GIVEN the dashboard is displaying data
   - WHEN the page renders
   - THEN a timestamp shows "Last updated: [timestamp]" indicating data freshness
   - AND if data is older than 60 seconds, a warning indicator appears
   - AND the data auto-refreshes or provides a manual refresh option

5. **Real-time Data Binding**
   - GIVEN the Live Pulse pipeline (Story 2.2) is populating `live_snapshots`
   - WHEN new data arrives (every 15 minutes)
   - THEN the dashboard reflects updated values within the NFR2 latency requirement (60 seconds)

6. **Responsive Layout**
   - GIVEN the dashboard is viewed on different devices
   - WHEN displayed on tablet (primary) or desktop
   - THEN the layout adapts appropriately:
     - Tablet: Card grid or stacked view optimized for touch
     - Desktop: Full dashboard with all metrics visible
   - AND text sizes meet "glanceability" requirement (readable from 3 feet)

7. **Empty State Handling**
   - GIVEN no throughput data exists for an asset
   - WHEN the dashboard loads
   - THEN a meaningful empty state is displayed: "No throughput data available. Waiting for Live Pulse data."
   - AND the UI does not break or show errors

8. **Asset Filtering (Optional Enhancement)**
   - GIVEN multiple assets exist
   - WHEN viewing the dashboard
   - THEN users can optionally filter by:
     - Asset area (from `assets.area`)
     - Status (on_target, behind, ahead)

## Tasks / Subtasks

- [ ] Task 1: Create API Endpoint for Throughput Data (AC: #2, #5)
  - [ ] 1.1 Create `/api/production/throughput` endpoint in FastAPI
  - [ ] 1.2 Query `live_snapshots` JOIN `assets` for latest snapshot per asset
  - [ ] 1.3 Calculate variance and percentage of target
  - [ ] 1.4 Return structured JSON with asset details, actual, target, variance, status, timestamp

- [ ] Task 2: Create Throughput Dashboard Page (AC: #1, #6)
  - [ ] 2.1 Create page component at `apps/web/src/app/dashboard/production/throughput/page.tsx`
  - [ ] 2.2 Integrate with Command Center navigation
  - [ ] 2.3 Implement responsive grid layout using Tailwind CSS
  - [ ] 2.4 Add page metadata (title: "Throughput Dashboard")

- [ ] Task 3: Build Throughput Card Component (AC: #2, #3)
  - [ ] 3.1 Create `ThroughputCard` component in `apps/web/src/components/production/`
  - [ ] 3.2 Display asset name, actual, target, variance, percentage
  - [ ] 3.3 Implement status-based styling (on_target=green, behind=amber)
  - [ ] 3.4 Use Shadcn/UI Card with Industrial Clarity theme

- [ ] Task 4: Implement Status Indicators (AC: #3)
  - [ ] 4.1 Create status badge component or extend Badge from Story 1.6
  - [ ] 4.2 Define threshold logic: on_target (>=100%), behind (<100% && >=90%), critical (<90%)
  - [ ] 4.3 Apply appropriate color tokens (success, warning, warning-dark)
  - [ ] 4.4 Ensure NO use of safety-red for production status

- [ ] Task 5: Add Data Freshness Indicator (AC: #4)
  - [ ] 5.1 Display "Last updated" timestamp in human-readable format
  - [ ] 5.2 Add visual warning if data older than 60 seconds
  - [ ] 5.3 Implement auto-refresh (polling or real-time subscription)
  - [ ] 5.4 Add manual refresh button

- [ ] Task 6: Implement Data Fetching and State Management (AC: #5, #7)
  - [ ] 6.1 Create React hook or server component for data fetching
  - [ ] 6.2 Handle loading state with skeleton/spinner
  - [ ] 6.3 Implement empty state component
  - [ ] 6.4 Handle error states gracefully

- [ ] Task 7: Visual Design and Glanceability (AC: #6)
  - [ ] 7.1 Ensure minimum font sizes per Industrial Clarity guidelines
  - [ ] 7.2 Use appropriate card spacing for tablet touch targets
  - [ ] 7.3 Test contrast ratios for factory floor visibility
  - [ ] 7.4 Apply "Live" mode styling (vibrant indicators) per UX design

- [ ] Task 8: Optional Asset Filtering (AC: #8)
  - [ ] 8.1 Add filter dropdown for asset area
  - [ ] 8.2 Add filter tabs/buttons for status
  - [ ] 8.3 Implement client-side filtering or server-side query params

## Dev Notes

### Architecture Patterns

**Frontend (Next.js App Router):**
- Use React Server Components where data doesn't need client interactivity
- Use Client Components for interactive elements (filters, refresh button)
- File path: `apps/web/src/app/dashboard/production/throughput/page.tsx`
- Components: `apps/web/src/components/production/`

**Backend (FastAPI):**
- Endpoint location: `apps/api/app/api/production.py` or `apps/api/app/api/endpoints/throughput.py`
- Use SQLAlchemy session from MSSQL connection (Story 1.5) for source queries
- Use Supabase client for `live_snapshots` queries
- Follow existing API patterns from Epic 1 stories

**Data Flow:**
```
MSSQL (source) -> Pipeline B (Live Pulse) -> Supabase live_snapshots -> API -> Frontend
```

### Technical Requirements

**API Response Schema:**
```typescript
interface ThroughputData {
  assets: {
    id: string;
    name: string;
    area: string;
    actual_output: number;
    target_output: number;
    variance: number;
    percentage: number;
    status: 'on_target' | 'behind' | 'ahead';
    snapshot_timestamp: string;
  }[];
  last_updated: string;
}
```

**Status Calculation Logic:**
```python
def calculate_status(actual: int, target: int) -> str:
    if target == 0:
        return 'on_target'  # Avoid division by zero
    percentage = (actual / target) * 100
    if percentage >= 100:
        return 'on_target'
    elif percentage >= 90:
        return 'behind'
    else:
        return 'ahead'  # Actually means critically behind
```

**Color Token Usage (from Story 1.6 Industrial Clarity):**
- On Target: `success.green` (#10B981)
- Behind: `warning.amber` (#F59E0B)
- Critical Behind: `warning.amber-dark` (#B45309)
- NEVER use `safety.red` for production metrics

### NFR Compliance

| NFR | Requirement | Implementation |
|-----|-------------|----------------|
| NFR2 | Data reflects SQL within 60 seconds | Auto-refresh polling + freshness warning |
| NFR3 | Read-only MSSQL access | Data sourced from Supabase cache, not direct MSSQL |

### Dependencies

**Requires (Must be completed first):**
- Story 1.4: Analytical Cache Schema - `live_snapshots` table must exist
- Story 1.5: MSSQL Read-Only Connection - For source data
- Story 1.6: Industrial Clarity Design System - For styling components
- Story 1.7: Command Center UI Shell - For navigation integration
- Story 2.1: Batch Data Pipeline - For historical data context
- Story 2.2: Polling Data Pipeline (T-15m) - Populates `live_snapshots`

**Enables:**
- Story 2.4: OEE Metrics View - Similar visualization patterns
- Story 2.8: Cost of Loss Widget - Financial overlay on throughput
- Story 2.9: Live Pulse Ticker - Throughput summary component

### UX Design Compliance

| Principle | Implementation |
|-----------|----------------|
| **Action First, Data Second** | Throughput cards highlight variance/status prominently |
| **Glanceability** | Large numbers, clear status colors, readable from 3ft |
| **Industrial High-Contrast** | Use Industrial Clarity theme tokens |
| **Visual Context: Live Mode** | Use vibrant/pulsing indicators for live data |
| **Safety Red Reserved** | Status indicators use amber/green ONLY |

### Project Structure Notes

```
apps/
  web/
    src/
      app/
        dashboard/
          production/
            throughput/
              page.tsx          # Main throughput dashboard page
      components/
        production/
          ThroughputCard.tsx    # Individual asset throughput card
          ThroughputGrid.tsx    # Grid container for cards
          StatusBadge.tsx       # Status indicator component
          DataFreshnessIndicator.tsx
  api/
    app/
      api/
        endpoints/
          production.py        # /api/production/throughput endpoint
      services/
        production.py          # Business logic for throughput calculations
```

### Testing Requirements

**Frontend Tests:**
- Component renders correctly with mock data
- Status indicators display correct colors for different variances
- Empty state displays when no data
- Responsive layout works on tablet viewport (768px - 1024px)

**Backend Tests:**
- API endpoint returns correct data structure
- Status calculation logic handles edge cases (zero target, negative values)
- Database queries use appropriate indexes

**Integration Tests:**
- End-to-end data flow from `live_snapshots` to dashboard
- Auto-refresh updates display within 60 seconds

### References

- [Source: _bmad/bmm/data/architecture.md#5. Data Models] - live_snapshots table schema
- [Source: _bmad/bmm/data/architecture.md#6. Data Pipelines] - Pipeline B (Live Pulse) context
- [Source: _bmad/bmm/data/ux-design.md#2. Overall UX Goals] - Glanceability, Industrial Clarity
- [Source: _bmad/bmm/data/ux-design.md#3. Information Architecture] - Production Intelligence > Throughput & OEE
- [Source: _bmad/bmm/data/prd.md#FR1] - Data Ingestion requirement
- [Source: _bmad/bmm/data/prd.md#NFR2] - 60-second latency requirement
- [Source: _bmad-output/planning-artifacts/epic-2.md#Story 2.3] - Story definition
- [Source: _bmad-output/implementation-artifacts/1-4-analytical-cache-schema.md] - live_snapshots schema
- [Source: _bmad-output/implementation-artifacts/1-6-industrial-clarity-design-system.md] - Color tokens and design patterns
- [Source: _bmad-output/implementation-artifacts/1-7-command-center-ui-shell.md] - Navigation integration patterns

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

### File List
