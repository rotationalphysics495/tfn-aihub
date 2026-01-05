# Story 1.7: Command Center UI Shell

Status: ready-for-dev

## Story

As a Plant Manager,
I want a Command Center dashboard layout with designated sections for Action List, Live Pulse, and Financial widgets,
so that I can navigate to a single "home base" that will house all critical manufacturing intelligence.

## Acceptance Criteria

1. **Dashboard Layout Structure**
   - Command Center page exists at route `/` (root) or `/dashboard`
   - Layout contains three distinct placeholder sections: Action List (primary), Live Pulse, and Financial widgets
   - Layout follows responsive grid: single column on mobile, multi-column on tablet/desktop
   - Page title displays "Command Center" in the header

2. **Action List Section (Primary)**
   - Positioned as the primary/prominent section per "Action First, Data Second" principle
   - Contains placeholder card indicating "Daily Action List - Coming in Epic 3"
   - Section visually distinguishable with appropriate heading

3. **Live Pulse Section**
   - Positioned to show real-time status area
   - Contains placeholder indicating "Live Pulse - Coming in Epic 2"
   - Uses distinct visual treatment for "Live" context (per UX: vibrant/pulsing indicators ready)

4. **Financial Widgets Section**
   - Contains placeholder for financial impact/cost widgets
   - Indicates "Financial Intelligence - Coming in Epic 2"

5. **Industrial Clarity Design Compliance**
   - Uses Tailwind CSS + Shadcn/UI components established in Story 1.6
   - High-contrast theme suitable for factory floor visibility
   - "Glanceability" - content readable from 3 feet away on tablet
   - "Safety Red" color NOT used (reserved for actual safety incidents)

6. **Navigation Integration**
   - Dashboard accessible via main navigation
   - Page renders without errors when authenticated user visits

## Tasks / Subtasks

- [ ] Task 1: Create Command Center page route (AC: #1, #6)
  - [ ] 1.1 Create `/app/dashboard/page.tsx` (or `/app/page.tsx` if dashboard is root)
  - [ ] 1.2 Add page metadata (title: "Command Center")
  - [ ] 1.3 Ensure route is accessible from navigation

- [ ] Task 2: Implement responsive grid layout (AC: #1, #5)
  - [ ] 2.1 Create grid container using Tailwind CSS
  - [ ] 2.2 Configure breakpoints: 1 col (mobile) -> 2 col (md) -> 3 col (lg)
  - [ ] 2.3 Ensure proper spacing and padding for readability

- [ ] Task 3: Build Action List placeholder section (AC: #2, #5)
  - [ ] 3.1 Create ActionListSection component
  - [ ] 3.2 Use Shadcn/UI Card component for placeholder
  - [ ] 3.3 Add section heading "Daily Action List"
  - [ ] 3.4 Add placeholder text with "Coming in Epic 3" indicator
  - [ ] 3.5 Style as primary/prominent section (larger area, prominent position)

- [ ] Task 4: Build Live Pulse placeholder section (AC: #3, #5)
  - [ ] 4.1 Create LivePulseSection component
  - [ ] 4.2 Use Shadcn/UI Card component for placeholder
  - [ ] 4.3 Add section heading "Live Pulse"
  - [ ] 4.4 Add placeholder with "Coming in Epic 2" indicator
  - [ ] 4.5 Prepare distinct visual styling for "live" context

- [ ] Task 5: Build Financial Widgets placeholder section (AC: #4, #5)
  - [ ] 5.1 Create FinancialWidgetsSection component
  - [ ] 5.2 Use Shadcn/UI Card component for placeholder
  - [ ] 5.3 Add section heading "Financial Intelligence"
  - [ ] 5.4 Add placeholder with "Coming in Epic 2" indicator

- [ ] Task 6: Verify Industrial Clarity compliance (AC: #5)
  - [ ] 6.1 Review contrast ratios for factory floor visibility
  - [ ] 6.2 Test text sizes for "glanceability" (readable at 3ft on tablet)
  - [ ] 6.3 Confirm no use of "Safety Red" color

## Dev Notes

### Architecture Patterns

- **Frontend Framework:** Next.js 14+ with App Router
- **File Location:** `apps/web/src/app/` for pages, `apps/web/src/components/` for components
- **Styling:** Tailwind CSS with Shadcn/UI components (established in Story 1.6)
- **Component Pattern:** Create reusable section components in `apps/web/src/components/dashboard/`

### Technical Requirements

- Use React Server Components where appropriate (Next.js App Router default)
- No API calls needed for this story - placeholder UI only
- Components should accept future props for data integration (Epic 2, 3)
- Follow existing code patterns from Story 1.6 design system setup

### UX Design Compliance

| Principle | Implementation |
|-----------|----------------|
| Action First, Data Second | Action List section positioned first/prominently in layout |
| Industrial High-Contrast | Use design tokens from Story 1.6 theme |
| Glanceability | Minimum text size 16px body, 24px+ headings |
| Visual Context Switching | Prepare distinct styling for Live vs Static sections |
| Safety Red Reserved | Do NOT use red for placeholders - only for actual safety incidents |

### Dependencies

- **Requires:** Story 1.6 (Industrial Clarity Design System) must be completed first
- **Enables:** Epic 2 (Data Pipelines - will populate Live Pulse, Financial sections)
- **Enables:** Epic 3 (Action Engine - will populate Daily Action List)

### Project Structure Notes

```
apps/web/src/
  app/
    dashboard/
      page.tsx           # Command Center main page
  components/
    dashboard/
      ActionListSection.tsx
      LivePulseSection.tsx
      FinancialWidgetsSection.tsx
    ui/                  # Shadcn/UI components (from Story 1.6)
```

### Testing Guidance

- Visual inspection on desktop and tablet viewports
- Verify responsive breakpoints work correctly
- Confirm navigation integration
- No unit tests required for placeholder components (will be added when real functionality is implemented)

### References

- [Source: _bmad/bmm/data/architecture.md#4. Repository Structure] - TurboRepo structure with apps/web
- [Source: _bmad/bmm/data/architecture.md#3. Tech Stack] - Next.js 14+, Tailwind CSS, Shadcn/UI
- [Source: _bmad/bmm/data/ux-design.md#2. Overall UX Goals] - Industrial Clarity, Glanceability, Action First
- [Source: _bmad/bmm/data/ux-design.md#3. Information Architecture] - Command Center as home with Action List, Live Pulse
- [Source: _bmad-output/planning-artifacts/epic-1.md] - Story context within Epic 1 foundation

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
