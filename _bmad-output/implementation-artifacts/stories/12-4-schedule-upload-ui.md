# Story 12.4: Schedule Upload UI

Status: ready-for-dev

## Story

As a Plant Manager or Planner,
I want a page where I can drag-and-drop or browse for a schedule file and preview it before committing,
so that I can verify the data is correct before it enters the system.

## Acceptance Criteria

1. **Given** a user navigates to `/settings/schedule-upload`, **When** the page loads, **Then** a drag-and-drop zone is displayed with "Drop CSV or Excel file here" and a file picker button, **And** accepted formats are shown: .csv, .xlsx

2. **Given** a user drops or selects a valid file, **When** the file is uploaded to the preview endpoint, **Then** a preview table is shown with all parsed rows, **And** matched assets show with a green checkmark, **And** unmatched assets show with a red warning and suggested matches, **And** new products show with a blue "will be created" indicator, **And** validation errors are highlighted in red with specific messages

3. **Given** the preview has no errors, **When** the user clicks "Confirm Upload", **Then** the data is committed to the database, **And** a success toast shows with count of rows inserted, **And** the user is redirected to the morning report

4. **Given** the preview has errors, **When** the user views the preview, **Then** the "Confirm Upload" button is disabled, **And** error rows are clearly highlighted with fix suggestions

## Tasks / Subtasks

- [ ] Task 1: Create `useScheduleUpload` hook (AC: #1, #2, #3, #4)
  - [ ] 1.1 Create `apps/web/src/hooks/useScheduleUpload.ts`
  - [ ] 1.2 Implement `uploadForPreview(file: File)` that sends FormData to `POST /api/v1/schedule/upload`
  - [ ] 1.3 Implement `confirmUpload(data)` that calls `POST /api/v1/schedule/upload/confirm`
  - [ ] 1.4 Manage loading, error, preview data, and confirmation states
  - [ ] 1.5 Handle auth token from Supabase session (follow `useDailyActions` pattern)

- [ ] Task 2: Create `ScheduleUploadZone` component (AC: #1)
  - [ ] 2.1 Create `apps/web/src/components/schedule/ScheduleUploadZone.tsx`
  - [ ] 2.2 Implement drag-and-drop zone with `onDragOver`, `onDragLeave`, `onDrop` handlers
  - [ ] 2.3 Add hidden file input with `.csv,.xlsx` accept filter and a "Browse Files" button
  - [ ] 2.4 Show visual drag-active state (border highlight, background change)
  - [ ] 2.5 Display accepted formats: ".csv, .xlsx"
  - [ ] 2.6 Validate file type on drop/select before uploading
  - [ ] 2.7 Show file name and size after selection

- [ ] Task 3: Create `SchedulePreviewTable` component (AC: #2, #4)
  - [ ] 3.1 Create `apps/web/src/components/schedule/SchedulePreviewTable.tsx`
  - [ ] 3.2 Render parsed rows in a Shadcn/UI-styled table
  - [ ] 3.3 Show status indicators per row: green checkmark (matched asset), red warning (unmatched with suggestions), blue "will be created" (new product), red highlight (validation error)
  - [ ] 3.4 Display error messages inline per row
  - [ ] 3.5 Show summary stats: total rows, matched, errors, new products to create
  - [ ] 3.6 Support scrollable table for large uploads

- [ ] Task 4: Create Schedule Upload page (AC: #1, #2, #3, #4)
  - [ ] 4.1 Create `apps/web/src/app/(main)/settings/schedule-upload/page.tsx`
  - [ ] 4.2 Wire `ScheduleUploadZone` to trigger preview upload on file selection
  - [ ] 4.3 Show `SchedulePreviewTable` when preview data is available
  - [ ] 4.4 Add "Confirm Upload" button that is disabled when errors exist
  - [ ] 4.5 Show loading spinner during upload and confirmation
  - [ ] 4.6 Display success toast on confirmation and redirect to `/morning-report`
  - [ ] 4.7 Display error states with retry option

- [ ] Task 5: Add navigation link (AC: #1)
  - [ ] 5.1 Add "Schedule Upload" link in `AppSidebar` under the Settings nav group
  - [ ] 5.2 Use `Upload` icon from lucide-react
  - [ ] 5.3 Verify active state highlighting works for `/settings/schedule-upload`

## Dev Notes

### Architecture & Patterns

**Frontend stack (MUST follow):**
- Next.js 14+ App Router with `'use client'` directive for interactive pages
- TypeScript 5.x throughout
- Tailwind CSS 3.4+ for all styling (utility-first, no CSS modules)
- Shadcn/UI + Radix UI for accessible component primitives
- Vitest + Testing Library for component tests

**Page placement:**
- Route: `apps/web/src/app/(main)/settings/schedule-upload/page.tsx`
- The `(main)` route group provides authenticated layout with `OnboardingGate` + `AppShell` (header + sidebar)
- No need to add auth checks -- the `(main)/layout.tsx` server component handles authentication via `supabase.auth.getUser()` and redirects unauthenticated users

**Component organization:**
- Create a new `apps/web/src/components/schedule/` directory for all schedule components
- Follow existing barrel export pattern with `index.ts` if creating 3+ components
- Each component gets its own file (no multi-component files)

**Hook pattern (follow `useDailyActions` exactly):**
- File: `apps/web/src/hooks/useScheduleUpload.ts`
- Auth: Get session token from `createClient()` via `@/lib/supabase/client`
- API base: `process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'`
- Use `Authorization: Bearer ${session.access_token}` header
- Track `mountedRef` to prevent state updates after unmount
- Return `{ isLoading, error, previewData, confirmResult, uploadForPreview, confirmUpload }`

### API Dependency (Story 12.3)

This story depends on Story 12.3 (Schedule Upload API) which defines these endpoints:

**Preview endpoint:**
```
POST /api/v1/schedule/upload
Content-Type: multipart/form-data
Body: file (CSV or XLSX)

Response: {
  rows: [
    {
      row_number: number,
      date: string,
      shift: string,
      asset_name: string,
      product_name: string,
      scheduled_quantity: number,
      asset_match: { matched: boolean, asset_id?: string, suggestions?: string[] },
      product_match: { matched: boolean, product_id?: string, is_new: boolean },
      errors: string[]
    }
  ],
  summary: {
    total_rows: number,
    matched_assets: number,
    unmatched_assets: number,
    new_products: number,
    error_count: number
  }
}
```

**Confirm endpoint:**
```
POST /api/v1/schedule/upload/confirm
Content-Type: application/json
Body: { rows: <parsed preview data> }

Response: {
  success: boolean,
  rows_inserted: number,
  rows_updated: number,
  products_created: number
}
```

If the API is not yet implemented, create the hook with the expected contract above and stub the endpoints. The UI must match this contract.

### Navigation Integration

Add to `AppSidebar` in the Settings nav group:
```tsx
// In apps/web/src/components/navigation/AppSidebar.tsx
// Add to the 'Settings' navGroup items array:
{ href: '/settings/schedule-upload', label: 'Schedule Upload', icon: <Upload className="w-5 h-5" /> }
```
Import `Upload` from `lucide-react` (already used in the project).

### UI/UX Requirements

**Drag-and-drop zone:**
- Dashed border, centered content
- Visual state change on drag hover (e.g., border-primary, bg-primary/5)
- Show file icon, "Drop CSV or Excel file here" text, and "Browse Files" button
- After file selected: show file name, size, and "Remove" option

**Preview table columns:**
| Column | Content |
|--------|---------|
| Status | Icon: checkmark/warning/error |
| Row # | Row number from file |
| Date | Scheduled date |
| Shift | Shift identifier |
| Asset | Asset name + match status |
| Product | Product name + new indicator |
| Quantity | Scheduled quantity |
| Issues | Error messages if any |

**Color coding (follow existing Tailwind patterns):**
- Green checkmark: `text-green-500` -- matched asset
- Red warning: `text-destructive` -- unmatched asset or validation error
- Blue indicator: `text-blue-500` -- new product to be created
- Error row background: `bg-destructive/5`

**Confirm button:**
- Disabled state when `error_count > 0` in preview summary
- Loading spinner during confirmation (follow existing pattern from PreferencesPage save button)

**Success flow:**
- Show toast notification with insert count
- Redirect to `/morning-report` via `router.push('/morning-report')` using `useRouter` from `next/navigation`

### Existing UI Components to Reuse

- `Card`, `CardContent`, `CardHeader`, `CardTitle`, `CardDescription` from `@/components/ui/card`
- `Button` from `@/components/ui/button`
- `Badge` from `@/components/ui/badge`
- `Alert` from `@/components/ui/alert` -- for error/success messages
- Do NOT install new UI libraries -- use Tailwind + existing Shadcn/UI components
- For the table: build a simple HTML table with Tailwind classes (Shadcn `Table` component is NOT installed in this project; do NOT try to import it)

### File Upload Implementation

Use native browser `FormData` API:
```typescript
const formData = new FormData()
formData.append('file', file)

const response = await fetch(`${apiUrl}/api/v1/schedule/upload`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${session.access_token}`,
    // Do NOT set Content-Type -- browser sets it with boundary for multipart
  },
  body: formData,
})
```

### Testing Requirements

- Component tests in `apps/web/src/components/schedule/__tests__/`
- Test `ScheduleUploadZone`: file drop handler, file type validation, drag state
- Test `SchedulePreviewTable`: rendering matched/unmatched/error rows, summary stats
- Test `useScheduleUpload`: mock fetch, verify state transitions
- Use Vitest + Testing Library (follow patterns in `apps/web/src/components/handoff/__tests__/`)
- Run tests: `cd apps/web && npm run test`

### Project Structure Notes

- Route follows `(main)/settings/` pattern, consistent with existing `(main)/settings/preferences/page.tsx`
- Components in `components/schedule/` follows domain-based organization pattern (`components/handoff/`, `components/admin/`, etc.)
- Hook in `hooks/useScheduleUpload.ts` follows flat hooks directory pattern

### References

- [Source: _bmad-output/planning-artifacts/epic-12.md#Story 12.4: Schedule Upload UI]
- [Source: _bmad-output/planning-artifacts/epic-12.md#Story 12.3: Schedule Upload API]
- [Source: docs/architecture-web.md#Directory Structure]
- [Source: docs/architecture-web.md#Component Architecture]
- [Source: docs/architecture-api.md#API Endpoints]
- [Source: apps/web/src/components/navigation/AppSidebar.tsx#Settings nav group]
- [Source: apps/web/src/hooks/useDailyActions.ts#API call pattern]
- [Source: apps/web/src/app/(main)/settings/preferences/page.tsx#Page pattern]
- [Source: apps/web/src/app/(main)/layout.tsx#Auth and OnboardingGate]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
