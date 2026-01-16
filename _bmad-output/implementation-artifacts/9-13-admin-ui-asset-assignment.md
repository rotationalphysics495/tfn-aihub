# Story 9.13: Admin UI - Asset Assignment

Status: ready-for-dev

## Story

As an **Admin**,
I want **to assign supervisors to specific assets and areas**,
so that **they receive appropriately scoped briefings and handoffs**.

## Acceptance Criteria

1. **Given** an Admin navigates to the assignment page, **When** the page loads (FR46), **Then** they see a grid of:
   - Columns: Areas and Assets
   - Rows: Supervisors
   - Cells: Checkboxes for assignments

2. **Given** an Admin checks/unchecks an assignment, **When** the change is made, **Then** preview shows impact: "User will see X assets across Y areas" (FR48), **And** change is not saved until confirmed

3. **Given** an Admin saves assignments, **When** confirmed, **Then** changes are written to `supervisor_assignments` table, **And** audit log entry is created (FR50, FR56), **And** affected supervisors see updated scope immediately

4. **Given** an Admin needs temporary coverage, **When** they make a temporary assignment (FR49), **Then** an expiration date can be set, **And** assignment auto-reverts after expiration

## Tasks / Subtasks

- [ ] Task 1: Create Database Migration for supervisor_assignments (AC: 1, 3, 4)
  - [ ] 1.1: Create `supervisor_assignments` table with `user_id`, `asset_id`, `assigned_by`, `assigned_at`, `expires_at` columns
  - [ ] 1.2: Create unique constraint on (user_id, asset_id)
  - [ ] 1.3: Create foreign key to `assets` table
  - [ ] 1.4: Create foreign key to `auth.users` for both `user_id` and `assigned_by`
  - [ ] 1.5: Add RLS policies for admin-only modification, authenticated read
  - [ ] 1.6: Create indexes for efficient querying by user_id and asset_id

- [ ] Task 2: Create Backend Admin API Endpoints (AC: 1, 2, 3, 4)
  - [ ] 2.1: Create `apps/api/app/api/admin.py` with FastAPI router
  - [ ] 2.2: Implement `GET /api/v1/admin/assignments` - List all assignments
  - [ ] 2.3: Implement `GET /api/v1/admin/assignments/user/{user_id}` - Get user's assignments
  - [ ] 2.4: Implement `POST /api/v1/admin/assignments/preview` - Preview impact of changes
  - [ ] 2.5: Implement `POST /api/v1/admin/assignments/batch` - Save batch assignment changes
  - [ ] 2.6: Implement `DELETE /api/v1/admin/assignments/{id}` - Remove single assignment
  - [ ] 2.7: Add `require_admin` dependency to all endpoints
  - [ ] 2.8: Integrate audit logging for all write operations

- [ ] Task 3: Create Pydantic Models for Admin Operations (AC: 1, 2, 3, 4)
  - [ ] 3.1: Create `apps/api/app/models/admin.py` with assignment models
  - [ ] 3.2: Define `SupervisorAssignment` model
  - [ ] 3.3: Define `AssignmentPreview` response model with asset/area counts
  - [ ] 3.4: Define `BatchAssignmentRequest` for bulk operations
  - [ ] 3.5: Define `AuditLogEntry` model

- [ ] Task 4: Create Audit Logging Service (AC: 3, 4)
  - [ ] 4.1: Create `apps/api/app/services/audit/logger.py`
  - [ ] 4.2: Implement `log_assignment_change()` function
  - [ ] 4.3: Capture before/after values for updates
  - [ ] 4.4: Include batch_id for bulk operations
  - [ ] 4.5: Store admin user_id, timestamp, action type

- [ ] Task 5: Create Admin Layout and Navigation (AC: 1)
  - [ ] 5.1: Create `apps/web/src/app/(admin)/layout.tsx` with admin sidebar
  - [ ] 5.2: Create `apps/web/src/components/admin/AdminNav.tsx` navigation component
  - [ ] 5.3: Add middleware for admin role check on `/admin/*` routes
  - [ ] 5.4: Add redirect to main app for non-admins

- [ ] Task 6: Create Asset Assignment Grid Component (AC: 1, 2)
  - [ ] 6.1: Create `apps/web/src/components/admin/AssetAssignmentGrid.tsx`
  - [ ] 6.2: Implement virtualized grid for performance with many assets
  - [ ] 6.3: Group assets by area as columns
  - [ ] 6.4: Display supervisors as rows
  - [ ] 6.5: Render checkboxes for each user-asset combination
  - [ ] 6.6: Track pending changes in local state

- [ ] Task 7: Create Assignment Preview Component (AC: 2)
  - [ ] 7.1: Create preview panel showing impact of pending changes
  - [ ] 7.2: Display "User will see X assets across Y areas" summary
  - [ ] 7.3: Show added/removed assignments in different colors
  - [ ] 7.4: Add confirm/cancel buttons

- [ ] Task 8: Create Temporary Assignment UI (AC: 4)
  - [ ] 8.1: Add expiration date picker to assignment dialog
  - [ ] 8.2: Display visual indicator for temporary assignments in grid
  - [ ] 8.3: Show countdown or expiration date on hover
  - [ ] 8.4: Implement auto-filter to exclude expired assignments

- [ ] Task 9: Create Assignment Page (AC: 1, 2, 3, 4)
  - [ ] 9.1: Create `apps/web/src/app/(admin)/assignments/page.tsx`
  - [ ] 9.2: Fetch supervisors list from API
  - [ ] 9.3: Fetch assets grouped by area from API
  - [ ] 9.4: Fetch current assignments from API
  - [ ] 9.5: Wire up save functionality with confirmation
  - [ ] 9.6: Add loading and error states

- [ ] Task 10: Write Tests (AC: 1, 2, 3, 4)
  - [ ] 10.1: Create `apps/api/app/tests/api/test_admin_endpoints.py`
  - [ ] 10.2: Test assignment CRUD operations
  - [ ] 10.3: Test preview calculation logic
  - [ ] 10.4: Test admin-only access control
  - [ ] 10.5: Test audit logging integration
  - [ ] 10.6: Create `apps/web/src/components/admin/__tests__/AssetAssignmentGrid.test.tsx`
  - [ ] 10.7: Test grid rendering and interaction
  - [ ] 10.8: Test preview panel updates

## Dev Notes

### Architecture Requirements

This story implements the Admin Asset Assignment UI as part of Epic 9 (Shift Handoff & EOD Summary). The assignment grid enables admins to manage which supervisors see which assets during briefings and handoffs.

**Key Architecture Decisions:**
- Admin UI uses separate route group (`/admin/*`) per [architecture/voice-briefing.md]
- Hybrid RBAC approach: RLS for sensitive data, service-level filtering for aggregations
- Grid virtualization required for performance with potentially many assets
- Audit logging is mandatory for all assignment changes (FR50, FR56)

### Technical Stack

| Component | Technology | Notes |
|-----------|------------|-------|
| Backend Framework | FastAPI 0.109+ | Use existing patterns from `apps/api/app/api/` |
| Database | Supabase PostgreSQL | New `supervisor_assignments` table |
| Frontend Framework | Next.js 14 (App Router) | New `(admin)` route group |
| UI Components | Shadcn/UI + Tailwind | Use existing component library |
| Grid Virtualization | `@tanstack/react-virtual` | For large dataset performance |

### Database Schema

```sql
-- supervisor_assignments table (from architecture/voice-briefing.md)
CREATE TABLE supervisor_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    asset_id UUID REFERENCES assets(id) NOT NULL,
    assigned_by UUID REFERENCES auth.users(id) NOT NULL,
    assigned_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ NULL,  -- For temporary assignments (FR49)
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, asset_id)
);

-- RLS Policies
-- Admins: full access
-- Authenticated users: read own assignments
CREATE POLICY "Admins can manage all assignments"
    ON supervisor_assignments FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM user_roles
            WHERE user_roles.user_id = auth.uid()
            AND user_roles.role = 'admin'
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM user_roles
            WHERE user_roles.user_id = auth.uid()
            AND user_roles.role = 'admin'
        )
    );

CREATE POLICY "Users can read own assignments"
    ON supervisor_assignments FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/assignments` | List all assignments with user/asset details |
| GET | `/api/v1/admin/assignments/user/{user_id}` | Get specific user's assignments |
| POST | `/api/v1/admin/assignments/preview` | Calculate impact preview for pending changes |
| POST | `/api/v1/admin/assignments/batch` | Save batch of assignment changes atomically |
| DELETE | `/api/v1/admin/assignments/{id}` | Remove single assignment |

### Frontend File Structure

```
apps/web/src/app/
└── (admin)/                         # NEW: Admin route group
    ├── layout.tsx                   # Admin layout with sidebar
    └── assignments/
        └── page.tsx                 # Asset assignment grid page

apps/web/src/components/admin/       # NEW: Admin components
├── AdminNav.tsx                     # Admin navigation sidebar
├── AssetAssignmentGrid.tsx          # Virtualized assignment grid
├── AssignmentPreview.tsx            # Preview impact panel
├── TemporaryAssignmentDialog.tsx    # Expiration date picker
└── __tests__/
    └── AssetAssignmentGrid.test.tsx
```

### Backend File Structure

```
apps/api/app/
├── api/
│   └── admin.py                     # NEW: Admin endpoints
├── models/
│   └── admin.py                     # NEW: Admin models
└── services/
    └── audit/
        └── logger.py                # NEW: Audit logging service
```

### Existing Code Patterns to Follow

**Backend API Pattern:**
```python
# From apps/api/app/api/auth.py
from fastapi import APIRouter, Depends
from app.core.security import get_current_user, require_admin
from app.models.admin import SupervisorAssignment

router = APIRouter()

@router.get("/assignments")
async def list_assignments(
    current_user: CurrentUser = Depends(require_admin),
) -> List[SupervisorAssignment]:
    # Implementation
```

**Frontend Component Pattern:**
```typescript
// From apps/web/src/components/production/ThroughputCard.tsx
interface AssetAssignmentGridProps {
  supervisors: Supervisor[];
  assets: Asset[];
  assignments: Assignment[];
  onChangesPending: (changes: AssignmentChange[]) => void;
}

export function AssetAssignmentGrid({ ... }: AssetAssignmentGridProps) {
  // Implementation
}
```

### Security Considerations

1. **Admin Role Verification**: Use existing `require_admin` dependency from `app/core/security.py`
2. **RLS Policies**: Admins can modify, authenticated users can read own assignments
3. **Audit Trail**: Every change must be logged with admin user ID, timestamp, before/after values
4. **Input Validation**: Validate user_id and asset_id exist before creating assignments

### Performance Considerations

1. **Grid Virtualization**: Use `@tanstack/react-virtual` for grids with 50+ assets
2. **Batch Operations**: Save all changes in single transaction
3. **Optimistic Updates**: Update UI immediately, rollback on error
4. **Efficient Queries**: Index on `user_id` and `asset_id` for fast lookups

### Dependencies

**Story Dependencies:**
- Depends on existing `assets` table from Story 1.3
- Depends on existing auth infrastructure
- Story 9.14 (Role Management) may run in parallel

**Technical Dependencies:**
- `@tanstack/react-virtual` for grid virtualization (install if not present)

### Project Structure Notes

- Alignment with unified project structure: New `(admin)` route group follows Next.js conventions
- Admin components in dedicated `components/admin/` folder per architecture pattern
- API endpoint under `/api/v1/admin/*` namespace

### References

- [Source: _bmad/bmm/data/architecture/voice-briefing.md#Admin UI Architecture]
- [Source: _bmad/bmm/data/architecture/voice-briefing.md#Role-Based Access Control]
- [Source: _bmad/bmm/data/prd/prd-functional-requirements.md#FR46-FR50]
- [Source: _bmad-output/planning-artifacts/epic-9.md#Story 9.13]
- [Source: supabase/migrations/20260106000000_plant_object_model.sql - assets table structure]
- [Source: apps/api/app/core/security.py - require_admin dependency]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

