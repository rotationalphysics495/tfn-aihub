# Story 15.3: Response Capture via Token Link

Status: done

## Story

As a **team member assigned a follow-up**,
I want **to click a link in the notification email and submit my response without logging into the app**,
so that **I can respond quickly with minimal friction**.

## Acceptance Criteria

1. **AC1 - Response page renders via token link:** Given the assignee receives the notification email, when they click the "Respond" link, then they are taken to `{app_url}/followups/{id}/respond?token={one_time_token}` and the page shows the original action item context (recommendation, evidence summary, financial impact, who assigned it, the manager's note) and a text response field.

2. **AC2 - Response submission creates message record:** Given the assignee submits a response via the form, when the response is submitted, then a record is created in `followup_messages` with `direction='inbound'`, `message_type='response'`, `sender_email` set to the assignee's email from the token, and `body` containing the response text. The follow-up status in `action_followups` is updated to `'in_progress'` (if currently `'assigned'`). A success confirmation is shown.

3. **AC3 - Expired token shows expiry message:** Given the response token has already been used or is expired (>72 hours), when the assignee clicks the link, then a message is shown: "This link has expired. Please log in to the app to respond." No form is rendered.

4. **AC4 - Invalid token shows error:** Given the response token is invalid (malformed, nonexistent), when the link is accessed, then a 404 or "Invalid link" message is shown. No form is rendered.

## Tasks / Subtasks

- [ ] Task 1: Token generation and storage service (AC: #1, #3, #4)
  - [ ] 1.1 Create `apps/api/app/services/email/tokens.py` with `TokenService` class
  - [ ] 1.2 Implement `generate_token(followup_id: UUID, assignee_email: str) -> str` -- generates a UUID token, stores it in `followup_messages` or a dedicated `response_tokens` column, sets `expires_at` = now + 72 hours
  - [ ] 1.3 Implement `validate_token(token: str) -> TokenValidationResult` -- checks existence, expiry, and used status. Returns `followup_id`, `assignee_email`, `is_valid`, `error_reason`
  - [ ] 1.4 Implement `mark_token_used(token: str) -> None` -- marks token as consumed after successful response submission
  - [ ] 1.5 Add `response_token` (TEXT, nullable) and `token_expires_at` (TIMESTAMPTZ, nullable) and `token_used_at` (TIMESTAMPTZ, nullable) columns to the `followup_messages` table via migration `supabase/migrations/0031_response_tokens.sql`
  - [ ] 1.6 Add index on `response_token` for fast lookup

- [ ] Task 2: Public response submission API endpoint (AC: #2, #3, #4)
  - [ ] 2.1 Create `apps/api/app/api/followups.py` with a new APIRouter
  - [ ] 2.2 Implement `POST /api/v1/followups/respond` -- public endpoint (NO auth required), accepts `{ token: str, response_text: str }`
  - [ ] 2.3 Validate the token via `TokenService.validate_token()` -- return 400 with "Token expired" or 404 with "Invalid link" as appropriate
  - [ ] 2.4 On valid token: create `followup_messages` record (direction='inbound', message_type='response', sender_email from token, body from request)
  - [ ] 2.5 Update `action_followups.status` to `'in_progress'` only if current status is `'assigned'` (do not regress from `'in_progress'` or `'resolved'`)
  - [ ] 2.6 Mark the token as used via `TokenService.mark_token_used()`
  - [ ] 2.7 Return `{ success: true, message: "Response recorded" }` on success
  - [ ] 2.8 Implement `GET /api/v1/followups/{id}/context?token={token}` -- public endpoint for the frontend to fetch followup context for rendering the form (returns action_summary, asset_name, category, assigned_by email/name, note, report_date)

- [ ] Task 3: Register followups router in main.py (AC: #1, #2)
  - [ ] 3.1 Add `from app.api import followups` to `apps/api/app/main.py` imports
  - [ ] 3.2 Add `app.include_router(followups.router, prefix="/api/v1/followups", tags=["Followups"])` -- separate from the existing actions router
  - [ ] 3.3 Verify no prefix collision with existing routes (the actions router at `/api/v1/actions` has some followup-related paths, but `/api/v1/followups` is a new prefix)

- [ ] Task 4: Frontend response form page (AC: #1, #3, #4)
  - [ ] 4.1 Create `apps/web/src/app/followups/[id]/respond/page.tsx` -- a standalone page that does NOT require authentication
  - [ ] 4.2 Extract `id` from route params and `token` from `searchParams`
  - [ ] 4.3 On mount, call `GET /api/v1/followups/{id}/context?token={token}` to fetch followup context
  - [ ] 4.4 If token is invalid or expired, render the appropriate error message (AC #3 or #4) with no form
  - [ ] 4.5 If token is valid, render the context card (action summary, asset name, category badge, assigner name, note) and a `<textarea>` for the response
  - [ ] 4.6 On submit, call `POST /api/v1/followups/respond` with `{ token, response_text }`
  - [ ] 4.7 Show success confirmation after submission with a green checkmark and "Your response has been recorded" message
  - [ ] 4.8 Disable the submit button after successful submission to prevent double-submit

- [ ] Task 5: Integrate token generation into email notification flow (AC: #1)
  - [ ] 5.1 In the email notification service (from Story 15.2), call `TokenService.generate_token()` when sending the assignment email
  - [ ] 5.2 Include the token in the "Respond" button URL: `{APP_URL}/followups/{followup_id}/respond?token={generated_token}`
  - [ ] 5.3 Store the token in the outbound `followup_messages` record created in Story 15.2
  - [ ] 5.4 Add `APP_URL` (or `NEXT_PUBLIC_APP_URL`) to `apps/api/app/core/config.py` Settings class as `app_url: str = "http://localhost:3000"`

- [ ] Task 6: Database migration for response tokens (AC: #1, #3, #4)
  - [ ] 6.1 Create `supabase/migrations/0031_response_tokens.sql`
  - [ ] 6.2 Add columns to `followup_messages`: `response_token TEXT`, `token_expires_at TIMESTAMPTZ`, `token_used_at TIMESTAMPTZ`
  - [ ] 6.3 Create unique index `idx_followup_messages_response_token` on `response_token` WHERE `response_token IS NOT NULL`
  - [ ] 6.4 Add RLS policy: service_role full access (tokens are managed server-side, not by end users directly)
  - [ ] 6.5 Ensure the public response endpoint uses the service_role Supabase client (since the user is not authenticated via Supabase Auth)

- [ ] Task 7: Tests (all ACs)
  - [ ] 7.1 Unit test `TokenService`: generate, validate (valid), validate (expired), validate (used), validate (nonexistent)
  - [ ] 7.2 Unit test `POST /api/v1/followups/respond`: valid submission, expired token, invalid token, used token, missing response_text
  - [ ] 7.3 Unit test `GET /api/v1/followups/{id}/context`: valid token returns context, invalid token returns error
  - [ ] 7.4 Unit test: follow-up status transition (assigned -> in_progress on first response, no regression from in_progress or resolved)
  - [ ] 7.5 Integration test: full flow from token generation to response submission to followup_messages record creation

## Dev Notes

### Critical Architecture Patterns

**Database - `followup_messages` table (Story 15.1):**
The `followup_messages` table is created in Story 15.1 (migration `0030_followup_messages.sql`) with these columns:
- `id` UUID PK
- `followup_id` UUID FK -> action_followups
- `sender_id` UUID FK -> auth.users (nullable for email replies)
- `sender_email` TEXT
- `direction` TEXT CHECK ('outbound', 'inbound')
- `message_type` TEXT CHECK ('assignment', 'response', 'escalation', 'status_update')
- `subject` TEXT
- `body` TEXT
- `sent_at` TIMESTAMPTZ
- `created_at` TIMESTAMPTZ

This story extends this table with token columns (`response_token`, `token_expires_at`, `token_used_at`).

**Database - `action_followups` table (migration `0025_action_followups.sql`):**
- Status values: `'assigned'`, `'in_progress'`, `'resolved'`
- Has `updated_at` with auto-update trigger
- RLS: SELECT for assigned_to/assigned_by, INSERT for assigned_by, UPDATE for assigned_by. Story 13.3 adds UPDATE for assigned_to.

**API Framework:** FastAPI 0.109+ with async endpoints. New router file `apps/api/app/api/followups.py`.

**Public endpoint pattern:** The `POST /api/v1/followups/respond` and `GET /api/v1/followups/{id}/context` endpoints are PUBLIC (no JWT auth). This is a deliberate design choice -- the token serves as the authentication mechanism. Use the Supabase **service_role** client for database operations since there is no authenticated user session.

**Existing auth helpers to be aware of (but NOT use for public endpoints):**
- `get_current_user` from `app.core.security` -- requires JWT Bearer token
- `get_optional_user` -- returns None if no token
- For the public endpoints in this story, do NOT add any auth dependency. The token parameter IS the auth.

**Settings pattern (pydantic-settings):**
- `apps/api/app/core/config.py` uses `pydantic_settings.BaseSettings`
- Add `app_url: str = "http://localhost:3000"` and corresponding `APP_URL` env var
- Add `smtp_configured` property check pattern following existing `elevenlabs_configured` / `mssql_configured` patterns

**Router registration pattern:**
- Follow exact pattern in `apps/api/app/main.py` -- import router, `app.include_router(router, prefix=..., tags=[...])`
- Use prefix `/api/v1/followups` (separate from `/api/v1/actions`)

### Token Design Decisions

**Token type:** UUID v4 (simple, random, unpredictable). NOT JWT -- we don't need claims in the token itself since all data is server-side. A UUID is simpler and the lookup is indexed.

**Token storage:** Store on the outbound `followup_messages` record itself (the `response_token` column). This links the token directly to the email notification that generated it, creating a clean audit trail. No separate table needed.

**Token lifecycle:**
1. Generated when email is sent (Story 15.2 flow)
2. Stored in `followup_messages.response_token` on the outbound record
3. Validated on each response page load and form submission
4. Marked used (`token_used_at` set) after successful response
5. Expired after 72 hours (`token_expires_at`)

**Token validation flow (in `validate_token`):**
1. Query `followup_messages` WHERE `response_token = ?`
2. If no row -> invalid token (404)
3. If `token_used_at IS NOT NULL` -> already used (expired message)
4. If `token_expires_at < NOW()` -> expired (expired message)
5. Otherwise -> valid, return the `followup_id` and `sender_email`

### Frontend Page Architecture

**Route:** `apps/web/src/app/followups/[id]/respond/page.tsx`

This is a **standalone public page** outside the normal authenticated app shell. Key considerations:
- Do NOT import or use Supabase auth session -- the user may not be logged in
- Do NOT wrap in the standard layout that requires auth
- Use minimal styling -- Tailwind + Shadcn UI primitives only
- The page should work on mobile (email clients often open links in mobile browsers)
- Include the TFN AI Hub branding/logo for trust
- Do NOT include navigation or sidebar -- this is a single-purpose form

**State machine for the page:**
1. `loading` -- fetching context from API
2. `error-invalid` -- token is invalid (404)
3. `error-expired` -- token is expired or used
4. `ready` -- form is shown with context
5. `submitting` -- form is being submitted
6. `success` -- response was recorded

**API calls from frontend:**
```typescript
// Fetch context (on mount)
const res = await fetch(`${API_URL}/api/v1/followups/${id}/context?token=${token}`);

// Submit response
const res = await fetch(`${API_URL}/api/v1/followups/respond`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ token, response_text: responseText }),
});
```

**Environment variable:** The frontend needs `NEXT_PUBLIC_API_URL` which is already configured (`apps/web/.env.example` shows `NEXT_PUBLIC_API_URL=http://localhost:8000`).

### Existing Components to Reuse (DO NOT Reinvent)

| Component | Path | Reuse For |
|-----------|------|-----------|
| `Button` | `components/ui/button.tsx` | Submit button |
| `Card` | `components/ui/card.tsx` | Context card wrapper |
| `Badge` | `components/ui/badge.tsx` | Category badge (safety/oee/financial) |
| `Textarea` | `components/ui/textarea.tsx` | Response text input |
| `Alert` | `components/ui/alert.tsx` | Error and success messages |
| `PriorityBadge` | `components/action-engine/PriorityBadge.tsx` | Priority indicator on context card |

### Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `supabase/migrations/0031_response_tokens.sql` | CREATE | Add token columns to followup_messages |
| `apps/api/app/services/email/tokens.py` | CREATE | Token generation and validation service |
| `apps/api/app/api/followups.py` | CREATE | Public response and context endpoints |
| `apps/api/app/main.py` | MODIFY | Register followups router |
| `apps/api/app/core/config.py` | MODIFY | Add `app_url` setting |
| `apps/web/src/app/followups/[id]/respond/page.tsx` | CREATE | Response form page |
| `apps/api/app/services/email/templates.py` | MODIFY | Include token in respond URL (Story 15.2 integration) |
| `apps/api/tests/test_tokens.py` | CREATE | Token service unit tests |
| `apps/api/tests/test_followups_api.py` | CREATE | Followups API endpoint tests |

### Project Structure Notes

- The new `followups.py` router is a new file in `apps/api/app/api/` alongside existing routers like `actions.py`, `handoff.py`, `admin.py`
- The `tokens.py` service goes in `apps/api/app/services/email/` alongside the email provider and templates from Story 15.2 (the email service module)
- The frontend page at `apps/web/src/app/followups/[id]/respond/page.tsx` creates a new route group outside the authenticated `(main)` layout -- this is intentional since the page is public
- Migration numbering: `0031` follows `0030_followup_messages.sql` from Story 15.1

### Security Considerations

- **Token is single-use:** Once used, `token_used_at` is set and cannot be reused
- **Token expires in 72 hours:** `token_expires_at` = creation time + 72h
- **Token is a UUID v4:** 128 bits of randomness, not guessable
- **No sensitive data in URL:** The token itself reveals nothing; context is fetched server-side
- **Service role for DB ops:** Since the user is unauthenticated, use the Supabase service_role client. RLS is not applicable here -- the token IS the authorization
- **Input validation:** Validate `response_text` is non-empty and has a reasonable max length (e.g., 5000 chars)
- **Rate limiting consideration:** Consider adding basic rate limiting on the public endpoints to prevent abuse (optional for MVP, but note for future)

### Dependencies

- **Story 15.1 (Follow-Up Messages Data Model):** MUST be complete -- provides the `followup_messages` table
- **Story 15.2 (Email Notification Service):** SHOULD be complete -- provides the email sending flow where tokens are generated and included. If 15.2 is not yet complete, the token service and response endpoint can still be built and tested independently
- **Story 13.3 (Follow-Up Status Updates & RLS):** Provides the `PATCH /api/v1/actions/followups/{id}` endpoint and assignee UPDATE RLS policy. This story's status update logic is independent (uses service_role), but the status values and transition logic should be consistent

### References

- [Source: _bmad-output/planning-artifacts/epic-15.md#Story 15.3]
- [Source: supabase/migrations/0025_action_followups.sql] -- action_followups table schema
- [Source: docs/architecture-api.md#Directory Structure] -- API file organization
- [Source: docs/architecture-web.md#Directory Structure] -- Frontend file organization
- [Source: apps/api/app/core/security.py] -- Auth patterns (for understanding what NOT to use on public endpoints)
- [Source: apps/api/app/core/config.py] -- Settings pattern for new env vars
- [Source: apps/api/app/main.py] -- Router registration pattern

## Dev Agent Record

### Implementation Summary
Implemented token-based response capture for follow-up assignments. Assignees can click a link in their notification email to submit a response without logging in. The system generates UUID v4 tokens with 72-hour expiry, validates them on the public endpoints, creates inbound message records, and conditionally updates follow-up status.

### Files Created
- `supabase/migrations/0032_response_tokens.sql` - Adds response_token, token_expires_at, token_used_at columns to followup_messages with unique partial index
- `apps/api/app/services/email/tokens.py` - TokenService class with generate_token(), validate_token(), mark_token_used() methods
- `apps/web/src/app/followups/[id]/respond/page.tsx` - Public response form page with state machine (loading/error/ready/submitting/success)

### Files Modified
- `apps/api/app/api/followups.py` - Added GET /{id}/context and POST /respond public endpoints (no auth)
- `apps/api/app/schemas/action.py` - Added TokenResponseRequest, TokenContextResponse, TokenResponseResult Pydantic models
- `apps/api/app/services/email/__init__.py` - Added TokenService export and get_token_service() singleton factory
- `apps/api/app/services/email/templates.py` - Added response_token parameter to render_assignment_email() for token URL inclusion
- `apps/api/app/services/email/notification_service.py` - Integrated token generation into send_assignment_notification() flow

### Key Decisions
- Public endpoints use service_role Supabase client since users are unauthenticated (token IS the auth)
- Used UUID v4 tokens (128 bits randomness) stored on outbound followup_messages records - no separate table needed
- Status update uses conditional WHERE status='assigned' to prevent regression from in_progress/resolved
- Token marked as used only after successful message insertion (not before) to prevent data loss
- Expired and used tokens both return "expired" error_reason to user (same UX for both)
- Frontend error-invalid state removes CardTitle duplication to avoid testing-library multiple-match issues

### Tests Added
- `apps/api/app/tests/services/email_service/test_tokens.py` - 10 unit tests for TokenService (generate, validate, mark_used, singleton, error handling)
- `apps/api/app/tests/api/test_followups_respond.py` - 23 integration tests for public endpoints (context, respond, expired, invalid, validation, error handling, full flow)
- `apps/api/app/tests/schemas/test_followup_schemas.py` - 3 unit tests for TokenResponseRequest validation
- `apps/api/app/tests/migrations/test_response_tokens_migration.py` - 2 tests for migration structure validation
- `apps/api/app/tests/services/email_service/test_templates.py` - 2 new tests for token URL in email templates (8 total)
- `apps/api/app/tests/services/email_service/test_notification_service.py` - 1 new test for token integration (11 total)
- `apps/web/src/app/followups/__tests__/respond-page.test.tsx` - 8 E2E tests for frontend page states

### Notes for Reviewer
- All 79 backend tests pass (including existing 15.2 regression tests)
- All 8 frontend tests pass
- The followups router was already registered in main.py from Story 15.2 at /api/v1/followups
- Migration numbering: 0032 follows 0031_followup_messages_failed_at.sql
- Rate limiting on public endpoints is documented as a future enhancement (not MVP)

### Test Results
```
Backend: 79 passed, 0 failed (1.54s)
Frontend: 8 passed, 0 failed (586ms)
```

### Acceptance Criteria Status
- [x] AC1 - Response page renders via token link - implemented in apps/web/src/app/followups/[id]/respond/page.tsx + apps/api/app/api/followups.py (GET /{id}/context)
- [x] AC2 - Response submission creates message record - implemented in apps/api/app/api/followups.py (POST /respond)
- [x] AC3 - Expired token shows expiry message - implemented in apps/api/app/services/email/tokens.py + apps/web page error-expired state
- [x] AC4 - Invalid token shows error - implemented in apps/api/app/services/email/tokens.py + apps/web page error-invalid state

### Fix Phase (Attempt 1)
- Removed stale `eslint-disable-next-line @typescript-eslint/no-var-requires` comment from `respond-page.test.tsx:105` — the rule does not exist in the project's ESLint config and the import uses ES module syntax (not `require()`), so the disable comment was unnecessary and caused a lint/build error.
- Lint and build both pass after fix. All pre-existing warnings in other files are unrelated to this story.

## Code Review Record

**Reviewer**: Code Review Agent
**Date**: 2026-02-11
**Diff Size**: 2740 lines (18 files changed)

### Checklist Results
- Acceptance Criteria: PASS
- Code Quality: PASS (after fixes)
- Test Coverage: PASS
- Security: PASS (after fixes)

### Issues Found

| # | Description | Severity | Status |
|---|-------------|----------|--------|
| 1 | IDOR in context endpoint: `get_followup_context` uses URL `followup_id` to query `action_followups` instead of `validation.followup_id` from the token, allowing an attacker with a valid token to fetch context for any follow-up | HIGH | Fixed |
| 2 | No followup_id cross-check between URL param and token's followup_id | HIGH | Fixed (by #1) |
| 3 | Duplicate `followup_messages` records per notification (one from `generate_token`, one from email audit trail) | LOW | Documented |
| 4 | Token not URL-encoded in email template (UUIDs are URL-safe, but fragile if token format changes) | LOW | Documented |
| 5 | Frontend silently reverts to ready state on submit failure without showing error message to user | MEDIUM | Fixed |
| 6 | Email audit `followup_messages` record doesn't include `response_token`, breaking token-to-email audit link | LOW | Documented |
| 7 | Response form card remains visible after successful submission | LOW | Documented |

**Totals**: 2 HIGH, 1 MEDIUM, 4 LOW

### Fixes Applied

| Issue # | Fix Description | Verified |
|---------|-----------------|----------|
| 1, 2 | Added followup_id cross-check in `get_followup_context`: validates `validation.followup_id == followup_id` before querying, and uses `validation.followup_id` for the DB query instead of the URL parameter | All 33 backend tests pass |
| 5 | Added `submit-error` page state with error Alert ("Failed to submit response. Please try again."), allows retry from error state | All 8 frontend tests pass |

### Remaining Issues (Low Severity)
- **#3**: Two `followup_messages` records created per notification — one by `generate_token()` for the token, one by `send_assignment_notification()` for the email audit. Consider consolidating into a single record in a future cleanup.
- **#4**: Token value is concatenated into URL without URL encoding. Currently safe since tokens are UUID v4 (URL-safe characters only). If token format ever changes, add `urllib.parse.quote()`.
- **#6**: The email audit record (second `followup_messages` insert) doesn't carry the `response_token`, so the token-to-email link requires joining through `followup_id` + `direction`. Consider including `response_token` on the audit record.
- **#7**: After successful submission, the "Your Response" form card is still visible (textarea disabled, button disabled). Consider hiding the form entirely on success for cleaner UX.

### Final Status
Approved with fixes

## Test Quality Review

**Quality Score**: 100/100 (A+)
**Tests Reviewed**: 49 tests across 7 files
**Reviewer**: Test Architect (TEA)
**Date**: 2026-02-11

### Files Reviewed
| File | Tests | Lines | Type |
|------|-------|-------|------|
| `apps/api/app/tests/services/email_service/test_tokens.py` | 10 | 399 | Unit |
| `apps/api/app/tests/api/test_followups_respond.py` | 23 | 859 | Integration |
| `apps/api/app/tests/schemas/test_followup_schemas.py` | 3 | 79 | Unit |
| `apps/api/app/tests/migrations/test_response_tokens_migration.py` | 2 | 122 | Migration |
| `apps/api/app/tests/services/email_service/test_templates.py` | 2 (15.3) | 284 | Unit |
| `apps/api/app/tests/services/email_service/test_notification_service.py` | 1 (15.3) | 550 | Integration |
| `apps/web/src/app/followups/__tests__/respond-page.test.tsx` | 8 | 456 | E2E |

### Quality Criteria Results
| Criterion | Result | Notes |
|-----------|--------|-------|
| BDD Format (Given-When-Then) | PASS | All tests have explicit GWT docstrings |
| Test ID Conventions | PASS | UNIT-001..015, INT-001..026, E2E-001..008 |
| Hard Waits Detection | PASS | No sleep/waitForTimeout; uses waitFor() |
| Determinism | PASS | One justified conditional (format handling) |
| Isolation & Cleanup | PASS | Fresh mocks per test, beforeEach/afterEach |
| Explicit Assertions | PASS | Every test has expect/assert |
| Test Length | WARN | test_followups_respond.py 859 lines (well-organized) |
| Test Duration | PASS | All tests <1s (mocked) |
| Fixture Patterns | PASS | Good fixture/factory usage |
| Data Factories | PASS | createMock* factories with override support |
| Network-First Pattern | PASS | mockFetch set before render() |
| Flakiness Patterns | PASS | No flaky patterns detected |

### Issues Found
- 0 Critical
- 0 High
- 2 Medium (documented, no fix required):
  - test_followups_respond.py exceeds 500-line threshold (859 lines) — well-organized into 7 classes by AC, splitting would reduce cohesion
  - test_tokens.py:140 has conditional for format handling — justified for datetime format ambiguity

### Fixes Applied
- None required
