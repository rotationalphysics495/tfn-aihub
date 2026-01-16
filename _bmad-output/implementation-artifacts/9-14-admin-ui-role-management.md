# Story 9.14: Admin UI - Role Management

Status: ready-for-dev

## Story

As an **Admin**,
I want **to assign roles to users**,
So that **they have appropriate access and features**.

## Acceptance Criteria

1. **Given** an Admin navigates to user management
   **When** the page loads (FR47)
   **Then** they see a list of users with current roles
   **And** roles shown: Plant Manager, Supervisor, Admin

2. **Given** an Admin changes a user's role
   **When** the change is saved
   **Then** the `user_roles` table is updated
   **And** audit log entry is created (FR56)
   **And** user's access changes immediately

3. **Given** an Admin tries to remove the last Admin
   **When** the action is attempted
   **Then** the system prevents it
   **And** displays "Cannot remove last admin"

4. **Given** a new user is created (via Supabase Auth)
   **When** they first log in
   **Then** default role is "Supervisor"
   **And** Admin must explicitly promote to Plant Manager or Admin

## Tasks / Subtasks

- [ ] Task 1: Create user_roles database migration (AC: #1, #2, #4)
  - [ ] 1.1 Create `supabase/migrations/20260115_001_user_roles.sql`
  - [ ] 1.2 Define `user_roles` table with FK to auth.users
  - [ ] 1.3 Add CHECK constraint for valid roles
  - [ ] 1.4 Create RLS policies (admin-only write, authenticated read)
  - [ ] 1.5 Add trigger for default Supervisor role on new user

- [ ] Task 2: Create audit logging table (AC: #2)
  - [ ] 2.1 Create `supabase/migrations/20260115_007_audit_logs.sql`
  - [ ] 2.2 Define append-only `audit_logs` table structure
  - [ ] 2.3 Add indexes for timestamp, user_id, action_type queries
  - [ ] 2.4 Create RLS policies (admin read-only, no UPDATE/DELETE)

- [ ] Task 3: Create backend admin API endpoints (AC: #1, #2, #3)
  - [ ] 3.1 Create `apps/api/app/api/admin.py` router
  - [ ] 3.2 Implement `GET /api/v1/admin/users` - list users with roles
  - [ ] 3.3 Implement `GET /api/v1/admin/users/{id}` - get single user
  - [ ] 3.4 Implement `PUT /api/v1/admin/users/{id}/role` - update role
  - [ ] 3.5 Add last-admin protection check before role change
  - [ ] 3.6 Add audit logging service call on role change

- [ ] Task 4: Create backend models (AC: #1, #2)
  - [ ] 4.1 Create `apps/api/app/models/admin.py`
  - [ ] 4.2 Define `UserWithRole`, `RoleUpdateRequest`, `AuditLogEntry` Pydantic models

- [ ] Task 5: Create audit logging service (AC: #2)
  - [ ] 5.1 Create `apps/api/app/services/audit/logger.py`
  - [ ] 5.2 Implement `AuditLogger.log_action()` method
  - [ ] 5.3 Support action types: role_change, assignment_change

- [ ] Task 6: Create admin layout and route protection (AC: #1)
  - [ ] 6.1 Create `apps/web/src/app/(admin)/layout.tsx`
  - [ ] 6.2 Implement admin role check middleware
  - [ ] 6.3 Redirect non-admins to main app

- [ ] Task 7: Create user list page (AC: #1)
  - [ ] 7.1 Create `apps/web/src/app/(admin)/users/page.tsx`
  - [ ] 7.2 Fetch users with roles from API
  - [ ] 7.3 Display table with user email, current role, actions

- [ ] Task 8: Create user role management page (AC: #2, #3)
  - [ ] 8.1 Create `apps/web/src/app/(admin)/users/[id]/page.tsx`
  - [ ] 8.2 Display user details with role selection
  - [ ] 8.3 Implement role change with confirmation dialog
  - [ ] 8.4 Handle last-admin error gracefully

- [ ] Task 9: Create UserRoleTable component (AC: #1, #2, #3)
  - [ ] 9.1 Create `apps/web/src/components/admin/UserRoleTable.tsx`
  - [ ] 9.2 Render user list with role badges
  - [ ] 9.3 Add inline role change dropdown
  - [ ] 9.4 Display loading/error states

- [ ] Task 10: Write tests (All ACs)
  - [ ] 10.1 Unit tests for admin API endpoints
  - [ ] 10.2 Unit tests for audit logger service
  - [ ] 10.3 Integration test for role change flow
  - [ ] 10.4 Test last-admin protection logic

## Dev Notes

### Architecture Compliance

**Route Structure (from voice-briefing.md):**
```
apps/web/src/app/
└── (admin)/          # Admin route group
    ├── layout.tsx    # Admin-specific layout with nav
    ├── page.tsx      # Admin dashboard (optional)
    └── users/        # Role management
        ├── page.tsx         # User list with role badges
        └── [id]/page.tsx    # User role management
```

**Access Control Pattern:**
- Middleware checks `user_roles.role = 'admin'` for `/admin/*` routes
- Non-admins redirected to main app
- Admin actions logged to `audit_logs` table

### Database Schema

**user_roles table (from voice-briefing.md):**
```sql
CREATE TABLE user_roles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id),
    role TEXT CHECK (role IN ('plant_manager', 'supervisor', 'admin')),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

**Role hierarchy:**
- Admin > Plant Manager > Supervisor
- Protection: at least one Admin must exist
- Default: new users get Supervisor role

**audit_logs table:**
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ DEFAULT now(),
    admin_user_id UUID REFERENCES auth.users(id),
    action_type TEXT NOT NULL,  -- 'role_change', 'assignment_change', etc.
    target_user_id UUID,
    target_asset_id UUID,
    before_value JSONB,
    after_value JSONB,
    batch_id UUID  -- For linking bulk operations
);
-- Append-only: no UPDATE/DELETE allowed
-- Retention: 90 days minimum (NFR25)
```

### Existing Patterns to Follow

**Security Pattern (from apps/api/app/core/security.py):**
```python
# Use existing require_admin dependency
from app.core.security import require_admin, get_current_user

@router.get("/users")
async def list_users(
    admin: CurrentUser = Depends(require_admin),
    supabase: AsyncClient = Depends(get_supabase_client)
):
    ...
```

**Migration Pattern (from 20260106000000_plant_object_model.sql):**
- Include story reference in header comment
- Use `uuid_generate_v4()` for primary keys
- Add table and column COMMENT statements
- Create indexes for common query patterns
- Enable RLS with explicit policies
- Create auto-update trigger for `updated_at`

**API Router Pattern (from existing routers):**
```python
router = APIRouter()

@router.get("/endpoint", response_model=ResponseModel)
async def endpoint_name(
    current_user: CurrentUser = Depends(get_current_user),
):
    """Docstring with endpoint description."""
    ...
```

**Pydantic Model Pattern (from apps/api/app/models/):**
```python
class ModelName(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {...}}
    )
    field: Type
```

### Technical Requirements

**Backend (FastAPI):**
- Python 3.11+
- FastAPI 0.109+
- Supabase client for database operations
- All endpoints require admin role via `require_admin` dependency

**Frontend (Next.js 14):**
- App Router with route groups: `(admin)`
- Shadcn/UI components: Card, Badge, Button, Alert
- Note: Table component may need to be added from shadcn/ui

**Database (Supabase/PostgreSQL):**
- UUID primary keys
- Row Level Security (RLS) enabled
- Foreign key to `auth.users(id)`

### File Structure Requirements

**Files to Create:**
```
supabase/migrations/
├── 20260115_001_user_roles.sql       # User roles table
└── 20260115_007_audit_logs.sql       # Audit logging table

apps/api/app/
├── api/admin.py                      # Admin endpoints
├── models/admin.py                   # Admin Pydantic models
└── services/audit/
    ├── __init__.py
    └── logger.py                     # Audit logging service

apps/web/src/
├── app/(admin)/
│   ├── layout.tsx                    # Admin layout with role check
│   ├── users/
│   │   ├── page.tsx                  # User list page
│   │   └── [id]/page.tsx             # User detail/edit page
└── components/admin/
    └── UserRoleTable.tsx             # User table component
```

**Files to Modify:**
- `apps/api/app/main.py` - Register admin router
- `apps/api/app/models/__init__.py` - Export admin models

### Testing Requirements

**Unit Tests:**
- Test `GET /api/v1/admin/users` returns users with roles
- Test `PUT /api/v1/admin/users/{id}/role` updates role
- Test last-admin protection prevents removing only admin
- Test audit log is created on role change
- Test non-admin users get 403 on admin endpoints

**Integration Tests:**
- Test full role change flow from API to database
- Test audit log entry contains correct before/after values

### Previous Story Context

Story 9.13 (Admin UI - Asset Assignment) handles `supervisor_assignments` table and asset assignment grid. This story (9.14) focuses on the complementary `user_roles` table. Both stories share:
- Admin route group structure
- Audit logging pattern
- Admin-only access control

Coordinate with Story 9.13 on:
- Shared admin layout component
- Shared audit logger service
- Admin navigation between users and assignments pages

### API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/users` | List all users with roles |
| GET | `/api/v1/admin/users/{id}` | Get single user details |
| PUT | `/api/v1/admin/users/{id}/role` | Update user role |

### Security Considerations

1. **Last Admin Protection:** Query count of admins before allowing role change
2. **Audit Trail:** All role changes logged with admin ID, timestamp, before/after
3. **RLS Policies:** Only admins can write to user_roles; all authenticated can read own role
4. **Default Role:** Trigger ensures new users get Supervisor role automatically

### Project Structure Notes

- Alignment: Admin pages follow existing `(main)` route group pattern
- New `(admin)` route group provides clean separation without separate deployment
- Shadcn/UI components provide consistent design language
- Backend follows existing FastAPI router/model/service patterns

### References

- [Source: _bmad/bmm/data/architecture/voice-briefing.md#Admin-UI-Architecture]
- [Source: _bmad/bmm/data/architecture/voice-briefing.md#Role-Based-Access-Control]
- [Source: _bmad-output/planning-artifacts/epic-9.md#Story-9.14]
- [Source: apps/api/app/core/security.py#require_admin]
- [Source: supabase/migrations/20260106000000_plant_object_model.sql] (migration patterns)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
