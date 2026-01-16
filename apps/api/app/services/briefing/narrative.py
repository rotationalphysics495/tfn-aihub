"""
Narrative Generator (Story 8.3)

LLM-powered narrative formatting for briefings.
Transforms tool data into natural language sections.

AC#2: Narrative Generation
- Headline summary
- Top wins (areas >100% target)
- Top concerns (gaps, issues)
- Recommended actions
- All metrics include citations

References:
- [Source: architecture/voice-briefing.md#BriefingService Architecture]
"""

import logging
import json
from typing import Optional, List, Dict, Any

from app.models.briefing import (
    BriefingSection,
    BriefingSectionStatus,
    BriefingMetric,
    BriefingCitation,
    BriefingData,
)

logger = logging.getLogger(__name__)


# Narrative generation prompt template
NARRATIVE_PROMPT = """You are a manufacturing briefing narrator. Transform the following data into natural, conversational briefing sections.

DATA:
{data}

Generate briefing sections in this JSON format:
{{
  "headline": {{
    "title": "Morning Briefing Summary",
    "content": "A 1-2 sentence executive summary of plant status"
  }},
  "wins": {{
    "title": "Top Wins",
    "content": "2-3 sentences highlighting areas/assets performing above target"
  }},
  "concerns": {{
    "title": "Areas of Concern",
    "content": "2-3 sentences about safety issues, OEE gaps, or downtime problems"
  }},
  "actions": {{
    "title": "Recommended Actions",
    "content": "2-3 prioritized action items for the day"
  }}
}}

Guidelines:
- Be conversational, not robotic ("We're tracking slightly behind" not "Variance: -3.2%")
- Round large numbers naturally ("about 145,000 units" not "145,230 units")
- Include [Source: table_name] citations after key metrics
- Start safety section with status (all clear vs issues)
- Keep each section under 50 words
- Use encouraging tone for wins, constructive tone for concerns

Respond with ONLY the JSON, no additional text.
"""


class NarrativeGenerator:
    """
    LLM-powered narrative generator for briefings.

    Story 8.3 AC#2: Narrative Generation
    - Transforms structured tool data into conversational narratives
    - Generates headline, wins, concerns, and actions sections
    - Includes inline citations for all metrics
    """

    def __init__(self, llm_client=None):
        """
        Initialize narrative generator.

        Args:
            llm_client: Optional LLM client (for testing). Uses default if not provided.
        """
        self._llm_client = llm_client

    def _get_llm_client(self):
        """Get LLM client (lazy init)."""
        if self._llm_client is None:
            try:
                from app.services.ai.llm_client import get_llm_client
                self._llm_client = get_llm_client()
            except Exception as e:
                logger.warning(f"Could not get LLM client: {e}")
                return None
        return self._llm_client

    async def generate_sections(
        self,
        briefing_data: BriefingData,
    ) -> List[BriefingSection]:
        """
        Generate narrative sections from briefing data.

        AC#2: Generates headline, wins, concerns, actions sections.

        Args:
            briefing_data: Aggregated data from tool orchestration

        Returns:
            List of BriefingSection with narrative content
        """
        # Prepare data summary for LLM
        data_summary = self._prepare_data_summary(briefing_data)

        # Try LLM generation
        llm = self._get_llm_client()
        if llm:
            try:
                sections = await self._generate_with_llm(data_summary, briefing_data)
                if sections:
                    return sections
            except Exception as e:
                logger.warning(f"LLM narrative generation failed: {e}")

        # Fall back to template-based generation
        return self._generate_with_template(briefing_data)

    def _prepare_data_summary(self, briefing_data: BriefingData) -> str:
        """Prepare data summary for LLM prompt."""
        summary_parts = []

        # Production status
        if briefing_data.production_status and briefing_data.production_status.success:
            data = briefing_data.production_status.data or {}
            summary = data.get("summary", {})
            summary_parts.append(f"""
PRODUCTION STATUS:
- Total Output: {summary.get('total_output', 'N/A')} units
- Target: {summary.get('total_target', 'N/A')} units
- Variance: {summary.get('total_variance_percent', 'N/A')}%
- Assets Ahead: {summary.get('ahead_count', 0)}
- Assets Behind: {summary.get('behind_count', 0)}
- Needing Attention: {', '.join(summary.get('assets_needing_attention', [])[:3])}
[Source: live_snapshots]""")

        # Safety events
        if briefing_data.safety_events and briefing_data.safety_events.success:
            data = briefing_data.safety_events.data or {}
            total = data.get("total_events", 0)
            summary_parts.append(f"""
SAFETY:
- Total Events (24h): {total}
- Status: {'All Clear' if total == 0 else 'Incidents Reported'}
[Source: safety_incidents]""")

        # OEE
        if briefing_data.oee_data and briefing_data.oee_data.success:
            data = briefing_data.oee_data.data or {}
            summary_parts.append(f"""
OEE:
- Plant OEE: {data.get('oee_percentage', data.get('oee', 'N/A'))}%
- Availability: {data.get('availability', 'N/A')}%
- Performance: {data.get('performance', 'N/A')}%
- Quality: {data.get('quality', 'N/A')}%
[Source: daily_summaries]""")

        # Downtime
        if briefing_data.downtime_analysis and briefing_data.downtime_analysis.success:
            data = briefing_data.downtime_analysis.data or {}
            reasons = data.get("top_reasons", [])[:3]
            reason_text = "; ".join([
                f"{r.get('reason', 'Unknown')}: {r.get('duration_minutes', 0)}min"
                for r in reasons
            ]) if reasons else "No significant downtime"
            summary_parts.append(f"""
DOWNTIME:
- Top Reasons: {reason_text}
[Source: downtime_events]""")

        # Actions
        if briefing_data.action_list and briefing_data.action_list.success:
            data = briefing_data.action_list.data or {}
            actions = data.get("actions", [])[:3]
            action_text = "; ".join([
                a.get("title", "Action") for a in actions
            ]) if actions else "No critical actions"
            summary_parts.append(f"""
RECOMMENDED ACTIONS:
- Priorities: {action_text}
[Source: action_recommendations]""")

        return "\n".join(summary_parts) if summary_parts else "No data available."

    async def _generate_with_llm(
        self,
        data_summary: str,
        briefing_data: BriefingData,
    ) -> Optional[List[BriefingSection]]:
        """Generate narrative using LLM."""
        llm = self._get_llm_client()
        if not llm:
            return None

        prompt = NARRATIVE_PROMPT.format(data=data_summary)

        try:
            # Call LLM
            response = await llm.agenerate(messages=[{"role": "user", "content": prompt}])

            # Parse response
            if hasattr(response, 'generations') and response.generations:
                text = response.generations[0][0].text
            elif hasattr(response, 'content'):
                text = response.content
            else:
                text = str(response)

            # Parse JSON
            # Find JSON in response
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = text[start_idx:end_idx]
                narrative_data = json.loads(json_str)
            else:
                logger.warning("No JSON found in LLM response")
                return None

            # Convert to sections
            sections = []
            all_citations = briefing_data.all_citations

            for section_type in ["headline", "wins", "concerns", "actions"]:
                if section_type in narrative_data:
                    section_data = narrative_data[section_type]
                    sections.append(BriefingSection(
                        section_type=section_type,
                        title=section_data.get("title", section_type.title()),
                        content=section_data.get("content", ""),
                        citations=all_citations,
                        status=BriefingSectionStatus.COMPLETE,
                        pause_point=True,
                    ))

            return sections if sections else None

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM JSON response: {e}")
            return None
        except Exception as e:
            logger.warning(f"LLM generation error: {e}")
            return None

    def _generate_with_template(
        self,
        briefing_data: BriefingData,
    ) -> List[BriefingSection]:
        """
        Generate narrative using templates (fallback).

        Used when LLM is unavailable or fails.
        """
        sections = []
        all_citations = briefing_data.all_citations

        # Headline
        headline_content = self._generate_headline_template(briefing_data)
        sections.append(BriefingSection(
            section_type="headline",
            title="Morning Briefing Summary",
            content=headline_content,
            citations=all_citations,
            status=BriefingSectionStatus.COMPLETE,
            pause_point=True,
        ))

        # Wins
        wins_content = self._generate_wins_template(briefing_data)
        if wins_content:
            sections.append(BriefingSection(
                section_type="wins",
                title="Top Wins",
                content=wins_content,
                citations=all_citations,
                status=BriefingSectionStatus.COMPLETE,
                pause_point=True,
            ))

        # Concerns
        concerns_content = self._generate_concerns_template(briefing_data)
        sections.append(BriefingSection(
            section_type="concerns",
            title="Areas of Concern",
            content=concerns_content,
            citations=all_citations,
            status=BriefingSectionStatus.COMPLETE,
            pause_point=True,
        ))

        # Actions
        actions_content = self._generate_actions_template(briefing_data)
        sections.append(BriefingSection(
            section_type="actions",
            title="Recommended Actions",
            content=actions_content,
            citations=all_citations,
            status=BriefingSectionStatus.COMPLETE,
            pause_point=True,
        ))

        return sections

    def _generate_headline_template(self, briefing_data: BriefingData) -> str:
        """Generate headline using template."""
        parts = []

        # Safety first
        if briefing_data.safety_events and briefing_data.safety_events.success:
            data = briefing_data.safety_events.data or {}
            if data.get("total_events", 0) == 0:
                parts.append("Good morning! No safety incidents to report.")
            else:
                parts.append(f"Attention: {data.get('total_events')} safety event(s) require review.")

        # Production summary
        if briefing_data.production_status and briefing_data.production_status.success:
            data = briefing_data.production_status.data or {}
            summary = data.get("summary", {})
            variance = summary.get("total_variance_percent", 0)
            if variance >= 0:
                parts.append(f"Production is tracking {abs(variance):.1f}% ahead of target.")
            else:
                parts.append(f"Production is {abs(variance):.1f}% behind target.")

        # OEE
        if briefing_data.oee_data and briefing_data.oee_data.success:
            data = briefing_data.oee_data.data or {}
            oee = data.get("oee_percentage", data.get("oee", 0))
            parts.append(f"Plant OEE stands at {oee}%. [Source: daily_summaries]")

        return " ".join(parts) if parts else "Here's your morning briefing summary."

    def _generate_wins_template(self, briefing_data: BriefingData) -> Optional[str]:
        """Generate wins section using template."""
        if not briefing_data.production_status or not briefing_data.production_status.success:
            return None

        data = briefing_data.production_status.data or {}
        summary = data.get("summary", {})
        ahead_count = summary.get("ahead_count", 0)

        if ahead_count == 0:
            return None

        # Find top performers from assets list
        assets = data.get("assets", [])
        top_performers = [a for a in assets if a.get("status") == "ahead"][:2]

        if top_performers:
            names = " and ".join([a.get("asset_name", "Unknown") for a in top_performers])
            return f"Great work from {names} - both exceeding their targets. {ahead_count} assets total are running ahead. [Source: live_snapshots]"
        else:
            return f"{ahead_count} assets are currently exceeding their production targets. [Source: live_snapshots]"

    def _generate_concerns_template(self, briefing_data: BriefingData) -> str:
        """Generate concerns section using template."""
        concerns = []

        # Safety concerns
        if briefing_data.safety_events and briefing_data.safety_events.success:
            data = briefing_data.safety_events.data or {}
            if data.get("total_events", 0) > 0:
                concerns.append(f"Safety: {data.get('total_events')} incident(s) recorded that need attention.")

        # Production concerns
        if briefing_data.production_status and briefing_data.production_status.success:
            data = briefing_data.production_status.data or {}
            summary = data.get("summary", {})
            behind = summary.get("assets_needing_attention", [])[:2]
            if behind:
                concerns.append(f"Production: {', '.join(behind)} are behind target. [Source: live_snapshots]")

        # Downtime concerns
        if briefing_data.downtime_analysis and briefing_data.downtime_analysis.success:
            data = briefing_data.downtime_analysis.data or {}
            reasons = data.get("top_reasons", [])
            if reasons:
                top_reason = reasons[0]
                concerns.append(
                    f"Downtime: {top_reason.get('reason', 'Unknown')} caused "
                    f"{top_reason.get('duration_minutes', 0)} minutes of lost time. [Source: downtime_events]"
                )

        if not concerns:
            return "No major concerns at this time. Keep up the good work!"

        return " ".join(concerns)

    def _generate_actions_template(self, briefing_data: BriefingData) -> str:
        """Generate actions section using template."""
        if briefing_data.action_list and briefing_data.action_list.success:
            data = briefing_data.action_list.data or {}
            actions = data.get("actions", [])[:3]
            if actions:
                action_items = []
                for i, action in enumerate(actions, 1):
                    action_items.append(f"{i}. {action.get('title', 'Review action item')}")
                return "Today's priorities: " + " ".join(action_items) + " [Source: action_recommendations]"

        # Default actions based on concerns
        return "Focus on monitoring production targets and addressing any safety items. Review downtime causes for improvement opportunities."


# Module-level singleton
_narrative_generator: Optional[NarrativeGenerator] = None


def get_narrative_generator() -> NarrativeGenerator:
    """
    Get the singleton NarrativeGenerator instance.

    Returns:
        NarrativeGenerator singleton instance
    """
    global _narrative_generator
    if _narrative_generator is None:
        _narrative_generator = NarrativeGenerator()
    return _narrative_generator
