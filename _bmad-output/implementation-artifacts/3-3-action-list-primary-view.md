# Story 3.3: Action List Primary View

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Plant Manager**,
I want the **Morning Report UI to display the Daily Action List as the primary landing page view on login**,
so that I can **immediately see prioritized, actionable recommendations when I start my day and direct my morning meetings effectively**.

## Acceptance Criteria

1. **Action List as Primary Landing View**
   - Morning Report / Action List page is the default landing view after successful authentication
   - Page loads within 2 seconds of login completion
   - Clear page header indicating "Morning Report" or "Daily Action List"
   - Date context prominently displayed (showing which day's data is being analyzed)

2. **Action First Layout Structure**
   - Action List section takes visual priority (top/center of viewport)
   - Supporting data (charts, metrics) appears as secondary context below or to the side
   - Layout follows UX principle: "Action First, Data Second"
   - Responsive design works on tablets (primary device) and desktop

3. **Action Item Card Display**
   - Each action item displayed as a distinct card component
   - Cards show the action recommendation prominently
   - Visual priority indicators (Safety = red flag, High $ = warning icon, Performance = info icon)
   - Cards are visually distinguishable from each other with clear boundaries

4. **Action Priority Ordering**
   - Action items sorted by priority: Safety first, then Financial Impact ($) descending
   - Priority order matches Action Engine logic from Story 3.1
   - Visual numbering or ranking indicator on each card (e.g., "#1", "#2")
   - Clear visual separation between safety-critical and non-safety items

5. **Data Integration with Action Engine API**
   - Consumes data from Daily Action List API endpoint (Story 3.2)
   - Displays loading skeleton while fetching action items
   - Shows empty state messaging when no action items exist ("All systems performing within targets")
   - Graceful error handling with retry option if API fails

6. **Morning Summary Section**
   - Brief textual summary of yesterday's performance (T-1 data)
   - Key metrics at a glance: Plant OEE, Total Financial Impact, Safety Events count
   - Prepared for Smart Summary integration (Story 3.5) - placeholder/slot for AI-generated text

7. **Navigation and Quick Actions**
   - Each action card is clickable/tappable for drill-down (links to Insight + Evidence Cards - Story 3.4)
   - Quick navigation to switch between "Morning Report" (T-1) and "Live Pulse" (T-15m) views
   - Breadcrumb or clear indication of current view mode

8. **Industrial Clarity Visual Compliance**
   - High-contrast colors readable from 3 feet on tablet (factory floor conditions)
   - Uses "Retrospective" mode styling (cool colors) per UX design - distinct from Live Pulse
   - Large typography for action text (minimum 18px body, 24px+ for key values)
   - "Safety Red" (#DC2626) ONLY used for actual safety-related action items
   - Clear visual hierarchy between action title, supporting details, and metadata

9. **Authentication Flow Integration**
   - Authenticated users redirect to Action List page immediately after login
   - Unauthenticated access redirects to login page
   - Uses Supabase Auth session management (established in Story 1.2)

10. **Performance Requirements**
    - Initial page render (with loading state) within 500ms
    - Full data load and display within 2 seconds
    - Tablet-optimized rendering (768px - 1024px viewport)

## Tasks / Subtasks

- [ ] Task 1: Create MorningReportPage route and layout (AC: #1, #9)
  - [ ] 1.1 Create `apps/web/src/app/morning-report/page.tsx` as App Router page
  - [ ] 1.2 Set up route as default authenticated landing page
  - [ ] 1.3 Add authentication check - redirect unauthenticated to login
  - [ ] 1.4 Configure page metadata (title: "Morning Report - Manufacturing Assistant")
  - [ ] 1.5 Update auth callback to redirect to `/morning-report` after login

- [ ] Task 2: Create ActionListContainer component (AC: #2, #5)
  - [ ] 2.1 Create `apps/web/src/components/action-list/ActionListContainer.tsx`
  - [ ] 2.2 Implement data fetching from Action List API (Story 3.2 endpoint)
  - [ ] 2.3 Add loading skeleton state while fetching
  - [ ] 2.4 Add empty state component ("All systems performing within targets")
  - [ ] 2.5 Add error state with retry button
  - [ ] 2.6 Use SWR or React Query for data fetching with caching

- [ ] Task 3: Create ActionItemCard component (AC: #3, #4, #8)
  - [ ] 3.1 Create `apps/web/src/components/action-list/ActionItemCard.tsx`
  - [ ] 3.2 Design card layout with recommendation text prominently displayed
  - [ ] 3.3 Add priority indicator icons (Safety = AlertTriangle red, Financial = DollarSign amber, Performance = Info blue)
  - [ ] 3.4 Add ranking number display (#1, #2, etc.)
  - [ ] 3.5 Apply "Retrospective" mode styling (cool colors from Industrial Clarity)
  - [ ] 3.6 Make card clickable for drill-down navigation
  - [ ] 3.7 Ensure minimum 18px body text, 24px+ for key values

- [ ] Task 4: Create MorningSummarySection component (AC: #6)
  - [ ] 4.1 Create `apps/web/src/components/action-list/MorningSummarySection.tsx`
  - [ ] 4.2 Display key metrics: Plant OEE, Total Financial Impact, Safety Events count
  - [ ] 4.3 Add date context (showing "Yesterday's Performance - [Date]")
  - [ ] 4.4 Create placeholder slot for AI-generated Smart Summary (Story 3.5)
  - [ ] 4.5 Style with Industrial Clarity Retrospective mode colors

- [ ] Task 5: Implement page layout and responsive design (AC: #2, #8, #10)
  - [ ] 5.1 Create ActionListLayout with Action First hierarchy
  - [ ] 5.2 Position MorningSummarySection as header context
  - [ ] 5.3 Position ActionListContainer as primary content area
  - [ ] 5.4 Implement responsive layout for tablet (768px-1024px) and desktop
  - [ ] 5.5 Test glanceability at 3-foot viewing distance simulation

- [ ] Task 6: Implement view mode navigation (AC: #7)
  - [ ] 6.1 Create ViewModeToggle component (Morning Report vs Live Pulse)
  - [ ] 6.2 Add navigation to switch between /morning-report and /live-pulse routes
  - [ ] 6.3 Highlight current active view mode
  - [ ] 6.4 Add breadcrumb component showing current location

- [ ] Task 7: Integration testing (AC: #5, #9, #10)
  - [ ] 7.1 Test authenticated user flow lands on Action List page
  - [ ] 7.2 Test unauthenticated redirect to login
  - [ ] 7.3 Test action items render from API mock data
  - [ ] 7.4 Test priority ordering (safety first, then $ impact)
  - [ ] 7.5 Test empty state when no action items
  - [ ] 7.6 Test loading and error states
  - [ ] 7.7 Performance test: page load under 2 seconds

## Dev Notes

### Architecture Patterns

- **Frontend Framework:** Next.js 14+ with App Router
- **Backend Framework:** Python FastAPI (apps/api) - consumed via REST API
- **Styling:** Tailwind CSS + Shadcn/UI with Industrial Clarity theme (Story 1.6)
- **Data Source:** Action Engine API endpoint (Story 3.2)
- **Authentication:** Supabase Auth with JWT (Story 1.2)

### Technical Requirements

**Frontend (apps/web):**
- Use App Router file-based routing (`app/morning-report/page.tsx`)
- Implement with React Server Components where possible
- Use Client Components for interactive elements (cards, navigation)
- Leverage SWR or React Query for API data fetching with automatic revalidation
- Apply "Retrospective" mode color variants from Industrial Clarity palette:
  - `retro-bg: #1E293B` (slate-800 - cool dark background)
  - `retro-card: #334155` (slate-700 - card surface)
  - `retro-text: #F1F5F9` (slate-100 - primary text)
  - `retro-accent: #60A5FA` (blue-400 - accent color)
  - `safety-red: #DC2626` (ONLY for safety-related items)

**API Integration:**
```typescript
// Expected API endpoint from Story 3.2
GET /api/daily-actions

// Response type
interface DailyActionsResponse {
  date: string;                    // ISO date for T-1 data
  summary: {
    plantOee: number;              // Percentage
    totalFinancialImpact: number;  // Dollars
    safetyEventCount: number;
    totalActionItems: number;
  };
  actions: ActionItem[];
}

interface ActionItem {
  id: string;
  rank: number;                    // Priority ranking (1 = highest)
  type: 'safety' | 'financial' | 'performance';
  title: string;                   // Brief action recommendation
  description: string;             // Supporting detail
  priority: 'critical' | 'high' | 'medium';
  financialImpact?: number;        // Dollars (for financial type)
  assetName?: string;              // Related asset
  metric?: {                       // Supporting metric for evidence
    name: string;
    value: number;
    unit: string;
    target?: number;
  };
  createdAt: string;
}
```

### UX Design Compliance

| Principle | Implementation |
|-----------|----------------|
| Action First, Data Second | Action List is primary view; summary metrics are secondary header |
| Insight + Evidence | Cards show recommendation + supporting metric; click for full evidence |
| Glanceability | Large text (24px+), high contrast, readable from 3 feet |
| Industrial Clarity | Retrospective mode colors (cool/blue tones) for T-1 data |
| Trust & Transparency | Every action item links to supporting evidence (Story 3.4) |
| Safety Red Reserved | #DC2626 ONLY for safety action items |

### Project Structure Notes

```
apps/web/src/
  app/
    morning-report/
      page.tsx                     # Morning Report landing page (NEW)
      loading.tsx                  # Loading skeleton (NEW)
    (auth)/
      callback/route.ts            # UPDATE: redirect to /morning-report
  components/
    action-list/
      ActionListContainer.tsx      # Container with data fetching (NEW)
      ActionItemCard.tsx           # Individual action card (NEW)
      MorningSummarySection.tsx    # Summary header (NEW)
      EmptyActionState.tsx         # Empty state component (NEW)
      ActionListSkeleton.tsx       # Loading skeleton (NEW)
    navigation/
      ViewModeToggle.tsx           # Morning Report / Live Pulse toggle (NEW)
      Breadcrumb.tsx               # Breadcrumb navigation (NEW)
```

### Dependencies

**Requires (must be completed):**
- Story 1.2: Supabase Auth Integration (authentication flow)
- Story 1.6: Industrial Clarity Design System (styling components)
- Story 1.7: Command Center UI Shell (navigation context)
- Story 3.1: Action Engine Logic (prioritization algorithm - consumed via API)
- Story 3.2: Daily Action List API (backend endpoint providing action items)

**Enables:**
- Story 3.4: Insight + Evidence Cards (action card click-through)
- Story 3.5: Smart Summary Generator (AI summary slot in MorningSummarySection)

### Previous Epic Context (Epic 2)

From the completed Epic 2 stories:
- Live Pulse Ticker (Story 2.9) established patterns for real-time data display
- Financial Impact Calculator (Story 2.7) provides financial calculation patterns
- Safety Alert System (Story 2.6) established safety-red usage patterns
- Industrial Clarity design system (Story 1.6) provides all UI styling patterns

**Key patterns to follow from Story 2.9:**
- Use same responsive layout approach (tablet-first)
- Follow same Tailwind class patterns for high-contrast text
- Reuse loading skeleton patterns
- Consistent API response handling with SWR/React Query

### NFR Compliance

- **NFR1 (Accuracy):** Each action item cites specific data - linked to evidence via Story 3.4
- **NFR2 (Latency):** Page loads within 2 seconds, action items from cached daily_summaries

### Testing Guidance

**Unit Tests:**
- Test ActionItemCard renders all priority types correctly
- Test priority ordering logic (safety > financial > performance)
- Test empty state renders when actions array is empty
- Test loading state renders skeleton correctly

**Integration Tests:**
- Test full page renders with mocked API response
- Test authentication redirect flow
- Test action card click navigates to evidence view
- Test view mode toggle switches correctly

**Visual Tests:**
- Verify tablet viewport rendering (768px, 1024px breakpoints)
- Verify safety-red only appears on safety action items
- Verify text size meets glanceability requirements (24px+ primary)
- Verify Retrospective mode color palette is applied

### API Error Handling

```typescript
// Error states to handle
const ErrorStates = {
  NETWORK_ERROR: "Unable to connect to server. Check your connection and try again.",
  AUTH_ERROR: "Your session has expired. Please log in again.",
  SERVER_ERROR: "Something went wrong on our end. We're working on it.",
  NO_DATA: "No data available for yesterday. This may happen on Mondays after plant shutdown."
};
```

### References

- [Source: _bmad/bmm/data/prd.md#3. User Interface Design Goals] - "Action-First" primary view requirement
- [Source: _bmad/bmm/data/prd.md#2. Requirements] - FR3 Action Engine, NFR1 Accuracy
- [Source: _bmad/bmm/data/architecture.md#7. AI & Memory Architecture] - Action Engine Logic definition
- [Source: _bmad/bmm/data/ux-design.md#2. Overall UX Goals] - Glanceability, Trust & Transparency, Industrial Clarity
- [Source: _bmad/bmm/data/ux-design.md#2. Design Principles] - Action First Data Second, Insight + Evidence
- [Source: _bmad/bmm/data/ux-design.md#3. Information Architecture] - Action List & Morning Summary in Command Center
- [Source: _bmad-output/planning-artifacts/epic-3.md] - Epic 3 scope: Story 3.3 "Morning Report UI with Action List as landing page"
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 3] - FR3 coverage, scope definition
- [Source: _bmad-output/implementation-artifacts/1-6-industrial-clarity-design-system.md] - Retrospective mode colors, typography
- [Source: _bmad-output/implementation-artifacts/1-7-command-center-ui-shell.md] - UI shell structure to integrate with
- [Source: _bmad-output/implementation-artifacts/2-9-live-pulse-ticker.md] - Patterns for real-time display, financial context, safety alerts

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
