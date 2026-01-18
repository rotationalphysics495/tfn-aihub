"""
Admin Models for Asset Assignment (Story 9.13)

Pydantic models for admin operations including supervisor assignments,
batch operations, preview calculations, and audit logging.

References:
- [Source: architecture/voice-briefing.md#Admin UI Architecture]
- [Source: prd/prd-functional-requirements.md#FR46-FR50]
"""
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================================
# Enums
# ============================================================================


class AssignmentAction(str, Enum):
    """Action type for assignment changes."""
    ADD = "add"
    REMOVE = "remove"


class AuditActionType(str, Enum):
    """Type of admin action for audit logging (FR50, FR56)."""
    ASSIGNMENT_CREATED = "assignment_created"
    ASSIGNMENT_DELETED = "assignment_deleted"
    ASSIGNMENT_UPDATED = "assignment_updated"
    BATCH_UPDATE = "batch_update"
    # Story 9.14: Role management actions
    ROLE_CHANGE = "role_change"


class UserRole(str, Enum):
    """User role types (Story 9.14 AC#1)."""
    PLANT_MANAGER = "plant_manager"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"


class AuditEntityType(str, Enum):
    """Type of entity affected by admin action."""
    SUPERVISOR_ASSIGNMENT = "supervisor_assignment"
    USER_ROLE = "user_role"


class AuditLogActionType(str, Enum):
    """
    Type of audit log action (Story 9.15 Task 2.6).

    Unified action types for the audit_logs table.
    """
    ROLE_CHANGE = "role_change"
    ASSIGNMENT_CREATE = "assignment_create"
    ASSIGNMENT_UPDATE = "assignment_update"
    ASSIGNMENT_DELETE = "assignment_delete"
    BATCH_ASSIGNMENT = "batch_assignment"
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    PREFERENCE_UPDATE = "preference_update"


# ============================================================================
# Supervisor Assignment Models (AC: 1, 2, 3, 4)
# ============================================================================


class SupervisorAssignment(BaseModel):
    """
    Model for a supervisor assignment record (Task 3.2).

    Maps a supervisor to an asset they are responsible for.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "user-uuid-1",
                "asset_id": "asset-uuid-1",
                "assigned_by": "admin-uuid-1",
                "assigned_at": "2026-01-19T08:00:00Z",
                "expires_at": None,
                "created_at": "2026-01-19T08:00:00Z",
                "updated_at": "2026-01-19T08:00:00Z",
            }
        }
    )

    id: UUID = Field(..., description="Unique assignment ID")
    user_id: UUID = Field(..., description="Supervisor user ID")
    asset_id: UUID = Field(..., description="Assigned asset ID")
    assigned_by: UUID = Field(..., description="Admin who made the assignment")
    assigned_at: datetime = Field(..., description="When the assignment was made")
    expires_at: Optional[datetime] = Field(
        None,
        description="Expiration date for temporary assignments (FR49). NULL = permanent."
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Related data populated on response
    user_email: Optional[str] = Field(None, description="Supervisor email (populated on read)")
    user_name: Optional[str] = Field(None, description="Supervisor name (populated on read)")
    asset_name: Optional[str] = Field(None, description="Asset name (populated on read)")
    area_name: Optional[str] = Field(None, description="Asset area name (populated on read)")

    @property
    def is_temporary(self) -> bool:
        """Check if this is a temporary assignment."""
        return self.expires_at is not None

    @property
    def is_expired(self) -> bool:
        """Check if this temporary assignment has expired."""
        if self.expires_at is None:
            return False
        return self.expires_at < datetime.now(timezone.utc)


class SupervisorInfo(BaseModel):
    """Basic supervisor information for grid display."""
    user_id: UUID = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    name: Optional[str] = Field(None, description="User display name")


class AssetInfo(BaseModel):
    """Basic asset information for grid display."""
    asset_id: UUID = Field(..., description="Asset ID")
    name: str = Field(..., description="Asset name")
    area: Optional[str] = Field(None, description="Area where asset is located")


class AssignmentCell(BaseModel):
    """
    Represents a single cell in the assignment grid (AC: 1).

    Each cell shows whether a supervisor is assigned to an asset.
    """
    user_id: UUID
    asset_id: UUID
    is_assigned: bool = False
    expires_at: Optional[datetime] = None
    assignment_id: Optional[UUID] = None

    @property
    def is_temporary(self) -> bool:
        """Check if this is a temporary assignment."""
        return self.is_assigned and self.expires_at is not None


# ============================================================================
# Preview Models (AC: 2 - FR48)
# ============================================================================


class AssignmentChange(BaseModel):
    """
    A single assignment change for preview/batch operations (Task 3.4).

    Used in both preview requests and batch update requests.
    """
    user_id: UUID = Field(..., description="Supervisor user ID")
    asset_id: UUID = Field(..., description="Asset ID")
    action: AssignmentAction = Field(..., description="Whether to add or remove assignment")
    expires_at: Optional[datetime] = Field(
        None,
        description="For temporary assignments, when they expire (FR49)"
    )


class UserImpact(BaseModel):
    """Impact of changes on a single user for preview (FR48)."""
    user_id: UUID
    user_email: Optional[str] = None
    current_asset_count: int = Field(..., description="Current number of assigned assets")
    current_area_count: int = Field(..., description="Current number of unique areas")
    new_asset_count: int = Field(..., description="Asset count after changes")
    new_area_count: int = Field(..., description="Area count after changes")
    assets_added: List[UUID] = Field(default_factory=list)
    assets_removed: List[UUID] = Field(default_factory=list)


class AssignmentPreview(BaseModel):
    """
    Preview response showing impact of pending changes (Task 3.3, FR48).

    AC#2: Preview shows impact: "User will see X assets across Y areas"
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "changes_count": 5,
                "users_affected": 2,
                "impact_summary": "2 supervisors affected: Supervisor A will see 5 assets across 2 areas",
                "user_impacts": [],
                "warnings": [],
            }
        }
    )

    changes_count: int = Field(..., description="Total number of changes")
    users_affected: int = Field(..., description="Number of users affected by changes")
    impact_summary: str = Field(
        ...,
        description="Human-readable summary: 'User will see X assets across Y areas'"
    )
    user_impacts: List[UserImpact] = Field(
        default_factory=list,
        description="Detailed impact per affected user"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Warning messages (e.g., removing all assets from user)"
    )


# ============================================================================
# Request/Response Models (Task 2)
# ============================================================================


class AssignmentPreviewRequest(BaseModel):
    """Request body for preview calculation (Task 2.4)."""
    changes: List[AssignmentChange] = Field(
        ...,
        description="List of changes to preview",
        min_length=1
    )


class BatchAssignmentRequest(BaseModel):
    """
    Request body for batch assignment changes (Task 3.4).

    AC#3: Changes are saved atomically when confirmed.
    """
    changes: List[AssignmentChange] = Field(
        ...,
        description="List of changes to apply atomically",
        min_length=1
    )

    @field_validator("changes")
    @classmethod
    def validate_changes(cls, v: List[AssignmentChange]) -> List[AssignmentChange]:
        """Ensure no duplicate user-asset pairs in changes."""
        seen = set()
        for change in v:
            key = (str(change.user_id), str(change.asset_id))
            if key in seen:
                raise ValueError(
                    f"Duplicate change for user {change.user_id} and asset {change.asset_id}"
                )
            seen.add(key)
        return v


class BatchAssignmentResponse(BaseModel):
    """Response for batch assignment update."""
    success: bool = True
    applied_count: int = Field(..., description="Number of changes applied")
    batch_id: UUID = Field(..., description="Batch ID for audit trail")
    message: str = "Assignment changes applied successfully"


class AssignmentListResponse(BaseModel):
    """Response for listing all assignments (Task 2.2)."""
    assignments: List[SupervisorAssignment]
    total_count: int
    # Include basic user/asset info for grid display
    supervisors: List[SupervisorInfo] = Field(
        default_factory=list,
        description="List of all supervisors for grid rows"
    )
    assets: List[AssetInfo] = Field(
        default_factory=list,
        description="List of all assets grouped by area for grid columns"
    )


class UserAssignmentsResponse(BaseModel):
    """Response for getting a specific user's assignments (Task 2.3)."""
    user_id: UUID
    user_email: Optional[str] = None
    assignments: List[SupervisorAssignment]
    asset_count: int
    area_count: int


class CreateAssignmentRequest(BaseModel):
    """Request to create a single assignment."""
    user_id: UUID
    asset_id: UUID
    expires_at: Optional[datetime] = None


class CreateAssignmentResponse(BaseModel):
    """Response for creating a single assignment."""
    success: bool = True
    assignment: SupervisorAssignment
    message: str = "Assignment created successfully"


# ============================================================================
# Audit Log Models (Task 3.5, FR50, FR56)
# ============================================================================


class AuditLogEntry(BaseModel):
    """
    Audit log entry for admin actions (Task 3.5).

    Every admin change creates an immutable audit record.
    AC#3: Audit log entry is created for all write operations.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "audit-uuid-1",
                "action_type": "assignment_created",
                "entity_type": "supervisor_assignment",
                "entity_id": "assignment-uuid-1",
                "admin_user_id": "admin-uuid-1",
                "target_user_id": "supervisor-uuid-1",
                "state_before": None,
                "state_after": {"user_id": "...", "asset_id": "..."},
                "batch_id": None,
                "metadata": {"source": "admin_ui"},
                "created_at": "2026-01-19T08:00:00Z",
            }
        }
    )

    id: UUID = Field(..., description="Unique audit log ID")
    action_type: AuditActionType = Field(..., description="Type of action performed")
    entity_type: AuditEntityType = Field(..., description="Type of entity affected")
    entity_id: Optional[UUID] = Field(None, description="ID of affected entity")
    admin_user_id: UUID = Field(..., description="Admin who performed the action")
    target_user_id: Optional[UUID] = Field(
        None, description="User affected by the change"
    )
    state_before: Optional[Dict[str, Any]] = Field(
        None, description="State before the change"
    )
    state_after: Optional[Dict[str, Any]] = Field(
        None, description="State after the change"
    )
    batch_id: Optional[UUID] = Field(
        None, description="Groups batch operations together"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional context"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuditLogListResponse(BaseModel):
    """Response for listing audit logs."""
    logs: List[AuditLogEntry]
    total_count: int
    page: int = 1
    page_size: int = 50


# ============================================================================
# Role Management Models (Story 9.14)
# ============================================================================


class UserWithRole(BaseModel):
    """
    User with their current role (Story 9.14 Task 4.2).

    AC#1: List of users with current roles displayed.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user-uuid-1",
                "email": "manager@example.com",
                "role": "plant_manager",
                "created_at": "2026-01-15T08:00:00Z",
                "updated_at": "2026-01-19T08:00:00Z",
            }
        }
    )

    user_id: UUID = Field(..., description="User ID from auth.users")
    email: Optional[str] = Field(None, description="User email")
    role: UserRole = Field(..., description="Current role: plant_manager, supervisor, admin")
    created_at: Optional[datetime] = Field(None, description="When the role was created")
    updated_at: Optional[datetime] = Field(None, description="When the role was last updated")


class RoleUpdateRequest(BaseModel):
    """
    Request to update a user's role (Story 9.14 Task 4.2).

    AC#2: Admin changes a user's role.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "plant_manager"
            }
        }
    )

    role: UserRole = Field(..., description="New role to assign")


class RoleUpdateResponse(BaseModel):
    """
    Response after updating a user's role (Story 9.14).

    AC#2: Role is updated and audit log entry created.
    """
    success: bool = True
    user: UserWithRole = Field(..., description="Updated user with new role")
    message: str = "Role updated successfully"


class UserListResponse(BaseModel):
    """
    Response for listing all users with roles (Story 9.14 Task 3.2).

    AC#1: Admins see list of users with current roles.
    """
    users: List[UserWithRole]
    total_count: int


class RoleAuditLogEntry(BaseModel):
    """
    Audit log entry for role changes (Story 9.14 AC#2).

    Uses the audit_logs table defined in FR56.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "audit-uuid-1",
                "timestamp": "2026-01-19T08:00:00Z",
                "admin_user_id": "admin-uuid-1",
                "action_type": "role_change",
                "target_user_id": "user-uuid-1",
                "before_value": {"role": "supervisor"},
                "after_value": {"role": "plant_manager"},
                "metadata": {"source": "admin_ui"},
            }
        }
    )

    id: UUID = Field(..., description="Unique audit log ID")
    timestamp: datetime = Field(..., description="When the action occurred")
    admin_user_id: UUID = Field(..., description="Admin who performed the action")
    action_type: str = Field(default="role_change", description="Type of action")
    target_user_id: UUID = Field(..., description="User whose role was changed")
    before_value: Optional[Dict[str, Any]] = Field(None, description="Previous role state")
    after_value: Optional[Dict[str, Any]] = Field(None, description="New role state")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context")


# ============================================================================
# Audit Log Models (Story 9.15)
# ============================================================================


class AuditLogEntryResponse(BaseModel):
    """
    Response model for a single audit log entry (Story 9.15 Task 4.2).

    AC#1: Entry includes timestamp, admin_user_id, action_type, target, before/after values.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "audit-uuid-1",
                "timestamp": "2026-01-19T08:00:00Z",
                "admin_user_id": "admin-uuid-1",
                "admin_email": "admin@example.com",
                "action_type": "role_change",
                "target_type": "user",
                "target_id": "user-uuid-1",
                "target_user_id": "user-uuid-1",
                "target_asset_id": None,
                "before_value": {"role": "supervisor"},
                "after_value": {"role": "plant_manager"},
                "batch_id": None,
                "metadata": {"source": "admin_ui"},
            }
        }
    )

    id: UUID = Field(..., description="Unique audit log ID")
    timestamp: datetime = Field(..., description="When the action occurred")
    admin_user_id: UUID = Field(..., description="Admin who performed the action")
    admin_email: Optional[str] = Field(None, description="Admin email (populated on read)")
    action_type: str = Field(..., description="Type of action (role_change, assignment_create, etc.)")
    target_type: Optional[str] = Field(None, description="Type of entity affected")
    target_id: Optional[UUID] = Field(None, description="Generic target ID")
    target_user_id: Optional[UUID] = Field(None, description="User affected by the change")
    target_user_email: Optional[str] = Field(None, description="Target user email (populated on read)")
    target_asset_id: Optional[UUID] = Field(None, description="Asset affected by the change")
    target_asset_name: Optional[str] = Field(None, description="Asset name (populated on read)")
    before_value: Optional[Dict[str, Any]] = Field(None, description="State before the change")
    after_value: Optional[Dict[str, Any]] = Field(None, description="State after the change")
    batch_id: Optional[UUID] = Field(None, description="Groups batch operations together")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class AuditLogFilters(BaseModel):
    """
    Filter parameters for audit log queries (Story 9.15 Task 4.5).

    AC#2: Filters available - date range, action type, target user.
    """
    start_date: Optional[datetime] = Field(None, description="Filter entries after this date (ISO 8601)")
    end_date: Optional[datetime] = Field(None, description="Filter entries before this date (ISO 8601)")
    action_type: Optional[str] = Field(None, description="Filter by action type")
    target_user_id: Optional[UUID] = Field(None, description="Filter by target user")
    admin_user_id: Optional[UUID] = Field(None, description="Filter by admin who performed action")
    batch_id: Optional[UUID] = Field(None, description="Filter by batch operation ID")


class AuditLogListResponseV2(BaseModel):
    """
    Response for listing audit logs (Story 9.15 Task 4.4).

    AC#2: Entries displayed in reverse chronological order with pagination.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "entries": [],
                "total": 100,
                "page": 1,
                "page_size": 50,
            }
        }
    )

    entries: List[AuditLogEntryResponse] = Field(..., description="List of audit log entries")
    total: int = Field(..., description="Total count of entries matching filters")
    page: int = Field(default=1, ge=1, description="Current page number")
    page_size: int = Field(default=50, ge=1, le=100, description="Items per page")
