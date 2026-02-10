# Story 9.15: Admin Audit Logging

Status: done

## Story

As an **Admin**,
I want **all configuration changes logged**,
So that **we have accountability and can troubleshoot issues**.

## Acceptance Criteria

1. **Given** any admin action is taken
   **When** the action completes
   **Then** an audit log entry is created with:
   - Timestamp
   - Admin user ID
   - Action type (create, update, delete)
   - Target (user_id, asset_id, etc.)
   - Before/after values (for updates)

2. **Given** an Admin views audit logs
   **When** the log page loads
   **Then** entries are displayed in reverse chronological order
   **And** filters available: date range, action type, target user

3. **Given** audit log entries exist
   **When** 90 days pass (NFR25)
   **Then** entries remain available
   **And** entries are tamper-evident (append-only)

4. **Given** bulk actions are performed
   **When** logged
   **Then** each individual change has its own log entry
   **And** entries are linked by a batch ID

## Tasks / Subtasks

- [x] Task 1: Create audit_logs database migration (AC: #1, #3, #4)
  - [x] 1.1 Create `supabase/migrations/20260120_001_audit_logs.sql`
  - [x] 1.2 Define `audit_logs` table with timestamp, admin_user_id, action_type, target columns
  - [x] 1.3 Add JSONB columns for before_value and after_value
  - [x] 1.4 Add batch_id UUID column for linking bulk operations
  - [x] 1.5 Create indexes on timestamp, admin_user_id, action_type for efficient queries
  - [x] 1.6 Create composite index on (timestamp DESC, action_type) for filtered queries
  - [x] 1.7 Create append-only RLS policy (INSERT only for system, SELECT for admin)
  - [x] 1.8 Add CHECK constraint preventing UPDATE and DELETE operations (via triggers)
  - [x] 1.9 Add retention policy comment (90 days minimum per NFR25)

- [x] Task 2: Create Audit Logging Service (AC: #1, #4)
  - [x] 2.1 Update `apps/api/app/services/audit/__init__.py`
  - [x] 2.2 Update `apps/api/app/services/audit/logger.py`
  - [x] 2.3 Implement `AuditLogger` class with sync and async methods
  - [x] 2.4 Implement `log_action()` method with admin_user_id, action_type, target, before/after values
  - [x] 2.5 Implement `log_batch_start()` method that generates batch_id for linking
  - [x] 2.6 Add support for action_type enum: AuditLogActionType
  - [x] 2.7 Create helper methods: `log_role_change()`, `log_assignment_change()`
  - [x] 2.8 Add validation to ensure required fields are present

- [x] Task 3: Create Audit Log API Endpoints (AC: #2, #3)
  - [x] 3.1 Add audit log routes to `apps/api/app/api/admin.py`
  - [x] 3.2 Implement `GET /api/v1/admin/audit-logs` - paginated list
  - [x] 3.3 Add query parameters: page, page_size, start_date, end_date, action_type, target_user_id
  - [x] 3.4 Implement `GET /api/v1/admin/audit-logs/{id}` - single entry details
  - [x] 3.5 Add `require_admin` dependency to all audit endpoints
  - [x] 3.6 Implement response with total count for pagination

- [x] Task 4: Create Pydantic Models for Audit Logging (AC: #1, #2, #4)
  - [x] 4.1 Update `apps/api/app/models/admin.py` with audit models
  - [x] 4.2 Define `AuditLogEntryResponse` model with all fields
  - [x] 4.3 Define `AuditLogActionType` enum (role_change, assignment_create, etc.)
  - [x] 4.4 Define `AuditLogListResponseV2` with entries and pagination metadata
  - [x] 4.5 Define `AuditLogFilters` model for query parameters

- [x] Task 5: Integrate Audit Logging into Admin Endpoints (AC: #1, #4)
  - [x] 5.1 Import AuditLogger into admin.py (already integrated from Stories 9.13/9.14)
  - [x] 5.2 Audit logging for role changes (from Story 9.14)
  - [x] 5.3 Audit logging for batch assignments (from Story 9.13)
  - [x] 5.4 Audit logging for individual assignments (from Story 9.13)
  - [x] 5.5 Batch operations use linked batch_id

- [x] Task 6: Create Audit Log Viewer Page (AC: #2)
  - [x] 6.1 Create `apps/web/src/app/(admin)/audit/page.tsx`
  - [x] 6.2 Implement paginated table display
  - [x] 6.3 Display columns: timestamp, admin user, action type, target, summary
  - [x] 6.4 Add expandable row detail for before/after values
  - [x] 6.5 Add loading and error states

- [x] Task 7: Create Audit Log Filter Components (AC: #2)
  - [x] 7.1 Create `apps/web/src/components/admin/AuditLogFilters.tsx`
  - [x] 7.2 Implement date range picker (start date, end date)
  - [x] 7.3 Implement action type dropdown filter
  - [x] 7.4 Implement target user search/filter
  - [x] 7.5 Add "Clear Filters" button
  - [x] 7.6 Wire up filter state to URL query parameters for shareable links

- [x] Task 8: Create Audit Log Table Component (AC: #2, #3, #4)
  - [x] 8.1 Create `apps/web/src/components/admin/AuditLogTable.tsx`
  - [x] 8.2 Render entries in reverse chronological order
  - [x] 8.3 Display batch_id indicator for linked entries
  - [x] 8.4 Add expandable JSON diff view for before/after
  - [x] 8.5 Implement pagination controls (in page.tsx)
  - [x] 8.6 Add "Next/Previous" page navigation

- [x] Task 9: Add Audit Link to Admin Navigation (AC: #2)
  - [x] 9.1 AdminNav already includes "Audit Log" item (from Story 9.14)
  - [x] 9.2 "Audit Logs" navigation item present
  - [x] 9.3 Shield icon for audit logs menu item

- [x] Task 10: Write Tests (All ACs)
  - [x] 10.1 Create `apps/api/app/tests/services/test_audit_logger.py`
  - [x] 10.2 Test `log_action()` creates correct entry
  - [x] 10.3 Test `log_batch_start()` links entries with batch_id
  - [x] 10.4 Test before/after value capture accuracy
  - [x] 10.5 Add audit log tests to `apps/api/app/tests/api/test_admin_endpoints.py`
  - [x] 10.6 Test audit log list endpoint with pagination
  - [x] 10.7 Test audit log filters work correctly
  - [x] 10.8 Test admin-only access control
  - [x] 10.9 Create `apps/web/src/components/admin/__tests__/AuditLogTable.test.tsx`
  - [x] 10.10 Test table rendering and expansion

## Dev Notes

### Architecture Compliance

**Audit Logging Requirements (from PRD/Architecture):**
- FR50: System can maintain audit log of all assignment changes
- FR55: System can maintain audit trail of shift handoffs with acknowledgments
- FR56: System can log all admin configuration changes
- NFR25: Audit logs are tamper-evident and retained for 90 days minimum

**Key Design Decisions:**
- Append-only table design (no UPDATE/DELETE operations)
- JSONB for flexible before/after value storage
- batch_id for linking bulk operations
- Indexed for efficient queries on timestamp, user, and action type

### Database Schema

**audit_logs table (per architecture/voice-briefing.md and NFR25):**
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ DEFAULT now() NOT NULL,
    admin_user_id UUID REFERENCES auth.users(id) NOT NULL,
    action_type TEXT NOT NULL,
    target_user_id UUID REFERENCES auth.users(id),
    target_asset_id UUID REFERENCES assets(id),
    target_type TEXT,  -- 'user', 'assignment', 'role', etc.
    target_id UUID,    -- Generic target reference
    before_value JSONB,
    after_value JSONB,
    batch_id UUID,     -- Links bulk operations
    metadata JSONB,    -- Additional context
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- Indexes for efficient queries
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_admin_user_id ON audit_logs(admin_user_id);
CREATE INDEX idx_audit_logs_action_type ON audit_logs(action_type);
CREATE INDEX idx_audit_logs_target_user_id ON audit_logs(target_user_id);
CREATE INDEX idx_audit_logs_batch_id ON audit_logs(batch_id);
CREATE INDEX idx_audit_logs_timestamp_action ON audit_logs(timestamp DESC, action_type);

-- Append-only: No UPDATE or DELETE allowed
-- RLS: Admin read-only, system INSERT only
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Admins can read audit logs"
    ON audit_logs FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM user_roles
            WHERE user_roles.user_id = auth.uid()
            AND user_roles.role = 'admin'
        )
    );

-- Service role can INSERT (for backend audit logging)
-- No UPDATE/DELETE policies = append-only behavior

COMMENT ON TABLE audit_logs IS 'Audit trail for admin actions. Append-only, 90-day retention (NFR25).';
```

### Action Types Enum

```python
class AuditLogActionType(str, Enum):
    ROLE_CHANGE = "role_change"
    ASSIGNMENT_CREATE = "assignment_create"
    ASSIGNMENT_UPDATE = "assignment_update"
    ASSIGNMENT_DELETE = "assignment_delete"
    BATCH_ASSIGNMENT = "batch_assignment"
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    PREFERENCE_UPDATE = "preference_update"
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/audit-logs` | List audit entries with pagination and filters |
| GET | `/api/v1/admin/audit-logs/{id}` | Get single audit entry details |

**Query Parameters for GET /audit-logs:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 50, max: 100)
- `start_date`: Filter entries after this date (ISO 8601)
- `end_date`: Filter entries before this date (ISO 8601)
- `action_type`: Filter by action type
- `target_user_id`: Filter by target user
- `admin_user_id`: Filter by admin who performed action

### Frontend File Structure

```
apps/web/src/
├── app/(admin)/
│   └── audit/
│       └── page.tsx              # Audit log viewer page
└── components/admin/
    ├── AuditLogTable.tsx         # Table component with expansion (includes row/detail logic)
    ├── AuditLogFilters.tsx       # Filter controls
    └── __tests__/
        └── AuditLogTable.test.tsx
```

Note: AuditLogRow.tsx and AuditLogDetail.tsx planned in Dev Notes were consolidated into AuditLogTable.tsx for simplicity.

### Backend File Structure

```
apps/api/app/
├── api/
│   └── admin.py                  # ADD: audit log endpoints
├── models/
│   └── admin.py                  # ADD: audit log models
└── services/
    └── audit/
        ├── __init__.py           # UPDATE: exports
        └── logger.py             # UPDATE: AuditLogger class

supabase/migrations/
└── 20260120_001_audit_logs.sql   # NEW: audit_logs table
```

### Existing Patterns to Follow

**Audit Logger Service Pattern:**
```python
# apps/api/app/services/audit/logger.py
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from supabase import AsyncClient

class AuditLogger:
    def __init__(self, supabase: AsyncClient):
        self.supabase = supabase

    async def log_action(
        self,
        admin_user_id: UUID,
        action_type: str,
        target_type: str,
        target_id: Optional[UUID] = None,
        target_user_id: Optional[UUID] = None,
        target_asset_id: Optional[UUID] = None,
        before_value: Optional[dict] = None,
        after_value: Optional[dict] = None,
        batch_id: Optional[UUID] = None,
        metadata: Optional[dict] = None,
    ) -> UUID:
        """Log a single audit entry. Returns the entry ID."""
        entry = {
            "admin_user_id": str(admin_user_id),
            "action_type": action_type,
            "target_type": target_type,
            "target_id": str(target_id) if target_id else None,
            "target_user_id": str(target_user_id) if target_user_id else None,
            "target_asset_id": str(target_asset_id) if target_asset_id else None,
            "before_value": before_value,
            "after_value": after_value,
            "batch_id": str(batch_id) if batch_id else None,
            "metadata": metadata,
        }
        result = await self.supabase.table("audit_logs").insert(entry).execute()
        return UUID(result.data[0]["id"])

    async def log_role_change(
        self,
        admin_user_id: UUID,
        target_user_id: UUID,
        before_role: str,
        after_role: str,
    ) -> UUID:
        """Convenience method for role change logging."""
        return await self.log_action(
            admin_user_id=admin_user_id,
            action_type="role_change",
            target_type="user",
            target_user_id=target_user_id,
            before_value={"role": before_role},
            after_value={"role": after_role},
        )

    async def log_batch_start(self) -> UUID:
        """Generate a batch_id for linking multiple actions."""
        return uuid4()
```

**API Endpoint Pattern:**
```python
# In apps/api/app/api/admin.py
from app.services.audit.logger import AuditLogger

@router.get("/audit-logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    action_type: Optional[str] = None,
    target_user_id: Optional[UUID] = None,
    current_user: CurrentUser = Depends(require_admin),
    supabase: AsyncClient = Depends(get_supabase_client),
):
    """List audit log entries with pagination and optional filters."""
    query = supabase.table("audit_logs").select("*", count="exact")

    if start_date:
        query = query.gte("timestamp", start_date.isoformat())
    if end_date:
        query = query.lte("timestamp", end_date.isoformat())
    if action_type:
        query = query.eq("action_type", action_type)
    if target_user_id:
        query = query.eq("target_user_id", str(target_user_id))

    offset = (page - 1) * page_size
    result = await query.order("timestamp", desc=True).range(offset, offset + page_size - 1).execute()

    return AuditLogListResponse(
        entries=[AuditLogEntry(**entry) for entry in result.data],
        total=result.count,
        page=page,
        page_size=page_size,
    )
```

**Frontend Table Pattern:**
```typescript
// apps/web/src/components/admin/AuditLogTable.tsx
"use client";

import { useState } from "react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ChevronDown, ChevronRight } from "lucide-react";

interface AuditLogEntry {
  id: string;
  timestamp: string;
  admin_user_id: string;
  action_type: string;
  target_type: string;
  target_user_id?: string;
  before_value?: Record<string, unknown>;
  after_value?: Record<string, unknown>;
  batch_id?: string;
}

interface AuditLogTableProps {
  entries: AuditLogEntry[];
  isLoading?: boolean;
}

export function AuditLogTable({ entries, isLoading }: AuditLogTableProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // ... implementation
}
```

### Security Considerations

1. **Append-Only Design:** No UPDATE/DELETE policies on audit_logs table ensures tamper-evidence
2. **Admin-Only Access:** Only users with admin role can view audit logs via RLS
3. **Service Role Insert:** Backend uses service role for INSERT operations (not user context)
4. **Before/After Capture:** Always capture both states for complete audit trail
5. **Batch Linking:** Use batch_id to trace bulk operations back to single action

### Performance Considerations

1. **Index Strategy:** Indexes on timestamp, admin_user_id, action_type for common queries
2. **Pagination:** Default 50 entries per page, max 100
3. **JSONB Indexing:** Consider GIN index on before_value/after_value if needed for search
4. **Retention Policy:** Implement cleanup job for entries > 90 days (future story)

### Dependencies

**Story Dependencies:**
- Story 9.13 (Admin UI - Asset Assignment) - uses audit logger for assignment changes
- Story 9.14 (Admin UI - Role Management) - uses audit logger for role changes
- These stories may have already created partial audit infrastructure

**Technical Dependencies:**
- `user_roles` table from Story 9.14
- Admin route group structure from Story 9.13/9.14
- `require_admin` dependency from existing security module

### Integration Points

**With Story 9.13 (Asset Assignment):**
- Use AuditLogger.log_action() for assignment changes
- Use batch_id for batch assignment operations

**With Story 9.14 (Role Management):**
- Use AuditLogger.log_role_change() convenience method
- Capture before/after role values

**Future Stories:**
- Story 9.7 (Acknowledgment Flow) - logs handoff acknowledgments
- Any future admin action should integrate with AuditLogger

### Testing Requirements

**Unit Tests:**
- AuditLogger.log_action() creates correct database entry
- AuditLogger.log_role_change() captures before/after correctly
- Batch operations share the same batch_id
- Required fields validation works

**Integration Tests:**
- Audit log endpoint returns entries in reverse chronological order
- Filters work correctly (date range, action type, user)
- Pagination works correctly
- Admin-only access is enforced

**E2E Tests:**
- Role change action creates audit entry
- Assignment change action creates audit entry
- Audit log page displays entries correctly
- Filters update the displayed entries

### Project Structure Notes

- Alignment: Audit log page under existing `(admin)` route group
- AuditLogger service is reusable across all admin operations
- Table component follows existing Shadcn/UI patterns
- Database migration follows existing naming convention (20260115_007_audit_logs.sql)

### References

- [Source: _bmad/bmm/data/prd/prd-functional-requirements.md#FR50 - Audit log of assignment changes]
- [Source: _bmad/bmm/data/prd/prd-functional-requirements.md#FR55 - Audit trail of shift handoffs]
- [Source: _bmad/bmm/data/prd/prd-functional-requirements.md#FR56 - Log admin configuration changes]
- [Source: _bmad/bmm/data/prd/prd-non-functional-requirements.md#NFR25 - 90-day retention, tamper-evident]
- [Source: _bmad/bmm/data/architecture/voice-briefing.md#Admin-UI-Architecture]
- [Source: _bmad/bmm/data/architecture/voice-briefing.md#Role-Based-Access-Control]
- [Source: _bmad-output/planning-artifacts/epic-9.md#Story-9.15]
- [Source: _bmad-output/implementation-artifacts/9-13-admin-ui-asset-assignment.md - Shared audit pattern]
- [Source: _bmad-output/implementation-artifacts/9-14-admin-ui-role-management.md - Role management integration]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Code review performed on 2026-01-18 by Claude Opus 4.5
- Fixed 2 HIGH severity issues: Inconsistent table name `admin_audit_logs` → `audit_logs` in logger.py (_store_log and get_logs methods)
- Updated Frontend/Backend File Structure in Dev Notes to match actual implementation
- Migration filename was planned as `20260115_007` but implemented as `20260120_001` - both are valid
- AuditLogRow.tsx and AuditLogDetail.tsx planned components were consolidated into AuditLogTable.tsx

### File List

**New Files:**
- `supabase/migrations/20260120_001_audit_logs.sql` - Audit logs table migration with append-only design
- `apps/api/app/tests/services/test_audit_logger.py` - Unit tests for AuditLogger service
- `apps/web/src/app/(admin)/audit/page.tsx` - Audit log viewer page
- `apps/web/src/components/admin/AuditLogFilters.tsx` - Filter controls component
- `apps/web/src/components/admin/AuditLogTable.tsx` - Table component with expansion
- `apps/web/src/components/admin/__tests__/AuditLogTable.test.tsx` - Frontend tests

**Modified Files:**
- `apps/api/app/services/audit/__init__.py` - Added exports for log_action, log_batch_start
- `apps/api/app/services/audit/logger.py` - Added log_action(), log_batch_start() methods, fixed table names
- `apps/api/app/api/admin.py` - Added GET /audit-logs and GET /audit-logs/{id} endpoints
- `apps/api/app/models/admin.py` - Added AuditLogEntryResponse, AuditLogListResponseV2, AuditLogFilters, AuditLogActionType
- `apps/api/app/tests/api/test_admin_endpoints.py` - Added audit log endpoint tests

