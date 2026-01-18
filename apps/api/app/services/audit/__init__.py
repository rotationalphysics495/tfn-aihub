"""
Audit Logging Service (Story 9.13, 9.14, 9.15)

Provides audit logging for admin configuration changes.

Story 9.15 adds:
- log_action() - Primary method for logging to unified audit_logs table
- log_batch_start() - Generate batch_id for linking operations

References:
- [Source: prd/prd-functional-requirements.md#FR50, FR55, FR56]
- [Source: prd/prd-non-functional-requirements.md#NFR25]
"""
from app.services.audit.logger import (
    AuditLogger,
    log_assignment_change,
    log_batch_assignment_change,
    log_role_change,
    log_action,
    log_batch_start,
    get_audit_logger,
)

__all__ = [
    "AuditLogger",
    "log_assignment_change",
    "log_batch_assignment_change",
    "log_role_change",
    "log_action",
    "log_batch_start",
    "get_audit_logger",
]
