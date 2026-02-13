# Epic 13 Decision Log

This file tracks implementation decisions for context continuity across phases.

**Epic:** 13
**Started:** 2026-02-11 14:06:06

---


## DESIGN: 13-1-action-acknowledgment-backend
**Timestamp:** 2026-02-11 14:11:08

DESIGN START
story_id: 13-1-action-acknowledgment-backend

files_to_modify:
  - path: supabase/migrations/0027_action_acknowledgments.sql
    action: create
    purpose: Create action_acknowledgments table with columns, unique constraint, indexes, trigger, and RLS policies following the 0025_action_followups.sql pattern
  - path: apps/api/app/schemas/action.py
    action: modify
    purpose: Add AcknowledgmentCreate, AcknowledgmentResponse, AcknowledgmentInfo schemas and add Optional[AcknowledgmentInfo] acknowledgment field to ActionItem model
  - path: apps/api/app/api/actions.py
    action: modify
    purpose: Add POST /{action_id}/acknowledge endpoint with upsert logic, auth dependency, and 201/200 status codes. Update GET /daily to pass user_id for enrichment
  - path: apps/api/app/services/action_engine.py
    action: modify
    purpose: Add _load_acknowledgments() method and add optional user_id param to generate_action_list() with post-cache enrichment
  - path: apps/api/tests/test_actions_api.py
    action: modify
    purpose: Add TestAcknowledgeEndpoint class testing 201 create, 200 upsert, 401 unauth, enrichment in daily response
  - path: apps/api/tests/test_action_engine.py
    action: modify
    purpose: Add tests for _load_acknowledgments() and acknowledgment enrichment in generate_action_list()

patterns_to_use:
  - migration_pattern: Follow 0025_action_followups.sql exactly — CREATE TABLE, CREATE INDEX (idx_{table}_{col}), CREATE TRIGGER reusing update_updated_at_column(), ALTER TABLE ENABLE RLS, CREATE POLICY for authenticated/service_role
  - auth_dependency: Use Depends(get_current_user) returning CurrentUser with id/email/role, same as all existing endpoints in actions.py
  - supabase_query: Use client.table("action_acknowledgments").upsert({...}, on_conflict="action_item_id,user_id,report_date").execute() for idempotent create/update
  - schema_pattern: Pydantic V2 BaseModel with ConfigDict, Field, Optional[str] = None for optional fields
  - cache_bypass_enrichment: Acknowledgments are user-specific; enrichment happens AFTER cache retrieval so the shared action list cache is not polluted with per-user data
  - test_mock_pattern: patch('app.api.actions.get_action_engine') for API tests, MagicMock/AsyncMock for engine mocking, mock_verify_jwt fixture for auth, TestClient for HTTP assertions

dependencies:
  - fastapi: installed (0.109+)
  - supabase-py: installed (2.0+)
  - pydantic: installed (V2)
  - pytest: installed (dev dependency)

acceptance_criteria_mapping:
  - AC1 (Acknowledge Endpoint): apps/api/app/api/actions.py — new POST /{action_id}/acknowledge endpoint; apps/api/app/schemas/action.py — AcknowledgmentCreate (request body), AcknowledgmentResponse (response model); supabase/migrations/0027 — table definition
  - AC2 (Upsert Behavior): apps/api/app/api/actions.py — upsert via Supabase .upsert() with on_conflict; differentiate 201 vs 200 by querying existence first OR by checking created_at vs acknowledged_at timestamps in the returned record
  - AC3 (Daily Actions Enrichment): apps/api/app/services/action_engine.py — _load_acknowledgments() method, generate_action_list() user_id parameter, post-cache enrichment loop; apps/api/app/schemas/action.py — AcknowledgmentInfo schema, ActionItem.acknowledgment Optional field; apps/api/app/api/actions.py — pass current_user.id to generate_action_list()
  - AC4 (Authentication Required): apps/api/app/api/actions.py — Depends(get_current_user) on the POST endpoint, inheriting the existing HTTPBearer pattern from app.core.security
  - AC5 (RLS Enforcement): supabase/migrations/0027 — RLS policies: SELECT/INSERT/UPDATE for authenticated where user_id = auth.uid(), ALL for service_role

risks:
  - 201_vs_200_differentiation: Supabase .upsert() doesn't indicate whether the row was inserted or updated. Mitigation — first SELECT to check existence before upserting, or compare created_at with acknowledged_at in the returned row (if acknowledged_at > created_at by some threshold, it was an update). Simplest approach is a pre-check SELECT count.
  - action_id_stability: Action IDs are generated at runtime with random hex (action-{category}-{uuid.hex[:12]}), so the same action may get different IDs across cache rebuilds. This is an existing design constraint — acknowledgments are tied to specific generated IDs. If the cache is invalidated and actions regenerate with new IDs, existing acknowledgments won't match. Mitigation — this is documented as expected behavior; acknowledge within the same cache lifetime. Future story may address ID stability.
  - backward_compatibility: Adding acknowledgment: Optional[AcknowledgmentInfo] = None to ActionItem must default to None so existing serialization is unchanged. All existing tests that construct ActionItem without this field must continue to work.
  - cache_key_exclusion: user_id MUST NOT be added to the action list cache key. The enrichment step must run after cache retrieval. Mitigation — code placement is clearly after cache check/return in generate_action_list().

estimated_test_files:
  - apps/api/tests/test_actions_api.py: TestAcknowledgeEndpoint — POST creates 201, POST upsert returns 200, POST without auth returns 401, note is optional, report_date defaults to T-1, enrichment visible in GET /daily response
  - apps/api/tests/test_action_engine.py: Test _load_acknowledgments() returns correct dict mapping, test generate_action_list() enriches actions when user_id provided, test generate_action_list() returns null acknowledgments when user_id is None or no acks exist

implementation_order:
  1. Create migration file supabase/migrations/0027_action_acknowledgments.sql with table, unique constraint, indexes, trigger, and RLS policies (Task 1)
  2. Add Pydantic schemas (AcknowledgmentCreate, AcknowledgmentResponse, AcknowledgmentInfo) to apps/api/app/schemas/action.py and add Optional[AcknowledgmentInfo] field to ActionItem (Task 2)
  3. Add _load_acknowledgments() method to ActionEngine in apps/api/app/services/action_engine.py (Task 4 partial)
  4. Update generate_action_list() signature to accept optional user_id and add post-cache enrichment loop (Task 4)
  5. Add POST /{action_id}/acknowledge endpoint to apps/api/app/api/actions.py with upsert logic and 201/200 differentiation (Task 3)
  6. Update GET /daily endpoint in actions.py to pass current_user.id to generate_action_list() for enrichment (Task 4 completion)
  7. Add acknowledge endpoint tests to apps/api/tests/test_actions_api.py (Task 5 partial)
  8. Add acknowledgment enrichment tests to apps/api/tests/test_action_engine.py (Task 5 completion)
  9. Run full test suite to verify no regressions in existing tests
DESIGN END

---

## DESIGN: 13-2-action-acknowledgment-ui
**Timestamp:** 2026-02-11 14:32:53

DESIGN START
story_id: 13-2-action-acknowledgment-ui

files_to_modify:
  - path: apps/web/src/hooks/useDailyActions.ts
    action: modify
    purpose: Add optional `acknowledgment` field to the `ActionItem` interface (line 31-47) to match the backend's enriched response from Story 13.1 (AcknowledgmentInfo with acknowledged_by, acknowledged_at, note)
  - path: apps/web/src/components/action-engine/types.ts
    action: modify
    purpose: Add `AcknowledgmentInfo` type and optional `acknowledgment` field to the component-level `ActionItem` interface so cards can receive acknowledgment data
  - path: apps/web/src/components/action-engine/transformers.ts
    action: modify
    purpose: Pass through the `acknowledgment` field from API ActionItem to component ActionItem during transformation in `transformAPIActionItem()`
  - path: apps/web/src/hooks/useActionAcknowledgment.ts
    action: create
    purpose: New hook managing acknowledgment state — optimistic UI updates, POST to /api/v1/actions/{action_id}/acknowledge with Bearer token auth, error rollback, and toast feedback. Consumes initial acknowledgment state from useDailyActions data.
  - path: apps/web/src/components/action-engine/InsightSection.tsx
    action: modify
    purpose: Add acknowledge button to the context row (before the Assign button). Accept new props: `isAcknowledged`, `acknowledgedAt`, `onAcknowledge`. Render CheckCircle2/Circle icon toggle with "Mark Reviewed"/"Reviewed" labels.
  - path: apps/web/src/components/action-engine/InsightEvidenceCard.tsx
    action: modify
    purpose: Accept new `acknowledgment` prop and `onAcknowledge` callback. Pass them to InsightSection. Apply muted styling (opacity-60, muted border color) to the card when acknowledged.
  - path: apps/web/src/components/action-engine/InsightEvidenceCardList.tsx
    action: modify
    purpose: Integrate useActionAcknowledgment hook. Track acknowledged count vs total. Render "All items reviewed" success banner. Pass acknowledgment state and callbacks down through ActionCardList to each card.
  - path: apps/web/src/components/action-engine/ActionCardList.tsx
    action: modify
    purpose: Accept new `acknowledgments` map and `onAcknowledge` callback props. Pass them to each InsightEvidenceCard. (ActionCardList is the intermediate rendering layer between InsightEvidenceCardList and InsightEvidenceCard.)
  - path: apps/web/src/components/action-engine/index.ts
    action: modify
    purpose: Export the new AcknowledgmentInfo type from types.ts
  - path: apps/web/src/hooks/__tests__/useActionAcknowledgment.test.ts
    action: create
    purpose: Unit tests for the hook: optimistic update, rollback on API error, initial state from data, auth token usage
  - path: apps/web/src/components/action-engine/__tests__/InsightEvidenceCard.ack.test.tsx
    action: create
    purpose: Component tests for acknowledged/unacknowledged states, muted styling, button interactions
  - path: apps/web/src/components/action-engine/__tests__/AllItemsReviewed.test.tsx
    action: create
    purpose: Component tests for "All items reviewed" banner rendering when all items are acknowledged

patterns_to_use:
  - bearer_token_auth: Use `createClient()` from `@/lib/supabase/client` → `supabase.auth.getSession()` → `Authorization: Bearer ${session.access_token}`. Exact pattern from `useDailyActions.ts` lines 122-149 and `AssignFollowUpDialog.tsx` lines 63-72.
  - optimistic_update: Save previous acknowledgment map, immediately set new state, call API, rollback on failure. Pattern documented in story dev notes.
  - icon_button_toggle: Ghost Button with Lucide icon toggle (Circle → CheckCircle2) following the same styling pattern as the existing Assign button in InsightSection.tsx lines 127-145. No Checkbox component needed.
  - conditional_card_styling: Use existing `cn()` utility in InsightEvidenceCard to add `opacity-60` and muted border classes when acknowledged, same pattern as the existing hover/focus styling on lines 57-70.
  - test_mock_pattern: Mock `createClient` and `global.fetch` with `vi.fn()`, use `renderHook` / `act` / `waitFor` from Testing Library. Pattern from `useScheduleAttainment.test.ts`.
  - component_test_pattern: Use `render()` + `fireEvent.click()` from React Testing Library. Mock hook return values.
  - props_drilling_with_callbacks: Follow existing `onAssign` callback pattern — InsightEvidenceCardList → ActionCardList → InsightEvidenceCard → InsightSection, same as how assign dialog currently works.

dependencies:
  - lucide-react: installed (CheckCircle2, Circle already available; CheckCircle2 already imported in ActionCardList.tsx)
  - @/components/ui/button: installed (Button component)
  - @/components/ui/tooltip: installed (for timestamp hover tooltip)
  - @/lib/supabase/client: installed (createClient)
  - vitest: installed (dev dependency)
  - @testing-library/react: installed (dev dependency)

acceptance_criteria_mapping:
  - AC1 (Unacknowledged button on each card): InsightSection.tsx — new acknowledge button with Circle icon and "Mark Reviewed" label in the context row. InsightEvidenceCard.tsx — passes `isAcknowledged=false` by default. useActionAcknowledgment.ts — initializes acknowledgment map from useDailyActions data (items with null acknowledgment → unacknowledged).
  - AC2 (Optimistic acknowledge with visual change): useActionAcknowledgment.ts — `acknowledge(actionId)` immediately updates local state map, calls `POST /api/v1/actions/{action_id}/acknowledge`, rolls back on error. InsightSection.tsx — button switches to CheckCircle2 icon, green color, "Reviewed" label with timestamp. InsightEvidenceCard.tsx — card applies `opacity-60` and muted left-border when acknowledged.
  - AC3 (Preserved state on reload): useDailyActions.ts — ActionItem interface includes `acknowledgment` field. transformers.ts — passes `acknowledgment` through to component types. useActionAcknowledgment.ts — initializes state from the `acknowledgment` field already present on each action item from the GET /daily response (enriched by Story 13.1 backend).
  - AC4 (All items reviewed summary): InsightEvidenceCardList.tsx — tracks `acknowledgedCount` vs `totalCount`. When all acknowledged and count > 0, renders success banner with green styling, CheckCircle2 icon, "All items reviewed" text, and "N/N reviewed" count.

risks:
  - action_id_instability: Action IDs regenerate on cache rebuild (documented in 13.1 decisions). If the cache is invalidated between page loads, previously acknowledged items may not match. Mitigation: This is documented expected behavior. The daily actions endpoint returns fresh acknowledgment state on each load, so the UI will correctly show unacknowledged for new IDs.
  - race_condition_rapid_clicks: User rapidly clicking acknowledge on the same card could fire multiple POSTs. Mitigation: The hook will track in-flight request state per action ID and debounce/ignore duplicate calls. The backend upsert is idempotent so worst case is redundant requests.
  - transformer_field_passthrough: The `transformAPIActionItem` function in transformers.ts currently doesn't handle `acknowledgment`. If not updated, the field will be silently dropped. Mitigation: Explicitly add `acknowledgment` field passthrough in the transformer.
  - props_threading_depth: Acknowledgment state needs to flow from InsightEvidenceCardList → ActionCardList → InsightEvidenceCard → InsightSection (4 levels). Mitigation: Use a simple Map<string, AcknowledgmentInfo> and callback pattern, same depth as existing `onAssign`. Considered React Context but the prop drilling is manageable and matches existing patterns.
  - stale_closure_in_optimistic_update: The optimistic update pattern must use functional setState to avoid stale closures when multiple items are acknowledged in quick succession. Mitigation: Use `setState(prev => ...)` pattern consistently.

estimated_test_files:
  - apps/web/src/hooks/__tests__/useActionAcknowledgment.test.ts: Test optimistic state update (acknowledge sets state immediately), rollback on fetch failure (state reverts), initial state derivation from action items data, Bearer token auth header sent, error handling for expired session.
  - apps/web/src/components/action-engine/__tests__/InsightEvidenceCard.ack.test.tsx: Test unacknowledged card renders Circle icon with "Mark Reviewed" label, acknowledged card renders CheckCircle2 with "Reviewed" label and timestamp, acknowledged card has `opacity-60` class, click handler calls onAcknowledge with correct action ID, aria-label is set correctly.
  - apps/web/src/components/action-engine/__tests__/AllItemsReviewed.test.tsx: Test banner renders when all items acknowledged (N/N), banner does not render when some items unacknowledged, banner does not render when zero total items, banner shows correct count text.

implementation_order:
  1. Modify `apps/web/src/hooks/useDailyActions.ts` — add optional `acknowledgment` field to `ActionItem` interface to match backend AcknowledgmentInfo (acknowledged_by, acknowledged_at, note). No logic changes.
  2. Modify `apps/web/src/components/action-engine/types.ts` — add `AcknowledgmentInfo` interface and optional `acknowledgment` field to the component-level `ActionItem` interface.
  3. Modify `apps/web/src/components/action-engine/transformers.ts` — pass through `acknowledgment` field from API ActionItem to component ActionItem in `transformAPIActionItem()`.
  4. Modify `apps/web/src/components/action-engine/index.ts` — export `AcknowledgmentInfo` type.
  5. Create `apps/web/src/hooks/useActionAcknowledgment.ts` — implement hook with: state map of action_id → AcknowledgmentInfo, `initFromItems(items)` to seed state from fetched data, `acknowledge(actionId)` with optimistic update + POST + rollback, `isAcknowledged(actionId)` / `getAcknowledgment(actionId)` accessors, `acknowledgedCount` / `totalCount` computed values.
  6. Modify `apps/web/src/components/action-engine/InsightSection.tsx` — add `isAcknowledged`, `acknowledgedAt`, `onAcknowledge` props to InsightSectionProps. Add acknowledge button to context row before the Assign button, using ghost Button + Circle/CheckCircle2 icon toggle + conditional green styling + timestamp display.
  7. Modify `apps/web/src/components/action-engine/InsightEvidenceCard.tsx` — add `acknowledgment` and `onAcknowledge` props to InsightEvidenceCardProps. Pass `isAcknowledged` and `acknowledgedAt` to InsightSection. Apply conditional `opacity-60` and muted border color to the card when acknowledged.
  8. Modify `apps/web/src/components/action-engine/ActionCardList.tsx` — add `acknowledgments` (Map<string, AcknowledgmentInfo>) and `onAcknowledge` callback to ActionCardListProps. Pass them to each InsightEvidenceCard in the render loop.
  9. Modify `apps/web/src/components/action-engine/InsightEvidenceCardList.tsx` — integrate `useActionAcknowledgment` hook. Initialize from `transformedItems`. Pass acknowledgments map and callback down to ActionCardList. Add "All items reviewed" banner above ActionCardList when `acknowledgedCount === totalCount && totalCount > 0`.
  10. Create `apps/web/src/hooks/__tests__/useActionAcknowledgment.test.ts` — unit tests for the hook.
  11. Create `apps/web/src/components/action-engine/__tests__/InsightEvidenceCard.ack.test.tsx` — component tests for acknowledge button states and card styling.
  12. Create `apps/web/src/components/action-engine/__tests__/AllItemsReviewed.test.tsx` — component tests for the summary banner.
  13. Run full test suite (`cd apps/web && npm run test`) to verify no regressions.
DESIGN END

---

## TEST_SPEC: 13-2-action-acknowledgment-ui
**Timestamp:** 2026-02-11 14:35:51

TEST SPEC START
story_id: 13-2-action-acknowledgment-ui
generated: 2026-02-11

test_specifications:

## AC1: Given the morning report displays action items, When each action card renders, Then it shows an acknowledgment button/checkbox in an unacknowledged state.

### 13-2-action-acknowledgment-ui-UNIT-001: Unacknowledged action card renders Circle icon with "Mark Reviewed" label
- Priority: P0
- Type: unit
- Given: An InsightEvidenceCard renders with an action item that has no acknowledgment (acknowledgment is null/undefined)
- When: The card is rendered
- Then: A button with a Circle icon is visible, the button label reads "Mark Reviewed", the button has variant="ghost" and size="sm" styling, and the icon is not green-colored
- Data: ActionItem with `acknowledgment: null`, standard test fixture for other fields

### 13-2-action-acknowledgment-ui-UNIT-002: Acknowledge button is present in InsightSection context row
- Priority: P0
- Type: unit
- Given: An InsightSection component renders with `isAcknowledged=false`
- When: The component renders
- Then: The acknowledge button appears in the context row alongside the asset name, timestamp, and Assign button, positioned before the Assign button
- Data: Standard InsightSectionProps with `isAcknowledged: false`, `onAcknowledge: vi.fn()`

### 13-2-action-acknowledgment-ui-UNIT-003: Acknowledge button has correct aria-label for accessibility
- Priority: P1
- Type: unit
- Given: An InsightSection renders with `isAcknowledged=false`
- When: The component renders
- Then: The acknowledge button has an appropriate `aria-label` (e.g., "Mark action as reviewed") and is keyboard-focusable
- Data: Standard InsightSectionProps with `isAcknowledged: false`

### 13-2-action-acknowledgment-ui-UNIT-004: Acknowledge button is keyboard accessible (Enter and Space activate)
- Priority: P1
- Type: unit
- Given: An InsightSection with an unacknowledged action item
- When: The user focuses the acknowledge button and presses Enter or Space
- Then: The `onAcknowledge` callback is invoked
- Data: Standard InsightSectionProps, mock `onAcknowledge` callback

### 13-2-action-acknowledgment-ui-UNIT-005: useActionAcknowledgment hook initializes all items as unacknowledged when no prior acknowledgments exist
- Priority: P0
- Type: unit
- Given: The hook receives a list of action items where all have `acknowledgment: null`
- When: The hook initializes
- Then: `isAcknowledged(actionId)` returns false for every item, `acknowledgedCount` is 0, and `totalCount` equals the number of items
- Data: Array of 3 ActionItems with `acknowledgment: null`

### 13-2-action-acknowledgment-ui-UNIT-006: Each card in ActionCardList receives acknowledgment state and callback
- Priority: P1
- Type: unit
- Given: ActionCardList renders with items and an acknowledgments map where all are unacknowledged
- When: The list renders
- Then: Each InsightEvidenceCard receives `acknowledgment={null}` and a valid `onAcknowledge` callback prop
- Data: 3 ActionItems, empty acknowledgments map, mock `onAcknowledge`


## AC2: Given the user clicks the acknowledge button on an action card, When the acknowledgment API is called, Then the button immediately updates to "acknowledged" state (optimistic UI), And the card visually changes (e.g., muted styling or checkmark overlay), And a timestamp shows when it was acknowledged.

### 13-2-action-acknowledgment-ui-UNIT-007: Clicking acknowledge triggers optimistic UI update immediately
- Priority: P0
- Type: unit
- Given: The useActionAcknowledgment hook is initialized with unacknowledged items
- When: `acknowledge(actionId)` is called
- Then: `isAcknowledged(actionId)` returns true immediately (before API resolves), `getAcknowledgment(actionId)` returns an object with `acknowledged_at` timestamp, and `acknowledgedCount` increments by 1
- Data: ActionItem with id "action-1", mock fetch that delays resolution

### 13-2-action-acknowledgment-ui-UNIT-008: Acknowledge calls POST API with correct endpoint and Bearer token
- Priority: P0
- Type: unit
- Given: The hook has a valid Supabase session with access_token "mock-token-123"
- When: `acknowledge("action-42")` is called
- Then: `fetch` is called with URL `{API_URL}/api/v1/actions/action-42/acknowledge`, method POST, headers include `Authorization: Bearer mock-token-123` and `Content-Type: application/json`
- Data: Mock session with `access_token: 'mock-token-123'`, mock fetch resolving successfully

### 13-2-action-acknowledgment-ui-UNIT-009: Acknowledged card button shows CheckCircle2 icon and "Reviewed" label
- Priority: P0
- Type: unit
- Given: An InsightSection renders with `isAcknowledged=true` and `acknowledgedAt="2026-02-11T08:30:00Z"`
- When: The component renders
- Then: The button displays a CheckCircle2 icon (filled), the label reads "Reviewed", and the button text is styled with green color classes (`text-green-600` or `text-green-400`)
- Data: InsightSectionProps with `isAcknowledged: true`, `acknowledgedAt: "2026-02-11T08:30:00Z"`

### 13-2-action-acknowledgment-ui-UNIT-010: Acknowledged card applies muted visual styling
- Priority: P0
- Type: unit
- Given: An InsightEvidenceCard renders with a non-null `acknowledgment` prop
- When: The card renders
- Then: The card's root element has `opacity-60` class applied, and the left border color is muted compared to the unacknowledged state
- Data: ActionItem with acknowledgment `{ user_id: "u1", acknowledged_at: "2026-02-11T08:30:00Z", note: null }`

### 13-2-action-acknowledgment-ui-UNIT-011: Acknowledged card displays timestamp of acknowledgment
- Priority: P0
- Type: unit
- Given: An InsightSection with `isAcknowledged=true` and `acknowledgedAt="2026-02-11T08:30:00Z"`
- When: The component renders
- Then: A timestamp is displayed below the button in `text-sm text-muted-foreground` styling showing the formatted time (e.g., "8:30 AM")
- Data: InsightSectionProps with `acknowledgedAt: "2026-02-11T08:30:00Z"`

### 13-2-action-acknowledgment-ui-UNIT-012: Optimistic update rolls back on API failure
- Priority: P0
- Type: unit
- Given: The hook has an unacknowledged item "action-1" and the API will return an error (e.g., 500)
- When: `acknowledge("action-1")` is called and the API call rejects/fails
- Then: The optimistic state is rolled back — `isAcknowledged("action-1")` returns false, `acknowledgedCount` returns to original value
- Data: ActionItem with id "action-1", mock fetch rejecting with 500 status

### 13-2-action-acknowledgment-ui-UNIT-013: Error toast is shown when acknowledgment API fails
- Priority: P1
- Type: unit
- Given: The hook has an unacknowledged item and the API returns an error
- When: `acknowledge(actionId)` is called and the API fails
- Then: A user-visible error notification/toast is triggered indicating the acknowledgment failed
- Data: Mock fetch returning `{ ok: false, status: 500 }`

### 13-2-action-acknowledgment-ui-UNIT-014: Clicking an already-acknowledged button does not send duplicate API call
- Priority: P1
- Type: unit
- Given: The hook has item "action-1" already in acknowledged state
- When: `acknowledge("action-1")` is called again
- Then: No additional API call is made (fetch call count does not increase), OR the request is handled idempotently
- Data: ActionItem "action-1" already acknowledged

### 13-2-action-acknowledgment-ui-UNIT-015: Rapid successive clicks on acknowledge button are debounced
- Priority: P1
- Type: unit
- Given: The hook has an unacknowledged item "action-1" with an in-flight acknowledge request
- When: `acknowledge("action-1")` is called again before the first request completes
- Then: Only one API call is made (not two), preventing race conditions
- Data: ActionItem "action-1", mock fetch with delayed resolution

### 13-2-action-acknowledgment-ui-UNIT-016: Multiple items can be acknowledged in quick succession without stale closure issues
- Priority: P1
- Type: unit
- Given: The hook has 3 unacknowledged items ("action-1", "action-2", "action-3")
- When: `acknowledge("action-1")`, `acknowledge("action-2")`, `acknowledge("action-3")` are called in rapid succession
- Then: All three items are marked as acknowledged (no stale state overwrites), `acknowledgedCount` equals 3, all 3 API calls are made
- Data: 3 ActionItems, mock fetch resolving successfully for each

### 13-2-action-acknowledgment-ui-UNIT-017: Acknowledge button click handler calls onAcknowledge with correct action ID
- Priority: P0
- Type: unit
- Given: An InsightEvidenceCard renders with action item id "action-42" and a mock `onAcknowledge` callback
- When: The user clicks the acknowledge button
- Then: The `onAcknowledge` callback is called with argument "action-42"
- Data: ActionItem with `id: "action-42"`, mock `onAcknowledge: vi.fn()`

### 13-2-action-acknowledgment-ui-UNIT-018: Acknowledgment request includes optional note in body
- Priority: P2
- Type: unit
- Given: The hook is initialized and the API contract supports an optional note field
- When: `acknowledge(actionId)` is called (without explicit note)
- Then: The POST body is valid JSON (e.g., `{}` or `{ note: undefined }`), and when a note is provided, it is included in the body as `{ note: "some note" }`
- Data: Mock fetch, action ID "action-1"


## AC3: Given an action item was previously acknowledged, When the morning report reloads, Then the acknowledged state is preserved from the database.

### 13-2-action-acknowledgment-ui-UNIT-019: Hook initializes acknowledged state from action items data
- Priority: P0
- Type: unit
- Given: The useDailyActions hook returns action items where some have non-null `acknowledgment` fields (e.g., 2 out of 5 acknowledged)
- When: useActionAcknowledgment initializes from this data
- Then: `isAcknowledged(id)` returns true for the 2 acknowledged items and false for the 3 unacknowledged items, `acknowledgedCount` is 2, `totalCount` is 5
- Data: 5 ActionItems — 2 with `acknowledgment: { user_id: "u1", acknowledged_at: "2026-02-11T07:00:00Z" }`, 3 with `acknowledgment: null`

### 13-2-action-acknowledgment-ui-UNIT-020: Previously acknowledged card renders in acknowledged visual state on reload
- Priority: P0
- Type: unit
- Given: An InsightEvidenceCard receives an action item with `acknowledgment: { user_id: "u1", acknowledged_at: "2026-02-11T07:00:00Z", note: null }`
- When: The card renders
- Then: The card shows the CheckCircle2 icon, "Reviewed" label, muted opacity, and the acknowledgment timestamp — all without requiring a user click
- Data: ActionItem with pre-populated acknowledgment object

### 13-2-action-acknowledgment-ui-UNIT-021: Acknowledged timestamp from database is displayed correctly
- Priority: P1
- Type: unit
- Given: An action item was acknowledged at "2026-02-11T14:22:00Z" (stored in database)
- When: The card renders with this acknowledgment data on page reload
- Then: The timestamp is displayed in a human-readable format (e.g., "2:22 PM") in `text-sm text-muted-foreground` styling
- Data: ActionItem with `acknowledgment.acknowledged_at: "2026-02-11T14:22:00Z"`

### 13-2-action-acknowledgment-ui-UNIT-022: Transformer passes acknowledgment field from API response to component type
- Priority: P0
- Type: unit
- Given: The API response includes an action item with `acknowledgment: { user_id: "u1", acknowledged_at: "...", note: null }`
- When: `transformAPIActionItem()` processes this item
- Then: The resulting component-level ActionItem includes the `acknowledgment` field with the same data intact
- Data: API ActionItem with acknowledgment field populated

### 13-2-action-acknowledgment-ui-UNIT-023: Transformer handles missing acknowledgment field gracefully
- Priority: P1
- Type: unit
- Given: The API response includes an action item without an `acknowledgment` field (null or undefined)
- When: `transformAPIActionItem()` processes this item
- Then: The resulting component-level ActionItem has `acknowledgment: null` (or undefined), and no error is thrown
- Data: API ActionItem without acknowledgment field

### 13-2-action-acknowledgment-ui-INT-001: InsightEvidenceCardList loads and displays mix of acknowledged and unacknowledged items
- Priority: P0
- Type: integration
- Given: useDailyActions returns 4 action items — 2 acknowledged, 2 unacknowledged
- When: InsightEvidenceCardList mounts and renders
- Then: 2 cards display in acknowledged state (muted, CheckCircle2, "Reviewed"), 2 cards display in unacknowledged state (Circle, "Mark Reviewed"), and the "All items reviewed" banner is NOT shown
- Data: Mock useDailyActions returning 4 items with mixed acknowledgment states


## AC4: Given all action items are acknowledged, When the action list renders, Then a summary shows "All items reviewed" with a count.

### 13-2-action-acknowledgment-ui-UNIT-024: "All items reviewed" banner renders when all items are acknowledged
- Priority: P0
- Type: unit
- Given: InsightEvidenceCardList has 5 action items and all 5 are acknowledged
- When: The list renders
- Then: A success banner is visible above the action list with text "All items reviewed", a green CheckCircle2 icon, and count text "5/5 reviewed"
- Data: 5 ActionItems all with non-null acknowledgment, useActionAcknowledgment returning `acknowledgedCount: 5, totalCount: 5`

### 13-2-action-acknowledgment-ui-UNIT-025: "All items reviewed" banner has correct green styling
- Priority: P1
- Type: unit
- Given: All items are acknowledged and the banner renders
- When: The banner is visible
- Then: The banner has classes `bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800` applied
- Data: All items acknowledged

### 13-2-action-acknowledgment-ui-UNIT-026: Banner does NOT render when some items are unacknowledged
- Priority: P0
- Type: unit
- Given: InsightEvidenceCardList has 5 items but only 3 are acknowledged
- When: The list renders
- Then: The "All items reviewed" banner is NOT present in the DOM
- Data: 5 items, 3 acknowledged, 2 unacknowledged

### 13-2-action-acknowledgment-ui-UNIT-027: Banner does NOT render when there are zero action items
- Priority: P1
- Type: unit
- Given: InsightEvidenceCardList has 0 action items (empty list)
- When: The list renders
- Then: The "All items reviewed" banner is NOT present (even though 0/0 is technically "all"), and the empty state is shown instead
- Data: Empty action items array, `acknowledgedCount: 0, totalCount: 0`

### 13-2-action-acknowledgment-ui-UNIT-028: Banner appears dynamically when last item is acknowledged
- Priority: P0
- Type: unit
- Given: InsightEvidenceCardList has 3 items, 2 are already acknowledged, 1 is not
- When: The user clicks acknowledge on the last unacknowledged item
- Then: The banner appears showing "All items reviewed" with "3/3 reviewed" after the optimistic update
- Data: 3 ActionItems, mock acknowledge triggering state update from 2/3 to 3/3

### 13-2-action-acknowledgment-ui-UNIT-029: Banner shows correct count after acknowledging items incrementally
- Priority: P1
- Type: unit
- Given: 4 total items, 0 initially acknowledged
- When: Items are acknowledged one by one (simulating sequential user clicks)
- Then: The banner only appears after the 4th acknowledgment, with text "4/4 reviewed"
- Data: 4 ActionItems, sequential `acknowledge()` calls

### 13-2-action-acknowledgment-ui-INT-002: Full flow - acknowledge all items and see banner
- Priority: P0
- Type: integration
- Given: InsightEvidenceCardList renders with 2 unacknowledged action items
- When: The user clicks the acknowledge button on both cards sequentially
- Then: Both cards transition to acknowledged visual state, and the "All items reviewed" banner appears with "2/2 reviewed"
- Data: 2 ActionItems with `acknowledgment: null`, mock fetch resolving successfully


edge_cases:
  - Action item list is empty — no acknowledge buttons should render, no banner should show, empty state should display
  - User has an expired or null session when clicking acknowledge — hook should handle auth error gracefully, show error toast, not update UI optimistically (or rollback immediately)
  - API returns 401 Unauthorized on acknowledge POST — should rollback optimistic update, show session-expired error
  - Network disconnection during acknowledge POST — should rollback and show network error toast
  - Action IDs change between page loads (cache rebuild) — previously acknowledged items may appear unacknowledged; the UI should handle this gracefully based on the fresh GET response
  - Very long action item list (50+ items) — banner count should display correctly (e.g., "50/50 reviewed")
  - Dark mode rendering — acknowledged green styling should use dark mode variants (green-400, green-900/20, green-800)
  - Page reload mid-acknowledgment (optimistic state not yet persisted) — on reload, only database-confirmed acknowledgments should show

error_scenarios:
  - API returns 500 Internal Server Error on POST acknowledge — optimistic state must rollback, error toast displayed
  - API returns 401 Unauthorized — session likely expired, rollback state, show auth error message
  - API returns 404 Not Found for action ID — action may have been regenerated, rollback state, show appropriate error
  - Network timeout on POST acknowledge — rollback after timeout, show network error toast
  - Supabase getSession() returns null session — acknowledge should not be attempted, show "please log in" or similar
  - API returns 429 Too Many Requests — should handle rate limiting gracefully, rollback and retry or show message
  - Malformed API response (missing fields in acknowledgment object) — should not crash the UI, handle gracefully

test_file_mapping:
  - 13-2-action-acknowledgment-ui-UNIT-001 to UNIT-004, UNIT-009, UNIT-011, UNIT-017: apps/web/src/components/action-engine/__tests__/InsightEvidenceCard.ack.test.tsx
  - 13-2-action-acknowledgment-ui-UNIT-005, UNIT-007, UNIT-008, UNIT-012 to UNIT-016, UNIT-018, UNIT-019: apps/web/src/hooks/__tests__/useActionAcknowledgment.test.ts
  - 13-2-action-acknowledgment-ui-UNIT-010, UNIT-020, UNIT-021: apps/web/src/components/action-engine/__tests__/InsightEvidenceCard.ack.test.tsx
  - 13-2-action-acknowledgment-ui-UNIT-022, UNIT-023: apps/web/src/components/action-engine/__tests__/InsightEvidenceCard.ack.test.tsx
  - 13-2-action-acknowledgment-ui-UNIT-024 to UNIT-029: apps/web/src/components/action-engine/__tests__/AllItemsReviewed.test.tsx
  - 13-2-action-acknowledgment-ui-UNIT-006: apps/web/src/components/action-engine/__tests__/InsightEvidenceCard.ack.test.tsx
  - 13-2-action-acknowledgment-ui-INT-001, INT-002: apps/web/src/components/action-engine/__tests__/AllItemsReviewed.test.tsx

TEST SPEC END

---

## DESIGN: 13-3-followup-status-updates-rls
**Timestamp:** 2026-02-11 15:33:11

DESIGN START
story_id: 13-3-followup-status-updates-rls

files_to_modify:
  - path: supabase/migrations/0028_followup_assignee_rls.sql
    action: create
    purpose: Add new RLS UPDATE policy allowing assignees to update their own follow-ups. This is the key gap — the existing 0025 migration only grants UPDATE to assigned_by (assigner/manager), not assigned_to (assignee/team member).
  - path: apps/api/app/schemas/action.py
    action: modify
    purpose: Add FollowUpUpdateRequest (partial update with optional status + note, status validator) and FollowUpResponse (full follow-up record for API response) Pydantic V2 schemas.
  - path: apps/api/app/api/actions.py
    action: modify
    purpose: Add PATCH /followups/{followup_id} endpoint using user-scoped Supabase client for RLS enforcement. Includes auth dependency, partial update logic, 404/403 error differentiation.
  - path: apps/api/app/core/security.py
    action: modify
    purpose: Add get_current_user_with_token dependency that returns both CurrentUser and the raw JWT token string, needed for creating a user-scoped Supabase client in the PATCH endpoint.
  - path: apps/api/tests/test_followup_update.py
    action: create
    purpose: New test file covering all 5 test scenarios: successful update, partial updates, 403 unauthorized, 404 not found, and validation rejection of invalid status values.

patterns_to_use:
  - auth_dependency: Use Depends(get_current_user) from app.core.security for authentication, same pattern as all existing endpoints in actions.py. Additionally, inject HTTPAuthorizationCredentials via Depends(security) to get the raw JWT token for user-scoped Supabase client.
  - user_scoped_supabase_client: Create a Supabase client with the user's JWT token instead of the service role key. supabase-py 2.0+ create_client() accepts the supabase_url and a key; for user-scoped RLS we create a client with the anon/public key and then set the auth header to the user's JWT via postgrest.auth(token). Alternatively, create_client(url, anon_key) and set headers. The critical point is NOT using the service role key — this is what makes RLS enforce AC#2.
  - pydantic_v2_partial_update: Use model_dump(exclude_unset=True) to build the update dict for partial updates. Only fields explicitly provided in the request body are sent to the database. Both status and note are Optional[str] = None with exclude_unset semantics.
  - field_validator: Pydantic V2 @field_validator('status') with @classmethod decorator to validate status values against the allowed set {'assigned', 'in_progress', 'resolved'}, matching the DB CHECK constraint.
  - select_then_update_for_error_differentiation: To distinguish 404 (not found) from 403 (RLS blocked), first SELECT the follow-up using the service role client to check existence, then attempt the UPDATE using the user-scoped client. If SELECT returns nothing → 404. If UPDATE returns nothing but SELECT found it → 403 (RLS blocked).
  - test_mock_pattern: Use conftest.py fixtures (client, mock_verify_jwt, valid_jwt_payload). Mock the supabase create_client at the module level in actions.py. Use MagicMock chaining for table().select().eq().execute() patterns per test_actions_api.py.
  - migration_naming: Use next available number after 0027. File: 0028_followup_assignee_rls.sql. Only contains CREATE POLICY, no table or schema changes.

dependencies:
  - fastapi: installed (0.109+)
  - pydantic: installed (V2 — BaseModel, Field, field_validator, model_dump)
  - supabase-py: installed (>=2.0.0)
  - pytest: installed (dev dependency)

acceptance_criteria_mapping:
  - AC1 (Assignee can update follow-up status): 
    - supabase/migrations/0028_followup_assignee_rls.sql — new RLS UPDATE policy with USING (assigned_to = auth.uid()) enables DB-level update permission
    - apps/api/app/schemas/action.py — FollowUpUpdateRequest with optional status/note fields, field_validator for status enum, model_dump(exclude_unset=True) for partial updates
    - apps/api/app/api/actions.py — PATCH /followups/{followup_id} endpoint: authenticates via get_current_user, creates user-scoped Supabase client with JWT token, builds update dict from exclude_unset fields, calls .table("action_followups").update(update_data).eq("id", followup_id).execute(), returns FollowUpResponse with current status/note/updated_at
    - apps/api/app/schemas/action.py — FollowUpResponse schema for the returned record (id, action_item_id, action_summary, asset_name, category, assigned_to, assigned_by, status, note, report_date, created_at, updated_at)
  - AC2 (RLS denies unauthorized updates):
    - supabase/migrations/0028_followup_assignee_rls.sql — WITH CHECK (assigned_to = auth.uid()) prevents reassignment; combined with existing USING clause, non-assignees are blocked
    - apps/api/app/api/actions.py — endpoint uses user-scoped Supabase client (NOT service role), so PostgreSQL RLS policies are enforced. When RLS blocks the update (0 rows affected), endpoint first checks existence via service role SELECT: if found but update failed → 403 Forbidden
  - AC3 (Manager sees updated follow-up status):
    - No new code needed — the existing SELECT RLS policy ("Users can read followups assigned to or by them") already allows assigned_by (manager) to read follow-ups. After an assignee updates status/note via AC1, the manager's next SELECT query automatically returns the updated values. The FollowUpResponse schema includes status and note fields to make this visible in API responses.

risks:
  - supabase_user_scoped_client_creation: The codebase exclusively uses service role clients via create_client(url, service_key). Creating a user-scoped client requires using the anon/public key instead of the service role key, then overriding the Authorization header with the user's JWT. The supabase-py 2.0 API allows this via create_client(url, anon_key) followed by client.postgrest.auth(user_jwt). Mitigation: Implement a helper function _get_user_scoped_client(token) that creates a fresh client per request, document the pattern clearly.
  - service_role_key_vs_anon_key: The settings.supabase_key in config.py may be the service role key (bypasses RLS) rather than the anon key. For user-scoped RLS enforcement, we need to NOT pass the service role key as the client key. Mitigation: Create the client with the user's JWT directly as the key parameter (create_client(url, user_jwt_token)), which makes PostgREST use that token for auth. This is a documented supabase-py pattern where the "key" acts as the Authorization Bearer token.
  - 404_vs_403_differentiation: When a user-scoped UPDATE returns 0 rows, it could mean the row doesn't exist OR RLS blocked it. The PostgREST API doesn't distinguish these. Mitigation: Perform a service-role SELECT first to check existence (using the existing engine._get_client() pattern), then attempt the user-scoped UPDATE. If SELECT found a row but UPDATE returned empty → 403. If SELECT found nothing → 404.
  - partial_update_empty_body: If the user sends an empty body ({}) with no status or note, model_dump(exclude_unset=True) returns {}. An empty update to Supabase is a no-op but the trigger still fires updated_at. Mitigation: Validate that at least one field is provided; return 422 if the update body is effectively empty.
  - migration_numbering_collision: The story suggests 0028, but if another story creates 0028 first, there will be a collision. Mitigation: Check the migrations directory at implementation time (currently 0027 is the highest), use 0028.
  - existing_assigner_update_policy_interaction: PostgreSQL OR-combines multiple policies of the same command type. The existing "Assigners can update their followups" (assigned_by = auth.uid()) and new "Assignees can update their own followups" (assigned_to = auth.uid()) will both grant UPDATE access independently. This is correct behavior per the story requirements.

estimated_test_files:
  - apps/api/tests/test_followup_update.py: TestFollowUpUpdateEndpoint class with tests for: (1) PATCH requires auth (401), (2) successful status update by assignee returns 200 with updated record, (3) partial update with status only, (4) partial update with note only, (5) 403 when non-assignee attempts update (RLS blocks), (6) 404 when follow-up ID doesn't exist, (7) 422 when invalid status value provided, (8) 422 when empty body provided, (9) manager can see updated status via response schema verification

implementation_order:
  1. Create RLS migration supabase/migrations/0028_followup_assignee_rls.sql — single CREATE POLICY statement for assignee UPDATE access with USING and WITH CHECK clauses (Task 1)
  2. Add FollowUpUpdateRequest and FollowUpResponse Pydantic schemas to apps/api/app/schemas/action.py — FollowUpUpdateRequest with optional status/note, field_validator for status enum; FollowUpResponse with all follow-up record fields (Task 2)
  3. Add get_current_user_with_token dependency to apps/api/app/core/security.py — returns tuple of (CurrentUser, str) providing both user info and raw JWT token, OR alternatively just inject the HTTPAuthorizationCredentials directly in the endpoint alongside get_current_user (Task 3 prep)
  4. Add PATCH /followups/{followup_id} endpoint to apps/api/app/api/actions.py — implement helper _get_user_scoped_client(token) for creating user-scoped Supabase client; implement endpoint with auth, partial update logic via model_dump(exclude_unset=True), service-role existence check for 404 vs 403 differentiation, and FollowUpResponse return (Tasks 3 + 4)
  5. Create test file apps/api/tests/test_followup_update.py — unit tests covering: auth required, successful update, partial updates (status only, note only), 403 RLS denial, 404 not found, invalid status validation, empty body rejection (Task 5)
  6. Run full test suite (cd apps/api && python -m pytest) to verify no regressions in existing tests
DESIGN END

---

## TEST_SPEC: 13-3-followup-status-updates-rls
**Timestamp:** 2026-02-11 15:35:24

TEST SPEC START
story_id: 13-3-followup-status-updates-rls
generated: 2026-02-11

test_specifications:

## AC1: Assignee can update follow-up status — Given an assignee is authenticated and has follow-ups assigned to them, when they call PATCH /api/v1/followups/{followup_id} with status and optional note, then the follow-up status is updated in action_followups, the updated_at timestamp is refreshed, and only the fields provided are updated (partial update).

### 13-3-followup-status-updates-rls-UNIT-001: Successful full status update by assignee
- Priority: P0
- Type: unit
- Given: An authenticated user (user_id=sub from JWT) has a follow-up assigned to them (assigned_to = user_id) with status "assigned"
- When: They call PATCH /api/v1/actions/followups/{followup_id} with body `{"status": "in_progress", "note": "Working on this now"}`
- Then: Response is 200, response body contains the updated follow-up with status="in_progress", note="Working on this now", updated_at is refreshed, and all other FollowUpResponse fields (id, action_item_id, action_summary, asset_name, assigned_to, assigned_by, report_date, created_at) are present
- Data: Mock Supabase client returning updated follow-up record; mock_verify_jwt fixture with valid JWT payload; follow-up record with assigned_to matching JWT sub claim

### 13-3-followup-status-updates-rls-UNIT-002: Partial update with status only
- Priority: P0
- Type: unit
- Given: An authenticated assignee has a follow-up assigned to them with status "assigned" and note "Initial note"
- When: They call PATCH /api/v1/actions/followups/{followup_id} with body `{"status": "resolved"}`
- Then: Response is 200, the Supabase update call only includes `{"status": "resolved"}` (note is NOT included in the update dict via model_dump(exclude_unset=True)), and the response contains the full follow-up record with status="resolved" and the original note preserved
- Data: Mock Supabase client; verify that .update() is called with only the status field, not note

### 13-3-followup-status-updates-rls-UNIT-003: Partial update with note only
- Priority: P0
- Type: unit
- Given: An authenticated assignee has a follow-up assigned to them with status "in_progress"
- When: They call PATCH /api/v1/actions/followups/{followup_id} with body `{"note": "Still investigating root cause"}`
- Then: Response is 200, the Supabase update call only includes `{"note": "Still investigating root cause"}` (status is NOT included), and the response contains the full follow-up record with the original status preserved
- Data: Mock Supabase client; verify .update() is called with only the note field

### 13-3-followup-status-updates-rls-UNIT-004: Endpoint requires authentication
- Priority: P0
- Type: unit
- Given: No authentication token is provided
- When: PATCH /api/v1/actions/followups/{followup_id} is called without Authorization header
- Then: Response is 401 Unauthorized
- Data: No JWT mock; use mock_verify_jwt_invalid or no mock at all

### 13-3-followup-status-updates-rls-UNIT-005: Validation rejects invalid status values
- Priority: P0
- Type: unit
- Given: An authenticated assignee
- When: They call PATCH /api/v1/actions/followups/{followup_id} with body `{"status": "completed"}`
- Then: Response is 422 Unprocessable Entity with validation error indicating status must be one of: assigned, in_progress, resolved
- Data: No Supabase call should be made; Pydantic field_validator should reject before reaching endpoint logic

### 13-3-followup-status-updates-rls-UNIT-006: Validation rejects empty update body
- Priority: P1
- Type: unit
- Given: An authenticated assignee
- When: They call PATCH /api/v1/actions/followups/{followup_id} with body `{}`
- Then: Response is 422 Unprocessable Entity indicating at least one field (status or note) must be provided
- Data: Empty body; endpoint should check model_dump(exclude_unset=True) is non-empty before proceeding

### 13-3-followup-status-updates-rls-UNIT-007: Status transition from assigned to in_progress
- Priority: P1
- Type: unit
- Given: An authenticated assignee has a follow-up with status "assigned"
- When: They call PATCH with `{"status": "in_progress"}`
- Then: Response is 200, status is updated to "in_progress"
- Data: Mock Supabase returning updated record with status="in_progress"

### 13-3-followup-status-updates-rls-UNIT-008: Status transition from in_progress to resolved
- Priority: P1
- Type: unit
- Given: An authenticated assignee has a follow-up with status "in_progress"
- When: They call PATCH with `{"status": "resolved"}`
- Then: Response is 200, status is updated to "resolved"
- Data: Mock Supabase returning updated record with status="resolved"

### 13-3-followup-status-updates-rls-UNIT-009: Status can be set back to assigned
- Priority: P2
- Type: unit
- Given: An authenticated assignee has a follow-up with status "in_progress"
- When: They call PATCH with `{"status": "assigned"}`
- Then: Response is 200, status is updated to "assigned" (no enforced forward-only transitions)
- Data: Mock Supabase returning updated record with status="assigned"

### 13-3-followup-status-updates-rls-UNIT-010: Update with both status and note simultaneously
- Priority: P1
- Type: unit
- Given: An authenticated assignee has a follow-up with status "assigned" and no note
- When: They call PATCH with `{"status": "resolved", "note": "Issue was resolved by replacing the valve"}`
- Then: Response is 200, both fields are updated, Supabase .update() is called with both status and note in the update dict
- Data: Mock Supabase returning updated record with both fields

### 13-3-followup-status-updates-rls-UNIT-011: FollowUpUpdateRequest schema validates correctly
- Priority: P1
- Type: unit
- Given: Various input payloads for FollowUpUpdateRequest
- When: Pydantic model is constructed with valid statuses ("assigned", "in_progress", "resolved"), None status, invalid status ("pending", "done", ""), and optional note
- Then: Valid statuses pass validation, None status is allowed (optional field), invalid statuses raise ValidationError with descriptive message
- Data: Direct Pydantic model instantiation tests

### 13-3-followup-status-updates-rls-UNIT-012: FollowUpResponse schema serializes correctly
- Priority: P1
- Type: unit
- Given: A raw follow-up record dict from Supabase with all fields populated
- When: FollowUpResponse is constructed from the dict
- Then: All fields (id, action_item_id, action_summary, asset_name, category, assigned_to, assigned_by, status, note, report_date, created_at, updated_at) are correctly serialized, and optional fields (asset_name, category, note) handle None values
- Data: Sample follow-up record dicts with various field combinations

## AC2: RLS denies unauthorized updates — Given an assignee tries to update a follow-up not assigned to them, when the update request is made, then the request is denied with 403 (RLS enforcement).

### 13-3-followup-status-updates-rls-UNIT-013: 403 when non-assignee tries to update (RLS blocks)
- Priority: P0
- Type: unit
- Given: An authenticated user (user_id=A) attempts to update a follow-up that is assigned_to user_id=B (a different user)
- When: They call PATCH /api/v1/actions/followups/{followup_id} with `{"status": "resolved"}`
- Then: Response is 403 Forbidden. The service-role SELECT found the follow-up (it exists), but the user-scoped UPDATE returned 0 rows (RLS blocked), so the endpoint correctly returns 403
- Data: Mock service-role Supabase client returning the follow-up on SELECT (exists check); mock user-scoped Supabase client returning empty data on UPDATE (RLS denial)

### 13-3-followup-status-updates-rls-UNIT-014: 404 when follow-up does not exist
- Priority: P0
- Type: unit
- Given: An authenticated user attempts to update a follow-up with an ID that does not exist in the database
- When: They call PATCH /api/v1/actions/followups/{followup_id} with `{"status": "in_progress"}`
- Then: Response is 404 Not Found. The service-role SELECT returned no rows, indicating the follow-up does not exist
- Data: Mock service-role Supabase client returning empty data on SELECT (not found)

### 13-3-followup-status-updates-rls-UNIT-015: User-scoped Supabase client is used for update (not service role)
- Priority: P0
- Type: unit
- Given: An authenticated assignee with a valid JWT token
- When: They call PATCH /api/v1/actions/followups/{followup_id}
- Then: The update operation uses a Supabase client initialized with the user's JWT token (not the service role key), ensuring RLS policies are enforced at the database level
- Data: Verify the user-scoped client creation is called with the user's token; verify service-role client is NOT used for the update call

### 13-3-followup-status-updates-rls-INT-001: RLS migration adds correct assignee update policy
- Priority: P0
- Type: integration
- Given: The migration 0028_followup_assignee_rls.sql has been applied
- When: The policy is inspected
- Then: A new RLS policy "Assignees can update their own followups" exists on action_followups for UPDATE command, with USING clause `(assigned_to = auth.uid())` and WITH CHECK clause `(assigned_to = auth.uid())`
- Data: SQL migration file content validation

### 13-3-followup-status-updates-rls-INT-002: RLS migration preserves existing policies
- Priority: P0
- Type: integration
- Given: The migration 0028_followup_assignee_rls.sql is applied on top of existing 0025 migration
- When: All RLS policies on action_followups are listed
- Then: All existing policies remain intact: SELECT for assigned_to/assigned_by, INSERT for assigned_by, UPDATE for assigned_by (assigner), ALL for service_role — AND the new UPDATE for assigned_to (assignee) is added alongside them
- Data: Migration only contains CREATE POLICY, no DROP or ALTER POLICY statements

### 13-3-followup-status-updates-rls-INT-003: WITH CHECK prevents assignee field reassignment
- Priority: P1
- Type: integration
- Given: The RLS policy has WITH CHECK (assigned_to = auth.uid())
- When: An assignee attempts to update the assigned_to field to a different user ID via the PATCH endpoint
- Then: The database rejects the update because WITH CHECK ensures assigned_to still equals auth.uid() after the update — preventing reassignment
- Data: Attempt to include assigned_to in the update payload (should be rejected either by schema validation or WITH CHECK constraint)

### 13-3-followup-status-updates-rls-E2E-001: Assignee update blocked, assigner update allowed on same follow-up
- Priority: P1
- Type: e2e
- Given: A follow-up exists with assigned_to=UserA and assigned_by=UserB
- When: UserC (neither assignee nor assigner) attempts PATCH with `{"status": "resolved"}`
- Then: UserC receives 403 Forbidden; confirming that only UserA (assignee) and UserB (assigner) can update the record
- Data: Three distinct user JWTs; follow-up record linking UserA and UserB

## AC3: Manager sees updated follow-up status — Given a manager queries follow-ups they created, when the follow-up has been updated by the assignee, then the response includes the current status and the assignee's note.

### 13-3-followup-status-updates-rls-UNIT-016: FollowUpResponse includes status and note after assignee update
- Priority: P0
- Type: unit
- Given: An assignee has updated a follow-up to status="resolved" with note="Fixed the alignment issue"
- When: The PATCH endpoint returns the updated record
- Then: The FollowUpResponse includes status="resolved" and note="Fixed the alignment issue", along with all other fields (id, action_item_id, action_summary, asset_name, assigned_to, assigned_by, report_date, created_at, updated_at)
- Data: Mock Supabase returning the complete updated record with status and note populated

### 13-3-followup-status-updates-rls-UNIT-017: Response includes updated_at timestamp reflecting the update time
- Priority: P1
- Type: unit
- Given: An assignee updates a follow-up's status
- When: The PATCH endpoint returns the updated record
- Then: The updated_at field in the response reflects a recent timestamp (updated by the database trigger), different from created_at
- Data: Mock Supabase returning record where updated_at > created_at

### 13-3-followup-status-updates-rls-INT-004: Existing SELECT RLS allows manager to read updated follow-ups
- Priority: P1
- Type: integration
- Given: The existing SELECT RLS policy allows users to read follow-ups where assigned_by = auth.uid()
- When: A manager (assigned_by) queries follow-ups after an assignee has updated status and note
- Then: The manager sees the current status and note values as updated by the assignee — no additional code changes needed for this, just confirming existing SELECT policy handles it
- Data: Verify the existing RLS SELECT policy from migration 0025 permits this read pattern

### 13-3-followup-status-updates-rls-UNIT-018: Response includes action context fields for manager visibility
- Priority: P1
- Type: unit
- Given: A follow-up has been updated by the assignee
- When: The response is serialized via FollowUpResponse
- Then: The response includes action_summary and asset_name fields so the manager can identify which action item the follow-up relates to without needing a separate query
- Data: Mock record with action_summary="Check valve pressure on Line 3" and asset_name="Line 3 Assembly"

edge_cases:
  - Follow-up ID is not a valid UUID format — should return 422 validation error
  - Note field contains very long text (e.g., 10,000+ characters) — should either accept or have a documented max length
  - Status is provided as null explicitly ({"status": null}) vs not provided at all — model_dump(exclude_unset=True) should handle this correctly
  - Concurrent updates by both assignee and assigner on the same follow-up — last-write-wins, updated_at reflects latest
  - Follow-up ID contains SQL injection attempt — Supabase client parameterization prevents injection
  - JWT token is expired mid-request — should return 401 not 500
  - Supabase service is temporarily unavailable during update — should return 500/502 with appropriate error message

error_scenarios:
  - 401 Unauthorized: Missing or invalid JWT token
  - 403 Forbidden: Authenticated user is not the assignee (RLS blocks update)
  - 404 Not Found: Follow-up ID does not exist in the database
  - 422 Unprocessable Entity: Invalid status value (not in allowed enum)
  - 422 Unprocessable Entity: Empty update body (no fields provided)
  - 500 Internal Server Error: Supabase client connection failure or unexpected database error

test_file_mapping:
  - 13-3-followup-status-updates-rls-UNIT-*: apps/api/tests/test_followup_update.py
  - 13-3-followup-status-updates-rls-INT-*: apps/api/tests/test_followup_update.py
  - 13-3-followup-status-updates-rls-E2E-*: apps/api/tests/test_followup_update.py

TEST SPEC END

---

## DESIGN: 13-4-assignment-badge-on-action-cards
**Timestamp:** 2026-02-11 15:59:25

DESIGN START
story_id: 13-4-assignment-badge-on-action-cards

files_to_modify:
  - path: apps/web/src/hooks/useFollowUps.ts
    action: create
    purpose: New hook to query action_followups via Supabase client-side, group by action_item_id, resolve assignee UUIDs to emails via /api/v1/team/members, and return a Map<string, FollowUpData> for O(1) lookup. Handles AC#3 multiple follow-ups logic (most recent non-resolved, or most recent resolved if all resolved).
  - path: apps/web/src/components/action-engine/AssignmentBadge.tsx
    action: create
    purpose: New presentational component rendering a Shadcn Badge with color-coded variant (info=blue for assigned, warning=amber for in_progress, success=green for resolved) and assignee name + status label. Includes ARIA label for accessibility.
  - path: apps/web/src/components/action-engine/types.ts
    action: modify
    purpose: Add FollowUpData interface with fields (id, action_item_id, assigned_to, assignee_email, status, note, created_at, updated_at). Keep it separate from ActionItem — follow-up data is passed as a separate prop, not embedded in ActionItem.
  - path: apps/web/src/components/action-engine/InsightEvidenceCard.tsx
    action: modify
    purpose: Add optional followUp?: FollowUpData prop to InsightEvidenceCardProps. Pass followUp to InsightSection. When followUp exists, change "Assign" button label to "Reassign" in the onAssign callback area.
  - path: apps/web/src/components/action-engine/InsightSection.tsx
    action: modify
    purpose: Add optional followUp?: FollowUpData prop to InsightSectionProps. Render AssignmentBadge between the priority badge row and the recommendation text when followUp is present. When followUp exists, change "Assign" button text to "Reassign".
  - path: apps/web/src/components/action-engine/ActionCardList.tsx
    action: modify
    purpose: Add followUps?: Map<string, FollowUpData> prop to ActionCardListProps. Look up follow-up by item.id and pass matching FollowUpData to each InsightEvidenceCard.
  - path: apps/web/src/components/action-engine/InsightEvidenceCardList.tsx
    action: modify
    purpose: Call useFollowUps hook with reportDate derived from useDailyActions data. Pass the returned followUps map to ActionCardList.
  - path: apps/web/src/components/action-engine/index.ts
    action: modify
    purpose: Add AssignmentBadge export and FollowUpData type export.

patterns_to_use:
  - supabase_client_query: Use createClient() from @/lib/supabase/client for querying action_followups table client-side, same pattern as AssignFollowUpDialog.tsx line 63-64 and line 104. Query with .from('action_followups').select(...).eq('report_date', reportDate).order('created_at', { ascending: false }).
  - team_members_api_fetch: Fetch /api/v1/team/members with Bearer token auth (same pattern as AssignFollowUpDialog.tsx lines 60-91) to resolve assigned_to UUIDs to email strings for display. Build a Map<string, string> of userId -> email.
  - session_token_caching: Reuse the module-level getSessionToken() pattern from useActionAcknowledgment.ts (lines 33-54) for efficient session token retrieval without repeated getSession() calls.
  - badge_variant_mapping: Map follow-up status to existing Shadcn Badge variants — 'assigned' → 'info' (blue), 'in_progress' → 'warning' (amber), 'resolved' → 'success' (green) — from badge.tsx variants on lines 40-43.
  - props_drilling: Follow established InsightEvidenceCardList → ActionCardList → InsightEvidenceCard → InsightSection prop threading pattern, same as how acknowledgment data and onAcknowledge callbacks are threaded.
  - use_client_directive: All new client components use 'use client' directive, consistent with all existing action-engine components.
  - cn_utility: Use cn() from @/lib/utils for conditional className merging, consistent with all existing components.

dependencies:
  - @supabase/supabase-js: installed (via @/lib/supabase/client)
  - @/components/ui/badge: installed (Badge component with info/warning/success variants)
  - lucide-react: installed (for status icons — User, Clock, CheckCircle2)
  - class-variance-authority: installed (via badge.tsx)

acceptance_criteria_mapping:
  - AC1 (Badge with assignee name, status, color-coding): 
    - AssignmentBadge.tsx — renders Badge component with variant mapped from status (info/warning/success for assigned/in_progress/resolved), displays "[Assignee Email] · [Status Label]" format, ARIA label "Assigned to [name], status: [status]"
    - InsightSection.tsx — renders AssignmentBadge below the priority badge row (between PriorityBadge + financial impact and recommendation text h3) when followUp prop is present
    - InsightEvidenceCard.tsx — passes followUp prop to InsightSection
    - useFollowUps.ts — fetches follow-up data from action_followups table, resolves assigned_to UUID to email via team members API, returns FollowUpData with assignee_email populated
  - AC2 (No badge when no follow-up, Assign button preserved):
    - InsightSection.tsx — AssignmentBadge only renders when followUp prop is truthy (not null/undefined), existing "Assign" button remains visible via onAssign prop which is always passed from InsightEvidenceCard. When no follow-up exists, component renders identically to current behavior.
    - InsightEvidenceCard.tsx — followUp prop is optional and defaults to undefined, no rendering change when absent
    - useFollowUps.ts — returns Map that simply won't have an entry for action items without follow-ups, so lookup returns undefined → no badge
  - AC3 (Most recent active follow-up for reassigned items):
    - useFollowUps.ts — query orders by created_at DESC. When grouping by action_item_id, apply getMostRelevantFollowUp() logic: filter for non-resolved first (take [0] since already sorted DESC), fall back to most recent resolved if all are resolved. Return single FollowUpData per action_item_id in the Map.

risks:
  - rls_visibility_limitation: The SELECT RLS policy on action_followups only allows users to see follow-ups where they are assigned_to or assigned_by. A Plant Manager who did not create the follow-up AND is not assigned will not see the badge. Mitigation: This is by design per existing RLS. In practice, managers are the ones who assign follow-ups (assigned_by), so they will see all follow-ups they created. If broader visibility is needed, it would require a new RLS policy (out of scope for this story).
  - team_members_api_call_cost: Each render of InsightEvidenceCardList triggers a team members fetch to resolve UUIDs to emails. Mitigation: useFollowUps hook will cache team members in a useRef for the lifetime of the component mount, and only refetch if the component remounts. The team members list is small and changes infrequently.
  - follow_up_data_staleness: Follow-up data is fetched once when the component mounts. If another user assigns a follow-up while the page is open, it won't appear until refresh. Mitigation: This matches the existing behavior for action items (useDailyActions also fetches once). The existing refetch button in ActionCardList can be extended to re-trigger follow-up fetching.
  - empty_email_fallback: If the team members API doesn't return an email for a given user_id (e.g., user was removed from team), the badge would show a UUID. Mitigation: Fallback to truncated UUID format "abc123..." same pattern as AssignFollowUpDialog.tsx line 83.
  - action_id_instability: Action IDs regenerate on cache rebuild (documented in 13-1 decisions). Follow-ups keyed to old action IDs won't match new IDs. Mitigation: This is documented expected behavior. Follow-ups are scoped to report_date, so the most common scenario (daily usage) will have stable IDs within a single day's cache.

estimated_test_files:
  - apps/web/src/components/action-engine/__tests__/AssignmentBadge.test.tsx: Test badge renders correct variant for each status (assigned→info, in_progress→warning, resolved→success), correct display format with email and status label, correct ARIA label, no render when null followUp is passed
  - apps/web/src/hooks/__tests__/useFollowUps.test.ts: Test hook returns Map with correct FollowUpData keyed by action_item_id, test multiple follow-ups logic (most recent non-resolved wins, fallback to most recent resolved), test email resolution from team members, test empty result set returns empty Map, test loading/error states

implementation_order:
  1. Add FollowUpData interface to apps/web/src/components/action-engine/types.ts — define id, action_item_id, assigned_to, assignee_email, status ('assigned' | 'in_progress' | 'resolved'), note, created_at, updated_at fields
  2. Create apps/web/src/hooks/useFollowUps.ts — implement hook with: Supabase query for action_followups by report_date, team members fetch for UUID→email resolution, grouping by action_item_id with getMostRelevantFollowUp() logic, return { followUps: Map<string, FollowUpData>, isLoading, error }
  3. Create apps/web/src/components/action-engine/AssignmentBadge.tsx — presentational component using Shadcn Badge with status→variant mapping, display format "[email] · [Status]", ARIA label, status icons
  4. Modify apps/web/src/components/action-engine/InsightSection.tsx — add optional followUp?: FollowUpData prop, render AssignmentBadge between priority row and recommendation text when present, change "Assign" to "Reassign" when followUp exists
  5. Modify apps/web/src/components/action-engine/InsightEvidenceCard.tsx — add optional followUp?: FollowUpData prop, pass it to InsightSection
  6. Modify apps/web/src/components/action-engine/ActionCardList.tsx — add followUps?: Map<string, FollowUpData> prop, look up follow-up per item.id and pass to InsightEvidenceCard
  7. Modify apps/web/src/components/action-engine/InsightEvidenceCardList.tsx — call useFollowUps with reportDate from useDailyActions data, pass followUps map to ActionCardList
  8. Modify apps/web/src/components/action-engine/index.ts — export AssignmentBadge component and FollowUpData type
  9. Create tests: AssignmentBadge.test.tsx (badge rendering, variants, ARIA) and useFollowUps.test.ts (data fetching, grouping logic, email resolution)
  10. Manual verification: Create follow-up via AssignFollowUpDialog, confirm badge appears on card with correct name/status/color
DESIGN END

---

## TEST_SPEC: 13-4-assignment-badge-on-action-cards
**Timestamp:** 2026-02-11 16:02:38

TEST SPEC START
story_id: 13-4-assignment-badge-on-action-cards
generated: 2026-02-11

test_specifications:

## AC1: Given an action item has a follow-up assigned, When the action card renders, Then a badge shows on the card with the assignee's name and current status, And the badge is color-coded: blue (assigned), amber (in-progress), green (resolved).

### 13-4-assignment-badge-on-action-cards-UNIT-001: AssignmentBadge renders with blue info variant for "assigned" status
- Priority: P0
- Type: unit
- Given: A FollowUpData object with status "assigned" and assignee_email "john@example.com"
- When: The AssignmentBadge component renders with this follow-up data
- Then: A Badge component renders with the "info" variant (blue color), displays the assignee email "john@example.com" and status label "Assigned"
- Data: `{ id: 'fu-1', action_item_id: 'act-1', assigned_to: 'uuid-1', assignee_email: 'john@example.com', status: 'assigned', note: null, created_at: '2026-01-15T10:00:00Z', updated_at: '2026-01-15T10:00:00Z' }`

### 13-4-assignment-badge-on-action-cards-UNIT-002: AssignmentBadge renders with amber warning variant for "in_progress" status
- Priority: P0
- Type: unit
- Given: A FollowUpData object with status "in_progress" and assignee_email "jane@example.com"
- When: The AssignmentBadge component renders with this follow-up data
- Then: A Badge component renders with the "warning" variant (amber color), displays the assignee email "jane@example.com" and status label "In Progress"
- Data: `{ id: 'fu-2', action_item_id: 'act-2', assigned_to: 'uuid-2', assignee_email: 'jane@example.com', status: 'in_progress', note: 'Working on it', created_at: '2026-01-15T10:00:00Z', updated_at: '2026-01-15T11:00:00Z' }`

### 13-4-assignment-badge-on-action-cards-UNIT-003: AssignmentBadge renders with green success variant for "resolved" status
- Priority: P0
- Type: unit
- Given: A FollowUpData object with status "resolved" and assignee_email "bob@example.com"
- When: The AssignmentBadge component renders with this follow-up data
- Then: A Badge component renders with the "success" variant (green color), displays the assignee email "bob@example.com" and status label "Resolved"
- Data: `{ id: 'fu-3', action_item_id: 'act-3', assigned_to: 'uuid-3', assignee_email: 'bob@example.com', status: 'resolved', note: 'Fixed', created_at: '2026-01-15T10:00:00Z', updated_at: '2026-01-15T14:00:00Z' }`

### 13-4-assignment-badge-on-action-cards-UNIT-004: AssignmentBadge includes correct ARIA label for accessibility
- Priority: P0
- Type: unit
- Given: A FollowUpData object with assignee_email "john@example.com" and status "assigned"
- When: The AssignmentBadge component renders
- Then: The badge element has an aria-label attribute containing "Assigned to john@example.com, status: assigned"
- Data: Same as UNIT-001

### 13-4-assignment-badge-on-action-cards-UNIT-005: AssignmentBadge displays correct format with email and status label
- Priority: P0
- Type: unit
- Given: A FollowUpData object with assignee_email "alice@factory.com" and status "in_progress"
- When: The AssignmentBadge component renders
- Then: The rendered text contains both the assignee email "alice@factory.com" and a status label (e.g., "In Progress"), separated by a delimiter
- Data: `{ assignee_email: 'alice@factory.com', status: 'in_progress', ... }`

### 13-4-assignment-badge-on-action-cards-INT-001: InsightSection renders AssignmentBadge when followUp prop is provided
- Priority: P0
- Type: integration
- Given: An InsightSection component receives a valid followUp prop with status "assigned"
- When: The component renders
- Then: The AssignmentBadge is visible within the InsightSection, positioned between the priority badge row and the recommendation text
- Data: Full InsightSectionProps with followUp of status "assigned"

### 13-4-assignment-badge-on-action-cards-INT-002: InsightEvidenceCard passes followUp to InsightSection correctly
- Priority: P0
- Type: integration
- Given: An InsightEvidenceCard receives a followUp prop with status "in_progress" and assignee_email "worker@factory.com"
- When: The card renders
- Then: The AssignmentBadge appears in the InsightSection (left side) of the card showing "worker@factory.com" with amber/warning styling
- Data: Full ActionItem + FollowUpData with status "in_progress"

### 13-4-assignment-badge-on-action-cards-INT-003: InsightSection changes "Assign" button to "Reassign" when followUp exists
- Priority: P1
- Type: integration
- Given: An InsightSection component receives a valid followUp prop (any status)
- When: The component renders
- Then: The action button displays "Reassign" instead of "Assign", and the button still triggers the onAssign callback when clicked
- Data: InsightSectionProps with followUp and onAssign callback

### 13-4-assignment-badge-on-action-cards-UNIT-006: AssignmentBadge handles truncated UUID fallback for missing email
- Priority: P1
- Type: unit
- Given: A FollowUpData object where assignee_email is a truncated UUID format like "abc12345..."
- When: The AssignmentBadge component renders
- Then: The badge displays the truncated UUID as the assignee identifier without error
- Data: `{ assignee_email: 'abc12345...', status: 'assigned', ... }`

## AC2: Given an action item has no follow-up assigned, When the action card renders, Then no assignment badge is shown, And the "Assign Follow-Up" button remains prominent (existing behavior preserved).

### 13-4-assignment-badge-on-action-cards-UNIT-007: AssignmentBadge does not render when followUp prop is undefined
- Priority: P0
- Type: unit
- Given: An InsightSection component receives no followUp prop (undefined)
- When: The component renders
- Then: No AssignmentBadge element is present in the DOM
- Data: InsightSectionProps without followUp

### 13-4-assignment-badge-on-action-cards-UNIT-008: AssignmentBadge does not render when followUp prop is null
- Priority: P0
- Type: unit
- Given: An InsightSection component receives followUp as null
- When: The component renders
- Then: No AssignmentBadge element is present in the DOM
- Data: InsightSectionProps with followUp: null

### 13-4-assignment-badge-on-action-cards-INT-004: "Assign" button remains visible and labeled "Assign" when no follow-up exists
- Priority: P0
- Type: integration
- Given: An InsightSection component with an onAssign callback but no followUp prop
- When: The component renders
- Then: The "Assign" button is visible with the text "Assign" (not "Reassign"), and clicking it invokes the onAssign callback
- Data: InsightSectionProps with onAssign but without followUp

### 13-4-assignment-badge-on-action-cards-INT-005: Card renders identically to pre-story behavior when no follow-up exists
- Priority: P0
- Type: integration
- Given: An InsightEvidenceCard component with a standard ActionItem and no followUp prop
- When: The card renders
- Then: The card layout, priority badge, recommendation text, financial impact, evidence section, and "Assign" button all render exactly as before this story's changes
- Data: Standard ActionItem from createMockActionItem factory

### 13-4-assignment-badge-on-action-cards-UNIT-009: useFollowUps returns empty Map for action items without follow-ups
- Priority: P0
- Type: unit
- Given: The action_followups table returns an empty result set for the given reportDate
- When: The useFollowUps hook resolves
- Then: The returned followUps Map is empty (size === 0), isLoading is false, and error is null
- Data: Supabase mock returns `{ data: [], error: null }`

### 13-4-assignment-badge-on-action-cards-INT-006: ActionCardList passes undefined followUp to cards not in the followUps Map
- Priority: P1
- Type: integration
- Given: An ActionCardList receives a followUps Map containing an entry for "act-1" but not for "act-2"
- When: The list renders two action items with ids "act-1" and "act-2"
- Then: InsightEvidenceCard for "act-1" receives the followUp prop, and InsightEvidenceCard for "act-2" receives undefined (no badge shown)
- Data: Two ActionItems, followUps Map with single entry for "act-1"

## AC3: Given multiple follow-ups exist for the same action item (reassigned), When the card renders, Then the most recent active follow-up is shown (determined by created_at DESC, excluding resolved unless no active exists).

### 13-4-assignment-badge-on-action-cards-UNIT-010: useFollowUps selects most recent non-resolved follow-up when multiple exist
- Priority: P0
- Type: unit
- Given: The action_followups table returns 3 follow-ups for the same action_item_id: one "resolved" (oldest), one "assigned" (middle), one "in_progress" (newest)
- When: The useFollowUps hook processes the data
- Then: The returned Map contains a single entry for that action_item_id with the "in_progress" follow-up (most recent active)
- Data: Three follow-ups for "act-1" with created_at timestamps T1 < T2 < T3, statuses ["resolved", "assigned", "in_progress"]

### 13-4-assignment-badge-on-action-cards-UNIT-011: useFollowUps selects most recent resolved follow-up when all are resolved
- Priority: P0
- Type: unit
- Given: The action_followups table returns 2 follow-ups for the same action_item_id, both with status "resolved"
- When: The useFollowUps hook processes the data
- Then: The returned Map contains a single entry for that action_item_id with the most recently created resolved follow-up
- Data: Two follow-ups for "act-1" both with status "resolved", created_at T1 < T2

### 13-4-assignment-badge-on-action-cards-UNIT-012: useFollowUps prefers active over resolved even if resolved is newer
- Priority: P0
- Type: unit
- Given: The action_followups table returns 2 follow-ups for the same action_item_id: one "assigned" (older), one "resolved" (newer)
- When: The useFollowUps hook processes the data
- Then: The returned Map contains the "assigned" follow-up (active is preferred over resolved, regardless of created_at)
- Data: Two follow-ups for "act-1": `{ status: 'assigned', created_at: '2026-01-15T08:00:00Z' }`, `{ status: 'resolved', created_at: '2026-01-15T12:00:00Z' }`

### 13-4-assignment-badge-on-action-cards-UNIT-013: useFollowUps handles single follow-up per action item correctly
- Priority: P1
- Type: unit
- Given: The action_followups table returns exactly one follow-up for an action_item_id
- When: The useFollowUps hook processes the data
- Then: The returned Map contains that single follow-up, regardless of its status
- Data: Single follow-up for "act-1" with status "assigned"

### 13-4-assignment-badge-on-action-cards-UNIT-014: useFollowUps groups follow-ups correctly across different action items
- Priority: P0
- Type: unit
- Given: The action_followups table returns follow-ups for 3 different action_item_ids, some with multiple follow-ups
- When: The useFollowUps hook processes the data
- Then: The returned Map has exactly 3 entries, each keyed by the correct action_item_id with the most relevant follow-up for that item
- Data: 5 follow-ups total: 2 for "act-1" (one active, one resolved), 2 for "act-2" (both resolved), 1 for "act-3" (assigned)

### 13-4-assignment-badge-on-action-cards-INT-007: Card displays most recent active follow-up badge when reassigned
- Priority: P1
- Type: integration
- Given: An InsightEvidenceCard receives a followUp reflecting the most recent active follow-up (status "in_progress", recent email)
- When: The card renders
- Then: The badge shows the most recent assignee's email and "In Progress" status with amber styling, not the older resolved follow-up
- Data: FollowUpData with status "in_progress" and latest assignee email

## Hook Data Fetching & Integration

### 13-4-assignment-badge-on-action-cards-UNIT-015: useFollowUps fetches follow-ups filtered by reportDate
- Priority: P0
- Type: unit
- Given: A reportDate of "2026-01-15" is provided to useFollowUps
- When: The hook initializes and fetches data
- Then: The Supabase query includes `.eq('report_date', '2026-01-15')` and `.order('created_at', { ascending: false })`
- Data: Mock Supabase client verifying query chain

### 13-4-assignment-badge-on-action-cards-UNIT-016: useFollowUps resolves assigned_to UUIDs to emails via team members API
- Priority: P0
- Type: unit
- Given: Follow-ups contain assigned_to UUID "uuid-abc" and the team members API returns `{ members: [{ user_id: 'uuid-abc', email: 'alice@factory.com' }] }`
- When: The hook processes the data
- Then: The returned FollowUpData has assignee_email set to "alice@factory.com"
- Data: Mock follow-up with assigned_to "uuid-abc", mock fetch response for /api/v1/team/members

### 13-4-assignment-badge-on-action-cards-UNIT-017: useFollowUps falls back to truncated UUID when team member email not found
- Priority: P1
- Type: unit
- Given: Follow-ups contain assigned_to UUID "abcdef12-3456-7890-abcd-ef1234567890" but team members API does not include this user
- When: The hook processes the data
- Then: The returned FollowUpData has assignee_email set to a truncated format like "abcdef12..."
- Data: Mock follow-up with unresolvable UUID, mock team members without matching entry

### 13-4-assignment-badge-on-action-cards-UNIT-018: useFollowUps returns loading state during fetch
- Priority: P1
- Type: unit
- Given: The hook is initialized with a valid reportDate
- When: The Supabase query and team members fetch are in-flight
- Then: The hook returns `{ followUps: empty Map, isLoading: true, error: null }`
- Data: Pending mock promises

### 13-4-assignment-badge-on-action-cards-UNIT-019: useFollowUps handles Supabase query error gracefully
- Priority: P1
- Type: unit
- Given: The Supabase query for action_followups returns an error
- When: The hook processes the error
- Then: The hook returns `{ followUps: empty Map, isLoading: false, error: <error message> }`
- Data: Supabase mock returns `{ data: null, error: { message: 'Permission denied' } }`

### 13-4-assignment-badge-on-action-cards-UNIT-020: useFollowUps handles team members API failure gracefully
- Priority: P1
- Type: unit
- Given: The Supabase query succeeds but the /api/v1/team/members fetch fails (network error or non-200)
- When: The hook processes the data
- Then: The hook still returns follow-ups but with truncated UUID fallbacks for all assignee_email fields (does not fail entirely)
- Data: Successful Supabase mock, failing fetch mock

### 13-4-assignment-badge-on-action-cards-INT-008: InsightEvidenceCardList wires useFollowUps with reportDate from useDailyActions
- Priority: P0
- Type: integration
- Given: useDailyActions returns data with report_date "2026-01-15"
- When: InsightEvidenceCardList renders
- Then: useFollowUps is called with reportDate "2026-01-15", and the returned followUps Map is passed to ActionCardList
- Data: Mock useDailyActions with report_date, mock useFollowUps returning a Map with entries

## Barrel File & Exports

### 13-4-assignment-badge-on-action-cards-UNIT-021: AssignmentBadge is exported from barrel file
- Priority: P2
- Type: unit
- Given: The action-engine barrel file (index.ts) has been updated
- When: Importing AssignmentBadge from '@/components/action-engine'
- Then: The AssignmentBadge component is successfully imported and is a valid React component
- Data: Import verification

### 13-4-assignment-badge-on-action-cards-UNIT-022: FollowUpData type is exported from barrel file
- Priority: P2
- Type: unit
- Given: The action-engine barrel file (index.ts) has been updated
- When: Importing FollowUpData from '@/components/action-engine'
- Then: The FollowUpData type is successfully imported and usable for typing
- Data: Import verification

edge_cases:
  - Action item ID changes after cache rebuild (documented in 13-1 decisions) — follow-up keyed to old ID won't match; badge simply won't render (graceful degradation)
  - RLS policy limits visibility — Plant Manager who is neither assigned_to nor assigned_by will not see the follow-up badge for that action item
  - Team members API returns a user without an email field — fallback to truncated UUID display
  - Follow-up created while page is already loaded — badge won't appear until refetch/page refresh (matches existing staleness behavior)
  - Very long assignee email address — badge should truncate gracefully without breaking card layout
  - Action item is both acknowledged AND has a follow-up — both acknowledged visual state (opacity-60) and assignment badge should coexist
  - reportDate is undefined/null when useDailyActions data hasn't loaded yet — useFollowUps should not fetch and should return empty state

error_scenarios:
  - Supabase query returns permission denied error (RLS policy block) — hook returns error state, no badges rendered, no crash
  - Team members API returns 401 (expired session token) — hook falls back to truncated UUIDs for display names
  - Team members API returns 500 — hook falls back to truncated UUIDs, does not block follow-up display
  - Network timeout on Supabase query — hook returns error state after timeout
  - Supabase returns malformed data (missing required fields) — hook handles gracefully, skips malformed entries
  - Follow-up has assigned_to that is null or empty string — badge should either not render or show a sensible fallback

test_file_mapping:
  - 13-4-assignment-badge-on-action-cards-UNIT-001 to UNIT-006: apps/web/src/components/action-engine/__tests__/AssignmentBadge.test.tsx
  - 13-4-assignment-badge-on-action-cards-UNIT-007 to UNIT-008: apps/web/src/components/action-engine/__tests__/AssignmentBadge.test.tsx
  - 13-4-assignment-badge-on-action-cards-UNIT-009 to UNIT-020: apps/web/src/hooks/__tests__/useFollowUps.test.ts
  - 13-4-assignment-badge-on-action-cards-UNIT-021 to UNIT-022: apps/web/src/components/action-engine/__tests__/AssignmentBadge.test.tsx
  - 13-4-assignment-badge-on-action-cards-INT-001 to INT-003: apps/web/src/components/action-engine/__tests__/AssignmentBadge.test.tsx
  - 13-4-assignment-badge-on-action-cards-INT-004 to INT-006: apps/web/src/components/action-engine/__tests__/InsightEvidenceCard.badge.test.tsx
  - 13-4-assignment-badge-on-action-cards-INT-007: apps/web/src/components/action-engine/__tests__/InsightEvidenceCard.badge.test.tsx
  - 13-4-assignment-badge-on-action-cards-INT-008: apps/web/src/components/action-engine/__tests__/InsightEvidenceCardList.followups.test.tsx

TEST SPEC END

---

## DESIGN: 13-5-my-assignments-panel
**Timestamp:** 2026-02-11 16:49:13

DESIGN START
story_id: 13-5-my-assignments-panel

files_to_modify:
  - path: apps/api/app/schemas/action.py
    action: modify
    purpose: Add FollowUpListItem (extends FollowUpResponse with assigned_to_email field) and FollowUpListResponse (wraps list with total_count and counts_by_status) Pydantic V2 schemas for the new GET /followups endpoint
  - path: apps/api/app/api/actions.py
    action: modify
    purpose: Add GET /followups endpoint with query params (assigned_by=me, status filter, limit, offset). Uses service-role Supabase client to query action_followups table filtered by assigned_by=current_user.id, joins with team members to resolve assigned_to UUIDs to emails, returns FollowUpListResponse
  - path: apps/api/tests/test_followups_list.py
    action: create
    purpose: Pytest tests for GET /followups endpoint — auth required, filter by assigned_by, status filtering, empty response, counts_by_status accuracy, email resolution
  - path: apps/web/src/hooks/useMyFollowUps.ts
    action: create
    purpose: Data fetching hook following exact useDailyActions.ts pattern — Supabase auth session for Bearer token, useState/useEffect/useCallback/useRef, auto-fetch on mount, refetch() exposed, returns followups array grouped by status with totalCount/hasFollowUps computed values
  - path: apps/web/src/components/action-list/MyAssignmentsPanel.tsx
    action: create
    purpose: Collapsible Card panel with "My Assignments" header, count badge, expand/collapse chevron. Groups follow-ups by status with color-coded Badge section headers (info=blue assigned, warning=amber in_progress, success=green resolved). Handles loading skeleton, error retry, empty state per AC#4
  - path: apps/web/src/components/action-list/FollowUpEntry.tsx
    action: create
    purpose: Individual follow-up row showing asset name, truncated action summary, assignee email, relative time since assigned. Includes "New update" dot indicator via localStorage comparison. Click handler opens FollowUpDetailDialog
  - path: apps/web/src/components/action-list/FollowUpDetailDialog.tsx
    action: create
    purpose: Shadcn Dialog showing full assignment context — original action item info with PriorityBadge, manager's assignment note, current status badge, assignee's notes with timestamps. Uses existing Dialog/DialogContent/DialogHeader pattern from AssignFollowUpDialog
  - path: apps/web/src/components/action-list/index.ts
    action: modify
    purpose: Add barrel exports for MyAssignmentsPanel, FollowUpEntry, FollowUpDetailDialog
  - path: apps/web/src/app/(main)/morning-report/page.tsx
    action: modify
    purpose: Import MyAssignmentsPanel from action-list barrel and position it between MorningSummarySection and WorkcenterScorecard in the page layout

patterns_to_use:
  - bearer_token_auth_hook: Follow exact useDailyActions.ts pattern (lines 125-191) — createClient() from @/lib/supabase/client, supabase.auth.getSession(), Bearer token in Authorization header, error messages for NETWORK_ERROR/AUTH_ERROR/SERVER_ERROR, mountedRef for cleanup
  - fastapi_endpoint_auth: Use Depends(get_current_user) and Depends(security) for auth exactly as in the PATCH /followups/{followup_id} endpoint (actions.py:379-388). Service-role Supabase client via create_client(settings.supabase_url, settings.supabase_key) for querying
  - container_loading_error_empty: Follow ActionListContainer.tsx pattern — skeleton loading state on initial fetch, error state with AlertCircle + retry button, empty state with positive messaging, populated state with cards
  - card_collapsible: Use Card/CardHeader/CardContent from shadcn with a toggle state. Expand/collapse via button with ChevronDown/ChevronRight icon. Default expanded if followups exist, collapsed if empty
  - badge_status_variants: Map follow-up status to Badge variants — 'assigned' → 'info' (blue), 'in_progress' → 'warning' (amber), 'resolved' → 'success' (green) — using existing badgeVariants from badge.tsx
  - dialog_detail_pattern: Follow AssignFollowUpDialog.tsx structure — Dialog/DialogContent/DialogHeader/DialogTitle/DialogDescription with sm:max-w-md, contextual info in styled div, action item context with PriorityBadge
  - new_update_localstorage: Store lastViewedTimestamp per follow-up as localStorage key `followup-viewed-{followup_id}`, compare against follow-up's updated_at. Update on dialog open. Avoids new DB column
  - relative_time_utility: Inline formatRelativeTime(isoString) function — minutes/hours/days ago — no date library dependency per dev notes
  - test_mock_supabase: Follow test_followup_update.py pattern — patch("app.api.actions.create_client"), MagicMock chaining for table().select().eq().execute().data, conftest fixtures (client, mock_verify_jwt, valid_jwt_payload)
  - pydantic_v2_schema: Follow existing FollowUpResponse pattern — BaseModel with string fields, Optional for nullable fields, ConfigDict if needed

dependencies:
  - fastapi: installed (0.109+)
  - supabase-py: installed (>=2.0.0)
  - pydantic: installed (V2)
  - pytest: installed (dev)
  - @supabase/supabase-js: installed (via @/lib/supabase/client)
  - lucide-react: installed (ChevronDown, ChevronRight, AlertCircle, RefreshCw, Clock, User, CheckCircle2, ClipboardList, Circle)
  - @/components/ui/badge: installed (info, warning, success variants)
  - @/components/ui/card: installed (Card, CardHeader, CardTitle, CardDescription, CardContent)
  - @/components/ui/dialog: installed (Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription)
  - @/components/ui/button: installed
  - @/components/ui/scroll-area: installed
  - @/components/action-engine/PriorityBadge: installed

acceptance_criteria_mapping:
  - AC1 (Panel shows follow-ups grouped by status with entry details):
    - Backend: apps/api/app/api/actions.py — GET /followups endpoint with assigned_by=me filter, returns follow-ups with assigned_to_email resolved; apps/api/app/schemas/action.py — FollowUpListItem (adds assigned_to_email to FollowUpResponse), FollowUpListResponse (wraps with counts_by_status)
    - Frontend: apps/web/src/hooks/useMyFollowUps.ts — fetches from GET /api/v1/actions/followups?assigned_by=me&status=active, returns grouped data { assigned: [], in_progress: [], resolved: [] }
    - Frontend: apps/web/src/components/action-list/MyAssignmentsPanel.tsx — collapsible Card with "My Assignments" header + count badge, renders three status groups with color-coded Badge section headers using info/warning/success variants, maps FollowUpEntry per item
    - Frontend: apps/web/src/components/action-list/FollowUpEntry.tsx — shows asset_name, truncated action_summary, assignee email (assigned_to_email), relative time since created_at via formatRelativeTime()
    - Frontend: apps/web/src/app/(main)/morning-report/page.tsx — imports MyAssignmentsPanel, places between MorningSummarySection and WorkcenterScorecard
  - AC2 (Status group movement and "New update" indicator on refresh):
    - Backend: The GET /followups endpoint returns current status and updated_at per follow-up. On refetch, the frontend re-groups items by current status
    - Frontend: useMyFollowUps.ts — refetch() re-calls the endpoint, re-groups by status. The grouped object is recalculated on each fetch
    - Frontend: FollowUpEntry.tsx — compares follow-up's updated_at against localStorage key `followup-viewed-{id}`. If updated_at > lastViewedTimestamp, renders a blue dot indicator ("New update"). When user opens FollowUpDetailDialog, writes current timestamp to localStorage clearing the dot
  - AC3 (Click follow-up entry opens detail view with full context):
    - Frontend: FollowUpEntry.tsx — onClick handler sets selectedFollowUp state and opens FollowUpDetailDialog
    - Frontend: FollowUpDetailDialog.tsx — receives follow-up data, renders: original action summary with category/PriorityBadge, asset name, manager's assignment note, current status Badge, assignee's status update notes, full timeline with timestamps (created_at, updated_at). Updates localStorage on open for "New update" indicator clearing
  - AC4 (Empty state when no open follow-ups):
    - Frontend: MyAssignmentsPanel.tsx — when useMyFollowUps returns hasFollowUps=false, renders empty state: "No open follow-ups. Assign actions from the report below." with muted styling matching EmptyActionState pattern. Panel defaults to collapsed when empty

risks:
  - email_resolution_in_backend: The GET /followups endpoint needs to resolve assigned_to UUIDs to email addresses. The team members API (/api/v1/team/members) is the existing pattern, but calling it server-side requires a different approach. Mitigation: Use the service-role Supabase client to query auth.users directly (or the team_members table if it exists), similar to how the team endpoint itself works. Alternatively, have the endpoint call the team members logic internally. Simplest approach: query the Supabase auth.users table via admin API or service-role RPC to get emails.
  - rls_bypass_for_email_resolution: The dev notes explicitly call out using service-role client for the join since RLS on auth.users blocks cross-user lookups. Mitigation: The GET /followups endpoint will use service-role client (like the existing acknowledge endpoint uses engine._get_client()), filter by assigned_by=current_user.id in the WHERE clause manually, and join/resolve emails server-side.
  - route_ordering_collision: The existing PATCH /followups/{followup_id} uses a path parameter. A new GET /followups must be registered BEFORE the PATCH to avoid FastAPI treating "followups" as the {followup_id} parameter. Mitigation: Place the GET /followups route definition above the PATCH /followups/{followup_id} route in actions.py, or use a distinct path like GET /followups/my-assignments.
  - action_id_instability: Action IDs regenerate on cache rebuild (documented in 13-1 decisions). Follow-ups reference specific action_item_ids. Mitigation: This is existing behavior, documented and accepted. The panel shows follow-up data from the DB which retains the original action_item_id.
  - localstorage_new_update_indicator: The "New update" indicator relies on localStorage which is per-browser. Switching browsers or clearing storage resets the indicator. Mitigation: This is explicitly documented as the chosen approach in the dev notes to avoid a new DB column. Acceptable tradeoff for this story.
  - panel_position_in_server_component: The morning report page is a Server Component. MyAssignmentsPanel is a Client Component with hooks. Mitigation: Import the 'use client' component directly in the server page — this is the exact same pattern used for InsightEvidenceCardList and MorningSummarySection already.
  - assigned_to_email_vs_name: The story says "assignee name" but the existing team members API returns emails not display names. Mitigation: Use email as the display identifier, consistent with AssignFollowUpDialog and AssignmentBadge which both use email. This is the established pattern.

estimated_test_files:
  - apps/api/tests/test_followups_list.py: Tests for GET /followups endpoint — auth required (401 without token), returns only follow-ups where assigned_by matches current user, status filter works (active/assigned/in_progress/resolved/all), empty result returns empty array with zero counts, response includes assigned_to_email, counts_by_status is accurate, pagination (limit/offset) works
  - apps/web/src/hooks/__tests__/useMyFollowUps.test.ts: Tests for useMyFollowUps hook — initial loading state, successful fetch returns grouped data, auth error handling (expired session), server error handling, empty response sets hasFollowUps=false, refetch triggers new API call, grouping logic correctly separates by status
  - apps/web/src/components/action-list/__tests__/MyAssignmentsPanel.test.tsx: Tests for panel component — renders loading skeleton, renders error state with retry, renders empty state with correct message text, renders grouped follow-ups with color-coded headers, expand/collapse toggle works, count badge shows correct total, default expanded when has items, default collapsed when empty
  - apps/web/src/components/action-list/__tests__/FollowUpEntry.test.tsx: Tests for entry component — renders asset name and summary, renders assignee email, renders relative time, "New update" dot shows when updated_at > localStorage value, click triggers onSelect callback, handles missing optional fields gracefully
  - apps/web/src/components/action-list/__tests__/FollowUpDetailDialog.test.tsx: Tests for detail dialog — renders full action context, renders assignment note, renders status badge with correct variant, renders timeline with timestamps, dialog opens/closes correctly

implementation_order:
  1. Add FollowUpListItem and FollowUpListResponse Pydantic schemas to apps/api/app/schemas/action.py — FollowUpListItem extends FollowUpResponse with assigned_to_email: Optional[str] = None; FollowUpListResponse has followups: List[FollowUpListItem], total_count: int, counts_by_status: dict
  2. Add GET /followups endpoint to apps/api/app/api/actions.py — place ABOVE the PATCH /followups/{followup_id} route to avoid path collision. Accepts query params: assigned_by (str, default "me"), status (str, default "active" meaning assigned+in_progress), limit (int, default 50), offset (int, default 0). Uses service-role Supabase client, filters by assigned_by=current_user.id, resolves assigned_to emails via auth.users or team members logic, groups counts by status, returns FollowUpListResponse
  3. Create apps/api/tests/test_followups_list.py — test auth required, filter by assigned_by=me, status filtering, empty results, email resolution, counts_by_status
  4. Run backend tests (cd apps/api && python -m pytest tests/test_followups_list.py -v) to verify endpoint works
  5. Create apps/web/src/hooks/useMyFollowUps.ts — follow useDailyActions.ts pattern. Fetch from GET /api/v1/actions/followups?assigned_by=me&status=active. Return { followups, isLoading, error, refetch, grouped: { assigned, in_progress, resolved }, totalCount, hasFollowUps }. Group by status client-side from the flat list
  6. Create apps/web/src/components/action-list/FollowUpEntry.tsx — presentational component: asset name, truncated action_summary, assignee email, relative time. "New update" dot indicator via localStorage. onClick prop for opening detail view
  7. Create apps/web/src/components/action-list/FollowUpDetailDialog.tsx — Dialog with full context: action item summary + category PriorityBadge + asset name, manager's note, current status Badge, assignee's notes, timestamps. On open, write current timestamp to localStorage for the follow-up ID
  8. Create apps/web/src/components/action-list/MyAssignmentsPanel.tsx — Card with CardHeader "My Assignments" + count Badge + expand/collapse chevron Button. CardContent renders three status groups with Badge section headers (info/warning/success), each group maps FollowUpEntry components. Loading skeleton (reuse SkeletonPulse pattern), error state with retry, empty state per AC#4. ScrollArea if many items. Manages FollowUpDetailDialog open/close state
  9. Modify apps/web/src/components/action-list/index.ts — add exports for MyAssignmentsPanel, FollowUpEntry, FollowUpDetailDialog
  10. Modify apps/web/src/app/(main)/morning-report/page.tsx — import MyAssignmentsPanel from '@/components/action-list', place <MyAssignmentsPanel /> between <MorningSummarySection /> and <WorkcenterScorecard /> in the space-y-6 div
  11. Create frontend test files — useMyFollowUps.test.ts, MyAssignmentsPanel.test.tsx, FollowUpEntry.test.tsx, FollowUpDetailDialog.test.tsx
  12. Run full test suite (backend + frontend) to verify no regressions
DESIGN END

---

## TEST_SPEC: 13-5-my-assignments-panel
**Timestamp:** 2026-02-11 16:52:22

TEST SPEC START
story_id: 13-5-my-assignments-panel
generated: 2026-02-11

test_specifications:

## AC1: Panel shows follow-ups grouped by status with entry details

Given the manager has created follow-up assignments, When the "My Assignments" panel is visible on the morning report, Then it shows all follow-ups grouped by status (Assigned/blue, In Progress/amber, Resolved/green) And each entry shows: asset name, action summary, assignee name, time since assigned.

### 13-5-my-assignments-panel-INT-001: Backend returns follow-ups filtered by assigned_by=me
- Priority: P0
- Type: integration
- Given: The authenticated manager has created 3 follow-up assignments (1 assigned, 1 in_progress, 1 resolved) in the action_followups table
- When: GET /api/v1/actions/followups?assigned_by=me is called with a valid Bearer token
- Then: The response returns status 200 with all 3 follow-ups where assigned_by matches the current user's ID, and counts_by_status shows {"assigned": 1, "in_progress": 1, "resolved": 1}, and total_count is 3
- Data: 3 follow-up records with assigned_by=current_user_id, varying statuses; at least 1 follow-up assigned_by a different user (should NOT be returned)

### 13-5-my-assignments-panel-INT-002: Backend resolves assigned_to UUIDs to email addresses
- Priority: P0
- Type: integration
- Given: A follow-up exists with assigned_to pointing to a valid user UUID
- When: GET /api/v1/actions/followups?assigned_by=me is called
- Then: Each follow-up in the response includes assigned_to_email with the resolved email address (e.g., "john@company.com"), not just the UUID
- Data: Follow-up record with assigned_to UUID, corresponding user record with email in auth.users

### 13-5-my-assignments-panel-INT-003: Backend filters by status parameter
- Priority: P0
- Type: integration
- Given: The manager has follow-ups in all 3 statuses (assigned, in_progress, resolved)
- When: GET /api/v1/actions/followups?assigned_by=me&status=active is called
- Then: Only follow-ups with status "assigned" or "in_progress" are returned; resolved follow-ups are excluded; counts_by_status reflects only the returned items
- Data: 3 follow-ups (1 per status)

### 13-5-my-assignments-panel-INT-004: Backend status filter for specific statuses
- Priority: P1
- Type: integration
- Given: The manager has follow-ups in all 3 statuses
- When: GET /api/v1/actions/followups?assigned_by=me&status=assigned is called
- Then: Only follow-ups with status "assigned" are returned
- Data: 3 follow-ups (1 per status)

### 13-5-my-assignments-panel-INT-005: Backend status filter for "all" returns all statuses
- Priority: P1
- Type: integration
- Given: The manager has follow-ups in all 3 statuses
- When: GET /api/v1/actions/followups?assigned_by=me&status=all is called
- Then: All 3 follow-ups are returned regardless of status
- Data: 3 follow-ups (1 per status)

### 13-5-my-assignments-panel-INT-006: Backend requires authentication
- Priority: P0
- Type: integration
- Given: No Bearer token is provided in the request
- When: GET /api/v1/actions/followups is called without Authorization header
- Then: The response returns status 401 Unauthorized
- Data: None

### 13-5-my-assignments-panel-INT-007: Backend response includes all required fields per schema
- Priority: P0
- Type: integration
- Given: A follow-up assignment exists with all fields populated
- When: GET /api/v1/actions/followups?assigned_by=me is called
- Then: Each follow-up item in the response includes: id, action_item_id, action_summary, asset_name, category, assigned_to, assigned_to_email, assigned_by, note, status, report_date, created_at, updated_at
- Data: 1 fully-populated follow-up record

### 13-5-my-assignments-panel-INT-008: Backend supports pagination with limit and offset
- Priority: P1
- Type: integration
- Given: The manager has 10 follow-up assignments
- When: GET /api/v1/actions/followups?assigned_by=me&limit=3&offset=0 is called
- Then: The response returns exactly 3 follow-ups, total_count reflects the full count (10), and subsequent calls with offset=3 return the next 3 items
- Data: 10 follow-up records

### 13-5-my-assignments-panel-UNIT-001: FollowUpListItem schema includes assigned_to_email
- Priority: P0
- Type: unit
- Given: A FollowUpListItem Pydantic model is instantiated with all required fields including assigned_to_email
- When: The model is serialized to dict/JSON
- Then: The output includes the assigned_to_email field alongside all FollowUpResponse fields
- Data: Valid FollowUpListItem field values

### 13-5-my-assignments-panel-UNIT-002: FollowUpListResponse schema validates counts_by_status
- Priority: P1
- Type: unit
- Given: A FollowUpListResponse is constructed with followups list, total_count, and counts_by_status dict
- When: The model is validated
- Then: The schema accepts the structure with proper types; counts_by_status maps status strings to integers
- Data: Sample response with 2 assigned, 1 in_progress, 0 resolved

### 13-5-my-assignments-panel-UNIT-003: useMyFollowUps hook fetches and groups follow-ups on mount
- Priority: P0
- Type: unit
- Given: The Supabase session is authenticated and the API returns 3 follow-ups (1 assigned, 1 in_progress, 1 resolved)
- When: The useMyFollowUps hook is rendered
- Then: isLoading is initially true, then becomes false; grouped.assigned contains 1 item, grouped.in_progress contains 1 item, grouped.resolved contains 1 item; totalCount is 3; hasFollowUps is true
- Data: Mock API response with 3 follow-ups in different statuses

### 13-5-my-assignments-panel-UNIT-004: useMyFollowUps hook returns correct hasFollowUps=false when no follow-ups
- Priority: P0
- Type: unit
- Given: The Supabase session is authenticated and the API returns an empty followups array
- When: The useMyFollowUps hook is rendered
- Then: hasFollowUps is false, totalCount is 0, grouped.assigned/in_progress/resolved are all empty arrays
- Data: Mock API response with empty followups, total_count: 0

### 13-5-my-assignments-panel-UNIT-005: MyAssignmentsPanel renders status groups with correct color-coded badges
- Priority: P0
- Type: unit
- Given: The useMyFollowUps hook returns grouped follow-ups (2 assigned, 1 in_progress, 1 resolved)
- When: The MyAssignmentsPanel component renders
- Then: Three status group sections are visible; the "Assigned" section has a blue/info badge variant; the "In Progress" section has an amber/warning badge variant; the "Resolved" section has a green/success badge variant
- Data: 4 mock follow-up items across 3 status groups

### 13-5-my-assignments-panel-UNIT-006: MyAssignmentsPanel renders count badge in header
- Priority: P1
- Type: unit
- Given: The useMyFollowUps hook returns 5 total follow-ups
- When: The MyAssignmentsPanel component renders
- Then: The header shows "My Assignments" with a count badge displaying "5"
- Data: 5 mock follow-up items

### 13-5-my-assignments-panel-UNIT-007: FollowUpEntry renders asset name, action summary, assignee, and relative time
- Priority: P0
- Type: unit
- Given: A follow-up entry with asset_name="Grinder 5", action_summary="Investigate pressure anomaly on main valve", assigned_to_email="john@company.com", created_at=2 hours ago
- When: The FollowUpEntry component renders
- Then: The asset name "Grinder 5" is displayed; the action summary is displayed (possibly truncated); "john@company.com" is displayed as the assignee; "2h ago" is displayed as the relative time
- Data: Single FollowUpItem with all fields populated

### 13-5-my-assignments-panel-UNIT-008: FollowUpEntry truncates long action summaries
- Priority: P2
- Type: unit
- Given: A follow-up entry with action_summary exceeding 80+ characters
- When: The FollowUpEntry component renders
- Then: The action summary is truncated with ellipsis to fit the display area
- Data: Follow-up with a long action_summary string

### 13-5-my-assignments-panel-UNIT-009: formatRelativeTime utility returns correct relative times
- Priority: P1
- Type: unit
- Given: Various ISO timestamp strings representing different time differences
- When: formatRelativeTime is called with each timestamp
- Then: Returns "0m ago" for current time, "30m ago" for 30 minutes ago, "2h ago" for 2 hours ago, "1d ago" for 24 hours ago, "7d ago" for 7 days ago
- Data: Timestamps at 0min, 30min, 2hrs, 24hrs, 7days before now

### 13-5-my-assignments-panel-UNIT-010: MyAssignmentsPanel default expanded when follow-ups exist
- Priority: P1
- Type: unit
- Given: The useMyFollowUps hook returns hasFollowUps=true with some follow-ups
- When: The MyAssignmentsPanel component renders initially
- Then: The panel content (follow-up entries) is visible/expanded, not collapsed
- Data: At least 1 mock follow-up item

### 13-5-my-assignments-panel-UNIT-011: MyAssignmentsPanel default collapsed when no follow-ups
- Priority: P1
- Type: unit
- Given: The useMyFollowUps hook returns hasFollowUps=false
- When: The MyAssignmentsPanel component renders initially
- Then: The panel content is collapsed (only header visible with empty state message)
- Data: Empty follow-ups array

### 13-5-my-assignments-panel-UNIT-012: MyAssignmentsPanel expand/collapse toggle works
- Priority: P1
- Type: unit
- Given: The MyAssignmentsPanel is rendered with follow-ups (expanded by default)
- When: The user clicks the expand/collapse chevron button
- Then: The panel content collapses and is no longer visible; clicking again re-expands it
- Data: At least 1 mock follow-up item

### 13-5-my-assignments-panel-UNIT-013: MyAssignmentsPanel renders loading skeleton state
- Priority: P1
- Type: unit
- Given: The useMyFollowUps hook returns isLoading=true
- When: The MyAssignmentsPanel component renders
- Then: A loading skeleton/placeholder UI is displayed instead of follow-up entries
- Data: Hook in loading state

### 13-5-my-assignments-panel-UNIT-014: MyAssignmentsPanel renders error state with retry button
- Priority: P1
- Type: unit
- Given: The useMyFollowUps hook returns an error (e.g., network failure)
- When: The MyAssignmentsPanel component renders
- Then: An error message is displayed with a "Retry" button; clicking the retry button calls the refetch function
- Data: Hook in error state with error message

### 13-5-my-assignments-panel-UNIT-015: MyAssignmentsPanel hides empty status groups
- Priority: P2
- Type: unit
- Given: The useMyFollowUps hook returns follow-ups with only "assigned" status (no in_progress or resolved)
- When: The MyAssignmentsPanel component renders
- Then: Only the "Assigned" status group is rendered; empty groups for "In Progress" and "Resolved" are not shown (or shown collapsed)
- Data: 2 follow-ups all with status "assigned"

### 13-5-my-assignments-panel-E2E-001: Panel renders in correct position on morning report page
- Priority: P0
- Type: e2e
- Given: The manager is logged in and navigates to the morning report page, and has at least 1 follow-up assignment
- When: The morning report page fully loads
- Then: The MyAssignmentsPanel is positioned between MorningSummarySection and the action items section (WorkcenterScorecard/InsightEvidenceCardList)
- Data: At least 1 follow-up in the database for the current user

## AC2: Status group movement and "New update" indicator on refresh

Given a follow-up was recently updated by the assignee, When the panel refreshes, Then the follow-up moves to its new status group And a "New update" indicator appears if the manager hasn't viewed the update yet.

### 13-5-my-assignments-panel-UNIT-016: Follow-up moves to new status group after refetch
- Priority: P0
- Type: unit
- Given: A follow-up initially has status "assigned" and the hook has fetched data; the follow-up's status is then updated to "in_progress" on the server
- When: The refetch() function is called on useMyFollowUps
- Then: The follow-up moves from grouped.assigned to grouped.in_progress; grouped.assigned count decreases by 1; grouped.in_progress count increases by 1
- Data: Initial API response with 1 assigned follow-up; second API response with same follow-up now in_progress

### 13-5-my-assignments-panel-UNIT-017: "New update" dot indicator shows when updated_at > lastViewedTimestamp
- Priority: P0
- Type: unit
- Given: A follow-up has updated_at="2026-02-11T10:30:00Z" and localStorage key "followup-viewed-{id}" has value "2026-02-11T08:00:00Z" (earlier than updated_at)
- When: The FollowUpEntry component renders for this follow-up
- Then: A "New update" visual indicator (blue dot or similar) is visible on the entry
- Data: Follow-up with updated_at later than the localStorage timestamp

### 13-5-my-assignments-panel-UNIT-018: "New update" indicator does NOT show when already viewed
- Priority: P0
- Type: unit
- Given: A follow-up has updated_at="2026-02-11T10:30:00Z" and localStorage key "followup-viewed-{id}" has value "2026-02-11T11:00:00Z" (later than updated_at)
- When: The FollowUpEntry component renders for this follow-up
- Then: No "New update" indicator is visible on the entry
- Data: Follow-up with updated_at earlier than the localStorage timestamp

### 13-5-my-assignments-panel-UNIT-019: "New update" indicator shows when no localStorage entry exists
- Priority: P1
- Type: unit
- Given: A follow-up exists but no localStorage key "followup-viewed-{id}" has been set (first time viewing)
- When: The FollowUpEntry component renders for this follow-up
- Then: A "New update" indicator is visible (since the manager has never viewed it, any update should be flagged)
- Data: Follow-up without corresponding localStorage key

### 13-5-my-assignments-panel-UNIT-020: "New update" indicator clears when detail dialog is opened
- Priority: P0
- Type: unit
- Given: A follow-up has a "New update" indicator visible (updated_at > lastViewedTimestamp)
- When: The user clicks on the follow-up entry and the detail dialog opens
- Then: localStorage key "followup-viewed-{id}" is updated to the current timestamp; when the dialog closes and the entry re-renders, the "New update" indicator is no longer visible
- Data: Follow-up with updated_at later than localStorage value

### 13-5-my-assignments-panel-UNIT-021: useMyFollowUps refetch() triggers new API call
- Priority: P1
- Type: unit
- Given: The hook has completed initial fetch successfully
- When: The refetch() function is called
- Then: A new API call is made to GET /api/v1/actions/followups; the loading state may briefly be true; updated data is returned
- Data: Mock fetch that can be called multiple times with different responses

### 13-5-my-assignments-panel-UNIT-022: Backend returns updated_at reflecting latest status change
- Priority: P1
- Type: integration
- Given: A follow-up was created at T1 with status "assigned" and later updated to "in_progress" at T2
- When: GET /api/v1/actions/followups?assigned_by=me is called
- Then: The follow-up's updated_at field reflects T2 (the time of the status change), not T1
- Data: Follow-up with updated_at > created_at

## AC3: Click follow-up entry opens detail view with full assignment context

Given the manager clicks on a follow-up entry, When the detail view opens, Then it shows the full assignment context: original action item, assigned note, assignee's status updates with timestamps.

### 13-5-my-assignments-panel-UNIT-023: FollowUpEntry click triggers detail dialog open
- Priority: P0
- Type: unit
- Given: A FollowUpEntry component is rendered with a follow-up item
- When: The user clicks on the entry
- Then: The onSelect callback is called with the follow-up's data (or ID), triggering the FollowUpDetailDialog to open
- Data: Single follow-up item

### 13-5-my-assignments-panel-UNIT-024: FollowUpDetailDialog renders original action item context
- Priority: P0
- Type: unit
- Given: A FollowUpDetailDialog is opened with a follow-up that has action_summary="Investigate pressure anomaly", category="safety", asset_name="Grinder 5"
- When: The dialog renders
- Then: The action summary text is displayed; the category is shown (with PriorityBadge if applicable); the asset name is displayed
- Data: Follow-up with action_summary, category, asset_name

### 13-5-my-assignments-panel-UNIT-025: FollowUpDetailDialog renders manager's assignment note
- Priority: P0
- Type: unit
- Given: A FollowUpDetailDialog is opened with a follow-up that has note="Please check by EOD and report back"
- When: The dialog renders
- Then: The manager's assignment note "Please check by EOD and report back" is visible in the dialog
- Data: Follow-up with a non-null note field

### 13-5-my-assignments-panel-UNIT-026: FollowUpDetailDialog renders current status badge
- Priority: P0
- Type: unit
- Given: A FollowUpDetailDialog is opened with a follow-up with status="in_progress"
- When: The dialog renders
- Then: A status badge is displayed showing "In Progress" with the amber/warning color variant
- Data: Follow-up with status "in_progress"

### 13-5-my-assignments-panel-UNIT-027: FollowUpDetailDialog renders timestamps for creation and last update
- Priority: P1
- Type: unit
- Given: A FollowUpDetailDialog is opened with a follow-up that has created_at="2026-02-09T08:30:00Z" and updated_at="2026-02-10T14:00:00Z"
- When: The dialog renders
- Then: Both timestamps are displayed in the timeline/detail section, showing when the assignment was created and when it was last updated
- Data: Follow-up with distinct created_at and updated_at values

### 13-5-my-assignments-panel-UNIT-028: FollowUpDetailDialog handles follow-up with no note gracefully
- Priority: P1
- Type: unit
- Given: A FollowUpDetailDialog is opened with a follow-up where note=null
- When: The dialog renders
- Then: The note section either shows a placeholder (e.g., "No note provided") or is omitted entirely; no error is thrown
- Data: Follow-up with note=null

### 13-5-my-assignments-panel-UNIT-029: FollowUpDetailDialog renders assignee email
- Priority: P1
- Type: unit
- Given: A FollowUpDetailDialog is opened with a follow-up with assigned_to_email="jane@company.com"
- When: The dialog renders
- Then: The assignee's email "jane@company.com" is displayed in the dialog
- Data: Follow-up with assigned_to_email

### 13-5-my-assignments-panel-UNIT-030: FollowUpDetailDialog opens and closes correctly
- Priority: P1
- Type: unit
- Given: The MyAssignmentsPanel is rendered with follow-ups
- When: The user clicks a follow-up entry to open the detail dialog, then clicks the close button or outside the dialog
- Then: The dialog opens with the correct follow-up data, and closes cleanly when dismissed, returning focus to the panel
- Data: At least 1 follow-up item

### 13-5-my-assignments-panel-UNIT-031: FollowUpDetailDialog updates localStorage on open to clear "New update"
- Priority: P0
- Type: unit
- Given: A follow-up has a "New update" indicator (updated_at > localStorage value)
- When: The FollowUpDetailDialog is opened for this follow-up
- Then: localStorage key "followup-viewed-{id}" is set to the current timestamp (Date.now()), marking the update as viewed
- Data: Follow-up with updated_at > existing localStorage timestamp

## AC4: Empty state when no open follow-ups

Given the manager has no open follow-ups, When the panel renders, Then it shows an empty state: "No open follow-ups. Assign actions from the report below."

### 13-5-my-assignments-panel-UNIT-032: Empty state renders exact message text
- Priority: P0
- Type: unit
- Given: The useMyFollowUps hook returns hasFollowUps=false with an empty followups array
- When: The MyAssignmentsPanel component renders
- Then: The text "No open follow-ups. Assign actions from the report below." is displayed verbatim
- Data: Empty API response (followups: [], total_count: 0)

### 13-5-my-assignments-panel-UNIT-033: Empty state renders when API returns zero follow-ups
- Priority: P0
- Type: unit
- Given: The API returns a valid response with followups=[], total_count=0, counts_by_status={assigned: 0, in_progress: 0, resolved: 0}
- When: The useMyFollowUps hook processes the response and MyAssignmentsPanel renders
- Then: The empty state is shown; no status group headers are rendered; hasFollowUps is false
- Data: Empty API response

### 13-5-my-assignments-panel-INT-009: Backend returns empty list for manager with no follow-ups
- Priority: P0
- Type: integration
- Given: The authenticated manager has not created any follow-up assignments
- When: GET /api/v1/actions/followups?assigned_by=me is called
- Then: The response returns status 200 with followups=[], total_count=0, counts_by_status={"assigned": 0, "in_progress": 0, "resolved": 0}
- Data: No follow-up records with assigned_by matching current user

### 13-5-my-assignments-panel-E2E-002: Empty state displays on morning report when manager has no assignments
- Priority: P1
- Type: e2e
- Given: The manager is logged in and has no follow-up assignments in the database
- When: The morning report page loads
- Then: The MyAssignmentsPanel shows the empty state message "No open follow-ups. Assign actions from the report below."
- Data: No follow-up records for the current user

edge_cases:
  - Follow-up with null/missing asset_name: FollowUpEntry should handle gracefully (display fallback or omit asset field)
  - Follow-up with null/missing category: FollowUpDetailDialog should not crash when category is null
  - Very long assignee email address: FollowUpEntry should truncate or wrap without breaking layout
  - Manager has follow-ups only in one status (e.g., all "assigned"): Only one status group should render; others should be hidden or empty
  - Rapid refetch calls (double-click refresh): useMyFollowUps should debounce or handle concurrent requests without race conditions
  - localStorage unavailable (private browsing): "New update" indicator logic should handle gracefully without throwing errors
  - Follow-up with created_at very close to now (less than 1 minute): formatRelativeTime should return "0m ago" or similar, not negative values
  - Timestamps in different timezones: formatRelativeTime should correctly handle ISO strings with timezone offsets
  - Panel with large number of follow-ups (50+): ScrollArea should be used; rendering performance should be acceptable
  - Session expiry during panel interaction: useMyFollowUps should handle auth error gracefully and show error state

error_scenarios:
  - Network failure during follow-up fetch: useMyFollowUps returns error state; MyAssignmentsPanel shows error UI with retry button
  - Expired/invalid Supabase session: Hook detects auth error and surfaces user-friendly "AUTH_ERROR" message
  - API returns 500 server error: Hook detects server error and surfaces "SERVER_ERROR" message with retry
  - API returns malformed JSON: Hook should catch parse error and set error state
  - Backend Supabase service-role client fails to connect: GET /followups returns 500; frontend handles gracefully
  - Backend fails to resolve assigned_to email (user deleted): assigned_to_email should be null or "Unknown"; entry still renders

test_file_mapping:
  - 13-5-my-assignments-panel-INT-001 to INT-009: apps/api/tests/test_followups_list.py
  - 13-5-my-assignments-panel-UNIT-001 to UNIT-002: apps/api/tests/test_followups_list.py (schema validation section)
  - 13-5-my-assignments-panel-UNIT-003 to UNIT-004, UNIT-016, UNIT-021: apps/web/src/hooks/__tests__/useMyFollowUps.test.ts
  - 13-5-my-assignments-panel-UNIT-005 to UNIT-015, UNIT-032, UNIT-033: apps/web/src/components/action-list/__tests__/MyAssignmentsPanel.test.tsx
  - 13-5-my-assignments-panel-UNIT-007 to UNIT-009, UNIT-017 to UNIT-020: apps/web/src/components/action-list/__tests__/FollowUpEntry.test.tsx
  - 13-5-my-assignments-panel-UNIT-023 to UNIT-031: apps/web/src/components/action-list/__tests__/FollowUpDetailDialog.test.tsx
  - 13-5-my-assignments-panel-E2E-001 to E2E-002: apps/web/src/__tests__/my-assignments-panel.e2e.test.tsx (or integration-level test)

TEST SPEC END

---
