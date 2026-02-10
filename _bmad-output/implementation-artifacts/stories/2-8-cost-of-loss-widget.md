# Story 2.8: Cost of Loss Widget

Status: Done

## Story

As a Plant Manager,
I want a financial loss display widget integrated into production views,
so that I can immediately see the dollar impact of downtime and waste without navigating away from operational dashboards.

## Acceptance Criteria

1. **Cost of Loss Widget Component**
   - Widget displays total financial loss for the current view period (T-1 for Morning Report, rolling for Live Pulse)
   - Shows breakdown by loss category: Downtime Cost, Waste/Scrap Cost, OEE Loss Cost
   - Displays values in USD currency format with appropriate precision ($X,XXX.XX)
   - Widget has a clear title/heading indicating "Cost of Loss" or "Financial Impact"

2. **Data Integration with Financial Impact Calculator**
   - Widget consumes data from the Financial Impact Calculator service (Story 2.7)
   - Retrieves financial loss values from `daily_summaries` table for T-1 views
   - Retrieves financial loss values from `live_snapshots` table for Live Pulse views
   - Correctly aggregates cost_centers data linked to affected assets

3. **Integration into Command Center Dashboard**
   - Widget renders in the Financial Widgets section of Command Center (placeholder from Story 1.7)
   - Replaces the "Financial Intelligence - Coming in Epic 2" placeholder
   - Widget is visible without scrolling on tablet viewport (above the fold)
   - Maintains responsive behavior: stacks vertically on mobile, grid placement on tablet/desktop

4. **Integration into Production Views**
   - Widget appears on Throughput Dashboard (Story 2.3) page
   - Widget appears on Downtime Pareto Analysis (Story 2.5) page
   - Widget displays context-appropriate data based on current view/filters

5. **Industrial Clarity Design Compliance**
   - Uses Tailwind CSS + Shadcn/UI components from design system (Story 1.6)
   - High-contrast styling for factory floor visibility
   - Financial values use large, bold typography for "glanceability" (readable from 3 feet)
   - Loss values displayed in "neutral" or "warning" colors (NOT Safety Red - reserved for safety incidents)
   - Clear visual hierarchy: total loss prominent, category breakdown secondary

6. **Real-Time Update Support**
   - Widget supports automatic refresh when Live Pulse data updates (every 15 minutes)
   - Shows loading state during data fetch
   - Displays timestamp of last data update
   - Handles error states gracefully with user-friendly message

7. **API Endpoint for Widget Data**
   - GET `/api/v1/financial/cost-of-loss` endpoint returns aggregated widget data
   - Endpoint accepts query parameters: `period` (daily, live), `asset_id` (optional filter)
   - Response includes: total_loss, downtime_cost, waste_cost, oee_loss_cost, last_updated timestamp
   - Endpoint observes NFR3 (Read-Only MSSQL) - reads from Supabase cache only

## Tasks / Subtasks

- [x] Task 1: Create API endpoint for Cost of Loss data (AC: #2, #7)
  - [x] 1.1 Create `/api/v1/financial/cost-of-loss` endpoint in `apps/api/app/api/endpoints/`
  - [x] 1.2 Implement query logic to aggregate from `daily_summaries` for period=daily
  - [x] 1.3 Implement query logic to aggregate from `live_snapshots` for period=live
  - [x] 1.4 Add optional `asset_id` filter parameter for context-specific queries
  - [x] 1.5 Return structured response with total_loss, breakdown, and last_updated

- [x] Task 2: Create CostOfLossWidget React component (AC: #1, #5)
  - [x] 2.1 Create `apps/web/src/components/financial/CostOfLossWidget.tsx`
  - [x] 2.2 Use Shadcn/UI Card component as container
  - [x] 2.3 Display total financial loss with large, bold typography
  - [x] 2.4 Add breakdown section showing Downtime, Waste, OEE loss categories
  - [x] 2.5 Format currency values with USD formatting ($X,XXX.XX)
  - [x] 2.6 Apply Industrial Clarity design tokens (high contrast, no Safety Red)

- [x] Task 3: Implement data fetching and state management (AC: #2, #6)
  - [x] 3.1 Create custom hook `useCostOfLoss` for API data fetching
  - [x] 3.2 Implement loading state with skeleton or spinner
  - [x] 3.3 Implement error state with user-friendly message
  - [x] 3.4 Add automatic refresh interval for Live Pulse mode (15 min alignment)
  - [x] 3.5 Display last_updated timestamp in widget footer

- [x] Task 4: Integrate widget into Command Center (AC: #3)
  - [x] 4.1 Import CostOfLossWidget into Command Center dashboard page
  - [x] 4.2 Replace FinancialWidgetsSection placeholder with actual widget
  - [x] 4.3 Verify responsive layout on mobile, tablet, and desktop viewports
  - [x] 4.4 Ensure widget is visible above fold on tablet

- [x] Task 5: Integrate widget into Production views (AC: #4)
  - [x] 5.1 Add CostOfLossWidget to Throughput Dashboard page (Story 2.3)
  - [x] 5.2 Add CostOfLossWidget to Downtime Pareto Analysis page (Story 2.5)
  - [x] 5.3 Pass appropriate context/filters based on current view

- [x] Task 6: Testing and verification (AC: #1-7)
  - [x] 6.1 Verify API endpoint returns correct data structure
  - [x] 6.2 Test widget rendering with mock data
  - [x] 6.3 Verify Industrial Clarity compliance (contrast, typography, no Safety Red)
  - [x] 6.4 Test responsive behavior across viewports
  - [x] 6.5 Test automatic refresh in Live Pulse mode
  - [x] 6.6 Test error handling when API is unavailable

## Dev Notes

### Architecture Patterns

- **Frontend Framework:** Next.js 14+ with App Router (React Server Components where appropriate)
- **Backend Framework:** Python FastAPI for API endpoints
- **File Locations:**
  - Frontend component: `apps/web/src/components/financial/CostOfLossWidget.tsx`
  - Frontend hook: `apps/web/src/hooks/useCostOfLoss.ts`
  - API endpoint: `apps/api/app/api/endpoints/financial.py`
- **Styling:** Tailwind CSS with Shadcn/UI components
- **Data Source:** Reads from Supabase PostgreSQL (NOT directly from MSSQL per NFR3)

### Technical Requirements

| Requirement | Implementation |
|-------------|----------------|
| NFR2 (Latency) | Widget refreshes with Live Pulse cycle (60 second data freshness) |
| NFR3 (Read-Only) | API reads from Supabase cache tables, never queries MSSQL directly |
| FR5 (Financial Context) | Displays translated financial values from cost_centers data |

### Data Schema Dependencies

**From `daily_summaries` table:**
- `financial_loss_total`: Decimal - Total calculated loss
- `downtime_cost`: Decimal - Loss from downtime events
- `waste_cost`: Decimal - Loss from quality/scrap issues
- `oee_loss_cost`: Decimal - Loss from OEE below target
- `created_at`: Timestamp - For last_updated display

**From `live_snapshots` table:**
- Same financial fields as daily_summaries for live/rolling view

**From `cost_centers` table (referenced):**
- `standard_hourly_rate`: Decimal - Used in Financial Impact Calculator (Story 2.7)

### API Response Schema

```json
{
  "total_loss": 12500.00,
  "breakdown": {
    "downtime_cost": 7500.00,
    "waste_cost": 3200.00,
    "oee_loss_cost": 1800.00
  },
  "period": "daily",
  "last_updated": "2026-01-05T06:15:00Z"
}
```

### UX Design Compliance

| Principle | Implementation |
|-----------|----------------|
| Glanceability | Total loss displayed in 24px+ bold font, readable from 3 feet |
| Industrial High-Contrast | Use design tokens from Story 1.6, amber/yellow for warnings (NOT red) |
| Trust & Transparency | Display last_updated timestamp, link to detailed breakdown if clicked |
| Action First | Widget supports the Action List by quantifying loss impact |

### Component Props Interface

```typescript
interface CostOfLossWidgetProps {
  period: 'daily' | 'live';
  assetId?: string;  // Optional filter for specific asset context
  showBreakdown?: boolean;  // Default true
  autoRefresh?: boolean;  // Default true for 'live' period
  className?: string;  // For layout customization
}
```

### Dependencies

- **Requires:** Story 2.7 (Financial Impact Calculator) - provides calculation logic
- **Requires:** Story 1.6 (Industrial Clarity Design System) - provides design tokens
- **Requires:** Story 1.7 (Command Center UI Shell) - provides integration point
- **Requires:** Story 2.3 (Throughput Dashboard) - provides integration point
- **Requires:** Story 2.5 (Downtime Pareto Analysis) - provides integration point
- **Enables:** Story 2.9 (Live Pulse Ticker) - will consume financial context from same data

### Project Structure Notes

```
apps/web/src/
  components/
    financial/
      CostOfLossWidget.tsx      # Main widget component
      CostOfLossBreakdown.tsx   # Optional: breakdown sub-component
    ui/                         # Shadcn/UI components (from Story 1.6)
  hooks/
    useCostOfLoss.ts            # Data fetching hook
  app/
    dashboard/
      page.tsx                  # Command Center (integration point)

apps/api/app/
  api/
    endpoints/
      financial.py              # Financial endpoints including cost-of-loss
  services/
    financial_service.py        # Business logic (from Story 2.7)
```

### Testing Guidance

- Unit tests for API endpoint with mock database responses
- Unit tests for CostOfLossWidget component with mock API responses
- Integration test verifying widget renders on Command Center
- Visual regression test for Industrial Clarity compliance
- Test currency formatting for various value ranges (hundreds, thousands, millions)

### References

- [Source: _bmad/bmm/data/architecture.md#5. Data Models & Plant Object Model] - cost_centers schema
- [Source: _bmad/bmm/data/architecture.md#6. Data Pipelines] - daily_summaries, live_snapshots
- [Source: _bmad/bmm/data/prd.md#FR5] - Financial Context requirement
- [Source: _bmad/bmm/data/ux-design.md#2. Overall UX Goals] - Glanceability, Industrial High-Contrast
- [Source: _bmad/bmm/data/ux-design.md#3. Information Architecture] - Financial Impact section
- [Source: _bmad-output/planning-artifacts/epic-2.md] - Epic 2 context, Story 2.8 definition
- [Source: _bmad-output/planning-artifacts/epics.md#NFRs] - NFR2 Latency, NFR3 Read-Only

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - No blocking issues encountered during implementation.

### Implementation Summary

Implemented the Cost of Loss Widget story by creating:
1. A new API endpoint `/api/financial/cost-of-loss` that aggregates financial loss data from daily_summaries (T-1) and live_snapshots (rolling)
2. A new React component `CostOfLossWidget` in the financial components directory with Industrial Clarity design compliance
3. A custom hook `useCostOfLoss` for data fetching with auto-refresh support
4. Integrated the widget into Command Center, Throughput Dashboard, and Downtime Pareto Analysis pages

### Files Created/Modified

**Created:**
- `apps/api/app/api/financial.py` - Added `/cost-of-loss` endpoint with CostOfLossResponse and CostOfLossBreakdown schemas
- `apps/web/src/components/financial/CostOfLossWidget.tsx` - Main widget component with loading, error, and empty states
- `apps/web/src/components/financial/index.ts` - Component exports
- `apps/web/src/hooks/useCostOfLoss.ts` - Custom hook for API data fetching with auto-refresh
- `apps/web/src/components/financial/__tests__/CostOfLossWidget.test.tsx` - 20 unit tests
- `apps/api/tests/test_financial_api.py` - Added 6 tests for cost-of-loss endpoint

**Modified:**
- `apps/web/src/components/dashboard/FinancialWidgetsSection.tsx` - Replaced placeholder with actual widget
- `apps/web/src/components/production/ThroughputDashboard.tsx` - Added widget integration for live data
- `apps/web/src/components/downtime/DowntimeDashboard.tsx` - Added widget integration alongside existing summary widget

### Key Decisions

1. **API Placement**: Added endpoint to existing `financial.py` router rather than creating new file since it extends the Financial Impact Calculator (Story 2.7)
2. **OEE Loss Calculation**: Implemented as `(100 - OEE%) / 100 * hourly_rate * 8 hours * 0.25` to approximate opportunity cost from efficiency gaps
3. **Widget Integration Approach**: Used existing FinancialWidgetsSection for Command Center, added directly to dashboard components for production views
4. **Dual Widget Display on Downtime Page**: Added new financial breakdown widget alongside existing downtime summary widget in a grid layout for comprehensive view

### Tests Added

**Backend (pytest):**
- `test_cost_of_loss_requires_auth` - Auth verification
- `test_cost_of_loss_returns_correct_structure` - Response schema validation
- `test_cost_of_loss_with_period_daily` - T-1 data query
- `test_cost_of_loss_with_period_live` - Rolling data query
- `test_cost_of_loss_with_asset_filter` - Asset filtering
- `test_cost_of_loss_calculates_breakdown` - Breakdown calculation

**Frontend (vitest):**
- 20 tests covering: display, currency formatting, breakdown visibility, design compliance, loading/error/empty states, auto-refresh indicator

### Test Results

```
Backend: 6 passed (TestCostOfLossEndpoint)
Frontend: 20 passed (CostOfLossWidget.test.tsx)
```

### Notes for Reviewer

1. The widget uses `text-warning-amber` for financial values per AC#5 (NOT Safety Red)
2. Total loss uses large 4xl typography for glanceability (readable from 3 feet)
3. Auto-refresh is enabled only for `period='live'` at 15-minute intervals
4. The Downtime Pareto page now shows both the original summary widget and the new breakdown widget in a side-by-side grid

### Acceptance Criteria Status

| AC | Status | File Reference |
|----|--------|----------------|
| #1 - Cost of Loss Widget Component | PASS | `apps/web/src/components/financial/CostOfLossWidget.tsx:1-280` |
| #2 - Data Integration with Financial Impact Calculator | PASS | `apps/api/app/api/financial.py:379-552` |
| #3 - Integration into Command Center Dashboard | PASS | `apps/web/src/components/dashboard/FinancialWidgetsSection.tsx:1-39` |
| #4 - Integration into Production Views | PASS | `apps/web/src/components/production/ThroughputDashboard.tsx:243-252`, `apps/web/src/components/downtime/DowntimeDashboard.tsx:338-357` |
| #5 - Industrial Clarity Design Compliance | PASS | `apps/web/src/components/financial/CostOfLossWidget.tsx:200-240` |
| #6 - Real-Time Update Support | PASS | `apps/web/src/hooks/useCostOfLoss.ts:1-138` |
| #7 - API Endpoint for Widget Data | PASS | `apps/api/app/api/financial.py:401-551` |

### File List

- `apps/api/app/api/financial.py`
- `apps/api/tests/test_financial_api.py`
- `apps/web/src/components/financial/CostOfLossWidget.tsx`
- `apps/web/src/components/financial/index.ts`
- `apps/web/src/components/financial/__tests__/CostOfLossWidget.test.tsx`
- `apps/web/src/hooks/useCostOfLoss.ts`
- `apps/web/src/components/dashboard/FinancialWidgetsSection.tsx`
- `apps/web/src/components/production/ThroughputDashboard.tsx`
- `apps/web/src/components/downtime/DowntimeDashboard.tsx`
- `_bmad-output/implementation-artifacts/2-8-cost-of-loss-widget.md`

## Code Review Record

**Reviewer**: Code Review Agent
**Date**: 2026-01-06 12:40

### Issues Found

| # | Description | Severity | Status |
|---|-------------|----------|--------|
| 1 | Missing accessibility heading ID - `aria-labelledby="financial-widgets-heading"` in FinancialWidgetsSection references non-existent element | MEDIUM | Not Fixed (per policy) |
| 2 | No input validation for `period` parameter in API - accepts any string value silently | MEDIUM | Not Fixed (per policy) |
| 3 | Unused `settings` variable in `get_cost_of_loss` function (line 439) | LOW | Not Fixed (per policy) |
| 4 | Widget's ErrorState has `onRetry` prop but widget doesn't expose retry functionality | LOW | Not Fixed (per policy) |

**Totals**: 0 HIGH, 2 MEDIUM, 2 LOW (4 Total)

### Fixes Applied

None required per policy (no HIGH issues, and TOTAL <= 5).

### Remaining Issues

**MEDIUM severity (future cleanup):**
1. Add `<h2 id="financial-widgets-heading" className="sr-only">Financial Intelligence</h2>` to FinancialWidgetsSection for accessibility compliance
2. Add period validation in API: `if period not in ('daily', 'live'): raise HTTPException(status_code=400, detail="period must be 'daily' or 'live'")`

**LOW severity (future cleanup):**
3. Remove unused `settings = get_settings()` in `get_cost_of_loss` function
4. Add `onRetry` prop to CostOfLossWidget and wire it to the hook's `refetch` function

### Final Status

**Approved** - All acceptance criteria are met with comprehensive tests (26 total - 6 backend, 20 frontend). Implementation follows existing patterns, uses proper design tokens, and integrates correctly with Command Center and Production views. No HIGH severity issues found. MEDIUM and LOW issues are minor improvements that don't affect functionality.
