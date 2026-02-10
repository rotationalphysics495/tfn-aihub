# Story 2.3: Throughput Dashboard

Status: Done

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

- [x] Task 1: Create API Endpoint for Throughput Data (AC: #2, #5)
  - [x] 1.1 Create `/api/production/throughput` endpoint in FastAPI
  - [x] 1.2 Query `live_snapshots` JOIN `assets` for latest snapshot per asset
  - [x] 1.3 Calculate variance and percentage of target
  - [x] 1.4 Return structured JSON with asset details, actual, target, variance, status, timestamp

- [x] Task 2: Create Throughput Dashboard Page (AC: #1, #6)
  - [x] 2.1 Create page component at `apps/web/src/app/dashboard/production/throughput/page.tsx`
  - [x] 2.2 Integrate with Command Center navigation
  - [x] 2.3 Implement responsive grid layout using Tailwind CSS
  - [x] 2.4 Add page metadata (title: "Throughput Dashboard")

- [x] Task 3: Build Throughput Card Component (AC: #2, #3)
  - [x] 3.1 Create `ThroughputCard` component in `apps/web/src/components/production/`
  - [x] 3.2 Display asset name, actual, target, variance, percentage
  - [x] 3.3 Implement status-based styling (on_target=green, behind=amber)
  - [x] 3.4 Use Shadcn/UI Card with Industrial Clarity theme

- [x] Task 4: Implement Status Indicators (AC: #3)
  - [x] 4.1 Create status badge component or extend Badge from Story 1.6
  - [x] 4.2 Define threshold logic: on_target (>=100%), behind (<100% && >=90%), critical (<90%)
  - [x] 4.3 Apply appropriate color tokens (success, warning, warning-dark)
  - [x] 4.4 Ensure NO use of safety-red for production status

- [x] Task 5: Add Data Freshness Indicator (AC: #4)
  - [x] 5.1 Display "Last updated" timestamp in human-readable format
  - [x] 5.2 Add visual warning if data older than 60 seconds
  - [x] 5.3 Implement auto-refresh (polling or real-time subscription)
  - [x] 5.4 Add manual refresh button

- [x] Task 6: Implement Data Fetching and State Management (AC: #5, #7)
  - [x] 6.1 Create React hook or server component for data fetching
  - [x] 6.2 Handle loading state with skeleton/spinner
  - [x] 6.3 Implement empty state component
  - [x] 6.4 Handle error states gracefully

- [x] Task 7: Visual Design and Glanceability (AC: #6)
  - [x] 7.1 Ensure minimum font sizes per Industrial Clarity guidelines
  - [x] 7.2 Use appropriate card spacing for tablet touch targets
  - [x] 7.3 Test contrast ratios for factory floor visibility
  - [x] 7.4 Apply "Live" mode styling (vibrant indicators) per UX design

- [x] Task 8: Optional Asset Filtering (AC: #8)
  - [x] 8.1 Add filter dropdown for asset area
  - [x] 8.2 Add filter tabs/buttons for status
  - [x] 8.3 Implement client-side filtering or server-side query params

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

### Implementation Summary

Implemented a complete Throughput Dashboard feature that displays actual vs target production throughput for all assets. The dashboard includes:

- **Backend API** (`/api/production/throughput`): FastAPI endpoint that queries `live_snapshots` and `assets` tables from Supabase, calculates variance and percentage, determines status (on_target/behind/critical), and returns structured JSON data with filtering support.

- **Frontend Dashboard**: A dedicated page at `/dashboard/production/throughput` with responsive card grid layout, integrated into Command Center navigation via the LivePulseSection.

- **Component Library**: Created 7 production-specific components following Industrial Clarity design system patterns.

- **Real-time Features**: Auto-refresh every 30 seconds, manual refresh button, data freshness indicator with stale data warning.

### Files Created/Modified

**Created:**
- `apps/api/app/api/production.py` - FastAPI production endpoints
- `apps/web/src/app/dashboard/production/throughput/page.tsx` - Dashboard page
- `apps/web/src/components/production/StatusBadge.tsx` - Status indicator component
- `apps/web/src/components/production/DataFreshnessIndicator.tsx` - Freshness display
- `apps/web/src/components/production/ThroughputCard.tsx` - Asset throughput card
- `apps/web/src/components/production/ThroughputGrid.tsx` - Responsive grid container
- `apps/web/src/components/production/EmptyState.tsx` - Empty state display
- `apps/web/src/components/production/FilterBar.tsx` - Filter controls
- `apps/web/src/components/production/ThroughputDashboard.tsx` - Main dashboard client component
- `apps/web/src/components/production/index.ts` - Component exports
- `apps/api/tests/test_production_api.py` - Backend tests (20 tests)
- `apps/web/src/__tests__/throughput-dashboard.test.tsx` - Frontend tests (47 tests)

**Modified:**
- `apps/api/app/main.py` - Added production router
- `apps/web/src/components/dashboard/LivePulseSection.tsx` - Added navigation link

### Key Decisions

1. **Status Naming**: Used "critical" instead of "ahead" for assets below 90% target (matches UX intent - critically behind target)
2. **Status Colors**: Strictly followed Industrial Clarity - green for on_target, amber for behind, amber-dark for critical. NO safety-red used (reserved for safety incidents only)
3. **Auto-Refresh Interval**: 30 seconds to stay within NFR2 (60 second latency requirement)
4. **Server-Side Filtering**: API supports both area and status filters via query parameters
5. **Card Mode**: Used `mode="live"` for all cards to apply vibrant/real-time styling

### Tests Added

**Backend Tests (20 tests):**
- Status calculation logic (5 tests)
- Percentage calculation logic (5 tests)
- Throughput endpoint (5 tests)
- Areas endpoint (3 tests)
- Response schema validation (1 test)
- OpenAPI documentation (1 test)

**Frontend Tests (47 tests):**
- StatusBadge component (6 tests)
- ThroughputCard component (10 tests)
- ThroughputGrid component (4 tests)
- EmptyState component (5 tests)
- DataFreshnessIndicator component (8 tests)
- FilterBar component (8 tests)
- Glanceability/Typography (2 tests)
- Accessibility (4 tests)

### Test Results

```
Backend: 20 passed (0 failed)
Frontend: 47 passed (0 failed)
Total: 67 tests passing
```

### Notes for Reviewer

1. The frontend client component (`ThroughputDashboard.tsx`) handles data fetching via the backend API - requires `NEXT_PUBLIC_API_URL` environment variable to be set for production.

2. The status calculation uses different thresholds than the live_snapshots table's stored status (which uses +/- 5%). The API recalculates status based on AC#3 requirements (>=100% on_target, 90-99% behind, <90% critical).

3. Navigation is integrated via LivePulseSection on Command Center - the OEE Metrics link is shown as a placeholder for Story 2.4.

4. All components use the "live" mode styling from Industrial Clarity design system for consistent real-time data appearance.

### Acceptance Criteria Status

- [x] **AC #1**: Dashboard Route and Navigation - Route at `/dashboard/production/throughput`, linked from Command Center LivePulseSection (`apps/web/src/app/dashboard/production/throughput/page.tsx:1`, `apps/web/src/components/dashboard/LivePulseSection.tsx:37`)
- [x] **AC #2**: Actual vs Target Visualization - ThroughputCard displays name, actual, target, variance, percentage with progress bar (`apps/web/src/components/production/ThroughputCard.tsx:48-125`)
- [x] **AC #3**: Status Indicators - StatusBadge with on_target (green), behind (amber), critical (amber-dark), NO safety-red (`apps/web/src/components/production/StatusBadge.tsx:24-49`)
- [x] **AC #4**: Data Freshness Indicator - Shows timestamp, warns if >60s old, auto-refresh + manual button (`apps/web/src/components/production/DataFreshnessIndicator.tsx:1-117`)
- [x] **AC #5**: Real-time Data Binding - 30-second auto-refresh via useEffect interval (`apps/web/src/components/production/ThroughputDashboard.tsx:65-71`)
- [x] **AC #6**: Responsive Layout - grid-cols-1/md:grid-cols-2/lg:grid-cols-3, text-5xl metrics for glanceability (`apps/web/src/components/production/ThroughputGrid.tsx:23-31`, `apps/web/src/components/production/ThroughputCard.tsx:75`)
- [x] **AC #7**: Empty State Handling - EmptyState component with meaningful message (`apps/web/src/components/production/EmptyState.tsx:1-62`)
- [x] **AC #8**: Asset Filtering - FilterBar with area dropdown and status tabs, server-side query param support (`apps/web/src/components/production/FilterBar.tsx:1-109`, `apps/api/app/api/production.py:87-95`)

### File List

```
apps/api/app/api/production.py
apps/api/app/main.py
apps/api/tests/test_production_api.py
apps/web/src/app/dashboard/production/throughput/page.tsx
apps/web/src/components/production/StatusBadge.tsx
apps/web/src/components/production/DataFreshnessIndicator.tsx
apps/web/src/components/production/ThroughputCard.tsx
apps/web/src/components/production/ThroughputGrid.tsx
apps/web/src/components/production/EmptyState.tsx
apps/web/src/components/production/FilterBar.tsx
apps/web/src/components/production/ThroughputDashboard.tsx
apps/web/src/components/production/index.ts
apps/web/src/components/dashboard/LivePulseSection.tsx
apps/web/src/__tests__/throughput-dashboard.test.tsx
```

## Code Review Record

**Reviewer**: Code Review Agent
**Date**: 2026-01-06

### Issues Found

| # | Description | Severity | Status |
|---|-------------|----------|--------|
| 1 | Unused imports in production.py: `Decimal`, `ROUND_HALF_UP`, `timedelta`, `UUID` imported but never used | HIGH | Fixed |
| 2 | Dead code in production.py: Unused SQL query string `latest_snapshots_query` defined but never executed (lines 157-171) | MEDIUM | Fixed |
| 3 | React Hook dependency warning in ThroughputDashboard.tsx: `useEffect` at line 138-142 had missing dependencies and was redundant | MEDIUM | Fixed |
| 4 | Minor: Some SVGs use `aria-hidden` but already have descriptive content | LOW | Not Fixed |

**Totals**: 1 HIGH, 2 MEDIUM, 1 LOW

### Fixes Applied

1. **Removed unused imports** in `apps/api/app/api/production.py` (lines 11-15):
   - Removed: `timedelta`, `Decimal`, `ROUND_HALF_UP`, `UUID`
   - Kept: `datetime`, `List`, `Optional`

2. **Removed dead SQL query code** in `apps/api/app/api/production.py`:
   - Removed unused `latest_snapshots_query` variable and associated comments
   - Simplified code by removing the obsolete raw SQL that was never used

3. **Fixed React Hook dependency issue** in `apps/web/src/components/production/ThroughputDashboard.tsx`:
   - Removed redundant `useEffect` for filter changes (lines 137-142)
   - The initial data fetch effect already triggers when `fetchThroughputData` changes
   - Since `fetchThroughputData` has `selectedArea` and `selectedStatus` in its dependency array, filter changes are already handled

### Remaining Issues

| # | Description | Severity | Notes |
|---|-------------|----------|-------|
| 4 | Some SVGs use `aria-hidden="true"` | LOW | Acceptable pattern, no functional impact |

### Acceptance Criteria Verification

All 8 acceptance criteria have been verified as implemented and tested:

- [x] **AC #1**: Dashboard route at `/dashboard/production/throughput`, accessible from Command Center
- [x] **AC #2**: Actual vs Target visualization with name, actual, target, variance, percentage
- [x] **AC #3**: Status indicators (on_target=green, behind=amber, critical=amber-dark) - NO safety-red used
- [x] **AC #4**: Data freshness indicator with timestamp, stale warning (>60s), auto-refresh + manual button
- [x] **AC #5**: Real-time data binding with 30-second auto-refresh
- [x] **AC #6**: Responsive layout (1/2/3 columns for mobile/tablet/desktop), text-5xl for glanceability
- [x] **AC #7**: Empty state handling with meaningful message
- [x] **AC #8**: Asset filtering by area and status

### Test Results

- Backend: 20 tests passed
- Frontend: 47 tests passed
- Build: Compiles successfully with no warnings

### Final Status

**Approved with fixes** - All HIGH and MEDIUM severity issues have been resolved. The implementation meets all acceptance criteria and follows the established patterns.
