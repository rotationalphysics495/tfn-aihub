TEST SPEC START
story_id: 14-4-trend-indicators-on-action-cards
generated: 2026-02-11

test_specifications:

## AC1: Repeat offender badge displayed when consecutive_days >= 3

### 14-4-trend-indicators-on-action-cards-UNIT-001: Repeat offender badge renders with warning variant when consecutive_days >= 3
- Priority: P0
- Type: unit
- Given: An action item has trendData with consecutiveDays = 3 and daysOnReport = 5
- When: The RepeatOffenderBadge component renders
- Then: A Badge with variant="warning" is displayed containing text "3rd day in a row"
- Data: trendData = { consecutiveDays: 3, daysOnReport: 5, metricHistory: [70,71,72,73,74,75,76], weekOverWeekChange: -2.5 }

### 14-4-trend-indicators-on-action-cards-UNIT-002: Repeat offender badge shows correct ordinal suffix for higher consecutive counts
- Priority: P0
- Type: unit
- Given: An action item has trendData with consecutiveDays = 5
- When: The RepeatOffenderBadge component renders
- Then: A Badge with variant="warning" is displayed containing text "5th day in a row"
- Data: trendData = { consecutiveDays: 5, daysOnReport: 6, metricHistory: [...], weekOverWeekChange: -1.0 }

### 14-4-trend-indicators-on-action-cards-UNIT-003: Repeat offender badge shows correct ordinal for 4th consecutive day
- Priority: P1
- Type: unit
- Given: An action item has trendData with consecutiveDays = 4
- When: The RepeatOffenderBadge component renders
- Then: A Badge with variant="warning" is displayed containing text "4th day in a row"
- Data: trendData = { consecutiveDays: 4, daysOnReport: 4, metricHistory: [...], weekOverWeekChange: 3.0 }

### 14-4-trend-indicators-on-action-cards-UNIT-004: Frequency badge shown when days_on_report >= 3 but consecutive_days < 3
- Priority: P0
- Type: unit
- Given: An action item has trendData with daysOnReport = 4 and consecutiveDays = 1
- When: The RepeatOffenderBadge component renders
- Then: A Badge with variant="warning" is displayed containing text "4 of 7 days"
- Data: trendData = { consecutiveDays: 1, daysOnReport: 4, metricHistory: [...], weekOverWeekChange: -2.0 }

### 14-4-trend-indicators-on-action-cards-UNIT-005: Second day badge shown with outline variant when consecutive_days = 2
- Priority: P1
- Type: unit
- Given: An action item has trendData with consecutiveDays = 2 and daysOnReport = 2
- When: The RepeatOffenderBadge component renders
- Then: A Badge with variant="outline" is displayed containing text "2nd day"
- Data: trendData = { consecutiveDays: 2, daysOnReport: 2, metricHistory: [...], weekOverWeekChange: 1.5 }

### 14-4-trend-indicators-on-action-cards-UNIT-006: Repeat offender badge has correct ARIA label for accessibility
- Priority: P1
- Type: unit
- Given: An action item has trendData with consecutiveDays = 3
- When: The RepeatOffenderBadge component renders
- Then: The badge element has an appropriate aria-label describing the repeat status (e.g., "Repeat issue: 3rd day in a row")
- Data: trendData = { consecutiveDays: 3, daysOnReport: 5, metricHistory: [...], weekOverWeekChange: -3.0 }

### 14-4-trend-indicators-on-action-cards-UNIT-007: Consecutive_days >= 3 takes precedence over days_on_report >= 3
- Priority: P1
- Type: unit
- Given: An action item has trendData with consecutiveDays = 3 AND daysOnReport = 5 (both conditions met)
- When: The RepeatOffenderBadge component renders
- Then: The "3rd day in a row" badge is shown (not "5 of 7 days") because consecutive takes precedence
- Data: trendData = { consecutiveDays: 3, daysOnReport: 5, metricHistory: [...], weekOverWeekChange: -1.0 }

## AC2: Trend arrow displayed based on week_over_week_change

### 14-4-trend-indicators-on-action-cards-UNIT-008: Green arrow shown when OEE metric improves (positive change)
- Priority: P0
- Type: unit
- Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = 3.1
- When: The TrendIndicator component renders
- Then: A green trend arrow (up/improving direction) is displayed with text "+3.1%"
- Data: priority = "OEE", trendData = { weekOverWeekChange: 3.1, metricHistory: [70,71,72,73,74,75,76], consecutiveDays: 2, daysOnReport: 3 }

### 14-4-trend-indicators-on-action-cards-UNIT-009: Red arrow shown when OEE metric worsens (negative change)
- Priority: P0
- Type: unit
- Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = -4.2
- When: The TrendIndicator component renders
- Then: A red trend arrow (down/worsening direction) is displayed with text "-4.2%"
- Data: priority = "OEE", trendData = { weekOverWeekChange: -4.2, metricHistory: [76,75,74,73,72,71,70], consecutiveDays: 1, daysOnReport: 1 }

### 14-4-trend-indicators-on-action-cards-UNIT-010: Green arrow shown when FINANCIAL metric improves (negative change = loss decreased)
- Priority: P0
- Type: unit
- Given: An action item has priority = "FINANCIAL" and trendData with weekOverWeekChange = -5.0
- When: The TrendIndicator component renders
- Then: A green trend arrow (improving direction) is displayed with text "-5.0%"
- Data: priority = "FINANCIAL", trendData = { weekOverWeekChange: -5.0, metricHistory: [100,95,90,85,80,75,70], consecutiveDays: 2, daysOnReport: 4 }

### 14-4-trend-indicators-on-action-cards-UNIT-011: Red arrow shown when FINANCIAL metric worsens (positive change = loss increased)
- Priority: P0
- Type: unit
- Given: An action item has priority = "FINANCIAL" and trendData with weekOverWeekChange = 6.3
- When: The TrendIndicator component renders
- Then: A red trend arrow (worsening direction) is displayed with text "+6.3%"
- Data: priority = "FINANCIAL", trendData = { weekOverWeekChange: 6.3, metricHistory: [70,75,80,85,90,95,100], consecutiveDays: 3, daysOnReport: 5 }

### 14-4-trend-indicators-on-action-cards-UNIT-012: Gray horizontal arrow shown when change is stable (< 2% absolute)
- Priority: P0
- Type: unit
- Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = 1.5
- When: The TrendIndicator component renders
- Then: A gray horizontal arrow is displayed indicating stable trend
- Data: priority = "OEE", trendData = { weekOverWeekChange: 1.5, metricHistory: [72,73,72,73,72,73,72], consecutiveDays: 1, daysOnReport: 2 }

### 14-4-trend-indicators-on-action-cards-UNIT-013: Gray horizontal arrow for negative stable change (> -2%)
- Priority: P1
- Type: unit
- Given: An action item has priority = "FINANCIAL" and trendData with weekOverWeekChange = -1.9
- When: The TrendIndicator component renders
- Then: A gray horizontal arrow is displayed indicating stable trend
- Data: priority = "FINANCIAL", trendData = { weekOverWeekChange: -1.9, metricHistory: [...], consecutiveDays: 1, daysOnReport: 1 }

### 14-4-trend-indicators-on-action-cards-UNIT-014: Boundary test - exactly 2% absolute change shows directional arrow (not stable)
- Priority: P1
- Type: unit
- Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = 2.0
- When: The TrendIndicator component renders
- Then: A green arrow is displayed (2.0% is at the boundary, should show directional since stable is < 2%)
- Data: priority = "OEE", trendData = { weekOverWeekChange: 2.0, metricHistory: [...], consecutiveDays: 1, daysOnReport: 1 }

### 14-4-trend-indicators-on-action-cards-UNIT-015: Boundary test - exactly -2% absolute change shows directional arrow
- Priority: P1
- Type: unit
- Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = -2.0
- When: The TrendIndicator component renders
- Then: A red arrow is displayed (exactly 2% absolute is not < 2%, so not stable)
- Data: priority = "OEE", trendData = { weekOverWeekChange: -2.0, metricHistory: [...], consecutiveDays: 1, daysOnReport: 1 }

### 14-4-trend-indicators-on-action-cards-UNIT-016: No trend arrow for SAFETY priority items
- Priority: P0
- Type: unit
- Given: An action item has priority = "SAFETY" and trendData with weekOverWeekChange = -5.0
- When: The TrendIndicator component renders
- Then: No trend arrow is displayed (safety items do not show directional trend arrows)
- Data: priority = "SAFETY", trendData = { weekOverWeekChange: -5.0, metricHistory: [...], consecutiveDays: 3, daysOnReport: 5 }

### 14-4-trend-indicators-on-action-cards-UNIT-017: Trend arrow has correct ARIA label describing direction and percentage
- Priority: P1
- Type: unit
- Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = -3.1
- When: The TrendIndicator component renders
- Then: The trend indicator has an ARIA label like "Trend: worsening, OEE down 3.1%"
- Data: priority = "OEE", trendData = { weekOverWeekChange: -3.1, metricHistory: [...], consecutiveDays: 2, daysOnReport: 3 }

### 14-4-trend-indicators-on-action-cards-UNIT-018: Zero week_over_week_change shows gray stable arrow
- Priority: P1
- Type: unit
- Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = 0
- When: The TrendIndicator component renders
- Then: A gray horizontal arrow is displayed indicating stable trend
- Data: priority = "OEE", trendData = { weekOverWeekChange: 0, metricHistory: [72,72,72,72,72,72,72], consecutiveDays: 1, daysOnReport: 1 }

### 14-4-trend-indicators-on-action-cards-UNIT-019: Null weekOverWeekChange does not render trend arrow
- Priority: P1
- Type: unit
- Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = null
- When: The TrendIndicator component renders
- Then: No trend arrow is displayed (graceful handling of null)
- Data: priority = "OEE", trendData = { weekOverWeekChange: null, metricHistory: [...], consecutiveDays: 1, daysOnReport: 1 }

## AC3: 7-day sparkline chart displayed from trend_data

### 14-4-trend-indicators-on-action-cards-UNIT-020: Sparkline renders with 7-day metric history data
- Priority: P0
- Type: unit
- Given: An action item has trendData with metricHistory = [72.5, 74.1, 68.3, 71.0, 69.2, 73.8, 72.5]
- When: The TrendIndicator component renders
- Then: A small sparkline chart (approximately 80px wide x 24px tall) is rendered next to the metric value showing the 7-day trend
- Data: trendData = { metricHistory: [72.5, 74.1, 68.3, 71.0, 69.2, 73.8, 72.5], weekOverWeekChange: 0.0, consecutiveDays: 2, daysOnReport: 3 }

### 14-4-trend-indicators-on-action-cards-UNIT-021: Sparkline stroke color matches trend direction (green for improving)
- Priority: P1
- Type: unit
- Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = 3.5 (improving)
- When: The TrendIndicator component renders
- Then: The sparkline line stroke color is green
- Data: priority = "OEE", trendData = { metricHistory: [70,71,72,73,74,75,76], weekOverWeekChange: 3.5, consecutiveDays: 1, daysOnReport: 2 }

### 14-4-trend-indicators-on-action-cards-UNIT-022: Sparkline stroke color is red for worsening trend
- Priority: P1
- Type: unit
- Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = -4.0 (worsening)
- When: The TrendIndicator component renders
- Then: The sparkline line stroke color is red
- Data: priority = "OEE", trendData = { metricHistory: [76,75,74,73,72,71,70], weekOverWeekChange: -4.0, consecutiveDays: 2, daysOnReport: 4 }

### 14-4-trend-indicators-on-action-cards-UNIT-023: Sparkline stroke color is gray for stable trend
- Priority: P1
- Type: unit
- Given: An action item has priority = "OEE" and trendData with weekOverWeekChange = 0.5 (stable)
- When: The TrendIndicator component renders
- Then: The sparkline line stroke color is gray
- Data: priority = "OEE", trendData = { metricHistory: [72,72.5,72,72.5,72,72.5,72], weekOverWeekChange: 0.5, consecutiveDays: 1, daysOnReport: 1 }

### 14-4-trend-indicators-on-action-cards-UNIT-024: Sparkline handles null values in metricHistory gracefully
- Priority: P1
- Type: unit
- Given: An action item has trendData with metricHistory = [72.5, null, 68.3, null, 69.2, 73.8, 72.5]
- When: The TrendIndicator component renders
- Then: A sparkline is rendered connecting only the non-null data points without errors
- Data: trendData = { metricHistory: [72.5, null, 68.3, null, 69.2, 73.8, 72.5], weekOverWeekChange: 0.0, consecutiveDays: 1, daysOnReport: 3 }

### 14-4-trend-indicators-on-action-cards-UNIT-025: Sparkline handles all-null metricHistory gracefully
- Priority: P1
- Type: unit
- Given: An action item has trendData with metricHistory = [null, null, null, null, null, null, null]
- When: The TrendIndicator component renders
- Then: No sparkline is rendered (graceful degradation) and no error is thrown
- Data: trendData = { metricHistory: [null, null, null, null, null, null, null], weekOverWeekChange: null, consecutiveDays: 1, daysOnReport: 1 }

### 14-4-trend-indicators-on-action-cards-UNIT-026: Sparkline renders with empty metricHistory array
- Priority: P2
- Type: unit
- Given: An action item has trendData with metricHistory = []
- When: The TrendIndicator component renders
- Then: No sparkline is rendered (graceful degradation) and no error is thrown
- Data: trendData = { metricHistory: [], weekOverWeekChange: 2.0, consecutiveDays: 1, daysOnReport: 1 }

### 14-4-trend-indicators-on-action-cards-UNIT-027: Sparkline renders without animation
- Priority: P2
- Type: unit
- Given: An action item has valid trendData with metricHistory
- When: The TrendIndicator component renders
- Then: The Recharts LineChart renders with isAnimationActive={false} for instant display
- Data: trendData = { metricHistory: [70,71,72,73,74,75,76], weekOverWeekChange: 2.5, consecutiveDays: 1, daysOnReport: 1 }

## AC4: "New" badge shown for first-appearance items

### 14-4-trend-indicators-on-action-cards-UNIT-028: "New" badge shown when days_on_report = 1 and consecutive_days = 1
- Priority: P0
- Type: unit
- Given: An action item has trendData with daysOnReport = 1 and consecutiveDays = 1
- When: The RepeatOffenderBadge component renders
- Then: A Badge with variant="info" is displayed containing text "New"
- Data: trendData = { consecutiveDays: 1, daysOnReport: 1, metricHistory: [72.5], weekOverWeekChange: null }

### 14-4-trend-indicators-on-action-cards-UNIT-029: "New" badge has info variant styling (blue background)
- Priority: P1
- Type: unit
- Given: An action item has trendData with daysOnReport = 1 and consecutiveDays = 1
- When: The RepeatOffenderBadge component renders
- Then: The Badge uses the "info" variant which applies blue background styling
- Data: trendData = { consecutiveDays: 1, daysOnReport: 1, metricHistory: [72.5], weekOverWeekChange: null }

### 14-4-trend-indicators-on-action-cards-UNIT-030: "New" badge has appropriate ARIA label
- Priority: P1
- Type: unit
- Given: An action item has trendData with daysOnReport = 1 and consecutiveDays = 1
- When: The RepeatOffenderBadge component renders
- Then: The badge has an ARIA label like "New issue"
- Data: trendData = { consecutiveDays: 1, daysOnReport: 1, metricHistory: [72.5], weekOverWeekChange: null }

### 14-4-trend-indicators-on-action-cards-UNIT-031: No badge rendered when trendData is undefined
- Priority: P0
- Type: unit
- Given: An action item has no trendData (trendData is undefined)
- When: The RepeatOffenderBadge component renders
- Then: No badge is rendered (returns null)
- Data: trendData = undefined

### 14-4-trend-indicators-on-action-cards-UNIT-032: No badge rendered when trendData is null
- Priority: P1
- Type: unit
- Given: An action item has trendData = null
- When: The RepeatOffenderBadge component renders
- Then: No badge is rendered (returns null)
- Data: trendData = null

## AC5: Skeleton placeholder when trend data is loading or unavailable

### 14-4-trend-indicators-on-action-cards-UNIT-033: Skeleton placeholder shown when isLoading is true
- Priority: P0
- Type: unit
- Given: The TrendIndicator component receives isLoading = true and no trendData
- When: The component renders
- Then: A compact skeleton placeholder is displayed (animated pulse divs) in place of the trend arrow and sparkline
- Data: isLoading = true, trendData = undefined, priority = "OEE"

### 14-4-trend-indicators-on-action-cards-UNIT-034: Card remains functional without trend data
- Priority: P0
- Type: integration
- Given: An action item has no trendData (undefined) and isLoading is false
- When: The InsightEvidenceCard renders
- Then: The card renders fully with PriorityBadge, recommendation text, asset name, timestamp, and action buttons; the trend indicator area is either empty or absent (no error)
- Data: ActionItem with trendData = undefined

### 14-4-trend-indicators-on-action-cards-UNIT-035: Skeleton placeholder has correct approximate dimensions
- Priority: P2
- Type: unit
- Given: The TrendIndicator component receives isLoading = true
- When: The component renders
- Then: The skeleton placeholder area is approximately the same size as the actual trend indicators (80x24px sparkline area, arrow area)
- Data: isLoading = true, trendData = undefined, priority = "OEE"

### 14-4-trend-indicators-on-action-cards-INT-001: InsightSection passes loading state to TrendIndicator
- Priority: P1
- Type: integration
- Given: InsightSection receives isLoading = true and trendData = undefined
- When: The component renders
- Then: The TrendIndicator within InsightSection shows a skeleton state
- Data: InsightSectionProps with isLoading = true, trendData = undefined

### 14-4-trend-indicators-on-action-cards-UNIT-036: TrendIndicator does not render when trendData is undefined and isLoading is false
- Priority: P1
- Type: unit
- Given: TrendIndicator receives trendData = undefined and isLoading = false
- When: The component renders
- Then: Nothing is rendered (no empty space, no skeleton, no indicators)
- Data: trendData = undefined, isLoading = false, priority = "OEE"

## AC6: TypeScript types and transformer mapping for trend_data

### 14-4-trend-indicators-on-action-cards-UNIT-037: TrendData interface has correct fields
- Priority: P0
- Type: unit
- Given: The TrendData interface is defined in types.ts
- When: A developer creates a TrendData object
- Then: The interface requires/allows: metricHistory: (number | null)[], daysOnReport: number, consecutiveDays: number, weekOverWeekChange: number | null
- Data: Type-level verification

### 14-4-trend-indicators-on-action-cards-UNIT-038: ActionItem type includes optional trendData field
- Priority: P0
- Type: unit
- Given: The ActionItem interface in types.ts
- When: A developer creates an ActionItem
- Then: The trendData field is optional (trendData?: TrendData) and the item can be created without it
- Data: Type-level verification

### 14-4-trend-indicators-on-action-cards-UNIT-039: Transformer maps API trend_data snake_case to component trendData camelCase
- Priority: P0
- Type: unit
- Given: An API response ActionItem has trend_data = { metric_values: [72.5, 74.1, 68.3], days_on_report: 4, consecutive_days: 3, week_over_week_change: -3.1 }
- When: transformAPIActionItem() processes the item
- Then: The result has trendData = { metricHistory: [72.5, 74.1, 68.3], daysOnReport: 4, consecutiveDays: 3, weekOverWeekChange: -3.1 }
- Data: API item with trend_data field populated

### 14-4-trend-indicators-on-action-cards-UNIT-040: Transformer handles null trend_data from API
- Priority: P0
- Type: unit
- Given: An API response ActionItem has trend_data = null
- When: transformAPIActionItem() processes the item
- Then: The result has trendData = undefined (not null)
- Data: API item with trend_data: null

### 14-4-trend-indicators-on-action-cards-UNIT-041: Transformer handles absent trend_data from API
- Priority: P0
- Type: unit
- Given: An API response ActionItem has no trend_data field at all
- When: transformAPIActionItem() processes the item
- Then: The result has trendData = undefined
- Data: API item without trend_data key

### 14-4-trend-indicators-on-action-cards-UNIT-042: Transformer preserves null values in metric_values array
- Priority: P1
- Type: unit
- Given: An API response has trend_data.metric_values = [72.5, null, 68.3, null, 69.2, 73.8, 72.5]
- When: transformAPIActionItem() processes the item
- Then: The result trendData.metricHistory = [72.5, null, 68.3, null, 69.2, 73.8, 72.5] (nulls preserved for component to handle)
- Data: API item with trend_data containing null metric values

### 14-4-trend-indicators-on-action-cards-UNIT-043: Transformer handles null week_over_week_change
- Priority: P1
- Type: unit
- Given: An API response has trend_data with week_over_week_change = null
- When: transformAPIActionItem() processes the item
- Then: The result trendData.weekOverWeekChange = null
- Data: API item with trend_data.week_over_week_change: null

## AC7: Responsive layout on tablet viewport

### 14-4-trend-indicators-on-action-cards-INT-002: Trend indicators render within InsightSection layout
- Priority: P0
- Type: integration
- Given: An InsightSection with trendData, priority, and all standard props
- When: The component renders
- Then: RepeatOffenderBadge appears inline with PriorityBadge in the first row AND TrendIndicator appears as a new row between the badge row and recommendation text
- Data: Full InsightSectionProps with trendData = { consecutiveDays: 3, daysOnReport: 5, metricHistory: [70,71,72,73,74,75,76], weekOverWeekChange: 3.5 }, priority = "OEE"

### 14-4-trend-indicators-on-action-cards-INT-003: InsightEvidenceCard passes trendData to InsightSection
- Priority: P0
- Type: integration
- Given: An InsightEvidenceCard renders with an ActionItem that has trendData
- When: The card renders
- Then: The InsightSection child receives the trendData prop and renders trend indicators
- Data: ActionItem with trendData = { consecutiveDays: 3, daysOnReport: 5, metricHistory: [70,71,72,73,74,75,76], weekOverWeekChange: 3.5 }

### 14-4-trend-indicators-on-action-cards-E2E-001: Trend indicators visible on tablet viewport without scrolling
- Priority: P0
- Type: e2e
- Given: The action items page is loaded with items containing trend data
- When: Viewed on a tablet viewport (768px-1024px width)
- Then: The trend arrow, sparkline, and repeat offender badge are all visible and readable within the card's left column without horizontal scrolling
- Data: Viewport width 768px, ActionItem with full trendData

### 14-4-trend-indicators-on-action-cards-E2E-002: Trend indicators render correctly on desktop viewport
- Priority: P1
- Type: e2e
- Given: The action items page is loaded with items containing trend data
- When: Viewed on a desktop viewport (1280px+ width)
- Then: Trend indicators are rendered inline and proportionally sized within the card layout
- Data: Viewport width 1280px, ActionItem with full trendData

### 14-4-trend-indicators-on-action-cards-INT-004: Layout does not overflow when all trend elements are present
- Priority: P1
- Type: integration
- Given: An InsightSection with a repeat offender badge (consecutiveDays=5), trend arrow, percentage change text, sparkline, AND a long recommendation text
- When: The component renders at md breakpoint
- Then: No horizontal overflow occurs; all elements wrap appropriately within the card boundaries
- Data: InsightSectionProps with long recommendation text (~100 chars) and full trendData

### 14-4-trend-indicators-on-action-cards-INT-005: TrendIndicator and RepeatOffenderBadge exported from barrel index
- Priority: P1
- Type: integration
- Given: The action-engine index.ts barrel export file
- When: A consumer imports TrendIndicator, RepeatOffenderBadge, or TrendData from the barrel
- Then: All three exports are available and correctly typed
- Data: Import verification from '@/components/action-engine'

edge_cases:
  - metricHistory array with fewer than 7 data points (e.g., 3 data points for a new item that has only been tracked 3 days)
  - metricHistory array with all identical values (perfectly flat sparkline)
  - Extremely large weekOverWeekChange values (e.g., +500% or -90%) - display should not overflow
  - consecutiveDays = 0 (invalid/unexpected data from API) - should render nothing or handle gracefully
  - daysOnReport = 0 (invalid/unexpected data from API) - should render nothing or handle gracefully
  - Very large consecutiveDays (e.g., 30) - ordinal suffix should still work ("30th day in a row")
  - Negative metricHistory values (edge case for financial data) - sparkline should still render
  - weekOverWeekChange = -0 (negative zero) - should be treated as stable
  - ActionItem with trendData but missing some nested fields (partial trendData object)

error_scenarios:
  - API returns malformed trend_data (e.g., metric_values is not an array) - transformer should handle without crashing
  - API returns trend_data with unexpected field names - transformer should still produce valid output (missing fields become undefined)
  - Recharts LineChart fails to render (e.g., invalid data) - component should catch error and show fallback
  - trendData.weekOverWeekChange is NaN - should be treated as unavailable, no arrow shown
  - trendData.consecutiveDays is negative - should be treated as no badge
  - Rapid re-renders with changing trendData (no animation means no stale state issues)

test_file_mapping:
  - 14-4-trend-indicators-on-action-cards-UNIT-001 to UNIT-007: apps/web/src/components/action-engine/__tests__/RepeatOffenderBadge.test.tsx
  - 14-4-trend-indicators-on-action-cards-UNIT-008 to UNIT-019: apps/web/src/components/action-engine/__tests__/TrendIndicator.test.tsx
  - 14-4-trend-indicators-on-action-cards-UNIT-020 to UNIT-027: apps/web/src/components/action-engine/__tests__/TrendIndicator.test.tsx
  - 14-4-trend-indicators-on-action-cards-UNIT-028 to UNIT-032: apps/web/src/components/action-engine/__tests__/RepeatOffenderBadge.test.tsx
  - 14-4-trend-indicators-on-action-cards-UNIT-033 to UNIT-036: apps/web/src/components/action-engine/__tests__/TrendIndicator.test.tsx
  - 14-4-trend-indicators-on-action-cards-UNIT-037 to UNIT-038: apps/web/src/components/action-engine/__tests__/types.test.ts (compile-time / type assertion tests)
  - 14-4-trend-indicators-on-action-cards-UNIT-039 to UNIT-043: apps/web/src/components/action-engine/__tests__/transformers.trend.test.tsx
  - 14-4-trend-indicators-on-action-cards-INT-001 to INT-005: apps/web/src/components/action-engine/__tests__/InsightSection.trend.test.tsx
  - 14-4-trend-indicators-on-action-cards-E2E-001 to E2E-002: apps/web/e2e/action-cards-trend.spec.ts (Playwright or Cypress)

TEST SPEC END
