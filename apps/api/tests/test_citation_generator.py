"""
Tests for Citation Generator Service (Story 4.5)

Unit tests for the citation generator which creates citations
from database records and memory sources.

AC#1: Response Citation Format Tests
AC#2: Data Source Integration Tests
AC#6: Mem0 Memory Citation Tests
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from uuid import uuid4

from app.models.citation import (
    Citation,
    SourceType,
)
from app.services.citation_generator import (
    CitationGenerator,
    get_citation_generator,
)


@pytest.fixture
def citation_generator():
    """Create a CitationGenerator instance for testing."""
    generator = CitationGenerator()
    return generator


@pytest.fixture
def sample_query_results():
    """Sample database query results for testing."""
    return [
        {
            "id": str(uuid4()),
            "asset_name": "Grinder 5",
            "oee_percentage": 87.5,
            "report_date": "2026-01-05",
            "downtime_minutes": 45,
            "financial_loss_dollars": 1250.00,
        },
        {
            "id": str(uuid4()),
            "asset_name": "Pump 3",
            "oee_percentage": 92.1,
            "report_date": "2026-01-05",
            "downtime_minutes": 12,
            "financial_loss_dollars": 320.00,
        },
    ]


@pytest.fixture
def sample_memory_result():
    """Sample Mem0 memory result for testing."""
    return {
        "memory_id": f"mem-{uuid4().hex[:8]}",
        "content": "Grinder 5 underwent preventive maintenance on 2026-01-03",
        "created_at": "2026-01-03T10:30:00Z",
        "metadata": {
            "asset_id": str(uuid4()),
            "event_type": "maintenance",
        },
        "similarity": 0.89,
    }


class TestCitationGeneratorInitialization:
    """Tests for CitationGenerator initialization."""

    def test_generator_can_be_created(self, citation_generator):
        """Test that generator can be instantiated."""
        assert citation_generator is not None

    def test_singleton_returns_same_instance(self):
        """Test that get_citation_generator returns singleton."""
        gen1 = get_citation_generator()
        gen2 = get_citation_generator()
        assert gen1 is gen2


class TestDatabaseCitationGeneration:
    """Tests for generating citations from database records."""

    def test_generate_citation_from_record(self, citation_generator, sample_query_results):
        """Test generating a citation from a database record."""
        record = sample_query_results[0]

        citation = citation_generator.generate_citation_from_record(
            record=record,
            source_table="daily_summaries",
            claim_text="Grinder 5 had 87.5% OEE",
        )

        assert citation is not None
        assert citation.source_type == SourceType.DATABASE
        assert citation.source_table == "daily_summaries"
        assert citation.record_id == record["id"]
        assert citation.confidence > 0

    def test_citation_includes_excerpt(self, citation_generator, sample_query_results):
        """Test that citation includes relevant excerpt."""
        record = sample_query_results[0]

        citation = citation_generator.generate_citation_from_record(
            record=record,
            source_table="daily_summaries",
            claim_text="OEE was 87.5%",
        )

        assert citation.excerpt is not None
        assert len(citation.excerpt) > 0
        # Excerpt should contain the relevant value
        assert "87.5" in citation.excerpt or "oee" in citation.excerpt.lower()

    def test_citation_has_display_text(self, citation_generator, sample_query_results):
        """Test that citation has human-readable display text."""
        record = sample_query_results[0]

        citation = citation_generator.generate_citation_from_record(
            record=record,
            source_table="daily_summaries",
            claim_text="test claim",
        )

        assert citation.display_text is not None
        assert len(citation.display_text) > 0
        # Display text should mention the source
        assert "daily_summaries" in citation.display_text.lower() or "source" in citation.display_text.lower()

    def test_generate_citations_from_query_results(self, citation_generator, sample_query_results):
        """Test generating citations from multiple query results."""
        citations = citation_generator.generate_citations_from_query_results(
            query_results=sample_query_results,
            source_table="daily_summaries",
            claim_text=None,
        )

        assert len(citations) == len(sample_query_results)
        for cit in citations:
            assert cit.source_type == SourceType.DATABASE
            assert cit.source_table == "daily_summaries"

    def test_empty_query_results_returns_empty_list(self, citation_generator):
        """Test that empty query results return empty citation list."""
        citations = citation_generator.generate_citations_from_query_results(
            query_results=[],
            source_table="daily_summaries",
            claim_text=None,
        )

        assert citations == []


class TestMemoryCitationGeneration:
    """Tests for generating citations from Mem0 memories (AC#6)."""

    def test_generate_citation_from_memory(self, citation_generator, sample_memory_result):
        """Test generating a citation from a memory result."""
        citation = citation_generator.generate_citation_from_memory(
            memory=sample_memory_result,
            claim_text="Grinder 5 had maintenance",
        )

        assert citation is not None
        assert citation.source_type == SourceType.MEMORY
        assert citation.memory_id == sample_memory_result["memory_id"]

    def test_memory_citation_includes_content(self, citation_generator, sample_memory_result):
        """Test that memory citation includes content excerpt."""
        citation = citation_generator.generate_citation_from_memory(
            memory=sample_memory_result,
            claim_text="maintenance event",
        )

        assert citation.excerpt is not None
        assert "maintenance" in citation.excerpt.lower()

    def test_memory_citation_uses_similarity_for_confidence(
        self, citation_generator, sample_memory_result
    ):
        """Test that memory citation confidence relates to similarity."""
        citation = citation_generator.generate_citation_from_memory(
            memory=sample_memory_result,
            claim_text="test claim",
        )

        # Confidence should be related to similarity score
        assert citation.confidence > 0
        assert citation.confidence <= 1.0

    def test_memory_citation_includes_timestamp(self, citation_generator, sample_memory_result):
        """Test that memory citation includes creation timestamp."""
        citation = citation_generator.generate_citation_from_memory(
            memory=sample_memory_result,
            claim_text="test claim",
        )

        assert citation.timestamp is not None


class TestCalculationCitation:
    """Tests for generating citations from calculations."""

    def test_generate_calculation_citation(self, citation_generator):
        """Test generating a calculation citation."""
        citation = citation_generator.generate_calculation_citation(
            calculation_name="Average OEE",
            formula="(87.5 + 92.1) / 2",
            inputs={"grinder_oee": 87.5, "pump_oee": 92.1},
            result="89.8",
            claim_text="Average OEE was 89.8%",
        )

        assert citation is not None
        assert citation.source_type == SourceType.CALCULATION
        assert "89.8" in citation.excerpt

    def test_calculation_citation_includes_formula(self, citation_generator):
        """Test that calculation citation shows formula."""
        formula = "SUM(downtime_minutes)"
        result = "57"

        citation = citation_generator.generate_calculation_citation(
            calculation_name="Total Downtime",
            formula=formula,
            inputs={"grinder_downtime": 45, "pump_downtime": 12},
            result=result,
            claim_text="Total downtime was 57 minutes",
        )

        assert formula in citation.excerpt or "SUM" in citation.excerpt


class TestCitationAggregation:
    """Tests for citation aggregation and deduplication."""

    def test_aggregate_citations_limits_count(self, citation_generator, sample_query_results):
        """Test that aggregation limits citation count."""
        # Generate many citations
        citations = []
        for i in range(20):
            record = sample_query_results[0].copy()
            record["id"] = str(uuid4())
            cit = citation_generator.generate_citation_from_record(
                record=record,
                source_table="daily_summaries",
                claim_text=f"claim {i}",
            )
            citations.append(cit)

        aggregated = citation_generator.aggregate_citations(
            citations=citations,
            max_citations=10,
        )

        assert len(aggregated) <= 10

    def test_aggregate_citations_removes_duplicates(self, citation_generator, sample_query_results):
        """Test that aggregation removes duplicate citations."""
        record = sample_query_results[0]

        # Create duplicate citations with same record_id
        citations = []
        for _ in range(5):
            cit = citation_generator.generate_citation_from_record(
                record=record,
                source_table="daily_summaries",
                claim_text="same claim",
            )
            citations.append(cit)

        aggregated = citation_generator.aggregate_citations(
            citations=citations,
            max_citations=10,
        )

        # Should have only one unique citation
        record_ids = [c.record_id for c in aggregated]
        assert len(set(record_ids)) == len(record_ids)

    def test_aggregate_citations_prioritizes_high_confidence(
        self, citation_generator, sample_query_results
    ):
        """Test that aggregation prioritizes high confidence citations."""
        citations = []

        # Create citations with varying confidence
        for i, confidence in enumerate([0.3, 0.9, 0.5, 0.95, 0.4]):
            record = sample_query_results[0].copy()
            record["id"] = str(uuid4())
            cit = citation_generator.generate_citation_from_record(
                record=record,
                source_table="daily_summaries",
                claim_text=f"claim {i}",
            )
            cit.confidence = confidence
            citations.append(cit)

        aggregated = citation_generator.aggregate_citations(
            citations=citations,
            max_citations=3,
        )

        # Top 3 should be 0.95, 0.9, 0.5
        confidences = [c.confidence for c in aggregated]
        assert confidences == sorted(confidences, reverse=True)


class TestResponseFormatting:
    """Tests for formatting citations in responses."""

    def test_format_citations_inline(self, citation_generator, sample_query_results):
        """Test inline citation formatting in response text."""
        record = sample_query_results[0]
        citation = citation_generator.generate_citation_from_record(
            record=record,
            source_table="daily_summaries",
            claim_text="87.5% OEE",
        )

        response_text = "Grinder 5 had 87.5% OEE yesterday."

        formatted, used = citation_generator.format_citations_for_response(
            response_text=response_text,
            citations=[citation],
            inline=True,
        )

        # Should have some form of citation marker
        assert formatted != response_text or len(used) > 0

    def test_format_citations_returns_used_citations(self, citation_generator, sample_query_results):
        """Test that formatting returns list of used citations."""
        citations = []
        for record in sample_query_results:
            cit = citation_generator.generate_citation_from_record(
                record=record,
                source_table="daily_summaries",
                claim_text="test",
            )
            citations.append(cit)

        response_text = "Grinder 5 and Pump 3 had good performance."

        formatted, used = citation_generator.format_citations_for_response(
            response_text=response_text,
            citations=citations,
            inline=True,
        )

        assert isinstance(used, list)


class TestCitationCaching:
    """Tests for citation caching functionality."""

    def test_get_citation_returns_cached(self, citation_generator, sample_query_results):
        """Test that get_citation returns cached citation."""
        record = sample_query_results[0]
        citation = citation_generator.generate_citation_from_record(
            record=record,
            source_table="daily_summaries",
            claim_text="test",
        )

        # Cache the citation
        citation_generator._citation_cache[citation.id] = citation

        # Retrieve from cache
        retrieved = citation_generator.get_citation(citation.id)

        assert retrieved is not None
        assert retrieved.id == citation.id

    def test_get_citation_returns_none_for_unknown(self, citation_generator):
        """Test that get_citation returns None for unknown ID."""
        retrieved = citation_generator.get_citation("unknown-citation-id")

        assert retrieved is None


class TestCitationIdFormat:
    """Tests for citation ID format compliance."""

    def test_database_citation_id_format(self, citation_generator, sample_query_results):
        """Test that database citations have correct ID format."""
        record = sample_query_results[0]
        citation = citation_generator.generate_citation_from_record(
            record=record,
            source_table="daily_summaries",
            claim_text="test",
        )

        # Should start with 'cit-' prefix
        assert citation.id.startswith("cit-")

    def test_memory_citation_id_format(self, citation_generator, sample_memory_result):
        """Test that memory citations have correct ID format."""
        citation = citation_generator.generate_citation_from_memory(
            memory=sample_memory_result,
            claim_text="test",
        )

        # Should start with 'mem-' prefix
        assert citation.id.startswith("mem-")

    def test_calculation_citation_id_format(self, citation_generator):
        """Test that calculation citations have correct ID format."""
        citation = citation_generator.generate_calculation_citation(
            calculation_name="Test Calc",
            formula="1+1",
            inputs={"a": 1, "b": 1},
            result="2",
            claim_text="test",
        )

        # Should start with 'calc-' prefix
        assert citation.id.startswith("calc-")
