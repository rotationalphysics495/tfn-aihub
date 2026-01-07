"""
Query Validator (Story 4.2)

Security layer for SQL query validation to prevent injection attacks
and enforce table access restrictions.

AC#5: Query Security and Guardrails
Task 4: Build Query Validator
"""

import logging
import re
from typing import List, Optional, Set, Tuple

import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where, Parenthesis
from sqlparse.tokens import Keyword, DML, DDL, Name

logger = logging.getLogger(__name__)


class QueryValidationError(Exception):
    """Base exception for query validation errors."""
    pass


class SQLInjectionError(QueryValidationError):
    """Raised when SQL injection attempt is detected."""
    pass


class TableAccessError(QueryValidationError):
    """Raised when query attempts to access unauthorized tables."""
    pass


class QueryComplexityError(QueryValidationError):
    """Raised when query is too complex or expensive."""
    pass


# Allowed tables whitelist (AC#1, AC#5)
ALLOWED_TABLES: Set[str] = {
    "assets",
    "cost_centers",
    "daily_summaries",
    "live_snapshots",
    "safety_events",
}

# Dangerous SQL patterns to block (AC#5)
DANGEROUS_PATTERNS: List[Tuple[str, str]] = [
    (r";\s*(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE)", "Multiple statements detected"),
    (r"--", "SQL comment injection detected"),
    (r"/\*", "SQL block comment detected"),
    (r"UNION\s+(?:ALL\s+)?SELECT", "UNION injection detected"),
    (r"INTO\s+(?:OUTFILE|DUMPFILE)", "File operation detected"),
    (r"LOAD_FILE", "File read attempt detected"),
    (r"BENCHMARK\s*\(", "Timing attack detected"),
    (r"SLEEP\s*\(", "Sleep injection detected"),
    (r"pg_sleep", "PostgreSQL sleep injection detected"),
    (r"WAITFOR\s+DELAY", "Delay injection detected"),
    (r"\\x[0-9a-fA-F]+", "Hex encoding detected"),
    (r"CHR\s*\(", "Character encoding injection detected"),
    (r"CONCAT\s*\(.*SELECT", "Concatenated subquery detected"),
    (r"EXEC\s*\(", "Dynamic execution detected"),
    (r"EXECUTE\s+", "Execute statement detected"),
    (r"xp_", "Extended stored procedure detected"),
    (r"sp_", "System stored procedure detected"),
    (r"@@", "System variable access detected"),
    (r"INFORMATION_SCHEMA", "Schema information access detected"),
    (r"pg_catalog", "PostgreSQL catalog access detected"),
    (r"sys\.", "System table access detected"),
]

# Forbidden statement types (AC#5)
FORBIDDEN_STATEMENTS: Set[str] = {
    "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
    "TRUNCATE", "GRANT", "REVOKE", "EXECUTE", "EXEC"
}

# Maximum query complexity limits
MAX_JOINS: int = 5
MAX_SUBQUERIES: int = 3
MAX_QUERY_LENGTH: int = 5000


class QueryValidator:
    """
    SQL query validator with security checks.

    AC#5: Query Security and Guardrails
    - SQL injection prevention
    - SELECT-only enforcement
    - Table whitelist enforcement
    - Query complexity limits
    """

    def __init__(
        self,
        allowed_tables: Optional[Set[str]] = None,
        max_joins: int = MAX_JOINS,
        max_subqueries: int = MAX_SUBQUERIES,
        max_query_length: int = MAX_QUERY_LENGTH,
    ):
        """
        Initialize the query validator.

        Args:
            allowed_tables: Set of allowed table names (default: ALLOWED_TABLES)
            max_joins: Maximum number of JOINs allowed
            max_subqueries: Maximum number of subqueries allowed
            max_query_length: Maximum query string length
        """
        self.allowed_tables = allowed_tables or ALLOWED_TABLES
        self.max_joins = max_joins
        self.max_subqueries = max_subqueries
        self.max_query_length = max_query_length

    def validate_input(self, user_input: str) -> str:
        """
        Validate and sanitize user input before SQL generation.

        Args:
            user_input: Raw user question

        Returns:
            Sanitized user input

        Raises:
            SQLInjectionError: If input contains SQL injection patterns
        """
        if not user_input or not user_input.strip():
            raise QueryValidationError("Empty input is not allowed")

        # Check for SQL-like patterns in natural language input
        suspicious_patterns = [
            r";\s*(?:DROP|DELETE|INSERT|UPDATE)",
            r"(?:OR|AND)\s+1\s*=\s*1",
            r"(?:OR|AND)\s+['\"]?\s*=\s*['\"]?",
            r"UNION\s+SELECT",
        ]

        input_upper = user_input.upper()
        for pattern in suspicious_patterns:
            if re.search(pattern, input_upper, re.IGNORECASE):
                logger.warning(f"Suspicious pattern in input: {user_input[:100]}")
                raise SQLInjectionError(
                    "Input contains potentially malicious content. "
                    "Please rephrase your question in natural language."
                )

        return user_input.strip()

    def validate_sql(self, sql: str) -> str:
        """
        Validate a generated SQL query for safety.

        AC#5: Comprehensive SQL validation.

        Args:
            sql: Generated SQL query string

        Returns:
            Validated and cleaned SQL query

        Raises:
            QueryValidationError: If query fails validation
            SQLInjectionError: If injection patterns detected
            TableAccessError: If unauthorized tables accessed
            QueryComplexityError: If query is too complex
        """
        if not sql or not sql.strip():
            raise QueryValidationError("Empty SQL query")

        # Clean the SQL (remove markdown code blocks if present)
        sql = self._clean_sql(sql)

        # Length check
        if len(sql) > self.max_query_length:
            raise QueryComplexityError(
                f"Query exceeds maximum length of {self.max_query_length} characters"
            )

        # Check for dangerous patterns
        self._check_dangerous_patterns(sql)

        # Parse and validate SQL structure
        parsed = sqlparse.parse(sql)
        if not parsed:
            raise QueryValidationError("Failed to parse SQL query")

        statement = parsed[0]

        # Validate statement type (SELECT only)
        self._validate_statement_type(statement, sql)

        # Validate tables accessed
        self._validate_tables(sql)

        # Check query complexity
        self._check_complexity(sql)

        # Ensure LIMIT is present for safety
        sql = self._ensure_limit(sql)

        logger.debug(f"SQL validation passed: {sql[:100]}...")
        return sql

    def _clean_sql(self, sql: str) -> str:
        """Remove markdown code blocks and clean whitespace."""
        # Remove markdown code blocks
        sql = re.sub(r"```sql\s*", "", sql, flags=re.IGNORECASE)
        sql = re.sub(r"```\s*", "", sql)

        # Remove leading/trailing whitespace
        sql = sql.strip()

        # Remove trailing semicolons (we'll add them if needed)
        sql = sql.rstrip(";").strip()

        return sql

    def _check_dangerous_patterns(self, sql: str) -> None:
        """Check for dangerous SQL patterns."""
        for pattern, message in DANGEROUS_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                logger.warning(f"Dangerous pattern detected: {message}")
                raise SQLInjectionError(f"Query blocked: {message}")

    def _validate_statement_type(self, statement, sql: str) -> None:
        """Validate that the statement is a SELECT query."""
        # Check statement type using sqlparse
        stmt_type = statement.get_type()

        if stmt_type and stmt_type.upper() != "SELECT":
            raise QueryValidationError(
                f"Only SELECT queries are allowed. Got: {stmt_type}"
            )

        # Double-check by looking at the SQL string
        sql_upper = sql.upper().strip()

        # Check for forbidden statements
        for forbidden in FORBIDDEN_STATEMENTS:
            # Check if forbidden word appears at start or after whitespace
            pattern = rf"(?:^|\s){forbidden}(?:\s|$)"
            if re.search(pattern, sql_upper):
                raise QueryValidationError(
                    f"Statement type '{forbidden}' is not allowed. Only SELECT queries permitted."
                )

        # Ensure it starts with SELECT (or WITH for CTEs)
        if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
            raise QueryValidationError(
                "Query must start with SELECT. Other statement types are not allowed."
            )

    def _validate_tables(self, sql: str) -> None:
        """Validate that only allowed tables are accessed."""
        # Extract table names from the query
        tables = self._extract_tables(sql)

        # Check each table against whitelist
        for table in tables:
            table_lower = table.lower()
            if table_lower not in self.allowed_tables:
                raise TableAccessError(
                    f"Access to table '{table}' is not allowed. "
                    f"Allowed tables: {', '.join(sorted(self.allowed_tables))}"
                )

    def _extract_tables(self, sql: str) -> Set[str]:
        """Extract table names from SQL query."""
        tables = set()

        # Parse the SQL
        parsed = sqlparse.parse(sql)[0]

        # Use regex to find table names in common patterns
        # FROM clause
        from_pattern = r"\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)"
        for match in re.finditer(from_pattern, sql, re.IGNORECASE):
            tables.add(match.group(1))

        # JOIN clauses
        join_pattern = r"\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)"
        for match in re.finditer(join_pattern, sql, re.IGNORECASE):
            tables.add(match.group(1))

        # Subquery handling - check for tables in parentheses
        subquery_pattern = r"\(\s*SELECT.*?FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)"
        for match in re.finditer(subquery_pattern, sql, re.IGNORECASE | re.DOTALL):
            tables.add(match.group(1))

        return tables

    def _check_complexity(self, sql: str) -> None:
        """Check query complexity limits."""
        sql_upper = sql.upper()

        # Count JOINs
        join_count = len(re.findall(r"\bJOIN\b", sql_upper))
        if join_count > self.max_joins:
            raise QueryComplexityError(
                f"Query has too many JOINs ({join_count}). Maximum allowed: {self.max_joins}"
            )

        # Count subqueries (SELECT inside parentheses)
        subquery_count = len(re.findall(r"\(\s*SELECT", sql_upper))
        if subquery_count > self.max_subqueries:
            raise QueryComplexityError(
                f"Query has too many subqueries ({subquery_count}). Maximum allowed: {self.max_subqueries}"
            )

    def _ensure_limit(self, sql: str) -> str:
        """Ensure the query has a LIMIT clause for safety."""
        sql_upper = sql.upper()

        # Check if LIMIT already exists
        if "LIMIT" in sql_upper:
            return sql

        # Add LIMIT 100 as safety measure
        return f"{sql} LIMIT 100"

    def get_allowed_tables(self) -> Set[str]:
        """Return the set of allowed tables."""
        return self.allowed_tables.copy()


def get_query_validator() -> QueryValidator:
    """Get a QueryValidator instance with default settings."""
    return QueryValidator()
