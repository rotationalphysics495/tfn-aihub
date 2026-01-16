"""
Briefing Services Package (Story 8.3)

Provides briefing synthesis and generation services.
Orchestrates existing LangChain tools into coherent narratives.

Components:
- BriefingService: Main orchestration service
- NarrativeGenerator: LLM-powered narrative formatting
"""

from app.services.briefing.service import BriefingService, get_briefing_service
from app.services.briefing.narrative import NarrativeGenerator, get_narrative_generator

__all__ = [
    "BriefingService",
    "get_briefing_service",
    "NarrativeGenerator",
    "get_narrative_generator",
]
