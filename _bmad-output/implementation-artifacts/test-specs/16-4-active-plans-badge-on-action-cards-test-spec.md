TEST SPEC START
story_id: 16-4-active-plans-badge-on-action-cards
generated: 2026-02-12
```

**28 test specifications** covering **3 acceptance criteria**:

| AC | Coverage | Test Count |
|---|---|---|
| **AC1** - Single active plan badge | Badge rendering, info variant, click navigation, aria-label, role semantics, hook fetch/auth, client-side filtering, skip-when-empty | 11 specs (UNIT-001 through UNIT-011) |
| **AC2** - Multiple active plans summary | Summary count text, 3+ count, tooltip on hover, click navigation, info variant, aria-label | 6 specs (UNIT-012 through UNIT-017) |
| **AC3** - No badge for empty/completed | No plans, completed-only, verified-only, draft-only, mixed inactive, mixed active+inactive | 6 specs (UNIT-018 through UNIT-023) |
| **Integration** | InsightSection integration, InsightEvidenceCard prop passing, layout preservation, barrel export | 4 specs (INT-001 through INT-004) |
| **Loading/Error** | Loading state, API 500, network error, auth error, unmount cleanup | 5 specs (UNIT-024 through UNIT-028) |

Plus **8 edge cases** and **7 error scenarios** documented.

All test specs map to: `apps/web/src/components/action-engine/__tests__/ActivePlanBadge.test.tsx`

```json
{
  "status": "COMPLETE",
  "story_id": "16-4-active-plans-badge-on-action-cards",
  "summary": "Generated 28 test specifications for 3 acceptance criteria",
  "tests_added": 28
}
```

TEST SPEC COMPLETE: 16-4-active-plans-badge-on-action-cards - Generated 28 specifications
