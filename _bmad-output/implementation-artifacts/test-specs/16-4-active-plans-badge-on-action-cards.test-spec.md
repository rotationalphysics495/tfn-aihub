TEST SPEC START
story_id: 16-4-active-plans-badge-on-action-cards
generated: 2026-02-12

test_specifications:

## AC1: Given an action item's asset has an open/in-progress action plan, When the action card renders, Then a badge is displayed: "Action plan: {title} (due {date}, {status})" And clicking the badge opens the action plan detail.

### 16-4-active-plans-badge-on-action-cards-UNIT-001: Single active plan badge renders with title and due date
- Priority: P0
- Type: unit
- Given: An asset has one action plan with status "open", title "Fix valve leak", and due_date "2026-03-15"
- When: The ActivePlanBadge component renders with the assetId for that asset
- Then: A Badge with variant="info" is displayed containing text "Plan: Fix valve leak (due Mar 15, 2026)" or equivalent formatted date
- Data: mockFetch returns `{ items: [{ id: "ap-1", title: "Fix valve leak", due_date: "2026-03-15", status: "open" }], total_count: 1 }`

### 16-4-active-plans-badge-on-action-cards-UNIT-002: Single active plan badge renders for "in_progress" status
- Priority: P0
- Type: unit
- Given: An asset has one action plan with status "in_progress", title "Replace bearing", and due_date "2026-04-01"
- When: The ActivePlanBadge component renders with the assetId for that asset
- Then: A Badge with variant="info" is displayed containing the plan title and formatted due date
- Data: mockFetch returns `{ items: [{ id: "ap-2", title: "Replace bearing", due_date: "2026-04-01", status: "in_progress" }], total_count: 1 }`

### 16-4-active-plans-badge-on-action-cards-UNIT-003: Single plan badge uses info variant (blue styling)
- Priority: P0
- Type: unit
- Given: An asset has one active action plan
- When: The ActivePlanBadge component renders
- Then: The badge element has info variant class (contains "info" or "border-info-blue" in className)
- Data: Single open plan fixture

### 16-4-active-plans-badge-on-action-cards-UNIT-004: Clicking single plan badge navigates to action plan detail
- Priority: P0
- Type: unit
- Given: An asset has one active action plan with id "ap-uuid-123"
- When: The user clicks the ActivePlanBadge
- Then: router.push is called with "/action-plans/ap-uuid-123"
- Data: mockRouter.push spy, single plan with id "ap-uuid-123"

### 16-4-active-plans-badge-on-action-cards-UNIT-005: Single plan badge has ClipboardList icon
- Priority: P1
- Type: unit
- Given: An asset has one active action plan
- When: The ActivePlanBadge component renders
- Then: A ClipboardList icon (or equivalent plan icon) is rendered alongside the badge text
- Data: Single open plan fixture

### 16-4-active-plans-badge-on-action-cards-UNIT-006: Single plan badge has correct aria-label for accessibility
- Priority: P1
- Type: unit
- Given: An asset has one active action plan with title "Fix valve leak"
- When: The ActivePlanBadge component renders
- Then: The badge element has an aria-label containing "action plan" and the plan title (e.g., "Action plan: Fix valve leak")
- Data: Single open plan fixture

### 16-4-active-plans-badge-on-action-cards-UNIT-007: Single plan badge has role="link" semantics
- Priority: P1
- Type: unit
- Given: An asset has one active action plan
- When: The ActivePlanBadge component renders
- Then: The clickable badge element has role="link" or is rendered as an anchor/button with appropriate semantics
- Data: Single open plan fixture

### 16-4-active-plans-badge-on-action-cards-UNIT-008: Hook fetches action plans with correct API URL and auth
- Priority: P0
- Type: unit
- Given: A valid Supabase session with access_token "mock-token-abc" and assetId "asset-123"
- When: The useActiveActionPlans hook is initialized with assetId "asset-123"
- Then: fetch is called with URL matching `${API_BASE_URL}/api/v1/action-plans?asset_id=asset-123` and headers include `Authorization: Bearer mock-token-abc`
- Data: mockGetSession returns valid session, mockFetch spy

### 16-4-active-plans-badge-on-action-cards-UNIT-009: Hook filters response to only open and in_progress statuses client-side
- Priority: P0
- Type: unit
- Given: The API returns plans with statuses [open, in_progress, completed, draft, verified] for an asset
- When: The useActiveActionPlans hook resolves
- Then: The returned plans array contains only the "open" and "in_progress" plans, excluding "completed", "draft", and "verified"
- Data: mockFetch returns 5 plans with mixed statuses

### 16-4-active-plans-badge-on-action-cards-UNIT-010: Hook skips fetch when assetId is undefined
- Priority: P1
- Type: unit
- Given: The useActiveActionPlans hook is called with assetId = undefined
- When: The hook initializes
- Then: fetch is NOT called and plans is an empty array
- Data: No mockFetch setup needed

### 16-4-active-plans-badge-on-action-cards-UNIT-011: Hook skips fetch when assetId is empty string
- Priority: P1
- Type: unit
- Given: The useActiveActionPlans hook is called with assetId = ""
- When: The hook initializes
- Then: fetch is NOT called and plans is an empty array
- Data: No mockFetch setup needed

## AC2: Given an asset has multiple active action plans, When the action card renders, Then a summary badge shows: "2 active action plans" with a dropdown or link to view them.

### 16-4-active-plans-badge-on-action-cards-UNIT-012: Multiple plans badge renders summary count text
- Priority: P0
- Type: unit
- Given: An asset has 2 active action plans (1 open, 1 in_progress)
- When: The ActivePlanBadge component renders
- Then: A Badge with variant="info" is displayed containing text "2 active plans"
- Data: mockFetch returns `{ items: [{ id: "ap-1", title: "Plan A", status: "open", due_date: "2026-03-15" }, { id: "ap-2", title: "Plan B", status: "in_progress", due_date: "2026-04-01" }], total_count: 2 }`

### 16-4-active-plans-badge-on-action-cards-UNIT-013: Multiple plans badge shows correct count for 3+ plans
- Priority: P1
- Type: unit
- Given: An asset has 3 active action plans
- When: The ActivePlanBadge component renders
- Then: A Badge is displayed containing text "3 active plans"
- Data: mockFetch returns 3 plans with open/in_progress statuses

### 16-4-active-plans-badge-on-action-cards-UNIT-014: Multiple plans badge displays tooltip with plan titles on hover
- Priority: P0
- Type: unit
- Given: An asset has 2 active action plans with titles "Fix valve leak" and "Replace bearing"
- When: The user hovers over the summary badge (tooltip trigger)
- Then: A tooltip/popover appears listing the individual plan titles
- Data: 2 plan fixture with distinct titles

### 16-4-active-plans-badge-on-action-cards-UNIT-015: Clicking multiple plans badge navigates to filtered action plans view
- Priority: P0
- Type: unit
- Given: An asset with id "asset-uuid-456" has 2 active action plans
- When: The user clicks the summary badge
- Then: router.push is called with "/action-plans?asset_id=asset-uuid-456"
- Data: mockRouter.push spy, assetId "asset-uuid-456", 2 active plans

### 16-4-active-plans-badge-on-action-cards-UNIT-016: Multiple plans badge uses info variant (blue styling)
- Priority: P1
- Type: unit
- Given: An asset has multiple active action plans
- When: The ActivePlanBadge component renders
- Then: The badge element has info variant class (contains "info" or "border-info-blue" in className)
- Data: 2 active plans fixture

### 16-4-active-plans-badge-on-action-cards-UNIT-017: Multiple plans badge has correct aria-label
- Priority: P1
- Type: unit
- Given: An asset has 2 active action plans
- When: The ActivePlanBadge component renders
- Then: The badge has an aria-label indicating multiple active plans (e.g., "2 active action plans")
- Data: 2 active plans fixture

## AC3: Given an asset has no action plans or only completed/verified plans, When the action card renders, Then no action plan badge is shown.

### 16-4-active-plans-badge-on-action-cards-UNIT-018: No badge rendered when asset has no action plans
- Priority: P0
- Type: unit
- Given: An asset has no action plans at all
- When: The ActivePlanBadge component renders with the assetId for that asset
- Then: The component returns null and nothing is rendered (container.innerHTML is empty or no badge element exists)
- Data: mockFetch returns `{ items: [], total_count: 0 }`

### 16-4-active-plans-badge-on-action-cards-UNIT-019: No badge rendered when asset has only completed plans
- Priority: P0
- Type: unit
- Given: An asset has 2 action plans both with status "completed"
- When: The ActivePlanBadge component renders
- Then: The component returns null after client-side filtering excludes completed plans
- Data: mockFetch returns 2 plans with status "completed"

### 16-4-active-plans-badge-on-action-cards-UNIT-020: No badge rendered when asset has only verified plans
- Priority: P0
- Type: unit
- Given: An asset has 1 action plan with status "verified"
- When: The ActivePlanBadge component renders
- Then: The component returns null after client-side filtering excludes verified plans
- Data: mockFetch returns 1 plan with status "verified"

### 16-4-active-plans-badge-on-action-cards-UNIT-021: No badge rendered when asset has only draft plans
- Priority: P1
- Type: unit
- Given: An asset has 1 action plan with status "draft"
- When: The ActivePlanBadge component renders
- Then: The component returns null after client-side filtering excludes draft plans
- Data: mockFetch returns 1 plan with status "draft"

### 16-4-active-plans-badge-on-action-cards-UNIT-022: No badge rendered when asset has mix of completed, verified, and draft plans
- Priority: P1
- Type: unit
- Given: An asset has 3 plans with statuses "completed", "verified", and "draft"
- When: The ActivePlanBadge component renders
- Then: The component returns null since no active (open/in_progress) plans remain after filtering
- Data: mockFetch returns 3 plans with non-active statuses

### 16-4-active-plans-badge-on-action-cards-UNIT-023: Badge only counts active plans when asset has mix of active and inactive
- Priority: P0
- Type: unit
- Given: An asset has 4 plans: 1 open, 1 in_progress, 1 completed, 1 verified
- When: The ActivePlanBadge component renders
- Then: A badge renders showing "2 active plans" (only counting open + in_progress)
- Data: mockFetch returns 4 plans with mixed statuses, only 2 are active

## Integration Tests

### 16-4-active-plans-badge-on-action-cards-INT-001: ActivePlanBadge integrates correctly within InsightSection
- Priority: P0
- Type: integration
- Given: An InsightSection is rendered with assetId prop pointing to an asset with 1 active plan
- When: The component renders and the fetch resolves
- Then: The ActivePlanBadge appears in the context row alongside asset name, timestamp, and acknowledge button
- Data: Full InsightSection props with assetId, mockFetch returns 1 active plan

### 16-4-active-plans-badge-on-action-cards-INT-002: InsightEvidenceCard passes assetId to InsightSection
- Priority: P0
- Type: integration
- Given: An InsightEvidenceCard renders with item.asset.id = "asset-uuid-789"
- When: The component renders
- Then: The InsightSection receives assetId="asset-uuid-789" and the ActivePlanBadge fetches plans for that asset
- Data: Full ActionItem with asset.id = "asset-uuid-789", mockFetch returns 1 active plan

### 16-4-active-plans-badge-on-action-cards-INT-003: Badge does not disrupt existing card layout
- Priority: P1
- Type: integration
- Given: An InsightSection renders with all existing elements (priority, recommendation, asset name, timestamp, acknowledge button) and an active plan badge
- When: The component renders
- Then: All existing elements remain rendered and visible; the badge does not break the flex-wrap layout
- Data: Full InsightSection props, mockFetch returns 1 active plan

### 16-4-active-plans-badge-on-action-cards-INT-004: ActivePlanBadge is exported from barrel file
- Priority: P1
- Type: integration
- Given: The action-engine barrel file (index.ts) exists
- When: ActivePlanBadge is imported from '@/components/action-engine'
- Then: The import resolves successfully (the component is properly exported)
- Data: Dynamic import of barrel file

## Loading and Error State Tests

### 16-4-active-plans-badge-on-action-cards-UNIT-024: Loading state does not block card rendering
- Priority: P1
- Type: unit
- Given: The useActiveActionPlans hook is in loading state (fetch pending)
- When: The ActivePlanBadge component renders
- Then: Either a minimal skeleton/shimmer is shown inline, or nothing is rendered (no blocking spinner, no layout disruption)
- Data: mockFetch never resolves (pending promise)

### 16-4-active-plans-badge-on-action-cards-UNIT-025: API error state renders nothing (silent failure)
- Priority: P0
- Type: unit
- Given: The API call to fetch action plans fails with a 500 error
- When: The ActivePlanBadge component renders and the fetch rejects
- Then: The component renders null (no error message displayed, no badge shown) — silent failure since badge is informational
- Data: mockFetch returns `{ ok: false, status: 500, json: async () => ({ detail: "Internal Server Error" }) }`

### 16-4-active-plans-badge-on-action-cards-UNIT-026: Network error renders nothing (silent failure)
- Priority: P1
- Type: unit
- Given: The API call to fetch action plans throws a network error
- When: The ActivePlanBadge component renders and the fetch throws
- Then: The component renders null silently
- Data: mockFetch rejects with `new Error("Network error")`

### 16-4-active-plans-badge-on-action-cards-UNIT-027: Auth error (no session) renders nothing
- Priority: P1
- Type: unit
- Given: The Supabase session is null (unauthenticated)
- When: The useActiveActionPlans hook initializes
- Then: No fetch is made and the component renders null
- Data: mockGetSession returns `{ data: { session: null } }`

### 16-4-active-plans-badge-on-action-cards-UNIT-028: Hook cleanup prevents state update after unmount
- Priority: P1
- Type: unit
- Given: The ActivePlanBadge component is rendered then immediately unmounted
- When: The API fetch resolves after unmount
- Then: No React state update warning occurs (mountedRef prevents setState on unmounted component)
- Data: mockFetch with delayed resolution, unmount before resolve

edge_cases:
  - Asset has exactly 1 open and 0 in_progress plans → renders single plan badge (not summary)
  - Asset has exactly 0 open and 1 in_progress plan → renders single plan badge
  - Asset has many (10+) active plans → summary badge shows correct count "10 active plans"
  - Action plan has null due_date → badge handles gracefully (shows title without date, or "no due date")
  - Action plan has very long title → badge truncates or wraps appropriately without breaking layout
  - Asset ID changes dynamically (re-render with different assetId) → hook re-fetches for new asset
  - Multiple cards sharing same asset ID → each card independently fetches (per design, acceptable for MVP)
  - API returns plans with asset_id=null (plant-wide plans) → these are excluded from per-asset badge

error_scenarios:
  - API returns 401 Unauthorized → silent failure, no badge rendered
  - API returns 403 Forbidden → silent failure, no badge rendered
  - API returns 500 Internal Server Error → silent failure, no badge rendered
  - Network timeout → silent failure, no badge rendered
  - API returns malformed JSON → silent failure, no badge rendered
  - API returns unexpected schema (missing title/due_date fields) → graceful degradation or null render
  - Supabase getSession() throws → hook catches error, no fetch attempted, no badge rendered

test_file_mapping:
  - 16-4-active-plans-badge-on-action-cards-UNIT-*: apps/web/src/components/action-engine/__tests__/ActivePlanBadge.test.tsx
  - 16-4-active-plans-badge-on-action-cards-INT-*: apps/web/src/components/action-engine/__tests__/ActivePlanBadge.test.tsx
  - 16-4-active-plans-badge-on-action-cards-E2E-*: (not specified — no E2E tests in this spec; all tests are unit/integration using Vitest + Testing Library)

TEST SPEC END
