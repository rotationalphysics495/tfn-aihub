"""
Text-to-SQL Service Module (Story 4.2)

LangChain-based natural language to SQL translation for manufacturing data queries.

Provides:
- TextToSQLService: Main service for converting natural language to SQL
- QueryValidator: Security layer for SQL validation
- ResponseFormatter: Human-readable output with citations
- Manufacturing domain prompts and context

AC#1: LangChain SQLDatabase Integration
AC#2: Natural Language Query Parsing
AC#3: Query Execution and Result Formatting
AC#4: Data Citation for NFR1 Compliance
AC#5: Query Security and Guardrails
AC#6: Error Handling and Graceful Degradation
AC#7: Conversation Context Integration
AC#8: API Endpoint Design
"""

from app.services.ai.text_to_sql.service import (
    TextToSQLService,
    TextToSQLError,
    get_text_to_sql_service,
)
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
from app.services.ai.text_to_sql.prompts import (
    get_sql_system_prompt,
    get_table_descriptions,
    get_example_queries,
)

__all__ = [
    # Service
    "TextToSQLService",
    "TextToSQLError",
    "get_text_to_sql_service",
    # Validator
    "QueryValidator",
    "QueryValidationError",
    "SQLInjectionError",
    "TableAccessError",
    # Formatter
    "ResponseFormatter",
    "Citation",
    # Prompts
    "get_sql_system_prompt",
    "get_table_descriptions",
    "get_example_queries",
]
