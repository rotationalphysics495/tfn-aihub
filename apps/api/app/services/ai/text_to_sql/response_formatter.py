"""
Response Formatter (Story 4.2)

Formats query results into human-readable natural language responses
with proper data citations for NFR1 compliance.

AC#3: Query Execution and Result Formatting
AC#4: Data Citation for NFR1 Compliance
Task 6: Build Response Formatter with Citations
"""

import logging
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Citation(BaseModel):
    """
    Data citation for NFR1 compliance.

    AC#4: Specific data points are cited with source table and context.
    """
    value: str = Field(..., description="The cited value (e.g., '87%')")
    field: str = Field(..., description="The database column name (e.g., 'oee_percentage')")
    table: str = Field(..., description="The source table (e.g., 'daily_summaries')")
    context: str = Field(..., description="Business context (e.g., 'Grinder 5 on 2026-01-04')")


class ResponseFormatter:
    """
    Formats SQL query results into natural language with citations.

    AC#3: Results are formatted into human-readable natural language responses.
    AC#4: Every AI response cites specific data points from query results.
    """

    # Column formatting rules
    PERCENTAGE_COLUMNS = {"oee_percentage", "efficiency", "rate", "percentage"}
    CURRENCY_COLUMNS = {"financial_loss_dollars", "standard_hourly_rate", "cost", "loss"}
    COUNT_COLUMNS = {"actual_output", "target_output", "current_output", "downtime_minutes",
                     "waste_count", "output_variance", "total_downtime", "total_waste"}
    DATE_COLUMNS = {"report_date", "effective_date"}
    TIMESTAMP_COLUMNS = {"event_timestamp", "snapshot_timestamp", "created_at",
                         "updated_at", "resolved_at"}

    def __init__(self):
        """Initialize the response formatter."""
        pass

    def format_response(
        self,
        query_results: List[Dict[str, Any]],
        sql: str,
        question: str,
    ) -> Tuple[str, List[Citation]]:
        """
        Format query results into a natural language response with citations.

        AC#3: Results are formatted into human-readable natural language.
        AC#4: Data points are cited with source and context.

        Args:
            query_results: List of row dictionaries from query execution
            sql: The SQL query that was executed
            question: The original user question

        Returns:
            Tuple of (natural_language_answer, list_of_citations)
        """
        if not query_results:
            return self._format_no_results(question, sql), []

        # Extract table name from SQL for citations
        source_table = self._extract_source_table(sql)

        # Generate citations from the data
        citations = self._generate_citations(query_results, source_table)

        # Format the natural language response
        answer = self._format_answer(query_results, question, source_table)

        return answer, citations

    def _format_no_results(self, question: str, sql: str) -> str:
        """
        Format a helpful message when no results are found.

        AC#3: Empty results return helpful "no data found" messages with suggestions.
        """
        # Extract what the user was looking for
        suggestions = []

        if "yesterday" in question.lower():
            suggestions.append("Check if data for yesterday has been processed")
        if "last week" in question.lower() or "week" in question.lower():
            suggestions.append("Try a different date range")
        if any(word in question.lower() for word in ["grinder", "press", "asset"]):
            suggestions.append("Verify the asset name is spelled correctly")
        if "safety" in question.lower():
            suggestions.append("There may be no safety events recorded in this period")

        message = "No data found for your query."

        if suggestions:
            message += "\n\nSuggestions:\n"
            for suggestion in suggestions:
                message += f"- {suggestion}\n"
        else:
            message += "\n\nYou might try:\n"
            message += "- Checking for a different date range\n"
            message += "- Verifying asset names are correct\n"
            message += "- Asking about a different metric or time period"

        return message

    def _extract_source_table(self, sql: str) -> str:
        """Extract the primary source table from SQL query."""
        # Find the main FROM table
        match = re.search(r"\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)", sql, re.IGNORECASE)
        if match:
            return match.group(1).lower()
        return "unknown"

    def _generate_citations(
        self,
        results: List[Dict[str, Any]],
        source_table: str,
    ) -> List[Citation]:
        """Generate citations for key data points in results."""
        citations = []

        for row in results[:5]:  # Limit citations to first 5 rows
            # Build context string from identifying columns
            context = self._build_context(row)

            # Extract citable values
            for key, value in row.items():
                if value is None:
                    continue

                # Skip identifier columns
                if key.lower() in {"id", "asset_id", "cost_center_id"}:
                    continue

                # Format the value and create citation
                formatted_value = self._format_value(key, value)
                if formatted_value:
                    citations.append(Citation(
                        value=formatted_value,
                        field=key,
                        table=source_table,
                        context=context,
                    ))

        return citations

    def _build_context(self, row: Dict[str, Any]) -> str:
        """Build context string for citation from row data."""
        context_parts = []

        # Asset name
        if "asset_name" in row and row["asset_name"]:
            context_parts.append(str(row["asset_name"]))
        elif "name" in row and row["name"]:
            context_parts.append(str(row["name"]))

        # Date context
        for date_col in ["report_date", "event_timestamp", "snapshot_timestamp"]:
            if date_col in row and row[date_col]:
                date_val = row[date_col]
                if isinstance(date_val, (date, datetime)):
                    context_parts.append(f"on {date_val.strftime('%Y-%m-%d')}")
                else:
                    context_parts.append(f"on {str(date_val)[:10]}")
                break

        return " ".join(context_parts) if context_parts else "query result"

    def _format_value(self, column: str, value: Any) -> Optional[str]:
        """Format a value based on its column type."""
        if value is None:
            return None

        column_lower = column.lower()

        # Percentage formatting
        if any(p in column_lower for p in self.PERCENTAGE_COLUMNS):
            try:
                num = float(value)
                return f"{num:.1f}%"
            except (TypeError, ValueError):
                return str(value)

        # Currency formatting
        if any(c in column_lower for c in self.CURRENCY_COLUMNS):
            try:
                num = float(value)
                return f"${num:,.2f}"
            except (TypeError, ValueError):
                return str(value)

        # Count formatting
        if any(c in column_lower for c in self.COUNT_COLUMNS):
            try:
                num = int(float(value))
                return f"{num:,}"
            except (TypeError, ValueError):
                return str(value)

        # Date formatting
        if any(d in column_lower for d in self.DATE_COLUMNS):
            if isinstance(value, date):
                return value.strftime("%B %d, %Y")
            return str(value)

        # Timestamp formatting
        if any(t in column_lower for t in self.TIMESTAMP_COLUMNS):
            if isinstance(value, datetime):
                return value.strftime("%B %d, %Y at %I:%M %p")
            return str(value)

        # Status formatting
        if column_lower in {"status", "severity"}:
            return str(value).replace("_", " ").title()

        # Boolean formatting
        if isinstance(value, bool):
            return "Yes" if value else "No"

        # Default string conversion
        return str(value)

    def _format_answer(
        self,
        results: List[Dict[str, Any]],
        question: str,
        source_table: str,
    ) -> str:
        """Format results into a natural language answer."""
        question_lower = question.lower()

        # Single result handling
        if len(results) == 1:
            return self._format_single_result(results[0], question, source_table)

        # Multiple results handling
        return self._format_multiple_results(results, question, source_table)

    def _format_single_result(
        self,
        row: Dict[str, Any],
        question: str,
        source_table: str,
    ) -> str:
        """Format a single result row into natural language."""
        parts = []

        # Get asset name if available
        asset_name = row.get("asset_name") or row.get("name")

        # OEE question
        if "oee" in question.lower() or "efficiency" in question.lower():
            if "oee_percentage" in row:
                oee = self._format_value("oee_percentage", row["oee_percentage"])
                if asset_name:
                    parts.append(f"{asset_name} had an OEE of {oee}")
                else:
                    parts.append(f"The OEE was {oee}")

                # Add context about target
                if row.get("oee_percentage") and float(row["oee_percentage"]) >= 85:
                    parts.append("which is above the typical plant target of 85%")
                elif row.get("oee_percentage") and float(row["oee_percentage"]) < 85:
                    gap = 85 - float(row["oee_percentage"])
                    parts.append(f"which is {gap:.1f}% below the target of 85%")

        # Downtime question
        elif "downtime" in question.lower():
            if "downtime_minutes" in row:
                downtime = row["downtime_minutes"]
                if asset_name:
                    parts.append(f"{asset_name} had {downtime:,} minutes of downtime")
                else:
                    parts.append(f"Total downtime was {downtime:,} minutes")
            elif "total_downtime" in row:
                parts.append(f"Total downtime: {row['total_downtime']:,} minutes")

        # Financial loss question
        elif "loss" in question.lower() or "cost" in question.lower() or "financial" in question.lower():
            if "financial_loss_dollars" in row:
                loss = self._format_value("financial_loss_dollars", row["financial_loss_dollars"])
                if asset_name:
                    parts.append(f"{asset_name} had a financial loss of {loss}")
                else:
                    parts.append(f"The financial loss was {loss}")
            elif "total_loss" in row:
                loss = self._format_value("financial_loss_dollars", row["total_loss"])
                parts.append(f"Total financial loss: {loss}")

        # Safety event question
        elif "safety" in question.lower() or "incident" in question.lower():
            severity = row.get("severity", "")
            description = row.get("description", "No description available")
            if asset_name:
                parts.append(f"{severity.title()} safety event at {asset_name}: {description}")
            else:
                parts.append(f"{severity.title()} safety event: {description}")

        # Production/output question
        elif "output" in question.lower() or "production" in question.lower():
            current = row.get("current_output") or row.get("actual_output")
            target = row.get("target_output")
            if current is not None and target is not None:
                status = row.get("status", "").replace("_", " ")
                if asset_name:
                    parts.append(f"{asset_name}: current output {current:,} vs target {target:,} ({status})")
                else:
                    parts.append(f"Current output: {current:,} vs target: {target:,} ({status})")

        # Generic fallback - format all important columns
        if not parts:
            parts = self._format_generic_result(row)

        # Add date context if available
        date_str = self._get_date_context(row)
        if date_str:
            parts.append(date_str)

        return ". ".join(parts) + "."

    def _format_multiple_results(
        self,
        results: List[Dict[str, Any]],
        question: str,
        source_table: str,
    ) -> str:
        """Format multiple result rows into natural language."""
        parts = []
        parts.append(f"Found {len(results)} results:")
        parts.append("")

        for i, row in enumerate(results[:10], 1):  # Limit to 10 rows
            row_parts = []

            # Get asset name
            asset_name = row.get("asset_name") or row.get("name") or f"Result {i}"
            row_parts.append(f"**{asset_name}**")

            # Add key metrics based on what's in the row
            metrics = []
            if "oee_percentage" in row and row["oee_percentage"] is not None:
                metrics.append(f"OEE: {self._format_value('oee_percentage', row['oee_percentage'])}")
            if "total_downtime" in row and row["total_downtime"] is not None:
                metrics.append(f"Downtime: {row['total_downtime']:,} min")
            if "downtime_minutes" in row and row["downtime_minutes"] is not None:
                metrics.append(f"Downtime: {row['downtime_minutes']:,} min")
            if "financial_loss_dollars" in row and row["financial_loss_dollars"] is not None:
                metrics.append(f"Loss: {self._format_value('financial_loss_dollars', row['financial_loss_dollars'])}")
            if "total_loss" in row and row["total_loss"] is not None:
                metrics.append(f"Loss: {self._format_value('financial_loss_dollars', row['total_loss'])}")
            if "severity" in row and row["severity"] is not None:
                metrics.append(f"Severity: {row['severity'].title()}")
            if "status" in row and row["status"] is not None:
                metrics.append(f"Status: {row['status'].replace('_', ' ').title()}")
            if "current_output" in row and "target_output" in row:
                current = row.get("current_output", 0)
                target = row.get("target_output", 0)
                if current is not None and target is not None:
                    metrics.append(f"Output: {current:,}/{target:,}")
            if "waste_count" in row and row["waste_count"] is not None:
                metrics.append(f"Waste: {row['waste_count']:,}")
            if "total_waste" in row and row["total_waste"] is not None:
                metrics.append(f"Total Waste: {row['total_waste']:,}")

            if metrics:
                row_parts.append(" - " + ", ".join(metrics))

            parts.append("".join(row_parts))

        if len(results) > 10:
            parts.append(f"\n... and {len(results) - 10} more results")

        return "\n".join(parts)

    def _format_generic_result(self, row: Dict[str, Any]) -> List[str]:
        """Format a generic result when no specific pattern matches."""
        parts = []
        asset_name = row.get("asset_name") or row.get("name")

        if asset_name:
            parts.append(f"Results for {asset_name}:")

        # Format each non-null, non-ID column
        for key, value in row.items():
            if value is None:
                continue
            if key.lower() in {"id", "asset_id", "asset_name", "name"}:
                continue

            formatted = self._format_value(key, value)
            if formatted:
                readable_key = key.replace("_", " ").title()
                parts.append(f"{readable_key}: {formatted}")

        return parts

    def _get_date_context(self, row: Dict[str, Any]) -> Optional[str]:
        """Extract date context from row."""
        for date_col in ["report_date", "event_timestamp", "snapshot_timestamp"]:
            if date_col in row and row[date_col]:
                date_val = row[date_col]
                if isinstance(date_val, datetime):
                    # Check if it's yesterday
                    today = datetime.now().date()
                    if date_val.date() == today:
                        return "Today"
                    elif (today - date_val.date()).days == 1:
                        return "Yesterday"
                    return f"On {date_val.strftime('%B %d, %Y')}"
                elif isinstance(date_val, date):
                    today = datetime.now().date()
                    if date_val == today:
                        return "Today"
                    elif (today - date_val).days == 1:
                        return "Yesterday"
                    return f"On {date_val.strftime('%B %d, %Y')}"
        return None


def get_response_formatter() -> ResponseFormatter:
    """Get a ResponseFormatter instance."""
    return ResponseFormatter()
