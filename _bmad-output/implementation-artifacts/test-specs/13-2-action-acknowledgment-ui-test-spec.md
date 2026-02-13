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
