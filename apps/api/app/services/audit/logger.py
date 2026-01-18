"""
Audit Logging Service (Story 9.13, Task 4)

Provides audit logging for admin configuration changes.

AC#3: Audit log entry is created for all write operations
AC#4: Include batch_id for bulk operations

Features:
- Immutable append-only audit log
- Captures before/after states for updates
- Groups batch operations with batch_id
- Stores admin user ID and timestamp

References:
- [Source: prd/prd-functional-requirements.md#FR50, FR56]
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from supabase import Client, create_client

from app.core.config import get_settings
from app.models.admin import (
    AuditActionType,
    AuditEntityType,
    AuditLogEntry,
    AssignmentChange,
)

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Audit logging service for admin operations (Task 4.1).

    All methods are designed to be non-blocking and fail gracefully
    to avoid disrupting the main operation.
    """

    def __init__(self, supabase_client: Optional[Client] = None):
        """Initialize with optional Supabase client."""
        self._client = supabase_client
        self._in_memory_logs: List[Dict[str, Any]] = []

    def _get_client(self) -> Optional[Client]:
        """Get Supabase client lazily."""
        if self._client is not None:
            return self._client

        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_key:
            return None

        try:
            self._client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            return self._client
        except Exception as e:
            logger.warning(f"Failed to create Supabase client for audit: {e}")
            return None

    def _store_log(self, log_data: Dict[str, Any]) -> Optional[UUID]:
        """
        Store audit log entry (Task 4.2).

        Attempts to store in Supabase, falls back to in-memory for testing.
        """
        client = self._get_client()

        if client is None:
            # Store in memory for testing/development
            log_id = uuid4()
            log_data["id"] = str(log_id)
            self._in_memory_logs.append(log_data)
            logger.info(f"Stored audit log in memory: {log_data['action_type']}")
            return log_id

        try:
            result = client.table("admin_audit_logs").insert(log_data).execute()
            if result.data and len(result.data) > 0:
                log_id = UUID(result.data[0]["id"])
                logger.info(
                    f"Stored audit log {log_id}: {log_data['action_type']} "
                    f"on {log_data['entity_type']}"
                )
                return log_id
        except Exception as e:
            # Audit logging should never fail the main operation
            logger.error(f"Failed to store audit log: {e}")
            # Fallback to in-memory
            log_id = uuid4()
            log_data["id"] = str(log_id)
            self._in_memory_logs.append(log_data)
            return log_id

        return None

    def log_assignment_change(
        self,
        action_type: AuditActionType,
        admin_user_id: str,
        target_user_id: str,
        asset_id: str,
        assignment_id: Optional[str] = None,
        state_before: Optional[Dict[str, Any]] = None,
        state_after: Optional[Dict[str, Any]] = None,
        batch_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[UUID]:
        """
        Log a single assignment change (Task 4.2).

        Args:
            action_type: Type of action (created, deleted, updated)
            admin_user_id: ID of admin performing the action
            target_user_id: ID of supervisor being assigned/unassigned
            asset_id: ID of asset being assigned
            assignment_id: ID of the assignment record
            state_before: State before the change (for updates/deletes)
            state_after: State after the change (for creates/updates)
            batch_id: ID grouping batch operations
            metadata: Additional context

        Returns:
            UUID of created audit log entry, or None if failed
        """
        now = datetime.now(timezone.utc)

        log_data = {
            "action_type": action_type.value,
            "entity_type": AuditEntityType.SUPERVISOR_ASSIGNMENT.value,
            "entity_id": assignment_id,
            "admin_user_id": admin_user_id,
            "target_user_id": target_user_id,
            "state_before": state_before,
            "state_after": state_after,
            "batch_id": batch_id,
            "metadata": {
                **(metadata or {}),
                "asset_id": asset_id,
            },
            "created_at": now.isoformat(),
        }

        return self._store_log(log_data)

    def log_batch_assignment_change(
        self,
        admin_user_id: str,
        changes: List[AssignmentChange],
        results: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """
        Log a batch assignment change (Task 4.4).

        Creates a single batch log entry plus individual entries for each change.

        Args:
            admin_user_id: ID of admin performing the batch operation
            changes: List of changes that were requested
            results: List of results for each change
            metadata: Additional context

        Returns:
            UUID of the batch_id used to group the operations
        """
        batch_id = uuid4()
        now = datetime.now(timezone.utc)

        # Log the batch operation summary
        batch_log = {
            "action_type": AuditActionType.BATCH_UPDATE.value,
            "entity_type": AuditEntityType.SUPERVISOR_ASSIGNMENT.value,
            "entity_id": None,  # Batch operation, no single entity
            "admin_user_id": admin_user_id,
            "target_user_id": None,
            "state_before": None,
            "state_after": {
                "changes_requested": len(changes),
                "changes_applied": len([r for r in results if r.get("success")]),
            },
            "batch_id": str(batch_id),
            "metadata": {
                **(metadata or {}),
                "changes_summary": [
                    {
                        "user_id": str(c.user_id),
                        "asset_id": str(c.asset_id),
                        "action": c.action.value,
                    }
                    for c in changes
                ],
            },
            "created_at": now.isoformat(),
        }
        self._store_log(batch_log)

        # Log individual changes with the same batch_id
        for change, result in zip(changes, results):
            if result.get("success"):
                action_type = (
                    AuditActionType.ASSIGNMENT_CREATED
                    if change.action.value == "add"
                    else AuditActionType.ASSIGNMENT_DELETED
                )
                self.log_assignment_change(
                    action_type=action_type,
                    admin_user_id=admin_user_id,
                    target_user_id=str(change.user_id),
                    asset_id=str(change.asset_id),
                    assignment_id=result.get("assignment_id"),
                    state_before=result.get("state_before"),
                    state_after=result.get("state_after"),
                    batch_id=str(batch_id),
                    metadata={"expires_at": str(change.expires_at) if change.expires_at else None},
                )

        logger.info(
            f"Logged batch assignment change: {len(changes)} changes "
            f"({len([r for r in results if r.get('success')])} successful)"
        )

        return batch_id

    def log_role_change(
        self,
        admin_user_id: str,
        target_user_id: str,
        old_role: str,
        new_role: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[UUID]:
        """
        Log a role change to the audit_logs table (Story 9.14 AC#2, Task 5.2).

        Uses the separate audit_logs table for FR56 compliance.

        Args:
            admin_user_id: ID of admin performing the change
            target_user_id: ID of user whose role is being changed
            old_role: Previous role value
            new_role: New role value
            metadata: Additional context

        Returns:
            UUID of created audit log entry, or None if failed
        """
        now = datetime.now(timezone.utc)

        log_data = {
            "admin_user_id": admin_user_id,
            "action_type": AuditActionType.ROLE_CHANGE.value,
            "target_user_id": target_user_id,
            "before_value": {"role": old_role},
            "after_value": {"role": new_role},
            "metadata": metadata or {},
            "timestamp": now.isoformat(),
        }

        client = self._get_client()

        if client is None:
            # Store in memory for testing/development
            log_id = uuid4()
            log_data["id"] = str(log_id)
            self._in_memory_logs.append(log_data)
            logger.info(f"Stored role change audit log in memory: {old_role} -> {new_role}")
            return log_id

        try:
            # Use the audit_logs table for role changes (FR56)
            result = client.table("audit_logs").insert(log_data).execute()
            if result.data and len(result.data) > 0:
                log_id = UUID(result.data[0]["id"])
                logger.info(
                    f"Stored role change audit log {log_id}: "
                    f"{old_role} -> {new_role} for user {target_user_id}"
                )
                return log_id
        except Exception as e:
            # Audit logging should never fail the main operation
            logger.error(f"Failed to store role change audit log: {e}")
            # Fallback to in-memory
            log_id = uuid4()
            log_data["id"] = str(log_id)
            self._in_memory_logs.append(log_data)
            return log_id

        return None

    def get_logs(
        self,
        entity_type: Optional[AuditEntityType] = None,
        admin_user_id: Optional[str] = None,
        target_user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AuditLogEntry]:
        """
        Retrieve audit logs with optional filtering (Task 4.5).

        Args:
            entity_type: Filter by entity type
            admin_user_id: Filter by admin who performed the action
            target_user_id: Filter by affected user
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of audit log entries
        """
        client = self._get_client()

        if client is None:
            # Return from in-memory for testing
            logs = self._in_memory_logs.copy()

            if entity_type:
                logs = [l for l in logs if l.get("entity_type") == entity_type.value]
            if admin_user_id:
                logs = [l for l in logs if l.get("admin_user_id") == admin_user_id]
            if target_user_id:
                logs = [l for l in logs if l.get("target_user_id") == target_user_id]

            # Sort by created_at descending
            logs.sort(key=lambda l: l.get("created_at", ""), reverse=True)
            logs = logs[offset:offset + limit]

            return [
                AuditLogEntry(
                    id=UUID(l["id"]),
                    action_type=AuditActionType(l["action_type"]),
                    entity_type=AuditEntityType(l["entity_type"]),
                    entity_id=UUID(l["entity_id"]) if l.get("entity_id") else None,
                    admin_user_id=UUID(l["admin_user_id"]),
                    target_user_id=UUID(l["target_user_id"]) if l.get("target_user_id") else None,
                    state_before=l.get("state_before"),
                    state_after=l.get("state_after"),
                    batch_id=UUID(l["batch_id"]) if l.get("batch_id") else None,
                    metadata=l.get("metadata"),
                    created_at=datetime.fromisoformat(l["created_at"].replace("Z", "+00:00")),
                )
                for l in logs
            ]

        try:
            query = client.table("admin_audit_logs").select("*")

            if entity_type:
                query = query.eq("entity_type", entity_type.value)
            if admin_user_id:
                query = query.eq("admin_user_id", admin_user_id)
            if target_user_id:
                query = query.eq("target_user_id", target_user_id)

            query = query.order("created_at", desc=True)
            query = query.range(offset, offset + limit - 1)

            result = query.execute()

            return [
                AuditLogEntry(
                    id=UUID(row["id"]),
                    action_type=AuditActionType(row["action_type"]),
                    entity_type=AuditEntityType(row["entity_type"]),
                    entity_id=UUID(row["entity_id"]) if row.get("entity_id") else None,
                    admin_user_id=UUID(row["admin_user_id"]),
                    target_user_id=UUID(row["target_user_id"]) if row.get("target_user_id") else None,
                    state_before=row.get("state_before"),
                    state_after=row.get("state_after"),
                    batch_id=UUID(row["batch_id"]) if row.get("batch_id") else None,
                    metadata=row.get("metadata"),
                    created_at=datetime.fromisoformat(
                        row["created_at"].replace("Z", "+00:00")
                    ),
                )
                for row in result.data
            ]
        except Exception as e:
            logger.error(f"Failed to retrieve audit logs: {e}")
            return []


# Module-level singleton
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the singleton audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def log_assignment_change(
    action_type: AuditActionType,
    admin_user_id: str,
    target_user_id: str,
    asset_id: str,
    assignment_id: Optional[str] = None,
    state_before: Optional[Dict[str, Any]] = None,
    state_after: Optional[Dict[str, Any]] = None,
    batch_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Optional[UUID]:
    """Convenience function to log assignment change using singleton."""
    return get_audit_logger().log_assignment_change(
        action_type=action_type,
        admin_user_id=admin_user_id,
        target_user_id=target_user_id,
        asset_id=asset_id,
        assignment_id=assignment_id,
        state_before=state_before,
        state_after=state_after,
        batch_id=batch_id,
        metadata=metadata,
    )


def log_batch_assignment_change(
    admin_user_id: str,
    changes: List[AssignmentChange],
    results: List[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None,
) -> UUID:
    """Convenience function to log batch change using singleton."""
    return get_audit_logger().log_batch_assignment_change(
        admin_user_id=admin_user_id,
        changes=changes,
        results=results,
        metadata=metadata,
    )


def log_role_change(
    admin_user_id: str,
    target_user_id: str,
    old_role: str,
    new_role: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Optional[UUID]:
    """
    Log a role change to the audit_logs table (Story 9.14 AC#2).

    Args:
        admin_user_id: ID of admin performing the change
        target_user_id: ID of user whose role is being changed
        old_role: Previous role value
        new_role: New role value
        metadata: Additional context

    Returns:
        UUID of created audit log entry, or None if failed
    """
    return get_audit_logger().log_role_change(
        admin_user_id=admin_user_id,
        target_user_id=target_user_id,
        old_role=old_role,
        new_role=new_role,
        metadata=metadata,
    )
