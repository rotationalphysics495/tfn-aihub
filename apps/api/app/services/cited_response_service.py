"""
Cited Response Service (Story 4.5)

High-level service for generating AI responses with citations.
Integrates grounding validation, citation generation, and audit logging.

This service is the main entry point for Story 4.5 functionality.

AC#1: Response Citation Format
AC#2: Data Source Integration
AC#3: Grounding Validation
AC#5: Multi-Source Response Synthesis
AC#6: Mem0 Memory Citations
AC#7: NFR1 Compliance Validation
AC#8: Performance Requirements
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from app.core.config import get_settings
from app.models.citation import (
    Citation,
    CitedResponse,
    Claim,
    SourceType,
    GROUNDING_THRESHOLD_MIN,
)
from app.services.grounding_service import (
    GroundingService,
    get_grounding_service,
)
from app.services.citation_generator import (
    CitationGenerator,
    get_citation_generator,
)
from app.services.citation_audit_service import (
    CitationAuditService,
    get_citation_audit_service,
)
from app.services.mem0_asset_service import (
    Mem0AssetService,
    get_mem0_asset_service,
)
from app.services.memory.mem0_service import (
    MemoryService,
    get_memory_service,
)

logger = logging.getLogger(__name__)


class CitedResponseServiceError(Exception):
    """Base exception for Cited Response Service errors."""
    pass


class CitedResponseService:
    """
    Main service for generating cited AI responses.

    Orchestrates:
    - Grounding validation (claim extraction and validation)
    - Citation generation (database and memory sources)
    - Response formatting (inline citation injection)
    - Audit logging (NFR1 compliance)

    Story 4.5 Implementation:
    - AC#1-8: Full cited response generation pipeline
    """

    def __init__(self):
        """Initialize the Cited Response Service."""
        self._settings = None
        self._grounding_service: Optional[GroundingService] = None
        self._citation_generator: Optional[CitationGenerator] = None
        self._audit_service: Optional[CitationAuditService] = None
        self._mem0_asset_service: Optional[Mem0AssetService] = None
        self._memory_service: Optional[MemoryService] = None
        self._initialized = False

    def _get_settings(self):
        """Get cached settings."""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    def initialize(self) -> bool:
        """
        Initialize all dependent services.

        Returns:
            True if initialization successful
        """
        if self._initialized:
            return True

        try:
            self._grounding_service = get_grounding_service()
            self._citation_generator = get_citation_generator()
            self._audit_service = get_citation_audit_service()
            self._mem0_asset_service = get_mem0_asset_service()
            self._memory_service = get_memory_service()

            self._initialized = True
            logger.info("Cited Response Service initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Cited Response Service: {e}")
            return False

    def _ensure_initialized(self) -> None:
        """Ensure the service is initialized."""
        if not self._initialized:
            if not self.initialize():
                raise CitedResponseServiceError(
                    "Cited Response Service could not be initialized"
                )

    async def generate_cited_response(
        self,
        raw_response: str,
        query_text: str,
        user_id: str,
        query_results: Optional[List[Dict[str, Any]]] = None,
        source_table: Optional[str] = None,
        asset_id: Optional[str] = None,
        session_id: Optional[str] = None,
        include_memory_context: bool = True,
    ) -> CitedResponse:
        """
        Generate a cited response from a raw AI response.

        This is the main entry point for Story 4.5 functionality.

        AC#1: All AI responses include inline citations
        AC#2: Citations link to actual database records
        AC#3: Grounding validation with threshold
        AC#5: Multi-source response synthesis
        AC#6: Mem0 memory citations
        AC#7: Audit logging
        AC#8: Performance requirements (< 500ms additional latency)

        Args:
            raw_response: The AI-generated response text
            query_text: Original user query
            user_id: User identifier
            query_results: Database query results for citation
            source_table: Source table name for database citations
            asset_id: Optional asset ID for asset-specific context
            session_id: Optional session identifier
            include_memory_context: Whether to include Mem0 memory citations

        Returns:
            CitedResponse with grounding score and citations
        """
        self._ensure_initialized()
        start_time = time.time()

        response_id = f"resp-{uuid.uuid4().hex[:12]}"

        try:
            # Gather all available sources for citation
            available_sources = []
            memory_sources = []

            # Add query results as sources
            if query_results:
                for result in query_results:
                    # Tag with source table for citation generation
                    result["_source_table"] = source_table or "query_results"
                    result["_record_id"] = result.get("id", str(uuid.uuid4()))
                    available_sources.append(result)

            # Gather memory sources if requested
            if include_memory_context:
                memory_sources = await self._gather_memory_sources(
                    query_text=query_text,
                    user_id=user_id,
                    asset_id=asset_id,
                )

            # Step 1: Validate grounding and generate citations
            grounding_start = time.time()
            cited_response = await self._grounding_service.validate_response(
                response_text=raw_response,
                available_sources=available_sources,
                memory_sources=memory_sources,
            )
            grounding_time = (time.time() - grounding_start) * 1000

            # Step 2: Enhance citations with additional context
            enhanced_citations = await self._enhance_citations(
                cited_response.citations,
                query_results or [],
                source_table,
            )

            # Step 3: Generate additional citations from query results
            if query_results and source_table:
                result_citations = self._citation_generator.generate_citations_from_query_results(
                    query_results=query_results,
                    source_table=source_table,
                    claim_text=None,  # Will be matched during formatting
                )
                # Merge with grounding citations, avoiding duplicates
                existing_ids = {c.record_id for c in enhanced_citations if c.record_id}
                for rc in result_citations:
                    if rc.record_id not in existing_ids:
                        enhanced_citations.append(rc)

            # Step 4: Select and aggregate citations
            final_citations = self._citation_generator.aggregate_citations(
                citations=enhanced_citations,
                max_citations=10,
            )

            # Step 5: Format response with inline citations
            formatted_text, used_citations = self._citation_generator.format_citations_for_response(
                response_text=cited_response.response_text,
                citations=final_citations,
                inline=True,
            )

            # Step 6: Handle low grounding with fallback
            if cited_response.grounding_score < GROUNDING_THRESHOLD_MIN:
                formatted_text = self._grounding_service.generate_fallback_response(
                    original_response=formatted_text,
                    grounding_score=cited_response.grounding_score,
                    ungrounded_claims=cited_response.ungrounded_claims,
                )

            total_time = (time.time() - start_time) * 1000

            # Build final response
            final_response = CitedResponse(
                id=response_id,
                response_text=formatted_text,
                citations=used_citations or final_citations,
                claims=cited_response.claims,
                grounding_score=cited_response.grounding_score,
                ungrounded_claims=cited_response.ungrounded_claims,
                meta={
                    "response_time_ms": round(total_time, 2),
                    "grounding_time_ms": round(grounding_time, 2),
                    "citation_count": len(final_citations),
                    "claim_count": len(cited_response.claims),
                    "groundable_claim_count": sum(1 for c in cited_response.claims if c.requires_grounding),
                    "ungrounded_claim_count": len(cited_response.ungrounded_claims),
                    "memory_sources_used": len(memory_sources),
                    "database_sources_used": len(available_sources),
                }
            )

            # Step 7: Log for audit (async, non-blocking)
            asyncio.create_task(
                self._audit_service.log_citation_response(
                    response=final_response,
                    user_id=user_id,
                    query_text=query_text,
                    session_id=session_id,
                )
            )

            logger.info(
                f"Generated cited response: id={response_id}, "
                f"grounding_score={final_response.grounding_score:.2f}, "
                f"citations={len(final_citations)}, "
                f"time={total_time:.0f}ms"
            )

            return final_response

        except Exception as e:
            logger.error(f"Failed to generate cited response: {e}")
            # Return minimal response on error
            return CitedResponse(
                id=response_id,
                response_text=raw_response,
                citations=[],
                claims=[],
                grounding_score=0.0,
                ungrounded_claims=["Error during citation generation"],
                meta={
                    "error": str(e),
                    "response_time_ms": (time.time() - start_time) * 1000,
                }
            )

    async def _gather_memory_sources(
        self,
        query_text: str,
        user_id: str,
        asset_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Gather memory sources from Mem0 for citation.

        AC#6: Mem0 memory citations with provenance.
        """
        memory_sources = []

        try:
            # Get user memories
            if self._memory_service.is_configured():
                user_memories = await self._memory_service.search_memory(
                    query=query_text,
                    user_id=user_id,
                    limit=3,
                )
                memory_sources.extend(user_memories)

            # Get asset-specific memories if asset_id provided
            if asset_id and self._mem0_asset_service.is_configured():
                asset_memories = await self._mem0_asset_service.retrieve_memories_with_provenance(
                    asset_id=UUID(asset_id),
                    query=query_text,
                    limit=3,
                )
                memory_sources.extend(asset_memories)

        except Exception as e:
            logger.warning(f"Failed to gather memory sources: {e}")

        return memory_sources

    async def _enhance_citations(
        self,
        citations: List[Citation],
        query_results: List[Dict[str, Any]],
        source_table: Optional[str],
    ) -> List[Citation]:
        """
        Enhance citations with additional metadata from query results.
        """
        if not query_results or not source_table:
            return citations

        enhanced = []
        for cit in citations:
            # Try to find matching record in query results
            if cit.source_type == SourceType.DATABASE and not cit.source_table:
                cit.source_table = source_table

            # Add asset name if available
            for result in query_results:
                if result.get("id") == cit.record_id:
                    if result.get("asset_name") and not cit.asset_id:
                        cit.asset_id = result.get("asset_id")
                    break

            enhanced.append(cit)

        return enhanced

    async def process_chat_response(
        self,
        raw_response: str,
        query_text: str,
        user_id: str,
        sql: Optional[str] = None,
        data: Optional[List[Dict[str, Any]]] = None,
        source_table: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a chat response and add citations.

        This method is designed to integrate with the existing chat API.
        It takes the output from Text-to-SQL and adds citation/grounding.

        Args:
            raw_response: The natural language answer
            query_text: Original user question
            user_id: User identifier
            sql: The SQL query that was executed
            data: Query results
            source_table: Source table for citations
            context: Additional context (asset_focus, session_id, etc.)

        Returns:
            Dict compatible with existing QueryResponse format but with enhanced citations
        """
        context = context or {}
        asset_id = context.get("asset_id") or context.get("asset_focus")
        session_id = context.get("session_id")

        # Generate cited response
        cited_response = await self.generate_cited_response(
            raw_response=raw_response,
            query_text=query_text,
            user_id=user_id,
            query_results=data,
            source_table=source_table,
            asset_id=str(asset_id) if asset_id else None,
            session_id=session_id,
            include_memory_context=True,
        )

        # Convert citations to format compatible with existing Citation model
        formatted_citations = []
        for cit in cited_response.citations:
            formatted_citations.append({
                "value": cit.excerpt[:50] if cit.excerpt else "",
                "field": cit.source_table or "memory" if cit.source_type == SourceType.MEMORY else "value",
                "table": cit.source_table or "memories",
                "context": cit.display_text,
                # Extended fields for Story 4.5
                "id": cit.id,
                "source_type": cit.source_type.value,
                "record_id": cit.record_id,
                "memory_id": cit.memory_id,
                "confidence": cit.confidence,
            })

        return {
            "answer": cited_response.response_text,
            "sql": sql,
            "data": data or [],
            "citations": formatted_citations,
            "grounding_score": cited_response.grounding_score,
            "ungrounded_claims": cited_response.ungrounded_claims,
            "meta": cited_response.meta,
        }

    def is_configured(self) -> bool:
        """Check if the service is properly configured."""
        return True  # No special configuration required

    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._initialized


# Module-level singleton instance
_cited_response_service: Optional[CitedResponseService] = None


def get_cited_response_service() -> CitedResponseService:
    """
    Get the singleton CitedResponseService instance.

    Returns:
        CitedResponseService singleton instance
    """
    global _cited_response_service
    if _cited_response_service is None:
        _cited_response_service = CitedResponseService()
    return _cited_response_service
