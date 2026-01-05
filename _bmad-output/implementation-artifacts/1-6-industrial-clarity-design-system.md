# Story 1.6: Industrial Clarity Design System

Status: ready-for-dev

## Story

As a **Plant Manager or Line Supervisor**,
I want **a high-contrast, industrial-grade design system with Tailwind CSS and Shadcn/UI**,
so that **dashboard displays are clearly readable from 3 feet away on tablets under factory floor lighting conditions**.

## Acceptance Criteria

1. **Tailwind CSS Configuration**: Tailwind CSS is installed and configured with a custom "Industrial Clarity" color palette featuring high-contrast colors optimized for factory floor visibility
2. **Shadcn/UI Integration**: Shadcn/UI is installed and initialized with core components (Button, Card, Badge, Alert) using the custom theme
3. **Color Semantics**: "Safety Red" (#DC2626 or similar) is reserved EXCLUSIVELY for safety incidents; other alert states use distinct colors (amber for warnings, blue for info)
4. **Typography Scale**: Font sizes are configured for "glanceability" - minimum 16px base, with heading sizes that remain readable from 3 feet away
5. **Component Variants**: Base components include variants for both "Retrospective" mode (cool, static colors) and "Live" mode (vibrant, high-contrast indicators)
6. **Dark/Light Modes**: Theme supports both dark and light modes optimized for different factory lighting conditions
7. **Accessibility Compliance**: All color combinations meet WCAG AA contrast ratios (minimum 4.5:1 for normal text, 3:1 for large text)

## Tasks / Subtasks

- [ ] Task 1: Install and Configure Tailwind CSS (AC: #1)
  - [ ] 1.1 Install Tailwind CSS and PostCSS dependencies in apps/web
  - [ ] 1.2 Create tailwind.config.ts with custom "Industrial Clarity" theme
  - [ ] 1.3 Configure content paths for App Router structure
  - [ ] 1.4 Add Tailwind directives to global CSS file

- [ ] Task 2: Define Industrial Clarity Color Palette (AC: #1, #3)
  - [ ] 2.1 Define semantic color tokens: safety-red, warning-amber, info-blue, success-green
  - [ ] 2.2 Define mode colors: retrospective-* (cool/muted), live-* (vibrant/saturated)
  - [ ] 2.3 Define neutral scale: industrial-gray-50 through industrial-gray-950
  - [ ] 2.4 Add CSS custom properties for runtime theme switching

- [ ] Task 3: Install and Configure Shadcn/UI (AC: #2)
  - [ ] 3.1 Initialize Shadcn/UI with `npx shadcn@latest init`
  - [ ] 3.2 Configure components.json for custom theme and App Router
  - [ ] 3.3 Add core components: Button, Card, Badge, Alert
  - [ ] 3.4 Verify components use Industrial Clarity theme variables

- [ ] Task 4: Configure Typography System (AC: #4)
  - [ ] 4.1 Define font-size scale in tailwind.config.ts (min 16px base)
  - [ ] 4.2 Configure Inter or similar sans-serif font via next/font
  - [ ] 4.3 Create typography utility classes for industrial contexts
  - [ ] 4.4 Add font-smoothing for screen readability

- [ ] Task 5: Create Component Variants (AC: #5)
  - [ ] 5.1 Extend Button with retrospective and live variants
  - [ ] 5.2 Extend Card with mode-specific border and shadow styles
  - [ ] 5.3 Extend Badge with status variants (safety, warning, info, success)
  - [ ] 5.4 Extend Alert with Safety-Red reserved styling

- [ ] Task 6: Implement Theme Mode Support (AC: #6)
  - [ ] 6.1 Install next-themes for dark/light mode switching
  - [ ] 6.2 Configure ThemeProvider in app layout
  - [ ] 6.3 Create dark mode color values optimized for low-light factory areas
  - [ ] 6.4 Create light mode color values optimized for bright factory floor

- [ ] Task 7: Verify Accessibility Compliance (AC: #7)
  - [ ] 7.1 Audit all color combinations with contrast checker
  - [ ] 7.2 Document contrast ratios in design system docs
  - [ ] 7.3 Fix any combinations below WCAG AA thresholds
  - [ ] 7.4 Add focus-visible styles for keyboard navigation

## Dev Notes

### Technical Stack Requirements

- **Framework**: Next.js 14+ with App Router (already scaffolded in apps/web)
- **Styling**: Tailwind CSS v3.4+ with PostCSS
- **Component Library**: Shadcn/UI (latest) - NOT a package, copies components into project
- **Theme Management**: next-themes v0.4+ for dark/light mode
- **Font Loading**: next/font for optimized font loading

### Architecture Patterns

Per Architecture document Section 4 (Repository Structure):
- Components go in `apps/web/src/components/`
- Shadcn/UI components install to `apps/web/src/components/ui/`
- Global styles in `apps/web/src/app/globals.css`
- Tailwind config at `apps/web/tailwind.config.ts`

### Industrial Clarity Color Palette Reference

Based on UX Design document "Design Principles":

```typescript
// Suggested color palette for tailwind.config.ts
colors: {
  // Safety - RESERVED for incidents only
  safety: {
    red: '#DC2626',      // Exclusive safety incident color
    'red-light': '#FEE2E2',
    'red-dark': '#991B1B',
  },
  // Status colors
  warning: {
    amber: '#F59E0B',
    'amber-light': '#FEF3C7',
    'amber-dark': '#B45309',
  },
  info: {
    blue: '#3B82F6',
    'blue-light': '#DBEAFE',
    'blue-dark': '#1D4ED8',
  },
  success: {
    green: '#10B981',
    'green-light': '#D1FAE5',
    'green-dark': '#047857',
  },
  // Mode colors - Retrospective (cool/static)
  retrospective: {
    primary: '#6B7280',   // Cool gray
    surface: '#F3F4F6',
    border: '#D1D5DB',
  },
  // Mode colors - Live (vibrant/pulsing)
  live: {
    primary: '#8B5CF6',   // Vibrant purple
    surface: '#F5F3FF',
    border: '#A78BFA',
    pulse: '#7C3AED',     // For animations
  },
  // Industrial neutrals
  industrial: {
    50: '#F9FAFB',
    100: '#F3F4F6',
    200: '#E5E7EB',
    300: '#D1D5DB',
    400: '#9CA3AF',
    500: '#6B7280',
    600: '#4B5563',
    700: '#374151',
    800: '#1F2937',
    900: '#111827',
    950: '#030712',
  },
}
```

### Typography Scale Reference

Based on UX "Glanceability" requirement (readable from 3 feet):

```typescript
fontSize: {
  'xs': ['0.875rem', { lineHeight: '1.25rem' }],     // 14px - minimum for labels
  'sm': ['1rem', { lineHeight: '1.5rem' }],          // 16px - body minimum
  'base': ['1.125rem', { lineHeight: '1.75rem' }],   // 18px - default body
  'lg': ['1.25rem', { lineHeight: '1.75rem' }],      // 20px
  'xl': ['1.5rem', { lineHeight: '2rem' }],          // 24px
  '2xl': ['1.875rem', { lineHeight: '2.25rem' }],    // 30px
  '3xl': ['2.25rem', { lineHeight: '2.5rem' }],      // 36px - section headers
  '4xl': ['3rem', { lineHeight: '1' }],              // 48px - page titles
  '5xl': ['3.75rem', { lineHeight: '1' }],           // 60px - dashboard metrics
}
```

### Component Implementation Guidelines

1. **Button Variants**: Include `default`, `destructive` (NOT safety-red), `outline`, `ghost`, `retrospective`, `live`
2. **Card Variants**: Include default styling plus `mode="retrospective"` and `mode="live"` props
3. **Badge Variants**: Include `safety` (red - reserved), `warning`, `info`, `success`, `default`
4. **Alert Variants**: The `destructive` variant should ONLY be used for safety incidents

### CRITICAL: Safety Red Usage

Per UX Design Section 2.4: "Safety Red is reserved EXCLUSIVELY for incidents"

- DO NOT use safety-red for error states, destructive buttons, or general warnings
- Use amber/warning colors for non-safety alerts
- Only components displaying actual safety incident data should use safety-red

### Testing Requirements

- Visual regression tests for component variants
- Contrast ratio validation in CI
- Responsive testing at tablet viewport (768px - 1024px primary)

### Project Structure Notes

Files to create/modify:
- `apps/web/tailwind.config.ts` - New Tailwind configuration
- `apps/web/postcss.config.mjs` - PostCSS configuration
- `apps/web/src/app/globals.css` - Global styles with Tailwind directives
- `apps/web/components.json` - Shadcn/UI configuration
- `apps/web/src/components/ui/button.tsx` - Customized Button
- `apps/web/src/components/ui/card.tsx` - Customized Card
- `apps/web/src/components/ui/badge.tsx` - Customized Badge
- `apps/web/src/components/ui/alert.tsx` - Customized Alert
- `apps/web/src/lib/utils.ts` - Utility functions (cn helper)
- `apps/web/src/app/layout.tsx` - Add ThemeProvider

### Dependencies to Install

```bash
# In apps/web directory
npm install tailwindcss postcss autoprefixer
npm install next-themes
npm install class-variance-authority clsx tailwind-merge
npm install @radix-ui/react-slot  # Required by Shadcn/UI
npm install lucide-react          # Icon library for Shadcn/UI
```

### References

- [Source: _bmad/bmm/data/architecture.md#3. Tech Stack] - Tailwind CSS + Shadcn/UI selection
- [Source: _bmad/bmm/data/architecture.md#4. Repository Structure] - File organization
- [Source: _bmad/bmm/data/ux-design.md#2. Overall UX Goals] - "Glanceability" and contrast requirements
- [Source: _bmad/bmm/data/ux-design.md#2.4 Design Principles] - "Industrial Clarity" and Safety Red rules
- [Source: _bmad/bmm/data/prd.md#3. User Interface Design Goals] - High-contrast factory floor visibility
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 1] - Foundation scope includes design system

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
