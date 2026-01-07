"""
AI Services Module

Contains LLM integration and Smart Summary generation services.

Story: 3.5 - Smart Summary Generator
"""

from app.services.ai.smart_summary import (
    SmartSummaryService,
    SmartSummaryError,
    get_smart_summary_service,
)
from app.services.ai.llm_client import (
    get_llm_client,
    LLMClientError,
    check_llm_health,
)
from app.services.ai.context_builder import (
    ContextBuilder,
    SummaryContext,
)
from app.services.ai.prompts import (
    get_system_prompt,
    render_data_prompt,
)

__all__ = [
    "SmartSummaryService",
    "SmartSummaryError",
    "get_smart_summary_service",
    "get_llm_client",
    "LLMClientError",
    "check_llm_health",
    "ContextBuilder",
    "SummaryContext",
    "get_system_prompt",
    "render_data_prompt",
]
