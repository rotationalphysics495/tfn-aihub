# Trend Intelligence & Downtime Pareto - User Acceptance Testing

**Epic**: 14
**Version**: 1.0
**Generated**: 2026-02-11
**Stories Covered**: 6

---

## Overview

### What Was Built

The daily action report now shows historical context for every action item. Instead of just telling you "Grinder 5 had low OEE today," the system tells you whether this is a new problem or a recurring one, shows a 7-day trend chart, and breaks down exactly *why* downtime happened by reason code (e.g., Mechanical, Changeover, Material Shortage). The AI-generated smart summary also now includes week-over-week comparisons, repeat offender callouts, and top downtime drivers.

### Who Should Test

A **Plant Manager** or **Operations Lead** who regularly reviews the daily action report. The tester should be familiar with the action cards, the smart summary section, and the general workflow of opening the report, reviewing action items, and assigning follow-ups.

### Time Estimate

30-45 minutes

---

## Prerequisites

### Before You Begin

1. **Environment**
   - URL: UAT / Staging environment URL
   - Browser: Chrome (recommended) or Firefox

2. **Test Account**
   - Log in with your standard test Plant Manager account
   - Ensure you have access to at least one plant with action items

3. **Test Data Setup**
   - Seed data must be loaded so that at least 7 days of historical daily summaries and downtime events exist
   - Run the seed script if the environment has been recently reset:
     ```bash
     npm run seed
     ```

4. **Clean State**
   - No special reset is needed between scenarios
   - If you want to re-test the smart summary, you may need to clear the summary cache by waiting 15 minutes or requesting a new date

---

## Test Scenarios

### Scenario 1: View Trend Indicators on an Action Card

**Purpose**: Verify that each action item card shows trend arrows, percentage changes, and 7-day sparkline charts so you can tell at a glance whether an issue is improving, worsening, or stable.

**Starting Point**: Open the daily action report for yesterday's date.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to the daily action report page and select yesterday's date | The action report loads with a list of action item cards |
| 2 | Look at any OEE-related action card (e.g., an asset with low OEE) | The card displays a small trend arrow (green, red, or gray) and a percentage change value (e.g., "-3.1%") |
| 3 | Look next to the percentage change on the same card | A small 7-day sparkline chart (a mini line graph) appears showing the metric trend over the past 7 days |
| 4 | Compare a card with a green arrow to one with a red arrow | Green arrow means the metric is improving (e.g., OEE going up); red arrow means it is worsening (e.g., OEE going down); gray arrow means it is stable (less than 2% change) |
| 5 | Check that the sparkline color matches the arrow direction | The sparkline line is green for improving, red for worsening, or gray for stable |

**Success Criteria**: Every action card with historical data displays a trend arrow with percentage change and a 7-day sparkline chart.

**Result**: ☒ Pass  ☐ Fail

**Notes**: Trend arrows and sparklines confirmed on OEE and Financial cards. Financial cards correctly show upward arrow in red for cost increases (e.g., Roaster 1 +95.7% WoW). Safety cards show no arrow as expected. Required seed data extension (daysAgo 8–9) and icon direction bug fix for Financial items.

---

### Scenario 2: Identify Repeat Offender Assets

**Purpose**: Verify that assets appearing on the report for 3 or more consecutive days are flagged with a prominent "repeat offender" badge, helping you spot chronic problems at a glance.

**Starting Point**: Open the daily action report for yesterday's date.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Scan the action cards for any orange/amber badge | At least one card shows a badge like "3rd day in a row" or "4 of 7 days" in an amber/orange color |
| 2 | Find an asset you know has been on the report for multiple days (e.g., Grinder 5) | The card for that asset shows a repeat offender badge indicating the consecutive day count |
| 3 | Look for a card that is appearing for the first time | That card shows a blue "New" badge instead of a repeat offender badge |
| 4 | Check that the repeat offender badge appears inline with the priority badge (SAFETY, OEE, FINANCIAL) | Both badges appear on the same row, and the layout is not broken or overlapping |

**Success Criteria**: Repeat offender badges (amber) appear on cards with 3+ consecutive days on the report, and "New" badges (blue) appear on first-time items.

**Result**: ☒ Pass  ☐ Fail

**Notes**: Grinder 5 confirmed showing "4th day in a row" amber badge. First-time items show blue "New" badge. Badge layout correct, no overlapping with priority badge.

---

### Scenario 3: View Downtime Reason Code Breakdown on OEE Cards

**Purpose**: Verify that OEE-related action cards show a horizontal bar chart breaking down the reasons for downtime (e.g., Mechanical, Changeover), so you can direct investigations to the right root cause.

**Starting Point**: Open the daily action report for yesterday's date.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Find an action card that is related to OEE or downtime (not a safety-only or financial-only card) | The card loads and displays its normal content |
| 2 | Look in the evidence section of that card (the right side or bottom area) | A "Downtime Breakdown" section appears with a horizontal bar chart |
| 3 | Read the bar chart | The chart shows the top 3-5 reason codes (e.g., "Mechanical", "Changeover", "Material Shortage") sorted from longest duration to shortest |
| 4 | Check the labels on each bar | Each bar shows the reason code name, duration in minutes (e.g., "35 min"), and a percentage of total downtime (e.g., "49%") |
| 5 | Look for a visual difference between planned and unplanned downtime | Planned downtime bars (e.g., "Planned Maintenance") appear with a hatched/striped pattern, while unplanned bars are solid-filled |
| 6 | Find a safety-only or financial-only action card | No downtime breakdown chart is shown on that card |

**Success Criteria**: OEE/downtime-related action cards show a horizontal bar chart with reason codes, durations, and percentages. Safety-only and financial-only cards do not show the chart.

**Result**: ☒ Pass  ☐ Fail

**Notes**: Downtime Breakdown chart confirmed on OEE cards (2026-02-25). Filler Line A showed Mechanical (80 min, 84.2%, solid) and Changeover (15 min, 15.8%, hatched) bars. Labels show reason code, duration, and percentage correctly. Safety and financial-only cards show no chart. Required fix during session: `downtime_analysis.py` was selecting non-existent `cost_center_id` column from `assets` table — fixed by keying cost centers map by `asset_id` directly. Charts for all 3 OEE cards confirmed rendering independently after fix.

---

### Scenario 4: AI Smart Summary Includes Trend Context

**Purpose**: Verify that the AI-generated smart summary at the top of the report now includes historical comparisons and trend commentary, not just today's data.

**Starting Point**: Open the daily action report for yesterday's date. Scroll to the smart summary section.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Read the smart summary opening paragraph | The summary includes a week-over-week OEE comparison, such as "Overall plant OEE 81.2%, down 3.1 points from last week" |
| 2 | Look for repeat offender callouts in the summary text | The summary mentions assets that have been on the report for 3+ consecutive days, with language like "Grinder 5 has appeared on the report for 3 consecutive days -- consider escalating to maintenance planning" |
| 3 | Look for a downtime driver callout in the summary text | The summary mentions the top downtime driver, such as "Top downtime driver yesterday: Mechanical (187 min across 4 assets)" |
| 4 | Verify the rest of the summary is still present and readable | The existing summary content (safety events, productivity observations, financial impact) is still present and not disrupted by the new trend content |

**Success Criteria**: The smart summary includes week-over-week OEE comparison, repeat offender mentions, and top downtime driver information alongside the existing summary content.

**Result**: ☒ Pass  ☐ Fail

**Notes**: Smart summary for 2026-02-25 includes week-over-week OEE comparison, Grinder 5 repeat offender callout, and top downtime driver (Mechanical). Existing safety, productivity, and financial content present and unaffected.

---

### Scenario 5: Trend Data Loads for Different Date Selections

**Purpose**: Verify that trend indicators, Pareto charts, and summary context update correctly when you change the report date.

**Starting Point**: Open the daily action report for yesterday's date.

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Note the trend arrows and sparklines on the current date's action cards | Trend indicators are displayed for the selected date |
| 2 | Change the report date to 3 days ago | The action cards reload with updated trend data. The sparkline charts show different data points reflecting the 7-day window ending 3 days ago |
| 3 | Check the repeat offender badges after changing the date | Badges update to reflect the consecutive day count as of the selected date (the count may differ from yesterday's) |
| 4 | Check the downtime breakdown chart on an OEE card for the new date | The Pareto bar chart shows the downtime reasons for the newly selected date, not yesterday's |
| 5 | Check the smart summary for the new date | The summary reflects the week-over-week comparison as of the newly selected date |

**Success Criteria**: All trend indicators, Pareto charts, and summary trend context update to reflect the selected report date.

**Result**: ☒ Pass  ☐ Fail

**Notes**: Date changed to 2026-02-22 (3 days ago). Trend arrows, sparklines, repeat offender badges, and Pareto charts all updated to reflect the new date's data. Smart summary also reflected the correct week-over-week window for that date. **Known issue (Issue #4):** Smart summary does not automatically clear or regenerate when the date is changed — stale summary from the previous date persists until page refresh. Flagged for developers.

---

### Scenario 6: Loading States Display Correctly

**Purpose**: Verify that the system shows proper loading indicators while trend data and Pareto charts are being fetched, so the page does not appear broken during data loading.

**Starting Point**: Open the daily action report (optionally with a slow network or throttled connection).

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Observe the action cards as the page initially loads | Where trend indicators will appear, you see brief placeholder/skeleton animations (gray shimmering bars) instead of blank space |
| 2 | Observe the evidence section of an OEE card while loading | Where the Pareto chart will appear, you see a skeleton placeholder animation |
| 3 | Wait for loading to complete | The skeleton placeholders are replaced by the actual trend arrows, sparklines, and Pareto charts |
| 4 | Confirm that the card is fully usable during loading | You can still read the recommendation text, see the priority badge, and interact with the card (e.g., click "Assign") while trend data is still loading |

**Success Criteria**: Skeleton loading placeholders appear where trend data and Pareto charts will be displayed, and the card remains fully functional during loading.

**Result**: ☒ Pass  ☐ Fail

**Notes**: Skeleton shimmer placeholders visible on trend indicator and Pareto chart areas during initial load. Cards remained fully readable and interactive (recommendation text, priority badge, Assign button) while trend data loaded. Skeletons replaced cleanly by actual content on load completion.

---

### Scenario 7: Graceful Handling When No Historical Data Exists

**Purpose**: Verify that the system handles missing or limited historical data gracefully, without errors or broken layouts.

**Starting Point**: Open the daily action report for a date that has limited or no prior history (e.g., the earliest available date in the system).

**Steps**:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Find an action card for an asset that has just appeared for the first time | The card shows a blue "New" badge. No trend arrow or sparkline is shown (or only a single-point sparkline) |
| 2 | Check that no error messages appear on the card | The card displays normally without any error banners or console errors |
| 3 | Check the smart summary on a date with limited history | The summary omits trend commentary entirely (no "week-over-week" line, no repeat offender callout) but the rest of the summary is complete and readable |
| 4 | Check the Pareto chart on an OEE card for a date with no downtime events | No Pareto chart appears, and no error message is shown in its place |

**Success Criteria**: The system gracefully omits trend indicators, Pareto charts, and summary trend context when historical data is not available, without displaying errors or breaking the layout.

**Result**: ☒ Pass  ☐ Fail

**Notes**: Tested on 2026-02-17 (earliest seeded date). Step 1: Filler Line C showed blue "New" badge with no trend arrow or sparkline. Step 2: No error banners or console errors. Step 3: Smart summary omitted week-over-week and repeat offender content; base summary remained complete and readable. Step 4: Not directly observable in UI — seed data does not produce an OEE-miss asset with zero downtime events on the same date. Graceful empty state confirmed via API (pareto endpoint returns empty array with total_minutes=0) and component null-render logic (DowntimePareto.tsx renders null on empty data). Marked Pass — this is a seed data gap, not an implementation gap.

---

## Edge Cases & Error Handling

### Edge Case 1: Stable Metrics Show Gray Arrow

**Purpose**: Verify that a very small change (less than 2%) shows a gray horizontal arrow, not a red or green one.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Find an action card where the metric changed less than 2% from the prior week | The trend arrow is gray and horizontal (not pointing up or down) |
| 2 | Verify the percentage change displayed is small | A value like "+0.5%" or "-1.2%" is shown alongside the gray arrow |

**Result**: ☒ Pass  ☐ Fail

**Notes**: Filler Line C on 2026-02-25 shows gray horizontal arrow at -0.99% WoW change (80.0% vs 80.8% seven days prior). Seed data adjusted during session to produce this test case (daysAgo(8) value updated from 83.5% to 80.8%).

---

### Edge Case 2: Pareto Chart Not Shown for Safety Items

**Purpose**: Verify that safety-only action items do not display a downtime Pareto chart.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Find a safety-related action card (red "SAFETY" priority badge) | The card displays normally |
| 2 | Check the evidence section | No "Downtime Breakdown" section or bar chart is present |

**Result**: ☒ Pass  ☐ Fail

**Notes**: Safety card on 2026-02-25 (Pressure Anomaly) confirmed displaying normally with no Downtime Breakdown section present.

---

### Edge Case 3: Multiple Pareto Charts on the Same Page

**Purpose**: Verify that when multiple OEE cards each have their own Pareto chart, they all render correctly without interfering with each other.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Scroll through the action report and find two or more OEE-related cards with Pareto charts | Each card has its own independent Pareto chart |
| 2 | Compare the charts | Each chart shows different data corresponding to its specific asset. The hatched pattern for planned downtime renders correctly on all charts |

**Result**: ☒ Pass  ☐ Fail

**Notes**: Three OEE cards on 2026-02-25 each rendered independent Pareto charts with distinct data. Hatched pattern for planned downtime (Changeover) rendered correctly across all charts with no interference between them.

---

## Success Criteria Summary

This epic is **successful** when a user can:

- [x] See trend arrows (green/red/gray) and percentage changes on every action card with historical data
- [x] See 7-day sparkline mini-charts on action cards showing the metric trend
- [x] Identify repeat offender assets via prominent amber badges (e.g., "3rd day in a row")
- [x] See a "New" badge on action items appearing for the first time
- [x] View a downtime reason code breakdown (Pareto chart) on OEE-related action cards
- [x] Distinguish planned vs. unplanned downtime in the Pareto chart (hatched vs. solid bars)
- [x] Read trend context in the AI smart summary (week-over-week OEE, repeat offenders, top downtime drivers)
- [x] Confirm that the system handles missing data gracefully without errors

**Minimum passing**: All checkboxes marked

---

## Issues Log

| # | Scenario | Issue Description | Severity | Screenshot |
|---|----------|-------------------|----------|------------|
| 1 | S1 | Trend arrow direction inverted for Financial items (cost increase shown as green) | Minor | — Fixed during Session 1 |
| 2 | S3 | `downtime_analysis.py` selecting non-existent `cost_center_id` column from `assets` table — Pareto endpoint returning 500 | Major | — Fixed during Session 2 |
| 3 | EC1 | No seed data produced OEE-miss asset with <2% WoW change — gray arrow not observable without seed adjustment | Minor | — Seed adjusted during Session 2 |
| 4 | S5 | AI smart summary does not clear/regenerate when report date is changed — stale summary persists until page refresh | Minor | — Not fixed; flagged for developers |

### Severity Definitions

- **Critical**: Blocks core functionality, cannot proceed
- **Major**: Significant issue but workaround exists
- **Minor**: Cosmetic or minor inconvenience

---

## Sign-off

### Testing Summary

| Metric | Value |
|--------|-------|
| Scenarios Tested | 7 / 7 |
| Scenarios Passed | 7 / 7 |
| Edge Cases Tested | 3 / 3 |
| Edge Cases Passed | 3 / 3 |
| Critical Issues | 0 |
| Major Issues | 1 (Pareto endpoint 500 — `cost_center_id` column missing on `assets` table — fixed during session) |
| Minor Issues | 3 (Financial trend arrow direction bug — fixed Session 1; seed gap for gray arrow — seed adjusted Session 2; smart summary stale on date change — flagged for developers) |

### Recommendation

☒ **Accept** - All criteria met, ready for production
☐ **Accept with conditions** - Minor issues noted, can proceed
☐ **Reject** - Critical/major issues must be resolved

### Signatures

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Tester | Dmitri Spiropoulos | 2026-02-26 | Dmitri Spiropoulos, QA |
| Product Owner | | | |
| Tech Lead | | | |

---

## Appendix

### Test Data Reference

- **Assets with known repeat offender behavior**: Grinder 5 (consecutive OEE issues over 7 days), Grinder 1, Roaster 1
- **Standard downtime reason codes**: Mechanical, Changeover, Material Shortage, Quality Hold, Operator Unavailable, Planned Maintenance
- **Planned downtime reason codes**: Planned Maintenance, Changeover (shown with hatched pattern in Pareto chart)
- **Seed data coverage**: 14 assets with 7+ days of daily summaries and downtime events across morning, afternoon, and night shifts

### Environment Details

- **Backend**: FastAPI with Python 3.11+, Supabase (PostgreSQL)
- **Frontend**: Next.js 14+ with TypeScript, Tailwind CSS, Recharts 3.6+, Shadcn/UI
- **Caching**: 15-minute TTL on trend and Pareto data (if re-testing the same date within 15 minutes, cached data may be returned)
- **API Endpoints Used**:
  - `GET /api/v1/actions/daily?date={date}` - Action items with trend data
  - `GET /api/v1/downtime/pareto?date={date}&asset_id={id}` - Downtime reason code breakdown
  - `GET /api/v1/summary/smart?date={date}` - AI-generated smart summary with trend context

### Related Documentation

- Epic: `_bmad-output/planning-artifacts/epic-14.md`
- Stories: `_bmad-output/implementation-artifacts/stories/14-*.md`

---

*Generated by BMAD epic-execute workflow*
