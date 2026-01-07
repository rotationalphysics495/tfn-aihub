"""
Manufacturing Domain Prompts (Story 4.2)

Custom prompts optimized for manufacturing domain SQL generation.

AC#2: Natural Language Query Parsing - Domain-specific prompts
AC#4: Data Citation - Prompt instructions for citation
Task 10: Manufacturing Domain Prompts
"""

from typing import Dict, List


# Table descriptions for LLM context
TABLE_DESCRIPTIONS: Dict[str, str] = {
    "assets": """
    Physical equipment/machines in the manufacturing plant.
    Columns:
    - id (UUID): Unique identifier
    - name (VARCHAR): Human-readable asset name (e.g., "Grinder 5", "Press Line 1")
    - source_id (VARCHAR): Maps to MSSQL locationName for data sync
    - area (VARCHAR): Plant area where asset is located (e.g., "Grinding", "Assembly")
    - created_at, updated_at (TIMESTAMP): Record timestamps
    """,

    "cost_centers": """
    Financial cost center information linked to assets.
    Columns:
    - id (UUID): Unique identifier
    - asset_id (UUID): Foreign key to assets table
    - standard_hourly_rate (DECIMAL): Cost per hour for financial calculations in USD
    - created_at, updated_at (TIMESTAMP): Record timestamps
    """,

    "daily_summaries": """
    T-1 processed daily reports with OEE metrics, waste data, and financial loss.
    Populated by Pipeline A ("Morning Report") at 06:00 AM.
    Columns:
    - id (UUID): Unique identifier
    - asset_id (UUID): Foreign key to assets table
    - report_date (DATE): Date of the daily report
    - oee_percentage (DECIMAL): Overall Equipment Effectiveness 0-100 (e.g., 87.5 means 87.5%)
    - actual_output (INTEGER): Actual production output count
    - target_output (INTEGER): Target production output count
    - downtime_minutes (INTEGER): Total downtime in minutes
    - waste_count (INTEGER): Number of waste/rejected items
    - financial_loss_dollars (DECIMAL): Calculated financial loss in USD
    - smart_summary_text (TEXT): AI-generated summary text
    - created_at, updated_at (TIMESTAMP): Record timestamps
    Note: oee_percentage is stored as 0-100, not as decimal 0-1
    """,

    "live_snapshots": """
    15-minute polling data for live production monitoring.
    Populated by Pipeline B ("Live Pulse") via background scheduler.
    Columns:
    - id (UUID): Unique identifier
    - asset_id (UUID): Foreign key to assets table
    - snapshot_timestamp (TIMESTAMP): When the snapshot was taken
    - current_output (INTEGER): Current production output at snapshot time
    - target_output (INTEGER): Target production output at snapshot time
    - output_variance (INTEGER): Calculated difference (current - target), auto-computed
    - status (TEXT): Production status: 'on_target', 'behind', or 'ahead'
    - created_at (TIMESTAMP): Record timestamp
    """,

    "safety_events": """
    Persistent log of safety incidents detected when reason_code = 'Safety Issue'.
    Columns:
    - id (UUID): Unique identifier
    - asset_id (UUID): Foreign key to assets table
    - event_timestamp (TIMESTAMP): When the safety event occurred
    - reason_code (TEXT): Code identifying the type of safety event
    - severity (TEXT): Severity level: 'low', 'medium', 'high', or 'critical'
    - description (TEXT): Detailed description of the safety event
    - is_resolved (BOOLEAN): Whether the event has been resolved
    - resolved_at (TIMESTAMP): When the event was resolved
    - created_at (TIMESTAMP): Record timestamp
    """
}


# Example question-SQL pairs for few-shot learning
EXAMPLE_QUERIES: List[Dict[str, str]] = [
    {
        "question": "What was Grinder 5's OEE yesterday?",
        "sql": """SELECT a.name AS asset_name, ds.oee_percentage, ds.report_date
FROM daily_summaries ds
JOIN assets a ON ds.asset_id = a.id
WHERE a.name ILIKE '%Grinder 5%'
AND ds.report_date = CURRENT_DATE - INTERVAL '1 day'
LIMIT 10;"""
    },
    {
        "question": "Which asset had the most downtime last week?",
        "sql": """SELECT a.name AS asset_name, SUM(ds.downtime_minutes) AS total_downtime
FROM daily_summaries ds
JOIN assets a ON ds.asset_id = a.id
WHERE ds.report_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY a.name
ORDER BY total_downtime DESC
LIMIT 10;"""
    },
    {
        "question": "Show me all safety events this month",
        "sql": """SELECT a.name AS asset_name, se.event_timestamp, se.severity, se.description, se.is_resolved
FROM safety_events se
JOIN assets a ON se.asset_id = a.id
WHERE se.event_timestamp >= DATE_TRUNC('month', CURRENT_DATE)
ORDER BY se.event_timestamp DESC
LIMIT 10;"""
    },
    {
        "question": "What's the total financial loss for the Grinding area?",
        "sql": """SELECT a.area, SUM(ds.financial_loss_dollars) AS total_loss
FROM daily_summaries ds
JOIN assets a ON ds.asset_id = a.id
WHERE a.area ILIKE '%Grinding%'
GROUP BY a.area
LIMIT 10;"""
    },
    {
        "question": "How is Press Line 1 performing right now?",
        "sql": """SELECT a.name AS asset_name, ls.snapshot_timestamp, ls.current_output, ls.target_output, ls.output_variance, ls.status
FROM live_snapshots ls
JOIN assets a ON ls.asset_id = a.id
WHERE a.name ILIKE '%Press Line 1%'
ORDER BY ls.snapshot_timestamp DESC
LIMIT 10;"""
    },
    {
        "question": "What assets are behind target today?",
        "sql": """SELECT DISTINCT a.name AS asset_name, ls.current_output, ls.target_output, ls.status
FROM live_snapshots ls
JOIN assets a ON ls.asset_id = a.id
WHERE ls.status = 'behind'
AND ls.snapshot_timestamp >= CURRENT_DATE
ORDER BY ls.snapshot_timestamp DESC
LIMIT 10;"""
    },
    {
        "question": "Show me the hourly rate for all cost centers",
        "sql": """SELECT a.name AS asset_name, cc.standard_hourly_rate
FROM cost_centers cc
JOIN assets a ON cc.asset_id = a.id
ORDER BY cc.standard_hourly_rate DESC
LIMIT 10;"""
    },
    {
        "question": "What are the critical safety events that haven't been resolved?",
        "sql": """SELECT a.name AS asset_name, se.event_timestamp, se.severity, se.description
FROM safety_events se
JOIN assets a ON se.asset_id = a.id
WHERE se.severity = 'critical'
AND se.is_resolved = FALSE
ORDER BY se.event_timestamp DESC
LIMIT 10;"""
    },
    {
        "question": "Compare OEE across all assets for yesterday",
        "sql": """SELECT a.name AS asset_name, ds.oee_percentage, ds.actual_output, ds.target_output
FROM daily_summaries ds
JOIN assets a ON ds.asset_id = a.id
WHERE ds.report_date = CURRENT_DATE - INTERVAL '1 day'
ORDER BY ds.oee_percentage DESC
LIMIT 10;"""
    },
    {
        "question": "What was the waste count for each asset last month?",
        "sql": """SELECT a.name AS asset_name, SUM(ds.waste_count) AS total_waste
FROM daily_summaries ds
JOIN assets a ON ds.asset_id = a.id
WHERE ds.report_date >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
AND ds.report_date < DATE_TRUNC('month', CURRENT_DATE)
GROUP BY a.name
ORDER BY total_waste DESC
LIMIT 10;"""
    }
]


# Manufacturing terminology mapping
TERMINOLOGY_MAP: Dict[str, str] = {
    "oee": "oee_percentage (Overall Equipment Effectiveness)",
    "efficiency": "oee_percentage",
    "output": "actual_output or current_output",
    "production": "actual_output or current_output",
    "downtime": "downtime_minutes",
    "stopped": "downtime_minutes",
    "loss": "financial_loss_dollars",
    "cost": "financial_loss_dollars or standard_hourly_rate",
    "waste": "waste_count",
    "scrap": "waste_count",
    "rejects": "waste_count",
    "safety": "safety_events table",
    "incident": "safety_events table",
    "accident": "safety_events table",
    "machine": "assets table",
    "equipment": "assets table",
    "area": "area column in assets",
    "zone": "area column in assets",
    "department": "area column in assets",
    "yesterday": "CURRENT_DATE - INTERVAL '1 day'",
    "today": "CURRENT_DATE",
    "last week": "CURRENT_DATE - INTERVAL '7 days'",
    "this month": "DATE_TRUNC('month', CURRENT_DATE)",
    "last month": "DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'",
}


def get_table_descriptions() -> str:
    """
    Get formatted table descriptions for LLM context.

    Returns:
        Formatted string with all table descriptions
    """
    descriptions = []
    for table, desc in TABLE_DESCRIPTIONS.items():
        descriptions.append(f"=== Table: {table} ===\n{desc.strip()}")
    return "\n\n".join(descriptions)


def get_example_queries() -> str:
    """
    Get formatted example queries for few-shot learning.

    Returns:
        Formatted string with example question-SQL pairs
    """
    examples = []
    for i, example in enumerate(EXAMPLE_QUERIES, 1):
        examples.append(
            f"Example {i}:\n"
            f"Question: {example['question']}\n"
            f"SQL: {example['sql']}"
        )
    return "\n\n".join(examples)


def get_terminology_hints() -> str:
    """
    Get terminology mapping hints.

    Returns:
        Formatted string with terminology mappings
    """
    hints = []
    for term, mapping in TERMINOLOGY_MAP.items():
        hints.append(f"- '{term}' -> {mapping}")
    return "\n".join(hints)


def get_sql_system_prompt() -> str:
    """
    Get the complete system prompt for SQL generation.

    AC#2: Custom prompt template optimized for manufacturing domain.
    AC#4: Instructions for citation-friendly output.

    Returns:
        Complete system prompt string
    """
    return f"""You are a SQL expert for a manufacturing plant database running PostgreSQL.
Your role is to translate natural language questions about plant operations into accurate SQL queries.

CRITICAL RULES:
1. ONLY generate SELECT statements - never INSERT, UPDATE, DELETE, DROP, or any modification
2. ONLY query these approved tables: assets, cost_centers, daily_summaries, live_snapshots, safety_events
3. Always include LIMIT 10 unless the user asks for all results or a specific limit
4. Use ILIKE for case-insensitive text matching when searching by name
5. Always JOIN with assets table when querying other tables to get asset names
6. For date comparisons, use PostgreSQL date functions (CURRENT_DATE, DATE_TRUNC, INTERVAL)
7. oee_percentage is stored as 0-100 (not 0-1), so 87.5 means 87.5%
8. financial_loss_dollars is in USD
9. Return ONLY the SQL query - no explanations, no markdown code blocks, no comments
10. If the question is ambiguous or unclear, generate a query for the most likely interpretation

TABLE SCHEMAS:
{get_table_descriptions()}

TERMINOLOGY MAPPING:
{get_terminology_hints()}

EXAMPLE QUERIES:
{get_example_queries()}

Remember:
- Always include asset names in results for context (JOIN with assets table)
- Use descriptive column aliases (AS asset_name, AS total_downtime, etc.)
- Order results meaningfully (by date DESC, by value DESC, etc.)
- Include relevant date/time columns in output for citation purposes
- Handle NULL values gracefully with COALESCE if needed

Now generate a PostgreSQL SELECT query for the following question:"""
