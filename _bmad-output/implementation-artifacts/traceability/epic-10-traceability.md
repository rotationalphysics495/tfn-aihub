# Traceability Matrix - Epic 10: Bug Fixes & Data Quality

**Generated**: 2026-02-11
**Epic**: 10 - Bug Fixes & Data Quality
**Stories**: 10.1, 10.2, 10.3
**Total Tests**: 59 (20 + 20 + 19)

---

## Coverage Summary

| Priority | Total Criteria | Covered | Coverage % | Status |
|----------|---------------|---------|------------|--------|
| P0       | 3             | 3       | 100%       | PASS   |
| P1       | 5             | 5       | 100%       | PASS   |
| P2       | 3             | 3       | 100%       | PASS   |
| P3       | 2             | 2       | 100%       | PASS   |
| **Total**| **13**        | **13**  | **100%**   | **PASS** |

---

## Detailed Mapping

### Story 10.1: Safety Alerts Auth Fix

**Test File**: `apps/web/src/hooks/__tests__/useSafetyAlerts.test.ts` (20 tests)

| AC ID | Description | Priority | Test IDs | Test File | Level | Status |
|-------|-------------|----------|----------|-----------|-------|--------|
| AC-1 | Bearer Token Auth Pattern: API request includes Bearer token, events display without 403 | P0 | UNIT-001, UNIT-002, UNIT-003 | hooks/__tests__/useSafetyAlerts.test.ts | Unit | FULL |
| AC-2 | Expired Session Handling: Fails gracefully, no confusing 403 error shown | P1 | UNIT-004, UNIT-005, UNIT-006 | hooks/__tests__/useSafetyAlerts.test.ts | Unit | FULL |
| AC-3 | Acknowledge Endpoint Auth Fix: POST includes Bearer token, succeeds without 403 | P1 | UNIT-007, UNIT-008, UNIT-009, UNIT-010 | hooks/__tests__/useSafetyAlerts.test.ts | Unit | FULL |
| AC-4 | Consistency With Other Hooks: Same pattern as useDailyActions, useLivePulse, useCostOfLoss | P2 | UNIT-011, UNIT-012, UNIT-013, UNIT-014, UNIT-015 | hooks/__tests__/useSafetyAlerts.test.ts | Unit | FULL |

**Edge Case Coverage** (5 additional tests): UNIT-016 (network error during getSession), UNIT-017 (acknowledge network error), UNIT-018 (polling with auth), UNIT-019 (API 500 handling), UNIT-020 (Content-Type preserved alongside Auth header)

---

### Story 10.2: Live Pulse Schema Fix

**Test Files**: `apps/api/tests/test_live_pulse_schema_fix.py` (20 tests) + `apps/api/tests/test_live_pulse_api.py` (18 pre-existing, all passing)

| AC ID | Description | Priority | Test IDs | Test File | Level | Status |
|-------|-------------|----------|----------|-----------|-------|--------|
| AC-1 | Successful API Response: Returns 200, no 500 from non-existent column | P0 | INT-001, INT-002, INT-003 | test_live_pulse_schema_fix.py | Int | FULL |
| AC-2 | Correct Column References: All column refs match actual live_snapshots schema | P0 | UNIT-001, UNIT-002, UNIT-003, INT-004, INT-005, INT-006 | test_live_pulse_schema_fix.py | Unit+Int | FULL |
| AC-3 | OEE Calculation Graceful Handling: OEE omitted or derived, defaults to 0.0 | P1 | UNIT-004, INT-007, INT-008, INT-009, INT-010 | test_live_pulse_schema_fix.py | Unit+Int | FULL |
| AC-4 | Existing Tests Pass: All test_live_pulse_api.py tests continue to pass | P3 | 18 tests | test_live_pulse_api.py | Int | FULL |

**Edge Case Coverage** (6 additional tests): UNIT-005 (.get() safe handling), INT-016 (empty snapshots), INT-017 (downtime absent), INT-018 (downtime backward compat), INT-019 (DB exception), INT-020 (latest snapshot dedup)

---

### Story 10.3: Cost of Loss Schema Fix

**Test Files**: `apps/api/tests/test_10_3_cost_of_loss_schema_fix.py` (19 tests) + `apps/api/tests/test_financial_api.py` (20 pre-existing, all passing)

| AC ID | Description | Priority | Test IDs | Test File | Level | Status |
|-------|-------------|----------|----------|-----------|-------|--------|
| AC-1 | Daily Summary Query Uses Correct Column: SELECT references waste_count, returns 200 | P0 | UNIT-001, UNIT-002, UNIT-003, INT-001, INT-002, INT-003 | test_10_3_cost_of_loss_schema_fix.py | Unit+Int | FULL |
| AC-2 | Financial Summary Query Uses Correct Column: waste_count in SELECT, correct aggregation | P1 | UNIT-004, UNIT-005, UNIT-006, INT-004 | test_10_3_cost_of_loss_schema_fix.py | Unit+Int | FULL |
| AC-3 | Financial Impact Service Uses Correct Column: waste_count in service SELECT and record.get() | P1 | UNIT-007, UNIT-008, UNIT-009, UNIT-010, UNIT-011 | test_10_3_cost_of_loss_schema_fix.py | Unit+Int | FULL |
| AC-4 | Existing Tests Updated To Match Schema: Mocks use waste_count, tests pass | P2 | UNIT-012, INT-005, INT-006 | test_10_3_cost_of_loss_schema_fix.py | Unit+Int | FULL |
| AC-5 | Agent Data Source Remains Correct: SupabaseDataSource already uses waste_count | P3 | UNIT-013 | test_10_3_cost_of_loss_schema_fix.py | Unit | FULL |

---

## Coverage Gaps

### Critical Gaps (BLOCKING - P0 without coverage)

None identified.

### High Priority Gaps (P1 coverage <90%)

None identified.

### Medium Priority Gaps (Advisory)

None identified.

### Low Priority Observations (Non-blocking)

| # | Observation | Impact |
|---|-------------|--------|
| 1 | No E2E tests across any story | Acceptable: all stories are backend schema fixes or single-file auth pattern fixes; unit + integration tests provide sufficient coverage for the bug-fix scope |
| 2 | No explicit P0/P1/P2/P3 priority markers in test files | Priorities assigned by TEA during traceability analysis based on criticality of acceptance criteria |
| 3 | Pre-existing test suite has 45 failures + 43 errors unrelated to Epic 10 | Out of scope; all Epic 10-specific tests pass |

---

## Quality Gate Decision

**Epic**: 10
**Decision**: PASS
**Date**: 2026-02-11

### Evidence Summary

| Metric | Threshold | Actual | Status |
|--------|-----------|--------|--------|
| P0 Coverage | 100% | 100% (3/3) | PASS |
| P1 Coverage | >=90% | 100% (5/5) | PASS |
| P2 Coverage | >=80% | 100% (3/3) | PASS |
| P3 Coverage | Advisory | 100% (2/2) | PASS |
| Overall Coverage | >=80% | 100% (13/13) | PASS |
| Critical Gaps | 0 | 0 | PASS |
| Total Tests | - | 59 (dedicated) + 38 (pre-existing) | - |

### Recommendation

**PASS: Proceed to UAT generation.** All acceptance criteria across all 3 stories have FULL test coverage. P0 criteria (core bug fixes) are 100% covered with both unit and integration tests. No gaps identified. The epic is ready for UAT.

---

## Test Inventory Summary

| Test File | Story | Tests | Level | All Pass |
|-----------|-------|-------|-------|----------|
| `apps/web/src/hooks/__tests__/useSafetyAlerts.test.ts` | 10.1 | 20 | Unit | Yes (20/20) |
| `apps/api/tests/test_live_pulse_schema_fix.py` | 10.2 | 20 | Unit+Int | Yes (20/20) |
| `apps/api/tests/test_live_pulse_api.py` | 10.2 | 18 | Int | Yes (18/18) |
| `apps/api/tests/test_10_3_cost_of_loss_schema_fix.py` | 10.3 | 19 | Unit+Int | Yes (19/19) |
| `apps/api/tests/test_financial_api.py` | 10.3 | 20 | Int | Yes (20/20) |
| **Total** | - | **97** | - | **Yes** |

---

## Gate YAML Snippet

```yaml
traceability:
  epic_id: "10"
  coverage:
    overall: 100
    p0: 100
    p1: 100
    p2: 100
    p3: 100
  gaps:
    critical: 0
    high: 0
    medium: 0
  criteria:
    total: 13
    covered: 13
  tests:
    dedicated: 59
    pre_existing: 38
    total: 97
  status: "PASS"
  timestamp: "2026-02-11T00:00:00Z"
```

---

## Acceptance Criteria Cross-Reference Index

| Story | AC | Description | Priority | Tests | Coverage |
|-------|-----|-------------|----------|-------|----------|
| 10.1 | AC-1 | Bearer Token Auth Pattern | P0 | 3 | FULL |
| 10.1 | AC-2 | Expired Session Handling | P1 | 3 | FULL |
| 10.1 | AC-3 | Acknowledge Endpoint Auth Fix | P1 | 4 | FULL |
| 10.1 | AC-4 | Consistency With Other Hooks | P2 | 5 | FULL |
| 10.2 | AC-1 | Successful API Response | P0 | 3 | FULL |
| 10.2 | AC-2 | Correct Column References | P0 | 6 | FULL |
| 10.2 | AC-3 | OEE Graceful Handling | P1 | 5 | FULL |
| 10.2 | AC-4 | Existing Tests Pass | P3 | 18 | FULL |
| 10.3 | AC-1 | Daily Summary Correct Column | P0 | 6 | FULL |
| 10.3 | AC-2 | Financial Summary Correct Column | P1 | 4 | FULL |
| 10.3 | AC-3 | Financial Impact Service Correct Column | P1 | 5 | FULL |
| 10.3 | AC-4 | Existing Tests Updated | P2 | 3 | FULL |
| 10.3 | AC-5 | Agent Data Source Correct | P3 | 1 | FULL |
