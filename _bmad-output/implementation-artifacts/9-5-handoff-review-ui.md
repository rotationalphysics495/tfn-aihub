# Story 9.5: Handoff Review UI

Status: ready-for-dev

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

- [ ] Task 1: Create handoff list page (AC: #1)
  - [ ] 1.1: Create `apps/web/src/app/(main)/handoff/page.tsx`
  - [ ] 1.2: Implement pending handoff query with asset overlap filter
  - [ ] 1.3: Display notification banner for pending handoffs

- [ ] Task 2: Create handoff list component (AC: #1)
  - [ ] 2.1: Create `apps/web/src/components/handoff/HandoffList.tsx`
  - [ ] 2.2: Fetch handoffs filtered by supervisor assignments
  - [ ] 2.3: Display list with status indicators

- [ ] Task 3: Create handoff card component (AC: #1, #2)
  - [ ] 3.1: Create `apps/web/src/components/handoff/HandoffCard.tsx`
  - [ ] 3.2: Display outgoing supervisor name, timestamp, summary preview
  - [ ] 3.3: Show pending/acknowledged status badge
  - [ ] 3.4: Link to detail page

- [ ] Task 4: Create handoff detail page (AC: #2, #3, #4)
  - [ ] 4.1: Create `apps/web/src/app/(main)/handoff/[id]/page.tsx`
  - [ ] 4.2: Implement handoff data fetching with voice notes
  - [ ] 4.3: Render HandoffViewer component

- [ ] Task 5: Create handoff viewer component (AC: #2, #3, #4)
  - [ ] 5.1: Create `apps/web/src/components/handoff/HandoffViewer.tsx`
  - [ ] 5.2: Display shift summary section with citations
  - [ ] 5.3: Display text notes section
  - [ ] 5.4: Integrate voice note player
  - [ ] 5.5: Add acknowledge button (placeholder for Story 9.7)
  - [ ] 5.6: Implement tablet-first responsive layout

- [ ] Task 6: Create voice note player (AC: #3)
  - [ ] 6.1: Create `apps/web/src/components/handoff/VoiceNotePlayer.tsx`
  - [ ] 6.2: Implement HTML5 audio element with custom controls
  - [ ] 6.3: Display transcript below audio player
  - [ ] 6.4: Add play/pause, seek bar, duration display
  - [ ] 6.5: Handle loading/error states gracefully

- [ ] Task 7: Create API types and hooks (AC: #1, #2)
  - [ ] 7.1: Create `apps/web/src/types/handoff.ts` with TypeScript interfaces
  - [ ] 7.2: Create `apps/web/src/hooks/useHandoff.ts` for data fetching
  - [ ] 7.3: Create `apps/web/src/hooks/useHandoffList.ts` for list queries

- [ ] Task 8: Write component tests
  - [ ] 8.1: Test HandoffList renders pending/completed sections
  - [ ] 8.2: Test HandoffCard displays correct information
  - [ ] 8.3: Test HandoffViewer renders all sections
  - [ ] 8.4: Test VoiceNotePlayer controls work correctly

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

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
