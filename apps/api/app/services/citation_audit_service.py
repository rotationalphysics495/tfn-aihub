"""
Citation Audit Service (Story 4.5)

Service for logging citation-response pairs for NFR1 compliance review.

AC#7: NFR1 Compliance Validation
  - Audit log records all citation-response pairs for compliance review
  - Grounding failures trigger alert for manual review

AC#8: Performance Requirements
  - Async logging to avoid impacting response time
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.models.citation import (
    Citation,
    CitedResponse,
    CitationLogEntry,
    GROUNDING_THRESHOLD_MIN,
)

logger = logging.getLogger(__name__)


class CitationAuditServiceError(Exception):
    """Base exception for Citation Audit Service errors."""
    pass


class CitationAuditService:
    """
    Service for audit logging of citation-response pairs.

    Story 4.5 Implementation:
    - AC#7: Records all citation-response pairs for compliance
    - AC#7: Triggers alerts for low grounding scores
    - AC#8: Uses async logging to minimize latency impact
    """

    def __init__(self):
        """Initialize the Citation Audit Service."""
        self._settings = None
        self._log_queue: List[CitationLogEntry] = []
        self._flush_task: Optional[asyncio.Task] = None

    def _get_settings(self):
        """Get cached settings."""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    async def log_citation_response(
        self,
        response: CitedResponse,
        user_id: str,
        query_text: str,
        session_id: Optional[str] = None,
    ) -> str:
        """
        Log a cited response for audit trail.

        AC#7: Audit log records all citation-response pairs.

        Args:
            response: The cited response to log
            user_id: User who made the query
            query_text: Original user query
            session_id: Optional session identifier

        Returns:
            Log entry ID
        """
        log_entry = CitationLogEntry(
            id=f"log-{uuid.uuid4().hex[:12]}",
            response_id=response.id,
            user_id=user_id,
            session_id=session_id,
            query_text=query_text,
            response_text=response.response_text,
            citations=[c.model_dump() for c in response.citations],
            grounding_score=response.grounding_score,
            ungrounded_claims=response.ungrounded_claims,
            validated_at=datetime.utcnow().isoformat(),
            created_at=datetime.utcnow().isoformat(),
        )

        # Add to queue for async flush
        self._log_queue.append(log_entry)

        # Check for low grounding alert
        if response.grounding_score < GROUNDING_THRESHOLD_MIN:
            await self._trigger_low_grounding_alert(log_entry)

        # Schedule flush if queue is getting large
        if len(self._log_queue) >= 10:
            await self._flush_logs()

        logger.debug(f"Logged citation response: {log_entry.id}")
        return log_entry.id

    async def log_citation_entry(
        self,
        response_id: str,
        user_id: str,
        query_text: str,
        response_text: str,
        citations: List[Citation],
        grounding_score: float,
        ungrounded_claims: List[str],
        session_id: Optional[str] = None,
    ) -> str:
        """
        Log a citation entry with individual parameters.

        Convenience method when CitedResponse is not available.

        Args:
            response_id: Response identifier
            user_id: User who made the query
            query_text: Original user query
            response_text: Generated response text
            citations: List of citations
            grounding_score: Overall grounding score
            ungrounded_claims: Claims without grounding
            session_id: Optional session identifier

        Returns:
            Log entry ID
        """
        log_entry = CitationLogEntry(
            id=f"log-{uuid.uuid4().hex[:12]}",
            response_id=response_id,
            user_id=user_id,
            session_id=session_id,
            query_text=query_text,
            response_text=response_text,
            citations=[c.model_dump() for c in citations],
            grounding_score=grounding_score,
            ungrounded_claims=ungrounded_claims,
            validated_at=datetime.utcnow().isoformat(),
            created_at=datetime.utcnow().isoformat(),
        )

        self._log_queue.append(log_entry)

        if grounding_score < GROUNDING_THRESHOLD_MIN:
            await self._trigger_low_grounding_alert(log_entry)

        if len(self._log_queue) >= 10:
            await self._flush_logs()

        logger.debug(f"Logged citation entry: {log_entry.id}")
        return log_entry.id

    async def _trigger_low_grounding_alert(
        self,
        log_entry: CitationLogEntry,
    ) -> None:
        """
        Trigger an alert for low grounding score.

        AC#7: Grounding failures trigger alert for manual review.

        Args:
            log_entry: The log entry with low grounding
        """
        alert_data = {
            "alert_type": "low_grounding_score",
            "severity": "warning",
            "message": f"Response {log_entry.response_id} has low grounding score: {log_entry.grounding_score:.2f}",
            "metadata": {
                "response_id": log_entry.response_id,
                "grounding_score": log_entry.grounding_score,
                "user_id": log_entry.user_id,
                "ungrounded_claims_count": len(log_entry.ungrounded_claims),
                "query_preview": log_entry.query_text[:200] if log_entry.query_text else "",
            }
        }

        # Log the alert - in production this would insert into system_alerts table
        logger.warning(
            f"Low grounding alert: score={log_entry.grounding_score:.2f}, "
            f"response_id={log_entry.response_id}, "
            f"ungrounded_claims={len(log_entry.ungrounded_claims)}"
        )

        # For now, the alert is triggered by the database trigger on citation_logs
        # This is just logging for visibility

    async def _flush_logs(self) -> None:
        """
        Flush pending log entries to the database.

        AC#8: Async flush to minimize latency impact.
        """
        if not self._log_queue:
            return

        entries_to_flush = self._log_queue.copy()
        self._log_queue.clear()

        try:
            # In production, this would batch insert into Supabase citation_logs table
            # For now, we just log that we would persist these entries
            logger.info(f"Flushing {len(entries_to_flush)} citation log entries to database")

            # The actual insert would look like:
            # async with get_supabase_client() as client:
            #     await client.table("citation_logs").insert([
            #         entry.model_dump() for entry in entries_to_flush
            #     ])

        except Exception as e:
            logger.error(f"Failed to flush citation logs: {e}")
            # Re-queue failed entries
            self._log_queue.extend(entries_to_flush)

    async def get_audit_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get audit summary statistics.

        Args:
            start_date: Start of period
            end_date: End of period
            user_id: Filter by user

        Returns:
            Dict with summary statistics
        """
        # In production, this would query the database using get_citation_audit_summary()
        # For now, return from in-memory queue

        entries = self._log_queue
        if user_id:
            entries = [e for e in entries if e.user_id == user_id]

        if not entries:
            return {
                "total_responses": 0,
                "avg_grounding_score": 0.0,
                "low_grounding_count": 0,
                "fully_grounded_count": 0,
                "total_citations": 0,
                "avg_citations_per_response": 0.0,
            }

        total = len(entries)
        avg_score = sum(e.grounding_score for e in entries) / total
        low_count = sum(1 for e in entries if e.grounding_score < GROUNDING_THRESHOLD_MIN)
        high_count = sum(1 for e in entries if e.grounding_score >= 0.8)
        total_citations = sum(len(e.citations) for e in entries)

        return {
            "total_responses": total,
            "avg_grounding_score": round(avg_score, 2),
            "low_grounding_count": low_count,
            "fully_grounded_count": high_count,
            "total_citations": total_citations,
            "avg_citations_per_response": round(total_citations / total, 2) if total > 0 else 0,
        }

    async def get_low_grounding_entries(
        self,
        limit: int = 20,
    ) -> List[CitationLogEntry]:
        """
        Get recent entries with low grounding scores.

        Useful for manual review of grounding failures.

        Args:
            limit: Maximum entries to return

        Returns:
            List of log entries with low grounding
        """
        low_entries = [
            e for e in self._log_queue
            if e.grounding_score < GROUNDING_THRESHOLD_MIN
        ]

        # Sort by grounding score (lowest first)
        low_entries.sort(key=lambda e: e.grounding_score)

        return low_entries[:limit]

    def clear_queue(self) -> None:
        """Clear the log queue (for testing)."""
        self._log_queue.clear()
        self._settings = None
        logger.debug("Citation audit service queue cleared")


# Module-level singleton instance
_citation_audit_service: Optional[CitationAuditService] = None


def get_citation_audit_service() -> CitationAuditService:
    """
    Get the singleton CitationAuditService instance.

    Returns:
        CitationAuditService singleton instance
    """
    global _citation_audit_service
    if _citation_audit_service is None:
        _citation_audit_service = CitationAuditService()
    return _citation_audit_service
