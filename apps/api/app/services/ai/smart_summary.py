"""
Smart Summary Service

Main service for generating AI-powered smart summaries for manufacturing reports.

Story: 3.5 - Smart Summary Generator
AC: #1 - LLM Integration Setup
AC: #4 - Smart Summary Generation
AC: #5 - Data Citation Requirement (NFR1 Compliance)
AC: #6 - Summary Storage and Caching
AC: #7 - API Endpoint (service layer)
AC: #8 - Fallback Behavior for LLM Failures
AC: #10 - Token Usage Monitoring
"""

import json
import logging
import re
import time
from datetime import date as date_type, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel, Field
from supabase import create_client, Client
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.core.config import get_settings
from app.services.ai.llm_client import (
    get_llm_client,
    get_llm_config,
    LLMClientError,
    estimate_tokens,
)
from app.services.ai.context_builder import (
    ContextBuilder,
    SummaryContext,
    get_context_builder,
)
from app.services.ai.prompts import (
    get_system_prompt,
    render_data_prompt,
)

logger = logging.getLogger(__name__)


class SmartSummaryError(Exception):
    """Base exception for Smart Summary errors."""
    pass


class Citation(BaseModel):
    """
    Structured citation extracted from summary text.

    AC#5: Citations reference specific asset names, timestamps, or metric values.
    """

    asset_name: Optional[str] = Field(None, description="Referenced asset name")
    metric_name: str = Field(..., description="Name of the metric")
    metric_value: str = Field(..., description="Value of the metric")
    source_table: str = Field(..., description="Source database table")
    timestamp: Optional[str] = Field(None, description="Reference timestamp")


class SmartSummary(BaseModel):
    """
    Smart Summary model for storage and API response.

    AC#6: Stored in smart_summaries table with specified fields.
    """

    id: Optional[str] = Field(None, description="UUID of the summary")
    date: date_type = Field(..., description="Report date")
    summary_text: str = Field(..., description="Generated markdown summary")
    citations_json: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Extracted citations for verification"
    )
    model_used: str = Field(..., description="LLM model identifier")
    prompt_tokens: int = Field(0, description="Number of prompt tokens used")
    completion_tokens: int = Field(0, description="Number of completion tokens")
    generation_duration_ms: int = Field(0, description="Generation time in milliseconds")
    is_fallback: bool = Field(False, description="Whether fallback was used")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class SmartSummaryService:
    """
    Service for generating and managing Smart Summaries.

    Orchestrates context building, LLM generation, citation extraction,
    storage, and caching.
    """

    def __init__(
        self,
        supabase_client: Optional[Client] = None,
        context_builder: Optional[ContextBuilder] = None,
    ):
        """
        Initialize the Smart Summary Service.

        Args:
            supabase_client: Optional Supabase client
            context_builder: Optional ContextBuilder instance
        """
        self._client = supabase_client
        self._context_builder = context_builder

    def _get_client(self) -> Client:
        """Get or create Supabase client."""
        if self._client is None:
            settings = get_settings()
            if not settings.supabase_url or not settings.supabase_key:
                raise SmartSummaryError("Supabase not configured")
            self._client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
        return self._client

    def _get_context_builder(self) -> ContextBuilder:
        """Get or create ContextBuilder instance."""
        if self._context_builder is None:
            self._context_builder = get_context_builder()
        return self._context_builder

    def extract_citations(self, summary_text: str) -> List[Dict[str, Any]]:
        """
        Extract structured citations from summary text.

        AC#5: UI can hyperlink citations to drill-down views.
        Pattern: [Asset: <name>, <metric>: <value>] or [Source: <table>, <date>]

        Args:
            summary_text: Generated summary markdown

        Returns:
            List of citation dictionaries
        """
        citations = []

        # Pattern for asset citations: [Asset: Name, Metric: Value]
        asset_pattern = r'\[Asset:\s*([^,\]]+),\s*([^:]+):\s*([^\]]+)\]'
        for match in re.finditer(asset_pattern, summary_text):
            citations.append({
                "asset_name": match.group(1).strip(),
                "metric_name": match.group(2).strip(),
                "metric_value": match.group(3).strip(),
                "source_table": "daily_summaries",
            })

        # Pattern for source citations: [Source: table, date]
        source_pattern = r'\[Source:\s*([^,\]]+),?\s*([^\]]*)\]'
        for match in re.finditer(source_pattern, summary_text):
            citations.append({
                "source_table": match.group(1).strip(),
                "timestamp": match.group(2).strip() if match.group(2) else None,
                "metric_name": "source_reference",
                "metric_value": match.group(1).strip(),
            })

        return citations

    def generate_fallback_summary(
        self,
        context: SummaryContext,
        error_message: Optional[str] = None,
    ) -> SmartSummary:
        """
        Generate a template-based fallback summary when LLM is unavailable.

        AC#8: System falls back to a template-based summary.
        - Clearly indicates "AI summary unavailable"
        - Critical metrics still displayed

        Args:
            context: Assembled context data
            error_message: Optional error message to log

        Returns:
            SmartSummary with fallback content
        """
        if error_message:
            logger.warning(f"Using fallback summary: {error_message}")

        lines = [
            "## Executive Summary",
            "",
            "**AI summary unavailable - showing key metrics**",
            "",
        ]

        # Safety events section
        unresolved_events = [
            e for e in context.safety_events
            if not e.get("is_resolved", False)
        ]
        if unresolved_events:
            lines.append("## Safety Events (Requires Immediate Attention)")
            lines.append("")
            for event in unresolved_events:
                asset_name = event.get("asset_name", "Unknown")
                reason = event.get("reason_code", "Safety Issue")
                severity = event.get("severity", "critical")
                lines.append(
                    f"- **{asset_name}**: {reason} "
                    f"(Severity: {severity}) [Source: safety_events, {context.target_date}]"
                )
            lines.append("")

        # OEE performance section
        below_target = [
            s for s in context.daily_summaries
            if (s.get("oee_percentage", 0) or 0) < context.target_oee
        ]
        if below_target:
            lines.append("## OEE Below Target")
            lines.append("")
            for summary in sorted(
                below_target,
                key=lambda x: x.get("oee_percentage", 0) or 0
            )[:5]:
                asset_name = summary.get("asset_name", "Unknown")
                oee = summary.get("oee_percentage", 0) or 0
                gap = context.target_oee - oee
                lines.append(
                    f"- **{asset_name}**: OEE {oee:.1f}% "
                    f"({gap:.1f}% below target) [Asset: {asset_name}, OEE: {oee:.1f}%]"
                )
            lines.append("")

        # Financial losses section
        total_loss = context.total_financial_loss
        if total_loss > 0:
            lines.append("## Financial Losses")
            lines.append("")
            lines.append(f"Total Financial Impact: **${total_loss:,.2f}**")
            lines.append("")
            for summary in sorted(
                context.daily_summaries,
                key=lambda x: x.get("financial_loss_dollars", 0) or 0,
                reverse=True
            )[:5]:
                loss = summary.get("financial_loss_dollars", 0) or 0
                if loss > 0:
                    asset_name = summary.get("asset_name", "Unknown")
                    lines.append(
                        f"- **{asset_name}**: ${loss:,.2f} "
                        f"[Source: daily_summaries, {context.target_date}]"
                    )
            lines.append("")

        # Data sources section
        lines.append("## Data Sources Referenced")
        lines.append("")
        lines.append(f"- daily_summaries ({context.target_date})")
        lines.append(f"- safety_events ({context.target_date})")
        lines.append("- cost_centers")

        summary_text = "\n".join(lines)

        return SmartSummary(
            date=context.target_date,
            summary_text=summary_text,
            citations_json=self.extract_citations(summary_text),
            model_used="fallback_template",
            prompt_tokens=0,
            completion_tokens=0,
            generation_duration_ms=0,
            is_fallback=True,
        )

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((TimeoutError, ConnectionError)),
    )
    async def _generate_with_llm(
        self,
        context: SummaryContext,
    ) -> Tuple[str, int, int, int]:
        """
        Generate summary using LLM with retry logic.

        AC#4: LLM generates the summary with specified requirements.

        Args:
            context: Assembled context data

        Returns:
            Tuple of (summary_text, prompt_tokens, completion_tokens, duration_ms)
        """
        config = get_llm_config()
        client = get_llm_client(config)

        # Build prompts
        system_prompt = get_system_prompt()
        data_prompt = render_data_prompt(
            target_date=context.target_date,
            safety_events=context.safety_events,
            daily_summaries=context.daily_summaries,
            action_items=context.action_items,
            cost_centers=context.cost_centers,
            target_oee=context.target_oee,
        )

        # Estimate tokens for logging
        estimated_prompt_tokens = estimate_tokens(system_prompt + data_prompt)

        logger.info(
            f"Generating smart summary with {config.provider} "
            f"(~{estimated_prompt_tokens} tokens)"
        )

        from langchain_core.messages import SystemMessage, HumanMessage

        start_time = time.time()

        try:
            # AC#4: Generation completes within 30 seconds (timeout in config)
            response = await client.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=data_prompt),
            ])

            duration_ms = int((time.time() - start_time) * 1000)

            # Extract token usage if available
            prompt_tokens = estimated_prompt_tokens
            completion_tokens = 0

            if hasattr(response, "response_metadata"):
                usage = response.response_metadata.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", estimated_prompt_tokens)
                completion_tokens = usage.get("completion_tokens", 0)
            elif hasattr(response, "usage_metadata"):
                usage = response.usage_metadata
                prompt_tokens = getattr(usage, "input_tokens", estimated_prompt_tokens)
                completion_tokens = getattr(usage, "output_tokens", 0)

            summary_text = response.content

            logger.info(
                f"Summary generated in {duration_ms}ms "
                f"(prompt: {prompt_tokens}, completion: {completion_tokens})"
            )

            return summary_text, prompt_tokens, completion_tokens, duration_ms

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"LLM generation failed after {duration_ms}ms: {e}")
            raise

    async def generate_smart_summary(
        self,
        target_date: Optional[date_type] = None,
        regenerate: bool = False,
    ) -> SmartSummary:
        """
        Generate a Smart Summary for the given date.

        AC#4: Main generation function with all requirements.
        AC#6: Caching with optional regeneration.
        AC#8: Fallback on LLM failure.
        AC#10: Token usage logged.

        Args:
            target_date: Date to generate summary for (defaults to T-1)
            regenerate: If True, bypass cache and regenerate

        Returns:
            SmartSummary with generated content
        """
        if target_date is None:
            target_date = date_type.today() - timedelta(days=1)

        logger.info(f"Generating smart summary for {target_date}")

        # AC#6: Check cache first (unless regenerate=True)
        if not regenerate:
            cached = await self.get_cached_summary(target_date)
            if cached:
                logger.info(f"Returning cached summary for {target_date}")
                return cached

        # Build context
        context_builder = self._get_context_builder()
        context = await context_builder.build_context(target_date)

        if not context.has_data:
            logger.warning(f"No data available for {target_date}, using fallback")
            return self.generate_fallback_summary(
                context,
                error_message="No data available for date"
            )

        config = get_llm_config()

        try:
            # Generate with LLM
            summary_text, prompt_tokens, completion_tokens, duration_ms = \
                await self._generate_with_llm(context)

            # Extract citations
            citations = self.extract_citations(summary_text)

            summary = SmartSummary(
                date=target_date,
                summary_text=summary_text,
                citations_json=citations,
                model_used=config.get_model_name(),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                generation_duration_ms=duration_ms,
                is_fallback=False,
            )

            # AC#10: Log token usage
            await self.log_token_usage(
                target_date=target_date,
                provider=config.provider,
                model=config.get_model_name(),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )

            # AC#6: Store summary
            await self.store_summary(summary)

            return summary

        except Exception as e:
            # AC#8: Fall back to template on LLM failure
            logger.error(f"LLM generation failed, using fallback: {e}")
            fallback = self.generate_fallback_summary(
                context,
                error_message=str(e)
            )
            await self.store_summary(fallback)
            return fallback

    async def get_cached_summary(self, target_date: date_type) -> Optional[SmartSummary]:
        """
        Get cached summary from database.

        AC#6: Summaries are cached to avoid regeneration.

        Args:
            target_date: Date to query

        Returns:
            SmartSummary if found, None otherwise
        """
        try:
            client = self._get_client()

            response = client.table("smart_summaries").select("*").eq(
                "date", target_date.isoformat()
            ).execute()

            if not response.data:
                return None

            data = response.data[0]
            return SmartSummary(
                id=data.get("id"),
                date=date_type.fromisoformat(data.get("date")),
                summary_text=data.get("summary_text", ""),
                citations_json=data.get("citations_json", []),
                model_used=data.get("model_used", ""),
                prompt_tokens=data.get("prompt_tokens", 0),
                completion_tokens=data.get("completion_tokens", 0),
                generation_duration_ms=data.get("generation_duration_ms", 0),
                is_fallback=data.get("is_fallback", False),
                created_at=datetime.fromisoformat(data.get("created_at").replace("Z", "+00:00"))
                if data.get("created_at") else None,
                updated_at=datetime.fromisoformat(data.get("updated_at").replace("Z", "+00:00"))
                if data.get("updated_at") else None,
            )

        except Exception as e:
            logger.error(f"Failed to get cached summary: {e}")
            return None

    async def store_summary(self, summary: SmartSummary) -> bool:
        """
        Store or update a summary in the database.

        AC#6: Upsert pattern for idempotency.

        Args:
            summary: SmartSummary to store

        Returns:
            True if successful
        """
        try:
            client = self._get_client()

            data = {
                "date": summary.date.isoformat(),
                "summary_text": summary.summary_text,
                "citations_json": summary.citations_json,
                "model_used": summary.model_used,
                "prompt_tokens": summary.prompt_tokens,
                "completion_tokens": summary.completion_tokens,
                "generation_duration_ms": summary.generation_duration_ms,
                "is_fallback": summary.is_fallback,
                "updated_at": datetime.utcnow().isoformat(),
            }

            # Upsert on date (unique constraint)
            response = client.table("smart_summaries").upsert(
                data,
                on_conflict="date"
            ).execute()

            logger.debug(f"Stored summary for {summary.date}")
            return True

        except Exception as e:
            logger.error(f"Failed to store summary: {e}")
            return False

    async def invalidate_cache(self, target_date: date_type) -> bool:
        """
        Invalidate cached summary for a date.

        AC#6: Cache invalidation when source data is updated.

        Args:
            target_date: Date to invalidate

        Returns:
            True if invalidated
        """
        try:
            client = self._get_client()

            response = client.table("smart_summaries").delete().eq(
                "date", target_date.isoformat()
            ).execute()

            logger.info(f"Invalidated cache for {target_date}")
            return True

        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")
            return False

    async def log_token_usage(
        self,
        target_date: date_type,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> bool:
        """
        Log token usage for cost tracking.

        AC#10: Token usage is logged and tracked.

        Args:
            target_date: Report date
            provider: LLM provider name
            model: Model identifier
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            True if logged successfully
        """
        total_tokens = prompt_tokens + completion_tokens

        # Check alert threshold
        config = get_llm_config()
        if total_tokens > config.token_usage_alert_threshold:
            logger.warning(
                f"Token usage alert: {total_tokens} tokens exceeds threshold "
                f"of {config.token_usage_alert_threshold}"
            )

        logger.info(
            f"Token usage for {target_date}: "
            f"prompt={prompt_tokens}, completion={completion_tokens}, "
            f"total={total_tokens}, provider={provider}, model={model}"
        )

        # Store in database if llm_usage table exists
        try:
            client = self._get_client()

            # Estimate cost (rough estimates)
            cost_per_1k_input = 0.01  # $0.01 per 1k input tokens (GPT-4 Turbo approx)
            cost_per_1k_output = 0.03  # $0.03 per 1k output tokens
            estimated_cost = (
                (prompt_tokens / 1000) * cost_per_1k_input +
                (completion_tokens / 1000) * cost_per_1k_output
            )

            data = {
                "date": target_date.isoformat(),
                "provider": provider,
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_cost_usd": round(estimated_cost, 6),
            }

            client.table("llm_usage").insert(data).execute()
            return True

        except Exception as e:
            # Log but don't fail if usage table doesn't exist
            logger.debug(f"Could not log to llm_usage table: {e}")
            return False

    async def get_token_usage_summary(
        self,
        start_date: Optional[date_type] = None,
        end_date: Optional[date_type] = None,
    ) -> Dict[str, Any]:
        """
        Get aggregated token usage for cost management.

        AC#10: Daily/monthly token usage is tracked.

        Args:
            start_date: Start of period (defaults to start of month)
            end_date: End of period (defaults to today)

        Returns:
            Usage summary dictionary
        """
        if end_date is None:
            end_date = date_type.today()
        if start_date is None:
            start_date = end_date.replace(day=1)

        try:
            client = self._get_client()

            response = client.table("llm_usage").select(
                "date, provider, model, prompt_tokens, completion_tokens, total_cost_usd"
            ).gte(
                "date", start_date.isoformat()
            ).lte(
                "date", end_date.isoformat()
            ).execute()

            records = response.data or []

            total_prompt_tokens = sum(r.get("prompt_tokens", 0) for r in records)
            total_completion_tokens = sum(r.get("completion_tokens", 0) for r in records)
            total_cost = sum(r.get("total_cost_usd", 0) for r in records)

            return {
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "total_generations": len(records),
                "total_prompt_tokens": total_prompt_tokens,
                "total_completion_tokens": total_completion_tokens,
                "total_tokens": total_prompt_tokens + total_completion_tokens,
                "estimated_cost_usd": round(total_cost, 2),
            }

        except Exception as e:
            logger.error(f"Failed to get usage summary: {e}")
            return {
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "total_generations": 0,
                "total_prompt_tokens": 0,
                "total_completion_tokens": 0,
                "total_tokens": 0,
                "estimated_cost_usd": 0,
                "error": str(e),
            }


# Module-level singleton
_smart_summary_service: Optional[SmartSummaryService] = None


def get_smart_summary_service() -> SmartSummaryService:
    """Get or create singleton SmartSummaryService instance."""
    global _smart_summary_service
    if _smart_summary_service is None:
        _smart_summary_service = SmartSummaryService()
    return _smart_summary_service
