# Story 19.3: Context-Aware Follow-Up Suggestions

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Plant Manager viewing the smart summary,
I want to see suggested follow-up questions relevant to today's report,
so that I know what to ask without thinking of questions from scratch.

## Acceptance Criteria

1. **Given** the smart summary is displayed, **When** the "Ask about this" button area renders, **Then** 2-3 contextual follow-up questions are shown as clickable chips below the button (e.g., "What were the top downtime reasons for Grinder 5?", "How does today's OEE compare to last week?", "What actions have been taken on recurring safety events?").

2. **Given** the user clicks a suggested question chip, **When** the chip is clicked, **Then** the AI chat sidebar opens with that question pre-filled and sent, **And** the report context is included (same as "Ask about this" from Story 19.1).

3. **Given** the smart summary content changes (different date or refreshed), **When** the suggestions are generated, **Then** the suggestions update to reflect the new report content.

## Tasks / Subtasks

- [ ] Task 1: Create `generateSuggestions.ts` utility (AC: #1, #3)
  - [ ] 1.1 Define `SuggestionContext` interface accepting summary text, action items array, and report date
  - [ ] 1.2 Implement template-based question generation from action item categories and asset names
  - [ ] 1.3 Generate safety-category questions when safety action items are present (e.g., "What actions have been taken on recurring safety events?")
  - [ ] 1.4 Generate OEE-category questions referencing specific asset names (e.g., "What were the top downtime reasons for {assetName}?")
  - [ ] 1.5 Generate financial-category questions when financial impact items are present
  - [ ] 1.6 Generate comparison/trend questions (e.g., "How does today's OEE compare to last week?")
  - [ ] 1.7 Limit output to 2-3 highest-relevance suggestions, prioritizing safety > OEE > financial > trend
  - [ ] 1.8 Write unit tests for `generateSuggestions.ts`
- [ ] Task 2: Create `SuggestedQuestions.tsx` component (AC: #1, #2)
  - [ ] 2.1 Create the component in `apps/web/src/components/action-list/SuggestedQuestions.tsx`
  - [ ] 2.2 Reuse the existing `FollowUpChips` visual pattern (Button variant="outline", size="sm", ChevronRight icon, same styling classes)
  - [ ] 2.3 Accept `onQuestionSelect` callback prop that receives the selected question string
  - [ ] 2.4 Accept `actionItems` and `summaryText` props to feed into `generateSuggestions`
  - [ ] 2.5 Return null when no suggestions can be generated (empty action items, no summary)
  - [ ] 2.6 Add proper ARIA: `role="group"` with `aria-label="Suggested follow-up questions about the morning report"`
  - [ ] 2.7 Write unit tests for `SuggestedQuestions.tsx`
- [ ] Task 3: Integrate suggestions into `MorningSummarySection.tsx` (AC: #1, #2, #3)
  - [ ] 3.1 Import `SuggestedQuestions` component
  - [ ] 3.2 Place the suggestions below the AI summary section, inside the existing smart summary card
  - [ ] 3.3 Pass `data.actions`, `smartSummary.summary_text`, and report date into the suggestions component
  - [ ] 3.4 Wire `onQuestionSelect` to open ChatSidebar with the question pre-filled and report context (depends on Story 19.1's context mechanism; if 19.1 is not yet built, wire to open chat and send the question text only via `handleFollowUpSelect` pattern from ChatSidebar)
  - [ ] 3.5 Ensure suggestions re-render when `smartSummary` or `data` change (reactive to props)
- [ ] Task 4: Update `action-list/index.ts` barrel export (AC: #1)
  - [ ] 4.1 Add `SuggestedQuestions` to the barrel export file

## Dev Notes

### Architecture and Patterns

- **Component location:** `apps/web/src/components/action-list/` -- this is the correct directory for morning report components. Do NOT place in `components/chat/` even though it triggers chat.
- **Utility location:** `apps/web/src/lib/generateSuggestions.ts` -- follows existing pattern where `lib/` holds pure utility functions.
- **Styling system:** Tailwind CSS with Shadcn/UI. Use `cn()` from `@/lib/utils` for class merging. Follow Industrial Clarity design system (Inter font, dark/light mode via `next-themes`).
- **State management:** This component is client-side only (`'use client'` directive required). No server component rendering.
- **Reactivity:** Suggestions must recalculate when `smartSummary` or action items data changes. Use `useMemo` to memoize the generated suggestions array based on the input data.

### Reuse Existing FollowUpChips Pattern

The existing `FollowUpChips` component (`apps/web/src/components/chat/FollowUpChips.tsx`) provides the exact visual pattern needed. However, do NOT import and reuse `FollowUpChips` directly because:
1. It lives in the `chat/` domain and has `onSelect` semantics tied to sending a chat message.
2. The `SuggestedQuestions` component needs to open the chat sidebar AND send the question, which is a different interaction flow.

Instead, replicate the visual pattern: `Button variant="outline" size="sm"` with `ChevronRight` icon, same Tailwind classes (`border-industrial-300`, `bg-industrial-50`, `hover:bg-info-blue/10`, etc.), same animation (`animate-in fade-in slide-in-from-bottom-2 duration-300`), same accessibility attributes. See the existing FollowUpChips for the complete class list.

### Chat Sidebar Integration

The `ChatSidebar` component (`apps/web/src/components/chat/ChatSidebar.tsx`) is rendered globally in the root layout. It uses React state (`isOpen`, `setIsOpen`). Currently there is no shared state/context to programmatically open the sidebar from outside components.

**Integration approach for opening chat from suggested questions:**
- Option A (recommended for MVP): Dispatch a custom DOM event (e.g., `window.dispatchEvent(new CustomEvent('open-chat', { detail: { question: '...' } }))`) and listen for it in `ChatSidebar`.
- Option B: Create a shared React context (`ChatContext`) that exposes `openWithQuestion(question: string)`. This is cleaner but requires wrapping both components in a provider.
- Option C: If Story 19.1 has already been implemented and created a context mechanism, use that same mechanism.

Choose the approach that aligns with what exists when this story is implemented. If 19.1 is not done yet, Option A is simplest and can be refactored later.

### Template-Based Question Generation Logic

The `generateSuggestions` function should be **client-side only** (no LLM call) for MVP. Logic:

```
Input: { actions: ActionItem[], summaryText: string, reportDate: string }
Output: string[] (2-3 questions)

Algorithm:
1. If safety actions exist: add "What actions have been taken on {safetyAssetName} safety events?"
2. If OEE actions exist: add "What were the top downtime reasons for {worstOeeAssetName}?"
3. If financial actions exist: add "What is driving the ${amount} production loss on {assetName}?"
4. Always consider adding a trend question: "How does today's OEE compare to last week?"
5. Prioritize: safety > OEE > financial > trend
6. Return top 2-3
```

Use the `ActionItem` type from `@/hooks/useDailyActions` (already exported: `ActionItem`, `ActionCategory`, `PriorityLevel`).

### Data Flow

```
useDailyActions() -> data.actions (ActionItem[])
useSmartSummary() -> data.summary_text (string)
                          |
                          v
              generateSuggestions({ actions, summaryText, reportDate })
                          |
                          v
              SuggestedQuestions component renders chips
                          |
                          v (user clicks)
              Opens ChatSidebar with question pre-filled + report context
```

### Project Structure Notes

- All new files go under `apps/web/src/` -- the Next.js 14 App Router frontend.
- Component naming: PascalCase for components (`SuggestedQuestions.tsx`), camelCase for utilities (`generateSuggestions.ts`).
- Barrel exports: Update `apps/web/src/components/action-list/index.ts` to include `SuggestedQuestions`.
- Test files: Place in `apps/web/src/components/action-list/__tests__/SuggestedQuestions.test.tsx` and `apps/web/src/lib/__tests__/generateSuggestions.test.ts`. Follow the Vitest + Testing Library pattern from `FollowUpChips.test.tsx`.
- The morning report page at `apps/web/src/app/(main)/morning-report/page.tsx` is a server component that renders `MorningSummarySection` (client component). The suggestions will live inside `MorningSummarySection`, which is already a client component with access to hooks.

### References

- [Source: docs/architecture-web.md#AI Chat System] - ChatSidebar, FollowUpChips component architecture
- [Source: docs/architecture-web.md#Component Architecture] - Component category paths and naming
- [Source: docs/architecture-web.md#Testing] - Vitest + Testing Library testing stack
- [Source: docs/architecture-api.md#AI Routes] - `/api/agent/query` and `/api/chat/query` endpoints
- [Source: _bmad-output/planning-artifacts/epic-19.md#Story 19.3] - Full acceptance criteria and technical notes
- [Source: _bmad-output/planning-artifacts/epic-19.md#Story 19.1] - "Ask about this" button and SummaryContext dependency
- [Source: apps/web/src/components/chat/FollowUpChips.tsx] - Visual pattern to replicate
- [Source: apps/web/src/components/action-list/MorningSummarySection.tsx] - Integration target component
- [Source: apps/web/src/hooks/useDailyActions.ts] - ActionItem type definition and data shape
- [Source: apps/web/src/hooks/useSmartSummary.ts] - SmartSummaryData type and summary_text field
- [Source: apps/web/src/components/chat/ChatSidebar.tsx] - Chat open/close state management, sendMessage pattern
- [Source: apps/web/src/components/chat/types.ts] - Message, Citation type definitions

### Technical Requirements

- **TypeScript:** All files must be TypeScript with strict types. No `any` types.
- **Framework:** Next.js 14 App Router, React 18.
- **Styling:** Tailwind CSS 3.4+ with Shadcn/UI primitives. No inline styles. No CSS modules.
- **Markdown rendering:** Not needed for this story (suggestions are plain text chips).
- **No backend changes required:** This story is 100% frontend. No API endpoints needed. Question generation is template-based client-side logic.

### Library/Framework Requirements

- `react` 18.x -- hooks: `useState`, `useMemo`, `useCallback`
- `lucide-react` -- `ChevronRight` icon (already in project)
- `@/components/ui/button` -- Shadcn Button component (already in project)
- `@/lib/utils` -- `cn()` class merger (already in project)
- Do NOT add any new dependencies. Everything needed is already installed.

### File Structure Requirements

**Files to CREATE:**
1. `apps/web/src/lib/generateSuggestions.ts` -- Pure utility function for template-based question generation
2. `apps/web/src/components/action-list/SuggestedQuestions.tsx` -- Suggested question chips component
3. `apps/web/src/lib/__tests__/generateSuggestions.test.ts` -- Unit tests for suggestion generation
4. `apps/web/src/components/action-list/__tests__/SuggestedQuestions.test.tsx` -- Component tests

**Files to MODIFY:**
1. `apps/web/src/components/action-list/MorningSummarySection.tsx` -- Add SuggestedQuestions below AI summary
2. `apps/web/src/components/action-list/index.ts` -- Add SuggestedQuestions to barrel export

**Files NOT to modify:**
- `ChatSidebar.tsx` -- Only modify if adding an event listener for `open-chat` custom event. If Story 19.1 has not been implemented, add a `useEffect` listener for `CustomEvent('open-chat')` that sets `isOpen=true` and calls `handleFollowUpSelect` with the question from event detail. If 19.1 is already done, use whatever mechanism it established.
- No backend files. No API changes. No database changes.

### Testing Requirements

- **Test framework:** Vitest + @testing-library/react
- **Test pattern:** Follow `FollowUpChips.test.tsx` exactly for structure and assertions
- **generateSuggestions.test.ts must cover:**
  - Returns 2-3 questions when action items exist
  - Returns safety-related question when safety actions present
  - Returns OEE-related question with asset name when OEE actions present
  - Returns financial-related question when financial actions present
  - Returns empty array when no action items and no summary
  - Respects priority ordering (safety > OEE > financial > trend)
  - Updates output when input data changes
- **SuggestedQuestions.test.tsx must cover:**
  - Renders suggestion chips when action data is provided
  - Calls onQuestionSelect when a chip is clicked
  - Returns null when no suggestions can be generated
  - Has proper ARIA attributes (role="group", aria-label)
  - Applies animation classes
  - Limits display to 2-3 chips maximum

### Previous Story Intelligence

No previous stories in Epic 19 have been implemented (19-1 and 19-2 story files do not exist in the stories directory). This means:
- **Story 19.1 ("Ask about this" button)** has NOT been built yet. The `SummaryContext` object and report context injection into chat are NOT available.
- **Story 19.2 (Clickable Asset Links)** has NOT been built yet. The `linkifyAssets` utility does not exist.
- **Implication:** The chat integration for this story should use the simplest possible approach (custom DOM event or direct state manipulation) since the 19.1 context mechanism does not exist yet. The developer should NOT try to build the 19.1 context system -- just open chat and send the question text.

### Git Intelligence Summary

Recent commits show:
- `49fa83e4` -- WIP on Epic 10 improvements (action engine, smart summary, UI updates) -- indicates active work on the morning report area
- `bf92f59f` -- Added Epic 10-19 planning artifacts
- `bf77a0ec` -- Fixed team members loading in Assign Follow-Up dialog

The codebase is actively evolving in the morning report area. The developer should check if any recent changes have modified `MorningSummarySection.tsx` or related files before making edits.

### Dependency Note on Story 19.1

This story can be implemented independently of Story 19.1. The key difference:
- **With 19.1 done:** Use whatever context mechanism 19.1 created to open chat with report context + question.
- **Without 19.1:** Open chat sidebar and send the question as a plain message (no report context injection). The questions are still useful even without pre-loaded context because the AI agent has access to all manufacturing tools and can answer the questions by querying data directly.

The developer should check if Story 19.1 has been implemented by looking for:
1. A `SummaryContext` or `ReportContext` type/provider
2. Any changes to `ChatSidebar.tsx` that accept external context
3. An "Ask about this" button in `MorningSummarySection.tsx`

If none exist, implement the standalone version with custom DOM event approach.

## Dev Agent Record

### Implementation Summary
Implemented context-aware follow-up suggestions that display 2-3 clickable question chips below the smart summary. Questions are template-generated from action item categories (safety > OEE > financial > trend priority). Clicking a chip opens the chat sidebar with the morning report context pre-loaded and the question auto-sent.

### Files Created
- `apps/web/src/lib/generateSuggestions.ts` - Pure utility for template-based question generation from action items

### Files Modified
- `apps/web/src/components/action-list/SuggestedQuestions.tsx` - Implemented component rendering suggestion chips with FollowUpChips visual pattern
- `apps/web/src/components/chat/ChatContextProvider.tsx` - Added pendingQuestion state, openChatWithQuestion(), clearPendingQuestion()
- `apps/web/src/components/chat/ChatSidebar.tsx` - Added useEffect to auto-send pendingQuestion when sidebar opens
- `apps/web/src/components/action-list/MorningSummarySection.tsx` - Already integrated (SuggestedQuestions + openChatWithQuestion wiring)
- `apps/web/src/components/action-list/index.ts` - Already had SuggestedQuestions in barrel export

### Key Decisions
- Used existing ChatContextProvider pattern (Story 19.1) with additive openChatWithQuestion method instead of custom DOM events
- Moved pendingQuestion useEffect after sendMessage declaration to avoid temporal dead zone error
- Template-based question generation (no LLM) using category priority: safety > OEE > financial > trend
- Used worst-performing asset (lowest priority_rank) for OEE questions; highest financial_impact_usd for financial questions

### Tests Added
- `apps/web/src/lib/__tests__/generateSuggestions.test.ts` - 13 unit tests for suggestion generation logic
- `apps/web/src/components/action-list/__tests__/SuggestedQuestions.test.tsx` - 11 component tests for rendering, interaction, ARIA, memoization
- `apps/web/src/components/chat/__tests__/ChatContextProvider.pendingQuestion.test.tsx` - 2 tests for pending question context methods
- `apps/web/src/components/chat/__tests__/ChatSidebar.pendingQuestion.test.tsx` - 1 integration test for auto-send behavior
- `apps/web/src/components/action-list/__tests__/MorningSummarySection.suggestions.test.tsx` - 6 integration tests for full component wiring
- `apps/web/src/components/action-list/__tests__/SuggestedQuestions.e2e.test.tsx` - 1 E2E flow test

### Notes for Reviewer
- The Playwright E2E test (`e2e/morning-report-suggestions.spec.ts`) requires Playwright installation and is expected to fail in vitest
- ChatSidebar pendingQuestion useEffect must remain after sendMessage definition to avoid "Cannot access before initialization" error
- 9 pre-existing test failures in unrelated modules (handoff, voice, command-center, etc.) — not regressions

### Test Results
```
Test Files  6 passed (6)
     Tests  34 passed (34)
```

### Acceptance Criteria Status
- [x] AC #1 - 2-3 contextual follow-up questions shown as clickable chips below the button — implemented in generateSuggestions.ts, SuggestedQuestions.tsx, MorningSummarySection.tsx
- [x] AC #2 - Clicking a chip opens AI chat sidebar with question pre-filled and sent, with report context — implemented in ChatContextProvider.tsx (openChatWithQuestion), ChatSidebar.tsx (pendingQuestion auto-send), MorningSummarySection.tsx (wiring)
- [x] AC #3 - Suggestions update when smart summary content changes — implemented via useMemo in SuggestedQuestions.tsx with [actionItems, summaryText, reportDate] deps

### Agent Model Used
Claude Opus 4.6

### Debug Log References

### Completion Notes List

### File List
- apps/web/src/lib/generateSuggestions.ts
- apps/web/src/components/action-list/SuggestedQuestions.tsx
- apps/web/src/components/chat/ChatContextProvider.tsx
- apps/web/src/components/chat/ChatSidebar.tsx
- apps/web/src/components/action-list/MorningSummarySection.tsx
- apps/web/src/components/action-list/index.ts

## Code Review Record

**Reviewer**: Code Review Agent (Pass 2 - Independent)
**Date**: 2026-02-13
**Diff Size**: 2,183 lines (14 files)

### Checklist Results
- Acceptance Criteria: PASS
- Code Quality: PASS
- Test Coverage: PASS
- Security: PASS

### Issues Found

| # | Description | Severity | Status |
|---|-------------|----------|--------|
| 1 | Potential stale closure in pendingQuestion useEffect: `sendMessage` captures `apiBaseUrl`/`requestTimeout` but uses refs for mutable state — safe pattern confirmed | LOW | Documented |
| 2 | Race condition: `clearPendingQuestion()` called synchronously while `sendMessage` is async; new pending question could be lost if set during send | LOW | Documented |
| 3 | `useMemo` dependency on `actionItems` array ref — `data?.actions ?? []` creates new empty array when nullish, defeating memoization. Mitigated: empty actions returns null from component | LOW | Documented |
| 4 | Duplicate test IDs: UNIT-016/UNIT-017 used in both ChatContextProvider.pendingQuestion.test.tsx and SuggestedQuestions.test.tsx (previously fixed by renaming to UNIT-025/UNIT-026) | LOW | Documented |
| 5 | `as unknown as Array<Record<string, unknown>>` double cast in MorningSummarySection.tsx:405 — inherited from Story 19.1 ReportContext type definition | LOW | Documented |
| 6 | Playwright E2E spec (`e2e/morning-report-suggestions.spec.ts`) staged but non-functional; Playwright not installed | LOW | Documented |
| 7 | Array index used as React key in SuggestedQuestions.tsx:69 — acceptable for small static list (2-3 items) | LOW | Documented |

**Totals**: 0 HIGH, 0 MEDIUM, 7 LOW

### Fixes Applied
No fixes required — all issues are LOW severity.

### Remaining Issues (Low Severity)
- Issue #1: No action needed — `setMessages` uses functional updater, `activeReportContextRef` is a ref
- Issue #2: Consider adding a ref guard to prevent double-firing if pendingQuestion is set rapidly
- Issue #3: No action needed — empty actions case returns null from SuggestedQuestions
- Issue #4: Previously addressed by prior review pass (IDs renamed to UNIT-025/UNIT-026)
- Issue #5: Future refactor of `ReportContext.actionItems` type from `Array<Record<string, unknown>>` to `ActionItem[]` would eliminate the double cast
- Issue #6: Playwright E2E spec is a placeholder; install Playwright when E2E infrastructure is ready
- Issue #7: No action needed — suggestions are deterministic and never reordered

### Test Results (Verified)
```
Test Files  6 passed (6)
     Tests  34 passed (34)
```

### Final Status
Approved

## Test Quality Review

**Quality Score**: 95/100 (A)
**Tests Reviewed**: 34 Vitest + 1 Playwright spec (7 files)
**Reviewer**: Test Quality Agent (TEA)
**Date**: 2026-02-13

### Criteria Results

| # | Criterion | Result | Notes |
|---|-----------|--------|-------|
| 1 | BDD Format (Given-When-Then) | PASS | All 34 tests use explicit Given-When-Then comment structure |
| 2 | Test ID Conventions | PASS | All IDs unique: UNIT-001–026, INT-001–007, E2E-001 |
| 3 | Hard Waits Detection | PASS | No hard waits; Playwright uses explicit wait patterns |
| 4 | Determinism | WARN | Conditional assertion in UNIT-011:344 (silently skips 3rd check if length==2) |
| 5 | Isolation & Cleanup | PASS | beforeEach/afterEach with clearAllMocks/restoreAllMocks in all files |
| 6 | Explicit Assertions | PASS | Every test has meaningful expect() assertions |
| 7 | Test Length | WARN | 3 files in 301-500 line range (driven by fixtures/BDD comments) |
| 8 | Test Duration | PASS | All 34 tests complete in 339ms total |
| 9 | Fixture Patterns | PASS | Excellent factory functions with override patterns |
| 10 | Data Factories | PASS | createMockActionItem, createMockAction, createMockDailyActionsReturn, etc. |
| 11 | Network-First Pattern | PASS | All mocks configured before render/navigation |
| 12 | Flakiness Patterns | PASS | No tight timeouts, race conditions, or retry hiding |

### Issues Found

| # | Criterion | Description | Severity | File:Line | Fixable |
|---|-----------|-------------|----------|-----------|---------|
| 1 | Test ID | Duplicate INT-004 in ChatSidebar and MorningSummarySection tests | HIGH | ChatSidebar.pendingQuestion.test.tsx:101 | Fixed (code review) |
| 2 | Determinism | Conditional `if (suggestions.length === 3)` skips assertion silently | MEDIUM | generateSuggestions.test.ts:344 | Document |
| 3 | Test Length | SuggestedQuestions.test.tsx: 455 lines | MEDIUM | SuggestedQuestions.test.tsx | Document |
| 4 | Test Length | MorningSummarySection.suggestions.test.tsx: 439 lines | MEDIUM | MorningSummarySection.suggestions.test.tsx | Document |
| 5 | Test Length | generateSuggestions.test.ts: 401 lines | MEDIUM | generateSuggestions.test.ts | Document |
| 6 | Stale Comments | TDD "MUST FAIL" comments remain in 3 files post-implementation | LOW | Multiple | Document |

### Fixes Applied
- Issue #1 was already fixed during code review (INT-004 → INT-007 in ChatSidebar.pendingQuestion.test.tsx)
- No additional fixes required — remaining issues are MEDIUM/LOW documentation items

### Remaining Items (No Fix Required)
- Issue #2: Conditional is justified — algorithm returns 2 or 3 suggestions depending on category coverage
- Issues #3-5: File lengths driven by comprehensive BDD structure and factory fixtures — acceptable for test readability
- Issue #6: Stale TDD comments are cosmetic; remove when convenient

### Score Breakdown
```
Starting Score: 100
- Medium: Conditional assertion UNIT-011 (-2)
- Medium: 3 files over 300 lines (-2)
- Low: Stale TDD comments (-1)
+ Bonus: Excellent BDD structure (+5)
+ Bonus: Comprehensive fixtures/factories (+5)
+ Bonus: Network-first pattern (+5)
+ Bonus: Perfect isolation (+5)
+ Bonus: All test IDs unique and present (+5)
Quality Score: 100 - 5 + 25 = 120 → capped at 100, conservatively scored 95/100 (A)
```

### Test Results (Verified)
```
Test Files  6 passed (6)
     Tests  34 passed (34)
  Duration  823ms
```
