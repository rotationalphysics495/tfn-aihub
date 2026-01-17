"""
Tests for EOD Morning vs Actual Comparison (Story 9.11)

Comprehensive test coverage for all acceptance criteria:
AC#1: Morning Briefing Retrieval - Retrieves morning briefing and compares concerns
AC#2: Concern Outcome Classification - Materialized/Averted/Escalated/Unexpected
AC#3: Accuracy Metrics Display - accuracy_percentage, false_positives, misses
AC#4: Accuracy Trend Tracking - Storage and query for trends
AC#5: No Morning Briefing Handling - Shows performance without comparison

References:
- [Source: epic-9.md#Story-9.11]
- [Source: 9-11-morning-vs-actual-comparison.md]
"""

import pytest
from datetime import datetime, timezone, date, time
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.briefing import (
    ConcernOutcome,
    ConcernComparison,
    AccuracyMetrics,
    EODComparisonResult,
    BriefingData,
    ToolResultData,
)
from app.services.briefing.eod import (
    EODService,
    MorningBriefingRecord,
    MorningConcern,
)


# =============================================================================
# Test: ConcernOutcome Enum (AC#2)
# =============================================================================


class TestConcernOutcomeEnum:
    """Tests for ConcernOutcome enum values (AC#2)."""

    def test_materialized_value(self):
        """AC#2: MATERIALIZED - issue occurred as predicted."""
        assert ConcernOutcome.MATERIALIZED.value == "materialized"

    def test_averted_value(self):
        """AC#2: AVERTED - issue was prevented/resolved."""
        assert ConcernOutcome.AVERTED.value == "averted"

    def test_escalated_value(self):
        """AC#2: ESCALATED - worse than predicted."""
        assert ConcernOutcome.ESCALATED.value == "escalated"

    def test_unexpected_value(self):
        """AC#2: UNEXPECTED - new issue not predicted."""
        assert ConcernOutcome.UNEXPECTED.value == "unexpected"


# =============================================================================
# Test: ConcernComparison Model (AC#2)
# =============================================================================


class TestConcernComparisonModel:
    """Tests for ConcernComparison model (AC#2)."""

    def test_concern_comparison_creation(self):
        """AC#2: Create concern comparison with all fields."""
        comparison = ConcernComparison(
            concern_id="mc-1",
            asset_id="asset-123",
            asset_name="Line 1",
            area="Area A",
            issue_type="production",
            morning_description="Line 1 may fall behind target",
            morning_severity="medium",
            actual_description="Line 1 met target ahead of schedule",
            outcome=ConcernOutcome.AVERTED,
            notes="Production concern was addressed",
        )

        assert comparison.concern_id == "mc-1"
        assert comparison.outcome == ConcernOutcome.AVERTED
        assert comparison.issue_type == "production"

    def test_concern_comparison_minimal(self):
        """AC#2: Create concern comparison with required fields only."""
        comparison = ConcernComparison(
            concern_id="mc-2",
            issue_type="safety",
            morning_description="Safety hazard in Area B",
            outcome=ConcernOutcome.MATERIALIZED,
        )

        assert comparison.concern_id == "mc-2"
        assert comparison.asset_id is None
        assert comparison.actual_description is None


# =============================================================================
# Test: AccuracyMetrics Model (AC#3)
# =============================================================================


class TestAccuracyMetricsModel:
    """Tests for AccuracyMetrics model (AC#3)."""

    def test_accuracy_metrics_default_values(self):
        """AC#3: Default accuracy metrics."""
        metrics = AccuracyMetrics()

        assert metrics.accuracy_percentage == 0.0
        assert metrics.total_predictions == 0
        assert metrics.correct_predictions == 0
        assert metrics.false_positives == 0
        assert metrics.misses == 0

    def test_accuracy_metrics_with_values(self):
        """AC#3: Accuracy metrics with calculated values."""
        metrics = AccuracyMetrics(
            accuracy_percentage=75.0,
            total_predictions=4,
            correct_predictions=3,
            false_positives=1,
            misses=1,
            averted_count=1,
            escalated_count=0,
        )

        assert metrics.accuracy_percentage == 75.0
        assert metrics.total_predictions == 4
        assert metrics.false_positives == 1
        assert metrics.misses == 1


# =============================================================================
# Test: EODComparisonResult Model (AC#1-3)
# =============================================================================


class TestEODComparisonResultModel:
    """Tests for EODComparisonResult model (AC#1-3)."""

    def test_eod_comparison_with_morning_briefing(self):
        """AC#1: EODComparisonResult with morning briefing."""
        now = datetime.now(timezone.utc)
        comparison = EODComparisonResult(
            morning_briefing_id="mb-123",
            morning_generated_at=now,
            eod_summary_id="eod-456",
            comparisons=[
                ConcernComparison(
                    concern_id="mc-1",
                    issue_type="production",
                    morning_description="Test concern",
                    outcome=ConcernOutcome.AVERTED,
                )
            ],
            accuracy_metrics=AccuracyMetrics(accuracy_percentage=100.0),
            unexpected_issues=[],
            comparison_summary="All concerns averted.",
            has_morning_briefing=True,
        )

        assert comparison.has_morning_briefing is True
        assert comparison.morning_briefing_id == "mb-123"
        assert len(comparison.comparisons) == 1
        assert comparison.prediction_accuracy == 100.0

    def test_eod_comparison_no_morning_briefing(self):
        """AC#5: EODComparisonResult without morning briefing."""
        comparison = EODComparisonResult(
            has_morning_briefing=False,
            comparison_summary="No morning briefing to compare.",
        )

        assert comparison.has_morning_briefing is False
        assert comparison.morning_briefing_id is None
        assert len(comparison.comparisons) == 0


# =============================================================================
# Test: EODService - Issue Type Inference
# =============================================================================


class TestIssueTypeInference:
    """Tests for issue type inference from content."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = EODService()

    def test_infer_safety_issue(self):
        """Infer safety issue type from content."""
        assert self.service._infer_issue_type("Safety hazard in area B") == "safety"
        assert self.service._infer_issue_type("Potential injury risk") == "safety"
        assert self.service._infer_issue_type("Incident near line 3") == "safety"

    def test_infer_downtime_issue(self):
        """Infer downtime issue type from content."""
        assert self.service._infer_issue_type("Line 1 offline for maintenance") == "downtime"
        assert self.service._infer_issue_type("Machine stopped unexpectedly") == "downtime"
        assert self.service._infer_issue_type("Downtime risk on Line 2") == "downtime"

    def test_infer_quality_issue(self):
        """Infer quality issue type from content."""
        assert self.service._infer_issue_type("Quality defects increasing") == "quality"
        assert self.service._infer_issue_type("High reject rate on Line 1") == "quality"
        assert self.service._infer_issue_type("Scrap levels elevated") == "quality"

    def test_infer_production_default(self):
        """Default to production issue type."""
        assert self.service._infer_issue_type("Line 1 behind target") == "production"
        assert self.service._infer_issue_type("Output lower than expected") == "production"


# =============================================================================
# Test: EODService - Severity Inference
# =============================================================================


class TestSeverityInference:
    """Tests for severity inference from content."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = EODService()

    def test_infer_high_severity(self):
        """Infer high severity from content."""
        assert self.service._infer_severity("Critical issue on Line 1") == "high"
        assert self.service._infer_severity("Severe safety risk") == "high"
        assert self.service._infer_severity("Urgent attention needed") == "high"

    def test_infer_low_severity(self):
        """Infer low severity from content."""
        assert self.service._infer_severity("Minor delay expected") == "low"
        assert self.service._infer_severity("Small variance in output") == "low"

    def test_infer_medium_default(self):
        """Default to medium severity."""
        assert self.service._infer_severity("Line 1 behind target") == "medium"
        assert self.service._infer_severity("Watch for issues") == "medium"


# =============================================================================
# Test: EODService - Asset Info Extraction
# =============================================================================


class TestAssetInfoExtraction:
    """Tests for asset/area extraction from content."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = EODService()

    def test_extract_line_reference(self):
        """Extract line reference from content."""
        result = self.service._extract_asset_info("Line 1 behind target")
        assert result["asset_name"] == "Line 1"

        result = self.service._extract_asset_info("line 2 needs attention")
        assert result["asset_name"] == "Line 2"

    def test_extract_area_reference(self):
        """Extract area reference from content."""
        result = self.service._extract_asset_info("Issue in Area A")
        assert result["area"] == "Area A"

        result = self.service._extract_asset_info("area B has downtime")
        assert result["area"] == "Area B"

    def test_extract_both_line_and_area(self):
        """Extract both line and area from content."""
        result = self.service._extract_asset_info("Line 1 in Area A behind target")
        assert result["asset_name"] == "Line 1"
        assert result["area"] == "Area A"

    def test_no_extraction(self):
        """No extraction when no patterns match."""
        result = self.service._extract_asset_info("General production issue")
        assert result["asset_name"] is None
        assert result["area"] is None


# =============================================================================
# Test: EODService - Accuracy Metrics Calculation (AC#3)
# =============================================================================


class TestAccuracyMetricsCalculation:
    """Tests for accuracy metrics calculation (AC#3)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = EODService()

    def test_calculate_perfect_accuracy(self):
        """AC#3: Calculate 100% accuracy (all predictions correct)."""
        comparisons = [
            ConcernComparison(
                concern_id="mc-1",
                issue_type="production",
                morning_description="Test 1",
                outcome=ConcernOutcome.MATERIALIZED,
            ),
            ConcernComparison(
                concern_id="mc-2",
                issue_type="safety",
                morning_description="Test 2",
                outcome=ConcernOutcome.MATERIALIZED,
            ),
        ]
        unexpected = []

        metrics = self.service._calculate_accuracy_metrics(comparisons, unexpected)

        assert metrics.accuracy_percentage == 100.0
        assert metrics.total_predictions == 2
        assert metrics.correct_predictions == 2
        assert metrics.false_positives == 0
        assert metrics.misses == 0

    def test_calculate_with_false_positives(self):
        """AC#3: Calculate accuracy with false positives."""
        comparisons = [
            ConcernComparison(
                concern_id="mc-1",
                issue_type="production",
                morning_description="Test 1",
                outcome=ConcernOutcome.MATERIALIZED,
            ),
            ConcernComparison(
                concern_id="mc-2",
                issue_type="safety",
                morning_description="Test 2 (didn't happen)",
                outcome=ConcernOutcome.AVERTED,
            ),
        ]
        unexpected = []

        metrics = self.service._calculate_accuracy_metrics(comparisons, unexpected)

        assert metrics.total_predictions == 2
        assert metrics.correct_predictions == 1
        assert metrics.false_positives == 1  # Averted counts as false positive

    def test_calculate_with_misses(self):
        """AC#3: Calculate accuracy with misses (unexpected issues)."""
        comparisons = [
            ConcernComparison(
                concern_id="mc-1",
                issue_type="production",
                morning_description="Test 1",
                outcome=ConcernOutcome.MATERIALIZED,
            ),
        ]
        unexpected = ["Unexpected safety event", "Unexpected downtime"]

        metrics = self.service._calculate_accuracy_metrics(comparisons, unexpected)

        assert metrics.total_predictions == 1
        assert metrics.misses == 2
        # Accuracy = 1 / (1 + 2) = 33.3%
        assert metrics.accuracy_percentage == pytest.approx(33.3, 0.1)

    def test_calculate_with_escalations(self):
        """AC#3: Calculate accuracy with escalated concerns."""
        comparisons = [
            ConcernComparison(
                concern_id="mc-1",
                issue_type="production",
                morning_description="Test 1",
                outcome=ConcernOutcome.ESCALATED,
            ),
        ]
        unexpected = []

        metrics = self.service._calculate_accuracy_metrics(comparisons, unexpected)

        assert metrics.escalated_count == 1
        assert metrics.correct_predictions == 1  # Escalated counts as correct (issue did occur)

    def test_calculate_empty(self):
        """AC#3: Calculate accuracy with no data."""
        metrics = self.service._calculate_accuracy_metrics([], [])

        assert metrics.accuracy_percentage == 100.0  # No predictions, no issues = perfect
        assert metrics.total_predictions == 0


# =============================================================================
# Test: EODService - Comparison Summary Generation
# =============================================================================


class TestComparisonSummaryGeneration:
    """Tests for comparison summary generation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = EODService()

    def test_summary_high_accuracy(self):
        """Generate summary for high accuracy."""
        comparisons = [
            ConcernComparison(
                concern_id="mc-1",
                issue_type="production",
                morning_description="Test",
                outcome=ConcernOutcome.MATERIALIZED,
            ),
        ]
        metrics = AccuracyMetrics(
            accuracy_percentage=85.0,
            total_predictions=1,
            correct_predictions=1,
        )

        summary = self.service._generate_comparison_summary(comparisons, metrics, [])

        assert "85 percent" in summary
        assert "accurate" in summary

    def test_summary_with_escalations(self):
        """Generate summary mentioning escalations."""
        comparisons = [
            ConcernComparison(
                concern_id="mc-1",
                issue_type="production",
                morning_description="Test",
                outcome=ConcernOutcome.ESCALATED,
            ),
        ]
        metrics = AccuracyMetrics(
            accuracy_percentage=50.0,
            escalated_count=1,
        )

        summary = self.service._generate_comparison_summary(comparisons, metrics, [])

        assert "escalated" in summary.lower()

    def test_summary_with_unexpected(self):
        """Generate summary mentioning unexpected issues."""
        comparisons = []
        metrics = AccuracyMetrics(accuracy_percentage=0.0)
        unexpected = ["Issue 1", "Issue 2"]

        summary = self.service._generate_comparison_summary(comparisons, metrics, unexpected)

        assert "unexpected" in summary.lower()


# =============================================================================
# Test: EODService - Concern Classification (AC#2)
# =============================================================================


class TestConcernClassification:
    """Tests for concern outcome classification (AC#2)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = EODService()

    def test_classify_safety_averted(self):
        """AC#2: Classify safety concern as averted when no events."""
        concern = MorningConcern(
            concern_id="mc-1",
            description="Safety hazard in Area A",
            issue_type="safety",
            severity="medium",
            area="Area A",
        )

        briefing_data = BriefingData(
            safety_events=ToolResultData(
                tool_name="safety_events",
                success=True,
                data={"total_events": 0, "events": []},
            )
        )

        outcome, desc, notes = self.service._classify_safety_concern(concern, briefing_data)

        assert outcome == ConcernOutcome.AVERTED

    def test_classify_safety_materialized(self):
        """AC#2: Classify safety concern as materialized when matching event."""
        concern = MorningConcern(
            concern_id="mc-1",
            description="Safety hazard in Area A",
            issue_type="safety",
            severity="medium",
            area="Area A",
        )

        briefing_data = BriefingData(
            safety_events=ToolResultData(
                tool_name="safety_events",
                success=True,
                data={
                    "total_events": 1,
                    "events": [{"area": "Area A", "description": "Incident"}],
                },
            )
        )

        outcome, desc, notes = self.service._classify_safety_concern(concern, briefing_data)

        assert outcome == ConcernOutcome.MATERIALIZED

    def test_classify_downtime_averted(self):
        """AC#2: Classify downtime concern as averted."""
        concern = MorningConcern(
            concern_id="mc-1",
            description="Line 1 maintenance risk",
            issue_type="downtime",
            severity="medium",
        )

        briefing_data = BriefingData(
            downtime_analysis=ToolResultData(
                tool_name="downtime_analysis",
                success=True,
                data={"total_downtime_minutes": 0, "top_reasons": []},
            )
        )

        outcome, desc, notes = self.service._classify_downtime_concern(concern, briefing_data)

        assert outcome == ConcernOutcome.AVERTED

    def test_classify_production_averted(self):
        """AC#2: Classify production concern as averted when ahead."""
        concern = MorningConcern(
            concern_id="mc-1",
            description="Line 1 may fall behind",
            issue_type="production",
            severity="medium",
        )

        briefing_data = BriefingData(
            production_status=ToolResultData(
                tool_name="production_status",
                success=True,
                data={
                    "summary": {
                        "total_variance_percent": 5.0,
                        "behind_count": 0,
                    }
                },
            )
        )

        outcome, desc, notes = self.service._classify_production_concern(concern, briefing_data)

        assert outcome == ConcernOutcome.AVERTED

    def test_classify_production_escalated(self):
        """AC#2: Classify production concern as escalated when significantly behind."""
        concern = MorningConcern(
            concern_id="mc-1",
            description="Line 1 may fall behind",
            issue_type="production",
            severity="medium",
        )

        briefing_data = BriefingData(
            production_status=ToolResultData(
                tool_name="production_status",
                success=True,
                data={
                    "summary": {
                        "total_variance_percent": -15.0,
                        "behind_count": 2,
                    }
                },
            )
        )

        outcome, desc, notes = self.service._classify_production_concern(concern, briefing_data)

        assert outcome == ConcernOutcome.ESCALATED


# =============================================================================
# Test: EODService - Unexpected Issue Detection (AC#2)
# =============================================================================


class TestUnexpectedIssueDetection:
    """Tests for unexpected issue detection (AC#2)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = EODService()

    def test_detect_unexpected_safety(self):
        """AC#2: Detect unexpected safety event."""
        concerns = [
            MorningConcern(
                concern_id="mc-1",
                description="Production issue",
                issue_type="production",
                severity="medium",
            )
        ]

        briefing_data = BriefingData(
            safety_events=ToolResultData(
                tool_name="safety_events",
                success=True,
                data={
                    "total_events": 1,
                    "events": [{"description": "Near miss incident"}],
                },
            )
        )

        unexpected = self.service._detect_unexpected_issues(concerns, briefing_data)

        assert len(unexpected) > 0
        assert any("safety" in u.lower() for u in unexpected)

    def test_detect_unexpected_downtime(self):
        """AC#2: Detect unexpected downtime."""
        concerns = [
            MorningConcern(
                concern_id="mc-1",
                description="Safety concern",
                issue_type="safety",
                severity="medium",
            )
        ]

        briefing_data = BriefingData(
            downtime_analysis=ToolResultData(
                tool_name="downtime_analysis",
                success=True,
                data={
                    "total_downtime_minutes": 60,
                    "top_reasons": [
                        {"reason": "Equipment failure", "duration_minutes": 45}
                    ],
                },
            )
        )

        unexpected = self.service._detect_unexpected_issues(concerns, briefing_data)

        assert len(unexpected) > 0
        assert any("downtime" in u.lower() for u in unexpected)

    def test_no_unexpected_when_predicted(self):
        """AC#2: No unexpected when issues were predicted."""
        concerns = [
            MorningConcern(
                concern_id="mc-1",
                description="Equipment failure risk",
                issue_type="downtime",
                severity="medium",
            )
        ]

        briefing_data = BriefingData(
            downtime_analysis=ToolResultData(
                tool_name="downtime_analysis",
                success=True,
                data={
                    "total_downtime_minutes": 45,
                    "top_reasons": [
                        {"reason": "Equipment failure", "duration_minutes": 45}
                    ],
                },
            )
        )

        unexpected = self.service._detect_unexpected_issues(concerns, briefing_data)

        # Should not detect as unexpected since "equipment failure" was in concerns
        assert len([u for u in unexpected if "equipment failure" in u.lower()]) == 0


# =============================================================================
# Test: EODService - No Morning Briefing Handling (AC#5)
# =============================================================================


class TestNoMorningBriefingHandling:
    """Tests for no morning briefing handling (AC#5)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = EODService()

    @pytest.mark.asyncio
    async def test_compare_no_morning_briefing(self):
        """AC#5: Handle comparison when no morning briefing exists."""
        with patch.object(
            self.service, '_find_morning_briefing',
            new_callable=AsyncMock,
            return_value=None
        ):
            result = await self.service.compare_to_morning_briefing(
                user_id="test-user",
                summary_date=date.today(),
            )

            assert result.has_morning_briefing is False
            assert result.morning_briefing_id is None
            assert "No morning briefing" in result.comparison_summary


# =============================================================================
# Test: EODService - Structured Concern Extraction
# =============================================================================


class TestStructuredConcernExtraction:
    """Tests for extracting structured concerns from morning briefing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = EODService()

    def test_extract_from_sections(self):
        """Extract concerns from morning briefing sections."""
        morning_briefing = MorningBriefingRecord(
            id="mb-1",
            generated_at=datetime.now(timezone.utc),
            concerns=["Safety issue in Area A"],
            wins=["Line 1 on track"],
            sections=[
                {"type": "concerns", "content": "Line 2 may have downtime"},
            ],
        )

        structured = self.service._extract_structured_concerns(morning_briefing)

        assert len(structured) == 2
        assert any(c.issue_type == "safety" for c in structured)
        assert any(c.issue_type == "downtime" for c in structured)

    def test_extract_with_existing_structured(self):
        """Use existing structured concerns if available."""
        existing = [
            MorningConcern(
                concern_id="mc-1",
                description="Pre-structured concern",
                issue_type="quality",
                severity="high",
            )
        ]

        morning_briefing = MorningBriefingRecord(
            id="mb-1",
            generated_at=datetime.now(timezone.utc),
            concerns=[],
            wins=[],
            sections=[],
            structured_concerns=existing,
        )

        structured = self.service._extract_structured_concerns(morning_briefing)

        assert len(structured) == 1
        assert structured[0].concern_id == "mc-1"


# =============================================================================
# Test: EODService - Action Engine Feedback (AC#4)
# =============================================================================


class TestActionEngineFeedback:
    """Tests for Action Engine feedback generation (AC#4)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = EODService()

    def test_feedback_high_false_positives(self):
        """AC#4: Generate feedback for high false positives."""
        metrics = AccuracyMetrics(
            accuracy_percentage=30.0,
            correct_predictions=1,
            false_positives=3,
        )

        feedback = self.service.get_action_engine_feedback(metrics)

        assert "false positives" in str(feedback["recommendations"]).lower()
        assert feedback["weight_adjustments"].get("sensitivity") == -0.1

    def test_feedback_high_misses(self):
        """AC#4: Generate feedback for high misses."""
        metrics = AccuracyMetrics(
            accuracy_percentage=50.0,
            misses=3,
        )

        feedback = self.service.get_action_engine_feedback(metrics)

        assert "missing" in str(feedback["recommendations"]).lower()
        assert feedback["weight_adjustments"].get("sensitivity") == 0.1

    def test_feedback_escalations(self):
        """AC#4: Generate feedback for escalated concerns."""
        metrics = AccuracyMetrics(
            accuracy_percentage=70.0,
            escalated_count=2,
        )

        feedback = self.service.get_action_engine_feedback(metrics)

        assert "escalated" in str(feedback["recommendations"]).lower()
        assert "severity_factor" in feedback["weight_adjustments"]

    def test_feedback_good_accuracy(self):
        """AC#4: Generate positive feedback for good accuracy."""
        metrics = AccuracyMetrics(
            accuracy_percentage=85.0,
            correct_predictions=4,
            false_positives=1,
        )

        feedback = self.service.get_action_engine_feedback(metrics)

        assert "good" in str(feedback["recommendations"]).lower()


# =============================================================================
# Test: EODService - Accuracy Storage and Trends (AC#4)
# =============================================================================


class TestAccuracyStorageAndTrends:
    """Tests for accuracy storage and trend queries (AC#4)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = EODService()

    @pytest.mark.asyncio
    async def test_store_accuracy_metrics(self):
        """AC#4: Store accuracy metrics."""
        comparison_result = EODComparisonResult(
            morning_briefing_id="mb-1",
            has_morning_briefing=True,
            accuracy_metrics=AccuracyMetrics(
                accuracy_percentage=75.0,
                total_predictions=4,
                false_positives=1,
                misses=1,
            ),
        )

        result = await self.service.store_accuracy_metrics(
            user_id="test-user",
            summary_date=date.today(),
            comparison_result=comparison_result,
            eod_summary_id="eod-1",
        )

        # MVP implementation logs and returns True
        assert result is True

    @pytest.mark.asyncio
    async def test_get_accuracy_trends(self):
        """AC#4: Query accuracy trends."""
        trends = await self.service.get_accuracy_trends(
            user_id="test-user",
            days=30,
        )

        # MVP returns empty list
        assert isinstance(trends, list)
