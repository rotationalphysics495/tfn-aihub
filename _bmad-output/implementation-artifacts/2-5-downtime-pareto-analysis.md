# Story 2.5: Downtime Pareto Analysis

Status: ready-for-dev

## Story

As a **Plant Manager**,
I want **granular downtime breakdown and pareto charts organized by reason code**,
so that **I can quickly identify the top causes of production loss and prioritize corrective actions based on data-driven insights**.

## Acceptance Criteria

1. **Downtime Data Retrieval**
   - API endpoint exists to fetch downtime events from the analytical cache (daily_summaries, live_snapshots)
   - Downtime data includes: asset_id, reason_code, duration_minutes, event_timestamp, financial_impact
   - Data supports both T-1 (yesterday) and T-15m (live) time windows
   - Query performance meets NFR2 (<60 seconds latency)

2. **Pareto Analysis Calculation**
   - Backend service calculates Pareto distribution of downtime by reason code
   - Calculation includes: total downtime per reason code, percentage of total, cumulative percentage
   - Supports filtering by: date range, asset, area, and shift
   - Results are sorted by descending downtime duration (highest first)

3. **Pareto Chart Visualization**
   - Frontend displays Pareto chart with:
     - Bar chart showing downtime duration per reason code (descending order)
     - Line chart overlay showing cumulative percentage (0-100%)
     - 80% threshold line indicator (Pareto principle visual)
   - Chart is responsive and works on tablet (primary) and desktop
   - Follows "Industrial Clarity" design: high-contrast, readable at 3 feet

4. **Granular Breakdown Table**
   - Detailed data table showing all downtime events
   - Columns: Asset, Reason Code, Duration, Start Time, End Time, Financial Impact ($)
   - Supports sorting by any column
   - Supports pagination for large datasets
   - Row click navigates to Asset Detail View (future story)

5. **Financial Impact Integration**
   - Each reason code shows associated financial loss in dollars
   - Financial calculation uses cost_centers.standard_hourly_rate from Plant Object Model
   - Total financial impact displayed prominently per FR5 requirements
   - "Cost of Loss" summary widget above the Pareto chart

6. **Safety Reason Code Highlighting**
   - "Safety Issue" reason codes displayed with "Safety Red" visual treatment
   - Safety-related downtime events appear first or are visually prominent
   - Clicking safety entries shows full safety event details
   - Complies with FR4 (Safety Alerting) requirements

7. **Time Window Toggle**
   - User can toggle between "Yesterday" (T-1) and "Live" (T-15m) views
   - Clear visual distinction between Retrospective (cool colors) and Live (vibrant) modes per UX spec
   - Live view auto-refreshes at 15-minute intervals (when user on page)

## Tasks / Subtasks

- [ ] Task 1: Create Downtime API Endpoint (AC: #1)
  - [ ] 1.1 Create FastAPI endpoint `GET /api/v1/downtime/events` in `apps/api/app/api/downtime.py`
  - [ ] 1.2 Add query parameters: start_date, end_date, asset_id (optional), area (optional)
  - [ ] 1.3 Implement database query joining daily_summaries/live_snapshots with assets
  - [ ] 1.4 Add pagination support (limit, offset)
  - [ ] 1.5 Include response model with downtime event schema

- [ ] Task 2: Create Pareto Analysis Service (AC: #2)
  - [ ] 2.1 Create service class `DowntimeAnalysisService` in `apps/api/app/services/downtime_analysis.py`
  - [ ] 2.2 Implement `calculate_pareto(events, group_by='reason_code')` method
  - [ ] 2.3 Calculate: total_minutes, percentage, cumulative_percentage per reason code
  - [ ] 2.4 Add filtering logic for asset, area, shift parameters
  - [ ] 2.5 Create API endpoint `GET /api/v1/downtime/pareto` returning Pareto data

- [ ] Task 3: Integrate Financial Impact Calculation (AC: #5)
  - [ ] 3.1 Join cost_centers table to get standard_hourly_rate for each asset
  - [ ] 3.2 Calculate financial_impact = (downtime_minutes / 60) * standard_hourly_rate
  - [ ] 3.3 Aggregate total financial impact per reason code
  - [ ] 3.4 Include financial data in Pareto API response

- [ ] Task 4: Build Pareto Chart Component (AC: #3, #7)
  - [ ] 4.1 Create `ParetoChart.tsx` component in `apps/web/src/components/downtime/`
  - [ ] 4.2 Use charting library (recharts or chart.js) for combined bar+line chart
  - [ ] 4.3 Implement 80% threshold line indicator
  - [ ] 4.4 Add responsive design for tablet/desktop
  - [ ] 4.5 Apply Industrial Clarity styling (high-contrast colors from design system)
  - [ ] 4.6 Add toggle for T-1 vs Live view with distinct visual treatment

- [ ] Task 5: Build Downtime Breakdown Table (AC: #4)
  - [ ] 5.1 Create `DowntimeTable.tsx` component in `apps/web/src/components/downtime/`
  - [ ] 5.2 Use Shadcn/UI Table component for consistent styling
  - [ ] 5.3 Implement column sorting functionality
  - [ ] 5.4 Add pagination controls
  - [ ] 5.5 Format financial values as currency ($X,XXX.XX)
  - [ ] 5.6 Add row click handler (prepare for future Asset Detail navigation)

- [ ] Task 6: Implement Safety Highlighting (AC: #6)
  - [ ] 6.1 Add safety detection logic: check if reason_code contains "Safety" or matches safety patterns
  - [ ] 6.2 Apply "Safety Red" styling to safety-related rows and chart bars
  - [ ] 6.3 Sort/prioritize safety events to top of list when applicable
  - [ ] 6.4 Create safety event detail modal/panel

- [ ] Task 7: Create Downtime Analysis Page (AC: #3, #4, #5, #7)
  - [ ] 7.1 Create page at `apps/web/src/app/production/downtime/page.tsx`
  - [ ] 7.2 Add "Cost of Loss" summary widget at top
  - [ ] 7.3 Layout Pareto chart and breakdown table
  - [ ] 7.4 Implement time window toggle (Yesterday/Live)
  - [ ] 7.5 Add filter controls (asset, area, date range)
  - [ ] 7.6 Implement auto-refresh for Live view (15-minute interval)
  - [ ] 7.7 Add loading and error states

- [ ] Task 8: Navigation Integration
  - [ ] 8.1 Add "Downtime Analysis" to Production Intelligence section in navigation
  - [ ] 8.2 Link from Command Center placeholder (if exists)
  - [ ] 8.3 Ensure proper route protection (authenticated users only)

## Dev Notes

### Architecture Patterns

- **Backend:** Python FastAPI in `apps/api/` following existing patterns
- **Frontend:** Next.js 14+ with App Router in `apps/web/`
- **API Communication:** REST endpoints with Supabase JWT authentication
- **Charting:** Recommend `recharts` (React-native) or `chart.js` with react-chartjs-2 wrapper
- **State Management:** React Query (TanStack Query) for data fetching and caching

### Technical Requirements

**From Architecture Document:**
- Data flows from MSSQL (read-only per NFR3) through Pipeline B (Live Pulse) into `live_snapshots` and `safety_events` tables
- Financial calculations use `cost_centers.standard_hourly_rate` joined with assets
- Supabase PostgreSQL for analytical cache queries
- FastAPI endpoints protected via Supabase Auth JWT validation

**Performance Requirements (NFR2):**
- All "Live" views must reflect data within 60 seconds of ingestion
- Index usage critical for date range and asset_id queries
- Consider caching Pareto calculations for frequently-accessed date ranges

### Database Schema Reference

**Tables Used:**
- `daily_summaries` - T-1 aggregated data (from Story 1.4)
- `live_snapshots` - T-15m polling data (from Story 1.4)
- `safety_events` - Safety incident log (from Story 1.4)
- `assets` - Asset information (from Story 1.3)
- `cost_centers` - Financial rates (from Story 1.3)

**Key Columns for Pareto:**
```sql
-- From daily_summaries
SELECT
  ds.asset_id,
  ds.report_date,
  ds.downtime_minutes,
  ds.financial_loss_dollars,
  a.name as asset_name,
  a.area
FROM daily_summaries ds
JOIN assets a ON ds.asset_id = a.id
WHERE ds.report_date BETWEEN :start_date AND :end_date
```

### UX Design Compliance

| Principle | Implementation |
|-----------|----------------|
| Industrial High-Contrast | Use design tokens from Story 1.6 theme; ensure chart colors pass contrast requirements |
| Glanceability | Pareto chart readable at 3 feet; large axis labels, prominent bars |
| Safety Red Reserved | ONLY use red for "Safety Issue" reason codes, never for general downtime |
| Visual Context Switching | Cool colors for T-1 (retrospective), vibrant/pulsing for Live view |
| Trust & Transparency | Each bar/row links to underlying data evidence |

### Pareto Chart Technical Spec

```typescript
interface ParetoData {
  reason_code: string;
  total_minutes: number;
  percentage: number;
  cumulative_percentage: number;
  financial_impact: number;
  is_safety_related: boolean;
  event_count: number;
}

// Pareto principle: top ~20% of causes account for ~80% of effects
// Display 80% threshold line on cumulative percentage axis
```

### Dependencies

**Requires (must be completed):**
- Story 1.3: Plant Object Model Schema (assets, cost_centers tables)
- Story 1.4: Analytical Cache Schema (daily_summaries, live_snapshots, safety_events)
- Story 1.5: MSSQL Read-Only Connection (for Pipeline B data source)
- Story 1.6: Industrial Clarity Design System (styling tokens)
- Story 2.1: Batch Data Pipeline (populates daily_summaries)
- Story 2.2: Polling Data Pipeline (populates live_snapshots)

**Enables (future stories):**
- Story 2.6: Safety Alert System (uses safety event highlighting from this story)
- Story 2.7: Financial Impact Calculator (expands on financial logic established here)
- Epic 3: Action Engine (consumes downtime data for prioritization)

### Project Structure Notes

```
apps/
  api/
    app/
      api/
        downtime.py           # New: Downtime API endpoints
      services/
        downtime_analysis.py  # New: Pareto calculation service
      models/
        downtime.py           # New: Pydantic models for downtime data
  web/
    src/
      app/
        production/
          downtime/
            page.tsx          # New: Downtime Analysis page
      components/
        downtime/
          ParetoChart.tsx     # New: Pareto visualization
          DowntimeTable.tsx   # New: Granular breakdown table
          CostOfLossWidget.tsx  # New: Financial summary widget
          TimeWindowToggle.tsx  # New: T-1 vs Live toggle
```

### Testing Requirements

**Backend Tests:**
1. API endpoint returns correct downtime events with filters
2. Pareto calculation produces accurate percentages
3. Cumulative percentage reaches 100% for full dataset
4. Financial impact calculation matches expected formula
5. Safety events correctly identified and flagged
6. Query performance under NFR2 threshold (benchmark test)

**Frontend Tests:**
1. Pareto chart renders with correct data mapping
2. Table sorting works for all columns
3. Pagination controls function correctly
4. Time window toggle switches data source
5. Safety highlighting applied to correct rows/bars
6. Responsive layout works on tablet viewport
7. Auto-refresh triggers at 15-minute intervals in Live mode

### Error Handling

- Handle empty datasets gracefully (show "No downtime events" message)
- Display error states if API fails (retry button, helpful message)
- Handle missing cost_center data (use default rate or show "N/A" for financial impact)
- Log and surface safety event detection failures prominently

### References

- [Source: _bmad/bmm/data/architecture.md#5. Data Models & Plant Object Model]
- [Source: _bmad/bmm/data/architecture.md#6. Data Pipelines]
- [Source: _bmad/bmm/data/prd.md#FR1 (Data Ingestion)]
- [Source: _bmad/bmm/data/prd.md#FR4 (Safety Alerting)]
- [Source: _bmad/bmm/data/prd.md#FR5 (Financial Context)]
- [Source: _bmad/bmm/data/prd.md#NFR2 (Latency)]
- [Source: _bmad/bmm/data/prd.md#NFR3 (Read-Only)]
- [Source: _bmad/bmm/data/ux-design.md#2. Overall UX Goals]
- [Source: _bmad/bmm/data/ux-design.md#3. Information Architecture - Downtime Analysis]
- [Source: _bmad-output/planning-artifacts/epic-2.md#Story 2.5]
- [Source: _bmad-output/implementation-artifacts/1-4-analytical-cache-schema.md] - Database schema foundation

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
