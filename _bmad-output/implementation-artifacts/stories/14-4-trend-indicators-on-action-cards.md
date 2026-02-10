# Story 14.4: Trend Indicators on Action Cards

Status: ready-for-dev

## Story

As a Plant Manager,
I want to see trend arrows, repeat offender badges, and 7-day sparklines on each action item card,
so that I can instantly tell whether an issue is new, improving, or getting worse and decide whether to escalate.

## Acceptance Criteria

1. **Given** an action item has trend data with `consecutive_days` >= 3, **When** the action card renders, **Then** a "repeat offender" badge is displayed (e.g., "3rd consecutive day" or "4 of last 7 days") **And** the badge uses amber/orange background styling via the existing Shadcn/UI `Badge` component with the `warning` variant.

2. **Given** an action item has `week_over_week_change` data, **When** the action card renders, **Then** a trend arrow is displayed:
   - Green down arrow if the metric improved (OEE up or downtime down)
   - Red up arrow if the metric worsened (OEE down or downtime up)
   - Gray horizontal arrow if stable (< 2% absolute change)

3. **Given** an action item has a 7-day sparkline array in `trend_data`, **When** the action card renders, **Then** a small sparkline chart (approximately 80px wide x 24px tall) shows the 7-day trend next to the metric value.

4. **Given** an action item has no trend data (first appearance, `days_on_report` = 1, `consecutive_days` = 1), **When** the action card renders, **Then** a "New" badge is shown instead of trend indicators, using the `info` badge variant.

5. **Given** trend data is loading or unavailable, **When** the action card renders, **Then** the trend indicator area shows a compact skeleton placeholder **And** the card remains fully functional without trend data (graceful degradation).

6. **Given** the action items API returns `trend_data` on each item, **When** the frontend receives the response, **Then** the `ActionItem` TypeScript type includes a `trendData` field **And** the transformer maps API `trend_data` to the component's `TrendData` interface.

7. **Given** the InsightSection renders trend indicators, **When** viewed on a tablet (primary device), **Then** the trend arrow + sparkline + badge are visible and readable without scrolling within the card's left column.

## Tasks / Subtasks

- [ ] Task 1: Add TrendData types to frontend type system (AC: #6)
  - [ ] 1.1 Add `TrendData` interface to `apps/web/src/components/action-engine/types.ts`
  - [ ] 1.2 Add optional `trendData` field to the `ActionItem` interface in `types.ts`
  - [ ] 1.3 Add `TrendData` type to the `useDailyActions.ts` hook's `ActionItem` interface
  - [ ] 1.4 Update `transformers.ts` to map API `trend_data` snake_case to `trendData` camelCase

- [ ] Task 2: Create TrendIndicator component (AC: #2, #3, #5)
  - [ ] 2.1 Create `apps/web/src/components/action-engine/TrendIndicator.tsx`
  - [ ] 2.2 Implement trend arrow with SVG icons (green down, red up, gray horizontal)
  - [ ] 2.3 Implement 7-day sparkline using Recharts `LineChart` (minimal, no axes)
  - [ ] 2.4 Add skeleton state for loading/unavailable trend data
  - [ ] 2.5 Add ARIA labels for accessibility (e.g., "Trend: worsening, OEE down 3.1%")

- [ ] Task 3: Create RepeatOffenderBadge component (AC: #1, #4)
  - [ ] 3.1 Create `apps/web/src/components/action-engine/RepeatOffenderBadge.tsx`
  - [ ] 3.2 Show "New" badge (info variant) when `consecutive_days` = 1 and `days_on_report` = 1
  - [ ] 3.3 Show repeat offender badge (warning variant) when `consecutive_days` >= 3
  - [ ] 3.4 Show frequency badge (e.g., "4 of 7 days") when `days_on_report` >= 3 but not consecutive
  - [ ] 3.5 Use existing Shadcn/UI `Badge` component from `@/components/ui/badge`

- [ ] Task 4: Integrate trend indicators into InsightSection (AC: #7)
  - [ ] 4.1 Update `InsightSection.tsx` to accept optional `trendData` prop
  - [ ] 4.2 Place TrendIndicator between PriorityBadge row and recommendation text
  - [ ] 4.3 Place RepeatOffenderBadge inline with the PriorityBadge
  - [ ] 4.4 Ensure layout works on tablet (md breakpoint) without overflow

- [ ] Task 5: Wire InsightEvidenceCard to pass trend data (AC: #6)
  - [ ] 5.1 Update `InsightEvidenceCard.tsx` to pass `item.trendData` to `InsightSection`
  - [ ] 5.2 Update barrel export in `index.ts` to export new components

- [ ] Task 6: Verify responsive layout and visual polish (AC: #7)
  - [ ] 6.1 Test on tablet viewport (768px-1024px) to confirm trend elements fit
  - [ ] 6.2 Test dark mode styling for trend arrows and sparkline
  - [ ] 6.3 Confirm graceful degradation when `trendData` is undefined/null

## Dev Notes

### Architecture & Patterns

- **Component Pattern:** Follow existing action-engine component structure. Each new component gets its own file in `apps/web/src/components/action-engine/`. Use `'use client'` directive since these components are interactive.
- **Styling:** Tailwind CSS with `cn()` utility from `@/lib/utils`. Follow "Industrial Clarity" design system. Use existing Shadcn/UI primitives (`Badge` from `@/components/ui/badge`) rather than creating custom badge components.
- **Charts:** Recharts 3.6+ is already installed (`"recharts": "^3.6.0"` in package.json). Use `LineChart` with `Line` for the sparkline. No axes, no grid, no tooltip -- just the line itself for a compact visualization.
- **Type Safety:** All components must use TypeScript. The `ActionItem` type flows from API (Python Pydantic) through `useDailyActions.ts` hook types to the component `types.ts` types, with `transformers.ts` doing the mapping between them.

### Key Existing Files to Understand

| File | Role | What to Know |
|------|------|-------------|
| `apps/web/src/components/action-engine/types.ts` | Component-level types | `ActionItem` interface -- add `trendData?: TrendData` here |
| `apps/web/src/hooks/useDailyActions.ts` | API data hook | `ActionItem` interface (API shape) -- add `trend_data` snake_case field here |
| `apps/web/src/components/action-engine/transformers.ts` | API-to-component mapping | `transformAPIActionItem()` -- add `trendData` mapping here |
| `apps/web/src/components/action-engine/InsightSection.tsx` | Left side of card | Where trend indicators are rendered. Currently shows PriorityBadge, financial impact, recommendation text, asset/timestamp row |
| `apps/web/src/components/action-engine/InsightEvidenceCard.tsx` | Card wrapper | Passes `item` props to InsightSection. Must pass `trendData` through |
| `apps/web/src/components/action-engine/PriorityBadge.tsx` | Priority badge | `PriorityType` = 'SAFETY' \| 'FINANCIAL' \| 'OEE'. Do NOT modify this. |
| `apps/web/src/components/ui/badge.tsx` | Shadcn Badge | Has `warning` variant (amber) and `info` variant (blue). Use these for repeat offender and "New" badges. |
| `apps/web/src/components/action-engine/index.ts` | Barrel export | Add new component exports here |

### API Contract (Story 14.2 Dependency)

Story 14.2 adds a `trend_data` field to each `ActionItem` in the API response from `GET /api/v1/actions/daily?date={date}`. The expected shape from the backend:

```json
{
  "trend_data": {
    "metric_history": [72.5, 74.1, 68.3, 71.0, 69.2, 73.8, 72.5],
    "days_on_report": 4,
    "consecutive_days": 3,
    "week_over_week_change": -3.1
  }
}
```

- `metric_history`: 7-day array of the relevant metric value (OEE % for OEE items, downtime minutes for downtime items)
- `days_on_report`: count of days this asset+category appeared as action item in last 7 days
- `consecutive_days`: consecutive days this has been an issue (resets when asset drops off)
- `week_over_week_change`: percentage change vs same metric 7 days ago. Positive = metric went up. For OEE, positive is good; for downtime, positive is bad. The frontend must interpret direction based on category.

**If Story 14.2 is not yet deployed:** The `trend_data` field will be undefined/null. All trend components MUST handle this gracefully (show nothing or a "New" badge). Do NOT make trend data required on the ActionItem type.

### Trend Direction Logic (CRITICAL)

The meaning of "improvement" depends on the metric category:
- **OEE/Schedule Adherence:** Higher is better. `week_over_week_change > 0` = improving (green arrow).
- **Downtime/Financial Loss:** Lower is better. `week_over_week_change > 0` = worsening (red arrow).
- **Safety:** No trend arrow. Safety items always show the "New" or repeat offender badge only.

Map this in the `TrendIndicator` component using the `priority` prop (SAFETY/FINANCIAL/OEE) from the parent card:

```typescript
function isImprovement(change: number, priority: PriorityType): boolean {
  if (priority === 'OEE') return change > 0;        // OEE up = good
  if (priority === 'FINANCIAL') return change < 0;   // Loss down = good
  return false; // Safety has no trend arrow
}
```

### Sparkline Implementation

Use Recharts `LineChart` with absolute minimal config:

```tsx
import { LineChart, Line } from 'recharts';

<LineChart width={80} height={24} data={sparkData}>
  <Line
    type="monotone"
    dataKey="value"
    stroke={trendColor}
    strokeWidth={1.5}
    dot={false}
    isAnimationActive={false}
  />
</LineChart>
```

- Width: 80px, Height: 24px (compact, fits inline)
- No axes, grid, tooltip, or legend
- `dot={false}` to keep it clean
- `isAnimationActive={false}` for instant render
- Stroke color matches trend direction (green/red/gray)

### Repeat Offender Badge Text

| Condition | Badge Text | Variant |
|-----------|-----------|---------|
| `consecutive_days` = 1 AND `days_on_report` = 1 | "New" | `info` |
| `consecutive_days` >= 3 | "3rd day in a row" (or nth) | `warning` |
| `days_on_report` >= 3 AND `consecutive_days` < 3 | "4 of 7 days" | `warning` |
| `consecutive_days` = 2 | "2nd day" | `outline` |
| Else (no trend data) | No badge | -- |

### Visual Layout in InsightSection

Current InsightSection layout (top to bottom):
1. Row: `[PriorityBadge] [Financial Impact $]`
2. Recommendation text (h3)
3. Row: `[Asset name] [Timestamp] [Assign button]`

Updated layout with trend indicators:
1. Row: `[PriorityBadge] [RepeatOffenderBadge] [Financial Impact $]`
2. Row: `[TrendArrow + % change] [Sparkline]` (new row)
3. Recommendation text (h3)
4. Row: `[Asset name] [Timestamp] [Assign button]`

### Testing Approach

- Unit test `TrendIndicator` with different `week_over_week_change` values and categories to verify arrow direction
- Unit test `RepeatOffenderBadge` with different `consecutive_days`/`days_on_report` combinations
- Unit test `transformAPIActionItem` to verify `trend_data` mapping
- Visual smoke test in browser with mock data to confirm layout on tablet and desktop

### Project Structure Notes

- All new files go in `apps/web/src/components/action-engine/` alongside existing components
- Follow existing naming: PascalCase filenames matching component names
- Barrel exports go in `apps/web/src/components/action-engine/index.ts`
- No new dependencies needed -- Recharts 3.6+ and Shadcn Badge are already available
- Do NOT install any new sparkline libraries. Use Recharts that is already in the project.

### References

- [Source: _bmad-output/planning-artifacts/epic-14.md - Story 14.4 section]
- [Source: docs/architecture-web.md - Component Architecture, Action Engine section]
- [Source: docs/data-models.md - daily_summaries table schema]
- [Source: docs/improvements.md - "Trend indicators on action items" planned feature]
- [Source: apps/web/src/components/action-engine/types.ts - ActionItem interface]
- [Source: apps/web/src/components/action-engine/InsightSection.tsx - Current layout]
- [Source: apps/web/src/components/action-engine/InsightEvidenceCard.tsx - Card wrapper]
- [Source: apps/web/src/hooks/useDailyActions.ts - API types and data fetching]
- [Source: apps/web/src/components/action-engine/transformers.ts - API-to-component mapping]
- [Source: apps/web/src/components/ui/badge.tsx - Badge variants (warning, info)]
- [Source: apps/web/package.json - recharts ^3.6.0 dependency]
- [Source: apps/api/app/schemas/action.py - Backend ActionItem schema]
- [Source: apps/api/app/services/action_engine.py - Backend action engine service]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
