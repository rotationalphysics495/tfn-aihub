# Story 2.4: OEE Metrics View

Status: ready-for-dev

## Story

As a **Plant Manager**,
I want **to view Overall Equipment Effectiveness (OEE) metrics calculated from ingested production data**,
so that **I can quickly assess equipment performance and identify opportunities for improvement**.

## Acceptance Criteria

1. OEE calculation displays three core components: Availability, Performance, and Quality
2. OEE metrics are computed from data in `daily_summaries` (T-1) and `live_snapshots` (T-15m) tables
3. Plant-wide OEE percentage is prominently displayed with a gauge or large numeric indicator
4. Individual asset OEE breakdown is available showing each component's contribution
5. OEE values update within 60 seconds of new data ingestion (NFR2 compliance)
6. Visual indicators distinguish between "Yesterday's Analysis" (T-1) and "Live Pulse" (T-15m) OEE
7. OEE targets from `shift_targets` table are shown alongside actual values for comparison
8. Color-coded status indicators: Green (>=85%), Yellow (70-84%), Red (<70%) for OEE thresholds
9. OEE view follows "Industrial Clarity" design - readable from 3 feet on tablet
10. API endpoint returns OEE data with proper error handling and data validation

## Tasks / Subtasks

- [ ] Task 1: Create OEE calculation service in FastAPI backend (AC: #2, #10)
  - [ ] 1.1 Create `app/services/oee_calculator.py` with OEE calculation logic
  - [ ] 1.2 Implement Availability calculation: (Run Time / Planned Production Time) x 100
  - [ ] 1.3 Implement Performance calculation: (Actual Output / Ideal Output) x 100
  - [ ] 1.4 Implement Quality calculation: (Good Units / Total Units) x 100
  - [ ] 1.5 Implement Overall OEE: (Availability x Performance x Quality) / 10000
  - [ ] 1.6 Add data validation and error handling for null/zero values

- [ ] Task 2: Create OEE API endpoints (AC: #2, #5, #10)
  - [ ] 2.1 Create `app/api/oee.py` router
  - [ ] 2.2 Implement `GET /api/oee/plant` - Plant-wide OEE summary
  - [ ] 2.3 Implement `GET /api/oee/assets` - Per-asset OEE breakdown
  - [ ] 2.4 Implement `GET /api/oee/assets/{asset_id}` - Single asset OEE detail
  - [ ] 2.5 Add query params for time range selection (yesterday/live)
  - [ ] 2.6 Include target comparison data from `shift_targets`

- [ ] Task 3: Create OEE dashboard components in Next.js (AC: #1, #3, #4, #8, #9)
  - [ ] 3.1 Create `src/components/oee/OEEGauge.tsx` - Large gauge/numeric display
  - [ ] 3.2 Create `src/components/oee/OEEBreakdown.tsx` - Three-component visualization
  - [ ] 3.3 Create `src/components/oee/AssetOEEList.tsx` - Per-asset OEE table/cards
  - [ ] 3.4 Create `src/components/oee/OEEStatusBadge.tsx` - Color-coded status indicator
  - [ ] 3.5 Apply "Industrial Clarity" styling with high-contrast colors

- [ ] Task 4: Create OEE page in Next.js App Router (AC: #6, #7)
  - [ ] 4.1 Create `src/app/production/oee/page.tsx` route
  - [ ] 4.2 Add toggle/tabs for Yesterday vs Live OEE view
  - [ ] 4.3 Display target vs actual comparison section
  - [ ] 4.4 Integrate OEE components into cohesive dashboard layout
  - [ ] 4.5 Add loading states and error boundaries

- [ ] Task 5: Implement real-time data refresh (AC: #5)
  - [ ] 5.1 Add SWR or React Query for data fetching with 60-second refresh
  - [ ] 5.2 Implement visual indicator when data is refreshing
  - [ ] 5.3 Show last updated timestamp on OEE view

## Dev Notes

### OEE Calculation Formula

OEE = Availability x Performance x Quality

| Component | Formula | Data Source |
|-----------|---------|-------------|
| **Availability** | Run Time / Planned Production Time | `daily_summaries.run_time`, `shift_targets.planned_time` |
| **Performance** | (Total Units / Run Time) / Ideal Rate | `daily_summaries.total_output`, `shift_targets.target_output` |
| **Quality** | Good Units / Total Units | `daily_summaries.good_output`, `daily_summaries.total_output` |

**Note:** Handle edge cases where divisor is zero - return null/N/A rather than error.

### Technical Stack Requirements

| Component | Technology | Notes |
|-----------|-----------|-------|
| Backend Calculation | Python/FastAPI | Use `app/services/` pattern |
| Data Source | Supabase PostgreSQL | Query `daily_summaries`, `live_snapshots`, `shift_targets` |
| Frontend | Next.js 14+ App Router | Route: `/production/oee` |
| Styling | Tailwind CSS + Shadcn/UI | "Industrial Clarity" theme |
| Data Fetching | SWR or React Query | 60-second auto-refresh |

### API Response Structure

```json
{
  "plant_oee": {
    "overall": 78.5,
    "availability": 92.1,
    "performance": 88.3,
    "quality": 96.5,
    "target": 85.0,
    "status": "yellow"
  },
  "assets": [
    {
      "asset_id": "uuid",
      "name": "Grinder 5",
      "oee": 82.3,
      "availability": 95.0,
      "performance": 90.1,
      "quality": 96.2,
      "target": 85.0,
      "status": "yellow"
    }
  ],
  "data_source": "daily_summaries",
  "last_updated": "2026-01-05T06:00:00Z"
}
```

### Color Thresholds (OEE Status)

| Status | OEE Range | Tailwind Class |
|--------|-----------|----------------|
| Green | >= 85% | `bg-green-500` or `text-green-500` |
| Yellow | 70-84% | `bg-yellow-500` or `text-yellow-500` |
| Red | < 70% | `bg-red-500` or `text-red-500` |

**Important:** "Safety Red" (`bg-red-600` or darker) is reserved for safety incidents per UX design. Use standard red for OEE status.

### UI/UX Requirements

- **Glanceability:** OEE percentage must be readable from 3 feet away
  - Use large font sizes (48px+) for primary OEE value
  - High contrast (dark text on light, or white on colored background)
- **Contextual Separation:**
  - Cool colors/static style for T-1 "Yesterday" data
  - Vibrant/pulsing indicators for T-15m "Live Pulse" data
- **Industrial Clarity:** Follow established design system from Story 1.6

### Directory Structure

```text
apps/
├── api/
│   └── app/
│       ├── api/
│       │   └── oee.py          # NEW: OEE API router
│       └── services/
│           └── oee_calculator.py # NEW: OEE calculation logic
└── web/
    └── src/
        ├── app/
        │   └── production/
        │       └── oee/
        │           └── page.tsx  # NEW: OEE dashboard page
        └── components/
            └── oee/              # NEW: OEE component folder
                ├── OEEGauge.tsx
                ├── OEEBreakdown.tsx
                ├── AssetOEEList.tsx
                └── OEEStatusBadge.tsx
```

### Project Structure Notes

- API router follows existing pattern in `apps/api/app/api/`
- Service layer follows existing pattern in `apps/api/app/services/`
- Frontend route under `/production/` matches IA from UX design (Production Intelligence section)
- Components organized in feature-specific folder under `components/`

### Dependencies on Previous Stories

- **Story 1.1:** TurboRepo monorepo structure (apps/web, apps/api)
- **Story 1.3:** Plant Object Model schema (assets, shift_targets tables)
- **Story 1.4:** Analytical Cache schema (daily_summaries, live_snapshots tables)
- **Story 1.6:** Industrial Clarity design system (Tailwind + Shadcn/UI)
- **Story 2.1:** Batch Data Pipeline populates daily_summaries with T-1 data
- **Story 2.2:** Polling Data Pipeline populates live_snapshots with T-15m data

### References

- [Source: architecture.md#5-data-models] - daily_summaries, live_snapshots, shift_targets schema
- [Source: architecture.md#6-data-pipelines] - Pipeline A/B data flow
- [Source: prd.md#2-requirements] - FR1 (Data Ingestion), NFR2 (60-second latency)
- [Source: ux-design.md#2-usability-goals] - Glanceability, Industrial Clarity
- [Source: ux-design.md#3-information-architecture] - Production Intelligence > Throughput & OEE
- [Source: epic-2.md#story-2.4] - OEE Metrics View requirements

### Anti-Patterns to Avoid

1. **DO NOT** calculate OEE in the frontend - all calculations must be server-side
2. **DO NOT** use "Safety Red" color for OEE status - reserve for safety incidents only
3. **DO NOT** write to MSSQL - system is read-only (NFR3)
4. **DO NOT** fetch raw MSSQL data directly - use the analytical cache tables
5. **DO NOT** create custom styling - reuse Industrial Clarity design system from Story 1.6
6. **DO NOT** skip error handling for zero divisors in OEE calculations

### Testing Verification

After implementation, verify:
1. `GET /api/oee/plant` returns valid OEE data structure
2. `GET /api/oee/assets` returns list of assets with OEE metrics
3. OEE calculations handle zero/null values gracefully
4. Frontend displays plant-wide OEE gauge with correct color coding
5. Asset breakdown shows all three OEE components
6. Yesterday/Live toggle correctly switches data source
7. Data auto-refreshes every 60 seconds on Live view
8. UI is readable on tablet screen from 3 feet away

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
