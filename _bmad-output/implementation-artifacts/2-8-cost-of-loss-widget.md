# Story 2.8: Cost of Loss Widget

Status: ready-for-dev

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

- [ ] Task 1: Create API endpoint for Cost of Loss data (AC: #2, #7)
  - [ ] 1.1 Create `/api/v1/financial/cost-of-loss` endpoint in `apps/api/app/api/endpoints/`
  - [ ] 1.2 Implement query logic to aggregate from `daily_summaries` for period=daily
  - [ ] 1.3 Implement query logic to aggregate from `live_snapshots` for period=live
  - [ ] 1.4 Add optional `asset_id` filter parameter for context-specific queries
  - [ ] 1.5 Return structured response with total_loss, breakdown, and last_updated

- [ ] Task 2: Create CostOfLossWidget React component (AC: #1, #5)
  - [ ] 2.1 Create `apps/web/src/components/financial/CostOfLossWidget.tsx`
  - [ ] 2.2 Use Shadcn/UI Card component as container
  - [ ] 2.3 Display total financial loss with large, bold typography
  - [ ] 2.4 Add breakdown section showing Downtime, Waste, OEE loss categories
  - [ ] 2.5 Format currency values with USD formatting ($X,XXX.XX)
  - [ ] 2.6 Apply Industrial Clarity design tokens (high contrast, no Safety Red)

- [ ] Task 3: Implement data fetching and state management (AC: #2, #6)
  - [ ] 3.1 Create custom hook `useCostOfLoss` for API data fetching
  - [ ] 3.2 Implement loading state with skeleton or spinner
  - [ ] 3.3 Implement error state with user-friendly message
  - [ ] 3.4 Add automatic refresh interval for Live Pulse mode (15 min alignment)
  - [ ] 3.5 Display last_updated timestamp in widget footer

- [ ] Task 4: Integrate widget into Command Center (AC: #3)
  - [ ] 4.1 Import CostOfLossWidget into Command Center dashboard page
  - [ ] 4.2 Replace FinancialWidgetsSection placeholder with actual widget
  - [ ] 4.3 Verify responsive layout on mobile, tablet, and desktop viewports
  - [ ] 4.4 Ensure widget is visible above fold on tablet

- [ ] Task 5: Integrate widget into Production views (AC: #4)
  - [ ] 5.1 Add CostOfLossWidget to Throughput Dashboard page (Story 2.3)
  - [ ] 5.2 Add CostOfLossWidget to Downtime Pareto Analysis page (Story 2.5)
  - [ ] 5.3 Pass appropriate context/filters based on current view

- [ ] Task 6: Testing and verification (AC: #1-7)
  - [ ] 6.1 Verify API endpoint returns correct data structure
  - [ ] 6.2 Test widget rendering with mock data
  - [ ] 6.3 Verify Industrial Clarity compliance (contrast, typography, no Safety Red)
  - [ ] 6.4 Test responsive behavior across viewports
  - [ ] 6.5 Test automatic refresh in Live Pulse mode
  - [ ] 6.6 Test error handling when API is unavailable

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

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
