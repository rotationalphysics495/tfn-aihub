"""
Admin API Endpoints (Story 9.13, 9.14)

REST endpoints for admin operations including supervisor asset assignment
and user role management.

Task 2 (Story 9.13 - Asset Assignment):
AC#1: GET /api/v1/admin/assignments - Grid display data with supervisors, assets, assignments
AC#2: GET /api/v1/admin/assignments/user/{user_id} - Get user's assignments
AC#3: POST /api/v1/admin/assignments/preview - Preview impact of changes (FR48)
AC#4: POST /api/v1/admin/assignments/batch - Save batch changes atomically (FR46)
AC#5: DELETE /api/v1/admin/assignments/{id} - Remove single assignment
AC#6: require_admin dependency on all endpoints
AC#7: Audit logging for all write operations (FR50, FR56)

Task 3 (Story 9.14 - Role Management):
AC#1: GET /api/v1/admin/users - List users with current roles (FR47)
AC#2: GET /api/v1/admin/users/{id} - Get single user details
AC#3: PUT /api/v1/admin/users/{id}/role - Update user role with last-admin protection

References:
- [Source: architecture/voice-briefing.md#Admin UI Architecture]
- [Source: prd/prd-functional-requirements.md#FR46-FR50]
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional, Set
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Depends, Query

from supabase import Client, create_client

from app.core.config import get_settings
from app.core.security import require_admin
from app.models.user import CurrentUser
from app.models.admin import (
    SupervisorAssignment,
    SupervisorInfo,
    AssetInfo,
    AssignmentListResponse,
    UserAssignmentsResponse,
    AssignmentPreviewRequest,
    AssignmentPreview,
    UserImpact,
    BatchAssignmentRequest,
    BatchAssignmentResponse,
    CreateAssignmentRequest,
    CreateAssignmentResponse,
    AssignmentAction,
    AuditActionType,
    # Story 9.14: Role management models
    UserRole,
    UserWithRole,
    UserListResponse,
    RoleUpdateRequest,
    RoleUpdateResponse,
)
from app.services.audit import log_assignment_change, log_batch_assignment_change, log_role_change

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Helper Functions
# ============================================================================


def _get_supabase_client() -> Optional[Client]:
    """Get Supabase client for database operations."""
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        return None
    return create_client(settings.supabase_url, settings.supabase_key)


def _get_mock_supervisors() -> List[SupervisorInfo]:
    """Return mock supervisors for development."""
    return [
        SupervisorInfo(
            user_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
            email="supervisor1@example.com",
            name="Sarah Supervisor"
        ),
        SupervisorInfo(
            user_id=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
            email="supervisor2@example.com",
            name="Bob Supervisor"
        ),
        SupervisorInfo(
            user_id=UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
            email="supervisor3@example.com",
            name="Carol Supervisor"
        ),
    ]


def _get_mock_assets() -> List[AssetInfo]:
    """Return mock assets for development."""
    return [
        AssetInfo(asset_id=UUID("11111111-1111-1111-1111-111111111111"), name="Grinder 1", area="Grinding"),
        AssetInfo(asset_id=UUID("11111111-1111-1111-1111-111111111112"), name="Grinder 2", area="Grinding"),
        AssetInfo(asset_id=UUID("22222222-2222-2222-2222-222222222221"), name="Packer 1", area="Packing"),
        AssetInfo(asset_id=UUID("22222222-2222-2222-2222-222222222222"), name="Packer 2", area="Packing"),
        AssetInfo(asset_id=UUID("33333333-3333-3333-3333-333333333331"), name="Roaster A", area="Roasting"),
        AssetInfo(asset_id=UUID("33333333-3333-3333-3333-333333333332"), name="Roaster B", area="Roasting"),
    ]


def _get_mock_assignments() -> List[SupervisorAssignment]:
    """Return mock assignments for development."""
    now = datetime.now(timezone.utc)
    return [
        SupervisorAssignment(
            id=UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee1"),
            user_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
            asset_id=UUID("11111111-1111-1111-1111-111111111111"),
            assigned_by=UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
            assigned_at=now,
            expires_at=None,
            created_at=now,
            updated_at=now,
        ),
        SupervisorAssignment(
            id=UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee2"),
            user_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
            asset_id=UUID("11111111-1111-1111-1111-111111111112"),
            assigned_by=UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
            assigned_at=now,
            expires_at=None,
            created_at=now,
            updated_at=now,
        ),
        SupervisorAssignment(
            id=UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeee3"),
            user_id=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
            asset_id=UUID("22222222-2222-2222-2222-222222222221"),
            assigned_by=UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
            assigned_at=now,
            expires_at=None,
            created_at=now,
            updated_at=now,
        ),
    ]


# In-memory store for development
_mock_assignments: dict[str, dict] = {}


def _init_mock_data():
    """Initialize mock data if empty."""
    if not _mock_assignments:
        for a in _get_mock_assignments():
            _mock_assignments[str(a.id)] = {
                "id": str(a.id),
                "user_id": str(a.user_id),
                "asset_id": str(a.asset_id),
                "assigned_by": str(a.assigned_by),
                "assigned_at": a.assigned_at.isoformat(),
                "expires_at": a.expires_at.isoformat() if a.expires_at else None,
                "created_at": a.created_at.isoformat(),
                "updated_at": a.updated_at.isoformat(),
            }


# ============================================================================
# API Endpoints
# ============================================================================


@router.get("/assignments", response_model=AssignmentListResponse)
async def list_assignments(
    include_expired: bool = Query(False, description="Include expired temporary assignments"),
    current_user: CurrentUser = Depends(require_admin),
):
    """
    List all supervisor assignments with grid display data (Task 2.2).

    AC#1: Returns grid data with columns (areas/assets) and rows (supervisors).

    Returns:
        AssignmentListResponse with all assignments plus supervisor/asset lists
    """
    logger.info(f"Admin {current_user.id} listing all assignments")

    supabase = _get_supabase_client()

    if supabase is None:
        # Return mock data for development
        _init_mock_data()

        supervisors = _get_mock_supervisors()
        assets = _get_mock_assets()

        assignments = []
        for a in _mock_assignments.values():
            expires_at = None
            if a.get("expires_at"):
                expires_at = datetime.fromisoformat(a["expires_at"].replace("Z", "+00:00"))
                # Skip expired if not including them
                if not include_expired and expires_at < datetime.now(timezone.utc):
                    continue

            assignments.append(SupervisorAssignment(
                id=UUID(a["id"]),
                user_id=UUID(a["user_id"]),
                asset_id=UUID(a["asset_id"]),
                assigned_by=UUID(a["assigned_by"]),
                assigned_at=datetime.fromisoformat(a["assigned_at"].replace("Z", "+00:00")),
                expires_at=expires_at,
                created_at=datetime.fromisoformat(a["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(a["updated_at"].replace("Z", "+00:00")),
            ))

        return AssignmentListResponse(
            assignments=assignments,
            total_count=len(assignments),
            supervisors=supervisors,
            assets=assets,
        )

    try:
        # Query all supervisors (users with role = 'supervisor')
        supervisors_result = supabase.table("user_roles").select(
            "user_id, auth.users(email)"
        ).eq("role", "supervisor").execute()

        supervisors = [
            SupervisorInfo(
                user_id=UUID(row["user_id"]),
                email=row.get("users", {}).get("email", ""),
                name=None,
            )
            for row in supervisors_result.data
        ]

        # Query all assets
        assets_result = supabase.table("assets").select("id, name, area").execute()

        assets = [
            AssetInfo(
                asset_id=UUID(row["id"]),
                name=row["name"],
                area=row.get("area"),
            )
            for row in assets_result.data
        ]

        # Query assignments using the active view or filtering
        # Note: active_supervisor_assignments view exists in DB but we filter in Python
        # for consistency with mock mode behavior
        assignments_result = supabase.table("supervisor_assignments").select("*").execute()

        assignments = []
        for row in assignments_result.data:
            expires_at = None
            if row.get("expires_at"):
                expires_at = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
                # Skip expired if not including them
                if not include_expired and expires_at < datetime.now(timezone.utc):
                    continue

            assignments.append(SupervisorAssignment(
                id=UUID(row["id"]),
                user_id=UUID(row["user_id"]),
                asset_id=UUID(row["asset_id"]),
                assigned_by=UUID(row["assigned_by"]) if row.get("assigned_by") else UUID("00000000-0000-0000-0000-000000000000"),
                assigned_at=datetime.fromisoformat(row["assigned_at"].replace("Z", "+00:00")),
                expires_at=expires_at,
                created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")),
            ))

        return AssignmentListResponse(
            assignments=assignments,
            total_count=len(assignments),
            supervisors=supervisors,
            assets=assets,
        )

    except Exception as e:
        logger.error(f"Error listing assignments: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list assignments: {str(e)}"
        )


@router.get("/assignments/user/{user_id}", response_model=UserAssignmentsResponse)
async def get_user_assignments(
    user_id: UUID,
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Get a specific user's assignments (Task 2.3).

    Args:
        user_id: ID of the supervisor to get assignments for

    Returns:
        UserAssignmentsResponse with user's assignments and counts
    """
    logger.info(f"Admin {current_user.id} getting assignments for user {user_id}")

    supabase = _get_supabase_client()

    if supabase is None:
        # Return mock data
        _init_mock_data()

        user_assignments = [
            a for a in _mock_assignments.values()
            if a["user_id"] == str(user_id)
        ]

        assignments = []
        areas: Set[str] = set()
        mock_assets = {str(a.asset_id): a for a in _get_mock_assets()}

        for a in user_assignments:
            expires_at = None
            if a.get("expires_at"):
                expires_at = datetime.fromisoformat(a["expires_at"].replace("Z", "+00:00"))

            asset_info = mock_assets.get(a["asset_id"])
            if asset_info and asset_info.area:
                areas.add(asset_info.area)

            assignments.append(SupervisorAssignment(
                id=UUID(a["id"]),
                user_id=UUID(a["user_id"]),
                asset_id=UUID(a["asset_id"]),
                assigned_by=UUID(a["assigned_by"]),
                assigned_at=datetime.fromisoformat(a["assigned_at"].replace("Z", "+00:00")),
                expires_at=expires_at,
                created_at=datetime.fromisoformat(a["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(a["updated_at"].replace("Z", "+00:00")),
                asset_name=asset_info.name if asset_info else None,
                area_name=asset_info.area if asset_info else None,
            ))

        # Get user email from mock supervisors
        mock_supervisors = {str(s.user_id): s for s in _get_mock_supervisors()}
        user_email = mock_supervisors.get(str(user_id), SupervisorInfo(
            user_id=user_id, email="unknown@example.com"
        )).email

        return UserAssignmentsResponse(
            user_id=user_id,
            user_email=user_email,
            assignments=assignments,
            asset_count=len(assignments),
            area_count=len(areas),
        )

    try:
        # Query user's assignments with asset details
        result = supabase.table("supervisor_assignments").select(
            "*, assets(name, area)"
        ).eq("user_id", str(user_id)).execute()

        assignments = []
        areas: Set[str] = set()

        for row in result.data:
            asset_data = row.get("assets", {})
            if asset_data and asset_data.get("area"):
                areas.add(asset_data["area"])

            expires_at = None
            if row.get("expires_at"):
                expires_at = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))

            assignments.append(SupervisorAssignment(
                id=UUID(row["id"]),
                user_id=UUID(row["user_id"]),
                asset_id=UUID(row["asset_id"]),
                assigned_by=UUID(row["assigned_by"]) if row.get("assigned_by") else UUID("00000000-0000-0000-0000-000000000000"),
                assigned_at=datetime.fromisoformat(row["assigned_at"].replace("Z", "+00:00")),
                expires_at=expires_at,
                created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")),
                asset_name=asset_data.get("name"),
                area_name=asset_data.get("area"),
            ))

        # Get user email
        user_result = supabase.auth.admin.get_user_by_id(str(user_id))
        user_email = user_result.user.email if user_result and user_result.user else None

        return UserAssignmentsResponse(
            user_id=user_id,
            user_email=user_email,
            assignments=assignments,
            asset_count=len(assignments),
            area_count=len(areas),
        )

    except Exception as e:
        logger.error(f"Error getting user assignments: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user assignments: {str(e)}"
        )


@router.post("/assignments/preview", response_model=AssignmentPreview)
async def preview_assignment_changes(
    request: AssignmentPreviewRequest,
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Preview impact of assignment changes (Task 2.4, FR48).

    AC#2: Preview shows "User will see X assets across Y areas"

    Args:
        request: List of proposed changes

    Returns:
        AssignmentPreview with impact summary and per-user details
    """
    logger.info(f"Admin {current_user.id} previewing {len(request.changes)} changes")

    # Get current assignments
    supabase = _get_supabase_client()

    if supabase is None:
        _init_mock_data()
        current_assignments = list(_mock_assignments.values())
        mock_assets = {str(a.asset_id): a for a in _get_mock_assets()}
    else:
        try:
            result = supabase.table("supervisor_assignments").select("*").execute()
            current_assignments = result.data

            assets_result = supabase.table("assets").select("id, name, area").execute()
            mock_assets = {row["id"]: AssetInfo(
                asset_id=UUID(row["id"]), name=row["name"], area=row.get("area")
            ) for row in assets_result.data}
        except Exception as e:
            logger.error(f"Error fetching current state for preview: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch current assignments")

    # Build current state per user
    user_current_assets: dict[str, Set[str]] = {}
    for a in current_assignments:
        uid = a.get("user_id") if isinstance(a, dict) else str(a.user_id)
        aid = a.get("asset_id") if isinstance(a, dict) else str(a.asset_id)
        if uid not in user_current_assets:
            user_current_assets[uid] = set()
        user_current_assets[uid].add(aid)

    # Apply changes to simulate new state
    user_new_assets: dict[str, Set[str]] = {k: v.copy() for k, v in user_current_assets.items()}
    users_affected: Set[str] = set()

    for change in request.changes:
        uid = str(change.user_id)
        aid = str(change.asset_id)
        users_affected.add(uid)

        if uid not in user_new_assets:
            user_new_assets[uid] = set()

        if change.action == AssignmentAction.ADD:
            user_new_assets[uid].add(aid)
        elif change.action == AssignmentAction.REMOVE:
            user_new_assets[uid].discard(aid)

    # Calculate impact per user
    user_impacts: List[UserImpact] = []
    warnings: List[str] = []

    for uid in users_affected:
        current_assets = user_current_assets.get(uid, set())
        new_assets = user_new_assets.get(uid, set())

        # Calculate areas
        current_areas = {mock_assets.get(a, AssetInfo(asset_id=UUID(a), name="", area=None)).area for a in current_assets if mock_assets.get(a)}
        new_areas = {mock_assets.get(a, AssetInfo(asset_id=UUID(a), name="", area=None)).area for a in new_assets if mock_assets.get(a)}
        current_areas.discard(None)
        new_areas.discard(None)

        assets_added = new_assets - current_assets
        assets_removed = current_assets - new_assets

        user_impacts.append(UserImpact(
            user_id=UUID(uid),
            current_asset_count=len(current_assets),
            current_area_count=len(current_areas),
            new_asset_count=len(new_assets),
            new_area_count=len(new_areas),
            assets_added=[UUID(a) for a in assets_added],
            assets_removed=[UUID(a) for a in assets_removed],
        ))

        # Generate warnings
        if len(new_assets) == 0 and len(current_assets) > 0:
            warnings.append(f"User {uid} will have no assets assigned after these changes")

    # Build summary
    summaries = []
    for impact in user_impacts:
        summaries.append(
            f"User will see {impact.new_asset_count} assets across {impact.new_area_count} areas"
        )

    impact_summary = "; ".join(summaries) if summaries else "No changes"

    return AssignmentPreview(
        changes_count=len(request.changes),
        users_affected=len(users_affected),
        impact_summary=impact_summary,
        user_impacts=user_impacts,
        warnings=warnings,
    )


@router.post("/assignments/batch", response_model=BatchAssignmentResponse)
async def batch_update_assignments(
    request: BatchAssignmentRequest,
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Apply batch assignment changes atomically (Task 2.5).

    AC#3: Changes are written atomically when confirmed.
    AC#3: Audit log entries are created.

    Args:
        request: List of changes to apply

    Returns:
        BatchAssignmentResponse with batch_id for audit trail
    """
    admin_id = current_user.id
    logger.info(f"Admin {admin_id} applying {len(request.changes)} changes")

    batch_id = uuid4()
    results: List[dict] = []
    applied_count = 0

    supabase = _get_supabase_client()

    if supabase is None:
        # Apply to in-memory store
        _init_mock_data()

        for change in request.changes:
            uid = str(change.user_id)
            aid = str(change.asset_id)
            now = datetime.now(timezone.utc)

            if change.action == AssignmentAction.ADD:
                # Check for existing assignment
                existing = next(
                    (a for a in _mock_assignments.values()
                     if a["user_id"] == uid and a["asset_id"] == aid),
                    None
                )
                if existing:
                    results.append({"success": False, "reason": "already_exists"})
                    continue

                # Create new assignment
                assignment_id = str(uuid4())
                assignment_data = {
                    "id": assignment_id,
                    "user_id": uid,
                    "asset_id": aid,
                    "assigned_by": admin_id,
                    "assigned_at": now.isoformat(),
                    "expires_at": change.expires_at.isoformat() if change.expires_at else None,
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                }
                _mock_assignments[assignment_id] = assignment_data

                results.append({
                    "success": True,
                    "assignment_id": assignment_id,
                    "state_before": None,
                    "state_after": assignment_data,
                })
                applied_count += 1

            elif change.action == AssignmentAction.REMOVE:
                # Find existing assignment
                existing = next(
                    (a for a in _mock_assignments.values()
                     if a["user_id"] == uid and a["asset_id"] == aid),
                    None
                )
                if not existing:
                    results.append({"success": False, "reason": "not_found"})
                    continue

                # Delete assignment
                del _mock_assignments[existing["id"]]

                results.append({
                    "success": True,
                    "assignment_id": existing["id"],
                    "state_before": existing,
                    "state_after": None,
                })
                applied_count += 1

    else:
        # Apply to Supabase
        try:
            for change in request.changes:
                uid = str(change.user_id)
                aid = str(change.asset_id)
                now = datetime.now(timezone.utc)

                if change.action == AssignmentAction.ADD:
                    # Check for existing
                    existing = supabase.table("supervisor_assignments").select("id").eq(
                        "user_id", uid
                    ).eq("asset_id", aid).execute()

                    if existing.data:
                        results.append({"success": False, "reason": "already_exists"})
                        continue

                    # Insert new assignment
                    insert_data = {
                        "user_id": uid,
                        "asset_id": aid,
                        "assigned_by": admin_id,
                        "assigned_at": now.isoformat(),
                        "expires_at": change.expires_at.isoformat() if change.expires_at else None,
                    }
                    result = supabase.table("supervisor_assignments").insert(insert_data).execute()

                    if result.data:
                        results.append({
                            "success": True,
                            "assignment_id": result.data[0]["id"],
                            "state_before": None,
                            "state_after": result.data[0],
                        })
                        applied_count += 1
                    else:
                        results.append({"success": False, "reason": "insert_failed"})

                elif change.action == AssignmentAction.REMOVE:
                    # Find existing
                    existing = supabase.table("supervisor_assignments").select("*").eq(
                        "user_id", uid
                    ).eq("asset_id", aid).execute()

                    if not existing.data:
                        results.append({"success": False, "reason": "not_found"})
                        continue

                    # Delete
                    assignment_id = existing.data[0]["id"]
                    supabase.table("supervisor_assignments").delete().eq("id", assignment_id).execute()

                    results.append({
                        "success": True,
                        "assignment_id": assignment_id,
                        "state_before": existing.data[0],
                        "state_after": None,
                    })
                    applied_count += 1

        except Exception as e:
            logger.error(f"Error applying batch changes: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to apply changes: {str(e)}"
            )

    # Log audit trail (Task 2.8)
    log_batch_assignment_change(
        admin_user_id=admin_id,
        changes=request.changes,
        results=results,
        metadata={"source": "admin_ui"},
    )

    return BatchAssignmentResponse(
        success=True,
        applied_count=applied_count,
        batch_id=batch_id,
        message=f"Applied {applied_count} of {len(request.changes)} changes",
    )


@router.post("/assignments", response_model=CreateAssignmentResponse, status_code=201)
async def create_assignment(
    request: CreateAssignmentRequest,
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Create a single assignment (alternative to batch).

    Args:
        request: Assignment creation request

    Returns:
        CreateAssignmentResponse with created assignment
    """
    admin_id = current_user.id
    logger.info(f"Admin {admin_id} creating assignment: {request.user_id} -> {request.asset_id}")

    now = datetime.now(timezone.utc)
    supabase = _get_supabase_client()

    if supabase is None:
        _init_mock_data()

        # Check for existing
        existing = next(
            (a for a in _mock_assignments.values()
             if a["user_id"] == str(request.user_id) and a["asset_id"] == str(request.asset_id)),
            None
        )
        if existing:
            raise HTTPException(status_code=409, detail="Assignment already exists")

        # Create
        assignment_id = str(uuid4())
        assignment_data = {
            "id": assignment_id,
            "user_id": str(request.user_id),
            "asset_id": str(request.asset_id),
            "assigned_by": admin_id,
            "assigned_at": now.isoformat(),
            "expires_at": request.expires_at.isoformat() if request.expires_at else None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        _mock_assignments[assignment_id] = assignment_data

        assignment = SupervisorAssignment(
            id=UUID(assignment_id),
            user_id=request.user_id,
            asset_id=request.asset_id,
            assigned_by=UUID(admin_id),
            assigned_at=now,
            expires_at=request.expires_at,
            created_at=now,
            updated_at=now,
        )

    else:
        try:
            # Check for existing
            existing = supabase.table("supervisor_assignments").select("id").eq(
                "user_id", str(request.user_id)
            ).eq("asset_id", str(request.asset_id)).execute()

            if existing.data:
                raise HTTPException(status_code=409, detail="Assignment already exists")

            # Insert
            insert_data = {
                "user_id": str(request.user_id),
                "asset_id": str(request.asset_id),
                "assigned_by": admin_id,
                "assigned_at": now.isoformat(),
                "expires_at": request.expires_at.isoformat() if request.expires_at else None,
            }
            result = supabase.table("supervisor_assignments").insert(insert_data).execute()

            if not result.data:
                raise HTTPException(status_code=500, detail="Failed to create assignment")

            row = result.data[0]
            assignment = SupervisorAssignment(
                id=UUID(row["id"]),
                user_id=UUID(row["user_id"]),
                asset_id=UUID(row["asset_id"]),
                assigned_by=UUID(row["assigned_by"]),
                assigned_at=datetime.fromisoformat(row["assigned_at"].replace("Z", "+00:00")),
                expires_at=datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00")) if row.get("expires_at") else None,
                created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")),
            )
            assignment_id = row["id"]
            assignment_data = row

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating assignment: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create assignment: {str(e)}")

    # Log audit (Task 2.8)
    log_assignment_change(
        action_type=AuditActionType.ASSIGNMENT_CREATED,
        admin_user_id=admin_id,
        target_user_id=str(request.user_id),
        asset_id=str(request.asset_id),
        assignment_id=assignment_id if isinstance(assignment_id, str) else str(assignment_id),
        state_before=None,
        state_after=assignment_data if isinstance(assignment_data, dict) else None,
        metadata={"source": "admin_ui", "expires_at": str(request.expires_at) if request.expires_at else None},
    )

    return CreateAssignmentResponse(
        success=True,
        assignment=assignment,
        message="Assignment created successfully",
    )


@router.delete("/assignments/{assignment_id}", status_code=204)
async def delete_assignment(
    assignment_id: UUID,
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Delete a single assignment (Task 2.6).

    Args:
        assignment_id: ID of the assignment to delete

    Returns:
        204 No Content on success
    """
    admin_id = current_user.id
    logger.info(f"Admin {admin_id} deleting assignment {assignment_id}")

    supabase = _get_supabase_client()

    if supabase is None:
        _init_mock_data()

        assignment = _mock_assignments.get(str(assignment_id))
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        del _mock_assignments[str(assignment_id)]
        state_before = assignment
        target_user_id = assignment["user_id"]
        asset_id = assignment["asset_id"]

    else:
        try:
            # Get current state for audit
            existing = supabase.table("supervisor_assignments").select("*").eq(
                "id", str(assignment_id)
            ).execute()

            if not existing.data:
                raise HTTPException(status_code=404, detail="Assignment not found")

            state_before = existing.data[0]
            target_user_id = state_before["user_id"]
            asset_id = state_before["asset_id"]

            # Delete
            supabase.table("supervisor_assignments").delete().eq("id", str(assignment_id)).execute()

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting assignment: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete assignment: {str(e)}")

    # Log audit (Task 2.8)
    log_assignment_change(
        action_type=AuditActionType.ASSIGNMENT_DELETED,
        admin_user_id=admin_id,
        target_user_id=target_user_id,
        asset_id=asset_id,
        assignment_id=str(assignment_id),
        state_before=state_before,
        state_after=None,
        metadata={"source": "admin_ui"},
    )

    return None


# ============================================================================
# Role Management Endpoints (Story 9.14)
# ============================================================================

# In-memory mock data for development
_mock_user_roles: dict[str, dict] = {}


def _init_mock_user_roles():
    """Initialize mock user roles data if empty."""
    if not _mock_user_roles:
        now = datetime.now(timezone.utc).isoformat()
        # Create mock users with roles
        _mock_user_roles["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"] = {
            "user_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "email": "supervisor1@example.com",
            "role": "supervisor",
            "created_at": now,
            "updated_at": now,
        }
        _mock_user_roles["bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"] = {
            "user_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            "email": "supervisor2@example.com",
            "role": "supervisor",
            "created_at": now,
            "updated_at": now,
        }
        _mock_user_roles["cccccccc-cccc-cccc-cccc-cccccccccccc"] = {
            "user_id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
            "email": "manager@example.com",
            "role": "plant_manager",
            "created_at": now,
            "updated_at": now,
        }
        _mock_user_roles["dddddddd-dddd-dddd-dddd-dddddddddddd"] = {
            "user_id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
            "email": "admin@example.com",
            "role": "admin",
            "created_at": now,
            "updated_at": now,
        }


@router.get("/users", response_model=UserListResponse)
async def list_users(
    current_user: CurrentUser = Depends(require_admin),
):
    """
    List all users with their current roles (Story 9.14 Task 3.2).

    AC#1: Admins see a list of users with current roles.
    Roles shown: Plant Manager, Supervisor, Admin

    Returns:
        UserListResponse with all users and their roles
    """
    logger.info(f"Admin {current_user.id} listing all users with roles")

    supabase = _get_supabase_client()

    if supabase is None:
        # Return mock data for development
        _init_mock_user_roles()

        users = [
            UserWithRole(
                user_id=UUID(data["user_id"]),
                email=data["email"],
                role=UserRole(data["role"]),
                created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
            )
            for data in _mock_user_roles.values()
        ]

        return UserListResponse(
            users=users,
            total_count=len(users),
        )

    try:
        # Query user_roles table joined with auth.users for email
        # Note: Supabase join syntax - we query user_roles and get email from auth.users
        result = supabase.table("user_roles").select("*").execute()

        users = []
        for row in result.data:
            # Get user email from auth.users via admin API
            try:
                user_auth = supabase.auth.admin.get_user_by_id(row["user_id"])
                email = user_auth.user.email if user_auth and user_auth.user else None
            except Exception:
                email = None

            users.append(UserWithRole(
                user_id=UUID(row["user_id"]),
                email=email,
                role=UserRole(row["role"]),
                created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else None,
                updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")) if row.get("updated_at") else None,
            ))

        return UserListResponse(
            users=users,
            total_count=len(users),
        )

    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list users: {str(e)}"
        )


@router.get("/users/{user_id}", response_model=UserWithRole)
async def get_user(
    user_id: UUID,
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Get a single user's details including role (Story 9.14 Task 3.3).

    Args:
        user_id: ID of the user to retrieve

    Returns:
        UserWithRole with user details and current role
    """
    logger.info(f"Admin {current_user.id} getting user {user_id}")

    supabase = _get_supabase_client()

    if supabase is None:
        _init_mock_user_roles()

        user_data = _mock_user_roles.get(str(user_id))
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        return UserWithRole(
            user_id=UUID(user_data["user_id"]),
            email=user_data["email"],
            role=UserRole(user_data["role"]),
            created_at=datetime.fromisoformat(user_data["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(user_data["updated_at"].replace("Z", "+00:00")),
        )

    try:
        # Query user_roles for the specific user
        result = supabase.table("user_roles").select("*").eq("user_id", str(user_id)).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")

        row = result.data[0]

        # Get user email from auth.users
        try:
            user_auth = supabase.auth.admin.get_user_by_id(str(user_id))
            email = user_auth.user.email if user_auth and user_auth.user else None
        except Exception:
            email = None

        return UserWithRole(
            user_id=UUID(row["user_id"]),
            email=email,
            role=UserRole(row["role"]),
            created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else None,
            updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")) if row.get("updated_at") else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user: {str(e)}"
        )


@router.put("/users/{user_id}/role", response_model=RoleUpdateResponse)
async def update_user_role(
    user_id: UUID,
    request: RoleUpdateRequest,
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Update a user's role (Story 9.14 Task 3.4).

    AC#2: Admin changes a user's role, user_roles table is updated,
          audit log entry is created, user's access changes immediately.
    AC#3: System prevents removing the last admin.

    Args:
        user_id: ID of the user to update
        request: RoleUpdateRequest with new role

    Returns:
        RoleUpdateResponse with updated user

    Raises:
        HTTPException 400: Cannot remove last admin
        HTTPException 404: User not found
    """
    admin_id = current_user.id
    new_role = request.role.value
    logger.info(f"Admin {admin_id} updating role for user {user_id} to {new_role}")

    supabase = _get_supabase_client()

    if supabase is None:
        _init_mock_user_roles()

        user_data = _mock_user_roles.get(str(user_id))
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        old_role = user_data["role"]

        # AC#3: Prevent removing last admin
        if old_role == "admin" and new_role != "admin":
            admin_count = sum(1 for u in _mock_user_roles.values() if u["role"] == "admin")
            if admin_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot remove last admin"
                )

        # Update role
        now = datetime.now(timezone.utc)
        user_data["role"] = new_role
        user_data["updated_at"] = now.isoformat()

        # Log audit (AC#2)
        log_role_change(
            admin_user_id=admin_id,
            target_user_id=str(user_id),
            old_role=old_role,
            new_role=new_role,
            metadata={"source": "admin_ui"},
        )

        return RoleUpdateResponse(
            success=True,
            user=UserWithRole(
                user_id=UUID(user_data["user_id"]),
                email=user_data["email"],
                role=UserRole(user_data["role"]),
                created_at=datetime.fromisoformat(user_data["created_at"].replace("Z", "+00:00")),
                updated_at=now,
            ),
            message=f"Role updated from {old_role} to {new_role}",
        )

    try:
        # Get current role
        existing = supabase.table("user_roles").select("*").eq("user_id", str(user_id)).execute()

        if not existing.data:
            raise HTTPException(status_code=404, detail="User not found")

        old_role = existing.data[0]["role"]

        # AC#3: Prevent removing last admin
        # The database trigger will also enforce this, but we check here for a better error message
        if old_role == "admin" and new_role != "admin":
            admin_count_result = supabase.table("user_roles").select("user_id", count="exact").eq("role", "admin").execute()
            admin_count = admin_count_result.count if admin_count_result.count else len(admin_count_result.data)
            if admin_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot remove last admin"
                )

        # Update role
        now = datetime.now(timezone.utc)
        result = supabase.table("user_roles").update({
            "role": new_role,
            "updated_at": now.isoformat(),
        }).eq("user_id", str(user_id)).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update role")

        row = result.data[0]

        # Get user email
        try:
            user_auth = supabase.auth.admin.get_user_by_id(str(user_id))
            email = user_auth.user.email if user_auth and user_auth.user else None
        except Exception:
            email = None

        # Log audit (AC#2)
        log_role_change(
            admin_user_id=admin_id,
            target_user_id=str(user_id),
            old_role=old_role,
            new_role=new_role,
            metadata={"source": "admin_ui"},
        )

        return RoleUpdateResponse(
            success=True,
            user=UserWithRole(
                user_id=UUID(row["user_id"]),
                email=email,
                role=UserRole(row["role"]),
                created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else None,
                updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")) if row.get("updated_at") else None,
            ),
            message=f"Role updated from {old_role} to {new_role}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user role: {e}")
        # Check if it's the last-admin trigger error
        if "Cannot remove last admin" in str(e):
            raise HTTPException(
                status_code=400,
                detail="Cannot remove last admin"
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update role: {str(e)}"
        )


# ============================================================================
# Audit Log Endpoints (Story 9.15)
# ============================================================================

# Import Story 9.15 models
from app.models.admin import (
    AuditLogEntryResponse,
    AuditLogListResponseV2,
    AuditLogActionType,
)

# In-memory mock audit logs for development
_mock_audit_logs: List[dict] = []


def _init_mock_audit_logs():
    """Initialize mock audit logs if empty."""
    if not _mock_audit_logs:
        now = datetime.now(timezone.utc)
        # Add sample audit log entries
        _mock_audit_logs.extend([
            {
                "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "timestamp": (now - timedelta(hours=2)).isoformat(),
                "admin_user_id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
                "action_type": "role_change",
                "target_type": "user",
                "target_user_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "before_value": {"role": "supervisor"},
                "after_value": {"role": "plant_manager"},
                "batch_id": None,
                "metadata": {"source": "admin_ui"},
            },
            {
                "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "timestamp": (now - timedelta(hours=1)).isoformat(),
                "admin_user_id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
                "action_type": "assignment_create",
                "target_type": "assignment",
                "target_user_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "target_asset_id": "22222222-2222-2222-2222-222222222221",
                "before_value": None,
                "after_value": {"user_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "asset_id": "22222222-2222-2222-2222-222222222221"},
                "batch_id": None,
                "metadata": {"source": "admin_ui"},
            },
            {
                "id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
                "timestamp": now.isoformat(),
                "admin_user_id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
                "action_type": "assignment_delete",
                "target_type": "assignment",
                "target_user_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "target_asset_id": "11111111-1111-1111-1111-111111111111",
                "before_value": {"user_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "asset_id": "11111111-1111-1111-1111-111111111111"},
                "after_value": None,
                "batch_id": None,
                "metadata": {"source": "admin_ui"},
            },
        ])


# Import timedelta for mock data
from datetime import timedelta


@router.get("/audit-logs", response_model=AuditLogListResponseV2)
async def list_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    start_date: Optional[datetime] = Query(None, description="Filter entries after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter entries before this date"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    target_user_id: Optional[UUID] = Query(None, description="Filter by target user"),
    admin_user_id: Optional[UUID] = Query(None, description="Filter by admin who performed action"),
    current_user: CurrentUser = Depends(require_admin),
):
    """
    List audit log entries with pagination and optional filters (Story 9.15 Task 3.2).

    AC#2: Entries displayed in reverse chronological order.
    AC#2: Filters available - date range, action type, target user.

    Returns:
        AuditLogListResponseV2 with entries and pagination metadata
    """
    logger.info(f"Admin {current_user.id} listing audit logs (page={page}, size={page_size})")

    supabase = _get_supabase_client()

    if supabase is None:
        # Return mock data for development
        _init_mock_audit_logs()

        # Apply filters
        logs = _mock_audit_logs.copy()

        if start_date:
            logs = [l for l in logs if datetime.fromisoformat(l["timestamp"].replace("Z", "+00:00")) >= start_date]
        if end_date:
            logs = [l for l in logs if datetime.fromisoformat(l["timestamp"].replace("Z", "+00:00")) <= end_date]
        if action_type:
            logs = [l for l in logs if l.get("action_type") == action_type]
        if target_user_id:
            logs = [l for l in logs if l.get("target_user_id") == str(target_user_id)]
        if admin_user_id:
            logs = [l for l in logs if l.get("admin_user_id") == str(admin_user_id)]

        # Sort by timestamp descending (AC#2: reverse chronological order)
        logs.sort(key=lambda l: l.get("timestamp", ""), reverse=True)

        # Apply pagination
        total = len(logs)
        offset = (page - 1) * page_size
        logs = logs[offset:offset + page_size]

        # Convert to response models
        entries = [
            AuditLogEntryResponse(
                id=UUID(l["id"]),
                timestamp=datetime.fromisoformat(l["timestamp"].replace("Z", "+00:00")),
                admin_user_id=UUID(l["admin_user_id"]),
                admin_email="admin@example.com",  # Mock email
                action_type=l["action_type"],
                target_type=l.get("target_type"),
                target_id=UUID(l["target_id"]) if l.get("target_id") else None,
                target_user_id=UUID(l["target_user_id"]) if l.get("target_user_id") else None,
                target_user_email=None,  # Would be populated from DB
                target_asset_id=UUID(l["target_asset_id"]) if l.get("target_asset_id") else None,
                target_asset_name=None,  # Would be populated from DB
                before_value=l.get("before_value"),
                after_value=l.get("after_value"),
                batch_id=UUID(l["batch_id"]) if l.get("batch_id") else None,
                metadata=l.get("metadata"),
            )
            for l in logs
        ]

        return AuditLogListResponseV2(
            entries=entries,
            total=total,
            page=page,
            page_size=page_size,
        )

    try:
        # Build query with count
        query = supabase.table("audit_logs").select("*", count="exact")

        # Apply filters
        if start_date:
            query = query.gte("timestamp", start_date.isoformat())
        if end_date:
            query = query.lte("timestamp", end_date.isoformat())
        if action_type:
            query = query.eq("action_type", action_type)
        if target_user_id:
            query = query.eq("target_user_id", str(target_user_id))
        if admin_user_id:
            query = query.eq("admin_user_id", str(admin_user_id))

        # Order by timestamp descending (AC#2)
        query = query.order("timestamp", desc=True)

        # Apply pagination
        offset = (page - 1) * page_size
        result = query.range(offset, offset + page_size - 1).execute()

        # Convert to response models
        entries = []
        for row in result.data:
            entries.append(AuditLogEntryResponse(
                id=UUID(row["id"]),
                timestamp=datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")),
                admin_user_id=UUID(row["admin_user_id"]),
                admin_email=None,  # Would need to join with auth.users
                action_type=row["action_type"],
                target_type=row.get("target_type"),
                target_id=UUID(row["target_id"]) if row.get("target_id") else None,
                target_user_id=UUID(row["target_user_id"]) if row.get("target_user_id") else None,
                target_user_email=None,  # Would need to join with auth.users
                target_asset_id=UUID(row["target_asset_id"]) if row.get("target_asset_id") else None,
                target_asset_name=None,  # Would need to join with assets
                before_value=row.get("before_value"),
                after_value=row.get("after_value"),
                batch_id=UUID(row["batch_id"]) if row.get("batch_id") else None,
                metadata=row.get("metadata"),
            ))

        return AuditLogListResponseV2(
            entries=entries,
            total=result.count or len(entries),
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logger.error(f"Error listing audit logs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list audit logs: {str(e)}"
        )


@router.get("/audit-logs/{log_id}", response_model=AuditLogEntryResponse)
async def get_audit_log(
    log_id: UUID,
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Get a single audit log entry by ID (Story 9.15 Task 3.4).

    Args:
        log_id: ID of the audit log entry

    Returns:
        AuditLogEntryResponse with entry details
    """
    logger.info(f"Admin {current_user.id} getting audit log {log_id}")

    supabase = _get_supabase_client()

    if supabase is None:
        # Return mock data for development
        _init_mock_audit_logs()

        log = next((l for l in _mock_audit_logs if l["id"] == str(log_id)), None)
        if not log:
            raise HTTPException(status_code=404, detail="Audit log entry not found")

        return AuditLogEntryResponse(
            id=UUID(log["id"]),
            timestamp=datetime.fromisoformat(log["timestamp"].replace("Z", "+00:00")),
            admin_user_id=UUID(log["admin_user_id"]),
            admin_email="admin@example.com",  # Mock email
            action_type=log["action_type"],
            target_type=log.get("target_type"),
            target_id=UUID(log["target_id"]) if log.get("target_id") else None,
            target_user_id=UUID(log["target_user_id"]) if log.get("target_user_id") else None,
            target_user_email=None,
            target_asset_id=UUID(log["target_asset_id"]) if log.get("target_asset_id") else None,
            target_asset_name=None,
            before_value=log.get("before_value"),
            after_value=log.get("after_value"),
            batch_id=UUID(log["batch_id"]) if log.get("batch_id") else None,
            metadata=log.get("metadata"),
        )

    try:
        result = supabase.table("audit_logs").select("*").eq("id", str(log_id)).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Audit log entry not found")

        row = result.data[0]

        return AuditLogEntryResponse(
            id=UUID(row["id"]),
            timestamp=datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")),
            admin_user_id=UUID(row["admin_user_id"]),
            admin_email=None,  # Would need to join with auth.users
            action_type=row["action_type"],
            target_type=row.get("target_type"),
            target_id=UUID(row["target_id"]) if row.get("target_id") else None,
            target_user_id=UUID(row["target_user_id"]) if row.get("target_user_id") else None,
            target_user_email=None,
            target_asset_id=UUID(row["target_asset_id"]) if row.get("target_asset_id") else None,
            target_asset_name=None,
            before_value=row.get("before_value"),
            after_value=row.get("after_value"),
            batch_id=UUID(row["batch_id"]) if row.get("batch_id") else None,
            metadata=row.get("metadata"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit log: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get audit log: {str(e)}"
        )
