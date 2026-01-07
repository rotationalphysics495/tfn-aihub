"""
Tests for Smart Summary Service

Story: 3.5 - Smart Summary Generator
Tests cover all acceptance criteria.
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.ai.smart_summary import (
    SmartSummaryService,
    SmartSummary,
    SmartSummaryError,
    get_smart_summary_service,
)
from app.services.ai.context_builder import (
    ContextBuilder,
    SummaryContext,
    ContextBuilderError,
)
from app.services.ai.prompts import (
    get_system_prompt,
    render_data_prompt,
    format_safety_events,
    format_oee_data,
    format_financial_data,
    format_action_items,
)
from app.services.ai.llm_client import (
    get_llm_client,
    get_llm_config,
    LLMConfig,
    LLMClientError,
    check_llm_health,
    estimate_tokens,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    client = MagicMock()
    return client


@pytest.fixture
def sample_daily_summaries():
    """Sample daily summary data."""
    return [
        {
            "id": "sum-1",
            "asset_id": "asset-1",
            "asset_name": "Grinder 5",
            "report_date": "2024-01-15",
            "oee_percentage": 72.5,
            "actual_output": 850,
            "target_output": 1000,
            "financial_loss_dollars": 2500.00,
            "downtime_minutes": 45,
            "waste_count": 15,
        },
        {
            "id": "sum-2",
            "asset_id": "asset-2",
            "asset_name": "Mill 3",
            "report_date": "2024-01-15",
            "oee_percentage": 88.0,
            "actual_output": 950,
            "target_output": 1000,
            "financial_loss_dollars": 500.00,
            "downtime_minutes": 10,
            "waste_count": 5,
        },
    ]


@pytest.fixture
def sample_safety_events():
    """Sample safety event data."""
    return [
        {
            "id": "safety-1",
            "asset_id": "asset-1",
            "asset_name": "Grinder 5",
            "event_timestamp": "2024-01-15T10:30:00Z",
            "duration_minutes": 15,
            "reason_code": "Emergency Stop",
            "severity": "critical",
            "description": "Operator triggered e-stop due to material jam",
            "is_resolved": False,
        },
    ]


@pytest.fixture
def sample_action_items():
    """Sample action item data."""
    return [
        {
            "id": "action-1",
            "asset_id": "asset-1",
            "asset_name": "Grinder 5",
            "category": "safety",
            "priority_level": "critical",
            "primary_metric_value": "Safety Event: Emergency Stop",
            "recommendation_text": "Investigate emergency stop on Grinder 5",
            "evidence_summary": "Unresolved safety event",
            "financial_impact_usd": 0,
        },
        {
            "id": "action-2",
            "asset_id": "asset-1",
            "asset_name": "Grinder 5",
            "category": "oee",
            "priority_level": "high",
            "primary_metric_value": "OEE: 72.5%",
            "recommendation_text": "Review performance on Grinder 5",
            "evidence_summary": "OEE 12.5% below target",
            "financial_impact_usd": 2500.00,
        },
    ]


@pytest.fixture
def sample_context(sample_daily_summaries, sample_safety_events, sample_action_items):
    """Sample SummaryContext for testing."""
    return SummaryContext(
        target_date=date(2024, 1, 15),
        daily_summaries=sample_daily_summaries,
        safety_events=sample_safety_events,
        cost_centers={},
        action_items=sample_action_items,
        assets={
            "asset-1": {"name": "Grinder 5"},
            "asset-2": {"name": "Mill 3"},
        },
        target_oee=85.0,
    )


# =============================================================================
# AC#1: LLM Integration Setup Tests
# =============================================================================

class TestLLMIntegration:
    """Tests for LLM client and configuration (AC#1)."""

    def test_llm_config_defaults(self):
        """Test default LLM configuration values."""
        with patch.dict('os.environ', {}, clear=True):
            config = LLMConfig()
            assert config.provider == "openai"
            assert config.temperature == 0.3
            assert config.timeout_seconds == 30
            assert config.max_tokens == 1500

    def test_llm_config_from_env(self):
        """Test LLM configuration from environment variables."""
        env = {
            "LLM_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "test-key",
            "LLM_MODEL": "claude-3-opus",
            "LLM_TEMPERATURE": "0.5",
            "LLM_TIMEOUT_SECONDS": "60",
        }
        with patch.dict('os.environ', env, clear=True):
            config = LLMConfig()
            assert config.provider == "anthropic"
            assert config.anthropic_api_key == "test-key"
            assert config.model == "claude-3-opus"
            assert config.temperature == 0.5
            assert config.timeout_seconds == 60

    def test_llm_config_is_configured(self):
        """Test is_configured property."""
        with patch.dict('os.environ', {"OPENAI_API_KEY": "test-key"}, clear=True):
            config = LLMConfig()
            assert config.is_configured is True

        with patch.dict('os.environ', {}, clear=True):
            config = LLMConfig()
            assert config.is_configured is False

    def test_get_llm_client_not_configured(self):
        """Test error when LLM not configured."""
        with patch.dict('os.environ', {}, clear=True):
            config = LLMConfig()
            with pytest.raises(LLMClientError) as exc_info:
                get_llm_client(config)
            assert "not configured" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_check_llm_health_not_configured(self):
        """Test health check when not configured."""
        with patch.dict('os.environ', {}, clear=True):
            result = await check_llm_health()
            assert result["healthy"] is False
            assert result["status"] == "not_configured"


# =============================================================================
# AC#2: Data Context Assembly Tests
# =============================================================================

class TestContextBuilder:
    """Tests for context building (AC#2)."""

    def test_summary_context_has_data(self, sample_context):
        """Test has_data property."""
        assert sample_context.has_data is True

        empty_context = SummaryContext(
            target_date=date(2024, 1, 15),
            daily_summaries=[],
            safety_events=[],
            action_items=[],
        )
        assert empty_context.has_data is False

    def test_summary_context_safety_count(self, sample_context):
        """Test safety_event_count property."""
        assert sample_context.safety_event_count == 1

    def test_summary_context_total_loss(self, sample_context):
        """Test total_financial_loss property."""
        assert sample_context.total_financial_loss == 3000.00

    @pytest.mark.asyncio
    async def test_fetch_daily_summaries(self, mock_supabase_client, sample_daily_summaries):
        """Test fetching daily summaries."""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=sample_daily_summaries
        )

        builder = ContextBuilder(supabase_client=mock_supabase_client)
        result = await builder.fetch_daily_summaries(date(2024, 1, 15))

        assert len(result) == 2
        assert result[0]["asset_name"] == "Grinder 5"

    @pytest.mark.asyncio
    async def test_fetch_safety_events(self, mock_supabase_client, sample_safety_events):
        """Test fetching safety events."""
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lt.return_value.execute.return_value = MagicMock(
            data=sample_safety_events
        )

        builder = ContextBuilder(supabase_client=mock_supabase_client)
        result = await builder.fetch_safety_events(date(2024, 1, 15))

        assert len(result) == 1
        assert result[0]["severity"] == "critical"


# =============================================================================
# AC#3: Prompt Engineering Tests
# =============================================================================

class TestPromptTemplates:
    """Tests for prompt templates (AC#3)."""

    def test_system_prompt_contains_requirements(self):
        """Test system prompt includes required elements."""
        prompt = get_system_prompt()

        # AC#3: Role instruction
        assert "manufacturing" in prompt.lower()
        assert "analyst" in prompt.lower()

        # AC#3: Citation requirements
        assert "cite" in prompt.lower() or "citation" in prompt.lower()

        # AC#3: Priority order
        assert "Safety" in prompt
        assert "Financial" in prompt

    def test_format_safety_events(self, sample_safety_events):
        """Test safety events formatting."""
        result = format_safety_events(sample_safety_events)

        assert "Grinder 5" in result
        assert "Emergency Stop" in result
        assert "critical" in result.lower()
        assert "UNRESOLVED" in result

    def test_format_safety_events_empty(self):
        """Test safety events formatting with no events."""
        result = format_safety_events([])
        assert "No safety events" in result

    def test_format_oee_data(self, sample_daily_summaries):
        """Test OEE data formatting."""
        result = format_oee_data(sample_daily_summaries, target_oee=85.0)

        assert "Grinder 5" in result
        assert "72.5%" in result
        assert "BELOW TARGET" in result
        assert "Target OEE: 85.0%" in result

    def test_format_financial_data(self, sample_daily_summaries):
        """Test financial data formatting."""
        result = format_financial_data(sample_daily_summaries)

        assert "$2,500.00" in result or "2500" in result
        assert "Grinder 5" in result
        assert "Total Financial Impact" in result

    def test_format_action_items(self, sample_action_items):
        """Test action items formatting."""
        result = format_action_items(sample_action_items)

        assert "SAFETY" in result
        assert "OEE" in result
        assert "Grinder 5" in result
        assert "critical" in result

    def test_render_data_prompt(self, sample_context):
        """Test complete data prompt rendering."""
        prompt = render_data_prompt(
            target_date=sample_context.target_date,
            safety_events=sample_context.safety_events,
            daily_summaries=sample_context.daily_summaries,
            action_items=sample_context.action_items,
            target_oee=sample_context.target_oee,
        )

        # Should include all sections
        assert "SAFETY EVENTS" in prompt
        assert "OEE PERFORMANCE" in prompt
        assert "FINANCIAL LOSSES" in prompt
        assert "ACTION ENGINE" in prompt
        assert "2024-01-15" in prompt


# =============================================================================
# AC#4 & AC#5: Smart Summary Generation Tests
# =============================================================================

class TestSmartSummaryGeneration:
    """Tests for summary generation (AC#4, AC#5)."""

    def test_extract_citations_asset_pattern(self):
        """Test citation extraction from asset pattern."""
        text = "Grinder 5 performance dropped [Asset: Grinder 5, OEE: 72%]"

        service = SmartSummaryService()
        citations = service.extract_citations(text)

        assert len(citations) >= 1
        assert any(c["asset_name"] == "Grinder 5" for c in citations)
        assert any(c["metric_name"] == "OEE" for c in citations)

    def test_extract_citations_source_pattern(self):
        """Test citation extraction from source pattern."""
        text = "Data from [Source: daily_summaries, 2024-01-15]"

        service = SmartSummaryService()
        citations = service.extract_citations(text)

        assert len(citations) >= 1
        assert any(c["source_table"] == "daily_summaries" for c in citations)

    def test_generate_fallback_summary(self, sample_context):
        """Test fallback summary generation (AC#8)."""
        service = SmartSummaryService()
        summary = service.generate_fallback_summary(
            sample_context,
            error_message="Test error"
        )

        assert summary.is_fallback is True
        assert "AI summary unavailable" in summary.summary_text
        assert "Grinder 5" in summary.summary_text
        assert summary.model_used == "fallback_template"

    def test_fallback_includes_safety_events(self, sample_context):
        """Test fallback includes safety events (AC#8)."""
        service = SmartSummaryService()
        summary = service.generate_fallback_summary(sample_context)

        assert "Safety Events" in summary.summary_text
        assert "Emergency Stop" in summary.summary_text

    def test_fallback_includes_oee_gaps(self, sample_context):
        """Test fallback includes OEE gaps (AC#8)."""
        service = SmartSummaryService()
        summary = service.generate_fallback_summary(sample_context)

        assert "OEE Below Target" in summary.summary_text
        assert "72.5%" in summary.summary_text

    def test_fallback_includes_financial_losses(self, sample_context):
        """Test fallback includes financial losses (AC#8)."""
        service = SmartSummaryService()
        summary = service.generate_fallback_summary(sample_context)

        assert "Financial" in summary.summary_text
        assert "2,500" in summary.summary_text or "2500" in summary.summary_text


# =============================================================================
# AC#6: Storage and Caching Tests
# =============================================================================

class TestStorageAndCaching:
    """Tests for storage and caching (AC#6)."""

    @pytest.mark.asyncio
    async def test_get_cached_summary_not_found(self, mock_supabase_client):
        """Test cache miss returns None."""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )

        service = SmartSummaryService(supabase_client=mock_supabase_client)
        result = await service.get_cached_summary(date(2024, 1, 15))

        assert result is None

    @pytest.mark.asyncio
    async def test_get_cached_summary_found(self, mock_supabase_client):
        """Test cache hit returns summary."""
        mock_data = {
            "id": "sum-123",
            "date": "2024-01-15",
            "summary_text": "Test summary",
            "citations_json": [],
            "model_used": "gpt-4",
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "generation_duration_ms": 1000,
            "is_fallback": False,
            "created_at": "2024-01-16T06:00:00Z",
            "updated_at": "2024-01-16T06:00:00Z",
        }
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[mock_data]
        )

        service = SmartSummaryService(supabase_client=mock_supabase_client)
        result = await service.get_cached_summary(date(2024, 1, 15))

        assert result is not None
        assert result.summary_text == "Test summary"
        assert result.model_used == "gpt-4"

    @pytest.mark.asyncio
    async def test_store_summary(self, mock_supabase_client):
        """Test storing a summary."""
        mock_supabase_client.table.return_value.upsert.return_value.execute.return_value = MagicMock()

        service = SmartSummaryService(supabase_client=mock_supabase_client)
        summary = SmartSummary(
            date=date(2024, 1, 15),
            summary_text="Test",
            model_used="gpt-4",
        )

        result = await service.store_summary(summary)

        assert result is True
        mock_supabase_client.table.assert_called_with("smart_summaries")

    @pytest.mark.asyncio
    async def test_invalidate_cache(self, mock_supabase_client):
        """Test cache invalidation."""
        mock_supabase_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock()

        service = SmartSummaryService(supabase_client=mock_supabase_client)
        result = await service.invalidate_cache(date(2024, 1, 15))

        assert result is True


# =============================================================================
# AC#10: Token Usage Monitoring Tests
# =============================================================================

class TestTokenUsageMonitoring:
    """Tests for token usage monitoring (AC#10)."""

    def test_estimate_tokens(self):
        """Test token estimation."""
        text = "This is a test sentence with some words."
        tokens = estimate_tokens(text)

        # Should return a positive number
        assert tokens > 0
        assert isinstance(tokens, int)

    @pytest.mark.asyncio
    async def test_log_token_usage(self, mock_supabase_client):
        """Test token usage logging."""
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = MagicMock()

        service = SmartSummaryService(supabase_client=mock_supabase_client)
        result = await service.log_token_usage(
            target_date=date(2024, 1, 15),
            provider="openai",
            model="gpt-4",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_get_token_usage_summary(self, mock_supabase_client):
        """Test getting usage summary."""
        mock_data = [
            {
                "date": "2024-01-15",
                "provider": "openai",
                "model": "gpt-4",
                "prompt_tokens": 1000,
                "completion_tokens": 500,
                "total_cost_usd": 0.05,
            },
            {
                "date": "2024-01-16",
                "provider": "openai",
                "model": "gpt-4",
                "prompt_tokens": 1200,
                "completion_tokens": 600,
                "total_cost_usd": 0.06,
            },
        ]
        mock_supabase_client.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value = MagicMock(
            data=mock_data
        )

        service = SmartSummaryService(supabase_client=mock_supabase_client)
        result = await service.get_token_usage_summary(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        assert result["total_generations"] == 2
        assert result["total_prompt_tokens"] == 2200
        assert result["total_completion_tokens"] == 1100


# =============================================================================
# Integration Tests
# =============================================================================

class TestSmartSummaryIntegration:
    """Integration tests for end-to-end flow."""

    @pytest.mark.asyncio
    async def test_generate_with_mocked_llm(self, mock_supabase_client, sample_context):
        """Test full generation flow with mocked LLM."""
        # Mock context builder
        mock_context_builder = MagicMock(spec=ContextBuilder)
        mock_context_builder.build_context = AsyncMock(return_value=sample_context)

        # Mock LLM response
        mock_response = MagicMock()
        mock_response.content = """## Executive Summary

Production targets were missed on Grinder 5 due to a safety event. [Asset: Grinder 5, OEE: 72%]

## Priority Issues

### 1. Safety Event - Emergency Stop
- **What Happened:** Emergency stop triggered [Source: safety_events, 2024-01-15]
- **Impact:** Production halted for 15 minutes
- **Recommended Action:** Investigate root cause"""

        mock_response.response_metadata = {
            "usage": {"prompt_tokens": 500, "completion_tokens": 200}
        }

        # Mock get_cached_summary to return None (cache miss)
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )
        # Mock upsert for storing
        mock_supabase_client.table.return_value.upsert.return_value.execute.return_value = MagicMock()
        # Mock insert for llm_usage
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = MagicMock()

        service = SmartSummaryService(
            supabase_client=mock_supabase_client,
            context_builder=mock_context_builder,
        )

        with patch('app.services.ai.smart_summary.get_llm_config') as mock_config:
            config_mock = MagicMock()
            config_mock.provider = "openai"
            config_mock.get_model_name.return_value = "gpt-4"
            config_mock.is_configured = True
            config_mock.token_usage_alert_threshold = 100000
            mock_config.return_value = config_mock
            with patch('app.services.ai.smart_summary.get_llm_client') as mock_client:
                mock_llm = MagicMock()
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)
                mock_client.return_value = mock_llm

                summary = await service.generate_smart_summary(
                    target_date=date(2024, 1, 15)
                )

        # Verify result
        assert summary.is_fallback is False
        assert "Grinder 5" in summary.summary_text
        assert len(summary.citations_json) > 0

    @pytest.mark.asyncio
    async def test_generate_falls_back_on_llm_error(self, mock_supabase_client, sample_context):
        """Test fallback when LLM fails."""
        mock_context_builder = MagicMock(spec=ContextBuilder)
        mock_context_builder.build_context = AsyncMock(return_value=sample_context)

        # Mock cache miss
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )
        # Mock upsert
        mock_supabase_client.table.return_value.upsert.return_value.execute.return_value = MagicMock()

        service = SmartSummaryService(
            supabase_client=mock_supabase_client,
            context_builder=mock_context_builder,
        )

        with patch('app.services.ai.smart_summary.get_llm_config') as mock_config:
            mock_config.return_value = MagicMock(
                provider="openai",
                get_model_name=lambda: "gpt-4",
                is_configured=True,
            )
            with patch('app.services.ai.smart_summary.get_llm_client') as mock_client:
                mock_llm = MagicMock()
                mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM Error"))
                mock_client.return_value = mock_llm

                summary = await service.generate_smart_summary(
                    target_date=date(2024, 1, 15)
                )

        # Should use fallback
        assert summary.is_fallback is True
        assert "AI summary unavailable" in summary.summary_text
