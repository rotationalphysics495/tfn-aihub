# Story 8.8: User Preference Onboarding

Status: ready-for-dev

## Story

As a **first-time user**,
I want **a quick onboarding flow to set my preferences**,
So that **briefings are personalized from my first interaction**.

## Acceptance Criteria

1. **Given** a user interacts with the system for the first time (FR42)
   **When** onboarding is detected
   **Then** the onboarding flow is triggered before the original request
   **And** flow completes in under 2 minutes (FR43)

2. **Given** onboarding begins
   **When** the user progresses through steps (FR44)
   **Then** the flow includes:
   - Step 1: Welcome + explain quick setup
   - Step 2: Role selection (Plant Manager or Supervisor)
   - Step 3: For Supervisor: display assigned assets (from `supervisor_assignments`)
   - Step 4: Area order preference (drag-to-reorder or numbered selection)
   - Step 5: Detail level preference (Summary or Detailed)
   - Step 6: Voice preference (On/Off)
   - Step 7: Confirmation + handoff to original request

3. **Given** the user completes onboarding
   **When** preferences are saved
   **Then** preferences are stored in `user_preferences` table
   **And** user is redirected to their original destination

4. **Given** the user abandons onboarding
   **When** they close or navigate away
   **Then** default preferences are applied
   **And** onboarding triggers again on next visit

5. **Given** a user wants to modify preferences later (FR45)
   **When** they navigate to Settings > Preferences
   **Then** all onboarding options are available to edit

## Tasks / Subtasks

- [ ] Task 1: Create database migration for `user_preferences` table (AC: #3)
  - [ ] 1.1: Create migration file `supabase/migrations/20260115_003_user_preferences.sql`
  - [ ] 1.2: Define table schema with all preference columns
  - [ ] 1.3: Add RLS policies for user-owned records
  - [ ] 1.4: Create index on `user_id` for fast lookups

- [ ] Task 2: Create `WelcomeStep` component (AC: #2 - Step 1)
  - [ ] 2.1: Create `apps/web/src/components/onboarding/WelcomeStep.tsx`
  - [ ] 2.2: Display welcome message and explain the setup process
  - [ ] 2.3: Show estimated completion time (under 2 minutes)
  - [ ] 2.4: Add "Get Started" button to proceed

- [ ] Task 3: Create `RoleStep` component (AC: #2 - Step 2)
  - [ ] 3.1: Create `apps/web/src/components/onboarding/RoleStep.tsx`
  - [ ] 3.2: Display role selection cards (Plant Manager, Supervisor)
  - [ ] 3.3: Show role descriptions and scope differences
  - [ ] 3.4: Update state on role selection

- [ ] Task 4: Create `SupervisorAssetsStep` component (AC: #2 - Step 3)
  - [ ] 4.1: Create `apps/web/src/components/onboarding/SupervisorAssetsStep.tsx`
  - [ ] 4.2: Fetch assigned assets from `supervisor_assignments` table
  - [ ] 4.3: Display read-only list of assigned assets/areas
  - [ ] 4.4: Handle case when no assets are assigned (show message)
  - [ ] 4.5: Only render for Supervisor role

- [ ] Task 5: Create `AreaOrderSelector` component (AC: #2 - Step 4)
  - [ ] 5.1: Create `apps/web/src/components/preferences/AreaOrderSelector.tsx`
  - [ ] 5.2: Implement drag-and-drop reordering (use @dnd-kit or native HTML5 DnD)
  - [ ] 5.3: Add numbered input fallback for accessibility
  - [ ] 5.4: Display all 7 production areas with default order
  - [ ] 5.5: Update state on order change

- [ ] Task 6: Create `DetailLevelToggle` component (AC: #2 - Step 5)
  - [ ] 6.1: Create `apps/web/src/components/preferences/DetailLevelToggle.tsx`
  - [ ] 6.2: Implement toggle between "Summary" and "Detailed"
  - [ ] 6.3: Show description of each level
  - [ ] 6.4: Use existing toggle/switch UI pattern

- [ ] Task 7: Create `VoiceToggle` component (AC: #2 - Step 6)
  - [ ] 7.1: Create `apps/web/src/components/preferences/VoiceToggle.tsx`
  - [ ] 7.2: Implement On/Off toggle for voice delivery
  - [ ] 7.3: Show description of voice feature
  - [ ] 7.4: Default to "On"

- [ ] Task 8: Create `PreferencesStep` component (AC: #2 - Steps 4-6)
  - [ ] 8.1: Create `apps/web/src/components/onboarding/PreferencesStep.tsx`
  - [ ] 8.2: Compose AreaOrderSelector, DetailLevelToggle, VoiceToggle
  - [ ] 8.3: Manage local state for all preferences
  - [ ] 8.4: Add navigation (Back/Continue) buttons

- [ ] Task 9: Create `OnboardingFlow` orchestrator component (AC: #1, #2, #3, #4)
  - [ ] 9.1: Create `apps/web/src/components/preferences/OnboardingFlow.tsx`
  - [ ] 9.2: Implement multi-step wizard with progress indicator
  - [ ] 9.3: Manage step navigation and validation
  - [ ] 9.4: Handle completion: save preferences and redirect
  - [ ] 9.5: Handle abandonment: apply defaults, flag for re-trigger

- [ ] Task 10: Create first-time detection hook (AC: #1, #4)
  - [ ] 10.1: Create `apps/web/src/lib/hooks/useOnboardingRequired.ts`
  - [ ] 10.2: Query `user_preferences` for current user on load
  - [ ] 10.3: Return `isRequired: true` if no record exists
  - [ ] 10.4: Return `originalDestination` for post-onboarding redirect

- [ ] Task 10b: Integrate onboarding into app layout (AC: #1)
  - [ ] 10b.1: Create `OnboardingGate` wrapper component in `components/onboarding/`
  - [ ] 10b.2: Use `useOnboardingRequired` hook in the wrapper
  - [ ] 10b.3: Render `OnboardingFlow` as full-screen overlay when required
  - [ ] 10b.4: Block navigation until onboarding completes or is dismissed
  - [ ] 10b.5: Wrap main layout in `apps/web/src/app/(main)/layout.tsx` with `OnboardingGate`

- [ ] Task 11: Create Settings > Preferences page (AC: #5)
  - [ ] 11.1: Create `apps/web/src/app/(main)/settings/preferences/page.tsx`
  - [ ] 11.2: Reuse all preference components (AreaOrderSelector, etc.)
  - [ ] 11.3: Load current preferences on mount
  - [ ] 11.4: Save on submit with feedback message

- [ ] Task 12: Create API endpoints for preferences (AC: #3, #5)
  - [ ] 12.1: Create `apps/api/app/api/preferences.py` with FastAPI router
  - [ ] 12.2: Implement `GET /api/v1/preferences` - get current user preferences
  - [ ] 12.3: Implement `POST /api/v1/preferences` - create preferences (onboarding)
  - [ ] 12.4: Implement `PUT /api/v1/preferences` - update preferences (settings page)
  - [ ] 12.5: Add user_id from auth token (not from request body)
  - [ ] 12.6: Register router in `apps/api/app/main.py`

- [ ] Task 12b: Create `usePreferences` hook for frontend API calls (AC: #3, #5)
  - [ ] 12b.1: Create `apps/web/src/lib/hooks/usePreferences.ts`
  - [ ] 12b.2: Implement `loadPreferences()` function
  - [ ] 12b.3: Implement `savePreferences()` function
  - [ ] 12b.4: Handle loading/error states

- [ ] Task 13: Integration testing
  - [ ] 13.1: Test full onboarding flow completion
  - [ ] 13.2: Test onboarding abandonment and re-trigger
  - [ ] 13.3: Test settings page edit and save
  - [ ] 13.4: Test first-time detection accuracy

## Dev Notes

### Architecture Compliance

**Required Pattern:** This story implements user preference onboarding as specified in the Voice Briefing Extension architecture. Preferences are stored in Supabase for structured queries, with Mem0 sync handled in Story 8.9.

**Key Dependencies:**
- Depends on Story 8.5 (Supervisor Scoped Briefings) for `supervisor_assignments` table
  - **Note:** If 8.5 is not yet implemented, the `SupervisorAssetsStep` should gracefully handle missing table by showing "No assets assigned yet - your administrator will configure your assignments"
- Story 8.9 (Mem0 Preference Storage) will add Mem0 sync after this story
- Used by Story 8.4 (Morning Briefing Workflow) for briefing personalization
- Used by Story 8.5 for supervisor scope filtering

**Database Schema (from architecture):**
```sql
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id),
    role TEXT, -- 'plant_manager' or 'supervisor' - Denormalized for quick access
    area_order TEXT[], -- ['Grinding', 'Packing', ...] - User-controlled sequence
    detail_level TEXT CHECK (detail_level IN ('summary', 'detailed')),
    voice_enabled BOOLEAN DEFAULT true,
    onboarding_complete BOOLEAN DEFAULT false,
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

### Technical Requirements

**Frontend Framework:** Next.js 14+ (App Router)
- Use `'use client'` directive for all interactive components
- Follow existing patterns in `apps/web/src/components/`

**Backend Framework:** FastAPI
- Follow existing endpoint patterns in `apps/api/app/api/`
- Use Pydantic models for request/response validation
- Use `get_current_user()` dependency for auth

**Styling Requirements:**
- Use Tailwind CSS + Shadcn/UI components
- Follow "Industrial Clarity" design principles:
  - High contrast for factory lighting visibility
  - Clear step progress indicators
  - Touch-friendly targets (minimum 44x44px)

### Default Preferences (for abandonment)

If user abandons onboarding, apply these defaults:
- `role`: `'plant_manager'`
- `area_order`: Default order from architecture (Packing, Rychigers, Grinding, Powder, Roasting, Green Bean, Flavor Room)
- `detail_level`: `'summary'`
- `voice_enabled`: `true`
- `onboarding_complete`: `false` (triggers again on next visit)

### 7 Production Areas (from PRD)

The briefing system covers these 7 areas in configurable order:
1. **Packing** - CAMA lines, Pack Cells, Variety Pack, Bag Lines, Nuspark
2. **Rychigers** - 101-109, 1009
3. **Grinding** - Grinders 1-5
4. **Powder** - 1002-1004 Fill & Pack, Manual Bulk
5. **Roasting** - Roasters 1-4
6. **Green Bean** - Manual, Silo Transfer
7. **Flavor Room** - Coffee Flavor Room (Manual)

### File Structure Requirements

**Files to Create:**
```
apps/web/src/
  app/(main)/settings/
    preferences/
      page.tsx                       # Settings > Preferences page
  components/onboarding/
    WelcomeStep.tsx                  # Step 1: Welcome
    RoleStep.tsx                     # Step 2: Role selection
    SupervisorAssetsStep.tsx         # Step 3: Assigned assets (Supervisor only)
    PreferencesStep.tsx              # Steps 4-6: Preferences composite
    OnboardingGate.tsx               # Wrapper to trigger onboarding for first-time users
    __tests__/
      WelcomeStep.test.tsx
      RoleStep.test.tsx
      OnboardingFlow.test.tsx
      OnboardingGate.test.tsx
  components/preferences/
    OnboardingFlow.tsx               # Multi-step wizard orchestrator
    AreaOrderSelector.tsx            # Drag-to-reorder or numbered input
    DetailLevelToggle.tsx            # Summary/Detailed toggle
    VoiceToggle.tsx                  # On/Off toggle
    __tests__/
      AreaOrderSelector.test.tsx
      DetailLevelToggle.test.tsx
      VoiceToggle.test.tsx
  lib/hooks/
    useOnboardingRequired.ts         # First-time detection hook
    usePreferences.ts                # Hook for loading/saving preferences

apps/api/app/
  api/
    preferences.py                   # Preference API endpoints
  models/
    preferences.py                   # UserPreferences Pydantic model

supabase/migrations/
  20260115_003_user_preferences.sql  # Database table creation
```

### Existing Code Patterns to Follow

**Component Pattern (from FilterBar.tsx):**
```typescript
'use client'

import { cn } from '@/lib/utils'

interface ComponentProps {
  className?: string
  // ... props
}

export function Component({ className, ...props }: ComponentProps) {
  return (
    <div className={cn('...', className)}>
      {/* Implementation */}
    </div>
  )
}
```

**Hook Pattern (from existing hooks):**
```typescript
'use client'

import { useState, useEffect } from 'react'
import { useSupabaseClient, useSession } from '@supabase/auth-helpers-react'

interface UseOnboardingRequiredReturn {
  isRequired: boolean
  isLoading: boolean
  originalDestination: string | null
}

export function useOnboardingRequired(): UseOnboardingRequiredReturn {
  const supabase = useSupabaseClient()
  const session = useSession()
  const [state, setState] = useState({
    isRequired: false,
    isLoading: true,
    originalDestination: null
  })

  useEffect(() => {
    if (!session?.user) return

    async function checkOnboarding() {
      const { data, error } = await supabase
        .from('user_preferences')
        .select('onboarding_complete')
        .eq('user_id', session.user.id)
        .single()

      setState({
        isRequired: !data || !data.onboarding_complete,
        isLoading: false,
        originalDestination: window.location.pathname
      })
    }

    checkOnboarding()
  }, [session, supabase])

  return state
}
```

**Shadcn/UI Components Available:**
- `Button` - for navigation actions
- `Card` - for role selection cards
- `Badge` - for step indicators
- `Switch` - for toggle components
- `ScrollArea` - for asset lists

**OnboardingGate Pattern:**
```typescript
'use client'

import { useOnboardingRequired } from '@/lib/hooks/useOnboardingRequired'
import { OnboardingFlow } from '@/components/preferences/OnboardingFlow'

interface OnboardingGateProps {
  children: React.ReactNode
}

export function OnboardingGate({ children }: OnboardingGateProps) {
  const { isRequired, isLoading, originalDestination } = useOnboardingRequired()

  if (isLoading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>
  }

  if (isRequired) {
    return (
      <>
        {/* Render children in background (dimmed/blurred) */}
        <div className="opacity-20 pointer-events-none">{children}</div>
        {/* Overlay onboarding flow */}
        <OnboardingFlow
          originalDestination={originalDestination}
          onComplete={() => window.location.reload()}
        />
      </>
    )
  }

  return <>{children}</>
}
```

### UI/UX Specifications

**From UX Design Document:**
- "Glanceability": Progress clearly visible
- "Trust & Transparency": Explain what each preference does
- Mobile-first responsive design

**Onboarding Flow UI:**
- Full-screen modal overlay
- Progress indicator showing current step (e.g., "Step 2 of 6")
- Clear Back/Continue navigation buttons
- Estimated time remaining
- Can dismiss (applies defaults)

**Role Selection UI:**
- Two large cards side-by-side (or stacked on mobile)
- Plant Manager card: "Full plant overview" description
- Supervisor card: "Focus on your assigned assets" description
- Visual icons for each role

**Area Order UI:**
- Vertical list of areas
- Drag handles on left side
- Numbers on right side (auto-update on drag)
- Accessible keyboard reordering (up/down arrows)

### Performance Requirements

**From FR43:** Flow completes in under 2 minutes
**Target:** Each step should be completable in under 20 seconds

**UI Performance:**
- Step transitions should be instant (<100ms)
- API calls should complete within 500ms
- Show loading state during API operations

### Database Migration SQL

```sql
-- Migration: 20260115_003_user_preferences.sql
-- Creates user_preferences table for onboarding and settings

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT CHECK (role IN ('plant_manager', 'supervisor')),
    area_order TEXT[] DEFAULT ARRAY['Packing', 'Rychigers', 'Grinding', 'Powder', 'Roasting', 'Green Bean', 'Flavor Room'],
    detail_level TEXT CHECK (detail_level IN ('summary', 'detailed')) DEFAULT 'summary',
    voice_enabled BOOLEAN DEFAULT true,
    onboarding_complete BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create index for fast user lookup
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- RLS: Users can only read/write their own preferences
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own preferences"
    ON user_preferences FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own preferences"
    ON user_preferences FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own preferences"
    ON user_preferences FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Trigger to update updated_at on changes
CREATE OR REPLACE FUNCTION update_user_preferences_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_user_preferences_updated_at();
```

### API Endpoint Specifications

**GET /api/v1/preferences**
- Returns current user's preferences
- 404 if no preferences exist (triggers onboarding)
- Response: `UserPreferencesResponse`

**POST /api/v1/preferences**
- Creates preferences (onboarding completion)
- Request body: `CreateUserPreferencesRequest`
- Response: `UserPreferencesResponse`

**PUT /api/v1/preferences**
- Updates existing preferences (settings page)
- Request body: `UpdateUserPreferencesRequest`
- Response: `UserPreferencesResponse`

**Pydantic Models:**
```python
from pydantic import BaseModel
from typing import List, Optional

class UserPreferencesBase(BaseModel):
    role: str  # 'plant_manager' or 'supervisor'
    area_order: List[str]
    detail_level: str  # 'summary' or 'detailed'
    voice_enabled: bool

class CreateUserPreferencesRequest(UserPreferencesBase):
    pass

class UpdateUserPreferencesRequest(BaseModel):
    role: Optional[str] = None
    area_order: Optional[List[str]] = None
    detail_level: Optional[str] = None
    voice_enabled: Optional[bool] = None

class UserPreferencesResponse(UserPreferencesBase):
    user_id: str
    onboarding_complete: bool
    updated_at: str
```

### Previous Story Intelligence

**From Story 8.7 (Area-by-Area Delivery UI):**
- Established `BriefingSection` interface with `area_name` field
- Area progress stepper component pattern
- Responsive tablet-first design approach
- Hook pattern with cleanup and mounted refs

**Recommendation:** Reuse the stepper visual pattern from 8.7 for the onboarding progress indicator.

### Testing Requirements

**Test Framework:** Jest + React Testing Library (existing setup)

**Required Test Coverage:**
- Unit tests for each preference component
- Unit tests for `useOnboardingRequired` hook
- Integration test for full onboarding flow
- Test default preference application on abandonment
- Test settings page load and save

**Test Pattern:**
```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { RoleStep } from '../RoleStep'

describe('RoleStep', () => {
  it('renders role selection options', () => {
    render(<RoleStep onSelect={jest.fn()} />)
    expect(screen.getByText('Plant Manager')).toBeInTheDocument()
    expect(screen.getByText('Supervisor')).toBeInTheDocument()
  })

  it('calls onSelect with selected role', () => {
    const onSelect = jest.fn()
    render(<RoleStep onSelect={onSelect} />)
    fireEvent.click(screen.getByText('Supervisor'))
    expect(onSelect).toHaveBeenCalledWith('supervisor')
  })
})
```

### Project Structure Notes

**Route Structure:**
```
apps/web/src/app/
  (auth)/login/           # Existing auth routes
  dashboard/              # Existing dashboard
  morning-report/         # Existing morning report
  (main)/                 # Main layout group
    briefing/             # Briefing feature (from earlier stories)
    settings/             # NEW: Settings section
      preferences/        # NEW: Preferences page (this story)
        page.tsx
```

**Onboarding Trigger Points:**
The onboarding should trigger on any first interaction. Implement via:
1. Create `OnboardingGate` wrapper component that wraps authenticated routes
2. `useOnboardingRequired` hook checks on app load
3. If `isRequired: true`, render `OnboardingFlow` as full-screen modal overlay
4. Store original destination (current URL) in component state
5. Block navigation/interaction with underlying page during onboarding
6. On completion, redirect to original destination
7. On abandonment, apply defaults and redirect to dashboard

**Implementation Location:**
- Wrap the main layout in `apps/web/src/app/(main)/layout.tsx` with `OnboardingGate`
- Or create `OnboardingProvider` context that any page can consume
- Recommended: Layout wrapper approach for simplicity

### References

- [Source: architecture/voice-briefing.md#User Preferences Architecture]
- [Source: architecture/voice-briefing.md#Project Structure]
- [Source: epic-8.md#Story 8.8]
- [Source: prd-voice-briefing-context.md#Feature 3: User Preferences System]
- [Source: prd-voice-briefing-context.md#Onboarding Flow Summary]
- [Source: apps/web/src/components/production/FilterBar.tsx] - Component pattern reference
- [Source: supabase/migrations/] - Migration pattern reference

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
