"""
Briefing Services Package (Story 8.3, 8.6)

Provides briefing synthesis and generation services.
Orchestrates existing LangChain tools into coherent narratives.

Components:
- BriefingService: Main orchestration service
- NarrativeGenerator: LLM-powered narrative formatting
- Voice formatters: Natural language formatting for numbers (Story 8.6)
"""

from app.services.briefing.service import BriefingService, get_briefing_service
from app.services.briefing.narrative import NarrativeGenerator, get_narrative_generator
from app.services.briefing.formatters import (
    format_number_for_voice,
    format_percentage_for_voice,
    format_currency_for_voice,
    format_duration_for_voice,
    format_for_voice,
    detect_and_format,
)

__all__ = [
    "BriefingService",
    "get_briefing_service",
    "NarrativeGenerator",
    "get_narrative_generator",
    # Voice formatters (Story 8.6)
    "format_number_for_voice",
    "format_percentage_for_voice",
    "format_currency_for_voice",
    "format_duration_for_voice",
    "format_for_voice",
    "detect_and_format",
]
