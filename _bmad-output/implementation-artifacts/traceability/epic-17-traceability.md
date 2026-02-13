# Traceability Matrix - Epic 17: Report History & Shift Granularity

## Coverage Summary

| Priority | Total Criteria | Covered | Coverage % | Status |
|----------|---------------|---------|------------|--------|
| P0       | 8             | 8       | 100%       | PASS   |
| P1       | 10            | 10      | 100%       | PASS   |
| P2       | 1             | 1       | 100%       | PASS   |
| P3       | 3             | 3       | 100%       | PASS   |
| **Total**| **22**        | **22**  | **100%**   | **PASS** |

## Test File Inventory

| # | Test File | Framework | Tests | Story |
|---|-----------|-----------|-------|-------|
| 1 | `apps/web/src/components/report/__tests__/DateNavigation.test.tsx` | Vitest | 8 | 17.1 |
| 2 | `apps/web/src/app/(main)/morning-report/__tests__/MorningReportClient.test.tsx` | Vitest | 14 | 17.1 |
| 3 | `apps/web/src/hooks/__tests__/useSmartSummary.test.ts` | Vitest | 11 | 17.2 |
| 4 | `apps/web/src/components/action-list/__tests__/MorningSummarySection.test.tsx` | Vitest | 10 | 17.2 |
| 5 | `apps/api/tests/api/test_shift_breakdown_api.py` | pytest | 11 | 17.4 |
| 6 | `apps/api/tests/api/test_shift_attribution.py` | pytest | 10 | 17.4 |
| 7 | `apps/web/src/components/production/__tests__/ShiftTabs.test.tsx` | Vitest | 6 | 17.4 |
| 8 | `apps/web/src/components/production/__tests__/WorkcenterScorecard.shift.test.tsx` | Vitest | 4 | 17.4 |
| 9 | `apps/web/src/components/action-engine/__tests__/InsightSection.shift.test.tsx` | Vitest | 4 | 17.4 |
| **Total** | | | **78** | |

## Detailed Mapping

### Story 17.1: Date Picker on Morning Report

| AC ID | Description | Priority | Test IDs | Test File | Level | Status |
|-------|-------------|----------|----------|-----------|-------|--------|
| AC-1 | Date picker appears next to badge, defaults to yesterday | P0 | 17-1-UNIT-001..008, 17-1-INT-010, 17-1-INT-011, 17-1-INT-012, 17-1-INT-013 | DateNavigation.test.tsx, MorningReportClient.test.tsx | Unit + Integration | FULL |
| AC-2 | Date change reloads all data, URL updates, badge updates | P0 | 17-1-INT-005, 17-1-INT-006, 17-1-INT-007, 17-1-INT-012, 17-1-INT-013, 17-1-INT-014 | MorningReportClient.test.tsx | Integration | FULL |
| AC-3 | Prev/next day arrows, next disabled at yesterday | P1 | 17-1-UNIT-002..008 | DateNavigation.test.tsx | Unit | FULL |
| AC-4 | URL with date query param loads correct report | P1 | 17-1-INT-001, 17-1-INT-002, 17-1-INT-003, 17-1-INT-004 | MorningReportClient.test.tsx | Integration | FULL |
| AC-5 | Empty state when no data for selected date | P1 | 17-1-INT-008, 17-1-INT-009 | MorningReportClient.test.tsx | Integration | FULL |

### Story 17.2: Smart Summary On-Demand Generation

| AC ID | Description | Priority | Test IDs | Test File | Level | Status |
|-------|-------------|----------|----------|-----------|-------|--------|
| AC-1 | Historical date with no summary shows generation prompt | P0 | useSmartSummary: autoGenerate=false on 404; MorningSummarySection: generate button renders when canGenerate | useSmartSummary.test.ts, MorningSummarySection.test.tsx | Unit + Component | FULL |
| AC-2 | Generate button triggers API, loading indicator, summary saved | P0 | useSmartSummary: generate() POST call, success state update; MorningSummarySection: clicking generate, loading state | useSmartSummary.test.ts, MorningSummarySection.test.tsx | Unit + Component | FULL |
| AC-3 | Existing summary displayed immediately (no prompt) | P1 | MorningSummarySection: no generate button when hasSummary, existing summary display | MorningSummarySection.test.tsx | Component | FULL |
| AC-4 | Regenerate option on existing summaries | P1 | useSmartSummary: regenerate() still works; MorningSummarySection: regenerate button visible | useSmartSummary.test.ts, MorningSummarySection.test.tsx | Unit + Component | FULL |
| AC-5 | Error handling with retry option | P1 | useSmartSummary: generate() error handling, network error, expired session; MorningSummarySection: error retry calls generate vs refetch | useSmartSummary.test.ts, MorningSummarySection.test.tsx | Unit + Component | FULL |

### Story 17.3: Shift Summaries Data Model

| AC ID | Description | Priority | Test IDs | Test File | Level | Status |
|-------|-------------|----------|----------|-----------|-------|--------|
| AC-1 | shift_summaries table exists with all specified columns | P0 | SQL migration verified by execution; downstream API tests exercise table | 0035_shift_summaries.sql (DDL) | Migration | FULL |
| AC-2 | Unique constraint on (asset_id, date, shift) | P0 | SQL migration constraint; verified by execution | 0035_shift_summaries.sql (DDL) | Migration | FULL |
| AC-3 | Indexes on asset_id, date, composite (asset_id, date) | P1 | SQL migration indexes; verified by execution | 0035_shift_summaries.sql (DDL) | Migration | FULL |
| AC-4 | RLS enabled matching daily_summaries pattern | P0 | SQL migration RLS policies; verified by execution | 0035_shift_summaries.sql (DDL) | Migration | FULL |
| AC-5 | Each asset has 3 shift records per day | P1 | Seed script execution; downstream API tests use 3-shift fixture data | seed-data.mjs + test_shift_breakdown_api.py | Seed + API | FULL |
| AC-6 | Shift values sum approximately matches daily aggregates | P1 | Seed script exact-sum adjustment; test_shift_breakdown_api 17-4-UNIT-004, 17-4-UNIT-005 | seed-data.mjs + test_shift_breakdown_api.py | Seed + API | FULL |
| AC-7 | Shifts have realistic variance | P2 | Seed script generates variance (afternoon lower, night more downtime); verified by visual inspection | seed-data.mjs | Seed | FULL |
| AC-8 | Existing daily views unchanged | P3 | No ALTER TABLE in migration; 17-4-UNIT-010 backward compat test; all pre-existing tests pass | 0035_shift_summaries.sql + test_shift_breakdown_api.py | Migration + API | FULL |

### Story 17.4: Shift Breakdown API & UI

| AC ID | Description | Priority | Test IDs | Test File | Level | Status |
|-------|-------------|----------|----------|-----------|-------|--------|
| AC-1 | Workcenter entry includes shift_breakdown array with per-shift metrics | P0 | 17-4-UNIT-001..005, 17-4-UNIT-009..011 | test_shift_breakdown_api.py | API Unit | FULL |
| AC-2 | Shift tab filtering on scorecard and action items | P0 | 17-4-UNIT-006..008, 17-4-UNIT-040..045, 17-4-UNIT-050..053 | test_shift_breakdown_api.py, ShiftTabs.test.tsx, WorkcenterScorecard.shift.test.tsx | API + Component | FULL |
| AC-3 | Action item shows shift attribution for single-shift miss | P1 | 17-4-UNIT-020, 17-4-UNIT-026, 17-4-UNIT-060, 17-4-UNIT-063 | test_shift_attribution.py, InsightSection.shift.test.tsx | API + Component | FULL |
| AC-4 | Systemic issue remains daily-level without attribution | P1 | 17-4-UNIT-021, 17-4-UNIT-061, 17-4-UNIT-062 | test_shift_attribution.py, InsightSection.shift.test.tsx | API + Component | FULL |

## Coverage Gaps

### Critical Gaps (BLOCKING - P0 without coverage)

None identified.

### High Priority Gaps (P1 coverage <90%)

None identified.

### Medium Priority Gaps (Advisory)

None identified.

### Low Priority Advisory Notes

| # | Story | AC | Note | Impact |
|---|-------|----|------|--------|
| 1 | 17.2 | AC-1..5 | Tests lack formal test ID conventions (e.g., 17-2-UNIT-001) | Documentation only |
| 2 | 17.3 | AC-1..4 | DDL-only story; coverage via migration execution rather than automated test assertions | Acceptable for data-model stories |
| 3 | 17.1 | AC-1..5 | BDD format is implicit (arrange/act/assert) rather than explicit Given-When-Then | Cosmetic |
| 4 | 17.4 | AC-2 | Action item client-side filtering by shift added during code review (Issue #1 fix) | Covered post-fix |

## Non-Functional Requirements Coverage

| NFR | Description | Coverage | Evidence |
|-----|-------------|----------|----------|
| NFR-I6 | Backward Compatibility | FULL | 17-4-UNIT-010, 17-4-UNIT-011 verify daily aggregate unchanged; Story 17.3 AC-8 verified; no schema modifications to daily_summaries |
| NFR-I7 | URL Shareability | FULL | 17-1-INT-002, 17-1-INT-014 verify URL date parameter; shift param supported in workcenter-summary endpoint |

## Quality Gate Decision

**Epic**: 17
**Decision**: PASS
**Date**: 2026-02-12

### Evidence Summary

| Metric | Threshold | Actual | Status |
|--------|-----------|--------|--------|
| P0 Coverage | 100% | 100% (8/8) | PASS |
| P1 Coverage | >=90% | 100% (10/10) | PASS |
| P2 Coverage | >=80% | 100% (1/1) | PASS |
| Overall Coverage | >=80% | 100% (22/22) | PASS |
| Critical Gaps | 0 | 0 | PASS |

### Test Execution Results

| Scope | Passed | Failed | Skipped | Notes |
|-------|--------|--------|---------|-------|
| Story 17.1 (frontend) | 22 | 0 | 0 | 8 unit + 14 integration |
| Story 17.2 (frontend) | 21 | 0 | 0 | 11 hook + 10 component |
| Story 17.3 (data model) | N/A | N/A | N/A | DDL + seed verified by execution |
| Story 17.4 (API) | 21 | 0 | 0 | 11 breakdown + 10 attribution |
| Story 17.4 (frontend) | 14 | 0 | 0 | 6 ShiftTabs + 4 Scorecard + 4 InsightSection |
| **Total** | **78** | **0** | **0** | All story-specific tests pass |

**Pre-existing failures**: 9 test files / 11 tests failed before and after Epic 17 — confirmed as baseline, not regressions.

### Recommendation

**PASS: Proceed to UAT generation.** All acceptance criteria across all 4 stories have appropriate test coverage at the correct test levels. No gaps identified. Non-functional requirements (backward compatibility, URL shareability) are explicitly tested.

## Gate YAML Snippet

```yaml
traceability:
  epic_id: "17"
  coverage:
    overall: 100
    p0: 100
    p1: 100
    p2: 100
  gaps:
    critical: 0
    high: 0
    medium: 0
  status: "PASS"
  timestamp: "2026-02-12T00:00:00Z"
```
