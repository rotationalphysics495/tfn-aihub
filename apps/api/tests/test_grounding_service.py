"""
Tests for Grounding Validation Service (Story 4.5)

Unit tests for the grounding service which validates AI response claims
against available data sources.

AC#3: Grounding Validation Tests
AC#8: Performance Tests
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from app.models.citation import (
    Citation,
    Claim,
    ClaimType,
    CitedResponse,
    SourceType,
    GROUNDING_THRESHOLD_MIN,
    GROUNDING_THRESHOLD_HIGH,
)
from app.services.grounding_service import (
    GroundingService,
    get_grounding_service,
    GroundingResult,
)


@pytest.fixture
def grounding_service():
    """Create a GroundingService instance for testing."""
    service = GroundingService()
    return service


@pytest.fixture
def sample_sources():
    """Sample database sources for testing."""
    return [
        {
            "_source_table": "daily_summaries",
            "_record_id": "uuid-001",
            "asset_name": "Grinder 5",
            "oee_percentage": 87.5,
            "report_date": "2026-01-05",
            "downtime_minutes": 45,
        },
        {
            "_source_table": "daily_summaries",
            "_record_id": "uuid-002",
            "asset_name": "Pump 3",
            "oee_percentage": 92.1,
            "report_date": "2026-01-05",
            "downtime_minutes": 12,
        },
        {
            "_source_table": "safety_events",
            "_record_id": "uuid-003",
            "asset_name": "Conveyor A",
            "severity": "low",
            "description": "Minor belt misalignment",
        },
    ]


@pytest.fixture
def sample_memory_sources():
    """Sample memory sources for testing."""
    return [
        {
            "memory_id": "mem-001",
            "content": "Grinder 5 had maintenance on 2026-01-03",
            "created_at": "2026-01-03T10:00:00Z",
            "metadata": {"asset_id": "asset-001"},
        },
        {
            "memory_id": "mem-002",
            "content": "User prefers detailed OEE breakdowns",
            "created_at": "2026-01-01T08:00:00Z",
            "metadata": {"user_id": "user-001"},
        },
    ]


class TestGroundingServiceInitialization:
    """Tests for GroundingService initialization."""

    def test_service_can_be_created(self, grounding_service):
        """Test that service can be instantiated."""
        assert grounding_service is not None

    def test_singleton_returns_same_instance(self):
        """Test that get_grounding_service returns singleton."""
        service1 = get_grounding_service()
        service2 = get_grounding_service()
        assert service1 is service2


class TestClaimExtraction:
    """Tests for claim extraction from AI responses."""

    @pytest.mark.asyncio
    async def test_extract_claims_from_simple_response(self, grounding_service):
        """Test extracting claims from a simple response."""
        response = "Grinder 5 had 87.5% OEE yesterday."

        with patch.object(grounding_service, '_extract_json_from_response') as mock_extract:
            mock_extract.return_value = [
                {
                    "text": "Grinder 5 had 87.5% OEE",
                    "claim_type": "factual",
                    "requires_grounding": True,
                    "entity_mentions": ["Grinder 5"],
                    "metric_mentions": ["87.5% OEE"],
                }
            ]

            # Mock the LLM call
            grounding_service._llm = MagicMock()
            grounding_service._llm.invoke = MagicMock(return_value=MagicMock(content="[]"))
            grounding_service._initialized = True

            claims = await grounding_service.extract_claims(response)

            assert len(claims) == 1
            assert claims[0].text == "Grinder 5 had 87.5% OEE"
            assert claims[0].requires_grounding is True

    @pytest.mark.asyncio
    async def test_extract_claims_identifies_multiple_claims(self, grounding_service):
        """Test extracting multiple claims from a response."""
        response = "Grinder 5 had 87.5% OEE. Pump 3 was more efficient at 92.1%."

        with patch.object(grounding_service, '_extract_json_from_response') as mock_extract:
            mock_extract.return_value = [
                {
                    "text": "Grinder 5 had 87.5% OEE",
                    "claim_type": "factual",
                    "requires_grounding": True,
                    "entity_mentions": ["Grinder 5"],
                    "metric_mentions": ["87.5% OEE"],
                },
                {
                    "text": "Pump 3 was at 92.1%",
                    "claim_type": "factual",
                    "requires_grounding": True,
                    "entity_mentions": ["Pump 3"],
                    "metric_mentions": ["92.1%"],
                },
            ]

            grounding_service._llm = MagicMock()
            grounding_service._llm.invoke = MagicMock(return_value=MagicMock(content="[]"))
            grounding_service._initialized = True

            claims = await grounding_service.extract_claims(response)

            assert len(claims) == 2

    @pytest.mark.asyncio
    async def test_extract_claims_handles_non_factual_statements(self, grounding_service):
        """Test that non-factual statements don't require grounding."""
        response = "I hope this helps with your analysis."

        with patch.object(grounding_service, '_extract_json_from_response') as mock_extract:
            mock_extract.return_value = [
                {
                    "text": "I hope this helps",
                    "claim_type": "recommendation",
                    "requires_grounding": False,
                    "entity_mentions": [],
                    "metric_mentions": [],
                }
            ]

            grounding_service._llm = MagicMock()
            grounding_service._llm.invoke = MagicMock(return_value=MagicMock(content="[]"))
            grounding_service._initialized = True

            claims = await grounding_service.extract_claims(response)

            assert len(claims) == 1
            assert claims[0].requires_grounding is False

    @pytest.mark.asyncio
    async def test_extract_claims_handles_empty_response(self, grounding_service):
        """Test extracting claims from empty response."""
        with patch.object(grounding_service, '_extract_json_from_response') as mock_extract:
            mock_extract.return_value = []

            grounding_service._llm = MagicMock()
            grounding_service._llm.invoke = MagicMock(return_value=MagicMock(content="[]"))
            grounding_service._initialized = True

            claims = await grounding_service.extract_claims("")

            assert len(claims) == 0


class TestClaimValidation:
    """Tests for validating claims against sources."""

    @pytest.mark.asyncio
    async def test_validate_claim_finds_matching_source(self, grounding_service, sample_sources):
        """Test that validation finds matching source for claim."""
        claim = Claim(
            text="Grinder 5 had 87.5% OEE",
            claim_type=ClaimType.FACTUAL,
            requires_grounding=True,
            entity_mentions=["Grinder 5"],
            metric_mentions=["87.5% OEE", "87.5"],
        )

        result = await grounding_service.validate_claim(claim, sample_sources, [])

        assert result.is_grounded is True
        assert result.confidence >= GROUNDING_THRESHOLD_MIN

    @pytest.mark.asyncio
    async def test_validate_claim_no_match_returns_ungrounded(self, grounding_service, sample_sources):
        """Test that validation returns ungrounded when no match."""
        claim = Claim(
            text="Mixer 7 had 95% OEE",
            claim_type=ClaimType.FACTUAL,
            requires_grounding=True,
            entity_mentions=["Mixer 7"],
            metric_mentions=["95% OEE"],
        )

        result = await grounding_service.validate_claim(claim, sample_sources, [])

        assert result.is_grounded is False
        assert result.confidence < GROUNDING_THRESHOLD_MIN

    @pytest.mark.asyncio
    async def test_validate_claim_uses_memory_sources(self, grounding_service, sample_memory_sources):
        """Test that validation can use memory sources."""
        claim = Claim(
            text="Grinder 5 had maintenance on 2026-01-03",
            claim_type=ClaimType.HISTORICAL,
            requires_grounding=True,
            entity_mentions=["Grinder 5"],
            metric_mentions=["maintenance"],
            temporal_reference="2026-01-03",
        )

        result = await grounding_service.validate_claim(claim, [], sample_memory_sources)

        # Check if result has confidence > 0 from memory match
        assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_validate_claim_non_grounding_always_passes(self, grounding_service):
        """Test that non-grounding claims always pass."""
        claim = Claim(
            text="I hope this helps",
            claim_type=ClaimType.RECOMMENDATION,
            requires_grounding=False,
            entity_mentions=[],
            metric_mentions=[],
        )

        result = await grounding_service.validate_claim(claim, [], [])

        assert result.is_grounded is True
        assert result.confidence == 1.0


class TestResponseValidation:
    """Tests for full response validation."""

    @pytest.mark.asyncio
    async def test_validate_response_computes_grounding_score(
        self, grounding_service, sample_sources
    ):
        """Test that response validation computes correct grounding score."""
        response = "Grinder 5 had 87.5% OEE yesterday."

        with patch.object(grounding_service, 'extract_claims', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = [
                Claim(
                    text="Grinder 5 had 87.5% OEE",
                    claim_type=ClaimType.FACTUAL,
                    requires_grounding=True,
                    entity_mentions=["Grinder 5"],
                    metric_mentions=["87.5% OEE", "87.5"],
                )
            ]

            result = await grounding_service.validate_response(
                response_text=response,
                available_sources=sample_sources,
                memory_sources=[],
            )

            assert isinstance(result, CitedResponse)
            assert 0 <= result.grounding_score <= 1
            assert len(result.claims) == 1

    @pytest.mark.asyncio
    async def test_validate_response_identifies_ungrounded_claims(
        self, grounding_service, sample_sources
    ):
        """Test that ungrounded claims are identified."""
        response = "Mixer 7 had 95% OEE and caused $50,000 in losses."

        with patch.object(grounding_service, 'extract_claims', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = [
                Claim(
                    text="Mixer 7 had 95% OEE",
                    claim_type=ClaimType.FACTUAL,
                    requires_grounding=True,
                    entity_mentions=["Mixer 7"],
                    metric_mentions=["95% OEE"],
                ),
                Claim(
                    text="caused $50,000 in losses",
                    claim_type=ClaimType.FACTUAL,
                    requires_grounding=True,
                    entity_mentions=[],
                    metric_mentions=["$50,000"],
                ),
            ]

            result = await grounding_service.validate_response(
                response_text=response,
                available_sources=sample_sources,
                memory_sources=[],
            )

            assert result.grounding_score < GROUNDING_THRESHOLD_HIGH
            assert len(result.ungrounded_claims) > 0

    @pytest.mark.asyncio
    async def test_validate_response_all_grounded_high_score(
        self, grounding_service, sample_sources
    ):
        """Test that fully grounded responses get high score."""
        response = "Grinder 5 had 87.5% OEE with 45 minutes downtime."

        with patch.object(grounding_service, 'extract_claims', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = [
                Claim(
                    text="Grinder 5 had 87.5% OEE",
                    claim_type=ClaimType.FACTUAL,
                    requires_grounding=True,
                    entity_mentions=["Grinder 5"],
                    metric_mentions=["87.5% OEE", "87.5"],
                ),
                Claim(
                    text="45 minutes downtime",
                    claim_type=ClaimType.FACTUAL,
                    requires_grounding=True,
                    entity_mentions=["Grinder 5"],
                    metric_mentions=["45 minutes", "45"],
                    temporal_reference="yesterday",
                ),
            ]

            # Mock the claim validation to return grounded results
            async def mock_validate(claim, sources, memory):
                return GroundingResult(
                    claim_text=claim.text,
                    is_grounded=True,
                    confidence=0.9,
                    supporting_citations=[],
                    validation_time_ms=10.0,
                )

            with patch.object(grounding_service, 'validate_claim', side_effect=mock_validate):
                result = await grounding_service.validate_response(
                    response_text=response,
                    available_sources=sample_sources,
                    memory_sources=[],
                )

                assert result.grounding_score >= GROUNDING_THRESHOLD_HIGH
                assert len(result.ungrounded_claims) == 0


class TestFallbackResponse:
    """Tests for fallback response generation."""

    def test_generate_fallback_adds_disclaimer(self, grounding_service):
        """Test that fallback adds uncertainty disclaimer."""
        original = "Mixer 7 had 95% OEE yesterday."

        fallback = grounding_service.generate_fallback_response(
            original_response=original,
            grounding_score=0.3,
            ungrounded_claims=["Mixer 7 had 95% OEE"],
        )

        # Should contain some form of disclaimer
        assert fallback != original
        assert len(fallback) > len(original)

    def test_fallback_preserves_original_when_high_score(self, grounding_service):
        """Test that fallback doesn't modify high-grounded responses."""
        original = "Grinder 5 had 87.5% OEE yesterday."

        fallback = grounding_service.generate_fallback_response(
            original_response=original,
            grounding_score=0.9,
            ungrounded_claims=[],
        )

        # Should be unchanged or minimally modified
        assert original in fallback or fallback == original


class TestPerformance:
    """Tests for performance requirements (AC#8)."""

    @pytest.mark.asyncio
    async def test_claim_validation_under_200ms(self, grounding_service, sample_sources):
        """Test that claim validation completes within 200ms."""
        import time

        claim = Claim(
            text="Grinder 5 had 87.5% OEE",
            claim_type=ClaimType.FACTUAL,
            requires_grounding=True,
            entity_mentions=["Grinder 5"],
            metric_mentions=["87.5% OEE", "87.5"],
        )

        start = time.time()
        await grounding_service.validate_claim(claim, sample_sources, [])
        elapsed_ms = (time.time() - start) * 1000

        # Should complete within 200ms per AC#8
        assert elapsed_ms < 200, f"Claim validation took {elapsed_ms:.0f}ms, expected < 200ms"

    @pytest.mark.asyncio
    async def test_response_validation_scales_with_claims(self, grounding_service, sample_sources):
        """Test that response validation time scales reasonably with claims."""
        import time

        # Mock extract_claims to return varying number of claims
        with patch.object(grounding_service, 'extract_claims', new_callable=AsyncMock) as mock_extract:
            # Test with 5 claims
            mock_extract.return_value = [
                Claim(
                    text=f"Test claim {i}",
                    claim_type=ClaimType.FACTUAL,
                    requires_grounding=True,
                    entity_mentions=[],
                    metric_mentions=[],
                )
                for i in range(5)
            ]

            start = time.time()
            await grounding_service.validate_response(
                response_text="Test response with multiple claims",
                available_sources=sample_sources,
                memory_sources=[],
            )
            elapsed_ms = (time.time() - start) * 1000

            # 5 claims at 200ms each = 1000ms max, but should be faster with parallelization
            assert elapsed_ms < 1500, f"Response validation took {elapsed_ms:.0f}ms"
