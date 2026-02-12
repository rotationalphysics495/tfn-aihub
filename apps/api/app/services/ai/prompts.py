"""
Prompt Templates for Smart Summary Generation

Externalized prompt templates for manufacturing-optimized AI summaries.

Story: 3.5 - Smart Summary Generator
AC: #3 - Prompt Engineering for Manufacturing Context
AC: #5 - Data Citation Requirement (NFR1 Compliance)
"""

import os
from datetime import date as date_type
from typing import Any, Dict, List, Optional

# AC#3: Externalized prompt template - can be overridden via environment
SYSTEM_PROMPT_DEFAULT = """You are an experienced manufacturing operations analyst reviewing daily production data.
Your role is to provide concise, actionable insights for Plant Managers.

CRITICAL REQUIREMENTS:
1. ALWAYS cite specific data points in your analysis using this format: [Asset: <name>, <metric>: <value>]
   Example: [Asset: Grinder 5, OEE: 72%]
2. Prioritize issues in this order: Safety > Financial Impact > OEE Gaps
3. Provide specific, actionable recommendations with estimated impact
4. Keep the executive summary to 2-3 sentences maximum
5. Use bullet points for clarity
6. Reference source tables in citations: [Source: <table_name>, <date>]
7. When trend context is provided, incorporate week-over-week comparisons, highlight repeat offenders (3+ consecutive days), and mention top downtime drivers in your analysis
8. When an asset has an active action plan, mention it alongside the asset's issues (e.g., "Grinder 5 OEE is still below target — note that a corrective action plan is in progress (bearing replacement, due Friday)")
9. When a recently verified action plan exists and the asset's metrics improved, note the possible correlation (e.g., "Grinder 5 OEE improved 5 points since bearing replacement completed last Monday")

OUTPUT FORMAT:
## Executive Summary
[2-3 sentence overview of the day's key issues]

## Priority Issues

### 1. [Issue Title]
- **What Happened:** [Description with data citation]
- **Impact:** [Financial or safety impact in specific terms]
- **Recommended Action:** [Specific action to take]

### 2. [Next Issue]
...

## Data Sources Referenced
[List of source tables and dates used in this analysis]"""

DATA_TEMPLATE_DEFAULT = """Today's Date: {date}

=== SAFETY EVENTS ===
{safety_events_data}

=== OEE PERFORMANCE ===
{oee_data}

=== FINANCIAL LOSSES ===
{financial_data}

=== ACTION ENGINE PRIORITIES ===
{action_items}

=== TREND CONTEXT ===
{trend_context}

=== ACTION PLAN STATUS ===
{action_plan_data}

Based on this data, provide your analysis following the format specified in your instructions.
Ensure every claim is backed by a specific data citation."""


def get_system_prompt() -> str:
    """
    Get the system prompt for Smart Summary generation.

    AC#3: Prompt template is externalized (not hardcoded) for easy iteration.
    Can be overridden via SMART_SUMMARY_SYSTEM_PROMPT environment variable.

    Returns:
        System prompt string
    """
    return os.getenv("SMART_SUMMARY_SYSTEM_PROMPT", SYSTEM_PROMPT_DEFAULT)


def get_data_template() -> str:
    """
    Get the data template for Smart Summary generation.

    AC#3: Prompt template is externalized for easy iteration.
    Can be overridden via SMART_SUMMARY_DATA_TEMPLATE environment variable.

    Returns:
        Data template string
    """
    return os.getenv("SMART_SUMMARY_DATA_TEMPLATE", DATA_TEMPLATE_DEFAULT)


def format_safety_events(safety_events: list) -> str:
    """
    Format safety events data for prompt injection.

    AC#5: Citations reference specific asset names, timestamps, or metric values.

    Args:
        safety_events: List of safety event dictionaries

    Returns:
        Formatted string for prompt
    """
    if not safety_events:
        return "No safety events recorded for this date."

    lines = []
    for event in safety_events:
        asset_name = event.get("asset_name", "Unknown Asset")
        severity = event.get("severity", "unknown")
        reason_code = event.get("reason_code", "Unknown")
        description = event.get("description", "")
        timestamp = event.get("event_timestamp", "")
        is_resolved = event.get("is_resolved", False)
        status = "RESOLVED" if is_resolved else "UNRESOLVED"

        line = (
            f"- {asset_name}: {reason_code} (Severity: {severity}, Status: {status})"
        )
        if timestamp:
            line += f" at {timestamp}"
        if description:
            line += f"\n  Details: {description}"

        lines.append(line)

    return "\n".join(lines)


def format_oee_data(daily_summaries: list, target_oee: float = 85.0) -> str:
    """
    Format OEE performance data for prompt injection.

    AC#5: Citations include specific metric values.

    Args:
        daily_summaries: List of daily summary dictionaries
        target_oee: Target OEE percentage for comparison

    Returns:
        Formatted string for prompt
    """
    if not daily_summaries:
        return "No OEE data available for this date."

    lines = [f"Target OEE: {target_oee}%\n"]

    # Sort by OEE gap (lowest OEE first)
    sorted_summaries = sorted(
        daily_summaries,
        key=lambda x: x.get("oee_percentage", 0) or 0
    )

    for summary in sorted_summaries:
        asset_name = summary.get("asset_name", "Unknown Asset")
        oee = summary.get("oee_percentage", 0) or 0
        actual_output = summary.get("actual_output", 0) or 0
        target_output = summary.get("target_output", 0) or 0
        downtime_minutes = summary.get("downtime_minutes", 0) or 0

        gap = target_oee - oee
        status = "BELOW TARGET" if gap > 0 else "ON TARGET"

        line = f"- {asset_name}: OEE {oee:.1f}% ({status})"
        if gap > 0:
            line += f" - Gap: {gap:.1f}%"
        line += f"\n  Output: {actual_output} / {target_output} units"
        if downtime_minutes > 0:
            line += f", Downtime: {downtime_minutes} minutes"

        lines.append(line)

    return "\n".join(lines)


def format_financial_data(
    daily_summaries: list,
    cost_centers: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format financial loss data for prompt injection.

    AC#5: Citations include $ impact values.

    Args:
        daily_summaries: List of daily summary dictionaries
        cost_centers: Optional cost center mapping for context

    Returns:
        Formatted string for prompt
    """
    if not daily_summaries:
        return "No financial data available for this date."

    lines = []
    total_loss = 0

    # Sort by financial loss (highest first)
    sorted_summaries = sorted(
        daily_summaries,
        key=lambda x: x.get("financial_loss_dollars", 0) or 0,
        reverse=True
    )

    for summary in sorted_summaries:
        asset_name = summary.get("asset_name", "Unknown Asset")
        loss = summary.get("financial_loss_dollars", 0) or 0
        waste_count = summary.get("waste_count", 0) or 0
        downtime_minutes = summary.get("downtime_minutes", 0) or 0

        total_loss += loss

        if loss > 0:
            line = f"- {asset_name}: Loss ${loss:,.2f}"
            details = []
            if waste_count > 0:
                details.append(f"Waste: {waste_count} units")
            if downtime_minutes > 0:
                details.append(f"Downtime: {downtime_minutes} min")
            if details:
                line += f" ({', '.join(details)})"
            lines.append(line)

    if not lines:
        return "No significant financial losses recorded."

    lines.insert(0, f"Total Financial Impact: ${total_loss:,.2f}\n")
    return "\n".join(lines)


def format_trend_context(
    trend_data: Optional[Dict[str, Any]] = None,
    repeat_offenders: Optional[List[Dict[str, Any]]] = None,
    top_downtime_drivers: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Format trend context data for prompt injection.

    Renders week-over-week OEE comparison, repeat offenders, and top
    downtime drivers into a structured text block.

    Args:
        trend_data: Plant-level WoW OEE data
        repeat_offenders: Assets on report 3+ consecutive days
        top_downtime_drivers: Top downtime reason codes

    Returns:
        Formatted string for prompt
    """
    lines = []

    if trend_data:
        current = trend_data.get("plant_oee_current", 0)
        previous = trend_data.get("plant_oee_previous_week", 0)
        change = trend_data.get("plant_oee_wow_change", 0)
        lines.append(
            f"Week-over-Week OEE: Current {current:.1f}% vs Last Week "
            f"{previous:.1f}% (change: {change:+.1f} points)"
        )

    if repeat_offenders:
        lines.append("")
        lines.append("Repeat Offenders (3+ consecutive days on report):")
        for offender in repeat_offenders:
            name = offender.get("asset_name", "Unknown")
            days = offender.get("consecutive_days", 0)
            lines.append(f"- {name}: {days} consecutive days (OEE below target)")

    if top_downtime_drivers:
        lines.append("")
        lines.append("Top Downtime Drivers (yesterday):")
        for driver in top_downtime_drivers:
            reason = driver.get("reason_code", "Unknown")
            minutes = driver.get("total_minutes", 0)
            assets = driver.get("asset_count", 0)
            lines.append(f"- {reason}: {minutes} min across {assets} assets")

    if not lines:
        return "No trend data available for this period."

    return "\n".join(lines)


def format_action_plans(
    action_plans: Optional[list] = None,
    recently_verified_plans: Optional[list] = None,
) -> str:
    """
    Format action plan data for prompt injection.

    Args:
        action_plans: List of active action plan dictionaries
        recently_verified_plans: List of recently verified action plan dictionaries

    Returns:
        Formatted string for prompt
    """
    plans = action_plans or []
    verified = recently_verified_plans or []

    if not plans and not verified:
        return "No active action plans for assets on today's report."

    lines = []
    if plans:
        lines.append("Active action plans for assets on today's report:\n")
        for plan in plans:
            asset_name = plan.get("asset_name", "Unknown")
            title = plan.get("title", "Untitled")
            status = plan.get("status", "unknown")
            due_date = plan.get("due_date", "no date")
            category = plan.get("category", "")
            lines.append(
                f"- {asset_name}: \"{title}\" ({category}, {status}, due {due_date})"
            )

    if verified:
        lines.append("\nRecently completed action plans (last 7 days):\n")
        for plan in verified:
            asset_name = plan.get("asset_name", "Unknown")
            title = plan.get("title", "Untitled")
            corrective = plan.get("corrective_action", "")
            verified_at = plan.get("verified_at", "")
            lines.append(
                f"- {asset_name}: \"{title}\" completed — {corrective} (verified {verified_at})"
            )

    return "\n".join(lines)


def format_action_items(action_items: list) -> str:
    """
    Format action engine priorities for prompt injection.

    Args:
        action_items: List of ActionItem dictionaries

    Returns:
        Formatted string for prompt
    """
    if not action_items:
        return "No prioritized action items generated."

    lines = ["Prioritized actions from Action Engine:\n"]

    for i, item in enumerate(action_items[:10], 1):  # Limit to top 10
        asset_name = item.get("asset_name", "Unknown")
        category = item.get("category", "unknown")
        priority = item.get("priority_level", "medium")
        recommendation = item.get("recommendation_text", "")
        evidence = item.get("evidence_summary", "")

        line = f"{i}. [{category.upper()}] {asset_name} (Priority: {priority})"
        if recommendation:
            line += f"\n   Action: {recommendation}"
        if evidence:
            line += f"\n   Evidence: {evidence}"

        lines.append(line)

    return "\n".join(lines)


def render_data_prompt(
    target_date: date_type,
    safety_events: list,
    daily_summaries: list,
    action_items: list,
    cost_centers: Optional[Dict[str, Any]] = None,
    target_oee: float = 85.0,
    trend_data: Optional[Dict[str, Any]] = None,
    repeat_offenders: Optional[List[Dict[str, Any]]] = None,
    top_downtime_drivers: Optional[List[Dict[str, Any]]] = None,
    action_plans: Optional[List[Dict[str, Any]]] = None,
    recently_verified_plans: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Render the complete data prompt for LLM.

    AC#3: Prompt includes specific data points with values.
    AC#5: Data is formatted with verifiable citations.

    Args:
        target_date: Date of the report
        safety_events: List of safety event data
        daily_summaries: List of daily summary data
        action_items: List of action items from Action Engine
        cost_centers: Optional cost center mapping
        target_oee: Target OEE percentage
        trend_data: Optional plant-level WoW OEE data
        repeat_offenders: Optional list of repeat offender assets
        top_downtime_drivers: Optional list of top downtime drivers

    Returns:
        Rendered prompt string ready for LLM
    """
    template = get_data_template()

    # Pre-compute all format values so KeyErrors from format functions
    # propagate naturally rather than being caught by the template fallback
    format_values = {
        "date": target_date.isoformat(),
        "safety_events_data": format_safety_events(safety_events),
        "oee_data": format_oee_data(daily_summaries, target_oee),
        "financial_data": format_financial_data(daily_summaries, cost_centers),
        "action_items": format_action_items(action_items),
        "trend_context": format_trend_context(
            trend_data, repeat_offenders, top_downtime_drivers
        ),
        "action_plan_data": format_action_plans(
            action_plans, recently_verified_plans
        ),
    }

    try:
        return template.format(**format_values)
    except KeyError:
        # Handle case where custom template doesn't have new placeholders
        extra_sections = []
        for key, header in [
            ("trend_context", "TREND CONTEXT"),
            ("action_plan_data", "ACTION PLAN STATUS"),
        ]:
            if key in format_values:
                section = format_values.pop(key)
                extra_sections.append(f"\n\n=== {header} ===\n{section}")
        try:
            base = template.format(**format_values)
        except KeyError:
            # Last resort: use default template
            base = DATA_TEMPLATE_DEFAULT.format(**format_values)
        return base + "".join(extra_sections)
