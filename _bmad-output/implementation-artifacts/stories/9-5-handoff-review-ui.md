# Story 9.5: Handoff Review UI

Status: done

## Story

As an incoming Supervisor,
I want to review the handoff from the previous shift,
so that I understand what happened and what to watch.

## Acceptance Criteria

1. **AC1: Handoff Notification Banner**
   - Given an incoming Supervisor logs in
   - When a pending handoff exists for their assigned assets (FR25)
   - Then a notification/banner indicates "Handoff available from [Name]"
   - And they can click to view the full handoff

2. **AC2: Handoff Detail View**
   - Given the Supervisor opens a handoff
   - When viewing the handoff detail
   - Then they see:
     - Shift summary (auto-generated)
     - Voice notes (with play buttons)
     - Text notes
     - Timestamp and outgoing supervisor name
     - Acknowledgment button

3. **AC3: Voice Note Playback**
   - Given voice notes exist
   - When the Supervisor plays them
   - Then audio plays with transcript displayed below
   - And playback controls (play/pause, seek) are available

4. **AC4: Tablet-Optimized Layout**
   - Given the Supervisor views on a tablet
   - When the UI renders
   - Then layout is optimized for tablet viewing
   - And touch targets are appropriately sized (minimum 44x44px)

## Tasks / Subtasks

- [x] Task 1: Create handoff list page (AC: #1)
  - [x] 1.1: Create `apps/web/src/app/(main)/handoff/page.tsx`
  - [x] 1.2: Implement pending handoff query with asset overlap filter
  - [x] 1.3: Display notification banner for pending handoffs

- [x] Task 2: Create handoff list component (AC: #1)
  - [x] 2.1: Create `apps/web/src/components/handoff/HandoffList.tsx`
  - [x] 2.2: Fetch handoffs filtered by supervisor assignments
  - [x] 2.3: Display list with status indicators

- [x] Task 3: Create handoff card component (AC: #1, #2)
  - [x] 3.1: Create `apps/web/src/components/handoff/HandoffCard.tsx`
  - [x] 3.2: Display outgoing supervisor name, timestamp, summary preview
  - [x] 3.3: Show pending/acknowledged status badge
  - [x] 3.4: Link to detail page

- [x] Task 4: Create handoff detail page (AC: #2, #3, #4)
  - [x] 4.1: Create `apps/web/src/app/(main)/handoff/[id]/page.tsx`
  - [x] 4.2: Implement handoff data fetching with voice notes
  - [x] 4.3: Render HandoffViewer component

- [x] Task 5: Create handoff viewer component (AC: #2, #3, #4)
  - [x] 5.1: Create `apps/web/src/components/handoff/HandoffViewer.tsx`
  - [x] 5.2: Display shift summary section with citations
  - [x] 5.3: Display text notes section
  - [x] 5.4: Integrate voice note player
  - [x] 5.5: Add acknowledge button (placeholder for Story 9.7)
  - [x] 5.6: Implement tablet-first responsive layout

- [x] Task 6: Voice note player integration (AC: #3) - *Reused from Story 9.3*
  - [x] 6.1: VoiceNotePlayer.tsx already exists with AC#3 compliance
  - [x] 6.2: HTML5 audio element with custom controls (implemented in 9.3)
  - [x] 6.3: Transcript display below audio player (implemented in 9.3)
  - [x] 6.4: Play/pause, seek bar, duration display (implemented in 9.3)
  - [x] 6.5: Loading/error states (implemented in 9.3)

- [x] Task 7: Create API types and hooks (AC: #1, #2)
  - [x] 7.1: Create `apps/web/src/types/handoff.ts` with TypeScript interfaces
  - [x] 7.2: Create `apps/web/src/hooks/useHandoff.ts` for data fetching
  - [x] 7.3: Create `apps/web/src/hooks/useHandoffList.ts` for list queries

- [x] Task 8: Write component tests
  - [x] 8.1: Test HandoffList renders pending/completed sections
  - [x] 8.2: Test HandoffCard displays correct information
  - [x] 8.3: Test HandoffViewer renders all sections
  - [x] 8.4: Test VoiceNotePlayer controls work correctly

## Dev Notes

### Technical Requirements

**Database Query Pattern (Story 9.4 prerequisite)**
```sql
-- Query pending handoffs for incoming supervisor
SELECT h.*, u.email as creator_name
FROM shift_handoffs h
JOIN auth.users u ON h.created_by = u.id
WHERE h.status = 'pending_acknowledgment'
  AND h.assets_covered && (
    SELECT array_agg(asset_id)
    FROM supervisor_assignments
    WHERE user_id = $current_user_id
  )
ORDER BY h.created_at DESC;
```

**RLS Policy Expectation (from Story 9.4)**
- Users can read handoffs they created OR where their assigned assets overlap with `assets_covered`

### Architecture Compliance

**Component Pattern** - Follow existing card component structure:
```typescript
// Reference: apps/web/src/components/action-list/ActionItemCard.tsx
// - Use Card from @/components/ui/card
// - Include JSDoc with Story/AC references
// - Follow Industrial Clarity visual patterns
```

**Page Route Pattern:**
```
apps/web/src/app/(main)/handoff/
  page.tsx          // Handoff list
  [id]/page.tsx     // Handoff detail
```

**File Structure (per architecture/implementation-patterns.md):**
```
apps/web/src/components/handoff/
  HandoffList.tsx
  HandoffCard.tsx
  HandoffViewer.tsx
  VoiceNotePlayer.tsx
  __tests__/
    HandoffList.test.tsx
    HandoffCard.test.tsx
    HandoffViewer.test.tsx
    VoiceNotePlayer.test.tsx
```

### Library/Framework Requirements

| Library | Version | Purpose |
|---------|---------|---------|
| Next.js | 14+ (App Router) | Page routing, SSR |
| Shadcn/UI | Latest | Card, Badge, Button components |
| Tailwind CSS | Latest | Responsive tablet-first styling |
| Lucide React | Latest | Icons (Play, Pause, Clock, User) |

**HTML5 Audio API** - Native browser API for voice playback:
- Use `<audio>` element with custom controls
- `useRef` for audio element access
- Handle `onTimeUpdate`, `onLoadedMetadata`, `onEnded` events

### UI/UX Requirements

**Industrial Clarity Design:**
- Typography: 24px+ for key values, 18px minimum body text
- Touch targets: 44x44px minimum for tablet
- Color coding: Use existing badge variants (info, warning, safety)
- Cards: Use existing Card component with appropriate padding

**Tablet-First Responsive:**
```css
/* Mobile-first but optimize for tablet (768px-1024px) */
.handoff-viewer {
  @apply p-4 md:p-6 lg:p-8;
  @apply grid gap-4 md:gap-6;
}

/* Touch targets */
.play-button {
  @apply min-w-[44px] min-h-[44px];
}
```

### Anti-Pattern Prevention

**DO NOT:**
- Create custom audio player from scratch - use HTML5 `<audio>` with custom controls overlay
- Fetch all handoffs without filtering - always filter by supervisor assignments
- Skip TypeScript types - all data must be typed
- Hard-code user data - use auth context for current user
- Create new UI primitives - use existing Shadcn components

**DO:**
- Reuse existing card patterns from `ActionItemCard.tsx`
- Use existing hooks pattern from `useDailyActions.ts`
- Follow test file naming: `{Component}.test.tsx` in `__tests__/`
- Use Supabase client from existing setup
- Include loading and error states

### Testing Requirements

**Unit Tests (Vitest + React Testing Library):**
```typescript
// HandoffList.test.tsx
describe('HandoffList', () => {
  it('renders pending handoffs section when data exists')
  it('shows empty state when no pending handoffs')
  it('filters by supervisor assignments correctly')
})

// VoiceNotePlayer.test.tsx
describe('VoiceNotePlayer', () => {
  it('displays transcript below audio')
  it('shows duration after metadata loads')
  it('toggles play/pause state')
  it('handles audio load errors gracefully')
})
```

**Test Data Factories:**
```typescript
const createMockHandoff = (overrides = {}) => ({
  id: 'handoff-123',
  created_by: 'user-456',
  creator_name: 'John Smith',
  shift_date: '2026-01-15',
  shift_type: 'day',
  status: 'pending_acknowledgment',
  summary_text: 'Shift summary...',
  assets_covered: ['asset-1', 'asset-2'],
  created_at: '2026-01-15T14:00:00Z',
  voice_notes: [],
  ...overrides
})
```

### Project Structure Notes

**Alignment with Architecture:**
- Pages in `app/(main)/handoff/` per voice-briefing.md route structure
- Components in `components/handoff/` per implementation-patterns.md
- Hooks in `hooks/` following existing patterns

**Dependencies (Story 9.4 must provide):**
- `shift_handoffs` table with RLS policies
- `handoff_voice_notes` table
- Voice audio storage in Supabase Storage bucket

### References

- [Source: _bmad/bmm/data/architecture/voice-briefing.md#Frontend-Structure]
- [Source: _bmad/bmm/data/architecture/implementation-patterns.md#Handoff-Component-Naming]
- [Source: _bmad-output/planning-artifacts/epic-9.md#Story-9.5]
- [Source: apps/web/src/components/action-list/ActionItemCard.tsx] - Card pattern reference

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - No critical issues encountered during implementation.

### Completion Notes List

- **Task 7**: Created TypeScript types in `apps/web/src/types/handoff.ts` with full interfaces for Handoff, HandoffListItem, HandoffVoiceNote, and API response types. Created `useHandoff` and `useHandoffList` hooks following existing patterns from `useDailyActions.ts`.

- **Task 6**: VoiceNotePlayer already existed from Story 9.3 with full AC#3 compliance (play/pause, seek, transcript display). Reused existing component without modification.

- **Task 3**: Created HandoffCard component with status badges (pending/acknowledged), creator name display, timestamp, summary preview, voice note count, and drill-down navigation. Follows ActionItemCard pattern with Industrial Clarity styling.

- **Task 2**: Created HandoffList component with pending/completed sections, empty state, loading skeleton, and section headers with count badges.

- **Task 5**: Created HandoffViewer with shift summary section, text notes, expandable voice note players with transcript, assets covered list, and acknowledge button placeholder (for Story 9.7). Implements tablet-first layout with responsive padding and 44x44px touch targets.

- **Task 1**: Created handoff list page at `/handoff` with pending notification banner (AC#1), authentication check, success banner for created handoffs, and Create Handoff button linking to `/handoff/new`.

- **Task 4**: Created handoff detail page at `/handoff/[id]` with HandoffViewer integration, back navigation, loading/error states, and acknowledge callback placeholder.

- **Task 8**: Created comprehensive tests for HandoffList (9 tests), HandoffCard (15 tests), and HandoffViewer (15 tests). VoiceNotePlayer tests already existed from Story 9.3 (9 tests). Total: 48 tests (39 new + 9 reused).

### File List

- apps/web/src/types/handoff.ts (new)
- apps/web/src/hooks/useHandoff.ts (new)
- apps/web/src/hooks/useHandoffList.ts (new)
- apps/web/src/components/handoff/HandoffCard.tsx (new)
- apps/web/src/components/handoff/HandoffList.tsx (new)
- apps/web/src/components/handoff/HandoffViewer.tsx (new)
- apps/web/src/app/(main)/handoff/page.tsx (new)
- apps/web/src/app/(main)/handoff/[id]/page.tsx (new)
- apps/web/src/components/handoff/__tests__/HandoffList.test.tsx (new)
- apps/web/src/components/handoff/__tests__/HandoffCard.test.tsx (new)
- apps/web/src/components/handoff/__tests__/HandoffViewer.test.tsx (new)

## Change Log

- 2026-01-17: Story implementation complete - all 8 tasks completed with 48 tests passing
- 2026-01-17: Code review fixes applied - removed debug console.log, fixed VoiceNotePlayer touch target to 44x44px
