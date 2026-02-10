# Story 18.1: Meeting Mode Toggle & Talking Points View

Status: ready-for-dev

## Story

As a Plant Manager running a morning standup,
I want a condensed "meeting mode" that shows only the top 3-5 items as large, scannable talking points,
So that I can run a 15-minute meeting without getting lost in report details.

## Acceptance Criteria

1. **Given** the morning report page is in normal mode, **When** the user clicks a "Meeting Mode" toggle button in the report header, **Then** the view switches to a condensed layout showing:
   - Top 3-5 action items displayed as large cards with only: headline, asset, priority, and who's assigned
   - Evidence detail is hidden (collapsed/removed)
   - Clear section headers: "Safety" / "Yesterday's Performance" / "Today's Priorities"
   - The URL updates to include `?mode=meeting`

2. **Given** the meeting mode view is active, **When** the user views an action item, **Then** the "Assign Follow-Up" button is prominently visible (not discovered in a menu) **And** assignment badges are visible by default showing who's already assigned.

3. **Given** the user clicks the toggle again, **When** switching back to normal mode, **Then** the full report view is restored with all evidence and detail sections.

4. **Given** the URL includes `?mode=meeting`, **When** the page loads, **Then** meeting mode is activated automatically.

## Tasks / Subtasks

- [ ] Task 1: Add Shadcn/UI Toggle component to the project (AC: #1)
  - [ ] 1.1: Run `npx shadcn-ui@latest add toggle` in `apps/web` to install the Toggle primitive
  - [ ] 1.2: Verify `components/ui/toggle.tsx` is created and exports correctly

- [ ] Task 2: Create `MeetingModeToggle` component (AC: #1, #3)
  - [ ] 2.1: Create `apps/web/src/components/report/MeetingModeToggle.tsx`
  - [ ] 2.2: Implement toggle button using Shadcn/UI `Toggle` (pressed/unpressed states)
  - [ ] 2.3: Use `Presentation` (lucide-react) icon with label "Meeting Mode"
  - [ ] 2.4: Apply Industrial Clarity styling: high-contrast, minimum 18px text, visible at 3ft
  - [ ] 2.5: Emit `onToggle(isMeeting: boolean)` callback to parent

- [ ] Task 3: Add URL state management for `mode` parameter (AC: #1, #4)
  - [ ] 3.1: In `morning-report/page.tsx`, read `searchParams.mode` from the page props (Next.js App Router server component pattern)
  - [ ] 3.2: Create a client wrapper component `MorningReportClient.tsx` that manages `mode` state via `useSearchParams()` and `useRouter()`
  - [ ] 3.3: On toggle, update URL: `router.push(mode === 'meeting' ? '?mode=meeting' : pathname)` while preserving existing `date` param
  - [ ] 3.4: Initialize meeting mode from URL on page load (`searchParams.get('mode') === 'meeting'`)

- [ ] Task 4: Create `MeetingTalkingPoint` card component (AC: #1, #2)
  - [ ] 4.1: Create `apps/web/src/components/action-list/MeetingTalkingPoint.tsx`
  - [ ] 4.2: Render large card with: priority badge, headline text (24px+), asset name, assigned-to badge
  - [ ] 4.3: Hide all evidence/detail sections (no EvidenceSection, no metrics row, no drill-down chevron)
  - [ ] 4.4: Make "Assign Follow-Up" button prominent and always visible (not in menu) - use `Button` component with `UserPlus` icon
  - [ ] 4.5: Show existing assignment badges using data from `action_followups` table (query via API or Supabase)
  - [ ] 4.6: Apply 4px left border with priority color (reuse `getPriorityBorderColor` from PriorityBadge)
  - [ ] 4.7: Use `role="article"` and proper ARIA labels for accessibility

- [ ] Task 5: Create meeting mode section layout with grouped headers (AC: #1)
  - [ ] 5.1: Create `apps/web/src/components/report/MeetingModeView.tsx`
  - [ ] 5.2: Group action items by category: "Safety" / "Yesterday's Performance" (OEE) / "Today's Priorities" (financial)
  - [ ] 5.3: Render section headers with large, high-contrast text (section-header class)
  - [ ] 5.4: Limit to top 3-5 items total (configurable, slice sorted actions array)
  - [ ] 5.5: If no items in a section, show "No items" inline text (do not hide the section header)

- [ ] Task 6: Integrate meeting mode into morning report page (AC: #1, #3, #4)
  - [ ] 6.1: Convert `morning-report/page.tsx` to use the new client wrapper
  - [ ] 6.2: Add `MeetingModeToggle` to the page header area (between title and date badge)
  - [ ] 6.3: Conditionally render: if meeting mode, show `MeetingModeView`; if normal, show existing `MorningSummarySection` + `InsightEvidenceCardList`
  - [ ] 6.4: Pass action data from `useDailyActions` to both views (do not duplicate fetch calls)

- [ ] Task 7: Fetch and display assignment badges (AC: #2)
  - [ ] 7.1: Create a hook or utility to fetch followup assignments for displayed action items (query `action_followups` by `action_item_id`)
  - [ ] 7.2: Render assignment badge on `MeetingTalkingPoint` showing assignee email/name
  - [ ] 7.3: Use existing `Badge` component with "info" variant for assignment display

- [ ] Task 8: Testing and accessibility (AC: #1-4)
  - [ ] 8.1: Add Vitest tests for `MeetingModeToggle` (toggle state, callback)
  - [ ] 8.2: Add Vitest tests for `MeetingTalkingPoint` (rendering, assignment badge, ARIA labels)
  - [ ] 8.3: Add Vitest test for URL state sync (meeting mode from URL, URL update on toggle)
  - [ ] 8.4: Verify keyboard navigation: toggle is focusable and activates with Enter/Space
  - [ ] 8.5: Verify dark mode support for all new components

## Dev Notes

### Architecture Patterns

- **Component Organization:** New components follow the domain-based structure. Meeting mode components go in `components/report/` (new directory) for page-level components and `components/action-list/` for card variants.
- **Page Pattern:** The morning report page (`apps/web/src/app/(main)/morning-report/page.tsx`) is currently a **server component** that imports client components. To add URL state management with `useSearchParams()`, you need a client wrapper component. Keep the server component minimal (metadata + layout) and delegate interactive logic to the client wrapper.
- **Data Flow:** `useDailyActions()` hook is the single data source. Both normal and meeting mode views consume the same data -- meeting mode is a view filter, not a separate data fetch.
- **URL State:** The project already uses URL search params (e.g., date param for report history in Epic 17). Follow the same pattern: `useSearchParams()` + `useRouter().push()`.

### Existing Components to Reuse

| Component | Location | Reuse |
|-----------|----------|-------|
| `useDailyActions` hook | `src/hooks/useDailyActions.ts` | Data source for action items |
| `PriorityBadge` | `src/components/action-engine/PriorityBadge.tsx` | Priority styling, border colors |
| `Badge` | `src/components/ui/badge.tsx` | Assignment badges |
| `Button` | `src/components/ui/button.tsx` | Assign Follow-Up button |
| `Card` / `CardContent` | `src/components/ui/card.tsx` | Card containers |
| `AssignFollowUpDialog` | `src/components/action-engine/AssignFollowUpDialog.tsx` | Follow-up assignment dialog |
| `InsightEvidenceCardList` | `src/components/action-engine/InsightEvidenceCardList.tsx` | Normal mode rendering (unchanged) |
| `MorningSummarySection` | `src/components/action-list/MorningSummarySection.tsx` | Normal mode summary (unchanged) |
| `SafetyAlertsSection` | `src/components/dashboard/` | Safety banner (shown in both modes) |

### Critical Implementation Details

1. **No Toggle/Switch in UI library yet:** The project does NOT currently have a `toggle.tsx` or `switch.tsx` in `components/ui/`. You MUST install it via `npx shadcn-ui@latest add toggle` before using it. Do NOT create a custom toggle from scratch.

2. **Server Component Boundary:** `page.tsx` currently exports `metadata` (server-only). When converting to support client interactivity, extract interactive parts to a `'use client'` wrapper component. The page can remain a server component that renders the client wrapper.

3. **Action Item Types:** The meeting mode card needs data from two type systems:
   - `ActionItem` from `src/hooks/useDailyActions.ts` (API response format with `asset_name`, `recommendation_text`, `priority_level`, `category`)
   - `ActionItem` from `src/components/action-engine/types.ts` (transformed format with `recommendation.text`, `asset.name`, `priority`)
   - Use the `transformAPIActionItems()` function from `action-engine/transformers.ts` to convert between them, OR work directly with the hook's raw data format.

4. **Assignment Badge Data:** To show "who's assigned" on meeting mode cards, query the `action_followups` Supabase table filtered by `action_item_id`. Use the existing Supabase client pattern from `AssignFollowUpDialog.tsx` as reference for auth headers and client creation.

5. **Priority Category Mapping for Section Headers:**
   - "Safety" section: `category === 'safety'`
   - "Yesterday's Performance" section: `category === 'oee'`
   - "Today's Priorities" section: `category === 'financial'`

6. **Industrial Clarity Compliance:**
   - Key values (headlines, asset names) must be 24px+ (`text-xl md:text-2xl`)
   - Body text minimum 18px (`text-base` or `text-lg`)
   - Safety Red (`text-safety-red`, `bg-safety-red`) reserved exclusively for safety items
   - High contrast required for factory floor visibility (tablet at 3ft)

7. **URL Param Preservation:** When toggling meeting mode, preserve the existing `date` search param. Use `URLSearchParams` to merge both params. Example:
   ```typescript
   const params = new URLSearchParams(searchParams.toString())
   if (isMeeting) {
     params.set('mode', 'meeting')
   } else {
     params.delete('mode')
   }
   router.push(`${pathname}?${params.toString()}`)
   ```

### Project Structure Notes

- All new frontend files go under `apps/web/src/`
- New `components/report/` directory will be created for page-level meeting mode components
- Existing `components/action-list/` directory gets the `MeetingTalkingPoint.tsx` card component
- No backend changes required -- this is purely a frontend view layer feature
- No database migrations needed
- No new API endpoints needed

### Files to Create

| File | Purpose |
|------|---------|
| `apps/web/src/components/ui/toggle.tsx` | Shadcn/UI Toggle primitive (via CLI install) |
| `apps/web/src/components/report/MeetingModeToggle.tsx` | Toggle button component |
| `apps/web/src/components/report/MeetingModeView.tsx` | Grouped meeting layout with section headers |
| `apps/web/src/components/action-list/MeetingTalkingPoint.tsx` | Condensed action card for meeting mode |
| `apps/web/src/app/(main)/morning-report/MorningReportClient.tsx` | Client wrapper for URL state + mode toggle |

### Files to Modify

| File | Change |
|------|--------|
| `apps/web/src/app/(main)/morning-report/page.tsx` | Refactor to use client wrapper, pass searchParams |
| `apps/web/src/components/action-list/index.ts` | Export `MeetingTalkingPoint` |

### Dependencies (Epic 13)

- Epic 13 Story 13.4 (Assignment Badge on Action Cards) provides the assignment badge pattern. If that story is complete, reuse its badge component. If not yet implemented, implement a minimal version: query `action_followups` and show assignee email in a `Badge`.
- Epic 13 Story 13.5 (My Assignments Panel) establishes the follow-up query patterns. Reuse where possible.

### References

- [Source: _bmad-output/planning-artifacts/epic-18.md#Story 18.1]
- [Source: _bmad-output/planning-artifacts/epics-improvements.md#FR-I12]
- [Source: docs/architecture-web.md#Directory Structure]
- [Source: docs/architecture-web.md#State Management]
- [Source: apps/web/src/app/(main)/morning-report/page.tsx]
- [Source: apps/web/src/components/action-engine/InsightEvidenceCard.tsx]
- [Source: apps/web/src/components/action-engine/AssignFollowUpDialog.tsx]
- [Source: apps/web/src/hooks/useDailyActions.ts]
- [Source: apps/web/src/components/action-engine/types.ts]

## Dev Agent Record

### Agent Model Used

<!-- To be filled by dev agent -->

### Debug Log References

### Completion Notes List

### Change Log

| Change | Date | Reason |
|--------|------|--------|
| Story created | 2026-02-10 | Initial story creation from Epic 18 planning |

### File List
