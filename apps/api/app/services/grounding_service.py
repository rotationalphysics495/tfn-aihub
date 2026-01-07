"""
Grounding Validation Service (Story 4.5)

Service for validating LLM responses against source data to ensure
factual accuracy and generate citations for NFR1 compliance.

AC#3: Grounding Validation
  - Implement grounding score threshold (minimum 0.6) for claim validation
  - Responses below grounding threshold trigger fallback to "insufficient evidence" message
  - Each response includes meta.grounding_score indicating confidence level
  - Grounding validation logs are captured for observability

AC#7: NFR1 Compliance Validation
  - 100% of factual recommendations include at least one citation
  - Citation accuracy verified against source data (no hallucinated references)
  - Audit log records all citation-response pairs for compliance review
  - Grounding failures trigger alert for manual review

AC#8: Performance Requirements
  - Grounding validation completes within 200ms per claim
"""

import asyncio
import logging
import re
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from app.core.config import get_settings
from app.models.citation import (
    Claim,
    ClaimType,
    Citation,
    GroundingResult,
    CitedResponse,
    SourceType,
    GROUNDING_THRESHOLD_MIN,
    GROUNDING_THRESHOLD_HIGH,
    GROUNDING_THRESHOLD_LOW,
)

logger = logging.getLogger(__name__)


class GroundingServiceError(Exception):
    """Base exception for Grounding Service errors."""
    pass


class ClaimExtractionError(GroundingServiceError):
    """Error extracting claims from response."""
    pass


class GroundingValidationError(GroundingServiceError):
    """Error validating claim grounding."""
    pass


# Claim extraction prompt for LLM
CLAIM_EXTRACTION_PROMPT = """You are an expert at extracting factual claims from text.
Given the following AI response about manufacturing data, extract each distinct factual claim.

For each claim, identify:
1. The exact claim text
2. The type: factual (verifiable data), recommendation (suggestion), inference (derived conclusion), historical (past patterns)
3. Whether it requires grounding with evidence (true for factual/historical, false for recommendations/inferences)
4. Entity mentions (asset names, areas)
5. Metric mentions (OEE, downtime, values with units)
6. Temporal references (yesterday, last week, specific dates)

Return the claims in JSON format as a list.

Example input:
"Grinder 5 had the highest downtime at 47 minutes yesterday, costing approximately $2,350 in lost production. I recommend scheduling preventive maintenance."

Example output:
[
  {
    "text": "Grinder 5 had the highest downtime at 47 minutes yesterday",
    "claim_type": "factual",
    "requires_grounding": true,
    "entity_mentions": ["Grinder 5"],
    "metric_mentions": ["downtime", "47 minutes"],
    "temporal_reference": "yesterday"
  },
  {
    "text": "costing approximately $2,350 in lost production",
    "claim_type": "factual",
    "requires_grounding": true,
    "entity_mentions": ["Grinder 5"],
    "metric_mentions": ["$2,350", "financial loss"],
    "temporal_reference": "yesterday"
  },
  {
    "text": "I recommend scheduling preventive maintenance",
    "claim_type": "recommendation",
    "requires_grounding": false,
    "entity_mentions": [],
    "metric_mentions": [],
    "temporal_reference": null
  }
]

Now extract claims from this response:
"""


class GroundingService:
    """
    Service for validating LLM responses against source data.

    Implements a three-step grounding approach to reduce hallucination:
    1. Extract claims from LLM response
    2. Retrieve supporting sources for each claim
    3. Validate grounding and generate citations

    Story 4.5 Implementation:
    - AC#3: Grounding validation with 0.6 minimum threshold
    - AC#7: 100% factual claims must include citations
    - AC#8: Validation within 200ms per claim
    """

    def __init__(self):
        """Initialize the Grounding Service (lazy initialization)."""
        self._llm: Optional[ChatOpenAI] = None
        self._initialized: bool = False
        self._settings = None

    def _get_settings(self):
        """Get cached settings."""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    def initialize(self) -> bool:
        """
        Initialize the grounding service with OpenAI LLM.

        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized and self._llm is not None:
            return True

        settings = self._get_settings()

        if not settings.openai_api_key:
            logger.warning(
                "Grounding service not configured. "
                "Set OPENAI_API_KEY environment variable."
            )
            return False

        try:
            # Use gpt-4o-mini for faster claim extraction
            self._llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                api_key=settings.openai_api_key,
            )

            self._initialized = True
            logger.info("Grounding service initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Grounding service: {e}")
            return False

    def _ensure_initialized(self) -> None:
        """Ensure the service is initialized before operations."""
        if not self._initialized or self._llm is None:
            if not self.initialize():
                raise GroundingServiceError(
                    "Grounding service not configured. Check OPENAI_API_KEY."
                )

    async def extract_claims(self, response_text: str) -> List[Claim]:
        """
        Extract factual claims from an LLM response.

        AC#3: Claim extraction using LangChain.

        Args:
            response_text: The AI response text to analyze

        Returns:
            List of extracted claims
        """
        self._ensure_initialized()

        try:
            # Use LLM to extract claims
            full_prompt = CLAIM_EXTRACTION_PROMPT + f"\n\nResponse to analyze:\n{response_text}"

            response = await asyncio.to_thread(
                self._llm.invoke,
                [HumanMessage(content=full_prompt)]
            )

            # Parse the JSON response
            claims_json = self._extract_json_from_response(response.content)

            claims = []
            for claim_data in claims_json:
                claim_type = ClaimType.FACTUAL
                type_str = claim_data.get("claim_type", "factual").lower()
                if type_str == "recommendation":
                    claim_type = ClaimType.RECOMMENDATION
                elif type_str == "inference":
                    claim_type = ClaimType.INFERENCE
                elif type_str == "historical":
                    claim_type = ClaimType.HISTORICAL

                claims.append(Claim(
                    text=claim_data.get("text", ""),
                    claim_type=claim_type,
                    requires_grounding=claim_data.get("requires_grounding", True),
                    entity_mentions=claim_data.get("entity_mentions", []),
                    metric_mentions=claim_data.get("metric_mentions", []),
                    temporal_reference=claim_data.get("temporal_reference"),
                ))

            logger.debug(f"Extracted {len(claims)} claims from response")
            return claims

        except Exception as e:
            logger.error(f"Claim extraction failed: {e}")
            # Fallback: treat entire response as single factual claim
            return [Claim(
                text=response_text[:200],
                claim_type=ClaimType.FACTUAL,
                requires_grounding=True,
                entity_mentions=[],
                metric_mentions=[],
                temporal_reference=None,
            )]

    def _extract_json_from_response(self, response: str) -> List[Dict[str, Any]]:
        """Extract JSON array from LLM response."""
        import json

        # Try to find JSON array in the response
        try:
            # First, try direct parsing
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try to find JSON array in the text
        match = re.search(r'\[[\s\S]*\]', response)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # Fallback: return empty list
        logger.warning("Could not parse claims JSON from LLM response")
        return []

    async def validate_claim(
        self,
        claim: Claim,
        available_sources: List[Dict[str, Any]],
        memory_sources: Optional[List[Dict[str, Any]]] = None,
    ) -> GroundingResult:
        """
        Validate a single claim against available data sources.

        AC#3: Grounding score threshold (0.6 minimum).
        AC#8: Validation within 200ms per claim.

        Args:
            claim: The claim to validate
            available_sources: Database records that might support the claim
            memory_sources: Optional Mem0 memory entries

        Returns:
            GroundingResult with validation status and supporting citations
        """
        start_time = time.time()

        # If claim doesn't require grounding, return high confidence
        if not claim.requires_grounding:
            return GroundingResult(
                claim_text=claim.text,
                is_grounded=True,
                confidence=1.0,
                supporting_citations=[],
                validation_time_ms=(time.time() - start_time) * 1000,
            )

        # Find supporting evidence
        supporting_citations = []
        best_confidence = 0.0

        # Check database sources
        for source in available_sources:
            confidence, citation = self._match_claim_to_source(claim, source)
            if confidence > 0:
                if citation:
                    supporting_citations.append(citation)
                best_confidence = max(best_confidence, confidence)

        # Check memory sources
        if memory_sources:
            for mem in memory_sources:
                confidence, citation = self._match_claim_to_memory(claim, mem)
                if confidence > 0:
                    if citation:
                        supporting_citations.append(citation)
                    best_confidence = max(best_confidence, confidence)

        validation_time_ms = (time.time() - start_time) * 1000
        is_grounded = best_confidence >= GROUNDING_THRESHOLD_MIN

        # Generate fallback text if not grounded
        fallback_text = None
        if not is_grounded:
            fallback_text = f"[AI Inference - based on available patterns, but specific data for '{claim.text[:50]}...' could not be verified]"

        return GroundingResult(
            claim_text=claim.text,
            is_grounded=is_grounded,
            confidence=best_confidence,
            supporting_citations=supporting_citations,
            validation_time_ms=validation_time_ms,
            fallback_text=fallback_text,
        )

    def _match_claim_to_source(
        self,
        claim: Claim,
        source: Dict[str, Any]
    ) -> Tuple[float, Optional[Citation]]:
        """
        Match a claim against a database source record.

        Uses heuristic matching based on:
        - Entity mentions (asset names)
        - Metric mentions (values, units)
        - Temporal alignment

        Returns:
            Tuple of (confidence_score, citation)
        """
        confidence = 0.0
        matches = []

        # Check entity mentions
        for entity in claim.entity_mentions:
            entity_lower = entity.lower()
            for key, value in source.items():
                if isinstance(value, str) and entity_lower in value.lower():
                    confidence += 0.3
                    matches.append(f"{key}: {value}")
                elif key in ["asset_name", "name"] and entity_lower in str(value).lower():
                    confidence += 0.4
                    matches.append(f"{key}: {value}")

        # Check metric mentions - look for numeric values
        for metric in claim.metric_mentions:
            # Extract numbers from metric mention
            numbers = re.findall(r'[\d,]+\.?\d*', metric.replace(',', ''))
            for num_str in numbers:
                try:
                    num = float(num_str)
                    for key, value in source.items():
                        if isinstance(value, (int, float)):
                            # Allow some tolerance for floating point
                            if abs(value - num) < 0.5 or (num > 0 and abs(value - num) / num < 0.01):
                                confidence += 0.4
                                matches.append(f"{key}: {value}")
                except ValueError:
                    continue

        # Check for temporal alignment if source has date fields
        if claim.temporal_reference:
            for date_key in ["report_date", "event_timestamp", "snapshot_timestamp", "created_at"]:
                if date_key in source and source[date_key]:
                    # Basic temporal matching - could be enhanced
                    confidence += 0.2
                    matches.append(f"{date_key}: {source[date_key]}")
                    break

        # Normalize confidence to [0, 1]
        confidence = min(confidence, 1.0)

        if confidence > 0 and matches:
            # Build citation
            source_table = source.get("_source_table", "unknown")
            record_id = source.get("id", source.get("_record_id", str(uuid.uuid4())))
            asset_id = source.get("asset_id")
            asset_name = source.get("asset_name") or source.get("name")
            timestamp = source.get("report_date") or source.get("event_timestamp") or source.get("created_at")

            citation = Citation(
                id=f"cit-{uuid.uuid4().hex[:12]}",
                source_type=SourceType.DATABASE,
                source_table=source_table,
                record_id=str(record_id),
                asset_id=str(asset_id) if asset_id else None,
                timestamp=str(timestamp) if timestamp else None,
                excerpt="; ".join(matches[:3]),  # Limit to 3 matches
                confidence=confidence,
                display_text=self._format_citation_display(source_table, timestamp, asset_name),
                claim_text=claim.text,
            )
            return confidence, citation

        return 0.0, None

    def _match_claim_to_memory(
        self,
        claim: Claim,
        memory: Dict[str, Any]
    ) -> Tuple[float, Optional[Citation]]:
        """
        Match a claim against a Mem0 memory entry.

        AC#6: Mem0 memory citations.

        Returns:
            Tuple of (confidence_score, citation)
        """
        confidence = 0.0
        memory_content = memory.get("memory", memory.get("content", ""))

        if not memory_content:
            return 0.0, None

        memory_lower = memory_content.lower()
        claim_lower = claim.text.lower()

        # Check for entity overlap
        for entity in claim.entity_mentions:
            if entity.lower() in memory_lower:
                confidence += 0.3

        # Check for metric/keyword overlap
        for metric in claim.metric_mentions:
            # Simple keyword matching
            keywords = re.findall(r'\w+', metric.lower())
            for kw in keywords:
                if len(kw) > 2 and kw in memory_lower:
                    confidence += 0.2

        # Check overall text similarity (simple word overlap)
        claim_words = set(re.findall(r'\w+', claim_lower))
        memory_words = set(re.findall(r'\w+', memory_lower))
        if claim_words and memory_words:
            overlap = len(claim_words & memory_words) / len(claim_words)
            confidence += overlap * 0.3

        confidence = min(confidence, 1.0)

        if confidence > 0:
            memory_id = memory.get("id", memory.get("memory_id", str(uuid.uuid4())))
            metadata = memory.get("metadata", {})
            asset_id = metadata.get("asset_id")
            timestamp = metadata.get("timestamp") or memory.get("created_at")

            citation = Citation(
                id=f"mem-{uuid.uuid4().hex[:12]}",
                source_type=SourceType.MEMORY,
                memory_id=str(memory_id),
                asset_id=str(asset_id) if asset_id else None,
                timestamp=str(timestamp) if timestamp else None,
                excerpt=memory_content[:100] + ("..." if len(memory_content) > 100 else ""),
                confidence=confidence,
                display_text=f"[Memory: {memory_id[:20]}...]",
                claim_text=claim.text,
            )
            return confidence, citation

        return 0.0, None

    def _format_citation_display(
        self,
        source_table: str,
        timestamp: Optional[Any],
        asset_name: Optional[str] = None
    ) -> str:
        """Format a display-friendly citation text."""
        parts = [f"Source: {source_table}"]

        if timestamp:
            # Extract date portion
            date_str = str(timestamp)[:10]
            parts.append(date_str)

        if asset_name:
            parts.append(f"asset-{asset_name.lower().replace(' ', '-')}")

        return "[" + "/".join(parts) + "]"

    async def validate_response(
        self,
        response_text: str,
        available_sources: List[Dict[str, Any]],
        memory_sources: Optional[List[Dict[str, Any]]] = None,
    ) -> CitedResponse:
        """
        Validate an entire response and generate citations.

        AC#3: Full response validation with grounding score.
        AC#7: 100% factual claims must include citations.

        Args:
            response_text: The AI response to validate
            available_sources: Database records for citation
            memory_sources: Optional Mem0 memories for citation

        Returns:
            CitedResponse with citations and grounding score
        """
        start_time = time.time()
        response_id = f"resp-{uuid.uuid4().hex[:12]}"

        # Step 1: Extract claims
        claims = await self.extract_claims(response_text)

        # Step 2: Validate each claim
        grounding_results: List[GroundingResult] = []
        all_citations: List[Citation] = []
        ungrounded_claims: List[str] = []

        for claim in claims:
            result = await self.validate_claim(claim, available_sources, memory_sources)
            grounding_results.append(result)

            all_citations.extend(result.supporting_citations)

            if claim.requires_grounding and not result.is_grounded:
                ungrounded_claims.append(claim.text)

        # Step 3: Calculate overall grounding score
        groundable_claims = [c for c in claims if c.requires_grounding]
        if groundable_claims:
            grounding_score = sum(
                r.confidence for r in grounding_results
                if any(c.text == r.claim_text and c.requires_grounding for c in claims)
            ) / len(groundable_claims)
        else:
            grounding_score = 1.0

        grounding_score = min(grounding_score, 1.0)

        # Step 4: Generate cited response text
        cited_response_text = self._inject_citations(response_text, all_citations)

        # If grounding is insufficient, add disclaimer
        if grounding_score < GROUNDING_THRESHOLD_MIN:
            cited_response_text = (
                f"{cited_response_text}\n\n"
                "**Note:** Some claims in this response could not be verified against "
                "available data. Please verify critical information before making decisions."
            )

        total_time_ms = (time.time() - start_time) * 1000
        grounding_time_ms = sum(r.validation_time_ms for r in grounding_results)

        return CitedResponse(
            id=response_id,
            response_text=cited_response_text,
            citations=all_citations,
            claims=claims,
            grounding_score=round(grounding_score, 2),
            ungrounded_claims=ungrounded_claims,
            meta={
                "response_time_ms": round(total_time_ms, 2),
                "grounding_time_ms": round(grounding_time_ms, 2),
                "citation_count": len(all_citations),
                "claim_count": len(claims),
                "groundable_claim_count": len(groundable_claims),
                "ungrounded_claim_count": len(ungrounded_claims),
            }
        )

    def _inject_citations(
        self,
        response_text: str,
        citations: List[Citation]
    ) -> str:
        """
        Inject inline citations into response text.

        AC#1: Citations follow format [Source: table_name/record_id].
        """
        if not citations:
            return response_text

        # Group citations by claim text
        claim_citations: Dict[str, List[Citation]] = {}
        for cit in citations:
            if cit.claim_text:
                if cit.claim_text not in claim_citations:
                    claim_citations[cit.claim_text] = []
                claim_citations[cit.claim_text].append(cit)

        cited_text = response_text

        # Try to inject citations after relevant sentences
        for claim_text, cits in claim_citations.items():
            # Find a sentence that contains part of the claim
            sentences = re.split(r'(?<=[.!?])\s+', cited_text)
            for i, sentence in enumerate(sentences):
                # Check if this sentence relates to the claim
                claim_words = set(re.findall(r'\w+', claim_text.lower()))
                sentence_words = set(re.findall(r'\w+', sentence.lower()))

                if claim_words and sentence_words:
                    overlap = len(claim_words & sentence_words) / len(claim_words)
                    if overlap > 0.3:
                        # Inject the best citation after this sentence
                        best_cit = max(cits, key=lambda c: c.confidence)
                        # Only inject if not already present
                        if best_cit.display_text not in sentence:
                            sentences[i] = sentence.rstrip('.!?') + f" {best_cit.display_text}" + sentence[-1] if sentence[-1] in '.!?' else '.'

            cited_text = ' '.join(sentences)

        return cited_text

    def generate_fallback_response(
        self,
        original_response: str,
        grounding_score: float,
        ungrounded_claims: List[str]
    ) -> str:
        """
        Generate a fallback response when grounding is insufficient.

        AC#3: Responses below threshold trigger fallback to "insufficient evidence" message.

        Args:
            original_response: The original AI response
            grounding_score: The calculated grounding score
            ungrounded_claims: List of claims that couldn't be grounded

        Returns:
            Modified response with appropriate disclaimers
        """
        if grounding_score >= GROUNDING_THRESHOLD_MIN:
            return original_response

        if grounding_score < GROUNDING_THRESHOLD_LOW:
            # Very low grounding - provide minimal information
            return (
                "I cannot provide a reliable answer to your question based on the "
                "available data. The information I would typically provide could not "
                "be verified against the database records.\n\n"
                "**Suggestion:** Try asking about a different time period or asset, "
                "or rephrase your question to focus on available data."
            )

        # Moderate grounding - include response with strong disclaimer
        return (
            f"{original_response}\n\n"
            "---\n"
            f"**Data Verification Notice:** This response has a grounding confidence "
            f"of {grounding_score:.0%}, which is below our standard threshold. "
            f"The following claims could not be fully verified:\n"
            + "\n".join(f"- {claim[:100]}..." for claim in ungrounded_claims[:3])
            + "\n\nPlease verify these claims against actual data before making decisions."
        )

    def is_configured(self) -> bool:
        """Check if the service is properly configured."""
        settings = self._get_settings()
        return bool(settings.openai_api_key)

    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._initialized and self._llm is not None

    def clear_cache(self) -> None:
        """Clear any cached data."""
        self._settings = None
        logger.debug("Grounding service cache cleared")


# Module-level singleton instance
_grounding_service: Optional[GroundingService] = None


def get_grounding_service() -> GroundingService:
    """
    Get the singleton GroundingService instance.

    Returns:
        GroundingService singleton instance
    """
    global _grounding_service
    if _grounding_service is None:
        _grounding_service = GroundingService()
    return _grounding_service
