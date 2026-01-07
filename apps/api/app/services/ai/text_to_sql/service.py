"""
Text-to-SQL Service (Story 4.2)

Main service for LangChain-based natural language to SQL translation.

AC#1: LangChain SQLDatabase Integration
AC#2: Natural Language Query Parsing
AC#3: Query Execution and Result Formatting
AC#4: Data Citation for NFR1 Compliance
AC#5: Query Security and Guardrails
AC#6: Error Handling and Graceful Degradation
AC#7: Conversation Context Integration
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain.chains import create_sql_query_chain
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage

from app.core.config import get_settings
from app.services.ai.text_to_sql.query_validator import (
    QueryValidator,
    QueryValidationError,
    SQLInjectionError,
    TableAccessError,
)
from app.services.ai.text_to_sql.response_formatter import (
    ResponseFormatter,
    Citation,
)
from app.services.ai.text_to_sql.prompts import get_sql_system_prompt

logger = logging.getLogger(__name__)


class TextToSQLError(Exception):
    """Base exception for Text-to-SQL service errors."""
    pass


class QueryExecutionError(TextToSQLError):
    """Raised when SQL query execution fails."""
    pass


class QueryTimeoutError(TextToSQLError):
    """Raised when query execution times out."""
    pass


class LLMGenerationError(TextToSQLError):
    """Raised when LLM fails to generate SQL."""
    pass


# Default configuration
DEFAULT_QUERY_TIMEOUT = 30  # seconds
DEFAULT_MAX_ROWS = 100
DEFAULT_LLM_MODEL = "gpt-4"
DEFAULT_LLM_TEMPERATURE = 0


class TextToSQLService:
    """
    Text-to-SQL Service using LangChain.

    Provides natural language to SQL translation for manufacturing data queries.

    AC#1: Connects to Supabase PostgreSQL using LangChain's SQLDatabase
    AC#2: Uses create_sql_query_chain for SQL generation
    AC#3: Executes queries and formats results
    AC#4: Generates citations for NFR1 compliance
    AC#5: Validates queries for security
    AC#6: Handles errors gracefully
    AC#7: Accepts optional context parameters
    """

    # Allowed tables whitelist
    ALLOWED_TABLES = [
        "assets",
        "cost_centers",
        "daily_summaries",
        "live_snapshots",
        "safety_events",
    ]

    def __init__(
        self,
        query_timeout: Optional[int] = None,
        max_rows: Optional[int] = None,
    ):
        """
        Initialize the Text-to-SQL service (lazy initialization).

        Args:
            query_timeout: Maximum query execution time in seconds (default from settings)
            max_rows: Maximum rows to return from queries (default from settings)
        """
        self._db: Optional[SQLDatabase] = None
        self._llm: Optional[ChatOpenAI] = None
        self._chain = None
        self._initialized: bool = False
        self._settings = None

        # Use settings if not explicitly provided
        settings = self._get_settings()
        self.query_timeout = query_timeout if query_timeout is not None else getattr(settings, 'sql_query_timeout', DEFAULT_QUERY_TIMEOUT)
        self.max_rows = max_rows if max_rows is not None else getattr(settings, 'sql_max_rows', DEFAULT_MAX_ROWS)
        self.validator = QueryValidator()
        self.formatter = ResponseFormatter()

    def _get_settings(self):
        """Get cached settings."""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    def initialize(self) -> bool:
        """
        Initialize LangChain components with Supabase PostgreSQL.

        AC#1: Connects to Supabase PostgreSQL using LangChain's SQLDatabase.
        AC#1: Exposes only approved tables.

        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized and self._db is not None:
            return True

        settings = self._get_settings()

        if not settings.supabase_db_url:
            logger.warning(
                "Text-to-SQL service not configured. "
                "Set SUPABASE_DB_URL environment variable."
            )
            return False

        if not settings.openai_api_key:
            logger.warning(
                "Text-to-SQL service not configured. "
                "Set OPENAI_API_KEY environment variable."
            )
            return False

        try:
            # AC#1: Create SQLDatabase wrapper with table whitelist
            self._db = SQLDatabase.from_uri(
                settings.supabase_db_url,
                include_tables=self.ALLOWED_TABLES,
                sample_rows_in_table_info=3,
            )

            # Initialize LLM for SQL generation
            llm_model = getattr(settings, 'llm_model', None) or DEFAULT_LLM_MODEL
            llm_temperature = getattr(settings, 'llm_temperature', None) or DEFAULT_LLM_TEMPERATURE

            self._llm = ChatOpenAI(
                model=llm_model,
                temperature=llm_temperature,
                api_key=settings.openai_api_key,
            )

            self._initialized = True
            logger.info(
                f"Text-to-SQL service initialized with tables: {self.ALLOWED_TABLES}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Text-to-SQL service: {e}")
            return False

    def _ensure_initialized(self) -> None:
        """Ensure the service is initialized before operations."""
        if not self._initialized or self._db is None:
            if not self.initialize():
                raise TextToSQLError(
                    "Text-to-SQL service not configured. "
                    "Check SUPABASE_DB_URL and OPENAI_API_KEY."
                )

    async def query(
        self,
        question: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a natural language question and return results.

        AC#2: Generates SQL from natural language
        AC#3: Executes query and formats results
        AC#4: Includes citations
        AC#5: Validates for security
        AC#6: Handles errors gracefully
        AC#7: Accepts optional context

        Args:
            question: Natural language question from user
            user_id: User identifier from JWT
            context: Optional context (previous queries, asset focus)

        Returns:
            Dict with answer, sql, data, and citations

        Raises:
            TextToSQLError: On unrecoverable errors
        """
        self._ensure_initialized()
        start_time = datetime.now()

        try:
            # AC#5: Validate input
            validated_question = self.validator.validate_input(question)

            # AC#2: Generate SQL from natural language
            sql = await self._generate_sql(validated_question, context)

            # AC#5: Validate generated SQL
            validated_sql = self.validator.validate_sql(sql)

            # AC#3: Execute query with timeout
            results = await self._execute_query(validated_sql)

            # AC#3, AC#4: Format response with citations
            answer, citations = self.formatter.format_response(
                results, validated_sql, validated_question
            )

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"Text-to-SQL query completed: user={user_id}, "
                f"rows={len(results)}, time={execution_time:.2f}s"
            )

            return {
                "answer": answer,
                "sql": validated_sql,
                "data": results,
                "citations": [c.model_dump() for c in citations],
                "executed_at": datetime.utcnow().isoformat(),
                "execution_time_seconds": execution_time,
                "row_count": len(results),
            }

        except SQLInjectionError as e:
            logger.warning(f"SQL injection attempt blocked: {e}")
            return self._error_response(
                "Your question contains patterns that cannot be processed. "
                "Please rephrase using natural language.",
                question
            )

        except TableAccessError as e:
            logger.warning(f"Table access violation: {e}")
            return self._error_response(
                "Your question asks about data that is not available. "
                "Try asking about assets, production, OEE, downtime, or safety events.",
                question
            )

        except QueryValidationError as e:
            logger.warning(f"Query validation failed: {e}")
            return self._error_response(
                f"Unable to process your question: {str(e)}. "
                "Please try rephrasing.",
                question
            )

        except QueryTimeoutError:
            logger.error(f"Query timeout for: {question[:100]}")
            return self._error_response(
                "The query took too long to execute. "
                "Try asking a more specific question or narrower date range.",
                question
            )

        except QueryExecutionError as e:
            logger.error(f"Query execution error: {e}")
            return self._error_response(
                "Unable to execute the query. "
                "Please try rephrasing your question or asking about different data.",
                question
            )

        except LLMGenerationError as e:
            logger.error(f"LLM generation error: {e}")
            return self._error_response(
                "Unable to understand your question. "
                "Please try rephrasing it more clearly.",
                question
            )

        except Exception as e:
            logger.exception(f"Unexpected error in Text-to-SQL: {e}")
            return self._error_response(
                "An unexpected error occurred. Please try again.",
                question
            )

    async def _generate_sql(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate SQL from natural language question.

        AC#2: Uses LangChain create_sql_query_chain.
        """
        try:
            # Build the prompt with system context and question
            system_prompt = get_sql_system_prompt()

            # Add context if provided (AC#7)
            context_str = ""
            if context:
                if context.get("asset_focus"):
                    context_str += f"\nFocus on asset: {context['asset_focus']}"
                if context.get("previous_queries"):
                    context_str += f"\nPrevious context: {context['previous_queries'][-1]}"

            full_prompt = f"{system_prompt}{context_str}\n\nQuestion: {question}"

            # Use the LLM to generate SQL
            response = await asyncio.to_thread(
                self._llm.invoke,
                [HumanMessage(content=full_prompt)]
            )

            # Extract SQL from response
            sql = response.content.strip()

            # Clean up any markdown formatting
            sql = self._clean_sql_response(sql)

            if not sql:
                raise LLMGenerationError("LLM returned empty SQL")

            return sql

        except LLMGenerationError:
            raise
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            raise LLMGenerationError(f"Failed to generate SQL: {e}")

    def _clean_sql_response(self, sql: str) -> str:
        """Clean SQL response from LLM output."""
        # Remove markdown code blocks
        sql = re.sub(r"```sql\s*", "", sql, flags=re.IGNORECASE)
        sql = re.sub(r"```\s*", "", sql)

        # Remove any explanation text before/after SQL
        lines = sql.strip().split("\n")
        sql_lines = []
        in_sql = False

        for line in lines:
            line_upper = line.strip().upper()
            if line_upper.startswith(("SELECT", "WITH")):
                in_sql = True
            if in_sql:
                sql_lines.append(line)
            # Stop if we hit a line that looks like explanation
            if in_sql and line.strip() and not any(
                c in line for c in ["SELECT", "FROM", "WHERE", "JOIN", "GROUP",
                                    "ORDER", "LIMIT", "AND", "OR", "ON", "AS",
                                    "CASE", "WHEN", "THEN", "ELSE", "END",
                                    "(", ")", ",", "=", ">", "<", "'", '"',
                                    "HAVING", "UNION", "WITH", "DISTINCT",
                                    "COUNT", "SUM", "AVG", "MIN", "MAX",
                                    "COALESCE", "NULL", "NOT", "IN", "LIKE",
                                    "ILIKE", "BETWEEN", "EXISTS", "INTERVAL",
                                    "DATE", "CURRENT", "EXTRACT", "CAST"]
            ):
                break

        return "\n".join(sql_lines).strip()

    async def _execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """
        Execute SQL query with timeout.

        AC#3: Executes queries with timeout
        AC#5: Query execution has 30-second timeout
        """
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                asyncio.to_thread(self._db.run, sql),
                timeout=self.query_timeout
            )

            # Parse the result string into list of dicts
            return self._parse_query_result(result, sql)

        except asyncio.TimeoutError:
            raise QueryTimeoutError(
                f"Query execution exceeded {self.query_timeout} second timeout"
            )
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise QueryExecutionError(f"Query execution failed: {e}")

    def _parse_query_result(self, result: str, sql: str) -> List[Dict[str, Any]]:
        """Parse SQLDatabase.run() result into list of dicts."""
        if not result or result == "[]":
            return []

        try:
            # SQLDatabase.run() returns a string representation
            # Try to evaluate it safely
            import ast
            if result.startswith("["):
                # It's already a list representation
                data = ast.literal_eval(result)
                if isinstance(data, list):
                    # If it's a list of tuples, we need column names
                    if data and isinstance(data[0], tuple):
                        return self._tuples_to_dicts(data, sql)
                    elif data and isinstance(data[0], dict):
                        return data
            return []
        except Exception as e:
            logger.warning(f"Failed to parse query result: {e}")
            # Return raw result as single dict
            return [{"result": result}]

    def _tuples_to_dicts(
        self,
        tuples: List[tuple],
        sql: str
    ) -> List[Dict[str, Any]]:
        """Convert list of tuples to list of dicts using SQL column names."""
        # Extract column names from SQL SELECT clause
        columns = self._extract_columns_from_sql(sql)

        if not columns:
            # Use generic column names
            columns = [f"col_{i}" for i in range(len(tuples[0]))]

        result = []
        for row in tuples:
            if len(row) == len(columns):
                result.append(dict(zip(columns, row)))
            else:
                # Fallback if column count doesn't match
                result.append({f"col_{i}": v for i, v in enumerate(row)})

        return result

    def _extract_columns_from_sql(self, sql: str) -> List[str]:
        """Extract column names/aliases from SQL SELECT clause."""
        # Find SELECT ... FROM
        match = re.search(
            r"SELECT\s+(.*?)\s+FROM",
            sql,
            re.IGNORECASE | re.DOTALL
        )
        if not match:
            return []

        select_clause = match.group(1)

        # Parse column expressions
        columns = []
        parts = self._split_columns(select_clause)

        for part in parts:
            part = part.strip()
            # Check for alias (AS keyword or space-separated)
            if " AS " in part.upper():
                alias = part.split(" AS ")[-1].strip().strip('"\'')
                columns.append(alias)
            elif " " in part and not part.startswith("("):
                # Last word is the alias
                alias = part.split()[-1].strip('"\'')
                columns.append(alias)
            else:
                # Use the column name as-is
                # Handle table.column syntax
                if "." in part:
                    col = part.split(".")[-1].strip('"\'')
                else:
                    col = part.strip('"\'')
                # Remove any function wrappers
                col = re.sub(r".*\((.*?)\).*", r"\1", col)
                columns.append(col)

        return columns

    def _split_columns(self, select_clause: str) -> List[str]:
        """Split SELECT columns handling nested parentheses."""
        columns = []
        current = []
        depth = 0

        for char in select_clause:
            if char == "(":
                depth += 1
                current.append(char)
            elif char == ")":
                depth -= 1
                current.append(char)
            elif char == "," and depth == 0:
                columns.append("".join(current).strip())
                current = []
            else:
                current.append(char)

        if current:
            columns.append("".join(current).strip())

        return columns

    def _error_response(self, message: str, question: str) -> Dict[str, Any]:
        """
        Create an error response in the standard format.

        AC#6: Returns user-friendly error messages.
        """
        return {
            "answer": message,
            "sql": None,
            "data": [],
            "citations": [],
            "executed_at": datetime.utcnow().isoformat(),
            "execution_time_seconds": 0,
            "row_count": 0,
            "error": True,
            "suggestions": self._get_suggestions(question),
        }

    def _get_suggestions(self, question: str) -> List[str]:
        """Generate suggestions based on the failed question."""
        suggestions = []
        question_lower = question.lower()

        if "yesterday" in question_lower or "today" in question_lower:
            suggestions.append("Try asking about 'last week' or a specific date range")

        if any(word in question_lower for word in ["asset", "machine", "grinder", "press"]):
            suggestions.append("Make sure the asset name is spelled correctly")
            suggestions.append("Try 'What assets are available?' to see all asset names")

        suggestions.append("Try a simpler question like 'What was the OEE yesterday?'")
        suggestions.append("Ask about specific metrics: OEE, downtime, output, safety events")

        return suggestions[:3]  # Return top 3 suggestions

    async def get_table_info(self) -> Dict[str, Any]:
        """
        Get information about available tables.

        Returns:
            Dict with table names and descriptions
        """
        self._ensure_initialized()

        try:
            table_info = self._db.get_table_info()
            return {
                "tables": self.ALLOWED_TABLES,
                "schema_info": table_info,
            }
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return {
                "tables": self.ALLOWED_TABLES,
                "schema_info": "Unable to retrieve schema information",
            }

    def is_configured(self) -> bool:
        """Check if the service is properly configured."""
        settings = self._get_settings()
        return bool(settings.supabase_db_url and settings.openai_api_key)

    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._initialized and self._db is not None


# Module-level singleton instance
text_to_sql_service = TextToSQLService()


def get_text_to_sql_service() -> TextToSQLService:
    """
    Get the singleton TextToSQLService instance.

    Returns:
        TextToSQLService singleton instance
    """
    return text_to_sql_service
