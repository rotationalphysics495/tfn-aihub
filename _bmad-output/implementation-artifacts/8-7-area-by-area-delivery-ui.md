# Story 8.7: Area-by-Area Delivery UI

Status: ready-for-dev

## Story

As a **user**,
I want **a clear visual interface showing briefing progress**,
So that **I can follow along and know what's coming next**.

## Acceptance Criteria

1. **Given** a briefing is in progress
   **When** viewing the briefing page
   **Then** the UI displays:
   - Current section name and progress indicator
   - Text transcript of current section
   - List of upcoming areas (dimmed)
   - Completed areas (checked)
   - Controls: Pause, Skip to Next, End Briefing

2. **Given** a section is playing
   **When** audio completes
   **Then** the pause prompt appears
   **And** a countdown timer shows silence detection progress

3. **Given** the user clicks "Skip to Next"
   **When** in a section or at a pause
   **Then** the current section ends immediately
   **And** the next section begins

4. **Given** the user clicks "End Briefing"
   **When** confirmed
   **Then** briefing playback stops
   **And** user returns to the main briefing page
   **And** partial completion is noted in session

## Tasks / Subtasks

- [ ] Task 1: Create `useBriefing` hook for state management (AC: #1, #2, #3, #4)
  - [ ] 1.1: Define `BriefingState` interface (sections, currentIndex, status, pauseCountdown)
  - [ ] 1.2: Implement section navigation (next, previous, skip, end)
  - [ ] 1.3: Implement pause countdown timer logic (3-4 seconds)
  - [ ] 1.4: Add audio completion detection callback integration
  - [ ] 1.5: Add partial completion tracking for session
  - [ ] 1.6: Write unit tests for hook

- [ ] Task 2: Create `AreaProgress` stepper component (AC: #1)
  - [ ] 2.1: Implement vertical stepper with area names
  - [ ] 2.2: Style current section (highlighted)
  - [ ] 2.3: Style completed sections (checkmark, muted)
  - [ ] 2.4: Style upcoming sections (dimmed)
  - [ ] 2.5: Add responsive design (tablet + desktop)
  - [ ] 2.6: Write component tests

- [ ] Task 3: Update `BriefingPlayer` component (AC: #1, #2)
  - [ ] 3.1: Integrate with `useBriefing` hook
  - [ ] 3.2: Display current section name prominently
  - [ ] 3.3: Add text transcript panel with auto-scroll
  - [ ] 3.4: Show pause countdown overlay when audio completes
  - [ ] 3.5: Add progress indicator (e.g., "Section 3 of 7")

- [ ] Task 4: Create voice controls component (AC: #3, #4)
  - [ ] 4.1: Implement Pause/Resume button with icon toggle
  - [ ] 4.2: Implement "Skip to Next" button
  - [ ] 4.3: Implement "End Briefing" button with confirmation dialog
  - [ ] 4.4: Add keyboard shortcuts (Space for pause, Right arrow for skip)
  - [ ] 4.5: Write component tests

- [ ] Task 5: Create briefing playback page route (AC: #1, #4)
  - [ ] 5.1: Create `apps/web/src/app/(main)/briefing/[id]/page.tsx`
  - [ ] 5.2: Compose BriefingPlayer, AreaProgress, VoiceControls
  - [ ] 5.3: Handle briefing end navigation back to launcher
  - [ ] 5.4: Track partial completion in session storage
  - [ ] 5.5: Add responsive layout for tablet/desktop

- [ ] Task 6: Integration testing
  - [ ] 6.1: Test full briefing playback flow
  - [ ] 6.2: Test pause countdown and auto-continue
  - [ ] 6.3: Test skip and end functionality
  - [ ] 6.4: Test responsive behavior on different viewports

## Dev Notes

### Architecture Compliance

**Required Pattern:** This story implements the frontend UI for briefing delivery as specified in the Voice Briefing Extension architecture.

**Key Dependencies:**
- Depends on Story 8.3 (Briefing Synthesis Engine) for `BriefingResponse` structure
- Depends on Story 8.1 (ElevenLabs TTS Integration) for `BriefingPlayer` base component
- Depends on Story 8.4 (Morning Briefing Workflow) for briefing data

**BriefingResponse Structure (from architecture):**
```typescript
interface BriefingResponse {
  sections: BriefingSection[]  // Text + citations (always present)
  audio_stream_url?: string    // Nullable = graceful degradation
  total_duration_estimate: number  // For progress UI
}

interface BriefingSection {
  area_name: string
  content: string
  citations: Citation[]
  pause_prompt: string  // e.g., "Any questions on Grinding before I continue?"
}
```

### Technical Requirements

**Frontend Framework:** Next.js 14+ (App Router)
- Use `'use client'` directive for interactive components
- Follow existing patterns in `apps/web/src/components/`

**State Management Pattern:**
- Create `useBriefing` hook in `apps/web/src/lib/hooks/useBriefing.ts`
- Follow the existing hook pattern from `useLivePulse.ts`:
  - Use `useState` for state
  - Use `useRef` for timers/cleanup
  - Export interface for hook return type
  - Include proper cleanup in `useEffect`

**Styling Requirements:**
- Use Tailwind CSS + Shadcn/UI components
- Follow "Industrial Clarity" design principles:
  - High contrast for factory lighting visibility
  - Safety Red reserved exclusively for incidents
  - Status badges follow existing `StatusBadge` pattern

**Responsive Design:**
- Primary target: Tablet (iPad-size, ~768px-1024px)
- Secondary: Desktop (1024px+)
- Use Tailwind responsive prefixes: `md:`, `lg:`

### File Structure Requirements

**Files to Create:**
```
apps/web/src/
  app/(main)/briefing/[id]/
    page.tsx                    # Briefing playback view
  components/voice/
    AreaProgress.tsx            # Progress stepper
    VoiceControls.tsx           # Play/pause/next controls (may extend existing)
    BriefingTranscript.tsx      # Scrollable transcript panel
    PauseCountdown.tsx          # Countdown overlay
    __tests__/
      AreaProgress.test.tsx
      VoiceControls.test.tsx
  lib/hooks/
    useBriefing.ts              # Briefing state management
```

**Files to Modify:**
- `apps/web/src/components/voice/BriefingPlayer.tsx` (if exists from Story 8.1)

### Existing Code Patterns to Follow

**Hook Pattern (from `useLivePulse.ts`):**
```typescript
'use client'

import { useState, useEffect, useCallback, useRef } from 'react'

interface UseBriefingOptions {
  // Options here
}

interface UseBriefingReturn {
  // Return type here
}

export function useBriefing(options: UseBriefingOptions = {}): UseBriefingReturn {
  const [state, setState] = useState<BriefingState>({...})
  const timerRef = useRef<NodeJS.Timeout | null>(null)
  const mountedRef = useRef(true)

  // Cleanup on unmount
  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      if (timerRef.current) {
        clearTimeout(timerRef.current)
      }
    }
  }, [])

  // ... implementation
}
```

**Component Pattern (from existing components):**
```typescript
'use client'

import { cn } from '@/lib/utils'

interface AreaProgressProps {
  className?: string
  sections: BriefingSection[]
  currentIndex: number
  // ...
}

export function AreaProgress({ className, sections, currentIndex }: AreaProgressProps) {
  return (
    <div className={cn('...', className)}>
      {/* Implementation */}
    </div>
  )
}
```

**Shadcn/UI Components Available:**
- `Button` - for controls
- `Card` - for section containers
- `Badge` - for status indicators
- `Alert` - for notifications
- `ScrollArea` - for transcript scrolling

### Project Structure Notes

**Route Structure:**
```
apps/web/src/app/
  (auth)/login/           # Existing auth routes
  dashboard/              # Existing dashboard
  morning-report/         # Existing morning report
  (main)/                 # New: Main layout group
    briefing/             # New: Briefing feature
      page.tsx            # Launcher (Story 8.4)
      [id]/page.tsx       # Playback (This story)
```

**Note:** The `(main)` route group may need to be created. Check if it exists; if not, create the playback page under `app/briefing/[id]/page.tsx` following the existing flat structure.

### Testing Requirements

**Test Framework:** Jest + React Testing Library (existing setup)

**Test Location:** `__tests__/` subdirectory within component directory

**Required Test Coverage:**
- Unit tests for `useBriefing` hook
- Component tests for each new component
- Test pause countdown timer accuracy
- Test state transitions (playing -> paused -> playing)

**Test Pattern (from existing tests):**
```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { AreaProgress } from '../AreaProgress'

describe('AreaProgress', () => {
  it('highlights current section', () => {
    render(<AreaProgress sections={mockSections} currentIndex={2} />)
    // assertions
  })
})
```

### Previous Story Intelligence

No previous stories in Epic 8 have been implemented yet. This is one of the early stories in the Voice Briefing Foundation epic.

**Cross-Story Dependencies:**
- Story 8.1 (TTS) creates base `BriefingPlayer.tsx`
- Story 8.3 (Synthesis Engine) defines `BriefingResponse` model
- Story 8.4 (Morning Briefing Workflow) provides briefing data and launcher page

**Recommendation:** Coordinate with stories 8.1, 8.3, and 8.4 to ensure interface alignment.

### Latest Tech Information

**React 18+ Patterns:**
- Use `useCallback` for event handlers passed to children
- Use `useRef` for values that shouldn't trigger re-renders
- Cleanup timers in `useEffect` return function

**Tailwind CSS:**
- Current version supports `animate-*` classes for transitions
- Use `transition-all` for smooth state changes
- Use `backdrop-blur-sm` for overlay effects

**Next.js 14 App Router:**
- Dynamic routes use `[param]` folder naming
- Page components are server components by default; add `'use client'` for interactivity
- Use `useRouter()` from `next/navigation` for programmatic navigation

### UI/UX Specifications

**From UX Design Document:**
- "Glanceability": Status readable from 3 feet away on tablet
- "Trust & Transparency": AI recommendations link to raw data
- Visual distinction between states (active vs completed vs upcoming)

**Progress Stepper Design:**
- Vertical orientation for area list
- Active step: Full color, bold text, pulse/glow indicator
- Completed steps: Muted color, checkmark icon
- Upcoming steps: Dimmed text, circle/dot indicator

**Pause Countdown UI:**
- Overlay on briefing content
- Large countdown number (3, 2, 1)
- Text: "Continuing to [Next Area] in X seconds..."
- Manual continue button below countdown

**Voice Controls Layout:**
- Fixed position at bottom of briefing view
- Horizontal button row: [Pause/Resume] [Skip to Next] [End Briefing]
- End Briefing button should be visually distinct (outline/secondary style)

### Performance Requirements

**From NFR8:** Briefing generation completes within 30 seconds
**From NFR9:** TTS begins playback within 2 seconds

**UI Performance:**
- Progress updates should feel instant (<100ms)
- Countdown timer updates every 1 second
- Auto-scroll should be smooth (use `scrollIntoView({ behavior: 'smooth' })`)

### References

- [Source: architecture/voice-briefing.md#Project Structure]
- [Source: architecture/voice-briefing.md#Architectural Insights]
- [Source: prd.md#Epic 8]
- [Source: epic-8.md#Story 8.7]
- [Source: ux-design.md#Usability Goals]
- [Source: apps/web/src/hooks/useLivePulse.ts] - Hook pattern reference
- [Source: apps/web/src/components/chat/ChatSidebar.tsx] - Component pattern reference

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
