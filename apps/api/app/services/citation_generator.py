"""
Citation Generator Service (Story 4.5)

Service for generating citations from database records and Mem0 memories.
Integrates with LangChain response chain to inject citation context.

AC#1: Response Citation Format
  - All AI responses include inline citations linking claims to specific data sources
  - Citations follow format: [Source: table_name/record_id] or [Evidence: metric_name at timestamp]
  - Each factual claim is grounded with at least one verifiable citation

AC#2: Data Source Integration
  - Citations link to actual database records (daily_summaries, live_snapshots, safety_events)
  - Asset-specific claims cite the specific asset_id and relevant timestamp
  - Financial impact claims cite cost_centers data and calculation basis

AC#5: Multi-Source Response Synthesis
  - Responses can cite multiple sources when synthesizing insights
  - Cross-reference validation ensures cited sources support the claim
  - Primary source is indicated when multiple sources support same claim

AC#8: Performance Requirements
  - Citation generation adds no more than 500ms to response time
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import get_settings
from app.models.citation import (
    Citation,
    SourceType,
    GROUNDING_THRESHOLD_MIN,
)

logger = logging.getLogger(__name__)


class CitationGeneratorError(Exception):
    """Base exception for Citation Generator errors."""
    pass


class SourceNotFoundError(CitationGeneratorError):
    """Raised when source data cannot be found."""
    pass


class CitationGenerator:
    """
    Service for generating citations from various data sources.

    Story 4.5 Implementation:
    - AC#1: Generates inline citations in specified format
    - AC#2: Integrates with database tables and Mem0 memories
    - AC#5: Supports multi-source citation aggregation
    - AC#8: Optimized for performance (< 500ms)
    """

    # Table descriptions for citation context
    TABLE_DESCRIPTIONS = {
        "daily_summaries": "Daily OEE and production metrics",
        "live_snapshots": "Real-time production status",
        "safety_events": "Safety incidents and events",
        "cost_centers": "Financial and cost allocation data",
        "assets": "Manufacturing equipment and machines",
        "asset_history": "Historical events and resolutions",
    }

    # Metric formatters
    PERCENTAGE_METRICS = {"oee_percentage", "efficiency", "rate", "percentage"}
    CURRENCY_METRICS = {"financial_loss_dollars", "standard_hourly_rate", "cost", "loss"}
    COUNT_METRICS = {"downtime_minutes", "actual_output", "target_output", "waste_count"}

    def __init__(self):
        """Initialize the Citation Generator."""
        self._settings = None
        self._citation_cache: Dict[str, Citation] = {}

    def _get_settings(self):
        """Get cached settings."""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    def generate_citation_from_record(
        self,
        record: Dict[str, Any],
        source_table: str,
        claim_text: Optional[str] = None,
        confidence: float = 0.9,
    ) -> Citation:
        """
        Generate a citation from a database record.

        AC#1: Citations follow format [Source: table_name/record_id].
        AC#2: Links to actual database records.

        Args:
            record: The database record to cite
            source_table: Name of the source table
            claim_text: Optional claim this citation supports
            confidence: Confidence score for this citation

        Returns:
            Citation object
        """
        record_id = record.get("id", str(uuid.uuid4()))
        citation_id = f"cit-{uuid.uuid4().hex[:12]}"

        # Extract key fields
        asset_id = record.get("asset_id")
        asset_name = record.get("asset_name") or record.get("name")

        # Get timestamp from various possible fields
        timestamp = self._extract_timestamp(record)

        # Build excerpt from key metrics
        excerpt = self._build_excerpt(record, source_table)

        # Generate display text
        display_text = self._format_display_text(
            source_table=source_table,
            timestamp=timestamp,
            asset_name=asset_name,
            record_id=record_id,
        )

        citation = Citation(
            id=citation_id,
            source_type=SourceType.DATABASE,
            source_table=source_table,
            record_id=str(record_id),
            asset_id=str(asset_id) if asset_id else None,
            timestamp=timestamp,
            excerpt=excerpt,
            confidence=confidence,
            display_text=display_text,
            claim_text=claim_text,
        )

        # Cache the citation
        self._citation_cache[citation_id] = citation

        return citation

    def generate_citation_from_memory(
        self,
        memory: Dict[str, Any],
        claim_text: Optional[str] = None,
        confidence: float = 0.8,
    ) -> Citation:
        """
        Generate a citation from a Mem0 memory entry.

        AC#6: Historical context from Mem0 includes memory provenance.

        Args:
            memory: The Mem0 memory entry to cite
            claim_text: Optional claim this citation supports
            confidence: Confidence score for this citation

        Returns:
            Citation object
        """
        memory_id = memory.get("id", memory.get("memory_id", str(uuid.uuid4())))
        citation_id = f"mem-{uuid.uuid4().hex[:12]}"

        # Extract memory content
        content = memory.get("memory", memory.get("content", ""))
        metadata = memory.get("metadata", {})

        # Extract asset and timestamp from metadata
        asset_id = metadata.get("asset_id")
        asset_name = metadata.get("asset_name")
        timestamp = metadata.get("timestamp") or memory.get("created_at")
        event_type = metadata.get("event_type")

        # Build excerpt
        excerpt = content[:150] + ("..." if len(content) > 150 else "")

        # Generate display text for memory citation
        display_parts = ["Memory"]
        if asset_name:
            display_parts.append(f"asset-history/{asset_name.lower().replace(' ', '-')}")
        display_parts.append(f"mem-id-{str(memory_id)[:8]}")
        display_text = f"[{'/'.join(display_parts)}]"

        citation = Citation(
            id=citation_id,
            source_type=SourceType.MEMORY,
            memory_id=str(memory_id),
            asset_id=str(asset_id) if asset_id else None,
            timestamp=str(timestamp) if timestamp else None,
            excerpt=excerpt,
            confidence=confidence,
            display_text=display_text,
            claim_text=claim_text,
        )

        # Cache the citation
        self._citation_cache[citation_id] = citation

        return citation

    def generate_calculation_citation(
        self,
        calculation_name: str,
        formula: str,
        inputs: Dict[str, Any],
        result: Any,
        claim_text: Optional[str] = None,
    ) -> Citation:
        """
        Generate a citation for a calculated/derived value.

        AC#2: Financial impact claims cite calculation basis.

        Args:
            calculation_name: Name of the calculation
            formula: The formula or method used
            inputs: Input values used in calculation
            result: The calculated result
            claim_text: Optional claim this citation supports

        Returns:
            Citation object
        """
        citation_id = f"calc-{uuid.uuid4().hex[:12]}"

        # Build excerpt showing calculation details
        input_str = ", ".join(f"{k}={v}" for k, v in list(inputs.items())[:3])
        excerpt = f"{calculation_name}: {formula} ({input_str}) = {result}"

        # Display text for calculation citation
        display_text = f"[Evidence: {calculation_name} calculation @ {datetime.utcnow().strftime('%Y-%m-%d')}]"

        citation = Citation(
            id=citation_id,
            source_type=SourceType.CALCULATION,
            timestamp=datetime.utcnow().isoformat(),
            excerpt=excerpt,
            confidence=0.95,  # Calculations are highly reliable
            display_text=display_text,
            claim_text=claim_text,
        )

        self._citation_cache[citation_id] = citation
        return citation

    def generate_inference_citation(
        self,
        inference_basis: str,
        claim_text: Optional[str] = None,
    ) -> Citation:
        """
        Generate a citation marking a claim as AI inference.

        AC#1: Non-grounded claims are explicitly marked as "AI inference".

        Args:
            inference_basis: Brief description of inference basis
            claim_text: The inference claim

        Returns:
            Citation object
        """
        citation_id = f"inf-{uuid.uuid4().hex[:12]}"

        display_text = "[AI Inference - based on pattern analysis]"

        citation = Citation(
            id=citation_id,
            source_type=SourceType.INFERENCE,
            timestamp=datetime.utcnow().isoformat(),
            excerpt=inference_basis[:100],
            confidence=0.5,  # Inferences have lower confidence
            display_text=display_text,
            claim_text=claim_text,
        )

        self._citation_cache[citation_id] = citation
        return citation

    def generate_citations_from_query_results(
        self,
        query_results: List[Dict[str, Any]],
        source_table: str,
        claim_text: Optional[str] = None,
    ) -> List[Citation]:
        """
        Generate citations from a list of query results.

        AC#5: Multi-source citation aggregation.

        Args:
            query_results: List of database records
            source_table: Source table name
            claim_text: Optional claim these citations support

        Returns:
            List of Citation objects, with primary source marked
        """
        citations = []

        for i, record in enumerate(query_results[:5]):  # Limit to 5 citations
            # First result is primary source
            confidence = 0.95 if i == 0 else 0.85

            citation = self.generate_citation_from_record(
                record=record,
                source_table=source_table,
                claim_text=claim_text,
                confidence=confidence,
            )
            citations.append(citation)

        return citations

    def aggregate_citations(
        self,
        citations: List[Citation],
        max_citations: int = 5,
    ) -> List[Citation]:
        """
        Aggregate and deduplicate citations, selecting the best ones.

        AC#5: Primary source is indicated when multiple sources support same claim.

        Args:
            citations: List of all citations
            max_citations: Maximum number to return

        Returns:
            List of deduplicated, prioritized citations
        """
        if not citations:
            return []

        # Sort by confidence
        sorted_citations = sorted(citations, key=lambda c: c.confidence, reverse=True)

        # Deduplicate by record_id or memory_id
        seen_ids = set()
        unique_citations = []

        for cit in sorted_citations:
            id_key = cit.record_id or cit.memory_id or cit.id
            if id_key not in seen_ids:
                seen_ids.add(id_key)
                unique_citations.append(cit)

                if len(unique_citations) >= max_citations:
                    break

        return unique_citations

    def select_primary_source(
        self,
        citations: List[Citation],
    ) -> Optional[Citation]:
        """
        Select the primary source from a list of citations.

        AC#5: Primary source is indicated when multiple sources support same claim.

        Args:
            citations: List of citations to evaluate

        Returns:
            The primary (most reliable) citation
        """
        if not citations:
            return None

        # Prefer database sources over memories
        # Prefer higher confidence
        # Prefer sources with more specific asset/timestamp info

        def score_citation(c: Citation) -> float:
            score = c.confidence

            # Prefer database sources
            if c.source_type == SourceType.DATABASE:
                score += 0.2
            elif c.source_type == SourceType.CALCULATION:
                score += 0.1

            # Prefer citations with asset info
            if c.asset_id:
                score += 0.1

            # Prefer citations with timestamp
            if c.timestamp:
                score += 0.1

            return score

        return max(citations, key=score_citation)

    def format_citations_for_response(
        self,
        response_text: str,
        citations: List[Citation],
        inline: bool = True,
    ) -> Tuple[str, List[Citation]]:
        """
        Format citations and optionally inject them inline into response.

        AC#1: All AI responses include inline citations.

        Args:
            response_text: The response text to annotate
            citations: List of citations to inject
            inline: Whether to inject citations inline

        Returns:
            Tuple of (annotated response text, used citations)
        """
        if not citations:
            return response_text, []

        if not inline:
            # Return citations as footnotes
            citation_refs = []
            for i, cit in enumerate(citations, 1):
                citation_refs.append(f"[{i}] {cit.display_text}: {cit.excerpt[:80]}...")

            annotated = response_text + "\n\n**Sources:**\n" + "\n".join(citation_refs)
            return annotated, citations

        # Inject citations inline
        annotated = response_text
        used_citations = []

        for cit in citations:
            if cit.claim_text:
                # Find and annotate the claim
                if cit.claim_text in annotated:
                    # Append citation after the claim
                    annotated = annotated.replace(
                        cit.claim_text,
                        f"{cit.claim_text} {cit.display_text}",
                        1
                    )
                    used_citations.append(cit)

        # If no claims were matched, append primary citation to end
        if not used_citations and citations:
            primary = self.select_primary_source(citations)
            if primary:
                annotated = f"{annotated.rstrip('.')} {primary.display_text}."
                used_citations.append(primary)

        return annotated, used_citations

    def get_citation(self, citation_id: str) -> Optional[Citation]:
        """
        Retrieve a cached citation by ID.

        AC#4: Citation links resolve within 100ms (cached data).

        Args:
            citation_id: The citation ID to retrieve

        Returns:
            Citation object if found, None otherwise
        """
        return self._citation_cache.get(citation_id)

    def clear_cache(self) -> None:
        """Clear the citation cache."""
        self._citation_cache.clear()
        self._settings = None
        logger.debug("Citation generator cache cleared")

    def _extract_timestamp(self, record: Dict[str, Any]) -> Optional[str]:
        """Extract timestamp from record in ISO format."""
        for field in ["report_date", "event_timestamp", "snapshot_timestamp", "created_at", "updated_at"]:
            if field in record and record[field]:
                val = record[field]
                if isinstance(val, str):
                    return val
                elif hasattr(val, 'isoformat'):
                    return val.isoformat()
                else:
                    return str(val)
        return None

    def _build_excerpt(self, record: Dict[str, Any], source_table: str) -> str:
        """Build a concise excerpt from record key fields."""
        excerpts = []

        # Priority fields for excerpt
        priority_fields = {
            "daily_summaries": ["oee_percentage", "downtime_minutes", "financial_loss_dollars"],
            "live_snapshots": ["current_output", "target_output", "status"],
            "safety_events": ["severity", "description", "status"],
            "cost_centers": ["standard_hourly_rate", "name"],
            "assets": ["name", "area", "status"],
            "asset_history": ["event_type", "title", "resolution"],
        }

        fields = priority_fields.get(source_table, [])

        for field in fields:
            if field in record and record[field] is not None:
                formatted = self._format_value(field, record[field])
                excerpts.append(f"{field}: {formatted}")

        # Add asset name if present
        if "asset_name" in record and record["asset_name"]:
            excerpts.insert(0, f"asset: {record['asset_name']}")
        elif "name" in record and record["name"] and source_table != "cost_centers":
            excerpts.insert(0, f"name: {record['name']}")

        return "; ".join(excerpts[:4])  # Limit to 4 fields

    def _format_value(self, field: str, value: Any) -> str:
        """Format a value based on its field type."""
        field_lower = field.lower()

        if value is None:
            return "N/A"

        # Percentage formatting
        if any(p in field_lower for p in self.PERCENTAGE_METRICS):
            try:
                return f"{float(value):.1f}%"
            except (TypeError, ValueError):
                return str(value)

        # Currency formatting
        if any(c in field_lower for c in self.CURRENCY_METRICS):
            try:
                return f"${float(value):,.2f}"
            except (TypeError, ValueError):
                return str(value)

        # Count formatting
        if any(c in field_lower for c in self.COUNT_METRICS):
            try:
                return f"{int(float(value)):,}"
            except (TypeError, ValueError):
                return str(value)

        return str(value)

    def _format_display_text(
        self,
        source_table: str,
        timestamp: Optional[str] = None,
        asset_name: Optional[str] = None,
        record_id: Optional[str] = None,
    ) -> str:
        """Format the display text for a citation."""
        parts = [f"Source: {source_table}"]

        # Add date
        if timestamp:
            date_str = str(timestamp)[:10]
            parts.append(date_str)

        # Add asset reference
        if asset_name:
            parts.append(f"asset-{asset_name.lower().replace(' ', '-')}")
        elif record_id:
            parts.append(f"id-{str(record_id)[:8]}")

        return "[" + "/".join(parts) + "]"


# Module-level singleton instance
_citation_generator: Optional[CitationGenerator] = None


def get_citation_generator() -> CitationGenerator:
    """
    Get the singleton CitationGenerator instance.

    Returns:
        CitationGenerator singleton instance
    """
    global _citation_generator
    if _citation_generator is None:
        _citation_generator = CitationGenerator()
    return _citation_generator
